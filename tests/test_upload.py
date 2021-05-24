from io import BytesIO
from flask import json


def test_upload_files(jmb, client):
    r = client.post(
        "/jembe/upload_files",
        data=dict(
            uploadId1=(BytesIO(b"FILE1 CONTENT"), "file1.txt"),
            uploadId2=(BytesIO(b"FILE2 CONTENT"), "file2.txt"),
        ),
        headers={"x-jembe": "upload"},
    )
    assert r.status_code == 200

    rd = json.loads(r.data)
    assert "fileUploadResponseId" in rd
    assert rd["fileUploadResponseId"] is not None
    assert "files" in rd
    assert len(rd["files"].keys()) == 2
    assert rd["files"]["uploadId1"] == [
        dict(
            path="UPLOADS/{}/file1.txt".format(rd["fileUploadResponseId"]),
            storage="temp",
        )
    ]
    assert rd["files"]["uploadId2"] == [
        dict(
            path="UPLOADS/{}/file2.txt".format(rd["fileUploadResponseId"]),
            storage="temp",
        )
    ]

    r = client.post(
        "/jembe/upload_files",
        data=dict(
            uploadId1=(BytesIO(b"FILE1 CONTENT"), "file1.txt"),
            uploadId2=(BytesIO(b"FILE2 CONTENT"), "file1.txt"),
        ),
        headers={"x-jembe": "upload"},
    )
    assert r.status_code == 200

    rd = json.loads(r.data)
    assert rd["files"]["uploadId1"][0]["path"] != rd["files"]["uploadId2"][0]["path"]
