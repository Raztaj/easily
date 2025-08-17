import pytest
from app.models import MessageTemplate
from app import db

def test_create_template_api(client):
    """Test creating a new message template via the API."""
    response = client.post('/api/templates', json={
        'name': 'Welcome Message',
        'body': 'Hello [الاسم], welcome!'
    })
    assert response.status_code == 201
    assert response.json['name'] == 'Welcome Message'

    # Test creating a duplicate
    response = client.post('/api/templates', json={
        'name': 'Welcome Message',
        'body': 'Another body'
    })
    assert response.status_code == 409
    assert 'error' in response.json

    # Test creating with missing data
    response = client.post('/api/templates', json={'name': 'Incomplete'})
    assert response.status_code == 400

def test_get_templates_api(client, app):
    """Test fetching all message templates via the API."""
    # First, create some templates
    with app.app_context():
        t1 = MessageTemplate(name='Template A', body='Body A')
        t2 = MessageTemplate(name='Template B', body='Body B')
        db.session.add_all([t1, t2])
        db.session.commit()

    response = client.get('/api/templates')
    assert response.status_code == 200
    assert len(response.json) == 2
    assert response.json[0]['name'] == 'Template A'
    assert response.json[1]['body'] == 'Body B'
