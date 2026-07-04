"""
前端配置/设置模型
"""
from sqlalchemy import Column, String, Boolean, Text, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from models._base import Base, utcnow, gen_id


class Setting(Base):
    """前端配置项 (除 env 外的动态配置)"""
    __tablename__ = "settings"
    
    id = Column(String(32), primary_key=True, default=gen_id)
    key = Column(String(100), nullable=False, unique=True, index=True)
    value = Column(Text, nullable=True)
    value_type = Column(String(20), default="string")  # string, int, float, bool, json
    description = Column(Text, nullable=True)
    category = Column(String(50), nullable=True)  # ui, generation, system, etc.
    is_public = Column(Boolean, default=True)  # 是否暴露给前端
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class UserSetting(Base):
    """用户个性化设置"""
    __tablename__ = "user_settings"
    
    id = Column(String(32), primary_key=True, default=gen_id)
    user_id = Column(String(32), ForeignKey("yezhi_user.id"), nullable=False, index=True)
    key = Column(String(100), nullable=False)
    value = Column(Text, nullable=True)
    
    __table_args__ = (Index("idx_user_setting", "user_id", "key", unique=True),)
    
    user = relationship("User", back_populates="user_settings")
