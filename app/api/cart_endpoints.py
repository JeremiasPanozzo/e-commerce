from flask import Blueprint, request, jsonify, session
from flask_jwt_extended import jwt_required, get_jwt_identity, jwt_required
from sqlalchemy.exc import SQLAlchemyError
from ..models import Cart, CartItem, Product, ProductVariant
from app import db
from decimal import Decimal
import uuid

cart_bp = Blueprint('cart', __name__)

def get_or_create_cart(user_id=None, session_id=None):

    """Get an existing cart or create a new one"""
    if user_id: # If user is logged in
        cart = Cart.query.filter_by(user_id=user_id).first() # Try to find cart by user_id
        if not cart: # If no cart found, create a new one
            cart = Cart(user_id=user_id) # Create new cart for user
            db.session.add(cart) # Add to session
            db.session.commit() # Save to DB
    elif session_id: # If user is anonymous
        cart = Cart.query.filter_by(session_id=session_id).first() # Try to find cart by session_id
        if not cart: # If no cart found, create a new one
            cart = Cart(session_id=session_id)
            db.session.add(cart)
            db.session.commit()
    else:
        return None
    
    return cart

def calculate_cart_totals(cart_id):
    """Calculate subtotal and total items in the cart"""
    cart_items = CartItem.query.filter_by(cart_id=cart_id).all()
    
    subtotal = Decimal('0.00')
    total_items = 0
    
    # Loop through items to calculate totals
    for item in cart_items:
        item_total = Decimal(str(item.unit_price)) * item.quantity
        subtotal += item_total
        total_items += item.quantity
    
    return {
        'subtotal': float(subtotal),
        'total_items': total_items,
        'items_count': len(cart_items)
    }

def validate_product_and_variant(product_id, variant_id=None):
    """Validate product and optional variant"""
    # Find the product
    product = Product.query.filter_by(id=product_id, is_active=True).first()
    if not product:
        return None, None, "Product not found"
    
    # Si hay variante, verificarla
    variant = None
    if variant_id:
        variant = ProductVariant.query.filter_by(
            id=variant_id, 
            product_id=product_id, 
            is_active=True
        ).first()
        if not variant:
            return None, None, "Variant not found or does not belong to the product"
    
    return product, variant, None

