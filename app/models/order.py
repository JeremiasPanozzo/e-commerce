from app import db
from .basemodel import BaseModel
from sqlalchemy.dialects.postgresql import UUID, JSONB

class Order(BaseModel):
    __tablename__ = 'orders'
    
    order_number = db.Column(db.String(50), unique=True, nullable=False)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'))
    status = db.Column(db.String(20), default='pending', index=True)
    payment_status = db.Column(db.String(20), default='pending')
    
    # Importes
    subtotal = db.Column(db.Numeric(10, 2), nullable=False)
    tax_amount = db.Column(db.Numeric(10, 2), default=0)
    shipping_amount = db.Column(db.Numeric(10, 2), default=0)
    discount_amount = db.Column(db.Numeric(10, 2), default=0)
    total_amount = db.Column(db.Numeric(10, 2), nullable=False)
    
    # Información de envío y facturación
    shipping_address = db.Column(JSONB, nullable=False)
    billing_address = db.Column(JSONB, nullable=False)
    shipping_method = db.Column(db.String(100))
    tracking_number = db.Column(db.String(100))
    
    # Cupón aplicado
    coupon_id = db.Column(UUID(as_uuid=True), db.ForeignKey('coupons.id'))
    coupon_code = db.Column(db.String(50))
    
    # Notas
    customer_notes = db.Column(db.Text)
    admin_notes = db.Column(db.Text)
    
    # Fechas especiales
    shipped_at = db.Column(db.DateTime(timezone=True))
    delivered_at = db.Column(db.DateTime(timezone=True))
    
    # Relaciones
    items = db.relationship('OrderItem', backref='order', cascade='all, delete-orphan')
    payments = db.relationship('Payment', backref='order', cascade='all, delete-orphan')
    coupon = db.relationship('Coupon')
    
    def to_dict(self, include_items=False):
        data = {
            'id': str(self.id),
            'order_number': self.order_number,
            'status': self.status,
            'payment_status': self.payment_status,
            'subtotal': float(self.subtotal),
            'tax_amount': float(self.tax_amount),
            'shipping_amount': float(self.shipping_amount),
            'discount_amount': float(self.discount_amount),
            'total_amount': float(self.total_amount),
            'shipping_address': self.shipping_address,
            'billing_address': self.billing_address,
            'shipping_method': self.shipping_method,
            'tracking_number': self.tracking_number,
            'coupon_code': self.coupon_code,
            'customer_notes': self.customer_notes,
            'shipped_at': self.shipped_at.isoformat() if self.shipped_at else None,
            'delivered_at': self.delivered_at.isoformat() if self.delivered_at else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
        
        if include_items:
            data['items'] = [item.to_dict() for item in self.items]
            
        return data