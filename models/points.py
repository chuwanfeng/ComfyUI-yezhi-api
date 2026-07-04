"""
积分 & CDK 模型
"""
from sqlalchemy import (
    Column, String, Boolean, Integer, Text, Float, DateTime, ForeignKey,
)
from sqlalchemy.orm import relationship
from models._base import Base, utcnow, gen_id


class UserPoints(Base):
    __tablename__ = "yezhi_user_points"

    user_id = Column(String(32), ForeignKey("yezhi_user.id", ondelete="CASCADE"), primary_key=True)
    balance = Column(Integer, default=0, nullable=False)
    total_earned = Column(Integer, default=0)
    total_spent = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    user = relationship("User", backref="points")


class UserPointsRecord(Base):
    __tablename__ = "yezhi_user_points_record"

    id = Column(String(32), primary_key=True, default=gen_id)
    user_id = Column(String(32), ForeignKey("yezhi_user.id", ondelete="CASCADE"), nullable=False, index=True)
    amount = Column(Integer, nullable=False)
    balance_before = Column(Integer, nullable=False)
    balance_after = Column(Integer, nullable=False)
    source_type = Column(String(50), nullable=False)  # daily_award, cdk, purchase, consume
    source_id = Column(String(255))
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    user = relationship("User", back_populates="points_records")


class PointsPackage(Base):
    __tablename__ = "yezhi_points_package"

    id = Column(String(32), primary_key=True, default=gen_id)
    name = Column(String(255), nullable=False)
    name_tag = Column(String(50))
    points = Column(Integer, nullable=False)
    price_cents = Column(Integer, nullable=False)  # 分
    is_active = Column(Boolean, default=True)
    show_on_frontend = Column(Boolean, default=True)
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class CDK(Base):
    __tablename__ = "yezhi_cdk"

    id = Column(String(32), primary_key=True, default=gen_id)
    code = Column(String(64), unique=True, nullable=False, index=True)
    points = Column(Integer, nullable=False)
    max_uses = Column(Integer, default=1)
    used_count = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    expires_at = Column(DateTime(timezone=True))
    batch_id = Column(String(64), index=True)
    created_by = Column(String(32), ForeignKey("yezhi_user.id"))
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class CDKRedemption(Base):
    __tablename__ = "yezhi_cdk_redemption"

    id = Column(String(32), primary_key=True, default=gen_id)
    cdk_id = Column(String(32), ForeignKey("yezhi_cdk.id"), nullable=False)
    user_id = Column(String(32), ForeignKey("yezhi_user.id"), nullable=False)
    points_awarded = Column(Integer, nullable=False)
    redeemed_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)


class SubscriptionPlan(Base):
    __tablename__ = "yezhi_subscription_plan"

    id = Column(String(32), primary_key=True, default=gen_id)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    price_cents = Column(Integer, nullable=False)
    duration_days = Column(Integer, nullable=False)
    daily_generations = Column(Integer)
    is_active = Column(Boolean, default=True)
    is_popular = Column(Boolean, default=False)
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class UserSubscription(Base):
    __tablename__ = "yezhi_user_subscription"

    id = Column(String(32), primary_key=True, default=gen_id)
    user_id = Column(String(32), ForeignKey("yezhi_user.id"), nullable=False, unique=True)
    plan_id = Column(String(32), ForeignKey("yezhi_subscription_plan.id"), nullable=False)
    starts_at = Column(DateTime(timezone=True), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    auto_renew = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class Order(Base):
    __tablename__ = "yezhi_order"

    id = Column(String(32), primary_key=True, default=gen_id)
    user_id = Column(String(32), ForeignKey("yezhi_user.id"), nullable=False, index=True)
    order_no = Column(String(64), unique=True, nullable=False, index=True)
    product_type = Column(String(50), nullable=False)  # points_package, subscription
    product_id = Column(String(32), nullable=False)
    amount_cents = Column(Integer, nullable=False)
    status = Column(String(20), default="pending")  # pending, paid, cancelled, refunded
    paid_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
