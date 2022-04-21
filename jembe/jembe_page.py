from typing import Dict, Optional, TYPE_CHECKING, List
from jembe.defaults import DEFAULT_TEMP_STORAGE_UPLOAD_FOLDER
from uuid import uuid1
from flask import jsonify
from werkzeug.utils import secure_filename
from .component_config import UrlPath, config
from .component import Component
from .files import File

# from flask import send_from_directory
from .app import get_storage, get_temp_storage, get_processor

if TYPE_CHECKING:
    from .common import DisplayResponse


class DisplayFileComponent(Component):
    """Serve files from Jembe Storages on Direct HTTP request"""

    def __init__(self, storage_name: str, file_path: UrlPath):
        super().__init__()

    def display(self) -> "DisplayResponse":
        return get_storage(self.state.storage_name).send_file(self.state.file_path)


class UploadFilesComponent(Component):
    """
    Saves uploaded files in temporary storage in new dir named uniquly named fileUploadRequestId.
    Returns json
        dict(files = dict(fileUploadId, [{storage=storage_name, path=file_path}]), fileUploadResponseId = fileUplaodResponseId)

    This component is only component that directly interecat with
    http post request in order to obtain files from it.
    It does not uses state parama.

    Basicaly this component create state params of file instances for other
    components so that thay can use file as init/state param.
    """

    def __init__(self):
        self.files: Dict[str, List[File]] = dict()
        self.file_upload_response_id: Optional[str] = None
        super().__init__()

    def _save_files_to_temp_storage(self):
        """Saves files to temp storage and populates self.files and self.file_upload_response_id"""
        # checks if this is valid upload request
        processor = get_processor()
        if processor.is_x_jembe_upload_request:
            # procede with upload
            temp_storage = get_temp_storage()

            # generate unique file_upload_response_id
            while self.file_upload_response_id is None or temp_storage.exists(
                "/".join(
                    [DEFAULT_TEMP_STORAGE_UPLOAD_FOLDER, self.file_upload_response_id]
                )
            ):
                self.file_upload_response_id = secure_filename(str(uuid1()))
            temp_storage.makedirs(
                "/".join(
                    [DEFAULT_TEMP_STORAGE_UPLOAD_FOLDER, self.file_upload_response_id]
                )
            )

            for fileUploadId, file in processor.request.files.items(True):
                if file.filename != "":
                    if file and self.allowed_file(file.filename):
                        tmp_file = temp_storage.store_file(
                            file,
                            "/".join(
                                [
                                    DEFAULT_TEMP_STORAGE_UPLOAD_FOLDER,
                                    self.file_upload_response_id,
                                ]
                            ),
                            True,
                        )
                        if fileUploadId in self.files:
                            self.files[fileUploadId].append(tmp_file)
                        else:
                            self.files[fileUploadId] = [tmp_file]

    def display(self) -> "DisplayResponse":
        self._save_files_to_temp_storage()

        return jsonify(
            dict(
                files={
                    fid: [File.dump_init_param(f) for f in ffs]
                    for fid, ffs in self.files.items()
                },
                fileUploadResponseId=self.file_upload_response_id,
            )
        )

    def allowed_file(self, file_name: str) -> bool:
        # TODO
        return True


@config(
    Component.Config(
        components=dict(file=DisplayFileComponent, upload_files=UploadFilesComponent)
    )
)
class JembePage(Component):
    pass
