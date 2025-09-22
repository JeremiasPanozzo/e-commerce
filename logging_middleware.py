from flask import request, g, current_app
from flask_jwt_extended import get_jwt_identity
import logging
import uuid
import time
from functools import wraps
from logger_config import log_error, log_warning, log_info

def setup_request_logging(app):
    """Configura el logging de requests y responses"""
    
    logger = logging.getLogger('e-commerce_logger')
    
    @app.before_request
    def before_request():
        """Se ejecuta antes de cada request"""
        # Generar ID único para la request
        g.request_id = str(uuid.uuid4())[:8]
        g.start_time = time.time()
        
        # Obtener información del usuario si está logueado
        try:
            user_id = get_jwt_identity()
            g.user_id = user_id
        except:
            g.user_id = None
        
        # Log de la request entrante (solo para endpoints importantes)
        if should_log_request():
            context = {
                'endpoint': request.endpoint,
                'args': dict(request.args),
                'form_data': dict(request.form) if request.form else None,
                'json_data': request.get_json(silent=True) if request.is_json else None,
                'content_length': request.content_length
            }
            
            # Filtrar datos sensibles
            context = filter_sensitive_data(context)
            
            log_info(
                logger, 
                f"Request started: {request.method} {request.path}",
                context=context,
                user_id=g.user_id
            )
    
    @app.after_request
    def after_request(response):
        """Se ejecuta después de cada request"""
        # Calcular tiempo de respuesta
        if hasattr(g, 'start_time'):
            response_time = time.time() - g.start_time
        else:
            response_time = 0
        
        # Log de la response (solo para endpoints importantes)
        if should_log_request():
            context = {
                'status_code': response.status_code,
                'response_time': f"{response_time:.3f}s",
                'content_length': response.content_length
            }
            
            log_level = 'info'
            if response.status_code >= 400:
                log_level = 'warning' if response.status_code < 500 else 'error'
            
            message = f"Request completed: {request.method} {request.path}"
            
            if log_level == 'error':
                log_error(logger, message, context=context, user_id=g.user_id)
            elif log_level == 'warning':
                log_warning(logger, message, context=context, user_id=g.user_id)
            else:
                log_info(logger, message, context=context, user_id=g.user_id)
        
        return response
    
    @app.errorhandler(Exception)
    def handle_exception(e):
        """Maneja todas las excepciones no capturadas"""
        logger = logging.getLogger('e-commerce_logger')
        
        context = {
            'endpoint': request.endpoint,
            'method': request.method,
            'path': request.path,
            'args': dict(request.args),
            'user_id': getattr(g, 'user_id', None)
        }
        
        log_error(logger, e, context=context, user_id=getattr(g, 'user_id', None))
        
        # Retornar respuesta genérica para errores 500
        if current_app.config['DEBUG']:
            return {'error': 'Internal server error', 'details': str(e)}, 500
        else:
            return {'error': 'Internal server error'}, 500

def should_log_request():
    """Determina si se debe loggear la request basado en el endpoint"""
    # No loggear requests estáticas, health checks, etc.
    skip_paths = ['/favicon.ico', '/static/', '/health']
    skip_endpoints = ['static']
    
    if any(request.path.startswith(path) for path in skip_paths):
        return False
    
    if request.endpoint in skip_endpoints:
        return False
    
    return True

def filter_sensitive_data(data):
    """Filtra datos sensibles de los logs"""
    if not isinstance(data, dict):
        return data
    
    sensitive_keys = [
        'password', 'token', 'secret', 'key', 'auth',
        'authorization', 'credit_card', 'ssn', 'social_security'
    ]
    
    filtered_data = {}
    for key, value in data.items():
        if isinstance(key, str) and any(sensitive in key.lower() for sensitive in sensitive_keys):
            filtered_data[key] = '***REDACTED***'
        elif isinstance(value, dict):
            filtered_data[key] = filter_sensitive_data(value)
        elif isinstance(value, list):
            filtered_data[key] = [filter_sensitive_data(item) if isinstance(item, dict) else item for item in value]
        else:
            filtered_data[key] = value
    
    return filtered_data

def log_database_operation(operation, table, record_id=None, user_id=None):
    """Decorator para loggear operaciones de base de datos"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger = logging.getLogger('e-commerce_logger')
            
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                
                execution_time = time.time() - start_time
                context = {
                    'operation': operation,
                    'table': table,
                    'record_id': record_id,
                    'execution_time': f"{execution_time:.3f}s",
                    'success': True
                }
                
                log_info(
                    logger,
                    f"Database operation completed: {operation} on {table}",
                    context=context,
                    user_id=user_id or getattr(g, 'user_id', None)
                )
                
                return result
                
            except Exception as e:
                execution_time = time.time() - start_time
                context = {
                    'operation': operation,
                    'table': table,
                    'record_id': record_id,
                    'execution_time': f"{execution_time:.3f}s",
                    'success': False,
                    'error_details': str(e)
                }
                
                log_error(
                    logger,
                    f"Database operation failed: {operation} on {table}",
                    context=context,
                    user_id=user_id or getattr(g, 'user_id', None)
                )
                
                raise
        
        return wrapper
    return decorator

def log_business_operation(operation_name, **context_data):
    """Decorator para loggear operaciones de negocio importantes"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger = logging.getLogger('e-commerce_logger')
            
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                
                execution_time = time.time() - start_time
                context = {
                    'operation': operation_name,
                    'execution_time': f"{execution_time:.3f}s",
                    'success': True,
                    **context_data
                }
                
                log_info(
                    logger,
                    f"Business operation completed: {operation_name}",
                    context=context,
                    user_id=getattr(g, 'user_id', None)
                )
                
                return result
                
            except Exception as e:
                execution_time = time.time() - start_time
                context = {
                    'operation': operation_name,
                    'execution_time': f"{execution_time:.3f}s",
                    'success': False,
                    'error_details': str(e),
                    **context_data
                }
                
                log_error(
                    logger,
                    f"Business operation failed: {operation_name}",
                    context=context,
                    user_id=getattr(g, 'user_id', None)
                )
                
                raise
        
        return wrapper
    return decorator