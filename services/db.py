"""
数据库初始化与连接
SQLAlchemy 2.0 engine + session
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models._base import Base
import config


_engine = None
_SessionLocal = None


def _build_engine():
    """按数据库类型构建 engine"""
    kwargs = {"echo": config.DEBUG}
    if "sqlite" not in config.DATABASE_URL:
        kwargs.update(pool_size=10, max_overflow=20, pool_pre_ping=True)
    return create_engine(config.DATABASE_URL, **kwargs)


def _get_engine():
    global _engine, _SessionLocal
    if _engine is None:
        _engine = _build_engine()
        _SessionLocal = sessionmaker(bind=_engine, autocommit=False, autoflush=False)
    return _engine


def get_sessionmaker():
    _get_engine()
    return _SessionLocal


def init_db():
    """创建所有表（开发用，生产用 Alembic 迁移）"""
    import models  # noqa: F401 — 触发 __init__.py 注册所有模型
    Base.metadata.create_all(bind=_get_engine())


def get_db():
    """获取数据库 session（用于依赖注入）"""
    db = get_sessionmaker()()
    try:
        yield db
    finally:
        db.close()


def get_db_session():
    """直接获取 session（用于蓝图内手动管理）"""
    return get_sessionmaker()()
