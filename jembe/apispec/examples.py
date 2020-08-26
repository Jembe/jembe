from typing import Optional, Union, Sequence, Dict, Callable, List, Any, Tuple, Type
import datetime
from collections import namedtuple
from itertools import chain
from uuid import UUID
from .jembe import (
    Component,
    App,
    page,
    config,
    Event,
    action,
    listener,
    singleton,
)
from .utils import *
from flask import session


class Page(Component):
    """
    Simple static page

    Page template should be implicitly defined
    """

    pass


App.add_page("welcome", Page)
App.add_page("welcome", Page, Page.Config(template="welcome.jinja2"))
App.add_page("static_page", Component, Component.Config(template="static_page.jinja2"))


class PageWithTemplate(Component):
    """
    Simple static page with explict template 
    """

    class Config(Component.Config):
        def __init__(self, template="default_template.jinja2", **params):
            super().__init__(template=template, **params)


App.add_page("welcome2", PageWithTemplate)


@page("welcome3", Component.Config(template="welcome2.jinja2"))
class PageWithTemplate2(Component):
    pass


class PageMultipleTemplates(Component):
    @action
    def display(self):
        if session.user.is_superuser:
            return self._render_template("superuser_page.jinja2")
        return self._render_template(self._config.template)


App.add_page("mtpage", PageMultipleTemplates)


class BlogPostPage(Component):
    """
    Simple dynamic page that displays different BlogPost
    depending of url it is used
    """

    def __init__(self, blog_name: str):
        """
        self.init_params["blog_name"] = blog_name will be set by jembe processor
        Jembe processor will also check if the type and value are valid
        """
        self.blog_post = query(Blog).filter(name=blog_name).first()

    # def mount(self):
    #     self.blog_post = query(Blog).filter(name=self.init_params.blog_name).first()

    # blogpostpage.jinja2:
    # <div>{{blog_post.name}}</div><div>{{blog_post.content}}</div>


App.add_page("blogpost", BlogPostPage)
# set new blog post with different url_path
App.add_page( "blogpost2", BlogPostPage)


@page("news")
class NewsPage(Component):
    """
    Simple page that displays different News
    depending of url parameter
    """

    def __init__(self, news_id: int):
        self.news = query(News).filter(id=news_id).first()

    # def mount(self):
    #     self.news = query(News).filter(id=self.init_params.news_id).first()

    # def display(self):
    #     return self.render_template_string("""
    #     <h1>{{news.title}}</h1>
    #     <div>{{news.content}}</div>
    #     """)


@page("blogpostinline")
class BlogPostWithInlineTemplatePage(Component):
    # class Config(Component.Config):
    #     def __init__(self, url_path="<int:blog_id>", **params):
    #         super().__init__(url_path=url_path, **params)

    def __init__(self, blog_id: int):
        """Url path is created by default as <int:blog_id>"""
        self.blog_post = query(Blog).get(blog_id)

    # def mount(self):
    #     self.blog_post = query(Blog).get(self.init_params.blog_id)

    @action
    def display(self):
        return self.render_template_string(
            """
            <h1>{{blog_post.title}}</h1>
            <div>{{blog_post.content}}</div>
            """
        )


####################
# SimpleBlog with list and view
###################
# @config(Component.Config(url_path="<uuid:news_uuid>"))
class ViewBlogPost(Component):
    # def mount(self):
    #     self.blog_post = query(Blog).filter(uuid=self.url_params.news_uuid).first()
    def __init__(self, blog_uuid: "UUID", _blog: Optional["Blog"] = None):
        """
        blog_uuid is url_param
        _blog is performance param and will not be part of state_params
        """
        self.blog_post = (
            query(Blog).filter(uuid=blog_uuid).first() if not _blog else _blog
        )

    # render uses view_blog_post.jinja2 template by default
    @action
    def display(self):
        # TODO how to link to display of parent
        return self.render_template_string(
            """
        Ver 1:
        <nav><a jmb:click="$emit_up('close')">Display all blogs</a></nav>
        Ver 2, finds component on page via javascript and call action of that component 
        if component cant be found submits request to compoent with empty existing model data:
        # <nav><a jmb:click="$component('..').key(null).call('display')">Display all blogs</a></nav>
        <nav><a jmb:click="$component('..')">Display all blogs</a></nav>

        <h2>{{blog_post.title}}</h2>
        <div>{{blog_post.content}}</div>

        """
        )


