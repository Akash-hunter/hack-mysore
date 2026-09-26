import os
import sys
import tempfile
import sqlite3
import json

# Add backend to path
sys.path.insert(0, os.path.abspath('backend'))

from app import create_app
from app.extensions import db
from app.models.user import User

def test_auth():
    # Use in-memory SQLite for testing
    app = create_app()
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['TESTING'] = True
    
    with app.app_context():
        # Create all tables (models are imported in app/__init__.py or already registered)
        db.create_all()
        
        client = app.test_client()
        
        print("1. Testing Registration...")
        register_data = {
            "email": "test@example.com",
            "password": "password123",
            "role": "STUDENT"
        }
        resp = client.post('/api/auth/register', json=register_data)
        print("Register Status:", resp.status_code)
        print("Register Response:", resp.json)
        assert resp.status_code == 201
        
        print("\n2. Testing Login...")
        login_data = {
            "email": "test@example.com",
            "password": "password123"
        }
        resp = client.post('/api/auth/login', json=login_data)
        print("Login Status:", resp.status_code)
        print("Login Response:", resp.json)
        assert resp.status_code == 200
        assert 'token' in resp.json
        
        token = resp.json['token']
        
        print("\n3. Testing Protected Route (/api/auth/me)...")
        headers = {
            'Authorization': f'Bearer {token}'
        }
        resp = client.get('/api/auth/me', headers=headers)
        print("Get Me Status:", resp.status_code)
        print("Get Me Response:", resp.json)
        assert resp.status_code == 200
        assert resp.json['user']['email'] == "test@example.com"
        
        print("\nAuthentication Flow is WORKING correctly!")

if __name__ == '__main__':
    test_auth()
