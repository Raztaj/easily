from app.models import Contact, Tag, Campaign
from app import db

def test_index_redirect(client):
    """Test that the index page redirects to the dashboard."""
    response = client.get('/')
    assert response.status_code == 302
    assert response.headers['Location'] == '/dashboard'

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

def test_add_and_view_contact_with_tag(client, app):
    """Test adding a contact, then adding a tag to it."""
    # 1. Add a contact
    client.post('/contacts/new', data={'name': 'Tagged User', 'phone': '555444333'})

    # 2. Find the contact in the database to get its ID
    with app.app_context():
        contact = Contact.query.filter_by(phone='555444333').first()
        assert contact is not None
        contact_id = contact.id

    # 3. Go to the edit page and add a tag
    client.post(f'/contacts/{contact_id}/edit', data={
        'name': contact.name,
        'phone': contact.phone,
        'source': contact.source or '',
        'tags': 'VIP, test-tag'
    })

    # 4. Check if the tags are displayed on the main contacts page
    response = client.get('/contacts')
    assert response.status_code == 200
    assert b'Tagged User' in response.data
    assert b'<span class="tag">VIP</span>' in response.data
    assert b'<span class="tag">test-tag</span>' in response.data

def test_campaign_creation_and_api(client, app):
    """Test the contact count API and saving a campaign draft."""
    # 1. Setup: Create a contact and a tag
    with app.app_context():
        tag1 = Tag(name='customer')
        contact1 = Contact(name='Test Customer', phone='123123123', tags=[tag1])
        db.session.add(contact1)
        db.session.commit()

    # 2. Test the API endpoint
    response = client.post('/api/contacts/count', json={'tags': ['customer']})
    assert response.status_code == 200
    assert response.json['count'] == 1

    response = client.post('/api/contacts/count', json={'tags': ['non-existent-tag']})
    assert response.status_code == 200
    assert response.json['count'] == 0

    # 3. Test saving a campaign draft
    client.post('/campaigns/new', data={
        'campaign_name': 'Test Campaign',
        'message': 'This is a test message.',
        'tags': 'customer, new-tag',
        'action': 'save_draft'
    })

    # 4. Verify the campaign was created in the database
    with app.app_context():
        campaign = Campaign.query.filter_by(name='Test Campaign').first()
        assert campaign is not None
        assert campaign.message == 'This is a test message.'
        assert len(campaign.tags) == 2
        tag_names = {tag.name for tag in campaign.tags}
        assert 'customer' in tag_names
        assert 'new-tag' in tag_names

def test_campaign_export(client, app):
    """Test the campaign export functionality."""
    # 1. Setup: Create contacts with different tags
    with app.app_context():
        tag_a = Tag(name='group-a')
        tag_b = Tag(name='group-b')
        c1 = Contact(name='User A', phone='111', tags=[tag_a])
        c2 = Contact(name='User B', phone='222', tags=[tag_b])
        c3 = Contact(name='User AB', phone='333', tags=[tag_a, tag_b])
        db.session.add_all([c1, c2, c3])
        db.session.commit()

    # 2. Export a campaign targeting 'group-a'
    response = client.post('/campaigns/new', data={
        'campaign_name': 'Export Test 1',
        'message': 'Hello [الاسم]',
        'tags': 'group-a',
        'action': 'export'
    })

    assert response.status_code == 200
    assert response.mimetype == 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'

    # 3. Verify the content of the Excel file
    from openpyxl import load_workbook
    from io import BytesIO

    workbook = load_workbook(BytesIO(response.data))
    sheet = workbook.active
    rows = list(sheet.values)
    assert rows[0] == ('PhoneNumber', 'Message')
    assert rows[1] == ('111', 'Hello User A')
    assert rows[2] == ('333', 'Hello User AB')
    assert len(rows) == 3 # Header + 2 contacts

    # 4. Verify that recipients were logged
    with app.app_context():
        campaign = Campaign.query.filter_by(name='Export Test 1').first()
        assert len(campaign.recipients) == 2

    # 5. Test Anti-Annoyance Shield
    response = client.post('/campaigns/new', data={
        'campaign_name': 'Export Test 1', # Same name
        'message': 'Hello again [الاسم]',
        'tags': 'group-a',
        'action': 'export',
        'anti_spam_shield_active': 'on'
    }, follow_redirects=True)

    # The app should redirect back to the page with a flash message
    assert response.status_code == 200
    # Check for the Arabic warning message "لا يوجد مستلمين جدد لهذه الحملة."
    assert b'\xd9\x84\xd8\xa7 \xd9\x8a\xd9\x88\xd8\xac\xd8\xaf \xd9\x85\xd8\xb3\xd8\xaa\xd9\x84\xd9\x85\xd9\x8a\xd9\x86 \xd8\xac\xd8\xaf\xd8\xaf' in response.data

    # And verify the database state again to be sure
    with app.app_context():
        campaign = Campaign.query.filter_by(name='Export Test 1').first()
        # The number of recipients should NOT have changed.
        assert len(campaign.recipients) == 2

