from typing import TYPE_CHECKING, Union, Any, Dict, List, Optional
from enum import Enum
import shutil
import os
from abc import ABC, abstractmethod
from uuid import uuid1

from flask import session, current_app, url_for, send_from_directory, session
from werkzeug.datastructures import FileStorage
from werkzeug.utils import cached_property, secure_filename
from .app import get_private_storage, get_public_storage, get_storage
from .exceptions import NotFound
from .common import JembeInitParamSupport

if TYPE_CHECKING:
    from flask import Response

JEMBE_FILES_ACCESS_GRANTED = "jembe_files_access_granted"
JEMBE_FILES_ACCESS_GRANTED_MAX_SIZE = 500


class File(JembeInitParamSupport):
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

    def in_temp_storage(self) -> bool:
        return self.storage.type == self.storage.Type.TEMP

    def in_public_storage(self) -> bool:
        return self.storage.type == self.storage.Type.PUBLIC

    def in_private_storage(self) -> bool:
        return self.storage.type == self.storage.Type.PRIVATE

    @property
    def url(self) -> str:
        return url_for(
            "jembe./jembe/file",
            component_key="",
            component_key__1="",
            storage_name__1=self.storage.name,
            file_path__1=self.path,
        )

    @property
    def basename(self) -> str:
        return self.storage.basename(self.path)

    def copy_to(self, storage: Union["Storage", str], subdir: str = "") -> "File":
        if isinstance(storage, str):
            storage = get_storage(storage)
        return storage.store_file(self, subdir)

    def move_to(self, storage: Union["Storage", str], subdir: str = "") -> "File":
        file = self.copy_to(storage, subdir)
        self.storage.remove(self.path)
        return file

    def copy_to_public(self, subdir: str = "") -> "File":
        return self.copy_to(get_public_storage(), subdir)

    def copy_to_private(self, subdir: str = "") -> "File":
        return self.copy_to(get_private_storage(), subdir)

    def move_to_public(self, subdir: str = ""):
        file = self.move_to(get_public_storage(), subdir)
        self.storage = file.storage
        self.path = file.path

    def move_to_private(self, subdir: str = ""):
        file = self.move_to(get_private_storage(), subdir)
        self.storage = file.storage
        self.path = file.path

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

    def exists(self) -> bool:
        raise NotImplementedError()

    @classmethod
    def dump_init_param(cls, value: "File") -> Any:
        return dict(path=value.path, storage=value.storage.name)

    @classmethod
    def load_init_param(
        cls, value: Union[Dict[str, str], List[Dict[str, str]]]
    ) -> "File":
        # handelse both list and dict in order to support 
        # using $jmb.set(xx, $el.files) instead of jmb.set(xx, $el.files[0]) 
        # for regular, not multiple, file upload input
        if isinstance(value, list):
            value = value[0]
        return File(value["storage"], value["path"])

    def __str__(self) -> str:
        return "<File: storage={}, path={}>".format(self.storage, self.path)


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
                session.modified = True

            if (
                len(session[JEMBE_FILES_ACCESS_GRANTED])
                > JEMBE_FILES_ACCESS_GRANTED_MAX_SIZE
            ):
                session[JEMBE_FILES_ACCESS_GRANTED] = session[
                    JEMBE_FILES_ACCESS_GRANTED
                ][:JEMBE_FILES_ACCESS_GRANTED_MAX_SIZE]
                session.modified = True
        except KeyError:
            if JEMBE_FILES_ACCESS_GRANTED not in session:
                session[JEMBE_FILES_ACCESS_GRANTED] = dict()
            if self.name not in session[JEMBE_FILES_ACCESS_GRANTED]:
                session[JEMBE_FILES_ACCESS_GRANTED][self.name] = list()
            session[JEMBE_FILES_ACCESS_GRANTED][self.name].insert(0, file_path)
            session.modified = True

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
    def store_file(
        self, file: Union[File, FileStorage, str], subdir: str = "", move=False
    ) -> File:
        """
        Store file inside this storage dir with unique file name inside subdir

        file -- Jembe File instance or full file path relative to JEMBE_UPLOAD_FOLDER
        move -- if True then remove file from original location
        """
        raise NotImplementedError()

    @abstractmethod
    def remove_file(self, file: Union[File, str]):
        raise NotImplementedError()

    @abstractmethod
    def isdir(self, dir_path: str) -> bool:
        raise NotImplementedError()

    @abstractmethod
    def isfile(self, file_path: str) -> bool:
        raise NotImplementedError()

    @abstractmethod
    def exists(self, path: str) -> bool:
        raise NotImplementedError()

    @abstractmethod
    def makedirs(self, path: str, mode=0o777):
        raise NotImplementedError()

    @abstractmethod
    def path_join(self, path: str, *paths: str) -> str:
        raise NotImplementedError()

    @abstractmethod
    def rmdir(self, dir_path: str):
        raise NotImplementedError()

    @abstractmethod
    def rmtree(self, dir_path: str):
        raise NotImplementedError()

    @abstractmethod
    def remove(self, file_path: str):
        raise NotImplementedError()

    @abstractmethod
    def basename(self, path: str) -> str:
        raise NotImplementedError()


