from typing import Sequence, TYPE_CHECKING, Optional, Union, List
from jembe.component_config import listener
from dataclasses import dataclass
from jembe import Component, File
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


class DemoUploadWtForm(Component):
    """Uses wtForm and simulates saving to database by processing phot in save() action"""

    pass
    # def __init__(self, form: Optional[EditForm] = None, file: Optional[JFile] = None):
    #     super().__init__()

    # def save(self):
    #     if self.state.file.is_uploaded:
    #         self.state.file = self.state.file.moveto(
    #             self.get_storage("private"), to="test"
    #         )
    #     if self.state.form.is_valid():
    #         if self.form.photo.jfile.is_uploaded:
    #             jfile = self.get_storage("private").movein(
    #                 self.form.photo.jfile, to="test"
    #             )
    #             project.photo = jfile

    #             """{{project.photo|jfile_url}}"""


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
            <html><body>
            <nav>
                <a href="{{component('simple').url}}" jmb:on.click="{{component().jrl}};$event.stopPropagation();$event.preventDefault();">Simple Upload</a>
                <a href="{{component('multi').url}}" jmb:on.click="{{component().jrl}};$event.stopPropagation();$event.preventDefault();">Multiple Upload</a>
                <a href="{{component('wtform').url}}" jmb:on.click="{{component().jrl}};$event.stopPropagation();$event.preventDefault();">WTForm Upload</a>
            </nav>
            {{component(display_mode)}}

            <script src="{{ url_for('jembe.static', filename='js/jembe.js') }}"></script>
            </body><html>"""
        )
