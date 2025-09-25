# 🛒 E-commerce API

Este proyecto es una **API RESTful** para un sistema de e-commerce construida con **Flask**, que gestiona autenticación, productos, carritos de compra y usuarios.  

## 🚀 Tecnologías

- [Flask](https://flask.palletsprojects.com/) - Framework principal
- [Flask-SQLAlchemy](https://flask-sqlalchemy.palletsprojects.com/) - ORM para base de datos
- [Flask-Migrate](https://flask-migrate.readthedocs.io/) + [Alembic](https://alembic.sqlalchemy.org/) - Migraciones de base de datos
- [Flask-JWT-Extended](https://flask-jwt-extended.readthedocs.io/) - Autenticación con JWT
- [PostgreSQL](https://www.postgresql.org/) - Base de datos
- [python-dotenv](https://pypi.org/project/python-dotenv/) - Manejo de variables de entorno

---

## 📦 Instalación

1. Clona este repositorio:

```bash
git clone https://github.com/tuusuario/ecommerce-api.git
cd ecommerce-api
```
2. Crea un entorno virtual e instala dependencias:

```bash
python -m venv venv
source venv/bin/activate   # En Linux/Mac
venv\Scripts\activate      # En Windows

pip install -r requirements.txt
```

3. Configura variables de entorno (.env):

```bash
FLASK_APP=app.py
FLASK_ENV=development
DATABASE_URL=postgresql+psycopg2://usuario:password@localhost:5432/ecommerce
JWT_SECRET_KEY=supersecretkey
```

4. Inicializa la base de datos:

```bash
flask db init
flask db migrate
flask db upgrade
```
5. Ejecuta el servidor:

```bash
python run
```

## Endpoints
🔐 Autenticación (/api/auth)

- POST /api/auth/register → Registrar usuario
- POST /api/auth/login → Iniciar sesión
- POST /api/auth/logout → Cerrar sesión
- DELETE /api/auth/delete → Eliminar cuenta

🛍️ Carrito (/api/cart)

- POST /api/cart/add → Agregar producto
- DELETE /api/cart/cart/remove/<item_id> → Eliminar producto
- PUT /api/cart/cart/update → Actualizar producto
- GET /api/cart/get_cart → Ver carrito
- GET /api/cart/cart/count → Contar ítems
- DELETE /api/cart/cart/clear → Vaciar carrito
- POST /api/cart/cart/merge → Fusionar carrito de invitado

👤 Usuario (/api/user)

- POST /api/user/change_password → Cambiar contraseña
- POST /api/user/address → Editar dirección
- GET /api/user/profile → Ver perfil

📦 Productos (/api/products)

- GET /api/products/all → Listar productos
- GET /api/products/<product_id> → Obtener producto por ID
- GET /api/products/slug/<slug> → Obtener producto por slug
- GET /api/products/featured → Productos destacados
- GET /api/products/category/<category_slug> → Productos por categoría
- GET /api/products/<product_id>/images → Imágenes del producto
- GET /api/products/<product_id>/variants → Variantes del producto
- GET /api/products/search → Buscar productos
- GET /api/products/stats → Estadísticas de productos

🌐 Otros

- GET / → Bienvenida API
- GET /static/<path:filename> → Archivos estáticos

🛠️ Dependencias 

```bash
alembic==1.16.5
blinker==1.9.0
click==8.2.1
colorama==0.4.6
Flask==3.1.2
Flask-Alembic==3.1.1
Flask-JWT-Extended==4.7.1
Flask-Migrate==4.1.0
Flask-SQLAlchemy==3.1.1
greenlet==3.2.4
itsdangerous==2.2.0
Jinja2==3.1.6
Mako==1.3.10
MarkupSafe==3.0.2
psycopg2==2.9.10
psycopg2-binary==2.9.10
PyJWT==2.10.1
python-dotenv==1.1.1
SQLAlchemy==2.0.43
typing_extensions==4.15.0
Werkzeug==3.1.3
```
