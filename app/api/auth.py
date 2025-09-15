from flask import Blueprint, current_app, request, jsonify
from ..models.user import User
from ..models import RevokedToken
from app import db, jwt
from ..utils.utils_auth import validate_email, validate_password
from flask_jwt_extended import (
    create_access_token, create_refresh_token, 
    jwt_required, jwt_required, get_jwt, jwt_required, get_jwt,
    get_jwt_identity
)

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():

    """Register a new user."""
    request_data = request.get_json()
    
    """Validate request data."""
    if not request_data:
        return jsonify({"msg": "Missing JSON in request"}), 400
    
    required_fields = ['email', 'password', 'first_name', 'last_name']

    """"Check for missing fields."""
    for field in required_fields:
        if field not in request_data:
            return jsonify({"msg": f"Missing {field} parameter"}), 400
        
    email = request_data.get('email')
    password = request_data.get('password')
    first_name = request_data.get('first_name')
    last_name = request_data.get('last_name')
    phone = request_data.get('phone').strip() if request_data.get('phone') else None
    date_of_birth = request_data.get('date_of_birth').strip() if request_data.get('date_of_birth') else None

    """Validate email format."""
    email_valid, email_msg = validate_email(email)
    if email_valid is False:
        return jsonify({"msg": email_msg}), 400

    """Validate password strength."""
    password_valid, password_msg = validate_password(password)
    if password_valid is False:
        return jsonify({"msg": password_msg}), 400

    """Check if user already exists."""
    if User.filter_by_email(email):
        return jsonify({"msg": "User already exists"}), 400
    
    """Save user to database."""
    try:
        """Create new user instance."""
        user = User(email, password, first_name, last_name, phone, date_of_birth)

        user.save()
        return jsonify({
            'message': 'User registered successfully',
            'user': user.to_dict(),
            'access_token': 'access_token',
            'refresh_token': '',
            'token_type': 'Bearer'
        }), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({"msg": str(e)}), 500
    
@auth_bp.route('/login',methods=['POST'])
def login():

    """Login a user and return JWT tokens"""
    request_data = request.get_json()

    email = request_data.get('email')
    password = request_data.get('password')

    if not email or not password:
        return jsonify({"msg":"Missing email or password"}), 400
    
    user = User.filter_by_email(email)
    
    if not user or not user.check_password(password):
        return jsonify({"msg":"Invalid email or password"}), 401
    
    access_token = create_access_token(identity=str(user.id))
    refresh_token = create_refresh_token(identity=str(user.id))

    return jsonify({"access_token": access_token, "refresh_token": refresh_token})

@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():

    """Loggout a user by revoking their JWT token."""
    jti = get_jwt()['jti']
    try:
        revoked_token = RevokedToken(jti)
        db.session.add(revoked_token)
        db.session.commit()
        return jsonify({"msg": "Successfully logged out"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"msg": str(e)}), 500

@auth_bp.route('/profile', methods=['GET'])
@jwt_required()
def profile():

    user_id = get_jwt_identity()
    user = User.find_by_id(user_id)

    if not user:
        return jsonify({"msg": "User not found"}), 404
    
    return jsonify({
        'user': user.to_dict()
    })
    
## Errors token handlers ##
@jwt.token_in_blocklist_loader
def check_if_token_revoked(jwt_header, jwt_payload):
    jti = jwt_payload["jti"]
    return RevokedToken.query.filter_by(jti=jti).first() is not None

@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_data):
    return jsonify({"message": "Token has expired"}), 401

@jwt.invalid_token_loader
def invalid_token_callback(error):
    return jsonify({"message": "Invalid token", "error": str(error)}), 401

@jwt.unauthorized_loader
def missing_token_callback(error):
    return jsonify({"message": "Request does not contain an access token", "error": str(error)}), 401