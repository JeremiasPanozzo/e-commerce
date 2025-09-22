from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from config import config
import logging

db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()

from logger_config import setup_logging, log_error, log_info, log_warning
from logging_middleware import setup_request_logging

def create_app(config_name='development'):
    
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    app.config['LOGS_DIR'] = app.config.get('LOGS_DIR', 'dir')
    
    logger = setup_logging(app)
    setup_request_logging(app)

    log_info(logger,f"Starting e-commerce API in {config_name} mode")

    try:
        db.init_app(app)
        migrate.init_app(app, db)
        jwt.init_app(app)
        log_info(logger, "Flask extensions initialized successfully")
    except Exception as e:
        log_error(logger, f"Failed to initialize Flask extension: {e}")
        raise

    try:
        from app.api.auth_endpoints import auth_bp
        from app.api.user_endpoints import edit_user_bp
        from app.api.products_endpoints import products_bp
        from app.api.cart_endpoints import cart_bp

        app.register_blueprint(auth_bp, url_prefix='/api/auth')    
        app.register_blueprint(edit_user_bp, url_prefix='/api/user')
        app.register_blueprint(products_bp, url_prefix='/api/products')
        app.register_blueprint(cart_bp, url_prefix='/api/cart/')
        log_info(logger, f"All blueprint registered succesfully")
    except Exception as e:
        log_error(logger, f"Failed to registered blueprints: {e}")
        raise

    with app.app_context():
        try:
            from app.models import (Address, BaseModel, Cart, CartItem, 
                                Category, Coupon, Order, OrderItem, 
                                Payment, Product, ProductImage, 
                                ProductReview, ProductVariant, product_categories, 
                                User, Wishlist, RevokedToken
                    )
            log_info(logger, "Models imported succeesfully")
        except Exception as e:
            log_error(logger, f"Failed to import models: {e}")
            raise

    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        user_id = jwt_payload.get('sub', 'unknown')
        log_info(logger, "JWT token expired", {'user_id': user_id})
        return {'error': 'Token has expired'}, 401

    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        log_warning(logger, "Invalid JWT token", {'error': str(error)})
        return {'error': 'Invalid token'}, 401

    @jwt.unauthorized_loader
    def unauthorized_callback(error):
        log_info(logger, "Unauthorized access attempt", {'error': str(error)})
        return {'error': 'Authorization token required'}, 401

    # Error handlers con logging
    @app.errorhandler(404)
    def not_found(error):
        log_warning("404 Not Found", {
            'path': request.path,
            'method': request.method,
            'remote_addr': request.remote_addr
        })
        return {'error': 'Resource not found'}, 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        
        log_error("500 Internal Server Error", error, {
            'path': request.path,
            'method': request.method,
            'remote_addr': request.remote_addr
        })
        
        if app.config['DEBUG']:
            return {'error': 'Internal server error', 'details': str(error)}, 500
        else:
            return {'error': 'Internal server error'}, 500

    @app.errorhandler(400)
    def bad_request(error):
        log_warning("400 Bad Request", {
            'path': request.path,
            'method': request.method,
            'error': str(error)
        })
        return {'error': 'Bad request'}, 400

    @app.errorhandler(403)
    def forbidden(error):
        log_warning("403 Forbidden", {
            'path': request.path,
            'method': request.method,
            'error': str(error)
        })
        return {'error': 'Access forbidden'}, 403

    # Health check endpoint
    @app.route('/', methods=['GET'])
    def welcome_api():
        log_info("Health check endpoint accessed", {'remote_addr': request.remote_addr})
        return {'msg': 'Welcome to e-commerce API.'}, 200
    
    # Endpoint para probar logging (solo en desarrollo)
    if app.config['DEBUG']:
        @app.route('/api/logs/test', methods=['GET'])
        def test_logging():
            logger.debug("Debug message test")
            logger.info("Info message test")
            logger.warning("Warning message test")
            logger.error("Error message test")
            return {'message': 'Logging test completed. Check log files.'}, 200
                
    log_info(logger, "E-commerce API initialized successfully")
    
    return app