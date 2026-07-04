"""
用户模型 — user, session, account, verification
"""
from sqlalchemy import (
    Column, String, Boolean, Integer, Text, DateTime, ForeignKey,
)
from sqlalchemy.orm import relationship
from models._base import Base, utcnow, gen_id


class User(Base):
    __tablename__ = "yezhi_user"

    id = Column(String(32), primary_key=True, default=gen_id)
    name = Column(String(255))
    email = Column(String(255), unique=True, nullable=False, index=True)
    email_verified = Column(Boolean, default=False)
    image = Column(Text)
    nickname = Column(String(255))
    uid = Column(Integer, unique=True, autoincrement=True)
    avatar = Column(String(500), default="/static/images/default-avatar.svg")
    signature = Column(Text)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    is_premium = Column(Boolean, default=False)
    is_old_user = Column(Boolean, default=False)
    is_subscribed = Column(Boolean, default=False)
    subscription_expires_at = Column(DateTime(timezone=True))
    banned = Column(Boolean, default=False)
    ban_reason = Column(Text)
    daily_request_count = Column(Integer, default=0)
    last_request_reset_date = Column(DateTime(timezone=True))
    last_login_at = Column(DateTime(timezone=True))
    last_daily_award_date = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    sessions = relationship("Session", back_populates="user", cascade="all, delete-orphan")
    accounts = relationship("Account", back_populates="user", cascade="all, delete-orphan")
    points_records = relationship("UserPointsRecord", back_populates="user", cascade="all, delete-orphan")
    generated_images = relationship("UserGeneratedImage", back_populates="user", cascade="all, delete-orphan")
    workflows = relationship("Workflow", back_populates="user", cascade="all, delete-orphan")
    user_settings = relationship("UserSetting", back_populates="user", cascade="all, delete-orphan")


class Session(Base):
    __tablename__ = "yezhi_session"

    id = Column(String(32), primary_key=True, default=gen_id)
    token = Column(String(512), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    ip_address = Column(String(45))
    user_agent = Column(Text)
    user_id = Column(String(32), ForeignKey("yezhi_user.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    user = relationship("User", back_populates="sessions")


class Account(Base):
    __tablename__ = "yezhi_account"

    id = Column(String(32), primary_key=True, default=gen_id)
    account_id = Column(String(255), nullable=False)
    provider_id = Column(String(255), nullable=False)
    user_id = Column(String(32), ForeignKey("yezhi_user.id", ondelete="CASCADE"), nullable=False)
    access_token = Column(Text)
    refresh_token = Column(Text)
    id_token = Column(Text)
    access_token_expires_at = Column(DateTime(timezone=True))
    refresh_token_expires_at = Column(DateTime(timezone=True))
    scope = Column(Text)
    password_hash = Column(String(255))
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    user = relationship("User", back_populates="accounts")


class Verification(Base):
    __tablename__ = "yezhi_verification"

    id = Column(String(32), primary_key=True, default=gen_id)
    identifier = Column(String(255), nullable=False, index=True)
    value = Column(String(255), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
