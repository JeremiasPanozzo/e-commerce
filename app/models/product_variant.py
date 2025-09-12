from app import db
from .basemodel import BaseModel
from sqlalchemy.dialects.postgresql import UUID, JSONB

class ProductVariant(BaseModel):
    __tablename__ = 'product_variants'
    
    product_id = db.Column(UUID(as_uuid=True), db.ForeignKey('products.id'), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    sku = db.Column(db.String(100), unique=True, nullable=False)
    price = db.Column(db.Numeric(10, 2))
    compare_price = db.Column(db.Numeric(10, 2))
    cost_price = db.Column(db.Numeric(10, 2))
    stock_quantity = db.Column(db.Integer, default=0)
    weight = db.Column(db.Numeric(8, 3))
    is_active = db.Column(db.Boolean, default=True)
    attributes = db.Column(JSONB) 

    images = db.relationship('ProductImage', backref='variant', cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'product_id': str(self.product_id),
            'name': self.name,
            'sku': self.sku,
            'price': float(self.price) if self.price else None,
            'compare_price': float(self.compare_price) if self.compare_price else None,
            'stock_quantity': self.stock_quantity,
            'weight': float(self.weight) if self.weight else None,
            'is_active': self.is_active,
            'attributes': self.attributes
        }