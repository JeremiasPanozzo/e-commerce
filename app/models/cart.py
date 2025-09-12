from app import db
from .basemodel import BaseModel
from sqlalchemy.dialects.postgresql import UUID

class Cart(BaseModel):
    __tablename__ = 'carts'
    
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'))
    session_id = db.Column(db.String(255))
    
    # Relaciones
    items = db.relationship('CartItem', backref='cart', cascade='all, delete-orphan')
    
    @property
    def total_items(self):
        return sum(item.quantity for item in self.items)
    
    @property
    def subtotal(self):
        return sum(item.total_price for item in self.items)
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'total_items': self.total_items,
            'subtotal': float(self.subtotal),
            'items': [item.to_dict() for item in self.items],
            'created_at': self.created_at.isoformat()
        }