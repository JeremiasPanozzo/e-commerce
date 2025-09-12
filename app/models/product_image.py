from app import db
from .basemodel import BaseModel
from sqlalchemy.dialects.postgresql import UUID

class ProductImage(BaseModel):
    __tablename__ = 'product_images'
    
    product_id = db.Column(UUID(as_uuid=True), db.ForeignKey('products.id'), nullable=False)
    variant_id = db.Column(UUID(as_uuid=True), db.ForeignKey('product_variants.id'))
    image_url = db.Column(db.String(500), nullable=False)
    alt_text = db.Column(db.String(255))
    sort_order = db.Column(db.Integer, default=0)
    is_primary = db.Column(db.Boolean, default=False)
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'image_url': self.image_url,
            'alt_text': self.alt_text,
            'sort_order': self.sort_order,
            'is_primary': self.is_primary
        }