@page("blog", Component.Config(components={"blog": ViewBlogPost}))
class Blog(Component):
    def __init__(
        self,
        order_by: Optional[str] = None,
        page_size: Optional[int] = None,
        page: Optional[int] = None,
    ):
        """
        orderby, pagesize, and page are regular state param that can be used as query params
        """
        self.order_by = (
            order_by if order_by is not None else self.get_query_param("oby", "-id")
        )
        self.page_size = (
            page_size
            if page_size is not None
            else int(self.get_query_param("psize", 25))
        )
        self.page = page if page is not None else int(self.get_query_param("p", 25))

    def url(self) -> str:
        """
        bulding url (window.location) in order to allow navigation bach forward
        and sharing urls
        """
        return build_url(
            super.url(),
            oby=self.init_params.order_by,
            psize=self.init_params.page_size,
            p=self.init_params.page,
        )

    @action
    def next_page(self):
        self.page += 1
        return self.display()

    @action
    def prev_page(self):
        self.page -= 1
        return self.display()

    # @listener
    # def on_close(self, event: "Event"):
    #     if event.name == "close" and event.source.releative_path(self) == "blog":
    #         return self.display()

    # @listener("close", "blog")
    # def on_close(self, event: "Event"):
    #     return self.display()

    @action
    def display(self):
        self.blogs = query(Blog).order_by(self.order_by)[
            self.page * self.page_size : (self.page + 1) * self.page_size
        ]

        return self.render_template_string(
            """
            <a href="#" jmb:click="next_page()">Prev</a> 
            <a href="#" jmb:click="prev_page()">Next</a> 
            <ul>
            # {% for blog in blogs %}
            #     <li><a href="#" jmb:click="display_blog(blog.uuid)">{{blog.title}}</li>
            # {% endfor %}
            {% for blog in blogs %}
                <li><a href="#" jmb:click="$component("blog", uuid=blog.uuid)">{{blog.title}}</li>
            {% endfor %}
            </ul>
        """
        )

    # @listener
    # def on_display_blog(self, event: "Event"):
    #     if event.name == "display" and event.source.releative_path(self) == "blog":
    #         ....
    @listener("display", "blog")
    def on_display_blog(self, event: "Event"):
        return self.render_template_string(
            """
            {{component(blog_component)}}
            """,
            blog_component=event.source,
        )


####################
# Page with counter
###################
# @page("counter", Component.Config(components={"counter": Counter}))
@page("counter")
class CounterPage(Component):
    class Config(Component.Config):
        def __init__(
            self, components={"counter": (Counter, Counter.Config())}, **params
        ):
            super().__init__(components=components, **params)

    # since display is defautl action we dont need to mark it as action via decorator
    def display(self):
        return self.render_template_string(
            """
            {{component("counter")}}
            """
        )


class Counter(Component):
    def __init__(
        self, counter: Optional[int] = None, increase_by: Optional[int] = None
    ):
        self.counter = counter if counter is not None else session.get("counter", 0)
        self.increase_by = (
            increase_by if increase_by is not None else session.get("increase_by", 1)
        )

    @action
    def increase(self, by: int = 1):
        self.counter += by
        session["counter"] = self.counter
        self.display()

    def display(self):
        return self.render_template_string(
            """
        <div>{{counter}}</div>
        <button jmb:click="increase({{increase_by}})" type="button">Increase</button>
        <div>By: <input jmb:model="increase_by" type="number"></div>
        # <div>By: <input value="{{increase_by}}" onchange="$update('increase_by', $elm.value)" type="number"></div>
        # $elm is magic property that reference javascript current element
        # $set will chage init property of component and call display of that component via ajax
        <button jmb:click="increase(10)" type="button">Increase by 10</button>
        """
        )


@page("counter2", Component.Config(components={"counter": Counter2}))
class Counter2Page(Component):
    """preset multiple counters by parent page"""

    def display(self):
        return self.render_template_string(
            """
            <div>
                First: 
                    {{component("counter", increase_by=10).key("first")}}
            </div>
            <div>
                Second: 
                    {{component("counter", increase_by=2).key("second")}}
            </div>
            <div>
                Third: {{component(
                            "counter", 
                            increase_by=5, 
                            current_value=100
                         ).key("third")}}
            </div>
        """
        )


class Counter2(Component):
    def __init__(
        self, increase_by: Optional[int] = 1, current_value: Optional[int] = 0,
    ):
        self.increase_by = increase_by
        self.current_value = current_value

    @action
    def increase(self):
        self.current_value += self.increase_by
        return self.display()

    def display(self):
        return self.render_template_string(
            """
            <div>Value: {{current_value}}</div>
            <button jmb:click="increase()" type="button">Increase</button>
            <label>Increase by: <input jmb:model="increase_by" type="number"></label>
        """
        )


class EditRecord(Component):
    class Config(Component.Config):
        def __init__(
            self,
            url_path: Optional[str] = None,
            model: Optional[str] = None,
            form: Optional["Form"] = None,
            **params,
        ):
            self.model = model
            self.form = form
            if self.form is None:
                self.form = modelform_factory(self.model)
            if self.url_path is None:
                self.url_path = "edit/<int:id>"
            super().__init__(url_path=url_path, **params)

    def __init__(self, id: int, form_data: Optional[dict] = None):
        self.id = id
        self.record = query(self._config.model).get(self.id)
        self.form_data: dict = form_data if form_data is not None else {}
        # self._form_validated = False

    @action
    def save(self):
        # TODO how to post all form data and form files???
        # Should use WTForm or just send raw data and
        # use model paradigm of component
        #
        # model data can not handle file uploads or it will be
        # realy complicated to do
        #
        # On the other side using model data to submit form __init__(form_data:dict=None)
        # will allow partial form validation as you type and instant form save
        # without need to press save but can requre a loot of custom coding
        # which defines purpuse for building apps really fast

        # TODO create custom service in background for handling
        # file fields in form similar to jembe 0.1 branch

        self.form = self._config.form(self.form_data, self.record)
        if self.form.validate():
            self.form.populate_obj(self.record)
            self.record.save()
            self.emit_up("save_success", record=self.record)
        else:
            return self.display()

    def display(self):
        if not hasattr(self, "form"):
            self.form = self._config.form(self.form_data, self.record)
            if self.form_data:
                self.form.validate()
        return self.render_template_string(
            """
            <form jmb:submit.prevent="save()" jmb:model="form_data">
                {% for field in form.fields %}
                <div>{{field.label}}: {{field()}}</div>
                {% endfor %}
            </form>
            """
        )


