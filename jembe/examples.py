from typing import Optional, Union
from uuid import UUID
from .jembe import Component, App, page, config, Event, action, listener
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
    """Simple dynamic page that displays different BlogPost
    depending of url it is used
    """

    class Config(Component.Config):
        def __init__(self, url_path="<str:blog_name>", **params):
            super().__init__(url_path=url_path, **params)

    def __init__(self, blog_name: str):
        """
        self.state_params["blog_name"] = blog_name will be set by jembe processor
        Jembe processor will also check if the type and value are valid
        """
        self.blog_post = query(Blog).filter(name=blog_name).first()

    # def mount(self):
    #     self.blog_post = query(Blog).filter(name=self.url_params.blog_name).first()

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
    #     self.news = query(News).filter(id=self.url_params.news_id).first()

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
        self.blog_post = query(Blog).get(self.url_params.blog_id)

    # def mount(self):
    #     self.blog_post = query(Blog).get(self.url_params.blog_id)

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
@config()
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
        <nav><a jmb:click="emit_up('close')">Display all blogs</a></nav>
        Ver 2, finds component on page via javascript and call action of that component:
        <nav><a jmb:click="component('..', key=None).call('display')">Display all blogs</a></nav>
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
        orderby, pagesize, and page are regular state param that can be used query params
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

    # def mount(self):
    #     self.order_by = self.query_params.get("order_by", "-date")
    #     self.page_size = self.query_params.get("page_size", 25)
    #     self.page = self.query_params.get("page", 0)

    #     self.blogs = query(Blog).order_by(self.order_by)[
    #         self.page * self.page_size : (self.page + 1) * self.page_size
    #     ]
    @action
    def next_page(self):
        self.page += 1
        return self.display()

    @action
    def prev_page(self):
        self.page -= 1
        return self.display()

    @action
    def display_blog(self, uuid: "UUID"):
        return self._render_template_string(
            """
                {{component("blog", uuid)}}
            """,
            uuid=uuid,
        )

    @listener
    def _on_close(self, event: "Event"):
        if event.name == "close" and event.source.releative_path(self) == "blog":
            return self.display()

    # @listener("close", ".blog")
    # def _on_close(self, event: "Event"):
    #     return self.display()

    def _url(self) -> str:
        """
        bulding url (window.location) in order to allow navigation bach forward
        and sharing urls
        """
        return self._build_url(
            super.url(),
            oby=self.init_params.order_by,
            psize=self.init_params.page_size,
            p=self.init_params.page,
        )

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
        {%for blog in blogs%}
            <li><a href="#" jmb:click="display_blog(blog.uuid)">{{blog.title}}</li>
        {%%}
        </ul>
        """
        )


####################
# Page with counter
###################
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
        <div>By: <input jmb:model="increase_by" type="number" value="1"></div>
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
                    {{component("counter", increase_by=10)._set_key("first")}}
            </div>
            <div>
                Second: 
                    {{component("counter",  increase_by=2)._set_key("second")}}
            </div>
            <div>
                Third: {{component(
                            "counter", 
                            increase_by=5, 
                            current_value=100
                         )._set_key("third")}}
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
            name=None,
            url_path="edit/<int:id>",
            template=None,
            components=None,
            model: Optional[str] = None,
            form: Optional["Form"] = None,
            **params
        ):
            self.model = model
            self.form = form
            if self.form is None:
                self.form = modelform_factory(self.model)
            super().__init__(
                name=name,
                url_path=url_path,
                template=template,
                components=components,
                **params
            )

    def __init__(self, id: int, form_data: Optional[dict] = None):
        self.id = id
        self.record = query(self._config.model).get(self.id)
        self.form_data = form_data
        self._form_validated = False

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
class NavLink:
    def __init__(
        self,
        component_full_name: Optional[str] = None,
        action_name: str = "display",
        url: Optional[str] = None,
        title: Optional[str] = None,
        description: Optional[str] = None,
        icon: Optional[str] = None,
    ):
        self.component_full_name = (component_full_name,)
        self.action_name = action_name
        # etc


@singleton
class GlobalNavigationService:
    def __init__(self):
        self.links = []

    def add_link(self, link: "NavLink"):
        self.links.append(link)


class GlobalNavigation(Component):
    def display(self):
        return self._render_template_string(
            """
            <ul>
            {% for link in links %}
                <li>
                    <a 
                        jmb:click="component(
                            {{link.action.component_full_name}}
                        ).call(
                            {{link.action.name|default:'display'}}
                        )" 
                        title="{{link.description}}"
                    >
                        {{link.icon}} 
                        {{link.title}}
                    </a>
                </li>
            {% endfor %}
            </ul> 
            """
        )
# TODO create pages that uses and displays global navigation