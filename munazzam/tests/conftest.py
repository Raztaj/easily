import os
import sys
import tempfile
import pytest

# Add project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db

@pytest.fixture
def app():
    """Create and configure a new app instance for each test."""
    # Create a temporary file to isolate the database for each test
    db_fd, db_path = tempfile.mkstemp()

    app = create_app({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': f'sqlite:///{db_path}',
    })

    with app.app_context():
        db.create_all()

    yield app

    # Close and remove the temporary database
    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """A test runner for the `flask` command."""
    return app.test_cli_runner()

@pytest.fixture(autouse=True)
def cleanup_session(app):
    """Ensure the session is closed after each test to prevent stale data."""
    yield
    with app.app_context():
        db.session.close()
