from typing import Optional


def action(
    deferred=False,
    deferred_after: Optional[str] = None,
    deferred_before: Optional[str] = None,
):
    """
    decorator to mark method as public action inside component

    deferred aciton is executed last after allother actions from parent action template
    are executed no matter of its postion inside parent action template.

    Usefull if we need to create breadcrumb or other summary report 
    based from already executed actions

    deferred_after and deferred_before are used to execute this action after or before 
    other specific deferred action, when multiple actions has deferred execution
    """
    # This decorator don't anytthing except allow
    # componentconfig.set_compoenent_class to
    # recognise method as action

    def decorator(method):
        method._jembe_action = True
        method._jembe_action_deferred = deferred
        method._jembe_action_deferred_after = deferred_after
        method._jembe_action_deferred_before = deferred_before
        return method

    return decorator
