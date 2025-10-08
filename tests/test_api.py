import os
import json
from pathlib import Path

import pytest

from server.app import create_app


@pytest.fixture(scope="module")
def client(tmp_path_factory):
    tmpdir = tmp_path_factory.mktemp("data")
    os.environ["UPLOAD_ROOT"] = str(tmpdir / "uploads")
    os.environ["DATABASE_URL"] = f"sqlite:///{tmpdir / 'app.db'}"
    os.environ["JWT_SECRET_KEY"] = "test-secret"
    os.environ["TESTING"] = "True"
    app = create_app()
    app.config.update(TESTING=True)
    with app.test_client() as c:
        yield c


def register_and_login(client):
    client.post("/auth/register", json={"username": "alice", "password": "pwd"})
    r = client.post("/auth/login", json={"username": "alice", "password": "pwd"})
    assert r.status_code == 200
    token = r.get_json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_upload_list_preview_py(client, tmp_path):
    headers = register_and_login(client)
    pyfile = tmp_path / "hello.py"
    pyfile.write_text("print('hello')\n", encoding="utf-8")

    with open(pyfile, 'rb') as f:
        r = client.post("/files", headers=headers, data={"file": (f, "hello.py")})
    assert r.status_code in (200, 201)

    r = client.get("/files", headers=headers, query_string={"type": "py"})
    data = r.get_json()
    assert any(x["name"] == "hello.py" for x in data)

    fid = next(x["id"] for x in data if x["name"] == "hello.py")
    r = client.get(f"/files/{fid}/preview", headers=headers)
    assert r.status_code == 200
    j = r.get_json()
    assert "print('hello')" in j["content"]


def test_filter_and_sort_by_uploader(client, tmp_path):
    headers = register_and_login(client)
    f1 = tmp_path / "a.jpg"
    f1.write_bytes(b"\xff\xd8\xff\xd9")  # minimal jpeg markers
    with open(f1, 'rb') as f:
        client.post("/files", headers=headers, data={"file": (f, "a.jpg")})

    r = client.get("/files", headers=headers, query_string={"type": "jpg", "sort_by": "uploader", "order": "asc"})
    assert r.status_code == 200
    data = r.get_json()
    assert all(x["extension"] == ".jpg" for x in data)


def test_delete_file(client, tmp_path):
    headers = register_and_login(client)
    f1 = tmp_path / "todel.py"
    f1.write_text("x=1\n", encoding="utf-8")
    with open(f1, 'rb') as f:
        r = client.post("/files", headers=headers, data={"file": (f, "todel.py")})
    fid = r.get_json()["id"]
    r = client.delete(f"/files/{fid}", headers=headers)
    assert r.status_code == 200
    r = client.get(f"/files/{fid}/download", headers=headers)
    assert r.status_code == 404


