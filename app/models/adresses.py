from app import db
from .basemodel import BaseModel
from sqlalchemy.dialects.postgresql import UUID

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

    @property
    def full_address(self):
        address_parts = [self.street_address]
        if self.apartment:
            address_parts.append(f"Apt {self.apartment}")
        address_parts.extend([self.city, self.state, self.postal_code])
        return ", ".join(address_parts)
    
    def save(self):
        db.session.add(self)
        db.session.commit()
    
    def delet(self):
        db.session.delete(self)
        db.session.commit()
        
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