from typing import TYPE_CHECKING, Union, Tuple, Type, Dict, Any, get_args, get_origin
import re
import collections
import inspect
from abc import ABC, abstractmethod
from importlib import import_module
from dataclasses import is_dataclass, asdict
from datetime import date, datetime
from flask import Response, json, current_app
from jembe.exceptions import JembeError

if TYPE_CHECKING:  # pragma: no cover
    import jembe

ComponentRef = Union[
    Union[Type["jembe.Component"], str],
    Tuple[
        Union[Type["jembe.Component"], str],
        Union["jembe.ComponentConfig", Dict[str, Any]],
    ],
]

DisplayResponse = Union[str, Response]


def exec_name_to_full_name(exec_name: str) -> str:
    """
    Removes component keys from exec name to get full_name.

    keys in exec_name are separated by . (dot)
    """
    return "/".join(ck.split(".")[0] for ck in exec_name.split("/"))


def is_page_exec_name(exec_name: str) -> bool:
    """Is Exec name name of the page"""
    return len(exec_name.strip("/").split("/")) == 1


def direct_child_name(
    component: "jembe.Component", subcompoenent_full_name: str
) -> str:
    """
    Returns name of the direct child of component from subcomponent.
    If subcompoennt is not under component raise error.
    """
    parent_names = component._config.full_name.split("/")
    child_names = subcompoenent_full_name.split("/")
    if parent_names != child_names[: len(parent_names)]:
        raise ValueError(
            "Component {} is not subcomponent of {}".format(
                subcompoenent_full_name, component._config.full_name
            )
        )
    return child_names[len(parent_names)]


def is_direct_child_name(exec_name: str, sub_exec_name: str) -> bool:
    """Returns True if sub_exec_name is direct child of exec_name"""
    if not sub_exec_name.startswith(exec_name) or exec_name == sub_exec_name:
        return False
    relative_name = sub_exec_name[len(exec_name) :]
    if relative_name[0] != "/":
        return False
    if len(relative_name.split("/")) > 2:
        return False
    return True

def is_child_name(exec_name: str, sub_exec_name: str) -> bool:
    """Returns True if sub_exec_name is under exec_name"""
    if not sub_exec_name.startswith(exec_name) or exec_name == sub_exec_name:
        return False
    relative_name = sub_exec_name[len(exec_name) :]
    if relative_name[0] != "/":
        return False
    return True


def parent_exec_name(exec_name: str) -> str:
    return "/".join(exec_name.split("/")[:-1])


def import_by_name(object_name: str) -> Any:
    try:
        str_split = object_name.split(".")
        object_name = str_split[-1]
        modul_name = ".".join(str_split[:-1])
        modul = import_module(modul_name)
        object_type = getattr(modul, object_name)
    except:
        raise ValueError("Import with name {} doesn't exist".format(object_name))
    return object_type


class JembeInitParamSupport(ABC):
    @classmethod
    @abstractmethod
    def dump_init_param(cls, value: Any) -> Any:
        raise NotImplementedError()

    @classmethod
    @abstractmethod
    def load_init_param(cls, value: Any) -> Any:
        raise NotImplementedError()


# Transforming python type to json serializable type back and forth
def dump_param(annotation, value: Any) -> Any:
    """
    Transforms annotated component state param into json serializable type ready to be
    used by jembe client javascript, either as state variable, url query variale,
    jrl etc.
    """
    source_type, can_be_none = get_annotation_type(annotation)
    if value is None and can_be_none:
        return None
    elif _eq_type(source_type, list, tuple, set, collections.abc.Sequence):
        targs = get_args(source_type)
        if len(targs) == 0:
            _dump_load_unspecified_warning(source_type)
            return value
        return list(dump_param(targs[0], item) for item in value)
    elif _eq_type(source_type, dict):
        targs = get_args(source_type)
        if len(targs) < 2:
            _dump_load_unspecified_warning(source_type)
            return value
        return {
            dump_param(targs[0], k): dump_param(targs[1], v) for k, v in value.items()
        }
    elif (
        source_type == JembeInitParamSupport
        or (
            inspect.isclass(source_type)
            and issubclass(source_type, JembeInitParamSupport)
        )
        or (
            inspect.isclass(get_origin(source_type))
            and issubclass(
                get_origin(source_type), JembeInitParamSupport  # type:ignore
            )
        )
        or isinstance(value, JembeInitParamSupport)
    ):
        return source_type.dump_init_param(value)
    elif _eq_type(source_type, int, float, bool, str):
        return value
    elif _eq_type(source_type, date, datetime):
        return value.isoformat()
    elif is_dataclass(source_type):
        return asdict(value)
    elif source_type == Any:
        _dump_load_unspecified_warning(source_type)
        return value
    raise JembeError(
        "Unsupported state/init param type {}:{}".format(source_type, value)
    )


