from __future__ import print_function

import dataclasses
import logging
import multiprocessing
import pprint
import threading
import time
import traceback
import typing

import requests
from flask import current_app
from werkzeug.serving import make_server

from weave.legacy import (
    cache,
    context,
    execute,
    gql_json_cache,
    graph,
    serialize,
    value_or_error,
    wandb_api,
)
from weave.legacy.language_features.tagging import tag_store
from weave.legacy.language_features.tagging.tag_store import isolated_tagging_context

from . import engine_trace, logs, storage, util, weave_types

# A function to monkeypatch the request post method
# def patch_request_post():
#     r_post = requests.post

#     logging.info = lambda *args, **kwargs: None
#     logging.warn = lambda *args, **kwargs: None
#     logging.debug = lambda *args, **kwargs: None

#     def post(*args, **kwargs):
#         logging.critical(kwargs["json"]["query"].split(' ')[1])
#         return r_post(*args, **kwargs)

#     requests.post = post

# patch_request_post()

PROFILE = False

OptionalAuthType = typing.Optional[
    typing.Union[typing.Tuple[str, str], requests.models.HTTPBasicAuth]
]

logger = logging.getLogger("root")


@dataclasses.dataclass
class HandleRequestResponse:
    results: value_or_error.ValueOrErrors[dict[str, typing.Any]]
    nodes: value_or_error.ValueOrErrors[graph.Node]


def handle_request(
    request, deref=False, serialize_fn=storage.to_python
) -> HandleRequestResponse:
    # Stuff in the server path relies on lazy execution. Eager is now the default
    # in the weave package itself, so we need to switch to lazy mode here.
    with context.lazy_execution():
        start_time = time.time()
        tracer = engine_trace.tracer()
        # Need to add wandb_api.from_environment, which sets up the wandb api
        # The existing code only did this within the execute() function. But now
        # I'm hitting the need for this in deserialize, because node_id in deserialize
        # may try to access ref.type, which may try to access the wandb api.
        # That may not really be desirable, I didn't go deeper to figure out if
        # we should maybe stop that. But this fixes the problem for now.
        with wandb_api.from_environment():
            # nodes = [graph.Node.node_from_json(n) for n in request["graphs"]]
            with tracer.trace("request:deserialize"):
                nodes = serialize.deserialize(request["graphs"])

        with tracer.trace("request:execute"):
            with execute.top_level_stats() as stats:
                with context.execution_client():
                    with cache.time_interval_cache_prefix():
                        with gql_json_cache.gql_json_cache_context():
                            result = nodes.batch_map(execute.execute_nodes)

            with tracer.trace("request:deref"):
                if deref:
                    result = result.zip(nodes).safe_map(
                        lambda t: t[0]
                        if isinstance(t[1].type, weave_types.RefType)
                        else storage.deref(t[0])
                    )

        # print("Server request %s (%0.5fs): %s..." % (start_time,
        #                                              time.time() - start_time, [n.from_op.name for n in nodes[:3]]))

        logging.info("FINAL STATS\n%s" % pprint.pformat(stats.op_summary()))

        # Forces output to be untagged
        with tracer.trace("serialize_response"):
            with isolated_tagging_context():
                with wandb_api.from_environment():
                    result = result.safe_map(serialize_fn)

        logger.info("Server request done in: %ss" % (time.time() - start_time))
        tag_store.clear_tag_store()
        return HandleRequestResponse(result, nodes)


class SubprocessServer(multiprocessing.Process):
    def __init__(self, req_queue, resp_queue):
        multiprocessing.Process.__init__(self)
        self.req_queue = req_queue
        self.resp_queue = resp_queue

    def run(self):
        from weave.legacy import ops, panels, panels_py

        while True:
            req = self.req_queue.get()
            try:
                resp = handle_request(req).results.unwrap()
                self.resp_queue.put(resp)
            except:
                print("Weave subprocess server error")
                traceback.print_exc()
                self.resp_queue.put(Exception("Caught exception in sub-process server"))
                break

    def shutdown(self):
        self.kill()


