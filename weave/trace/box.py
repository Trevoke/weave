"""Alternate boxing implementation for Weave Trace.

This copies many things from weave/legacy/box.py, but it notably
does not box None and bool which simplify checks for trace users."""

from __future__ import annotations

import datetime
import typing

import numpy as np

from weave import ref_util

T = typing.TypeVar("T")


class BoxedInt(int):
    _id: typing.Optional[int] = None


class BoxedFloat(float):
    _id: typing.Optional[int] = None


class BoxedStr(str):
    _id: typing.Optional[int] = None


class BoxedDict(dict):
    _id: typing.Optional[int] = None

    def _lookup_path(self, path: typing.List[str]):
        assert len(path) > 1
        edge_type = path[0]
        edge_path = path[1]
        assert edge_type == ref_util.DICT_KEY_EDGE_NAME

        res = self[edge_path]
        remaining_path = path[2:]
        if remaining_path:
            return res._lookup_path(remaining_path)
        return res

    def __getitem__(self, __key: typing.Any) -> typing.Any:
        val = super().__getitem__(__key)
        return ref_util.val_with_relative_ref(
            self, val, [ref_util.DICT_KEY_EDGE_NAME, str(__key)]
        )


class BoxedList(list):
    def _lookup_path(self, path: typing.List[str]):
        assert len(path) > 1
        edge_type = path[0]
        edge_path = path[1]
        assert edge_type == ref_util.LIST_INDEX_EDGE_NAME

        res = self[int(edge_path)]
        remaining_path = path[2:]
        if remaining_path:
            return res._lookup_path(remaining_path)
        return res

    def __iter__(self):
        # Needed to make list-comprehensions work with our custom __getitem__,
        # otherwise, list.__iter__ uses the parent class __getitem__.
        for i in range(len(self)):
            yield self[i]

    def __getitem__(self, __index: typing.Any) -> typing.Any:
        val = super().__getitem__(__index)
        return ref_util.val_with_relative_ref(
            self, val, [ref_util.LIST_INDEX_EDGE_NAME, str(__index)]
        )


class BoxedDatetime(datetime.datetime):
    def __eq__(self, other):
        return (
            isinstance(other, datetime.datetime)
            and self.timestamp() == other.timestamp()
        )


class BoxedTimedelta(datetime.timedelta):
    def __eq__(self, other):
        return (
            isinstance(other, datetime.timedelta)
            and self.total_seconds() == other.total_seconds()
        )


# See https://numpy.org/doc/stable/user/basics.subclassing.html
class BoxedNDArray(np.ndarray):
    def __new__(cls, input_array):
        obj = np.asarray(input_array).view(cls)
        return obj

    def __array_finalize__(self, obj):
        if obj is None:
            return


def box(
    obj: T,
) -> (
    T
    | BoxedInt
    | BoxedFloat
    | BoxedStr
    | BoxedDict
    | BoxedList
    | BoxedNDArray
    | BoxedDatetime
    | BoxedTimedelta
):
    if type(obj) == int:
        return BoxedInt(obj)
    elif type(obj) == float:
        return BoxedFloat(obj)
    elif type(obj) == str:
        return BoxedStr(obj)
    elif type(obj) == dict:
        return BoxedDict(obj)
    elif type(obj) == list:
        return BoxedList(obj)
    elif type(obj) == np.ndarray:
        return BoxedNDArray(obj)
    elif type(obj) == datetime.datetime:
        return BoxedDatetime.fromtimestamp(obj.timestamp(), tz=datetime.timezone.utc)
    elif type(obj) == datetime.timedelta:
        return BoxedTimedelta(seconds=obj.total_seconds())
    return obj


def unbox(
    obj: T,
) -> (
    T
    | int
    | float
    | str
    | dict
    | list
    | np.ndarray
    | datetime.datetime
    | datetime.timedelta
):
    if type(obj) == BoxedInt:
        return int(obj)
    elif type(obj) == BoxedFloat:
        return float(obj)
    elif type(obj) == BoxedStr:
        return str(obj)
    elif type(obj) == BoxedDict:
        return dict(obj)
    elif type(obj) == BoxedList:
        return list(obj)
    elif type(obj) == BoxedNDArray:
        return np.array(obj)
    elif type(obj) == BoxedDatetime:
        return datetime.datetime.fromtimestamp(obj.timestamp())
    elif type(obj) == BoxedTimedelta:
        return datetime.timedelta(seconds=obj.total_seconds())
    return obj
