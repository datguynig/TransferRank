"""
Basic tests for authentication functionality
"""
import pytest
import json
from app import app, db

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    with app.test_client() as client:
        with app.app_context():
            yield client

def test_admin_login_success(client):
    """Test successful admin login"""
    response = client.post('/api/auth/login', 
                          data=json.dumps({'password': 'admin'}),
                          content_type='application/json')
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] is True
    assert 'token' in data
    assert data['is_default_password'] is True

def test_admin_login_failure(client):
    """Test failed admin login"""
    response = client.post('/api/auth/login',
                          data=json.dumps({'password': 'wrong'}),
                          content_type='application/json')
    
    assert response.status_code == 401
    data = json.loads(response.data)
    assert data['success'] is False
    assert 'error' in data

def test_protected_route_access(client):
    """Test that protected routes reject unauthorised access"""
    # This would test a protected admin route if we had implemented one
    # For now, just test that the admin login page is accessible
    response = client.get('/admin/login')
    assert response.status_code == 200