def load_param(annotation, value: Any) -> Any:
    """
    Loads component sate params received by jembe client javascript
    and transform it to python type according to its annotation
    ready to be process by component
    """
    target_type, can_be_none = get_annotation_type(annotation)
    if value is None and can_be_none:
        return None
    if _eq_type(target_type, list):
        if isinstance(value, str):
            value = _decode_str_to_type(list, value)
        targs = get_args(target_type)
        if len(targs) == 0:
            _dump_load_unspecified_warning(target_type)
            return value
        return list(load_param(targs[0], v) for v in value)
    elif _eq_type(target_type, tuple, collections.abc.Sequence):
        if isinstance(value, str):
            value = _decode_str_to_type(list, value)
        targs = get_args(target_type)
        if len(targs) == 0:
            _dump_load_unspecified_warning(target_type)
            return value
        return tuple([load_param(targs[0], v) for v in value])
    elif _eq_type(target_type, set):
        if isinstance(value, str):
            value = _decode_str_to_type(list, value)
        targs = get_args(target_type)
        if len(targs) == 0:
            _dump_load_unspecified_warning(target_type)
            return value
        return set([load_param(targs[0], v) for v in value])
    elif _eq_type(target_type, dict):
        if isinstance(value, str):
            value = _decode_str_to_type(dict, value)
        targs = get_args(target_type)
        if len(targs) == 0:
            _dump_load_unspecified_warning(target_type)
            return value
        return {
            load_param(targs[0], k): load_param(targs[1], v) for k, v in value.items()
        }
    elif (
        target_type == JembeInitParamSupport
        or (
            inspect.isclass(target_type)
            and issubclass(target_type, JembeInitParamSupport)
        )
        or (
            inspect.isclass(get_origin(target_type))
            and issubclass(
                get_origin(target_type), JembeInitParamSupport  # type:ignore
            )
        )
    ):
        return target_type.load_init_param(value)
    elif _eq_type(target_type, int):
        return int(value)
    elif _eq_type(target_type, float):
        return float(value)
    elif _eq_type(target_type, bool):
        if isinstance(value, str):
            value = _decode_str_to_type(dict, value)
        return bool(value)
    elif _eq_type(target_type, str):
        return str(value)
    elif _eq_type(target_type, date):
        return date.fromisoformat(value)
    elif _eq_type(target_type, datetime):
        return datetime.fromisoformat(value)
    elif is_dataclass(target_type):
        return dataclass_from_dict(target_type, value)
    elif target_type == Any:
        _dump_load_unspecified_warning(Any)
        return value
    raise JembeError(
        "Unsupported state/init param type {}:{}".format(target_type, value)
    )


def _eq_type(checked_type: Type[Any], *compare_with: Type[Any]) -> bool:
    for cw in compare_with:
        if checked_type == cw or get_origin(checked_type) == cw:
            return True
    return False


def get_annotation_type(annotation):
    """returns tuple(annotation_type, is_optional)"""

    def _geta(annotation):
        if inspect.isfunction(annotation):
            # handling typing.NewType
            # TODO make it robust and to cover all cases
            return annotation.__supertype__
        else:
            return annotation

    if get_origin(annotation) is Union and type(None) in get_args(annotation):
        # is_optional
        return (_geta(get_args(annotation)[0]), True)
    else:
        return (_geta(annotation), False)


def dataclass_from_dict(klass, dikt):
    try:
        fieldtypes = klass.__annotations__
        return klass(**{f: dataclass_from_dict(fieldtypes[f], dikt[f]) for f in dikt})
    except AttributeError:
        if isinstance(dikt, (tuple, list)):
            return [dataclass_from_dict(klass.__args__[0], f) for f in dikt]
        return dikt


def _decode_str_to_type(ttype, value: str):
    if ttype == bool:
        return ttype(value.upper() == "TRUE")

    return ttype(json.loads(re.sub("(?<!\\\\)'", '"', value)))


def _dump_load_unspecified_warning(ttype):
    current_app.logger.warning(
        "Do not use '{}' annotation for component state params "
        "you should be more specific in other to enable proper transformation"
        "into and out json".format(ttype)
    )
