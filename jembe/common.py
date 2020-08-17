from typing import TYPE_CHECKING, Optional, Union, Tuple, Type, List

if TYPE_CHECKING:
    from .component import Component, ComponentConfig

ComponentRef = Union[Type["Component"], Tuple[Type["Component"], "ComponentConfig"]]
