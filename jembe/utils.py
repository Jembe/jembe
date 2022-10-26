from functools import wraps
from typing import List, Dict, Any, Optional
from jembe.common import exec_name_to_full_name
from jembe.exceptions import JembeError
from jembe.app import get_processor
from flask import url_for


def page_url(exec_name: str, url_params: Optional[List[Dict[str, Any]]] = None):
    """Returns url of the Component referenced by exec_name (Component Execution Name).

    Url is genarated without initialising components but by bulidin url dynamicaly.

    .. note:: This method uses Url params names instead of state param names.If not renamed with `ComponentConfig(url_query_params={})` names are the same.

    Args:
        exec_name: Component Execution Name which url we want to obtain
        url_params: Optional list of component url params for every component in exec_name.  Defaults to None.

    """
    if not exec_name.startswith("/"):
        exec_name = "/{}".format(exec_name)
    root_page_name = exec_name.split("/")[1].split(".")[0]
    full_name = exec_name_to_full_name(exec_name)
    components_keys = [
        (".{}".format(cn.split(".")[1]) if len(cn.split(".")) == 2 else "")
        for cn in exec_name.split("/")[1:]
    ]
    endpoint_name = "{bp_name}.{full_name}".format(
        bp_name=root_page_name, full_name=full_name
    )
    no_of_components = len(full_name.split("/")) - 1
    url_values = {}
    for i in range(no_of_components):
        ckey_index = "__{}".format(i) if i > 0 else ""
        url_values["component_key{}".format(ckey_index)] = components_keys[i]
    if url_params:
        for (index, params) in enumerate(url_params):
            for key, value in params.items():
                url_key = "{}__{}".format(key, index) if index > 0 else key
                url_values[url_key] = value

    return url_for(endpoint_name, **url_values)


def run_only_once(_method=None, *, for_state: Optional[str] = None):
    """Decorator for component method that executes method only once and caches the result. 


    First time method is called result is cachend, on any subsequent calls method is not executed
    and cached valuted is returned.

    When for_state is provided than cache will be clear when state variable with same
    name is changed.

    .. warning:: 

        This decorator will cache return value regardles of method arguments values. 
        
    This decorator is usefull when we need to perform costly calculation only once
    and don't want and don't need to do it in __init__.

    .. code-block:: python

        @property
        @run_only_once(for_state="id")
        def record(self):
            return db.session.query(ComplexDBView).filter(ComplexDBView.id==id).first()



    Args:
        _method (_type_, optional): _description_. Defaults to None.
        for_state (Optional[str], optional): name of state variable to monitor for change. Defaults to None.

    Raises:
        JembeError: when for_state is not valid state name

    """
    attrname = "_{}_once_result".format(id(_method))

    def decorator(method):
        @wraps(method)
        def wrapper(self, *args, **kwargs):
            for_state_value = None
            if for_state is not None:
                try:
                    for_state_value = self.state[for_state]
                except KeyError:
                    raise JembeError(
                        "{} {}: for_state for decorator run_only_once has invalide state name".format(
                            self._config.full_name, method.__name__
                        )
                    )

            try:
                return_value, saved_for_state_value = getattr(self, attrname)
                if for_state is None or for_state_value == saved_for_state_value:
                    return return_value
            except AttributeError:
                pass
            # execute and save new value
            setattr(self, attrname, (method(self, *args, **kwargs), for_state_value))
            return getattr(self, attrname)[0]

        return wrapper

    if _method is None:
        return decorator
    else:
        return decorator(_method)

def call_window_open(url:str):
    processor = get_processor()
    processor.call_window_open.append(url)