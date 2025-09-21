from app import db
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid

class RevokedToken(db.Model):

    """Revoked Token model."""
    
    __tablename__ = "revoked_tokens"
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    jti = db.Column(db.String(120), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())

    @classmethod
    def add(cls, jti):
        revoked_token = cls(jti=jti)
        db.session.add(revoked_token)
        db.session.commit()
        
    def __init__(self, jti):
        self.jti = jti