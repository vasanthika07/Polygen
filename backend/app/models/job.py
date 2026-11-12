import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship, synonym
from app.core.database import Base

class GenerationJob(Base):
    __tablename__ = "generation_jobs"

    id = Column(String, primary_key=True, default=lambda: f"job_{uuid.uuid4().hex[:12]}", index=True)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    prompt = Column(Text, nullable=False)
    configuration = Column(JSON, nullable=True) # Stores {style, quality, polygon_budget, target_format, texture_resolution}
    status = Column(String(32), default="pending", index=True) # pending, queued, processing, completed, failed
    progress = Column(Integer, default=0) # 0 to 100
    current_stage = Column(String(64), default="queued") # prompt_processing, mesh_generation, uv_mapping, texture_generation, mesh_optimization, material_assignment, glb_export, completed
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)

    # job_id property synonym for backward compatibility with frontend / legacy routes
    job_id = synonym("id")

    # Relationships
    user = relationship("User", back_populates="jobs")
    asset = relationship("GeneratedAsset", back_populates="job", uselist=False, cascade="all, delete-orphan")
