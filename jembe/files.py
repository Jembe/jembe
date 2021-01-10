from typing import Dict, Union
from enum import Enum
from dataclasses import dataclass

from flask.helpers import send_from_directory
from flask import session
from .exceptions import NotFound

JEMBE_FILES_ACCESS_GRANTED = "jembe_files_access_granted"
JEMBE_FILES_ACCESS_GRANTED_MAX_SIZE = 500


def grant_access_to_file(storage_name: str, file_path: str):
    try:
        if file_path not in session[JEMBE_FILES_ACCESS_GRANTED][storage_name]:
            session[JEMBE_FILES_ACCESS_GRANTED][storage_name].insert(0, file_path)

        if (
            len(session[JEMBE_FILES_ACCESS_GRANTED])
            > JEMBE_FILES_ACCESS_GRANTED_MAX_SIZE
        ):
            session[JEMBE_FILES_ACCESS_GRANTED] = session[JEMBE_FILES_ACCESS_GRANTED][
                :JEMBE_FILES_ACCESS_GRANTED_MAX_SIZE
            ]
    except KeyError:
        if JEMBE_FILES_ACCESS_GRANTED not in session:
            session[JEMBE_FILES_ACCESS_GRANTED] = dict()
        if storage_name not in session[JEMBE_FILES_ACCESS_GRANTED]:
            session[JEMBE_FILES_ACCESS_GRANTED][storage_name] = list()
        session[JEMBE_FILES_ACCESS_GRANTED][storage_name].insert(0, file_path)


def is_access_granted_to_file(storage_name, file_path):
    return file_path in session.get(JEMBE_FILES_ACCESS_GRANTED, dict()).get(
        storage_name, list()
    )


@dataclass
class JmbFile:
    storage: str
    path: str

@dataclass
class Storage:
    class Type(Enum):
        PUBLIC = "public"
        PRIVATE = "private"
        TEMP = "temp"

    name: str
    folder: str
    type: Type = Type.PUBLIC

    def is_file_accessible(self, file_path: str):
        if self.type == self.Type.TEMP:
            return False
        elif self.type == self.Type.PUBLIC:
            return True
        elif self.type == self.Type.PRIVATE:
            return is_access_granted_to_file(self.name, file_path)
        raise NotImplementedError()

    def send_file(self, file_path: str):
        if self.is_file_accessible(file_path):
            return send_from_directory(self.folder, file_path)
        raise NotFound

    def movein(self, file: Union[JmbFile, str], dir: str = ""):
        """Moves file inside this storage dir with unique file name"""
        raise NotImplementedError()

    def copyin(self, file: Union[JmbFile, str], dir: str = ""):
        """Copies file inside this storage dir with unique file name"""
        raise NotImplementedError()
