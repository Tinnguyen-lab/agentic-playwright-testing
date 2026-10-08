"""Kết nối DB. URL lấy từ DATABASE_URL; mặc định SQLite cục bộ (artifacts/app.db).

SQL Server Express (Windows auth), ví dụ:
    DATABASE_URL=mssql+pyodbc://@localhost\\SQLEXPRESS/AgenticPlaywrightTesting?driver=ODBC+Driver+17+for+SQL+Server&trusted_connection=yes
"""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from src.database.models import Base

DEFAULT_URL = "sqlite:///artifacts/app.db"


def get_engine(url: str | None = None) -> Engine:
    load_dotenv(Path(__file__).resolve().parents[2] / ".env")  # không ghi đè biến môi trường đã có
    url = url or os.getenv("DATABASE_URL", "").strip() or DEFAULT_URL
    if url.startswith("sqlite:///") and not url.endswith(":memory:"):
        Path(url.removeprefix("sqlite:///")).parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(url)
    Base.metadata.create_all(engine)  # ponytail: create_all thay migration; thêm Alembic khi schema bắt đầu đổi trên DB thật
    return engine


def session_factory(url: str | None = None) -> sessionmaker[Session]:
    return sessionmaker(get_engine(url), expire_on_commit=False)
