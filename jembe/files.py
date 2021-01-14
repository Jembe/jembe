from typing import TYPE_CHECKING, Union
from enum import Enum
from abc import ABC, abstractmethod

from flask.helpers import send_from_directory
from flask import session
from .app import get_storage
from .exceptions import NotFound

if TYPE_CHECKING:
    from flask import Response

JEMBE_FILES_ACCESS_GRANTED = "jembe_files_access_granted"
JEMBE_FILES_ACCESS_GRANTED_MAX_SIZE = 500


class File:
    storage: "Storage"
    path: str

    def __init__(self, storage: Union[str, "Storage"], file_path: str):
        """
        Represents file inside Jembe File Storage

        storage -- instance or the name of the storage
        file_path -- full file path inside the storage.
        """
        self.storage = storage if not isinstance(storage, str) else get_storage(storage)
        self.path = file_path

    @property
    def accessible(self) -> bool:
        return self.storage.can_access_file(self.path)

    def grant_access(self):
        self.storage.grant_access_to_file(self.path)

    def revoke_access(self):
        self.storage.revoke_access_to_file(self.path)

    @abstractmethod
    def copy_to(self, storage: Union["Storage", str], subdir: str = ""):
        raise NotImplementedError()

    @abstractmethod
    def move_to(self, storage: Union["Storage", str], subdir: str = ""):
        raise NotImplementedError()

    @abstractmethod
    def open(
        self,
        mode="r",
        buffering=-1,
        encoding=None,
        errors=None,
        newline=None,
        closefd=True,
        opener=None,
    ):
        raise NotImplementedError()

    @abstractmethod
    def exists(self) -> bool:
        raise NotImplementedError()


class Storage(ABC):
    class Type(Enum):
        PUBLIC = "public"
        PRIVATE = "private"
        TEMP = "temp"

    def __init__(self, name: str, type: Type = Type.PUBLIC):
        """
        Initialise the Jembe Files Storage used
        to store and present uplaoded files/media

        name -- storage name 
        type -- Storage.Type
        """
        self.name = name
        self.type = type

    def can_access_file(self, file_path: str) -> bool:
        """
        Check if file inside storage can be accessed
        by current user using http request
        """
        if self.type == self.Type.TEMP:
            return False
        elif self.type == self.Type.PUBLIC:
            return True
        # private storage
        return file_path in session.get(JEMBE_FILES_ACCESS_GRANTED, dict()).get(
            self.name, list()
        )

    def grant_access_to_file(self, file_path: str):
        """Grants current user access to file"""
        if self.type in (self.Type.PUBLIC, self.Type.TEMP):
            # public already have granted access to all files
            # cannot grant access to temporay file
            return
        # adds file_path to session variable
        try:
            if file_path not in session[JEMBE_FILES_ACCESS_GRANTED][self.name]:
                session[JEMBE_FILES_ACCESS_GRANTED][self.name].insert(0, file_path)

            if (
                len(session[JEMBE_FILES_ACCESS_GRANTED])
                > JEMBE_FILES_ACCESS_GRANTED_MAX_SIZE
            ):
                session[JEMBE_FILES_ACCESS_GRANTED] = session[
                    JEMBE_FILES_ACCESS_GRANTED
                ][:JEMBE_FILES_ACCESS_GRANTED_MAX_SIZE]
        except KeyError:
            if JEMBE_FILES_ACCESS_GRANTED not in session:
                session[JEMBE_FILES_ACCESS_GRANTED] = dict()
            if self.name not in session[JEMBE_FILES_ACCESS_GRANTED]:
                session[JEMBE_FILES_ACCESS_GRANTED][self.name] = list()
            session[JEMBE_FILES_ACCESS_GRANTED][self.name].insert(0, file_path)

    def revoke_access_to_file(self, file_path: str):
        """Reveke access to file from current user"""
        if self.type in (self.Type.PUBLIC, self.Type.TEMP):
            # cant revoke access from public files
            # temporary files cannnot recive access
            return
        try:
            session.get(JEMBE_FILES_ACCESS_GRANTED).get(self.name).remove(file_path)
        except (KeyError, ValueError):
            pass

    @abstractmethod
    def send_file(self, file_path: str) -> "Response":
        """send file via http response"""
        raise NotImplementedError()

    @abstractmethod
    def store_file(self, file: Union[File, str], subdir: str = "", move=False):
        """
        Store file inside this storage dir with unique file name inside subdir

        file -- Jembe File instance or full file path relative to JEMBE_UPLOAD_FOLDER
        move -- if True then remove file from original location
        """
        raise NotImplementedError()

    @abstractmethod
    def remove_file(self, file: Union[File, str]):
        raise NotImplementedError()


class DiskStorage(Storage):
    """Stores files on disk"""

    def __init__(
        self, name: str, folder: str, type: Storage.Type = Storage.Type.PUBLIC
    ):
        super().__init__(name, type=type)
        self.folder = folder

    def send_file(self, file_path: str) -> "Response":
        if self.can_access_file(file_path):
            return send_from_directory(self.folder, file_path)
        raise NotFound


    def store_file(self, file: Union[File, str], subdir: str = "", move=False):
        """
        Store file inside this storage dir with unique file name inside subdir

        file -- Jembe File instance or full file path relative to JEMBE_UPLOAD_FOLDER
        move -- if True then remove file from original location
        """
        raise NotImplementedError()

    def remove_file(self, file: Union[File, str]):
        raise NotImplementedError()