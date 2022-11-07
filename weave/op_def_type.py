import textwrap
import json
import inspect
import types as py_types
import typing
import os
import sys
import ast

from . import artifacts_local
from . import op_def
from . import errors
from . import context_state
from . import weave_types as types
from . import registry_mem

from . import infer_types


def typed_dict_code(type_):
    result = f"class {type_.__name__}(typing.TypedDict):\n"
    for k in type_.__required_keys__:
        result += f"    {k}: {type_.__annotations__[k].__name__}\n"
    return result


def type_code(type_):
    # Absolutely horrible and hacky. This is not recursive in a tree/graph
    # way, its linear, so it'll only produce one TypedDict if there are many.
    # Using this to get the versioned object notebook working.
    if infer_types.is_typed_dict_like(type_):
        return typed_dict_code(type_) + "\n"
    elif isinstance(type_, py_types.GenericAlias) or isinstance(
        type_, typing._GenericAlias  # type: ignore
    ):
        return type_code(type_.__args__[0])


def get_import_code(fn):
    # Even more horrible and hacky
    source = inspect.getsource(fn)
    try:
        parsed = ast.parse(source)
    except IndentationError:
        return ""
    import_code = ""
    for node in ast.walk(parsed):
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
            # A really bad way to check if a variable reference is for
            # a module!
            if node.id in sys.modules:
                import_code += f"import {node.id}\n"
    return import_code


class OpDefType(types.Type):
    instance_class = op_def.OpDef
    instance_classes = op_def.OpDef

    def save_instance(self, obj: op_def.OpDef, artifact, name):

        if obj.is_builtin:
            with artifact.new_file(f"{name}.json") as f:
                json.dump({"name": obj.name}, f)
        else:
            code = "import typing\nimport weave\n"

            # Try to figure out module imports from the function body
            # (in a real hacky way as a POC)
            code += get_import_code(obj.resolve_fn)

            # Create TypedDict types for referenced TypedDicts
            resolve_annotations = obj.resolve_fn.__annotations__
            for k, type_ in resolve_annotations.items():
                gen_type_code = type_code(type_)
                if gen_type_code is not None:
                    code += gen_type_code

            code += textwrap.dedent(inspect.getsource(obj.resolve_fn))
            with artifact.new_file(f"{name}.py") as f:
                f.write(code)

    def load_instance(cls, artifact, name, extra=None):
        try:
            with artifact.open(f"{name}.json") as f:
                op_spec = json.load(f)

            return registry_mem.memory_registry._ops[op_spec["name"]]
        except FileNotFoundError:
            pass

        path_with_ext = os.path.relpath(
            artifact.path(f"{name}.py"), start=artifacts_local.local_artifact_dir()
        )
        # remove the .py extension
        path = os.path.splitext(path_with_ext)[0]
        # convert filename into module path
        parts = path.split("/")
        module_path = ".".join(parts)

        sys.path.insert(0, artifacts_local.local_artifact_dir())
        with context_state.loading_op_location(artifact.location):
            # This has a side effect of registering the op
            mod = __import__(module_path)
        sys.path.pop(0)
        # We justed imported e.g. 'op-number-add.xaybjaa._obj'. Navigate from
        # mod down to _obj.
        for part in parts[1:]:
            mod = getattr(mod, part)

        op_defs = inspect.getmembers(mod, op_def.is_op_def)
        if len(op_defs) != 1:
            raise errors.WeaveInternalError(
                "Unexpected Weave module saved in: %s" % path
            )
        _, od = op_defs[0]
        return od


def fully_qualified_opname(wrap_fn):
    op_module_file = os.path.abspath(inspect.getfile(wrap_fn))
    if op_module_file.endswith(".py"):
        op_module_file = op_module_file[:-3]
    elif op_module_file.endswith(".pyc"):
        op_module_file = op_module_file[:-4]
    return "file://" + op_module_file + "." + wrap_fn.__name__
