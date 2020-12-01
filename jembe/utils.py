from jembe import component
from typing import List, Dict, Any, Optional
from jembe.common import exec_name_to_full_name
from flask import url_for


def page_url(exec_name: str, url_params: Optional[List[Dict[str, Any]]] = None):
    """Returns page url with applied url_params"""
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


def run_only_once(_method):
    """
    decorator for class method to execute it only run once even if it is called 
    multiple times with diferrent arguments.
    NOTE: (WARNING) This decorator will cache return value nor will check method arguments
    Usefull form mount() method
    """
    attrname = "_%s_once_result" % id(_method)

    def decorator(self, *args, **kwargs):
        try:
            return getattr(self, attrname)
        except AttributeError:
            setattr(self, attrname, _method(self, *args, **kwargs))
            return getattr(self, attrname)

    return decorator
