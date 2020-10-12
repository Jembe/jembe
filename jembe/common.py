from typing import TYPE_CHECKING, Union, Tuple, Type, Dict, Any 

if TYPE_CHECKING:  # pragma: no cover
    from .component import Component, ComponentConfig

ComponentRef = Union[
    Union[Type["Component"], str],
    Tuple[Union[Type["Component"], str], Union["ComponentConfig", Dict[str, Any]]],
]


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
