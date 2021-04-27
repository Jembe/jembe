from typing import TYPE_CHECKING, Union, Tuple, Type, Dict, Any, get_args, get_origin
from abc import ABC, abstractmethod
import inspect
from importlib import import_module
from flask import Response

if TYPE_CHECKING:  # pragma: no cover
    from .component import Component, ComponentConfig

ComponentRef = Union[
    Union[Type["Component"], str],
    Tuple[Union[Type["Component"], str], Union["ComponentConfig", Dict[str, Any]]],
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


def direct_child_name(component: "Component", subcompoenent_full_name: str) -> str:
    """
    Returns name of the direct child of compoennt from subcomponent.
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


def convert_to_annotated_type(value: str, param: "inspect.Parameter"):
    def get_type(annotation):
        if get_origin(annotation) is Union and type(None) in get_args(annotation):
            # is_optional
            return get_args(annotation)[0]
        else:
            return annotation

    converted_type = get_type(param.annotation)
    try:
        if converted_type == int:
            return int(value)
        elif converted_type == str:
            return str(value)
        elif converted_type == bool:
            return value.upper() == "TRUE"
        elif converted_type == float:
            return float(value)
    except Exception as e:
        raise ValueError(
            "Cant convert url query param {}={}: {}".format(param.name, value, e)
        )

    raise ValueError(
        "Unsuported url query param type. Supported types are int, float, bool and string"
    )


def get_annotation_type(annotation):
    """ returns tuple(annotation_type, is_optional)"""

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


class JembeInitParamSupport(ABC):
    @classmethod
    @abstractmethod
    def dump_init_param(cls, value: Any) -> Any:
        raise NotImplementedError()

    @classmethod
    @abstractmethod
    def load_init_param(cls, value: Any) -> Any:
        raise NotImplementedError()
