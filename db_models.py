from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from data_base import Base

class ProcessedImage(Base):
    __tablename__ = "processed_images"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    processing_type = Column(String(50), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)