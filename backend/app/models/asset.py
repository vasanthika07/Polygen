import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship, synonym
from app.core.database import Base

class GeneratedAsset(Base):
    __tablename__ = "generated_assets"

    id = Column(String, primary_key=True, default=lambda: f"asset_{uuid.uuid4().hex[:12]}", index=True)
    job_id = Column(String, ForeignKey("generation_jobs.id", ondelete="CASCADE"), unique=True, index=True, nullable=False)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    asset_name = Column(String(255), nullable=False)
    original_prompt = Column(Text, nullable=True)
    glb_path = Column(String(512), nullable=False)
    thumbnail_path = Column(String(512), nullable=True)
    polygon_count = Column(Integer, nullable=False, default=0)
    file_size = Column(Integer, nullable=False, default=0) # in bytes
    texture_resolution = Column(Integer, nullable=False, default=1024)
    # Mapping to "metadata" database column while avoiding conflict with SQLAlchemy Base.metadata
    metadata_json = Column("metadata", JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Synonyms for frontend and legacy compatibility
    asset_id = synonym("id")
    preview_path = synonym("thumbnail_path")

    # Relationships
    job = relationship("GenerationJob", back_populates="asset")
    user = relationship("User", back_populates="assets")
