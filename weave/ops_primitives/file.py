import os
import dataclasses
import shutil

from ..refs import ArtifactVersionFileType
from ..api import op, mutation, weave_class
from .. import weave_types as types
from .. import wandb_util
from .. import ops_arrow
from .. import artifacts_local

_py_open = open


def path_ext(path):
    return os.path.splitext(path)[1].strip(".")


##### These are actually path ops, but they are called file for legacy reason


@op(
    name="file-dir",
    input_type={"file": types.DirType()},
    output_type=types.DirType(),
)
def file_dir(file):
    return file


##### End path ops


#### TODO: Table does not belong here!


class TableType(types.ObjectType):
    name = "table"

    def property_types(self):
        return {"_rows": ops_arrow.ArrowWeaveListType(types.TypedDict({}))}


@weave_class(weave_type=TableType)
class Table:
    def __init__(self, _rows):
        self._rows = _rows

    @op(
        name="table-rowsType",
        input_type={"table": TableType()},
        output_type=types.Type(),
    )
    def rows_type(table):
        ttype = types.TypeRegistry.type_of(table._rows)
        return ttype

    @op(
        name="table-rows",
        input_type={"table": TableType()},
        output_type=ops_arrow.ArrowWeaveListType(types.TypedDict({})),
        refine_output_type=rows_type,
    )
    def rows(table):
        return table._rows


@weave_class(weave_type=types.FileType)
class File:
    @op(
        name="file-table",
        input_type={"file": types.union(types.FileType(), ArtifactVersionFileType())},
        output_type=TableType(),
    )
    def table(file):
        local_path = file.get_local_path()
        import json

        with _py_open(local_path) as f:
            data = json.load(f)

        wb_artifact = None
        if hasattr(file, "artifact") and isinstance(
            file.artifact, artifacts_local.WandbArtifact
        ):
            wb_artifact = file.artifact._saved_artifact
        converted_object_type = wandb_util.weave0_type_json_to_weave1_type(
            data["column_types"], wb_artifact
        )

        # Fix two things:
        # 1. incoming table column names may not match the order of column_types
        # 2. if we had an unknown (happens when old type is "PythonObjectType")
        #    we need to manually detect the type.
        obj_prop_types = {}
        for i, key in enumerate(data["columns"]):
            col_type = converted_object_type.property_types[key]
            if col_type.assign_type(types.UnknownType()):
                unknown_col_example_data = [row[i] for row in data["data"]]
                detected_type = types.TypeRegistry.type_of(unknown_col_example_data)
                obj_prop_types[key] = detected_type.object_type
            else:
                obj_prop_types[key] = col_type
        object_type = types.TypedDict(obj_prop_types)

        # TODO: this will need to recursively convert dicts to Objects in some
        # cases.
        rows = []
        for data_row in data["data"]:
            row = {}
            for col_name, val in zip(data["columns"], data_row):
                row[col_name] = val
            rows.append(row)

        res = ops_arrow.to_arrow_from_list_and_artifact(
            rows, object_type, file.artifact
        )
        # I Don't think I need Table now. We won't parse again
        return Table(res)

    @op(
        name="file-directUrlAsOf",
        input_type={
            "file": types.union(types.FileType(), ArtifactVersionFileType()),
            "asOf": types.Int(),
        },
        output_type=types.String(),
    )
    def direct_url_as_of(file, asOf):
        # TODO: This should depend on whether its local or an artifact
        #    etc
        local_path = os.path.abspath(file.get_local_path())
        return "/__weave/file/%s" % local_path

    @op(
        name="file-size", input_type={"file": types.FileType()}, output_type=types.Int()
    )
    def file_size(file):
        # file is an artifact manifest entry for now.
        return 10
        return file.size

    @mutation
    def file_contents_set(self, val):
        return self._file_contents_set(val)

    @op(
        setter=file_contents_set,
        name="file-contents",
        input_type={"file": types.FileType()},
        output_type=types.String(),
    )
    def file_contents(file):
        return file._contents()


types.FileType.instance_class = File
types.FileType.instance_classes = File


# Question, should all tables be lazy? That would mean we can serialize
#     and hand them between processes.... How would the user choose to
#     save a serialized version of a given table?


@op(name="file-type", input_type={"file": types.FileType()}, output_type=types.Type())
def file_type(file):
    # file is an artifact manifest entry for now.
    path = file.path
    parts = path.split(".")
    extension = None
    if len(parts) > 1:
        extension = parts[-1]
    result_type = {"type": "file", "extension": extension}
    if len(parts) > 2 and extension == "json":
        # TODO: validate. I'm sure there is existing logic for this in wandb
        result_type["wbObjectType"] = {
            "type": parts[-2],
        }
    return result_type


@weave_class(weave_type=types.SubDirType)
class SubDir(object):
    def __init__(self, fullPath, size, dirs, files):
        self.fullPath = fullPath
        self.size = size
        self.dirs = dirs
        self.files = files


types.SubDirType.instance_classes = SubDir
types.SubDirType.instance_class = SubDir


@op(
    name="dir-pathReturnType",
    input_type={"dir": types.DirType(), "path": types.String()},
    output_type=types.Type(),
)
def path_return_type(dir, path):
    return dir._path_return_type(path)


@weave_class(weave_type=types.DirType)
class Dir:
    def __init__(self, fullPath, size, dirs, files):
        self.fullPath = fullPath
        self.size = size
        self.dirs = dirs
        self.files = files

    def get_local_path(self):
        return self.path

    @op(name="dir-size", input_type={"dir": types.DirType()}, output_type=types.Int())
    def size(dir):
        return dir.size

    @op(
        name="dir-path",
        input_type={"dir": types.DirType(), "path": types.String()},
        output_type=types.UnionType(types.FileType(), types.DirType(), types.none_type),
        refine_output_type=path_return_type,
    )
    def open(dir, path):
        return dir._path(path)


types.DirType.instance_classes = Dir
types.DirType.instance_class = Dir

#### VersionedDir is a directory that will automatically be saved to
# an artifact when it is used.
# TODO: the File/Dir/Artifact/Local/VersionedDir design needs to be
#    reworked. File/Dir are more like Refs...


class VersionedDirType(types.Type):
    def save_instance(self, obj, artifact, name):
        with artifact.new_dir(f"{name}") as dirpath:
            shutil.copytree(obj.path, dirpath, dirs_exist_ok=True)

    def load_instance(self, artifact, name, extra=None):
        return VersionedDir(artifact.path(name))


@weave_class(weave_type=VersionedDirType)
@dataclasses.dataclass
class VersionedDir:
    path: str


VersionedDirType.instance_classes = VersionedDir
