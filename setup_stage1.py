import os

directories = [
    "backend",
    "backend/app",
    "backend/app/models",
    "backend/app/routes",
    "backend/app/services",
    "backend/app/schemas",
    "backend/app/middleware",
    "backend/app/utils",
    "backend/migrations",
    "backend/tests"
]

for d in directories:
    os.makedirs(d, exist_ok=True)

files = {
    "backend/requirements.txt": """Flask==3.0.3
Flask-SQLAlchemy==3.1.1
Flask-Migrate==4.0.7
psycopg2-binary==2.9.9
python-dotenv==1.0.1
PyJWT==2.8.0
Werkzeug==3.0.2
gunicorn==22.0.0""",
    
    "backend/.env": """FLASK_APP=run.py
FLASK_ENV=development
DATABASE_URL=postgresql://postgres:postgres@db:5432/hackmysore
JWT_SECRET_KEY=super-secret-key-replace-in-prod""",
    
    "backend/.gitignore": """venv/
__pycache__/
*.pyc
.env
.pytest_cache/
coverage.xml
.coverage
htmlcov/
instance/""",
    
    "backend/Dockerfile": """FROM python:3.11-slim

WORKDIR /app

# Install dependencies for psycopg2
RUN apt-get update && apt-get install -y libpq-dev gcc

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Run gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "run:app"]""",
    
    "backend/docker-compose.yml": """version: '3.8'

services:
  web:
    build: .
    ports:
      - "5000:5000"
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@db:5432/hackmysore
      - FLASK_APP=run.py
      - FLASK_ENV=development
    volumes:
      - .:/app
    depends_on:
      - db
    command: flask run --host=0.0.0.0 --port=5000

  db:
    image: postgres:15-alpine
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
      - POSTGRES_DB=hackmysore
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:""",

    "backend/run.py": """import os
from app import create_app
from app.extensions import db

app = create_app()

if __name__ == '__main__':
    app.run(debug=True)""",
    
    "backend/app/__init__.py": """import os
from flask import Flask
from .extensions import db, migrate
from .config import Config

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)

    # Register blueprints
    from .routes.auth import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/api/auth')

    # Create tables if not using migrations for initial setup (optional, here we rely on migrations)
    with app.app_context():
        # Import models here to ensure they are registered with SQLAlchemy
        from .models import user, organization
        # db.create_all()

    return app""",
    
    "backend/app/config.py": """import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'hard-to-guess-string'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'postgresql://postgres:postgres@localhost:5432/hackmysore'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'super-secret-jwt-key'""",
    
    "backend/app/extensions.py": """from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

db = SQLAlchemy()
migrate = Migrate()""",
    
    "backend/app/models/__init__.py": """""",
    
    "backend/app/models/organization.py": """from app.extensions import db
from datetime import datetime

class Organization(db.Model):
    __tablename__ = 'organizations'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(50), nullable=False) # 'Company', 'Institution', etc.
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    users = db.relationship('User', backref='organization', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'type': self.type,
            'created_at': self.created_at.isoformat()
        }""",
    
    "backend/app/models/user.py": """from app.extensions import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(50), nullable=False) # 'STUDENT', 'RECRUITER', 'ADMIN'
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'role': self.role,
            'organization_id': self.organization_id,
            'created_at': self.created_at.isoformat()
        }""",
    
    "backend/app/middleware/__init__.py": """""",
    
    "backend/app/middleware/auth.py": """from functools import wraps
from flask import request, jsonify, current_app
import jwt
from app.models.user import User

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header.startswith('Bearer '):
                token = auth_header.split(" ")[1]

        if not token:
            return jsonify({'message': 'Token is missing!'}), 401

        try:
            data = jwt.decode(token, current_app.config['JWT_SECRET_KEY'], algorithms=["HS256"])
            current_user = User.query.filter_by(id=data['user_id']).first()
            if not current_user:
                raise Exception("User not found")
        except Exception as e:
            return jsonify({'message': 'Token is invalid!', 'error': str(e)}), 401

        return f(current_user, *args, **kwargs)
    return decorated

def role_required(role):
    def decorator(f):
        @wraps(f)
        def decorated_function(current_user, *args, **kwargs):
            if current_user.role != role:
                return jsonify({'message': 'Permission denied. Role mismatch.'}), 403
            return f(current_user, *args, **kwargs)
        return decorated_function
    return decorator""",

    "backend/app/routes/__init__.py": """""",
    
    "backend/app/routes/auth.py": """from flask import Blueprint, request, jsonify, current_app
from app.models.user import User
from app.models.organization import Organization
from app.extensions import db
from app.middleware.auth import token_required
import jwt
import datetime

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    role = data.get('role', 'STUDENT')
    org_id = data.get('organization_id')

    if User.query.filter_by(email=email).first():
        return jsonify({'message': 'User already exists'}), 400

    new_user = User(email=email, role=role, organization_id=org_id)
    new_user.set_password(password)

    db.session.add(new_user)
    db.session.commit()

    return jsonify({'message': 'Registered successfully', 'user': new_user.to_dict()}), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    user = User.query.filter_by(email=email).first()
    
    if not user or not user.check_password(password):
        return jsonify({'message': 'Login failed. Invalid credentials.'}), 401

    token = jwt.encode({
        'user_id': user.id,
        'role': user.role,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
    }, current_app.config['JWT_SECRET_KEY'], algorithm="HS256")

    return jsonify({'token': token, 'user': user.to_dict()}), 200

@auth_bp.route('/me', methods=['GET'])
@token_required
def get_me(current_user):
    return jsonify({'user': current_user.to_dict()}), 200"""
}

for filepath, content in files.items():
    with open(filepath, "w") as f:
        f.write(content)

print("Scaffolding complete.")
