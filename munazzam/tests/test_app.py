from app.models import Contact

def test_index_redirect(client):
    """Test that the index page redirects to the contacts list."""
    response = client.get('/')
    assert response.status_code == 302
    assert response.headers['Location'] == '/contacts'

def test_view_contacts_empty(client):
    """Test that the contacts page shows a message when no contacts exist."""
    response = client.get('/contacts')
    assert response.status_code == 200
    # The message is in Arabic
    assert b'text-center' in response.data
    assert b'\xd9\x84\xd8\xa7 \xd8\xaa\xd9\x88\xd8\xac\xd8\xaf \xd8\xac\xd9\x87\xd8\xa7\xd8\xaa \xd8\xa7\xd8\xaa\xd8\xb5\xd8\xa7\xd9\x84' in response.data # "لا توجد جهات اتصال"

def test_add_contact(client, app):
    """Test adding a new contact."""
    response = client.post('/contacts/new', data={
        'name': 'Test User',
        'phone': '1234567890',
        'source': 'Testing'
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b'Test User' not in response.data # Should be on the contacts page now, not add page
    assert b'\xd8\xaa\xd9\x85\xd8\xaa \xd8\xa5\xd8\xb6\xd8\xa7\xd9\x81\xd8\xa9 \xd8\xac\xd9\x87\xd8\xa9 \xd8\xa7\xd9\x84\xd8\xa7\xd8\xaa\xd8\xb5\xd8\xa7\xd9\x84 \xd8\xa8\xd9\x86\xd8\xac\xd8\xa7\xd8\xad!' in response.data # "تمت إضافة جهة الاتصال بنجاح!"

    with app.app_context():
        contact = Contact.query.filter_by(phone='1234567890').first()
        assert contact is not None
        assert contact.name == 'Test User'

def test_add_duplicate_contact(client, app):
    """Test that adding a duplicate contact fails."""
    # First, add a contact
    client.post('/contacts/new', data={'name': 'First User', 'phone': '111222333'})

    # Then, try to add another with the same phone
    response = client.post('/contacts/new', data={'name': 'Second User', 'phone': '111222333'}, follow_redirects=True)

    assert response.status_code == 200
    assert b'111222333 \xd9\x85\xd8\xb3\xd8\xac\xd9\x84 \xd8\xa8\xd8\xa7\xd9\x84\xd9\x81\xd8\xb9\xd9\x84.' in response.data # "{phone} مسجل بالفعل."

def test_view_added_contact(client):
    """Test that a newly added contact appears on the contacts list page."""
    client.post('/contacts/new', data={'name': 'View Me', 'phone': '987654321'})

    response = client.get('/contacts')
    assert response.status_code == 200
    assert b'View Me' in response.data
    assert b'987654321' in response.data

def test_add_and_view_arabic_contact(client):
    """Test adding and viewing a contact with Arabic characters."""
    arabic_name = 'تاج السر خالد'
    phone = '0912345678'

    # Add the contact
    client.post('/contacts/new', data={'name': arabic_name, 'phone': phone})

    # Check if it appears on the list page
    response = client.get('/contacts')
    assert response.status_code == 200
    # Search for the UTF-8 encoded version of the name in the response
    assert arabic_name.encode('utf-8') in response.data
