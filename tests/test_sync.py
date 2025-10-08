import os
from pathlib import Path
import time

import pytest

from server.app import create_app


def test_basic_sync_flow(tmp_path):
    # This test simulates upload then list to assert server reflects changes
    os.environ["UPLOAD_ROOT"] = str(tmp_path / "uploads")
    os.environ["DATABASE_URL"] = f"sqlite:///{tmp_path / 'app.db'}"
    os.environ["JWT_SECRET_KEY"] = "test-secret"
    os.environ["TESTING"] = "True"
    app = create_app()
    app.config.update(TESTING=True)
    c = app.test_client()

    c.post("/auth/register", json={"username": "bob", "password": "pwd"})
    r = c.post("/auth/login", json={"username": "bob", "password": "pwd"})
    token = r.get_json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # create local file (to be "synced" by uploading)
    local = tmp_path / "sync.py"
    local.write_text("print('sync')\n", encoding="utf-8")

    with open(local, 'rb') as f:
        r = c.post("/files", headers=headers, data={"file": (f, "sync.py")})
        assert r.status_code in (200, 201)

    # server should list it with .py extension
    r = c.get("/files", headers=headers, query_string={"type": "py"})
    items = r.get_json()
    assert any(x["name"] == "sync.py" for x in items)


