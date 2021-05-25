from typing import TYPE_CHECKING, Union, Any, Dict, List, Optional
from enum import Enum
import shutil
import os
from io import BufferedIOBase, TextIOBase, RawIOBase, IOBase
from abc import ABC, abstractmethod
from uuid import uuid4

from flask import session, current_app, url_for, send_from_directory
from werkzeug.datastructures import FileStorage
from werkzeug.utils import cached_property, secure_filename
from .app import get_private_storage, get_public_storage, get_storage, get_temp_storage
from .exceptions import NotFound
from .common import JembeInitParamSupport
from .defaults import (
    DEFAULT_SESSION_TEMP_STORAGE_ID,
    DEFAULT_SESSION_TEMP_STORAGE_SUBDIR,
    DEFAULT_STORAGE_CACHE_FOLDER,
    DEFAULT_TEMP_STORAGE_UPLOAD_FOLDER,
)

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

    def is_just_uploaded(self) -> bool:
        return self.in_temp_storage() and self.path.startswith(
            "{}/".format(DEFAULT_TEMP_STORAGE_UPLOAD_FOLDER)
        )

    def is_cache_version(self) -> bool:
        return not self.in_temp_storage() and self.path.startswith(
            "{}/".format(DEFAULT_STORAGE_CACHE_FOLDER)
        )

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

    def copy_to_temp(self, subdir: Optional[str] = None) -> "File":
        temp_subdir = self.storage._get_default_temp_subdir()
        return self.copy_to(
            get_temp_storage(),
            "/".join((temp_subdir, subdir)) if subdir is not None else temp_subdir,
        )

    def move_to_public(self, subdir: str = ""):
        file = self.move_to(get_public_storage(), subdir)
        self.storage = file.storage
        self.path = file.path

    def move_to_private(self, subdir: str = ""):
        file = self.move_to(get_private_storage(), subdir)
        self.storage = file.storage
        self.path = file.path

    def move_to_temp(self, subdir: Optional[str] = None):
        temp_subdir = self.storage._get_default_temp_subdir()
        file = self.move_to(
            get_temp_storage(),
            "/".join((temp_subdir, subdir)) if subdir is not None else temp_subdir,
        )
        self.storage = file.storage
        self.path = file.path

    def remove(self):
        self.storage.remove(self.path)

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
        return self.storage.open(
            self.path,
            buffering=buffering,
            mode=mode,
            encoding=encoding,
            errors=errors,
            newline=newline,
            closefd=closefd,
            opener=None,
        )

    def exists(self) -> bool:
        return self.storage.exists(self.path)

    def store_cache_version(
        self,
        cache_name: str,
        file: Union[
            "File", "FileStorage", "BufferedIOBase", "TextIOBase", "RawIOBase", str
        ],
    ) -> "File":
        return self.storage.store_cache_version_of_file(self.path, cache_name, file)

    def get_cache_version(self, cache_name: str) -> "File":
        return self.storage.get_cache_version_of_file(self.path, cache_name)

    def get_original(self) -> "File":
        return self.storage.get_original_file(self.path)

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
        return "<File: storage={}, path={}>".format(self.storage.name, self.path)

    def __repr__(self) -> str:
        return "<File: storage={}, path={}>".format(self.storage.name, self.path)


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
            if DEFAULT_SESSION_TEMP_STORAGE_ID in session and file_path.startswith(
                "{}/{}/".format(
                    DEFAULT_SESSION_TEMP_STORAGE_SUBDIR,
                    session[DEFAULT_SESSION_TEMP_STORAGE_ID],
                )
            ):
                return True
            # Access to uploaded files before they are moved to session_temp_storage_subdir
            # or public or private storage is prohibited
            return False
        elif self.type == self.Type.PUBLIC:
            return True
        # private storage
        if file_path.startswith("{}/".format(DEFAULT_STORAGE_CACHE_FOLDER)):
            return self.get_original_file(file_path).path in session.get(
                JEMBE_FILES_ACCESS_GRANTED, dict()
            ).get(self.name, list())
        else:
            return file_path in session.get(JEMBE_FILES_ACCESS_GRANTED, dict()).get(
                self.name, list()
            )

    def grant_access_to_file(self, file_path: str):
        """Grants current user access to file"""
        if self.type in (self.Type.PUBLIC, self.Type.TEMP):
            # public already have granted access to all files
            # cannot grant access to temporay file
            return
        if file_path.startswith("{}/".format(DEFAULT_STORAGE_CACHE_FOLDER)):
            raise ValueError(
                "Cant grant access to cache_version directly: file_path='{}', storage='{}'".format(
                    file_path, self.name
                )
            )
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

    def send_file(self, file_path: str) -> "Response":
        """send file via http response"""
        if self.can_access_file(file_path):
            return self.send_file_raw(file_path)
        raise NotFound()

    def store_file(
        self,
        file: Union[
            "File", "FileStorage", "BufferedIOBase", "TextIOBase", "RawIOBase", str
        ],
        subdir: str = "",
        filename: Optional[str] = None,
    ) -> File:
        """
        Store file inside this storage dir with unique file name inside subdir

        file -- Jembe File instance or full file path relative to JEMBE_UPLOAD_FOLDER
        subdir -- path iniside storage where file should be saved
        filename -- optionaly overide filename
        """
        # Check if subdir is valid when storing file
        if self.type == self.Type.TEMP:
            if not subdir.startswith(
                "{}/".format(DEFAULT_TEMP_STORAGE_UPLOAD_FOLDER)
            ) and not subdir.startswith(
                "{}/".format(DEFAULT_SESSION_TEMP_STORAGE_SUBDIR)
            ):
                raise ValueError(
                    "Invalid storage subdir '{}': In temporary storage '{}' files"
                    " can only be saved inside UPLOAD and SESSION TEMP STORAGE subdirs.".format(
                        subdir, self.name
                    )
                )
        elif (
            self.type == self.Type.PUBLIC or self.type == self.Type.PRIVATE
        ) and subdir.startswith("{}/".format(DEFAULT_STORAGE_CACHE_FOLDER)):
            raise ValueError(
                "Invalid storage subdir '{}': Cant store files directly "
                "inside CACHE dir in storage '{}'.".format(subdir, self.name)
            )
        return self.store_file_raw(file=file, subdir=subdir, filename=filename)

    def store_cache_version_of_file(
        self,
        file_path: str,
        cache_name: str,
        cache_file: Union[
            "File", "FileStorage", "BufferedIOBase", "TextIOBase", "RawIOBase", str
        ],
    ) -> "File":
        return self.store_file_raw(
            cache_file,
            self._get_cache_subdir(file_path),
            self._get_cache_name_with_extension(self.basename(file_path), cache_name),
        )

    def _get_cache_name_with_extension(self, file_name, cache_name) -> str:
        cache_name_with_extension = cache_name
        if "." not in cache_name:
            if "." in file_name:
                ext = file_name.split(".")[-1]
                cache_name_with_extension = "{}.{}".format(cache_name, ext)
        return cache_name_with_extension

    def _get_cache_subdir(self, file_path: str) -> str:
        if self.type == self.Type.TEMP:
            split_file_path = file_path.split("/")
            if split_file_path[0] == DEFAULT_TEMP_STORAGE_UPLOAD_FOLDER:
                return ""
            if split_file_path[0] in (
                DEFAULT_SESSION_TEMP_STORAGE_SUBDIR,
                DEFAULT_TEMP_STORAGE_UPLOAD_FOLDER,
            ):
                file_path = "/".join(split_file_path[2:])
            return "{}/{}/{}".format(
                self._get_default_temp_subdir(), DEFAULT_STORAGE_CACHE_FOLDER, file_path
            )
        else:
            return "{}/{}".format(DEFAULT_STORAGE_CACHE_FOLDER, file_path)

    def _get_default_temp_subdir(self) -> str:
        if DEFAULT_SESSION_TEMP_STORAGE_ID not in session:
            session[DEFAULT_SESSION_TEMP_STORAGE_ID] = uuid4()
        return "{}/{}".format(
            DEFAULT_SESSION_TEMP_STORAGE_SUBDIR,
            session[DEFAULT_SESSION_TEMP_STORAGE_ID],
        )

    def get_cache_version_of_file(self, file_path: str, cache_name: str) -> "File":
        split_file_path = file_path.split("/")
        if self.type != self.Type.TEMP:
            if split_file_path[0] == DEFAULT_STORAGE_CACHE_FOLDER:
                raise ValueError(
                    "Cant crate cache version of cached version '{}':'{}'".format(
                        self.name, file_path
                    )
                )
        else:
            if split_file_path[0] == DEFAULT_TEMP_STORAGE_UPLOAD_FOLDER:
                raise ValueError(
                    "Cant create cache version of just uploaded file, save it first somwhere else."
                )
            elif (
                split_file_path[0] == DEFAULT_SESSION_TEMP_STORAGE_SUBDIR
                and split_file_path[2] == DEFAULT_STORAGE_CACHE_FOLDER
            ):
                raise ValueError(
                    "Cant crate cache version of cached version '{}':'{}'".format(
                        self.name, file_path
                    )
                )
        full_path = "/".join(
            (
                self._get_cache_subdir(file_path),
                self._get_cache_name_with_extension(
                    self.basename(file_path), cache_name
                ),
            )
        )
        return File(storage=self, file_path=full_path)

    def get_original_file(self, cache_file_path: str) -> "File":
        if cache_file_path.startswith("{}/".format(DEFAULT_STORAGE_CACHE_FOLDER)):
            raise ValueError(
                "Invalid cache file name '{}' in storage '{}'".format(
                    cache_file_path, self.name
                )
            )
        return File(self, "/".join(cache_file_path.split("/")[1:-1]))

    def remove(self, file_path: str):
        try:
            self.remove_raw(file_path)
        except Exception as e:
            current_app.logger.warning(e)
        cache_subdir = self._get_cache_subdir(file_path)
        if cache_subdir and self.exists(cache_subdir):
            self.rmtree(cache_subdir)
            self._remove_empty_dirs("/".join(cache_subdir.split("/")[:-1]))
        self._remove_empty_dirs("/".join(file_path.split("/")[:-1]))

    def _remove_empty_dirs(self, file_path):
        fp_split = file_path.split("/")
        while fp_split:
            path = "/".join(fp_split)
            print("deleting", path)
            try:
                self.rmdir(path)
            except Exception as e:
                current_app.logger.warning(e)
                return
            fp_split.pop()

    @abstractmethod
    def send_file_raw(self, file_path: str) -> "Response":
        """send file via http response"""
        raise NotImplementedError()

    @abstractmethod
    def store_file_raw(
        self,
        file: Union[
            "File", "FileStorage", "BufferedIOBase", "TextIOBase", "RawIOBase", str
        ],
        subdir: str = "",
        filename: Optional[str] = None,
    ) -> File:
        raise NotImplementedError()

    def open(
        self,
        file_path: str,
        mode="r",
        buffering=-1,
        encoding=None,
        errors=None,
        newline=None,
        closefd=True,
        opener=None,
    ) -> "IOBase":
        self.makedirs("/".join(file_path.split("/")[:-1]))
        return self.open_raw(
            file_path=file_path,
            mode=mode,
            buffering=buffering,
            encoding=encoding,
            errors=errors,
            newline=newline,
            closefd=closefd,
            opener=opener,
        )

    @abstractmethod
    def open_raw(
        self,
        file_path: str,
        mode="r",
        buffering=-1,
        encoding=None,
        errors=None,
        newline=None,
        closefd=True,
        opener=None,
    ) -> "IOBase":
        raise NotImplementedError()

    @abstractmethod
    def remove_raw(self, file_path: str):
        raise NotImplementedError

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
    def rmdir(self, dir_path: str):
        raise NotImplementedError()

    @abstractmethod
    def rmtree(self, dir_path: str):
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

    def send_file_raw(self, file_path: str) -> "Response":
        return send_from_directory(self.folder, file_path)

    def _get_unique_filename(self, filename: Optional[str], subdir: str) -> str:
        sfn = secure_filename(filename if filename is not None else "unnamed")
        while self.exists(os.path.join(subdir, sfn)):
            sfn_base, sfn_ext = os.path.splitext(sfn)
            sfn = secure_filename(
                "{}_{}{}".format(sfn_base, str(uuid4()).split("-")[0], sfn_ext)
            )
        return sfn

    def store_file_raw(
        self,
        file: Union[
            "File", "FileStorage", "BufferedIOBase", "TextIOBase", "RawIOBase", str
        ],
        subdir: str = "",
        filename: Optional[str] = None,
    ) -> File:
        """
        Store file inside this storage dir with unique file name inside subdir

        file -- Jembe File instance or full file path relative to JEMBE_UPLOAD_FOLDER
        """
        if isinstance(file, File):
            sfn = self._get_unique_filename(file.basename, subdir)
            if isinstance(file.storage, DiskStorage):
                os.makedirs(os.path.join(self.folder, subdir), exist_ok=True)
                shutil.copy(
                    os.path.join(file.storage.folder, file.path),
                    os.path.join(self.folder, subdir, sfn),
                )
                return File(self, os.path.join(subdir, sfn))
            else:
                raise NotImplementedError()
        elif isinstance(file, FileStorage):
            sfn = self._get_unique_filename(file.filename, subdir)
            os.makedirs(os.path.join(self.folder, subdir), exist_ok=True)
            file.save(os.path.join(self.folder, subdir, sfn))
            return File(self, os.path.join(subdir, sfn))
        elif isinstance(file, IOBase):
            if filename is None:
                raise ValueError(
                    "Storge '{}': Filename is required when storing BufferedIOBase".format(
                        self.name
                    )
                )
            sfn = self._get_unique_filename(filename, subdir)
            os.makedirs(os.path.join(self.folder, subdir), exist_ok=True)
            new_file = File(self, os.path.join(self.folder, subdir, sfn))
            if isinstance(file, (BufferedIOBase, RawIOBase)):
                fio = new_file.open(mode="wb")
                file.seek(0)
                fio.write(file.read())
                fio.close()
                return new_file
            elif isinstance(file, TextIOBase):
                fio = new_file.open(mode="w")
                file.seek(0)
                fio.write(file.read())
                fio.close()
                return new_file
        else:
            # file is instance of str
            raise NotImplementedError()

    def remove_raw(self, file_path: str):
        os.remove(os.path.join(self.folder, file_path))

    def isdir(self, dir_path: str) -> bool:
        return os.path.isdir(os.path.join(self.folder, dir_path))

    def isfile(self, file_path: str) -> bool:
        return os.path.isfile(os.path.join(self.folder, file_path))

    def exists(self, path: str) -> bool:
        return os.path.exists(os.path.join(self.folder, path))

    def makedirs(self, path: str, mode=0o777):
        os.makedirs(os.path.join(self.folder, path), mode, exist_ok=True)

    def rmdir(self, dir_path: str):
        os.rmdir(os.path.join(self.folder, dir_path))

    def rmtree(self, dir_path: str):
        shutil.rmtree(os.path.join(self.folder, dir_path))

    def basename(self, path: str) -> str:
        return os.path.basename(path)

    def open_raw(
        self,
        file_path: str,
        mode: str = "r",
        buffering=-1,
        encoding=None,
        errors=None,
        newline=None,
        closefd=True,
        opener=None,
    ):
        return open(
            os.path.join(self.folder, file_path),
            mode=mode,
            buffering=buffering,
            encoding=encoding,
            errors=errors,
            newline=newline,
            closefd=closefd,
            opener=opener,
        )