###################
# Global navigation
###################
class NavigationItem:
    @property
    def is_link(self) -> bool:
        raise NotImplementedError()

    @property
    def is_menu(self) -> bool:
        return not self.is_link

    @property
    def jrl(self) -> Optional[str]:
        return None


class JRL(NavigationItem):
    """
    Jembe URL can reference some action inside jembe component
    or a regular URL
    """

    def __init__(
        self,
        name: str,
        component_full_name: Optional[str] = None,
        components_params: Sequence[Dict[str, Any]] = (),
        components_keys: Sequence[Optional[str]] = (),
        action_name: str = "display",
        action_params: Optional[Dict[str, Any]] = None,
        url: Optional[str] = None,
        target: str = "_blank",
        title: Optional[str] = None,
        help_text: Optional[str] = None,
        icon: Optional[str] = None,
    ):
        if (url is not None and component_full_name is not None) or (
            url is None and component_full_name is None
        ):
            raise ValueError()
        self.name = name
        self.component_full_name = component_full_name
        self.components_params = components_params
        self.components_keys = components_keys
        self.action_name = action_name
        self.action_params = action_params
        self.url = url
        self.target = target
        self.title = title
        self.help_text = help_text
        self.icon = icon

    @property
    def jrl(self) -> Optional[str]:
        if self.url:
            return (
                '$url({}, target="{}")'.format(self.url, self.target)
                if self.target
                else "$url({})".format(self.url)
            )
        else:
            # TODO add support for component and action params
            # $component("first",**params).component("second", **params)..call("action",**params)
            return '$component("{}").call("{}")'.format(
                self.component_full_name, self.action_name
            )

    @property
    def is_link(self) -> bool:
        return True


class Menu(NavigationItem):
    def __init__(
        self,
        name: str,
        title: Optional[str] = None,
        help_text: Optional[str] = None,
        icon: Optional[str] = None,
        items: Sequence[Union["Menu", "JRL"]] = (),
    ):
        self.name = name
        self.title = title
        self.help_text = help_text
        self.icon = icon
        self.items: list = list(items)

    @property
    def is_link(self) -> bool:
        return False


@singleton
class GlobalNavigationService:
    def __init__(self):
        self.items = []
        self.items_by_name: Dict[
            str, Union["Menu", "JRL"]
        ] = {}  # ["main/users"] = JRL; ["main"] = Menu

    def add(
        self,
        *items: Union["Menu", "JRL"],
        at: Optional[str] = None,
        at_start: Optional[str] = None,
        before: Optional[str] = None,
        after: Optional[str] = None,
    ):
        if (
            sum(
                [
                    at is not None,
                    at_start is not None,
                    before is not None,
                    after is not None,
                ]
            )
            > 1
        ):
            raise ValueError(
                "Only one of at, at_start, before and after attributes can be used"
            )
        # TODO add support for at, at_start, before and after
        self.items.extends(items)

        # # Add to BreadCrumbService also
        # for item in items:
        #     if item.component_full_name is not None:
        #         GlobalBreadcrumbService().add(
        #             Breadcrumb.init_for_global_menu(item.component_full_name)
        #         )

    def get(self, menu_full_name: str) -> Union["JRL", "Menu"]:
        """Returns menu item with supplied manu_full_name"""
        # example: get("/main/auth/users")
        raise NotImplementedError()

    def get_menu_path(
        self, component_full_name: str, partial=False
    ) -> Sequence[Union["Menu", "JRL"]]:
        """
        Used by breadcrumb service to get menupath of current component
        partial = True returns menu path from previous componet JRL item to componet_full_name component
        """
        raise NotImplementedError()
        # pseudo
        # depest_menu_name =""
        # for menu_name, item in menu:
        #    if (item is componentLink and
        #        component_full_name.startswith(item.component_full_name + "/") and
        #        len(menu_name.split("/")) > len(depest_menu_name.split("/"))):
        #      depest_menu_name = menu_name
        # path = []
        # childs = self.items
        # for name in depest_menu_name.split("/"):
        #   item = next(c for c in childs if c.name == name)
        #   if item is menu:
        #       childs = item.childs
        #   path.append(item)
        # return path


class GlobalNavigation(Component):
    def __init__(self):
        self.items = GlobalNavigationService().items

    # its deffered so that we are able to mark active menu state
    @action(deferred=True)
    def display(self):
        # pseudo not working:
        return self.render_template_string(
            """
            <ul>
            {% for item in items %}
                {% if item.is_link %}
                    <li>
                        <a 
                            jmb:click="{{item.jrl}}
                            title="{{item.help_text}}"
                        >
                            {{item.icon}} {{item.title}}
                        </a>
                    </li>
                {% else %}
                    <ul>
                        {{item.title}} {{item.help_text}} {{item.icon}}
                        # display for menu_item in item.items
                    </ul>
                {% endif %}
            {% endfor %}
            </ul> 
            """
        )


