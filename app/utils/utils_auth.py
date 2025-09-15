import re

def validate_password(password):
    """Validate password strength.
    Returns: (is_valid: bool, message: str)"""
    if not password:
        return False, "Password is required."
    
    if len(password) < 8:
        return False, "Password must be at least 8 characters long."

    if not re.search(r"[A-Z]", password):
        return False, "Password must contain uppercase letters."
    
    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter."
    
    if not re.search(r"[0-9]", password):
        return False, "Password must contain at least one digit."

    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False, "Password must contain at least one special character."

    return True, "Valid password."

def validate_email(email):
    """Validate email format."""
    if not email:
        return False, "Email is required."
    
    if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        return False, "Invalid email format."
    
    return True, "Email is valid."

def validate_phone(phone):
    """Validate phone number format (simple validation)."""
    if not phone:
        return True, "Phone number is optional."
    
    if not re.match(r"^\+?[0-9]{7,15}$", phone):
        return False, "Invalid phone number format."
    
    return True, "Phone number is valid."

def validate_date_of_birth(date_of_birth):
    if not date_of_birth:
        return True, "Date of birth is optional."
    
    