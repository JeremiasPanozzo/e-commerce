from app import db
from .basemodel import BaseModel
from werkzeug.security import generate_password_hash, check_password_hash

class User(BaseModel):

    __tablename__ = 'users'
    
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20))
    date_of_birth = db.Column(db.Date)
    is_active = db.Column(db.Boolean, default=True)
    is_verified = db.Column(db.Boolean, default=False)

    addresses = db.relationship('Address', backref='user', cascade='all, delete-orphan')
    carts = db.relationship('Cart', backref='user', cascade='all, delete-orphan')
    orders = db.relationship('Order', backref='user')
    reviews = db.relationship('ProductReview', backref='user', cascade='all, delete-orphan')
    wishlist = db.relationship('Wishlist', backref='user', cascade='all, delete-orphan')
        
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'full_name': self.full_name,
            'phone': self.phone,
            'date_of_birth': self.date_of_birth.isoformat() if self.date_of_birth else None,
            'is_active': self.is_active,
            'is_verified': self.is_verified,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }