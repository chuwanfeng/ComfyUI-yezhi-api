"""
生成统计 & 用户作品模型
"""
from sqlalchemy import (
    Column, String, Boolean, Integer, Text, Float, DateTime, ForeignKey, JSON,
)
from sqlalchemy.orm import relationship
from models._base import Base, utcnow, gen_id

class SiteStats(Base):
    __tablename__ = "yezhi_site_stats"

    id = Column(Integer, primary_key=True, default=1)
    total_generations = Column(Integer, default=0)
    daily_generations = Column(Integer, default=0)
    last_reset_date = Column(DateTime(timezone=True), default=utcnow)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class ModelUsageStats(Base):
    __tablename__ = "yezhi_model_usage_stats"

    id = Column(String(32), primary_key=True, default=gen_id)
    model_name = Column(String(255), nullable=False, index=True)
    user_id = Column(String(32), ForeignKey("yezhi_user.id"), nullable=True, index=True)
    response_time = Column(Float, nullable=False)
    is_authenticated = Column(Boolean, default=False)
    ip_address = Column(String(45))
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)


class IPDailyUsage(Base):
    __tablename__ = "yezhi_ip_daily_usage"

    ip_address = Column(String(45), primary_key=True)
    daily_request_count = Column(Integer, default=0)
    last_request_reset_date = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
    created_at = Column(DateTime(timezone=True), default=utcnow)


class UserGeneratedImage(Base):
    __tablename__ = "yezhi_user_generated_image"

    id = Column(String(32), primary_key=True, default=gen_id)
    user_id = Column(String(32), ForeignKey("yezhi_user.id", ondelete="CASCADE"), nullable=False, index=True)
    model_name = Column(String(255))
    prompt = Column(Text)
    negative_prompt = Column(Text)
    image_url = Column(Text, nullable=False)
    thumbnail_url = Column(Text)
    width = Column(Integer)
    height = Column(Integer)
    steps = Column(Integer)
    denoise = Column(Float)
    batch_index = Column(Integer, default=0)
    points_cost = Column(Integer, default=0)
    media_type = Column(String(20), default="image")  # image, video
    is_public = Column(Boolean, default=False)  # 是否发布到社区
    is_nsfw = Column(Boolean, default=False)
    report_count = Column(Integer, default=0)
    moderation_level = Column(String(20), default="none")
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    
    # 关联工作流
    duration_seconds = Column(Integer)  # 视频时长（秒）
    fps = Column(Integer)               # 帧率
    audio_start_time = Column(Integer)  # 音频开始帧
    audio_duration = Column(Integer)    # 音频长度（秒）
    workflow_id = Column(String(32), ForeignKey("workflows.id"), nullable=True, index=True)
    workflow = relationship("Workflow", back_populates="generations")

    user = relationship("User", back_populates="generated_images")

    # 社区标签
    tags = relationship("CommunityTag", back_populates="image", cascade="all, delete-orphan")
    likes = relationship("CommunityLike", back_populates="image", cascade="all, delete-orphan")