# $component
# $ -- means that is javascript magic request
# $component(name, **params).key(name).call(name, **params) will always send
# name of the source component that invoked request and all existing component on the page
# allowing processor to determine if whole page should be rendered
# or just specific requested component
#
# When $component needs to initialse params for parents components etc. it should use syntax
# $component("/main").component(
#   "whatever", param1=1, param2=2
# ).key("whatever_key_name").component(
#   "user", id=123
# ).call("display", param1=1..)

# Component link for above component will be
# JRL("somename", "/main/whatever/user", (
#       {},
#       {"param1":1, "param2":2},
#       {"user"}
#   ), (None, "whatever_key_name", None), "display", {"param1": 1, ...})

#
# $component(name) without call will execute .call("display") without params

# TODO create pages that uses and displays global navigation
########
# Create two page with components to simulate usage of global navigation
########
class UsersComponentGN(Component):
    pass


class GroupsComponentGN(Component):
    pass


class InvoicesComponentGN(Component):
    pass


class CustomersComponentGN(Component):
    pass


@page(
    "settings2_gn",
    Component.Config(
        components={
            "global_navigation": GlobalNavigation,
            "users": UsersComponentGN,
            "groups": GroupsComponentGN,
        }
    ),
)
class Settings2PageGN(Component):
    def __init__(self, component_name: Optional[str] = None):
        self._updated_component_name: Optional[str] = None
        super().__init__()

    # events beginig with _ are jembe system events
    # _render event is fired when any component action renders template response
    @listener("_render", children=True)
    def on_render_child(self, event: "Event"):
        direct_child_name = direct_child_name(self, event.source)
        if (
            self._updated_component_name is not None
            and self._updated_component_name != direct_child_name
        ) or direct_child_name == "global_navigation":
            raise ValueError()

        self._updated_component_name = direct_child_name
        self.init_params["component_name"] = direct_child_name

    def display(self):
        if self.init_params["component_name"]:
            return self.render_template_string(
                """
                ...
                {{component("global_navigation")}}
                {{component(init_params.component_name)}}
                ...
                """
            )
        else:
            return self.render_template_string(
                """
                ...
                {{component("global_navigation")}}
                ver 1:
                <div>Dashboard of some sort</div>
                ver 2:
                Display default users
                {{component("users")}}
                ...
                """
            )


# component() jinja2 funciton :
# component(name) will initialise and render component "name" with no params or
# with params obtained from url if this component that calls 'name' is primary component
# comonent_raw(name) will ignore url params even if thay exist

# component(name).key(name).call(name) will not execute if via ajax request
# same component already exist on page instead component that already exist on
# the page will be rendered ...
# comonent().call(name).force() will force componet to rerender itself event if
# it already exist on the page


@page(
    "main2_gn",
    Component.Config(
        components={
            "global_navigation": GlobalNavigation,
            "invoices": InvoicesComponentGN,
            "customers": CustomersComponentGN,
        }
    ),
)
class Main2PageGN(Component):
    def __init__(self, component_name: Optional[str] = None):
        self._updated_component_name: Optional[str] = None
        super().__init__()

    @listener("_render", children=True)
    def on_render_child(self, event: "Event"):
        self.init_params["component_name"] = direct_child_name(self, event.source)
        # # add checks for invalid behavior
        # direct_child_name = direct_child_name(self, event.source)
        # if (
        #     self._updated_component_name is not None
        #     and self._updated_component_name != direct_child_name
        # ) or direct_child_name == "global_navigation":
        #     raise ValueError()
        # self._updated_component_name = direct_child_name
        # self.init_params["component_name"] = direct_child_name

    def display(self):
        if self.init_params["component_name"]:
            return self.render_template_string(
                """
                ...
                {{component("global_navigation")}}
                {{component(init_params.component_name)}}
                ...
                """
            )
        else:
            return self.render_template_string(
                """
                ...
                {{component("global_navigation")}}
                ver 1:
                <div>Dashboard of some sort</div>
                ver 2:
                Display default users
                {{component("invoices")}}
                ...
                """
            )


GlobalNavigationService().add(
    Menu(
        "main",
        items=[
            JRL("invoices", "/main2_gn/invoices"),
            JRL("customers", "/main2_gn/customers"),
        ],
    ),
    Menu("settings", "Settings"),
)

GlobalNavigationService().add(
    JRL("users", "/setting2_gn/users"),
    JRL("groups", "/setting2_gn/groups"),
    at="settings",  # at_start, before, after
)
# No module name in full name
# It is simpler to just use convencition that prefix page names with
# "module" name like "jembeui_users", "jembeui_main", "finance_main", "finance_settings" etc.

Crumb = namedtuple("Crumb", ["title", "jrl"])


class Breadcrumb:
    def __init__(
        self,
        component_full_name: str,
        get_crumbs: Callable[["Component"], Sequence[Crumb]],
    ):
        """
        component_full_name must start with /
        """
        self.component_full_name = component_full_name
        self.get_crumbs = get_crumbs

    @classmethod
    def init_for_global_menu(cls, menu_full_name: str) -> Breadcrumb:
        jrl = GlobalNavigationService().get(menu_full_name)
        if not isinstance(jrl, JRL) or jrl.component_full_name is None:
            raise ValueError()
        return cls(jrl.component_full_name, cls.get_crumbs_from_global_menu)

    @classmethod
    def get_crumbs_from_global_menu(cls, component: "Component") -> Sequence[Crumb]:
        gns = GlobalNavigationService()
        menu_path: Sequence[Union["Menu", "JRL"]] = gns.get_menu_path(
            component._config.full_name, partial=True
        )
        return [Crumb(item.title, item.jrl) for item in menu_path]


