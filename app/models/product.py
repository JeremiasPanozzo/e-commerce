from app import db
from .basemodel import BaseModel
from sqlalchemy.dialects.postgresql import JSONB
from .associations import product_categories

class Product(BaseModel):
    __tablename__ = 'products'
    
    name = db.Column(db.String(255), nullable=False)
    slug = db.Column(db.String(255), unique=True, nullable=False, index=True)
    description = db.Column(db.Text)
    short_description = db.Column(db.String(500))
    sku = db.Column(db.String(100), unique=True, nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    compare_price = db.Column(db.Numeric(10, 2))
    cost_price = db.Column(db.Numeric(10, 2))
    weight = db.Column(db.Numeric(8, 3))
    dimensions = db.Column(JSONB)
    is_active = db.Column(db.Boolean, default=True, index=True)
    is_featured = db.Column(db.Boolean, default=False, index=True)
    stock_quantity = db.Column(db.Integer, default=0)
    low_stock_threshold = db.Column(db.Integer, default=5)
    manage_stock = db.Column(db.Boolean, default=True)
    allow_backorders = db.Column(db.Boolean, default=False)
    meta_title = db.Column(db.String(255))
    meta_description = db.Column(db.Text)

    categories = db.relationship('Category', secondary=product_categories, backref='products')
    variants = db.relationship('ProductVariant', backref='product', cascade='all, delete-orphan')
    images = db.relationship('ProductImage', backref='product', cascade='all, delete-orphan')
    reviews = db.relationship('ProductReview', backref='product', cascade='all, delete-orphan')
   
    @property
    def average_rating(self):
        if not self.reviews:
            return 0
        return sum(review.rating for review in self.reviews) / len(self.reviews)
    
    @property
    def is_in_stock(self):
        if not self.manage_stock:
            return True
        return self.stock_quantity > 0 or self.allow_backorders
    
    def to_dict(self, include_variants=False, include_images=False):
        data = {
            'id': str(self.id),
            'name': self.name,
            'slug': self.slug,
            'description': self.description,
            'short_description': self.short_description,
            'sku': self.sku,
            'price': float(self.price),
            'compare_price': float(self.compare_price) if self.compare_price else None,
            'weight': float(self.weight) if self.weight else None,
            'dimensions': self.dimensions,
            'is_active': self.is_active,
            'is_featured': self.is_featured,
            'stock_quantity': self.stock_quantity,
            'is_in_stock': self.is_in_stock,
            'average_rating': self.average_rating,
            'review_count': len(self.reviews)
        }

        if include_variants:
            data['variants'] = [variant.to_dict() for variant in self.variants]
        
        if include_images:
            data['images'] = [image.to_dict() for image in self.images]
            
        return data