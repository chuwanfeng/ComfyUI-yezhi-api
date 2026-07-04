"""
用户自定义工作流模型
Workflow JSON 存储在文件系统，数据库只存元数据
"""
from sqlalchemy import Column, String, Integer, Text, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from models._base import Base, utcnow, gen_id
import os


class Workflow(Base):
    """用户自定义工作流（数据库只存元数据，JSON 存文件）"""
    __tablename__ = "workflows"

    id = Column(String(32), primary_key=True, default=gen_id)
    user_id = Column(String(32), ForeignKey("yezhi_user.id"), nullable=True, index=True)

    # 基本信息
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    cover_url = Column(String(500), nullable=True)

    # JSON 文件相对路径（相对于 WORKFLOWS_DIR）
    json_path = Column(String(255), nullable=False)

    # ComfyUI 服务端配置（为空则使用全局配置）
    comfyui_url = Column(String(500), nullable=True)

    # 参数映射 (JSON字符串)：{"prompt": {"node_id": "6", "field": "text"}, ...}
    param_mapping = Column(Text, nullable=True)

    # 元数据
    is_public = Column(Boolean, default=False)
    is_builtin = Column(Boolean, default=False)
    use_count = Column(Integer, default=0)

    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    # 关联
    user = relationship("User", back_populates="workflows")
    generations = relationship("UserGeneratedImage", back_populates="workflow")


class WorkflowTemplate(Base):
    """工作流模板（快速创建用，同理存文件）"""
    __tablename__ = "workflow_templates"

    id = Column(String(32), primary_key=True, default=gen_id)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    cover_url = Column(String(500), nullable=True)
    category = Column(String(50), nullable=True)  # text2image, image2image, video

    # JSON 文件相对路径
    json_path = Column(String(255), nullable=False)

    # 参数映射模板
    param_mapping_template = Column(Text, nullable=True)

    is_active = Column(Boolean, default=True)
    sort_order = Column(Integer, default=0)

    created_at = Column(DateTime(timezone=True), default=utcnow)