@singleton
class GlobalBreadcrumbService:
    def __init__(self):
        # [component_full_name, Breadcrumb]
        self._breadcrumbs: Dict[str, "Breadcrumb"] = {}

    def add(self, *breadcrumbs: "Breadcrumb"):
        for breadcrumb in breadcrumbs:
            self._breadcrumbs[breadcrumb.component_full_name] = breadcrumb

    def get_crumbs(self, component_chain: Sequence["Component"]) -> Sequence[Crumb]:
        return tuple(
            chain(
                self._breadcrumbs[c._config.full_name].get_crumbs(c)
                for c in component_chain
            )
        )


class BreadcrumbComponent(Component):
    def __init__(self):
        self._depest_component_level: int = -1
        self._depest_component = None
        self._components = []
        super().__init__()

    @listener("_render")
    def on_render(self, event: "Event"):
        self._components.append(event.source)
        clevel = component_level(event.source)
        if clevel > self._depest_component_level:
            self._depest_component_level = clevel
            self._depest_component = event.source

    @action(deferred=True)
    def display(self):
        component_chain = sorted(
            [c for c in self._components if is_direct_child(c, self._depest_component)],
            key=component_level,
        )
        crumbs = GlobalBreadcrumbService().get_crumbs(component_chain)
        return self.render_template_string(
            """
                <ul>
                {% for crumb in crumbs %}
                    {% if crumb.jrl%}
                    <li><a jmb:click="{{crumb.jrl}}">{{crumb.title}}</a></li>
                    {% else %}
                    <li>{{crumb.title}}</li>
                    {% endif %}
                {% endfor %}
                </ul>
            """,
            crumbs=crumbs,
        )


class BreadcrumbUI(Breadcrumb):
    def __init__(
        self,
        component_full_name: str,
        get_crumbs: Optional[
            Union[Callable[["Component"], Sequence[Crumb]], str]
        ] = None,
    ):
        if get_crumbs is None:
            get_crumbs = lambda component: Crum(component.title, component.url)
        elif isinstance(get_crumbs, str):
            get_crumbs = lambda component: Crumb(get_crumbs, component.url)
        super().__init__(component_full_name, get_crumbs)


# Breadcrumb ??
# every componet has its breadcrumb name acuired from init params
# every component can have title that is used for breadcrumb
GlobalBreadcrumbService().add(
    Breadcrumb.init_for_global_menu("main.user"),
    Breadcrumb.init_for_global_menu("main.groups"),
    Breadcrumb.init_for_global_menu("main.invoices"),
    Breadcrumb.init_for_global_menu("main.customers"),
    # Settings > Countries
    Breadcrumb(
        "/myapp/codebook/countries",
        lambda component: [
            Crumb("Settings", None),
            Crumb(component.title, component.url),
        ],
    ),
    # Settings > Countries > France
    Breadcrumb(
        "/myapp/codebook/countries/1",
        lambda component: [Crumb(component.title, component.url)],
    ),
    # Settings > Countries > France > Paris
    BreadcrumbUI(
        "/myapp/codebook/countries/1/cities/3"
    ),  # default to lambda c: [Crumb(c.title, c.jrl)]
    BreadcrumbUI("/main/users", "Users"),
    Breadcrumb(
        "/main/users/view",
        lambda component: [Crumb("View {}".format(component.user), component.url)],
    ),
    BreadcrumbUI("/main/users/edit"),
)

# component(name, **params).key(name).call(name, **params) and it equivalent
# $component(name, **params).key(name).call(name, **params)
# should internaly be implemented via events:
# - _initial(parent_component_name, parent_key, component_name, component_key, raise_error=True, params):
#       That will initialise component with component_name and component_key if
#       parent component already exist otherwise it will raise error
# - _call(component_name, component_key, action_name, raise_error=True, params):
#       Will call action of existing component on page if it exist.
#       component with component_name and component_key doesn't exit
#       event will raise error
#
# On execution on every action inside any component jembe will fire following events:
# - _called(source, action_name, action_result): when action is executed
# - _render(source, action_name, action_result): when action returns rendered template string
#
# If component want to execute action of another component it must listen
# for that component _called event in order to get result of execution.
# This is delibrarly hard in order to encurage moving not UI logic out
# of UI components.


