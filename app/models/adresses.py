from app import db
from .basemodel import BaseModel
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.exc import OperationalError, InterfaceError, DBAPIError

class Address(BaseModel):
    __tablename__ = 'addresses'
    
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False)
    street_address = db.Column(db.String(255), nullable=False)
    apartment = db.Column(db.String(100))
    city = db.Column(db.String(100), nullable=False)
    state = db.Column(db.String(100), nullable=False)
    postal_code = db.Column(db.String(20), nullable=False)
    country = db.Column(db.String(100), nullable=False, default='Argentina')
    is_default = db.Column(db.Boolean, default=False)
    address_type = db.Column(db.String(20), default='shipping')

    def __init__(self, user_id, street_address, apartment, city, state, postal_code, country='Argentina', is_default=False, address_type='shipping'):
        self.user_id = user_id
        self.street_address = street_address
        self.apartment = apartment
        self.city = city
        self.state = state
        self.postal_code = postal_code
        self.country = country
        self.is_default = is_default
        self.address_type = address_type

    @property
    def full_address(self):
        address_parts = [self.street_address]
        if self.apartment:
            address_parts.append(f"Apt {self.apartment}")
        address_parts.extend([self.city, self.state, self.postal_code])
        return ", ".join(address_parts)
    
    def save(self):
        try:
            db.session.add(self)
            db.session.commit()
        except (OperationalError, InterfaceError, DBAPIError) as db_error:
            db.session.rollback()
            raise RuntimeError("Database error occurred") from db_error

    def delete(self):
        try:
            db.session.delete(self)
            db.session.commit()
        except (OperationalError, InterfaceError, DBAPIError) as db_error:
            db.session.rollback()
            raise RuntimeError("Database error occurred") from db_error

    def to_dict(self):
        return {
            'id': str(self.id),
            'street_address': self.street_address,
            'apartment': self.apartment,
            'city': self.city,
            'state': self.state,
            'postal_code': self.postal_code,
            'country': self.country,
            'is_default': self.is_default,
            'address_type': self.address_type,
            'full_address': self.full_address
        }