class SubprocessServerClient:
    def __init__(self):
        self.req_queue = multiprocessing.Queue()
        self.resp_queue = multiprocessing.Queue()
        self.server_proc = SubprocessServer(self.req_queue, self.resp_queue)
        self.server_proc.start()

    def shutdown(self):
        self.server_proc.shutdown()

    def execute(self, nodes, no_cache=False):
        self.req_queue.put({"graphs": serialize.serialize(nodes)})
        response = self.resp_queue.get()
        deserialized = [storage.from_python(r) for r in response]
        return [storage.deref(r) for r in deserialized]


class InProcessServer(object):
    def __init__(self):
        pass

    def execute(self, nodes, no_cache=False):
        return execute.execute_nodes(nodes, no_cache=no_cache).unwrap()


class HttpServerClient(object):
    def __init__(self, url, emulate_weavejs=False, auth: OptionalAuthType = None):
        """Constructor.

        Args:
            url: The server base url
            emulate_weavejs: For testing only, should not be used from user code.
            auth (optional): auth argument to `requests.post`
        """
        self.url = url
        self.emulate_weavejs = emulate_weavejs
        self.execute_endpoint = "/__weave/execute/v2"
        self.auth = auth
        if emulate_weavejs:
            self.execute_endpoint = "/__weave/execute"

    def execute(self, nodes, no_cache=False):
        serialized = serialize.serialize(nodes)
        r = requests.post(
            self.url + self.execute_endpoint,
            json={"graphs": serialized},
            auth=self.auth,
        )
        r.raise_for_status()

        response = r.json()["data"]

        if self.emulate_weavejs:
            # When emulating weavejs, just return the server's json response.
            return response

        deserialized = [storage.from_python(r) for r in response]
        return [storage.deref(r) for r in deserialized]


_REQUESTED_SERVER_LOG_LEVEL: typing.Optional[int] = None


class HttpServer(threading.Thread):
    def __init__(self, port=0, host="localhost"):
        from . import weave_server

        self.host = host

        app = weave_server.app
        threading.Thread.__init__(self, daemon=True)
        self.srv = make_server(host, port, app, threaded=False)

        # if the passed port is zero then a randomly allocated port will be used. this
        # gets the value of the port that was assigned.
        self.port = self.srv.socket.getsockname()[1]

    @property
    def name(self):
        return f"Weave Port: {self.port}"

    def run(self):
        if _REQUESTED_SERVER_LOG_LEVEL is None:
            capture_weave_server_logs(logging.ERROR)

        # The werkzeug logger does not exist at import time, so we can't just
        # iterate through all existing loggers and set their levels. Fetching it
        # explicitly here creates it.
        # Without these two lines, request logs will always be printend. But by
        # default we don't want that.
        log = logging.getLogger("werkzeug")
        if _REQUESTED_SERVER_LOG_LEVEL is not None:
            log.setLevel(_REQUESTED_SERVER_LOG_LEVEL)

        self.srv.serve_forever()

    def shutdown(self):
        self.srv.shutdown()

    @property
    def url(self):
        if util.is_colab():
            url = f"https://{self.host}"
        else:
            url = f"http://{self.host}"
        if self.port is not None:
            url = f"{url}:{self.port}"
        return url


def capture_weave_server_logs(log_level: int = logging.INFO):
    global _REQUESTED_SERVER_LOG_LEVEL
    _REQUESTED_SERVER_LOG_LEVEL = log_level

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    console_log_settings: typing.Optional[logs.LogSettings] = None
    if not util.is_notebook() or util.parse_boolean_env_var(
        "WEAVE_SERVER_FORCE_HTTP_SERVER_CONSOLE_LOGS"
    ):
        console_log_settings = logs.LogSettings(logs.LogFormat.PRETTY, level=None)

    logs.enable_stream_logging(
        root_logger,
        wsgi_stream_settings=console_log_settings,
        pid_logfile_settings=logs.LogSettings(logs.LogFormat.PRETTY, logging.INFO),
    )
