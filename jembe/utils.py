__all__ = ("build_url", "relative_name", "direct_child_name", "is_direct_child")


def build_url(url_path: str, **query_params) -> str:
    """
    Build url from url_path with or without query params and **query_params
    """
    raise NotImplementedError()


def direct_child_name(parent_component, child_component) -> str:
    """Returns name of the first child component of parent_component that
        is parent of child_component"""
    raise NotImplementedError()


def relative_name(parent_component, child_component) -> str:
    """ returns relative name of the child compoennt from parent_component"""
    raise NotImplementedError()


def is_direct_child(parent_component, child_component) -> bool:
    """Return true if child_component is direct child of parent_comopnent"""
    raise NotImplementedError()
