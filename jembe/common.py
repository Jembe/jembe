from typing import TYPE_CHECKING, Optional, Union, Tuple, Type, List

if TYPE_CHECKING: # pragma: no cover
    from .component import Component, ComponentConfig

ComponentRef = Union[Type["Component"], Tuple[Type["Component"], "ComponentConfig"]]

def exec_name_to_full_name(exec_name:str)->str:
    """
    Removes component keys from exec name to get full_name.

    keys in exec_name are separated by . (dot)
    """
    return "/".join(ck.split(".")[0] for ck in exec_name.split("/"))