import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base

class GeneratedAsset(Base):
    __tablename__ = "generated_assets"

    asset_id = Column(String, primary_key=True, default=lambda: f"asset_{uuid.uuid4().hex[:12]}", index=True)
    job_id = Column(String, ForeignKey("generation_jobs.job_id", ondelete="CASCADE"), unique=True, index=True, nullable=False)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    asset_name = Column(String(255), nullable=False)
    glb_path = Column(String(512), nullable=False)
    preview_path = Column(String(512), nullable=True)
    polygon_count = Column(Integer, nullable=False, default=0)
    file_size = Column(Integer, nullable=False, default=0) # in bytes
    texture_resolution = Column(Integer, nullable=False, default=1024)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    job = relationship("GenerationJob", back_populates="asset")
    user = relationship("User", back_populates="assets")

