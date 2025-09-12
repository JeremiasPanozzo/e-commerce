from app import db
from sqlalchemy.dialects.postgresql import UUID
from .basemodel import BaseModel

class Wishlist(BaseModel):
    __tablename__ = 'wishlists'
    
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False)
    product_id = db.Column(UUID(as_uuid=True), db.ForeignKey('products.id'), nullable=False)
    
    # Relaciones
    product = db.relationship('Product')
    
    # Constraint única
    __table_args__ = (db.UniqueConstraint('user_id', 'product_id'),)
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'product_id': str(self.product_id),
            'product': self.product.to_dict() if self.product else None,
            'created_at': self.created_at.isoformat()
        }