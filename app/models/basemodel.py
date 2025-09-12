from app import db
from sqlalchemy.dialects.postgresql import UUID
import uuid
from sqlalchemy import func

class BaseModel(db.Model):
    """Modelo base con campos comunes"""
    __abstract__ = True
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = db.Column(db.DateTime(timezone=True), default=func.now())
    updated_at = db.Column(db.DateTime(timezone=True), default=func.now(), onupdate=func.now())