# server side date picker component
class DatePickerSS(Component):
    def __init__(
        self,
        name: Optional[str] = None,
        value: Optional["datetime.date"] = None,
        c_open: bool = False,
        c_year: Optional[int] = None,
        c_month: Optional[int] = None,
    ):
        # if name is not set name is equal to key
        self.name = name if name is not None else self._key
        if self.name is None:
            raise ValueError()
        self.init_params["name"] = self.name

        self.value = value
        # if value is not set date open calendar at current month
        # othervise open calendar at month of the value
        open_at_date: "datetime.date" = datetime.date.today() if self.value is None else value
        self.c_year = open_at_date.year if c_year is None else c_year
        self.c_month = (
            open_at_date.month
            if c_month is None or c_month > 12 or c_month < 1
            else c_month
        )
        self.init_params["c_month"] = self.c_month
        self.init_params["c_year"] = self.c_year

        self.error: Optional[str] = None
        super().__init__()

    @action
    def validate(self, date_str: str):
        try:
            self.value = datetime.datetime.strptime(date_str, "dd.MM.YYYY.")
            self.init_params["value"] = self.value
            self.init_params["c_year"] = self.value.year
            self.init_params["c_month"] = self.value.month
            return self.display()
        except ValueError as ve:
            pass

    def display(self):
        return self.render_template_string(
            """
            <input name="{{name}}" type="hidden" value="{{value|datetime("ISO")}}">
            <input type="text" value="{{value|datetime}}" onchange="$call('validate', $elm.value)">
            <button jmb:click="$set('c_open', true)" type="button">open</button>
            {%if error%}<div class="text-red-700">{{error}}</div>{%endif%}
            {% if c_open %}
            <div class="relative jmb:click.away="$set('c_open', false)">
                <div class="absolute right-0 bottom-0..">
                <div> prev month year next</div>
                    <a jmb:click="$set("c_month", $this.c_month - 1)">prev</a>
                    <select onchange="$set("c_month", $elem.value)">
                        <option value="1">January</option>
                        ....
                    </select>
                    <select onchange="$set("c_year", $elem.value)">
                        <option value="1990">1990</option>
                        ....
                    </select>
                    <a jmb:click="$set("c_month", $this.c_month + 1)">next</a>
                <div>
                    ... display calendard
                </div>
                </div>
            </div>
            {%endif%}
            """
        )


@config(EditRecord.Config(model=...))
class EditWithDatepicker(EditRecord):
    """
    EditRecord component should have componets={dateinput: DatepickerSS} defined
    by default.
    So when form uses datepicker widget ... that widget should display field as
        {{component('dateinput', value=record.<date_field_name>).key("<date_field_name>")}}
        if needed DatePickerSS can have init_param form_id to be used on input element to
        associate it with form
    """

    pass


# client side date picker component


class DatePickerCS(Component):
    """
    DatePicker that relies on client side javascript to display calendar etc.
    Usefull for components that cannot be created purlly with html ower wire
    or when you just want to use some javascript library.

    It is easyest to implement this functionality as widget but 
    nevertheless this is implemented as component
    """

    def __init__(
        self, name: Optional[str] = None, value: Optional["datetime.date"] = None,
    ):
        # if name is not set name is equal to key
        self.name = name if name is not None else self._key
        if self.name is None:
            raise ValueError()
        self.init_params["name"] = self.name

        self.value = value
        super().__init__()

    def display(self):
        return self.render_template_string(
            """
            <div x-data="{}" x-init="
                function() {
                    this.fpr = window.flatpickr($refs.input, 
                        {allowInput:true, altInput:true, 
                         altFormat:window.jmbl10n.date_format, locale: window.flatpickrLangCode
                    });
                    return function() {
                        this.fpr.destroy();
                    }
                }
            ">
            <div jmb:ignore>
            # ignore ignores any changes inside this tags made by javascript
            # when rerendering component assumig that new html also has jmb:ignore tag
            # if multiple jmb:ignore tags exists every tag should have unique name
            # like jmb:ignore="<unique_name>"
                <input x-cloak x-ref="input" type="text" name={{name}}
                    {% if value != None %} value="{{value}}"{% endif %}>
                </div>
            </div>
            """
        )


LookupChoice = namedtuple("LookupChoice", ("value", "label"))


class LookupSS(Component):
    """
    Server side lookup form field with search and select
    usage in EditRecord, CreateRecord and similar FormComponents should be like:
        - in Form definition adds LookupSSWidget with choices callable
        - Form Definition add to EditRecord.Config
        - EditRecord Config reads Form definition and adds subcomponents
          to it self field_name:(LookupSS, LookupSS.Config(choices=choices)
        - widget is rendered in form like 
            {{component('field_name', value=record.field_name, name=field_name)}}
    """

    class Config(Component.Config):
        def __init__(
            self,
            choices: Union[
                Callable[[str], Sequence["LookupChoice"]], Sequence["LookupChoice"]
            ] = (),
            **params,
        ):
            self.choices = choices
            super().__init__(**params)

    def __init__(
        self,
        name: Optional[str] = None,
        value: Optional[Any] = None,
        s_open: bool = False,
        s_search: str = "",
    ):
        # consider moving choices to Config if thay will not change on each request

        # if name is not set name is equal to key
        self.name = name if name is not None else self._key
        if self.name is None:
            raise ValueError()
        self.init_params["name"] = self.name

        self.value = value
        self.s_open = s_open
        self.s_search = s_search

        super().__init__()

    def display(self):
        # from choices find label of choice with value == self.value
        self.label = None
        if self.s_open:
            # filter self.init_choices[choices] to be displayed with s_search string
            self.choices = None
        return self.render_template_string(
            """
            <input name="{{name}}" type="hidden" value="{{value}}">
            <div>{{label}}</div>
            <input name="{{name}}-search" value="{{s_search}}" onchange="$set('s_search',event.target.value)">
            {% if s_open %}
            <div x-data="{
                    hightlightNext:function(target){
                        $this.highlighted = target.previous.getAttribute("val")
                    }, 
                    higlighted:null
                }" 
                x-on:keydown.enter="$set('value', $this.higligted)">
                {% for choice in choices %}
                <button jmb:click="$set('value', '{{choice.value}}') type="button" 
                        x-on:keydown.down="higlightNext($event.target)>
                    {{choice.label}}
                </button>
                { % endfor %}
            </div>
            {%endif%}
        """
        )


