from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from config import config

db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()

def create_app(config_name):
    
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # print(app.config['SQLALCHEMY_DATABñASE_URI'])
    # print(app.config['SECRET_KEY'])
    # print(app.config['JWT_SECRET_KEY'])
    # print(app.config['DEBUG'])
    
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)

    from app.api.auth import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/api/auth')    

    with app.app_context():
        from app.models import (Address, BaseModel, Cart, CartItem, 
                                Category, Coupon, Order, OrderItem, 
                                Payment, Product, ProductImage, 
                                ProductReview, ProductVariant, product_categories, 
                                User, Wishlist, RevokedToken
                )

    @app.errorhandler(404)
    def not_found(error):
        return {'error': 'Resource not found'}, 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return {'error': 'Internal server error'}, 500
    
    # Health check endpoint
    @app.route('/health')
    def health_check():
        return {'status': 'healthy'}, 200
    
    return app

