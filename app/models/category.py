from app import db
from .basemodel import BaseModel
from sqlalchemy.dialects.postgresql import UUID

class Category(BaseModel):
    __tablename__ = 'categories'
    
    name = db.Column(db.String(100), nullable=False)
    slug = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)
    parent_id = db.Column(UUID(as_uuid=True), db.ForeignKey('categories.id'))
    image_url = db.Column(db.String(500))
    is_active = db.Column(db.Boolean, default=True)
    sort_order = db.Column(db.Integer, default=0)

    children = db.relationship('Category', backref=db.backref('parent', remote_side=lambda: [Category.id]))

    def to_dict(self):
        return {
            'id': str(self.id),
            'name': self.name,
            'slug': self.slug,
            'description': self.description,
            'parent_id': str(self.parent_id) if self.parent_id else None,
            'image_url': self.image_url,
            'is_active': self.is_active,
            'sort_order': self.sort_order
        }
    