def test_edit_contact_details(client, app):
    """Test editing a contact's name, phone, and source."""
    # 1. Setup: Create a contact to edit and another to test uniqueness
    with app.app_context():
        c1 = Contact(name='Initial Name', phone='12345')
        c2 = Contact(name='Other User', phone='54321')
        db.session.add_all([c1, c2])
        db.session.commit()
        contact_id = c1.id

    # 2. Test successful edit
    response = client.post(f'/contacts/{contact_id}/edit', data={
        'name': 'Updated Name',
        'phone': '12345-new',
        'source': 'Updated Source'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Updated Name' in response.data # Check if new name is on the redirected page

    with app.app_context():
        updated_contact = db.session.get(Contact, contact_id)
        assert updated_contact.name == 'Updated Name'
        assert updated_contact.source == 'Updated Source'
        assert updated_contact.phone == '12345-new'

    # 3. Test phone number conflict
    response = client.post(f'/contacts/{contact_id}/edit', data={
        'name': 'Another Update',
        'phone': '54321', # Phone number of c2
        'source': 'Another Source'
    }, follow_redirects=True)
    assert response.status_code == 200
    # Check for the Arabic error message "رقم الهاتف ... مسجل بالفعل"
    assert b'\xd9\x85\xd8\xb3\xd8\xac\xd9\x84 \xd8\xa8\xd8\xa7\xd9\x84\xd9\x81\xd8\xb9\xd9\x84' in response.data

def test_dashboard_stats(client, app):
    """Test that the dashboard displays correct stats."""
    from datetime import datetime, timedelta

    with app.app_context():
        # Create 2 contacts now
        db.session.add(Contact(name='New User 1', phone='999'))
        db.session.add(Contact(name='New User 2', phone='888'))

        # Create 1 contact last month
        last_month = datetime.utcnow() - timedelta(days=40)
        db.session.add(Contact(name='Old User', phone='777', created_at=last_month))

        # Create 1 sent campaign
        sent_campaign = Campaign(name='Sent Campaign', message='Test')
        sent_campaign.recipients.append(db.session.get(Contact, 1))
        db.session.add(sent_campaign)

        # Create 1 draft campaign (no recipients)
        db.session.add(Campaign(name='Draft Campaign', message='Draft'))

        db.session.commit()

    response = client.get('/dashboard', follow_redirects=True)
    assert response.status_code == 200

    # Check for total contacts: 3
    assert b'<p class="stat-number">3</p>' in response.data
    # Check for new contacts this month: 2
    assert b'<p class="stat-number">2</p>' in response.data
    # Check for sent campaigns: 1
    assert b'<p class="stat-number">1</p>' in response.data

    # Check for recent campaigns table
    assert b'Sent Campaign' in response.data
    assert b'Draft Campaign' not in response.data
