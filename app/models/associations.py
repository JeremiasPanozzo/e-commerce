from app import db
from sqlalchemy.dialects.postgresql import UUID

# Tabla de asociación para productos y categorías (many-to-many)
product_categories = db.Table('product_categories',
    db.Column('product_id', UUID(as_uuid=True), db.ForeignKey('products.id'), primary_key=True),
    db.Column('category_id', UUID(as_uuid=True), db.ForeignKey('categories.id'), primary_key=True)
)