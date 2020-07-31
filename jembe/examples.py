from typing import Optional, Union, Sequence, Dict, Callable, List, Any
from collections import namedtuple
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
    execute_last,
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

    class Config(Component.Config):
        def __init__(self, url_path="<str:blog_name>", **params):
            super().__init__(url_path=url_path, **params)

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
App.add_page(
    "blogpost2", BlogPostPage, BlogPostPage.Config(url_path="blogpost2/<str:blog_name>")
)


@page("news", Component.Config(url_path="<int:news_id>"))
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
        return self._render_template_string(
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
        return self._render_template_string(
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

        return self._render_template_string(
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
        return self._render_template_string(
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
        # <div>By: <input value="{{increase_by}}" onchange="$set('increase_by', $this.value)" type="number"></div>
        # $this is magic property that reference javascript current element
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
        return self._render_template_string(
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
            **params
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
        return self._render_template_string(
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

    @property
    def jrl(self):
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
        items: Sequence[Union["Menu", "JRL"]] = ()
    ):
        self.name = name
        self.title = title
        self.help_text = help_text
        self.icon = icon
        self.items:list = list(items)

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
        # TODO add to BreadCrumbService also

    def get_menu_path(self, component_full_name: str) -> Sequence[Union["Menu", "JRL"]]:
        """
        Used by breadcrumb service to get menupath of current component
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
        return self._render_template_string(
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
            return self._render_template_string(
                """
                ...
                {{component("global_navigation")}}
                {{component(init_params.component_name)}}
                ...
                """
            )
        else:
            return self._render_template_string(
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
            return self._render_template_string(
                """
                ...
                {{component("global_navigation")}}
                {{component(init_params.component_name)}}
                ...
                """
            )
        else:
            return self._render_template_string(
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
    Menu("main", items=[
        JRL("invoices", "/main2_gn/invoices"),
        JRL("customers", "/main2_gn/customers"),
    ]),
    Menu("settings", "Settings")
)

GlobalNavigationService().add(
    JRL("users", "/setting2_gn/users"),
    JRL("groups", "/setting2_gn/groups"),
    at="settings",  # at_start, before, after
)
# No module name in full name
# It is simpler to just use convencition that prefix page names with
# "module" name like "jembeui_users", "jembeui_main", "finance_main", "finance_settings" etc.

# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

Crumb = namedtuple("Crumb", ["title", "jrl"])


class Breadcrumb:
    def __init__(
        self,
        component_full_name: str,
        get_crumbs: Callable[["Component"], Sequence[Crumb]]
        # get_title: Union[str, Callable[["Component"], str]],
        # get_url: Optional[Union[str, Callable[["Component"], str]]] = None,
    ):
        """
        component_full_name must start with /
        """
        self.component_full_name = component_full_name

    @classmethod
    def init_for_global_menu(cls, menu_name: str) -> Breadcrumb:
        jrl = GlobalNavigationService().get_item(menu_name)
        return cls(jrl.component_full_name, cls.get_crumbs_from_global_menu)

    @classmethod
    def get_crumbs_from_global_menu(cls, component: "Component") -> Sequence[Crumb]:
        gns = GlobalNavigationService()
        menu_path: Sequence[Union["Menu", "JRL"]] = gns.get_menu_path(
            component._config.full_name
        )

        # TODO if item is component or item is parent menu
        return [Crumb(item.title, item.jrl) for item in menu_path]


@singleton
class GlobalBreadcrumbService:
    def __init__(self):
        # [full_name, Breadcrumb]
        self.breadcrumbs: Dict[str, "Breadcrumb"] = {}

    def add(self, *breadcrumbs: "Breadcrumb"):
        for breadcrumb in breadcrumbs:
            self.breadcrumbs[breadcrumb.component_full_name] = breadcrumb

    def get_crumbs(self) -> Sequence[Crumb]:
        """ returns crumbs for current app"""
        # PROBLEM how to execute this after all components are processed
        # for component in jembe_processor.all_commponents:
        #     find component with depeast full_name associated with bread crumbs
        # cmps =jembe_processor.get_component_chain(depest_component)
        # crumbs = []
        # for c inf cmps:
        #     bc = find breadcrubm where c.full_name == bc.component_full_name
        #     crumbs.extend(bc.get_crumbs(c))
        # return crumbs
        raise NotImplementedError()


class BreadcrumbComponent(Component):
    @execute_last
    def display(self):
        gbs = GlobalBreadcrumbService()
        return self._render_template_string(
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
            crumbs=gns.get_crumbs(),
        )


# Breadcrumb ??
# every componet has its breadcrumb name acuired from init params
# every component can have title that is used for breadcrumb
GlobalBreadcrumbService().add(
    Breadcrumb.init_for_global_menu("main.user"),
    Breadcrumb.init_for_global_menu("main.groups"),
    Breadcrumb.init_for_global_menu("main.invoices"),
    Breadcrumb.init_for_global_menu("main.customers"),
    Breadcrumb(
        "/myapp/codebook/countries",
        lambda component: [
            Crumb("Settings", None),
            Crumb(component.title, component.jrl),
        ],
    ),
    # Settings > Countries > France
    Breadcrumb(
        "/myapp/codebook/countries/1",
        lambda component: [Crumb(component.title, component.jrl)],
    ),
    # Settings > Countries > France > Paris
    Breadcrumb(
        "/myapp/codebook/countries/1/cities/3"
    ),  # default to lambda c: [Crumb(c.title, c.jrl)]
    Breadcrumb("/main/users", _("Users")),
    Breadcrumb(
        "/main/users/view",
        lambda component: [Crumb("View {}".format(component.user), component.jrl)],
    ),
    Breadcrumb("/main/users/edit"),
)
