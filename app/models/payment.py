from app import db
from .basemodel import BaseModel
from sqlalchemy.dialects.postgresql import UUID, JSONB

class Payment(BaseModel):
    __tablename__ = 'payments'
    
    order_id = db.Column(UUID(as_uuid=True), db.ForeignKey('orders.id'), nullable=False)
    payment_method = db.Column(db.String(50), nullable=False)
    payment_provider = db.Column(db.String(50))
    transaction_id = db.Column(db.String(255))
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    currency = db.Column(db.String(3), default='ARS')
    status = db.Column(db.String(20), default='pending')
    payment_data = db.Column(JSONB)
    processed_at = db.Column(db.DateTime(timezone=True))
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'order_id': str(self.order_id),
            'payment_method': self.payment_method,
            'payment_provider': self.payment_provider,
            'transaction_id': self.transaction_id,
            'amount': float(self.amount),
            'currency': self.currency,
            'status': self.status,
            'processed_at': self.processed_at.isoformat() if self.processed_at else None,
            'created_at': self.created_at.isoformat()
        }