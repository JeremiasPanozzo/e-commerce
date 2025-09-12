from app import db
from .basemodel import BaseModel
from datetime import datetime

class Coupon(BaseModel):
    __tablename__ = 'coupons'
    
    code = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(255))
    discount_type = db.Column(db.String(20), nullable=False)  # 'percentage' or 'fixed_amount'
    discount_value = db.Column(db.Numeric(10, 2), nullable=False)
    minimum_amount = db.Column(db.Numeric(10, 2))
    maximum_discount = db.Column(db.Numeric(10, 2))
    usage_limit = db.Column(db.Integer)
    used_count = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    valid_from = db.Column(db.DateTime(timezone=True))
    valid_until = db.Column(db.DateTime(timezone=True))
    
    def is_valid(self, order_amount=None):
        now = datetime.utcnow()
        
        # Verificar si está activo
        if not self.is_active:
            return False, "Cupón no válido"
        
        if self.minimum_amount and order_amount and order_amount < self.minimum_amount:
            return False, f"Monto mínimo requerido: ${self.minimum_amount}"

        return True, "Cupón válido"
    
    def calculate_discount(self, order_amount):
        if self.discount_type == 'percentage':
            discount = order_amount * (self.discount_value / 100)
            if self.maximum_discount:
                discount = min(discount, self.maximum_discount)
            return discount
        else:  # fixed_amount
            return min(self.discount_value, order_amount)
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'code': self.code,
            'description': self.description,
            'discount_type': self.discount_type,
            'discount_value': float(self.discount_value),
            'minimum_amount': float(self.minimum_amount) if self.minimum_amount else None,
            'maximum_discount': float(self.maximum_discount) if self.maximum_discount else None,
            'is_active': self.is_active,
            'valid_from': self.valid_from.isoformat() if self.valid_from else None,
            'valid_until': self.valid_until.isoformat() if self.valid_until else None
        }
