"""
ORM 基类与公共工具 — 避免循环导入
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


def utcnow():
    return datetime.now(timezone.utc)


def gen_id():
    return uuid.uuid4().hex
