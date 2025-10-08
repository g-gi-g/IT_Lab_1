from datetime import datetime
from typing import Dict, Any

from passlib.hash import bcrypt, sha256_crypt
import os
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import declarative_base, Mapped, mapped_column, relationship


Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(150), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(200), nullable=False)

    def set_password(self, raw: str) -> None:
        # Use SHA256 to avoid bcrypt compatibility issues
        self.password_hash = sha256_crypt.hash(raw)

    def check_password(self, raw: str) -> bool:
        # Use SHA256 to avoid bcrypt compatibility issues
        return sha256_crypt.verify(raw, self.password_hash)


class FileEntry(Base):
    __tablename__ = "files"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    uploader_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    editor_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    extension: Mapped[str] = mapped_column(String(10), nullable=False)
    disk_path: Mapped[str] = mapped_column(Text, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    owner = relationship("User", foreign_keys=[owner_id])
    uploader = relationship("User", foreign_keys=[uploader_id])
    editor = relationship("User", foreign_keys=[editor_id])

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "extension": self.extension,
            "disk_path": self.disk_path,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "uploader": self.uploader.username if self.uploader else None,
            "editor": self.editor.username if self.editor else None,
        }


