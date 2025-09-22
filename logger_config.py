import logging
import logging.handlers
import os
from datetime import datetime
from flask import request, g
import traceback
import sys
import app

class RequestFormatter(logging.Formatter):
    """Custom formatter to include request information in logs."""

    def format(self, record):
        # Basic information about the request
        record.timestamp = datetime.now().isoformat()

        try:
            record.url = request.url if request else 'N/A'
            record.method = request.method if request else 'N/A'
            record.remote_addr = request.remote_addr if request else 'N/A'
            record.user_agent = request.user_agent if request else 'N/A'
            record.request_id = getattr(g, 'request_id', 'N/A')

            headers = {}

            if request:
                safe_headers = ['Content-Type', 'Accept', 'Authorization']

                for header in safe_headers:
                    if header in request.headers:
                        value = request.headers[header]

                        if header == 'Authorization' and value:
                            value = f"{value[:20]}..." if len(value) > 20 else value
                        headers[header] = value
            
            record.headers = str(headers)

        except RuntimeError:
            record.url = 'N/A'
            record.method = 'N/A'
            record.remote_addr = 'N/A'
            record.user_agent = 'N/A'
            record.request_id = 'N/A'
            record.headers = 'N/A'

        return super().format(record)
    
def setup_logging(app):
    """"""
    logs_dir = app.config.get('LOGS_DIR', 'logs')
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)

    logger = logging.getLogger('e-commerce_logger')
    logger.setLevel(logging.DEBUG if app.config['DEBUG'] else logging.INFO)

    logger.handlers.clear()

    detailed_formatter = RequestFormatter(
        fmt='%(timestamp)s - %(levelname)s - %(name)s - '
            'ReqID: %(request_id)s - %(method)s %(url)s - '
            'IP: %(remote_addr)s - %(message)s - '
            'Headers: %(headers)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    simple_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(name)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Handler para errores (archivo rotativo)
    error_handler = logging.handlers.RotatingFileHandler(
        filename=os.path.join(logs_dir, 'error.log'),
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(detailed_formatter)
    
    # Handler para todos los logs (archivo rotativo)
    all_handler = logging.handlers.RotatingFileHandler(
        filename=os.path.join(logs_dir, 'app.log'),
        maxBytes=10*1024*1024,  # 10MB
        backupCount=10,
        encoding='utf-8'
    )
    all_handler.setLevel(logging.INFO)
    all_handler.setFormatter(detailed_formatter)
    
    # Handler para consola (solo en desarrollo)
    if app.config['DEBUG']:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(simple_formatter)
        logger.addHandler(console_handler)
    
    # Añadir handlers al logger
    logger.addHandler(error_handler)
    logger.addHandler(all_handler)
    
    # Handler específico para SQLAlchemy (opcional)
    sqlalchemy_logger = logging.getLogger('sqlalchemy')
    if app.config['DEBUG']:
        sqlalchemy_logger.setLevel(logging.INFO)
        sqlalchemy_handler = logging.handlers.RotatingFileHandler(
            filename=os.path.join(logs_dir, 'sqlalchemy.log'),
            maxBytes=5*1024*1024,  # 5MB
            backupCount=3,
            encoding='utf-8'
        )
        sqlalchemy_handler.setFormatter(simple_formatter)
        sqlalchemy_logger.addHandler(sqlalchemy_handler)
    
    return logger

def log_error(logger, error, context=None, user_id=None):
    """
    Función auxiliar para loggear errores con contexto adicional
    
    Args:
        logger: Instancia del logger
        error: Excepción o mensaje de error
        context: Contexto adicional (dict)
        user_id: ID del usuario si está disponible
    """
    error_info = {
        'error_type': type(error).__name__ if hasattr(error, '__class__') else 'Unknown',
        'error_message': str(error),
        'user_id': user_id,
        'context': context or {},
        'traceback': traceback.format_exc() if isinstance(error, Exception) else 'N/A'
    }
    
    logger.error(f"Error occurred: {error_info}")

def log_warning(logger, message, context=None, user_id=None):
    """
    Función auxiliar para loggear warnings
    
    Args:
        logger: Instancia del logger
        message: Mensaje de warning
        context: Contexto adicional (dict)
        user_id: ID del usuario si está disponible
    """
    warning_info = {
        'message': message,
        'user_id': user_id,
        'context': context or {}
    }
    
    logger.warning(f"Warning: {warning_info}")

def log_info(logger, message, context=None, user_id=None):
    """
    Función auxiliar para loggear información
    
    Args:
        logger: Instancia del logger
        message: Mensaje informativo
        context: Contexto adicional (dict)
        user_id: ID del usuario si está disponible
    """
    info_data = {
        'message': message,
        'user_id': user_id,
        'context': context or {}
    }
    
    logger.info(f"Info: {info_data}")