@cart_bp.route('/get_cart', methods=['GET'])
@jwt_required(optional=True)
def get_cart():

    """Get the current user's cart or session cart"""
    try:
        user_id = get_jwt_identity()
        
        # Check or create session_id for anonymous users
        if not user_id: # If user is not logged in
            session_id = session.get('cart_session_id') # Retrieve from session
            if not session_id: # If not session_id in session, first time user visit this site
                # Create a new session_id
                session_id = str(uuid.uuid4())
                # Save it in session
                session['cart_session_id'] = session_id
        else:
            # If user is logged in, no need for session_id
            session_id = None
        
        cart = get_or_create_cart(user_id, session_id) # Get or create cart
        
        # This should never happen, but just in case
        if not cart:
            return jsonify({"error": "Critical error"}), 500
        
        # Get cart items with product and variant details
        cart_items = db.session.query(CartItem).join(Product).filter(
            CartItem.cart_id == cart.id,
            Product.is_active == True
        ).all()
        
        items_data = [] # List to hold time details
        for item in cart_items: # Loop through each cart item
            item_data = item.to_dict() # Start with basic item info
            
            # Add product details
            product = item.product # Access related product
            item_data['product'] = { 
                'id': str(product.id),
                'name': product.name,
                'slug': product.slug,
                'price': float(product.price),
                'stock_quantity': product.stock_quantity,
                'is_active': product.is_active
            }
            
            # If there's a variant, add its details
            if item.variant_id:
                variant = item.variant
                if variant:
                    item_data['variant'] = {
                        'id': str(variant.id),
                        'name': variant.name,
                        'price': float(variant.price) if variant.price else float(product.price),
                        'stock_quantity': variant.stock_quantity,
                        'attributes': variant.attributes
                    }
                    # Use variant price if available, otherwise product price
                    item_data['current_price'] = float(variant.price) if variant.price else float(product.price)
                else:
                    # Variant ID is set but variant not found (maybe deleted)
                    item_data['variant'] = None
                    item_data['is_available'] = False
            else:
                item_data['current_price'] = float(product.price)
            
            # Check stock availability
            available_stock = variant.stock_quantity if item.variant_id and variant else product.stock_quantity
            item_data['is_available'] = available_stock >= item.quantity
            item_data['available_stock'] = available_stock
            
            items_data.append(item_data)
        
        # Calculate cart totals
        totals = calculate_cart_totals(cart.id)
        
        return jsonify({
            "cart_id": str(cart.id),
            "user_id": str(user_id) if user_id else None,
            "session_id": session_id,
            "items": items_data,
            "totals": totals,
            "updated_at": cart.updated_at.isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({"error": "Internal server error", "details": str(e)}), 500

@cart_bp.route('/add', methods=['POST'])
@jwt_required(optional=True)
def add_to_cart():
    """Add a product (and optional variant) to the cart"""
    try:
        data = request.get_json()
        
        # product_id is required
        if not data or 'product_id' not in data:
            return jsonify({"error": "product_id is required"}), 400
        
        product_id = data.get('product_id') # Required
        variant_id = data.get('variant_id') # Optional
        quantity = data.get('quantity', 1)  # Quantity to add, default to 1
        
        # Validar quantity
        if not isinstance(quantity, int) or quantity <= 0:
            return jsonify({"error": "Quantity must be an integer and greater than 0"}), 400
        
        if quantity > 10:  # Limit to 10 items per addition
            return jsonify({"error": "Maximum quantity allowed: 10"}), 400
        
        # Validate product and variant
        product, variant, error = validate_product_and_variant(product_id, variant_id)
        if error:
            return jsonify({"error": error}), 404
        
        # Check stock availability
        available_stock = variant.stock_quantity if variant else product.stock_quantity
        if available_stock < quantity: # Not enough stock
            return jsonify({
                "error": "Not enough stock available",
                "available_stock": available_stock
            }), 400
        
        user_id = get_jwt_identity() # Get user ID if logged in

        # For anonymous users, ensure session_id exists
        if not user_id: # If user is not logged in
            session_id = session.get('cart_session_id') # Retrieve from session
            if not session_id: # If not session_id in session, first time user visit this site
                session_id = str(uuid.uuid4()) # Create a new session_id
                session['cart_session_id'] = session_id
        else: # If user is logged in, no need for session_id
            session_id = None
        
        cart = get_or_create_cart(user_id, session_id) # Get or create cart
        
        # Check if item already exists in cart
        existing_item = CartItem.query.filter_by(
            cart_id=cart.id,
            product_id=product_id,
            variant_id=variant_id
        ).first()
        
        # If item exists, update quantity
        if existing_item:
            # Update quantity
            new_quantity = existing_item.quantity + quantity
            
            # Check stock against available stock
            if available_stock < new_quantity:
                return jsonify({
                    "error": "Insufficient stock for the requested quantity",
                    "current_in_cart": existing_item.quantity,
                    "available_stock": available_stock,
                    "max_additional": available_stock - existing_item.quantity
                }), 400
            
            existing_item.quantity = new_quantity
            existing_item.updated_at = db.func.current_timestamp()
            
        else:
            # Create new cart item
            unit_price = variant.price if variant and variant.price else product.price
            
            cart_item = CartItem(
                cart_id=cart.id,
                product_id=product_id,
                variant_id=variant_id,
                quantity=quantity,
                unit_price=unit_price
            )
            
            db.session.add(cart_item)
        
        # Update cart timestamp
        cart.updated_at = db.func.current_timestamp()
        
        db.session.commit()
        
        # Calculate new totals
        totals = calculate_cart_totals(cart.id)
        
        return jsonify({
            "message": "Product successfully added to cart",
            "cart_id": str(cart.id),
            "product_name": product.name,
            "quantity_added": quantity,
            "totals": totals
        }), 200
        
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"error": "Database error", "details": str(e)}), 500
    except Exception as e:
        return jsonify({"error": "Internal server", "details": str(e)}), 500

