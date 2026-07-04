"""
社区 & 审核模型
"""
from sqlalchemy import (
    Column, String, Boolean, Integer, Text, Float, DateTime, ForeignKey,
)
from sqlalchemy.orm import relationship
from models._base import Base, utcnow, gen_id


class CommunityTag(Base):
    __tablename__ = "yezhi_community_tag"

    id = Column(String(32), primary_key=True, default=gen_id)
    image_id = Column(String(32), ForeignKey("yezhi_user_generated_image.id", ondelete="CASCADE"), nullable=False, index=True)
    tag = Column(String(100), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)

    image = relationship("UserGeneratedImage", back_populates="tags")


class CommunityLike(Base):
    __tablename__ = "yezhi_community_like"

    id = Column(String(32), primary_key=True, default=gen_id)
    image_id = Column(String(32), ForeignKey("yezhi_user_generated_image.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String(32), ForeignKey("yezhi_user.id"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)

    image = relationship("UserGeneratedImage", back_populates="likes")


class ImageReport(Base):
    __tablename__ = "yezhi_image_report"

    id = Column(String(32), primary_key=True, default=gen_id)
    image_id = Column(String(32), ForeignKey("yezhi_user_generated_image.id", ondelete="CASCADE"), nullable=False, index=True)
    reporter_id = Column(String(32), ForeignKey("yezhi_user.id"), nullable=False)
    reason = Column(Text)
    status = Column(String(20), default="pending")  # pending, reviewed, dismissed
    created_at = Column(DateTime(timezone=True), default=utcnow)