class DiskStorage(Storage):
    """Stores files on disk"""

    def __init__(
        self, name: str, folder: str, type: Storage.Type = Storage.Type.PUBLIC
    ):
        super().__init__(name, type=type)

        self._folder = folder

    @cached_property
    def folder(self) -> str:
        if not os.path.isabs(self._folder):
            return os.path.join(current_app.root_path, self._folder)  # type:ignore
        return self._folder

    def send_file(self, file_path: str) -> "Response":
        if self.can_access_file(file_path):
            return send_from_directory(self.folder, file_path)
        raise NotFound

    def _get_unique_filename(self, filename: Optional[str], subdir: str) -> str:
        sfn = secure_filename(filename)
        while self.exists(os.path.join(subdir, sfn)):
            sfn_base, sfn_ext = os.path.splitext(sfn)
            sfn = secure_filename(
                "{}_{}{}".format(sfn_base, str(uuid1()).split("-")[0], sfn_ext)
            )
        return sfn

    def store_file(
        self, file: Union[File, FileStorage, str], subdir: str = "", move=False
    ) -> File:
        """
        Store file inside this storage dir with unique file name inside subdir

        file -- Jembe File instance or full file path relative to JEMBE_UPLOAD_FOLDER
        move -- if True then remove file from original location
        """
        if isinstance(file, File):
            sfn = self._get_unique_filename(file.basename, subdir)
            if isinstance(file.storage, DiskStorage):
                shutil.copy(
                    os.path.join(file.storage.folder, file.path),
                    os.path.join(self.folder, subdir, sfn),
                )
                return File(self, os.path.join(subdir, sfn))
            else:
                raise NotImplementedError()
        elif isinstance(file, FileStorage):
            sfn = self._get_unique_filename(file.filename, subdir)
            file.save(os.path.join(self.folder, subdir, sfn))
            return File(self, os.path.join(subdir, sfn))
        else:
            # file is instance of str
            raise NotImplementedError()

    def remove_file(self, file: Union[File, str]):
        raise NotImplementedError()

    def isdir(self, dir_path: str) -> bool:
        return os.path.isdir(os.path.join(self.folder, dir_path))

    def isfile(self, file_path: str) -> bool:
        return os.path.isfile(os.path.join(self.folder, file_path))

    def exists(self, path: str) -> bool:
        return os.path.exists(os.path.join(self.folder, path))

    def makedirs(self, path: str, mode=0o777):
        os.makedirs(os.path.join(self.folder, path), mode)

    def path_join(self, path: str, *paths: str) -> str:
        return os.path.join(path, *paths)

    def rmdir(self, dir_path: str):
        os.rmdir(os.path.join(self.folder, dir_path))

    def rmtree(self, dir_path: str):
        shutil.rmtree(os.path.join(self.folder, dir_path))

    def remove(self, file_path: str):
        os.remove(os.path.join(self.folder, file_path))

    def basename(self, path: str) -> str:
        return os.path.basename(path)