@cart_bp.route('/cart/update', methods=['PUT'])
@jwt_required(optional=True)
def update_cart_item():
    """Update the quantity of a specific cart item"""
    try:
        data = request.get_json()
        
        # Check required fields
        if not data or 'item_id' not in data or 'quantity' not in data:
            return jsonify({"error": "item_id and quantity are required"}), 400
        
        item_id = data.get('item_id') # ID of the cart item to update
        quantity = data.get('quantity') # New quantity
        
        # Check quantity validity
        if not isinstance(quantity, int) or quantity < 0:
            return jsonify({"error": "Quantity must be an integer and greater than 0"}), 400
        
        # Limit to 10 items per update
        if quantity > 10:
            return jsonify({"error": "Maximum quantity allowed: 10"}), 400
        
        # Get the cart item
        cart_item = CartItem.query.filter_by(id=item_id).first()
        if not cart_item:
            return jsonify({"error": "Item not found"}), 404
        
        # Check permissions
        user_id = get_jwt_identity()
        session_id = session.get('cart_session_id') if not user_id else None
        
        # Get de cart associated with the item
        cart = Cart.query.filter_by(id=cart_item.cart_id).first()
        if not cart or (cart.user_id != user_id and cart.session_id != session_id):
            return jsonify({"error": "Do not have permission to modify this cart"}), 403
        
        # If quantity is 0, remove the item
        if quantity == 0:
            product_name = cart_item.product.name # Get product name for message
            db.session.delete(cart_item) # Delete the item
            db.session.commit()
            
            totals = calculate_cart_totals(cart.id) # Recalculate totals
            return jsonify({
                "message": f"Remove '{product_name}' from cart",
                "totals": totals
            }), 200
        
        # Verificar stock disponible
        product = cart_item.product
        variant = cart_item.variant if cart_item.variant_id else None
        available_stock = variant.stock_quantity if variant else product.stock_quantity
        
        if available_stock < quantity:
            return jsonify({
                "error": "Not enough stock available",
                "requested_quantity": quantity,
                "available_stock": available_stock
            }), 400
        
        # Actualizar cantidad
        cart_item.quantity = quantity
        cart_item.updated_at = db.func.current_timestamp()
        cart.updated_at = db.func.current_timestamp()
        
        db.session.commit()
        
        totals = calculate_cart_totals(cart.id)
        
        return jsonify({
            "message": "Quantity updated successfully",
            "item_id": str(cart_item.id),
            "new_quantity": quantity,
            "product_name": product.name,
            "totals": totals
        }), 200
        
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"error": "Database error", "details": str(e)}), 500
    except Exception as e:
        return jsonify({"error": "Internal Server Error", "details": str(e)}), 500

@cart_bp.route('/cart/remove/<item_id>', methods=['DELETE'])
@jwt_required(optional=True)
def remove_from_cart(item_id):
    """Delete a specific item from the cart"""
    try:
        # Validate UUID
        try:
            uuid.UUID(item_id)
        except ValueError:
            return jsonify({"error": "Invalid UUID"}), 400
        
        # Get the item
        cart_item = CartItem.query.filter_by(id=item_id).first()
        if not cart_item:
            return jsonify({"error": "Item not found on cart"}), 404
        
        # Check permissions
        user_id = get_jwt_identity()
        session_id = session.get('cart_session_id') if not user_id else None
        
        cart = Cart.query.filter_by(id=cart_item.cart_id).first()
        if not cart or (cart.user_id != user_id and cart.session_id != session_id):
            return jsonify({"error": "Do not have permission"}), 403
        
        product_name = cart_item.product.name
        
        # Eliminar item
        db.session.delete(cart_item)
        cart.updated_at = db.func.current_timestamp()
        db.session.commit()
        
        # Recalcular totales
        totals = calculate_cart_totals(cart.id)
        
        return jsonify({
            "message": f"Product '{product_name}' deleted from cart",
            "removed_item_id": item_id,
            "totals": totals
        }), 200
        
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"error": "Database error", "details": str(e)}), 500
    except Exception as e:
        return jsonify({"error": "Internal server error", "details": str(e)}), 500

@cart_bp.route('/cart/clear', methods=['DELETE'])
@jwt_required(optional=True)
def clear_cart():
    """Clean all items from the cart"""
    try:
        user_id = get_jwt_identity()
        session_id = session.get('cart_session_id') if not user_id else None
        
        # Buscar carrito
        if user_id:
            cart = Cart.query.filter_by(user_id=user_id).first()
        elif session_id:
            cart = Cart.query.filter_by(session_id=session_id).first()
        else:
            return jsonify({"error": "Cart not found"}), 404
        
        if not cart:
            return jsonify({"error": "Cart not found"}), 404
        
        # Contar items antes de eliminar
        items_count = CartItem.query.filter_by(cart_id=cart.id).count()
        
        # Eliminar todos los items
        CartItem.query.filter_by(cart_id=cart.id).delete()
        cart.updated_at = db.func.current_timestamp()
        
        db.session.commit()
        
        return jsonify({
            "message": f"Carrito vaciado exitosamente. {items_count} items eliminados",
            "cart_id": str(cart.id)
        }), 200
        
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"error": "Error de base de datos", "details": str(e)}), 500
    except Exception as e:
        return jsonify({"error": "Error interno del servidor", "details": str(e)}), 500

