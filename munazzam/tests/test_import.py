import pytest
from app.models import Contact, Tag
from app import db
from openpyxl import Workbook
from io import BytesIO

@pytest.fixture
def sample_excel_file():
    """Creates a sample Excel file in memory for testing uploads."""
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Contacts"
    # Add headers
    sheet.append(['Full Name', 'Phone Number', 'Source'])
    # Add data rows
    sheet.append(['Alice', '111222333', 'Event 1'])
    sheet.append(['Bob', '444555666', 'Website'])
    sheet.append(['Alice', '777888999', 'Event 2']) # Same name, different number
    sheet.append(['Charlie', '111222333', 'Event 3']) # Duplicate phone number

    target = BytesIO()
    workbook.save(target)
    target.seek(0)
    return target

def test_import_page_loads(client):
    """Test that the import page loads correctly."""
    response = client.get('/contacts/import')
    assert response.status_code == 200
    assert b'\xd8\xa7\xd8\xb3\xd8\xaa\xd9\x8a\xd8\xb1\xd8\xa7\xd8\xaf' in response.data # "استيراد" (Import)

def test_import_contacts_success(client, app, sample_excel_file):
    """Test successful import of contacts from an Excel file."""
    response = client.post('/contacts/import', data={
        'file': (sample_excel_file, 'contacts.xlsx'),
        'tags': 'importer, new-leads'
    }, content_type='multipart/form-data', follow_redirects=True)

    assert response.status_code == 200
    # Check for the success flash message
    assert b'\xd8\xaa\xd9\x85 \xd8\xa7\xd8\xb3\xd8\xaa\xd9\x8a\xd8\xb1\xd8\xa7\xd8\xaf' in response.data # "تم استيراد"
    assert b'3' in response.data # Imported 3 contacts
    assert b'1' in response.data # Skipped 1 contact

    with app.app_context():
        assert Contact.query.count() == 3
        # Check Alice
        alice = Contact.query.filter_by(name='Alice').first()
        assert alice is not None
        assert alice.phone == '111222333'

        # Check tags
        assert len(alice.tags) == 2
        tag_names = {tag.name for tag in alice.tags}
        assert 'importer' in tag_names
        assert 'new-leads' in tag_names

        # Check that the duplicate phone number was skipped
        charlie = Contact.query.filter_by(name='Charlie').first()
        assert charlie is None

def test_import_skips_existing_in_db(client, app, sample_excel_file):
    """Test that the import skips contacts already present in the database."""
    # Pre-populate the database with one of the contacts from the file
    with app.app_context():
        c = Contact(name='Pre-existing Bob', phone='444555666')
        db.session.add(c)
        db.session.commit()

    response = client.post('/contacts/import', data={
        'file': (sample_excel_file, 'contacts.xlsx'),
        'tags': ''
    }, content_type='multipart/form-data', follow_redirects=True)

    assert response.status_code == 200
    # Should import 2 new contacts and skip 2 (1 duplicate in file, 1 in db)
    assert b'2' in response.data # Imported 2
    assert b'2' in response.data # Skipped 2

    with app.app_context():
        assert Contact.query.count() == 3 # 1 pre-existing + 2 new
        bob = Contact.query.filter_by(phone='444555666').first()
        assert bob.name == 'Pre-existing Bob' # Should not have been updated
