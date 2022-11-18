# TODO: rename this file to op_call.py
import logging
import typing

from . import graph
from . import weave_types as types
from . import context_state
from . import weave_internal
from . import api
from . import registry_mem
from . import errors
from . import op_def
from . import op_args
from . import dispatch
from . import pyfunc_type_util
from . import language_autocall
from . import engine_trace


def _make_output_node(
    fq_op_name, bound_params, input_type, output_type_, refine_output_type
):
    output_type = output_type_
    # Don't try to refine if there are variable nodes, we are building a
    # function in that case!
    if refine_output_type and not any(
        graph.expr_vars(arg_node) for arg_node in bound_params.values()
    ):
        # If the weave.op in question is defined on a class, then the
        # incoming bound_params will have a `self` key. Interestingly,
        # the `refine_output_type` is an instance of `weave.op_def.OpDef`
        # which means that it already is bound to an object. This results
        # in two (both valid) `self` values:
        #   1. `self` in the `bound_params` which is the logical `self` in the weave graph
        #   2. `self` bound to `refine_output_type` as a byproduct of python language.
        #
        # Normally, we would do `refine_output_type(**bound_params). However.
        # Now, we _want_ to use the self in #1 as the self paramter passed to the
        # underlying implementation. So, we drop down a level and manually call
        # the underlying implementation.
        called_refine_output_type = refine_output_type.call_fn(**bound_params)
        tracer = engine_trace.tracer()
        with tracer.trace("refine.%s" % fq_op_name):
            output_type = api.use(called_refine_output_type)

        # Sorry for this circular dep...
        from weave.language_features.tagging import process_opdef_output_type

        arg_types = {k: n.type for k, n in bound_params.items()}
        op_def = registry_mem.memory_registry.get_op(fq_op_name)
        output_type = process_opdef_output_type.process_opdef_refined_output_type(
            output_type, arg_types, op_def
        )
    elif callable(output_type):
        new_input_type = {}
        for k, n in bound_params.items():
            if isinstance(n, graph.ConstNode) and not isinstance(n.type, types.Const):
                new_input_type[k] = types.Const(n.type, n.val)
            else:
                new_input_type[k] = n.type

        new_input_type = language_autocall.update_input_types(
            input_type, new_input_type
        )

        output_type = output_type(new_input_type)

    name = "OutputNode"
    bases = [graph.OutputNode]

    # If the output type is a run, mixin the Run's output type
    # as well. execute.py automatic inserts await_output operations
    # as needed.
    if isinstance(output_type, types.RunType) and hasattr(
        output_type.output, "NodeMethodsClass"
    ):
        name += output_type.output.__class__.__name__
        bases.append(output_type.output.NodeMethodsClass)

    node_methods_class, node_name = language_autocall.node_methods_class(output_type)
    if node_methods_class is not None:
        name += node_name
        if node_methods_class not in bases:
            bases.append(node_methods_class)

    # Mixin Node methods
    bases += weave_internal.get_node_methods_classes(output_type)

    unique_bases = []
    for base in bases:
        if base not in unique_bases:
            unique_bases.append(base)
    return_type = type(name, tuple(unique_bases), {})
    return return_type(output_type, fq_op_name, bound_params)


def _type_of(v: typing.Any):
    if isinstance(v, graph.Node):
        # Check if its a Node first, sometimes we mixin a callables with Node!
        return v.type
    elif callable(v):
        input_type = pyfunc_type_util.determine_input_type(v, None, True)
        output_type = pyfunc_type_util.determine_output_type(v, None, True)
        if not isinstance(input_type, op_args.OpNamedArgs):
            raise errors.WeaveInternalError("Function conversion requires named args")
        if callable(output_type):
            raise errors.WeaveInternalError(
                "Function conversion does not support callable output types"
            )
        return types.Function(
            input_type.arg_types,
            output_type,
        )
    else:
        return types.TypeRegistry.type_of(v)


def make_lazy_call(f, fq_op_name, input_type, output_type, refine_output_type):
    """Given the parameters of an op definition, make a function that returns `graph.Node`

    Args:
        f: Op function body
        fq_op_name: Op name
        input_type: Op input_type
        output_type: Op output_type

    Returns:
        A lazy function with the same signature structure as f. The returned function accepts
        `graph.Node` arguments and will return a `graph.Node`
    """

    def lazy_call(*args, **kwargs):
        arg_types = [_type_of(a) for a in args]
        kwarg_types = {k: _type_of(v) for k, v in kwargs.items()}
        op = dispatch.get_op_for_input_types(
            fq_op_name,
            arg_types,
            kwarg_types,
        )

        # IMPORTANT: there is one case where we expect to fall into here: list<dict>["a"].
        # In this case, the outer list's `index` method will be called. This will result
        # in no valid op being found, and we should try to use the inner pick op. This
        # is one of the few "dispatch" hacks and could be avoided if we had different symbols:
        if op is None and op_def.common_name(fq_op_name) == "__getitem__":
            op = dispatch.get_op_for_input_types(
                "pick",
                arg_types,
                kwarg_types,
            )

        if op is None:
            # There is a parallel spot in compile.py which has a similar comment
            # This indicates that we believe there is no valid op to accept the
            # incoming data Before productionizing Weave, we should throw here -
            # for now since assignability is still a bit off, we are a bit more
            # relaxed. This is the case where we are not confident that any op
            # is appropriate, so we just go with the one provided at runtime -
            # not gaurenteed to be correct!
            logging.warning(
                f"Lazy Dispatch - Unable to find a valid op for {fq_op_name}"
            )
            # raise errors.WeaveInternalError(
            #     f"Could not find op for inputs {args} and {kwargs} for op {fq_op_name}"
            # )
            op = registry_mem.memory_registry.get_op(fq_op_name)

            op_name = fq_op_name
            op_output = output_type
            op_refine = refine_output_type
        else:
            # We use URI in case it is versioned - this is the fully qualified name of the op
            op_name = op.uri
            op_output = op.output_type
            op_refine = op.refine_output_type
        bound_params = op.bind_params(args, kwargs)
        return _make_output_node(
            op_name,
            bound_params,
            input_type,
            op_output,
            op_refine,
        )

    return lazy_call


def make_eager_call(lazy_call, op_def):
    if op_def.is_async:

        def eager_call_async(*args, **kwargs):
            output_node = lazy_call(*args, **kwargs)
            return weave_internal.use(output_node)

        return eager_call_async
    else:

        def eager_call_sync(*args, **kwargs):
            return op_def.resolve_fn(*args, **kwargs)

        return eager_call_sync


def make_call(eager_call, lazy_call):
    def call(*args, **kwargs):
        if context_state.eager_mode():
            return eager_call(*args, **kwargs)
        else:
            return lazy_call(*args, **kwargs)

    return call
