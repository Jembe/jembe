# Jembe key concepts

1. Everything can be created without javascript including frontend logic, such as;
    1. Hiding and showing part of the html (form, grid etc.)
    2. Datepicker;
    3. Lookup fields;
    4. Dialogs and modals;
    5. Dependent selects and similar fields;
    6. Validations
2. Components that probaly need some javascript in fronted are:
    1. File uploads;
    2. Drag nad drops;
    3. Richtext editors;
3. Javascript for this components should be isolated to this components only and use as litle as posible javascript internaly allowing them to be used inside jinja2 templates or nested withoin other components, without consern about javascript.
4. Creating new components should be straight foward. Only component.py and component.jinja2 need to be created;
5. Adding action to components is matter od adding methods
6. Every component should have its own unique url
7. State of components are:
    1. Configuration: one time when app starts
    2. Initialise: new instance of component for specific request is mounted
    3. Mount: populate component with data
    4. Execution of component logic
    5. Rendering component response
8. Rendering component response is done by response method, that can be called by other component methods or can be avoided all together in which case component will not render itself
9. Comonent is responsible to render itself.
10. Component is removed from page:
    1. When component send empty html response in which case only place holder for component will remain
    2. When parent component remove placeholder of component
11. Every component has its own unique name
12. Page is component (full futured) with its own unique name
13. Application can have multiple page component but only one can be display at user
14. Components comunicate by dispatching events:
    1. Events can be created and dispatched manually 
    2. Every component action, including special render action, will dispatch two event startAction and endAction but can also dispatch errorInAction or notAccessible event
15. Component will have special method isAccessible that will return True or False if false is returned action should dispatch notAccessible event
16. Event can be dispatched to:
    1. everyone who is listening (all previously initialised componets)
    2. only parrent components
    3. only children components
    4. specific component who will be initialised if its not exist
    5. when component recivies event it can prevent its parent/child components to receie this event in calse that event is dispetched to only parrent or child components
17. Every component can accept config parameters that change behavior of that component
    1. Final goal is to behavior change is implementd with metaprograming but for first versions simple conditionals will be sufficient
18. Parent componet can change config parameters of its childrens

19. Application structure should be orginised similar to django projects but without project folder (project folder should be root folder)
/settings
