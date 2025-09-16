from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import User, Address
from app import db
from ..utils.utils_auth import validate_password

edit_user_bp = Blueprint('edit_user', __name__)

@edit_user_bp.route('/address', methods=['POST'])
@jwt_required()
def edit_address():
    """Create an address from an authenticated user."""
    user_id = get_jwt_identity()
    user = User.find_by_id(user_id)

    if not user:
        return jsonify({"msg": "User not found"}), 404
    
    request_data = request.get_json()

    if not request_data:
        return jsonify({"msg": "Missing JSON in request"}), 400

    required_fields = ['country', 'apartment', 'street_address', 'city', 'state', 'postal_code']
    for field in required_fields:
        if field not in request_data:
            return jsonify({"msg": f"Missing {field} parameter"}), 400
        
    street = request_data.get('street_address')
    apartment = request_data.get('apartment')
    city = request_data.get('city')
    state = request_data.get('state')
    postal_code = request_data.get('postal_code')
    country = request_data.get('country', 'Argentina')
    
    address = Address(
        user_id=user.id,
        street_address=street,
        apartment=apartment,
        city=city,
        state=state,
        postal_code=postal_code,
        country=country
    )

    address.save()
    return jsonify({"msg": "Address created successfully", "address": address.to_dict()}), 201

@edit_user_bp.route('/change_password', methods=['POST'])
@jwt_required()
def change_password():
    """Change password for an authenticated user."""
    user_id = get_jwt_identity()
    user = User.find_by_id(user_id)

    if not user:
        return jsonify({"msg": "User not found"}), 404
    
    request_data = request.get_json()

    if not request_data:
        return jsonify({"msg": "Missing JSON in request"}), 400
    
    old_password = request_data.get('old_password')
    new_password = request_data.get('new_password')

    if not old_password or not new_password:
        return jsonify({"msg": "Both old_password and new_password are required"}), 400
    
    if not user.check_password(old_password):
        return jsonify({"msg": "Old password is incorrect"}), 400
    
    if old_password == new_password:
        return jsonify({"msg": "New password must be different from the old password"}), 400

    password_valid, password_msg = validate_password(new_password)
    
    if password_valid is False:
        return jsonify({"msg": password_msg}), 400

    user.set_password(new_password)
    try:
        user.save()
    except Exception as e:
        return jsonify({"msg": "Failed to update password", "error": str(e)}), 500

    return jsonify({"msg": "Password updated successfully"}), 200