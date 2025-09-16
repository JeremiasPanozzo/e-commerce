from flask import Blueprint, request, jsonify
from sqlalchemy import or_, desc, asc
from ..models import Product, Category, ProductVariant, ProductImage, product_categories
from app import db
from decimal import Decimal
import re
import uuid

products_bp = Blueprint('products', __name__)

def is_valid_uuid(value):
    """Check if the value is a valid UUID"""
    try:
        uuid.UUID(str(value))
        return True
    except ValueError:
        return False

def validate_pagination_params(page, per_page):
    """Validate and sanitize pagination parameters"""
    if page < 1:
        page = 1
    if per_page < 1 or per_page > 100:  # Límite máximo de 100 items por página
        per_page = 10
    return page, per_page

def build_product_response(products_pagination, include_variants=False, include_images=False):
    """Build the response with products and pagination metadata"""
    products_list = []
    
    for product in products_pagination.items:
        product_data = product.to_dict()
        
        # Incluir variantes si se solicita
        if include_variants:
            variants = ProductVariant.query.filter_by(product_id=product.id, is_active=True).all()
            product_data['variants'] = [variant.to_dict() for variant in variants]
        
        # Incluir imágenes si se solicita
        if include_images:
            images = ProductImage.query.filter_by(product_id=product.id).order_by(ProductImage.sort_order).all()
            product_data['images'] = [image.to_dict() for image in images]
        
        # Incluir categorías
        categories = db.session.query(Category).join(product_categories).filter(
            product_categories.c.product_id == product.id
        ).all()
        product_data['categories'] = [cat.to_dict() for cat in categories]
        
        products_list.append(product_data)
    
    return {
        'products': products_list,
        'pagination': {
            'page': products_pagination.page,
            'per_page': products_pagination.per_page,
            'total': products_pagination.total,
            'pages': products_pagination.pages,
            'has_next': products_pagination.has_next,
            'has_prev': products_pagination.has_prev,
            'next_num': products_pagination.next_num,
            'prev_num': products_pagination.prev_num
        }
    }

@products_bp.route('/all', methods=['GET'])
def get_products():
    """Get all products with filters, search, and pagination"""
    try:
        # Pagination parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        page, per_page = validate_pagination_params(page, per_page)
        
        # Parámetros de filtros
        category_id = request.args.get('category_id')
        category_slug = request.args.get('category_slug')
        min_price = request.args.get('min_price', type=float)
        max_price = request.args.get('max_price', type=float)
        is_featured = request.args.get('is_featured', type=bool)
        in_stock = request.args.get('in_stock', type=bool)
        search = request.args.get('search', '').strip()
        
        # Parámetros de ordenamiento
        sort_by = request.args.get('sort_by', 'created_at')  # created_at, name, price
        sort_order = request.args.get('sort_order', 'desc')  # asc, desc
        
        # Parámetros adicionales
        include_variants = request.args.get('include_variants', False, type=bool)
        include_images = request.args.get('include_images', False, type=bool)
        
        # Construir query base
        query = Product.query.filter(Product.is_active == True)
        
        # Filtrar por categoría
        if category_slug:
            category = Category.query.filter_by(slug=category_slug).first()
            if not category:
                return jsonify({'error': 'Category not found.'}), 404
            category_id = category.id

        if category_id:
            if not is_valid_uuid(category_id):
                return jsonify({'error': 'Category ID not valid.'}), 400
            
        query = query.join(product_categories).filter(product_categories.c.category_id == category_id)

        # Filtrar por precio
        if min_price is not None:
            query = query.filter(Product.price >= Decimal(str(min_price)))
        if max_price is not None:
            query = query.filter(Product.price <= Decimal(str(max_price)))
        
        # Filtrar por destacados
        if is_featured is not None:
            query = query.filter(Product.is_featured == is_featured)
        
        # Filtrar por stock
        if in_stock:
            query = query.filter(Product.stock_quantity > 0)
        
        # Búsqueda por texto
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    Product.name.ilike(search_term),
                    Product.short_description.ilike(search_term),
                    Product.description.ilike(search_term),
                    Product.sku.ilike(search_term)
                )
            )
        
        # Aplicar ordenamiento
        if sort_by == 'name':
            order_column = Product.name
        elif sort_by == 'price':
            order_column = Product.price
        elif sort_by == 'created_at':
            order_column = Product.created_at
        else:
            order_column = Product.created_at
        
        if sort_order == 'asc':
            query = query.order_by(asc(order_column))
        else:
            query = query.order_by(desc(order_column))
        
        # Ejecutar paginación
        products_pagination = query.paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
        
        # Construir respuesta
        response = build_product_response(products_pagination, include_variants, include_images)
        
        return jsonify(response), 200
        
    except Exception as e:
        return jsonify({'error': 'Internal server error', 'details': str(e)}), 500

