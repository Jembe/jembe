from dataclasses import dataclass
from typing import Optional
from jembe import Component
from wtforms import Form, FileField

# when displaying file it needs file url (file name can be obtained from url)
class JmbFileField(FileField):
    @property
    def jfile(self) -> Optional["JFile"]:
        return JFile("tmp", "file_path")

    @property
    def file_path(self) -> Optional[str]:
        return "full_file_path"


@dataclass
class JFile:
    storage_name: str
    file_path: str

    def __str__(self) -> str:
        return "{}:{}".format(self.storage_name, self.file_path)


class EditForm(Form):
    photo = JmbFileField()


class EditFile(Component):
    def __init__(self, form: Optional[EditForm] = None, file: Optional[JFile] = None):
        super().__init__()

    def save(self):
        if self.state.file.is_uploaded:
            self.state.file = self.state.file.moveto(
                self.get_storage("private"), to="test"
            )
        if self.state.form.is_valid():
            if self.form.photo.jfile.is_uploaded:
                jfile = self.get_storage("private").movein(
                    self.form.photo.jfile, to="test"
                )
                project.photo = jfile

                """{{project.photo|jfile_url}}"""
