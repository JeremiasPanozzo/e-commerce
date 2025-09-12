from app import db
from .basemodel import BaseModel
from sqlalchemy.dialects.postgresql import UUID

class CartItem(BaseModel):
    __tablename__ = 'cart_items'
    
    cart_id = db.Column(UUID(as_uuid=True), db.ForeignKey('carts.id'), nullable=False)
    product_id = db.Column(UUID(as_uuid=True), db.ForeignKey('products.id'), nullable=False)
    variant_id = db.Column(UUID(as_uuid=True), db.ForeignKey('product_variants.id'))
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)
    
    # Relaciones
    product = db.relationship('Product')
    variant = db.relationship('ProductVariant')
    
    @property
    def total_price(self):
        return self.unit_price * self.quantity
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'product_id': str(self.product_id),
            'variant_id': str(self.variant_id) if self.variant_id else None,
            'product_name': self.product.name,
            'quantity': self.quantity,
            'unit_price': float(self.unit_price),
            'total_price': float(self.total_price)
        }