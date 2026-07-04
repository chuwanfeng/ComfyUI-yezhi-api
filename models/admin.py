"""
管理员功能模型 — 黑名单、敏感词、限额配置等
"""
from sqlalchemy import (
    Column, String, Boolean, Integer, Text, DateTime, ForeignKey,
)
from models._base import Base, utcnow, gen_id


class IPBlacklist(Base):
    __tablename__ = "yezhi_ip_blacklist"

    id = Column(String(32), primary_key=True, default=gen_id)
    ip_address = Column(String(45), unique=True, nullable=False)
    reason = Column(Text)
    created_by = Column(String(32))
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class AccountBlacklist(Base):
    __tablename__ = "yezhi_account_blacklist"

    id = Column(String(32), primary_key=True, default=gen_id)
    user_id = Column(String(32), ForeignKey("yezhi_user.id", ondelete="CASCADE"), unique=True, nullable=False)
    reason = Column(Text)
    created_by = Column(String(32))
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class ProfanityWord(Base):
    __tablename__ = "yezhi_profanity_word"

    id = Column(String(32), primary_key=True, default=gen_id)
    word = Column(String(255), unique=True, nullable=False, index=True)
    category = Column(String(50))  # nsfw、politics、abuse
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)


class UserLimitConfig(Base):
    __tablename__ = "yezhi_user_limit_config"

    id = Column(Integer, primary_key=True, default=1)
    regular_daily_limit = Column(Integer)
    premium_daily_limit = Column(Integer)
    new_user_daily_limit = Column(Integer)
    unauthenticated_ip_daily_limit = Column(Integer)
    regular_max_images = Column(Integer)
    subscribed_max_images = Column(Integer)
    nsfw_report_threshold = Column(Integer, default=3)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class AvatarFrame(Base):
    __tablename__ = "yezhi_avatar_frame"

    id = Column(Integer, primary_key=True, autoincrement=True)
    category = Column(String(255), nullable=False)
    name = Column(String(255))
    image_url = Column(Text)
    is_active = Column(Boolean, default=True)
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class AllowedEmailDomain(Base):
    __tablename__ = "yezhi_allowed_email_domain"

    id = Column(Integer, primary_key=True, autoincrement=True)
    domain = Column(String(255), unique=True, nullable=False)
    is_enabled = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
