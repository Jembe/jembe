from typing import TYPE_CHECKING, Optional, Union, List, Any
from jembe import Component, File, listener
from wtforms import Form, BooleanField, FileField, validators
from dapp.jmb import jmb

# from wtforms import Form, FileField


if TYPE_CHECKING:
    from flask import Response
    from jembe import Event


class DemoUploadSimple(Component):
    """
    Uploades files to public or private storage and 
    redisplays itself showing uploaded file
    """

    def __init__(self, photo: Optional[File] = None, upload_to_public: bool = False):
        if photo is not None and photo.in_temp_storage():
            # TODO check if photo is acctual photo
            if upload_to_public:
                photo.move_to_public()
            else:
                photo.move_to_private()
                photo.grant_access()

        if photo and photo.in_temp_storage():
            self.state.photo = None
        super().__init__()


class MultiUploadSimple(Component):
    """
    Uploades multipe files to public or private storage and 
    redisplays itself showing uploaded file
    """

    def __init__(
        self, photos: Optional[List[File]] = None, upload_to_public: bool = True
    ):
        if photos is not None:
            for photo in photos:
                if photo.in_temp_storage():
                    # TODO check if photo is acctual photo
                    if upload_to_public:
                        photo.move_to_public()
                    else:
                        photo.move_to_private()
                        photo.grant_access()
        else:
            self.state.photos = list()
        super().__init__()


class PhotoForm(Form):
    photo = FileField("Photo", [validators.regexp("^[^/\\]\.[jpg|png]$")])
    upload_to_public = BooleanField(
        "Upload to public storage", [validators.input_required()], default=True
    )


class DemoUploadWtForm(Component):
    """Uses wtForm and simulates saving to database by processing photo in save() action"""

    def __init__(self, form: Optional[PhotoForm] = None):
        if form is None:
            form = PhotoForm()

        if (
            form.photo.data is not None
            and form.photo.data.in_temp_storage()
        ):
            if form.upload_to_public.data:
                form.photo.data.move_to_public()
            else:
                form.photo.data.move_to_private()
                form.photo.data.grant_access()
        self.state.form = form
        super().__init__()

    @classmethod
    def dump_init_param(cls, name: str, value: Any) -> Any:
        if name == "form":
            result = value.data.copy() if value is not None else dict()
            if "photo" in result and result["photo"] is not None:
                result ["photo"] = File.dump_init_param(result ["photo"])
            return result 
        return super().dump_init_param(name, value)  # type:ignore

    @classmethod
    def load_init_param(cls, name: str, value: Any) -> Any:
        if name == "form":
            if "photo" in value and value["photo"] is not None:
                value["photo"] = File.load_init_param(value["photo"])
            return PhotoForm(data=value)
        return super().load_init_param(name, value)  # type:ignore

@jmb.page(
    "demo_upload",
    Component.Config(
        components=dict(
            simple=DemoUploadSimple, wtform=DemoUploadWtForm, multi=MultiUploadSimple
        )
    ),
)
class DemoUploadPage(Component):
    def __init__(self, display_mode: str = "simple"):
        if display_mode not in self._config.components_configs.keys():
            self.state.display_mode = list(self._config.components_configs.keys())[0]
        super().__init__()

    @listener(event="_display", source="./*")
    def on_child_display(self, event: "Event"):
        self.state.display_mode = event.source_name

    def display(self) -> Union[str, "Response"]:
        return self.render_template_string(
            """
            <html>
            <head>
                <link rel="stylesheet" href="{{ url_for('static', filename='css/dapp.css') }}">
            </head>
            <body>
            <nav>
                <a href="{{component('simple').url}}" jmb-on:click="{{component().jrl}};$event.stopPropagation();$event.preventDefault();">Simple Upload</a>
                <a href="{{component('multi').url}}" jmb-on:click="{{component().jrl}};$event.stopPropagation();$event.preventDefault();">Multiple Upload</a>
                <a href="{{component('wtform').url}}" jmb-on:click="{{component().jrl}};$event.stopPropagation();$event.preventDefault();">WTForm Upload</a>
            </nav>
            {{component(display_mode)}}

            <script src="{{ url_for('jembe.static', filename='js/jembe.js') }}"></script>
            </body><html>"""
        )