class LookupEditableSS(Component):
    """
    Server side lookup form field with search, select, create and edit
    Usage similar tu LookupSS with coresponding widget
    """

    class Config(Component.Config):
        def __init__(
            self,
            components: Optional[
                Dict[str, Union[Tuple["Component", "ComponentConfig"], "Component"]]
            ] = None,
            choices: Union[
                Callable[[str], Sequence["LookupChoice"]], Sequence["LookupChoice"]
            ] = (),
            edit_record_component: Union[
                Tuple[Type["Component"], "ComponentConfig"], Type["Component"]
            ] = EditRecord,
            create_record_component: Union[
                Tuple[Type["Component"], "ComponentConfig"], Type["Component"]
            ] = CreateRecord,
            view_record_component: Union[
                Tuple[Type["Component"], "ComponentConfig"], Type["Component"]
            ] = ViewRecord,
            **params,
        ):
            self.choices = choices
            self.edit_record_component = edit_record_component
            self.create_record_component = create_record_component
            self.view_record_component = view_record_component
            # TODO initialise edit create view component config with model
            # if needed
            if components is None:
                components = {}
            components["edit"] = self.edit_record_component
            components["create"] = self.create_record_component
            components["view"] = self.view_record_component
            super().__init__(components=components, **params)

    def __init__(
        self,
        name: Optional[str] = None,
        value: Optional[Any] = None,
        s_open: bool = False,
        s_search: str = "",
        d_view: bool = False,
        d_create: bool = False,
        d_edit: bool = False,
    ):
        # consider moving choices to Config if thay will not change on each request

        # if name is not set name is equal to key
        self.name = name if name is not None else self._key
        if self.name is None:
            raise ValueError()
        self.init_params["name"] = self.name

        self.value = value
        self.s_open = s_open
        self.s_search = s_search
        self.d_view = d_view
        self.d_create = d_create
        self.d_edit = d_edit
        # TODO check that only one of d_view d_create and d_edit can be true

        super().__init__()

    @listener("_called", child=True)
    def on_save(self, event):
        if event.method_name == "save":
            self.value = event.source.init_params["record_id"]
            self.init_params["value"] = self.value
            self.init_params["d_view"] = False
            self.init_params["d_create"] = False
            self.init_params["d_edit"] = False
            # sets self.d_view, d_edit, d_create
            return self.display()

    def display(self):
        # from choices find label of choice with value == self.value
        self.label = None
        if self.s_open:
            # filter self.init_choices[choices] to be displayed with s_search string
            self.choices = None
        return self.render_template_string(
            """
            <input name="{{name}}" type="hidden" value="{{value}}">
            <div>{{label}}</div>
            <input name="{{name}}-search" value="{{s_search}}" onchange="$set('s_search',event.target.value)">
            <button jmb:click="$set('d_view', true)">View</button>
            <button jmb:click="$set('d_edit', true)">Edit</button>
            {% if s_open %}
            <div x-div="{hightlightNext:function(target){
                            $this.highlighted = target.previous.getAttribute("val")
                          }, 
                         higlighted:null}" 
                    x-on:keydown.enter="$set('value', $this.higligted)">
                <button jmb:click="$set('d_create', true) type="button" 
                        x-on:keydown.down="higlightNext($event.target)>
                    Create
                </button>
                {% for choice in choices %}
                <button jmb:click="$set('value', '{{choice.value}}') type="button" 
                        x-on:keydown.down="higlightNext($event.target)>
                        {{choice.label}}
                </button>
                { % endfor %}
            </div>
            {%endif%}
            ### over simplified
            {% if d_view %}
                <div class="MODAL">
                    <button jmb:click="$set("d_view", false)>Close</button>
                    {{component('d_view', record_id=value)}}
                </div>
            {% endif %}
            {% if d_create %}
                <div class="MODAL">
                    <button jmb:click="$set("d_create", false)>Close</button>
                    {{component('d_create')}}
                </div>
            {% endif %}
            {% if d_edit %}
                <div class="MODAL">
                    <button jmb:click="$set("d_edit", false)>Close</button>
                    {{component('d_edit', record_id=value)}}
                </div>
            {% endif %}
        """
        )


# Searchable Grid/Table
class GField:
    """represends grid field"""

    pass


class GFilter:
    """represends grid filter"""

    pass


class GFilterExp(JsonSerializable):
    """represents grid filter expression"""

    pass