@cart_bp.route('/cart/merge', methods=['POST'])
@jwt_required()
def merge_guest_cart():
    """Fusiona carrito de invitado con carrito de usuario logueado"""
    try:
        data = request.get_json()
        guest_session_id = data.get('guest_session_id')
        
        if not guest_session_id:
            return jsonify({"error": "guest_session_id es requerido"}), 400
        
        user_id = get_jwt_identity()
        
        # Obtener carrito de invitado
        guest_cart = Cart.query.filter_by(session_id=guest_session_id).first()
        if not guest_cart:
            return jsonify({"error": "Carrito de invitado no encontrado"}), 404
        
        # Obtener o crear carrito de usuario
        user_cart = get_or_create_cart(user_id=user_id)
        
        # Obtener items del carrito de invitado
        guest_items = CartItem.query.filter_by(cart_id=guest_cart.id).all()
        merged_items = 0
        
        for guest_item in guest_items:
            # Verificar si el item ya existe en el carrito del usuario
            existing_item = CartItem.query.filter_by(
                cart_id=user_cart.id,
                product_id=guest_item.product_id,
                variant_id=guest_item.variant_id
            ).first()
            
            if existing_item:
                # Sumar cantidades
                existing_item.quantity += guest_item.quantity
                existing_item.updated_at = db.func.current_timestamp()
            else:
                # Crear nuevo item en carrito de usuario
                new_item = CartItem(
                    cart_id=user_cart.id,
                    product_id=guest_item.product_id,
                    variant_id=guest_item.variant_id,
                    quantity=guest_item.quantity,
                    unit_price=guest_item.unit_price
                )
                db.session.add(new_item)
            
            merged_items += 1
        
        # Eliminar carrito de invitado
        CartItem.query.filter_by(cart_id=guest_cart.id).delete()
        db.session.delete(guest_cart)
        
        # Actualizar timestamp del carrito de usuario
        user_cart.updated_at = db.func.current_timestamp()
        
        db.session.commit()
        
        totals = calculate_cart_totals(user_cart.id)
        
        return jsonify({
            "message": f"Carrito fusionado exitosamente. {merged_items} items procesados",
            "cart_id": str(user_cart.id),
            "totals": totals
        }), 200
        
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"error": "Error de base de datos", "details": str(e)}), 500
    except Exception as e:
        return jsonify({"error": "Error interno del servidor", "details": str(e)}), 500

@cart_bp.route('/cart/count', methods=['GET'])
@jwt_required(optional=True)
def get_cart_count():
    """Obtiene el conteo rápido de items en el carrito"""
    try:
        user_id = get_jwt_identity()
        session_id = session.get('cart_session_id') if not user_id else None
        
        # Buscar carrito
        if user_id:
            cart = Cart.query.filter_by(user_id=user_id).first()
        elif session_id:
            cart = Cart.query.filter_by(session_id=session_id).first()
        else:
            return jsonify({"items_count": 0, "total_quantity": 0}), 200
        
        if not cart:
            return jsonify({"items_count": 0, "total_quantity": 0}), 200
        
        # Contar items y cantidad total
        result = db.session.query(
            db.func.count(CartItem.id),
            db.func.sum(CartItem.quantity)
        ).filter(CartItem.cart_id == cart.id).first()
        
        items_count = result[0] or 0
        total_quantity = result[1] or 0
        
        return jsonify({
            "items_count": items_count,
            "total_quantity": int(total_quantity),
            "cart_id": str(cart.id)
        }), 200
        
    except Exception as e:
        return jsonify({"error": "Error interno del servidor", "details": str(e)}), 500

# Error handlers
@cart_bp.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Recurso no encontrado'}), 404

@cart_bp.errorhandler(400)
def bad_request(error):
    return jsonify({'error': 'Solicitud inválida'}), 400

@cart_bp.errorhandler(403)
def forbidden(error):
    return jsonify({'error': 'Acceso denegado'}), 403