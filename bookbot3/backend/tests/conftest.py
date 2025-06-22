import pytest
from app import create_app
from backend.models import db
import backend.jobs
from backend.jobs import get_job_processor

class TestConfig:
    """Test configuration."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    SECRET_KEY = 'test-secret-key'

@pytest.fixture
def app():
    """Create test Flask application."""
    app_instance = create_app(TestConfig)
    
    with app_instance.app_context():
        db.create_all()
        yield app_instance
        db.session.remove()
        db.drop_all()

@pytest.fixture
def job_processor(app):
    """Get a job processor instance configured with the test app's db session."""
    # Reset the singleton so a new instance is created for this test.
    backend.jobs._job_processor = None
    with app.app_context():
        # Create a new processor, injecting the test's db session.
        processor = get_job_processor(db_session=db.session)
    return processor
