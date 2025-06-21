"""
Tests for the LLM picker API.

This module contains tests for the LLM picker API endpoints, including:
- Listing all LLMs
- Getting LLMs filtered by group
- Managing book LLM defaults
- Managing book LLM override
"""
import pytest
import json
from unittest.mock import patch

from app import create_app
from backend.models import db, Book
from backend.llmpicker.models import LLMInfo


# Sample test data matching the structure in test_llmpicker.py
SAMPLE_LLMS = [
    {
        "id": "test-llm-1", 
        "name": "Writer Test LLM", 
        "description": "A test LLM for writers", 
        "company": "Test Company", 
        "input_cost_per_mtok": 0.001, 
        "output_cost_per_mtok": 0.002, 
        "seconds_per_output_mtok": 0.5, 
        "router": "openrouter", 
        "context_length": 8000, 
        "groups": ["writer", "all"], 
        "quality_score": 8
    },
    {
        "id": "test-llm-2", 
        "name": "Editor Test LLM", 
        "description": "A test LLM for editors", 
        "company": "Test Company", 
        "input_cost_per_mtok": 0.001, 
        "output_cost_per_mtok": 0.002, 
        "seconds_per_output_mtok": 0.5, 
        "router": "openrouter", 
        "context_length": 16000, 
        "groups": ["editor"], 
        "quality_score": 7
    },
    {
        "id": "test-llm-3", 
        "name": "All Test LLM", 
        "description": "A test LLM for all uses", 
        "company": "Test Company", 
        "input_cost_per_mtok": 0.001, 
        "output_cost_per_mtok": 0.002, 
        "seconds_per_output_mtok": 0.5, 
        "router": "openrouter", 
        "context_length": 32000, 
        "groups": ["all", "override"], 
        "quality_score": 9
    },
]


@pytest.fixture
def client():
    """Create a test client for the Flask application."""
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    # Push an app context that will remain active for all tests using this fixture
    app_ctx = app.app_context()
    app_ctx.push()
    
    # Set up database
    db.create_all()
    
    with app.test_client() as test_client:
        yield test_client
    
    # Clean up after tests
    db.drop_all()
    app_ctx.pop()


@pytest.fixture(autouse=True)
def mock_catalog():
    """Mock the LLM catalog for all tests."""
    llm_objects = [LLMInfo(**item) for item in SAMPLE_LLMS]
    
    # Mock all catalog functions to ensure consistent behavior
    with patch('backend.llmpicker.catalog._load_llm_catalog') as mock_load, \
         patch('backend.llmpicker.catalog.get_all_llms') as mock_get_all, \
         patch('backend.llmpicker.catalog.get_llms_by_group') as mock_get_by_group, \
         patch('backend.llmpicker.catalog.get_llm_by_id') as mock_get_by_id:
        
        mock_load.return_value = llm_objects
        mock_get_all.return_value = llm_objects
        
        # Filter LLMs by group properly
        def filter_by_group(group):
            filtered = []
            for llm in llm_objects:
                if group in llm.groups or 'all' in llm.groups:
                    filtered.append(llm)
            return filtered
        mock_get_by_group.side_effect = filter_by_group
        
        # Get LLM by ID properly
        def get_by_id(llm_id):
            for llm in llm_objects:
                if llm.id == llm_id:
                    return llm
            return None
        mock_get_by_id.side_effect = get_by_id
        
        yield


@pytest.fixture
def test_book(client):
    """Create a test book in the database."""
    # Create a book for testing
    book = Book(book_id='test-book-123', user_id='default-user-123')
    db.session.add(book)
    db.session.commit()
    
    # Return the book_id to avoid detached instance issues
    yield book.book_id
    
    # Clean up
    db.session.delete(book)
    db.session.commit()


def test_list_llms(client, mock_catalog):
    """Test listing all LLMs."""
    response = client.get('/api/llms')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert 'llms' in data
    assert len(data['llms']) == len(SAMPLE_LLMS)