class GridBody(Component):
    class Config(Component.Config):
        def __init__(
            self,
            query: Union["Query", Callable[["Component"], "Query"]],
            fields: Sequence[GField] = (),
            **params,
        ):
            self.query = query
            self.fields = fields
            super().__init__(**params,)

        def get_query(
            self,
            component: "Component",
            filter_by: "GFilterExp",
            order_by: Sequence[str],
        ):
            if isinstance(self.query, Query):
                q = self.query
            else:
                q = self.query(component)
            q = filter_by.apply_to(q)
            q = q.order_by(*order_by)
            return q

    def __init__(
        self,
        page_size: int = 10,
        page: int = 0,
        order_by: Sequence[str] = (),
        filter_by: "GFilterExp" = GFilterExp(),
    ):
        self.order_by = order_by
        self.filter_by = filter_by
        self.page_size = page_size
        self.page = page
        super().__init__()

    @action
    def next_page(self):
        self.page += 1
        self.init_params["page"] = self.page
        return self.display()

    @action
    def prev_page(self):
        self.page -= 1
        self.init_params["page"] = self.page
        return self.display()

    def display(self):
        query = self._config.get_query(self, self.filter_by, self.order_by)
        self.data = query.all()
        self.total = query.count()
        self.display_next = self.page * self.page_size < self.total
        self.display_prev = self.page > 0
        return self.render_template_string(
            """
            # over simplified
            {% for field in _config.fields %}
                <th>field</th>
                # with order_by jmb:click="rotate_order_by('{{field.name}}')"

            {%endfor%}
            {%for record in data %}
            <tr>{{record}}</tr>
            {%endfor%}
            {% if display_prev %}
            <a jmb:click="prev_page">prev</a>
            {% endif %}
            {% if display_next %}
            <a jmb:click="next_page">next</a>
            {% endif %}
        """
        )

class GridFilters(Component):
    class Config(Component.Config):
        def __init__(
            self, filters: Sequence[GFilter] = (), **params,
        ):
            self.filters = filters
            super().__init__(**params)

    def __init__(self, filter_by: Optional["GFilterExp"] = None):
        self.filter_by = filter_by if filter_by is not None else self.get_filter_by()
        super().__init__()

    def get_filter_by(self):
        try:
            filter_by_str = self.get_query_param("fby")
            return GFilterExp(self._config.filters, filter_by_str)
        except ValueError:
            return session.get("filter_by", GFilterExp)

    def display(self):
        return self.render_template_string(
            """
            # over simplified
            {% for filter in _config.filters %}
                # render filter with jmb:model="filter_by.<filter_name>" 
                # or onchange="$set("filter_by.<filter_name>", event.target.value)"
            {% endfor %}
        """
        )


class Grid(Component):
    class Config(Component.Config):
        def __init__(
            self,
            query: Union["Query", Callable[["Component"], "Query"]],
            fields: Sequence[GField] = (),
            filters: Sequence[GFilter] = (),
            components=None,
            **params,
        ):
            if components is None:
                components = {}
            components["body"] = (GridBody, GridBody.Config(query=query, fields=fields))
            components["filter"] = (GridFilters, GridFilters.Config(filters=filters))
            # body and filters should not update window.location 
            # only this component shuld do it when any of those two are 
            # deepest components

            super().__init__(
                components=components, **params,
            )

    def __init__(
        self,
        page_size: Optional[int] = None,
        page: Optional[int] = None,
        order_by: Sequence[str] = (),
        filter_by: Optional["GFilterExp"] = None,
    ):
        self.order_by = order_by if order_by is not None else self.get_order_by()
        self.filter_by = filter_by if filter_by is not None else self.get_filter_by()
        self.page_size = page_size if page_size is not None else self.get_page_size()
        self.page = page if page is not None else self.get_page()
        self.init_params["order_by"] = self.order_by
        self.init_params["filter_by"] = self.filter_by
        self.init_params["page"] = self.page
        self.init_params["page_size"] = self.page_size
        session.set("order_by", self.order_by)
        session.set("filter_by", self.order_by)
        session.set("page", self.order_by)
        session.set("page_size", self.order_by)
        super().__init__()

    def get_page_size(self):
        try:
            page_size_str = self.get_query_param("ps")
            return int(page_size_str)
        except ValueError:
            return session.get("page_size", 10)

    def get_page(self):
        try:
            page_str = self.get_query_param("p")
            return int(page_str)
        except ValueError:
            return session.get("page", 0)

    def get_order_by(self):
        try:
            order_by_str = self.get_query_param("oby")
            return order_by_str.split(",")
        except ValueError:
            return session.get("order_by", ("-id"))

    def get_filter_by(self):
        try:
            filter_by_str = self.get_query_param("fby")
            return GFilterExp(self._config.filters, filter_by_str)
        except ValueError:
            return session.get("filter_by", GFilterExp)

    @listener("_render", child=True)
    def on_render(self, event):
        if event.source._config.name == "filters":
            # check if filter_by != event.source.init_params["filter_by"]
            # and then
            self.filter_by = event.source.init_params["filter_by"]
            # TODO update session and init_params
            return self.display()
        elif event.source._config.name == "body":
            # TODO check if any value is different
            # this should be done by jembe directly not explicitly here
            self.filter_by = event.source.init_params["filter_by"]
            self.order_by = event.source.init_params["order_by"]
            self.page = event.source.init_params["page"]
            self.page_size = event.source.init_params["page_size"]
            # TODO update session and init_params
            return self.display()

    def display(self):
        return self.render_template_string(
            """
            {{component("filters", filter_by=filter_by)}}
            {{component(
                "body", 
                filter_by=filter_by, 
                page=page, 
                page_size=page_size, 
                order_by=order_by
             )}}
        """
        )

# how to use grid inside edit record? 
# something like this
# {{component("notes_grid", parent_record_id=init_params.id, _parent_record=record)}}
