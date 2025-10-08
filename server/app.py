from datetime import datetime, timedelta
import os
from pathlib import Path
from typing import Optional

from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
from flask_jwt_extended import (
    JWTManager,
    create_access_token,
    get_jwt_identity,
    jwt_required,
)
from werkzeug.utils import secure_filename
import unicodedata
import re

from sqlalchemy import create_engine, select, func
from sqlalchemy.orm import sessionmaker, scoped_session

from .models import Base, User, FileEntry


def secure_filename_unicode(filename):
    """Secure filename that supports Unicode characters including Cyrillic"""
    # Normalize unicode characters
    filename = unicodedata.normalize('NFKD', filename)
    
    # Keep only safe characters: letters, digits, dots, hyphens, underscores
    # This includes Cyrillic letters
    safe_chars = re.sub(r'[^\w\-_\.]', '_', filename)
    
    # Remove multiple consecutive underscores
    safe_chars = re.sub(r'_+', '_', safe_chars)
    
    # Remove leading/trailing underscores and dots
    safe_chars = safe_chars.strip('_.')
    
    # Ensure filename is not empty and not too long
    if not safe_chars or len(safe_chars) > 255:
        safe_chars = f"file_{int(datetime.utcnow().timestamp())}"
    
    return safe_chars


def create_app() -> Flask:
    app = Flask(__name__)
    CORS(app)
    app.config["JWT_SECRET_KEY"] = os.environ.get("JWT_SECRET_KEY", "dev-secret")
    app.config["UPLOAD_ROOT"] = os.environ.get("UPLOAD_ROOT", str(Path(__file__).parent / "uploads"))
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
        "DATABASE_URL", f"sqlite:///{Path(__file__).parent / 'app.db'}"
    )
    app.config["JSON_AS_ASCII"] = False  # Enable Unicode support in JSON responses

    jwt = JWTManager(app)

    # SQLAlchemy (core) engine + session
    engine = create_engine(app.config["SQLALCHEMY_DATABASE_URI"], future=True)
    Base.metadata.create_all(engine)
    SessionLocal = scoped_session(sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True))

    Path(app.config["UPLOAD_ROOT"]).mkdir(parents=True, exist_ok=True)

    def get_db():
        return SessionLocal()

    @app.post("/auth/register")
    def register():
        data = request.get_json(force=True)
        username = (data.get("username") or "").strip()
        password = data.get("password") or ""
        if not username or not password:
            return jsonify({"message": "username and password are required"}), 400

        db = get_db()
        try:
            exists = db.execute(select(User).where(func.lower(User.username) == username.lower())).scalar_one_or_none()
            if exists is not None:
                return jsonify({"message": "user already exists"}), 409
            user = User(username=username)
            user.set_password(password)
            db.add(user)
            db.commit()
            return jsonify({"message": "registered"}), 201
        finally:
            db.close()

    @app.post("/auth/login")
    def login():
        data = request.get_json(force=True)
        username = (data.get("username") or "").strip()
        password = data.get("password") or ""
        db = get_db()
        try:
            user = db.execute(select(User).where(func.lower(User.username) == username.lower())).scalar_one_or_none()
            if user is None or not user.check_password(password):
                return jsonify({"message": "invalid credentials"}), 401
            token = create_access_token(identity=str(user.id), expires_delta=timedelta(hours=12))
            return jsonify({"access_token": token, "user": {"id": user.id, "username": user.username}})
        finally:
            db.close()

    @app.get("/files")
    @jwt_required()
    def list_files():
        user_id = int(get_jwt_identity())
        # filters: type in [all, py, jpg]
        ftype = (request.args.get("type") or "all").lower()
        sort_by = (request.args.get("sort_by") or "created_at").lower()
        order = (request.args.get("order") or "desc").lower()

        db = get_db()
        try:
            stmt = select(FileEntry).where(FileEntry.owner_id == user_id)
            if ftype in {"py", "jpg"}:
                stmt = stmt.where(FileEntry.extension == f".{ftype}")

            if sort_by == "uploader":
                # join with user for uploader name
                stmt = stmt.join(User, User.id == FileEntry.uploader_id).order_by(
                    (User.username.asc() if order == "asc" else User.username.desc())
                )
            else:
                # default by updated_at
                stmt = stmt.order_by(FileEntry.updated_at.asc() if order == "asc" else FileEntry.updated_at.desc())

            rows = db.execute(stmt).scalars().all()
            return jsonify([r.to_dict() for r in rows])
        finally:
            db.close()

    @app.post("/files")
    @jwt_required()
    def upload_file():
        user_id = int(get_jwt_identity())
        if "file" not in request.files:
            return jsonify({"message": "no file field"}), 400
        file = request.files["file"]
        if file.filename == "":
            return jsonify({"message": "empty filename"}), 400

        filename = secure_filename_unicode(file.filename)
        extension = Path(filename).suffix.lower()

        db = get_db()
        try:
            user_folder = Path(app.config["UPLOAD_ROOT"]) / str(user_id)
            user_folder.mkdir(parents=True, exist_ok=True)
            disk_path = user_folder / filename
            file.save(disk_path)

            now = datetime.utcnow()
            entry = FileEntry(
                owner_id=user_id,
                uploader_id=user_id,
                editor_id=user_id,
                name=filename,
                extension=extension,
                disk_path=str(disk_path),
                created_at=now,
                updated_at=now,
            )
            db.add(entry)
            db.commit()
            db.refresh(entry)
            return jsonify(entry.to_dict()), 201
        finally:
            db.close()

    @app.get("/files/<int:file_id>/download")
    @jwt_required()
    def download_file(file_id: int):
        user_id = int(get_jwt_identity())
        db = get_db()
        try:
            entry = db.get(FileEntry, file_id)
            if entry is None or entry.owner_id != user_id:
                return jsonify({"message": "not found"}), 404
            return send_file(entry.disk_path, as_attachment=True, download_name=entry.name)
        finally:
            db.close()

    @app.delete("/files/<int:file_id>")
    @jwt_required()
    def delete_file(file_id: int):
        user_id = int(get_jwt_identity())
        db = get_db()
        try:
            entry = db.get(FileEntry, file_id)
            if entry is None or entry.owner_id != user_id:
                return jsonify({"message": "not found"}), 404
            try:
                if os.path.exists(entry.disk_path):
                    os.remove(entry.disk_path)
            except Exception:
                # Ignore disk errors on delete, keep DB consistent with user action
                pass
            db.delete(entry)
            db.commit()
            return jsonify({"message": "deleted"})
        finally:
            db.close()

    @app.get("/files/<int:file_id>/preview")
    @jwt_required()
    def preview_file(file_id: int):
        """Return preview: for .py - text, for .jpg - image file stream."""
        user_id = int(get_jwt_identity())
        db = get_db()
        try:
            entry = db.get(FileEntry, file_id)
            if entry is None or entry.owner_id != user_id:
                return jsonify({"message": "not found"}), 404
            if entry.extension == ".py":
                try:
                    with open(entry.disk_path, "r", encoding="utf-8", errors="replace") as f:
                        content = f.read()
                    return jsonify({"name": entry.name, "content": content})
                except Exception:
                    return jsonify({"message": "cannot read file"}), 500
            elif entry.extension == ".jpg":
                return send_file(entry.disk_path, mimetype="image/jpeg")
            else:
                return jsonify({"message": "preview not supported"}), 400
        finally:
            db.close()

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=True)