def test_filter_llms_by_group(client, mock_catalog):
    """Test filtering LLMs by group."""
    response = client.get('/api/llms?group=writer')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert 'llms' in data
    # llm-1 (writer, all), llm-3 (all, override)
    assert len(data['llms']) == 2
    assert data['llms'][0]['id'] == 'test-llm-1'


def test_get_book_defaults_empty(client, test_book):
    """Test getting book LLM defaults when none are set."""
    response = client.get(f'/api/llms/books/{test_book}/defaults')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert data == {}


def test_set_and_get_book_defaults(client, test_book, mock_catalog):
    """Test setting and getting book LLM defaults."""
    defaults_payload = {
        'writer': 'test-llm-1',
        'editor': 'test-llm-2'
    }
    response = client.put(
        f'/api/llms/books/{test_book}/defaults',
        json=defaults_payload
    )
    assert response.status_code == 200
    assert 'success' in response.json['status']
    
    # Get all defaults
    response = client.get(f'/api/llms/books/{test_book}/defaults')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert data['writer'] == 'test-llm-1'
    assert data['editor'] == 'test-llm-2'


def test_clear_book_defaults(client, test_book, mock_catalog):
    """Test clearing book LLM defaults."""
    # Set defaults first
    client.put(
        f'/api/llms/books/{test_book}/defaults',
        json={'writer': 'test-llm-1', 'editor': 'test-llm-2'}
    )
    
    # Clear the writer default by sending a new payload without it
    response = client.put(
        f'/api/llms/books/{test_book}/defaults',
        json={'editor': 'test-llm-2'}
    )
    assert response.status_code == 200
    assert 'success' in response.json['status']
    
    # Verify it's been cleared and the other remains
    response = client.get(f'/api/llms/books/{test_book}/defaults')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'writer' not in data
    assert data['editor'] == 'test-llm-2'


def test_set_and_get_override(client, test_book, mock_catalog):
    """Test setting and getting LLM override."""
    # Set override
    response = client.put(
        f'/api/llms/books/{test_book}/override',
        json={'llm_id': 'test-llm-3'}
    )
    assert response.status_code == 200
    assert 'success' in response.json['status']
    
    # Get override
    response = client.get(f'/api/llms/books/{test_book}/override')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['override'] == 'test-llm-3'
    assert data['llm']['id'] == 'test-llm-3'


def test_clear_override(client, test_book, mock_catalog):
    """Test clearing LLM override."""
    # Set override first
    client.put(
        f'/api/llms/books/{test_book}/override',
        json={'llm_id': 'test-llm-3'}
    )
    
    # Clear override
    response = client.delete(f'/api/llms/books/{test_book}/override')
    assert response.status_code == 200
    assert 'success' in response.json['status']
    
    # Verify it's cleared
    response = client.get(f'/api/llms/books/{test_book}/override')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['override'] is None


def test_invalid_llm_for_group(client, test_book, mock_catalog):
    """Test setting an invalid LLM for a group."""
    # Try to set editor LLM for writer group
    response = client.put(
        f'/api/llms/books/{test_book}/defaults',
        json={'writer': 'test-llm-2'}  # An editor LLM
    )
    assert response.status_code == 400
    assert 'error' in response.json


def test_nonexistent_book(client):
    """Test accessing endpoints for a nonexistent book."""
    response = client.get('/api/llms/books/nonexistent-book/defaults')
    assert response.status_code == 404
    
    response = client.put(
        '/api/llms/books/nonexistent-book/defaults',
        json={'writer': 'any-id'}
    )
    assert response.status_code == 404


def test_missing_request_data(client, test_book):
    """Test endpoints with missing request data."""
    response = client.put(
        f'/api/llms/books/{test_book}/override',
        json={}  # Missing llm_id
    )
    assert response.status_code == 400