@products_bp.route('/<product_id>', methods=['GET'])
def get_product_by_id(product_id):
    """Get a specific product by ID"""
    try:
        # Validar formato UUID
        if not is_valid_uuid(product_id):
            return jsonify({'error': 'Invalid product ID. Must be a valid UUID.'}), 400
        
        product = Product.query.filter_by(id=product_id, is_active=True).first()
        if not product:
            return jsonify({'error': 'Product not found.'}), 404

        # Construir respuesta completa
        product_data = product.to_dict()
        
        # Incluir variantes
        variants = ProductVariant.query.filter_by(product_id=product.id, is_active=True).order_by(ProductVariant.created_at).all()
        product_data['variants'] = [variant.to_dict() for variant in variants]
        
        # Incluir imágenes
        images = ProductImage.query.filter_by(product_id=product.id).order_by(ProductImage.sort_order).all()
        product_data['images'] = [image.to_dict() for image in images]
        
        # Incluir categorías
        categories = db.session.query(Category).join(product_categories).filter(
            product_categories.c.product_id == product.id
        ).all()
        product_data['categories'] = [cat.to_dict() for cat in categories]
        
        return jsonify(product_data), 200
        
    except Exception as e:
        return jsonify({'error': 'Internal server error', 'details': str(e)}), 500

@products_bp.route('/slug/<slug>', methods=['GET'])
def get_product_by_slug(slug):
    """Get a specific product by slug"""
    try:
        product = Product.query.filter_by(slug=slug, is_active=True).first()
        if not product:
            return jsonify({'error': 'Product not found.'}), 404

        # Construir respuesta completa (similar a get_product_by_id)
        product_data = product.to_dict()
        
        # Incluir variantes
        variants = ProductVariant.query.filter_by(product_id=product.id, is_active=True).order_by(ProductVariant.created_at).all()
        product_data['variants'] = [variant.to_dict() for variant in variants]
        
        # Incluir imágenes
        images = ProductImage.query.filter_by(product_id=product.id).order_by(ProductImage.sort_order).all()
        product_data['images'] = [image.to_dict() for image in images]
        
        # Incluir categorías
        categories = db.session.query(Category).join(product_categories).filter(
            product_categories.c.product_id == product.id
        ).all()
        product_data['categories'] = [cat.to_dict() for cat in categories]
        
        return jsonify(product_data), 200
        
    except Exception as e:
        return jsonify({'error': 'Internal server error', 'details': str(e)}), 500

