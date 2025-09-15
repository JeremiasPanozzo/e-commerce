from app import db
from .basemodel import BaseModel
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.exc import OperationalError, InterfaceError, DBAPIError

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
        
    def __init__(self, email, password, first_name, last_name, phone=None, date_of_birth=None):
        super().__init__()
        self.email = email
        self.set_password(password)
        self.first_name = first_name
        self.last_name = last_name
        self.phone = phone
        self.date_of_birth = date_of_birth

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    @classmethod
    def filter_by_email(cls, email):
        return cls.query.filter_by(email=email).first()
    
    @classmethod
    def find_by_id(cls, user_id):
        return cls.query.get(user_id)
    
    @classmethod
    def find_by_username(cls, username):
        return cls.query.filter_by(username=username).first()
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    def save(self):
        try:
            db.session.add(self)
            db.session.commit()
        except (OperationalError, InterfaceError, DBAPIError) as db_error:
            db.session.rollback()
            raise RuntimeError("Database error") from db_error
        except Exception as e:
            db.session.rollback()
            raise e
    
    def delete(self):
        try:
            db.session.delete(self)
            db.session.commit()
        except (OperationalError, InterfaceError, DBAPIError) as db_error:
            db.session.rollback()
            raise RuntimeError("Database error") from db_error
        except Exception as e:
            db.session.rollback()
            raise e

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