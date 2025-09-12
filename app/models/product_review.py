from app import db
from sqlalchemy.dialects.postgresql import UUID
from .basemodel import BaseModel

class ProductReview(BaseModel):
    __tablename__ = 'product_reviews'
    
    product_id = db.Column(UUID(as_uuid=True), db.ForeignKey('products.id'), nullable=False)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False)
    order_id = db.Column(UUID(as_uuid=True), db.ForeignKey('orders.id'))
    rating = db.Column(db.Integer, nullable=False)
    title = db.Column(db.String(255))
    comment = db.Column(db.Text)
    is_verified = db.Column(db.Boolean, default=False)
    is_approved = db.Column(db.Boolean, default=False)
    helpful_votes = db.Column(db.Integer, default=0)
    
    # Constraint única para evitar múltiples reviews del mismo producto por el mismo usuario/orden
    __table_args__ = (db.UniqueConstraint('product_id', 'user_id', 'order_id'),)
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'product_id': str(self.product_id),
            'user_id': str(self.user_id),
            'rating': self.rating,
            'title': self.title,
            'comment': self.comment,
            'is_verified': self.is_verified,
            'is_approved': self.is_approved,
            'helpful_votes': self.helpful_votes,
            'user_name': self.user.full_name,
            'created_at': self.created_at.isoformat()
        }