@products_bp.route('/featured', methods=['GET'])
def get_featured_products():
    """Get featured products"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        page, per_page = validate_pagination_params(page, per_page)
        
        include_variants = request.args.get('include_variants', False, type=bool)
        include_images = request.args.get('include_images', True, type=bool)
        
        products_pagination = Product.query.filter(
            Product.is_active == True,
            Product.is_featured == True
        ).order_by(desc(Product.created_at)).paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        response = build_product_response(products_pagination, include_variants, include_images)
        return jsonify(response), 200
        
    except Exception as e:
        return jsonify({'error': 'Internal server error', 'details': str(e)}), 500

@products_bp.route('/search', methods=['GET'])
def search_products():
    """Advanced product search"""
    try:
        search_term = request.args.get('q', '').strip()
        if not search_term:
            return jsonify({'error': 'Search term is required.'}), 400

        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        page, per_page = validate_pagination_params(page, per_page)
        
        # Búsqueda en múltiples campos
        search_pattern = f"%{search_term}%"
        products_pagination = Product.query.filter(
            Product.is_active == True,
            or_(
                Product.name.ilike(search_pattern),
                Product.short_description.ilike(search_pattern),
                Product.description.ilike(search_pattern),
                Product.sku.ilike(search_pattern)
            )
        ).order_by(
            # Priorizar coincidencias en el nombre
            Product.name.ilike(search_pattern).desc(),
            desc(Product.created_at)
        ).paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        response = build_product_response(products_pagination, include_images=True)
        response['search_term'] = search_term
        
        return jsonify(response), 200
        
    except Exception as e:
        return jsonify({'error': 'Internal server error', 'details': str(e)}), 500

@products_bp.route('/category/<category_slug>', methods=['GET'])
def get_products_by_category(category_slug):
    """Get products by specific category"""
    try:
        # Find category
        category = Category.query.filter_by(slug=category_slug, is_active=True).first()
        if not category:
            return jsonify({'error': 'Category not found.'}), 404

        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        page, per_page = validate_pagination_params(page, per_page)
        
        # Parámetros de ordenamiento
        sort_by = request.args.get('sort_by', 'created_at')
        sort_order = request.args.get('sort_order', 'desc')
        
        # Query de productos por categoría
        query = Product.query.join(product_categories).filter(
            product_categories.c.category_id == category.id,
            Product.is_active == True
        )
        
        # Aplicar ordenamiento
        if sort_by == 'name':
            order_column = Product.name
        elif sort_by == 'price':
            order_column = Product.price
        else:
            order_column = Product.created_at
        
        if sort_order == 'asc':
            query = query.order_by(asc(order_column))
        else:
            query = query.order_by(desc(order_column))
        
        products_pagination = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        response = build_product_response(products_pagination, include_images=True)
        response['category'] = category.to_dict()
        
        return jsonify(response), 200
        
    except Exception as e:
        return jsonify({'error': 'Internal server error', 'details': str(e)}), 500

@products_bp.route('/<product_id>/variants', methods=['GET'])
def get_product_variants(product_id):
    """Get product variants"""
    try:
        # Validate product exists
        product = Product.query.filter_by(id=product_id, is_active=True).first()
        if not product:
            return jsonify({'error': 'Product not found.'}), 404

        variants = ProductVariant.query.filter_by(
            product_id=product_id,
            is_active=True
        ).order_by(ProductVariant.created_at).all()
        
        variants_list = [variant.to_dict() for variant in variants]
        
        return jsonify({
            'product_id': product_id,
            'product_name': product.name,
            'variants': variants_list
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Internal server error', 'details': str(e)}), 500

@products_bp.route('/<product_id>/images', methods=['GET'])
def get_product_images(product_id):
    """Get product images"""
    try:
        # Validate product exists
        product = Product.query.filter_by(id=product_id, is_active=True).first()
        if not product:
            return jsonify({'error': 'Product not found.'}), 404

        images = ProductImage.query.filter_by(product_id=product_id).order_by(
            ProductImage.is_primary.desc(),
            ProductImage.sort_order
        ).all()
        
        images_list = [image.to_dict() for image in images]
        
        return jsonify({
            'product_id': product_id,
            'product_name': product.name,
            'images': images_list
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Internal server error', 'details': str(e)}), 500

@products_bp.route('/stats', methods=['GET'])
def get_products_stats():
    """Get basic product statistics"""
    try:
        total_products = Product.query.filter_by(is_active=True).count()
        featured_products = Product.query.filter_by(is_active=True, is_featured=True).count()
        out_of_stock = Product.query.filter(
            Product.is_active == True,
            Product.stock_quantity == 0
        ).count()
        low_stock = Product.query.filter(
            Product.is_active == True,
            Product.stock_quantity <= Product.low_stock_threshold,
            Product.stock_quantity > 0
        ).count()
        
        # Precio promedio
        avg_price_result = db.session.query(db.func.avg(Product.price)).filter(
            Product.is_active == True
        ).scalar()
        avg_price = float(avg_price_result) if avg_price_result else 0
        
        return jsonify({
            'total_products': total_products,
            'featured_products': featured_products,
            'out_of_stock': out_of_stock,
            'low_stock': low_stock,
            'average_price': round(avg_price, 2)
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Internal server error', 'details': str(e)}), 500

# Error handlers específicos para este blueprint
@products_bp.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Resource not found.'}), 404

@products_bp.errorhandler(400)
def bad_request(error):
    return jsonify({'error': 'Bad request.'}), 400