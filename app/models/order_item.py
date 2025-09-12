from app import db
from .basemodel import BaseModel
from sqlalchemy.dialects.postgresql import UUID, JSONB

class OrderItem(BaseModel):
    __tablename__ = 'order_items'
    
    order_id = db.Column(UUID(as_uuid=True), db.ForeignKey('orders.id'), nullable=False)
    product_id = db.Column(UUID(as_uuid=True), db.ForeignKey('products.id'))
    variant_id = db.Column(UUID(as_uuid=True), db.ForeignKey('product_variants.id'))
    product_name = db.Column(db.String(255), nullable=False)
    product_sku = db.Column(db.String(100), nullable=False)
    variant_attributes = db.Column(JSONB)
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)
    total_price = db.Column(db.Numeric(10, 2), nullable=False)
    
    # Relaciones
    product = db.relationship('Product')
    variant = db.relationship('ProductVariant')
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'product_id': str(self.product_id) if self.product_id else None,
            'variant_id': str(self.variant_id) if self.variant_id else None,
            'product_name': self.product_name,
            'product_sku': self.product_sku,
            'variant_attributes': self.variant_attributes,
            'quantity': self.quantity,
            'unit_price': float(self.unit_price),
            'total_price': float(self.total_price)
        }