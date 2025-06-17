"""
Basic tests for BookBot backend.

This module contains unit tests for the core functionality.
More comprehensive tests will be added in a subsequent step.
"""

import pytest
import json
from flask import Flask
from backend.models import db, User, Book, Chunk, Job
from app import create_app


class TestConfig:
    """Test configuration."""
    TESTING = True
    DATABASE_URL = 'sqlite:///:memory:'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    SECRET_KEY = 'test-secret-key'


@pytest.fixture
def app():
    """Create test Flask application."""
    app = create_app(TestConfig)
    
    with app.app_context():
        db.create_all()
        
        # Create test user (use default-user-123 to match auth system)
        # Check if user already exists first
        existing_user = User.query.filter_by(user_id="default-user-123").first()
        if not existing_user:
            test_user = User(
                user_id="default-user-123",
                props={'name': 'Test User', 'email': 'test@example.com'}
            )
            db.session.add(test_user)
            db.session.commit()
            print("Created default user")
        
        yield app
        
        db.drop_all()


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


@pytest.fixture
def test_book(app):
    """Create a test book and return its ID."""
    with app.app_context():
        book = Book(
            user_id="default-user-123",
            props={'title': 'Test Book', 'genre': 'Fiction'}
        )
        db.session.add(book)
        db.session.commit()
        # Return the book_id to avoid DetachedInstanceError
        return book.book_id


class TestAPI:
    """Test API endpoints."""
    
    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get('/api/health')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['status'] == 'healthy'
        assert 'version' in data
    
    def test_config_endpoint(self, client):
        """Test configuration endpoint."""
        response = client.get('/api/config')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'api_url' in data
        assert 'app_name' in data
        assert data['app_name'] == 'BookBot'
    
    def test_list_books(self, client, test_book):
        """Test listing books."""
        response = client.get('/api/books')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'books' in data
        assert len(data['books']) >= 1
        assert data['books'][0]['book_id'] == test_book
    
    def test_create_book(self, client):
        """Test creating a book."""
        book_data = {
            'props': {
                'title': 'New Test Book',
                'genre': 'Science Fiction'
            }
        }
        
        response = client.post('/api/books', 
                             data=json.dumps(book_data),
                             content_type='application/json')
        assert response.status_code == 201
        
        data = json.loads(response.data)
        assert data['props']['title'] == 'New Test Book'
        assert 'book_id' in data
    
    def test_get_book(self, client, test_book):
        """Test getting a specific book."""
        response = client.get(f'/api/books/{test_book}')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['book_id'] == test_book
        assert data['props']['title'] == 'Test Book'
    
    def test_create_chunk(self, client, test_book):
        """Test creating a chunk."""
        chunk_data = {
            'props': {'tags': ['test']},
            'text': '# Test Chapter\n\nThis is a test chapter.',
            'type': 'chapter',
            'chapter': 1,
            'order': 1.0
        }
        
        response = client.post(f'/api/books/{test_book}/chunks',
                             data=json.dumps(chunk_data),
                             content_type='application/json')
        assert response.status_code == 201
        
        data = json.loads(response.data)
        assert data['text'] == chunk_data['text']
        assert data['word_count'] > 0
        assert data['version'] == 1
        assert data['is_latest'] is True
    
    def test_create_job(self, client, test_book):
        """Test creating a job."""
        job_data = {
            'job_type': 'demo',
            'props': {
                'target_word_count': 100
            }
        }
        
        response = client.post(f'/api/books/{test_book}/jobs',
                             data=json.dumps(job_data),
                             content_type='application/json')
        assert response.status_code == 201
        
        data = json.loads(response.data)
        assert data['job_type'] == 'demo'
        assert data['state'] == 'waiting'
        assert 'job_id' in data


class TestModels:
    """Test database models."""
    
    def test_user_creation(self, app):
        """Test user model creation."""
        with app.app_context():
            user = User(props={'name': 'Test User'})
            db.session.add(user)
            db.session.commit()
            
            assert user.user_id is not None
            assert user.props['name'] == 'Test User'
            assert user.created_at is not None
    
    def test_book_creation(self, app):
        """Test book model creation."""
        with app.app_context():
            book = Book(
                user_id="test-user",
                props={'title': 'Test Book'}
            )
            db.session.add(book)
            db.session.commit()
            
            assert book.book_id is not None
            assert book.user_id == "test-user"
            assert book.is_locked is False
    
    def test_chunk_versioning(self, app, test_book):
        """Test chunk versioning system."""
        with app.app_context():
            # Create first version
            chunk1 = Chunk(
                book_id=test_book,
                text="First version",
                version=1,
                is_latest=True
            )
            db.session.add(chunk1)
            db.session.commit()
            
            chunk_id = chunk1.chunk_id
            
            # Create second version
            chunk2 = Chunk(
                book_id=test_book,
                chunk_id=chunk_id,
                text="Second version",
                version=2,
                is_latest=True
            )
            
            # Mark first version as not latest
            chunk1.is_latest = False
            
            db.session.add(chunk2)
            db.session.commit()
            
            # Verify versioning
            latest = Chunk.query.filter_by(chunk_id=chunk_id, is_latest=True).first()
            assert latest.version == 2
            assert latest.text == "Second version"
            
            all_versions = Chunk.query.filter_by(chunk_id=chunk_id).all()
            assert len(all_versions) == 2
    
    def test_word_count(self, app):
        """Test word count calculation."""
        text = "This is a test sentence with eight words."
        count = Chunk.count_words(text)
        assert count == 8
        
        empty_count = Chunk.count_words("")
        assert empty_count == 0
        
        none_count = Chunk.count_words(None)
        assert none_count == 0


class TestLLM:
    """Test LLM functionality."""
    
    def test_fake_llm_call(self):
        """Test fake LLM implementation."""
        from backend.llm.fake_llm import FakeLLMCall
        
        llm_call = FakeLLMCall(
            model="test-model",
            api_key="test-key",
            target_word_count=50
        )
        
        success = llm_call.execute()
        assert success is True
        assert llm_call.output_text is not None
        assert len(llm_call.output_text.split()) > 0
        assert llm_call.cost > 0
        assert llm_call.execution_time > 0
    
    def test_llm_call_interface(self):
        """Test main LLM call interface."""
        from backend.llm import LLMCall
        
        llm_call = LLMCall(
            model="test-model",
            api_key="test-key",
            target_word_count=25
        )
        
        success = llm_call.execute()
        assert success is True
        assert llm_call.output_text is not None
        
        result_dict = llm_call.to_dict()
        assert 'model' in result_dict
        assert 'output_text' in result_dict
        assert 'cost' in result_dict
    
    def test_api_token_status(self):
        """Test API token status checking."""
        from backend.llm import get_api_token_status
        
        # Test valid key (use test-key which bypasses OpenRouter validation)
        status = get_api_token_status("test-key")
        assert status['valid'] is True
        assert 'balance' in status
        
        # Test invalid key
        status = get_api_token_status("invalid")
        assert status['valid'] is False
        assert 'error' in status


class TestJobs:
    """Test job system."""
    
    def test_job_creation(self, app, test_book):
        """Test job creation."""
        from backend.jobs import create_job
        
        with app.app_context():
            job = create_job(
                book_id=test_book,
                job_type="demo",
                props={"test": True}
            )
            
            assert job.job_id is not None
            assert job.state == 'waiting'
            assert job.job_type == 'demo'
            assert job.props['test'] is True
    
    def test_demo_job(self, app, test_book):
        """Test demo job execution."""
        from backend.jobs import DemoJob, Job
        
        with app.app_context():
            # Create job record
            job_record = Job(
                book_id=test_book,
                job_type="demo",
                props={"target_word_count": 25},
                state="running"
            )
            db.session.add(job_record)
            db.session.commit()
            
            # Create and execute demo job
            demo_job = DemoJob(job_record)
            
            # Mock the time.sleep to speed up tests
            import time
            original_sleep = time.sleep
            time.sleep = lambda x: None
            
            try:
                success = demo_job.execute()
                assert success is True
                
                # Check that logs were created
                from backend.models import JobLog
                logs = JobLog.query.filter_by(job_id=job_record.job_id).all()
                assert len(logs) > 0
                
            finally:
                time.sleep = original_sleep


class TestCreateFoundationJob:
    """Test Create Foundation job functionality."""
    
    def test_create_foundation_job_creation(self, app):
        """Test creating a CreateFoundation job."""
        from backend.jobs import CreateFoundationJob, Job
        
        with app.app_context():
            # Create test book within this context
            book = Book(
                user_id="test-user-123",
                props={'title': 'Test Book', 'genre': 'Fiction'}
            )
            db.session.add(book)
            db.session.commit()
            
            # Create job record
            job_record = Job(
                book_id=book.book_id,
                job_type="create_foundation",
                props={
                    "brief": "A young wizard discovers a hidden magical academy.",
                    "style": "Fantasy adventure for young adults, similar to Harry Potter."
                },
                state="running"
            )
            db.session.add(job_record)
            db.session.commit()
            
            # Create CreateFoundation job
            foundation_job = CreateFoundationJob(job_record)
            assert foundation_job.job.job_type == "create_foundation"
            assert foundation_job.job.props["brief"] is not None
            assert foundation_job.job.props["style"] is not None
    
    def test_create_foundation_job_execution(self, app):
        """Test executing a CreateFoundation job."""
        from backend.jobs import CreateFoundationJob, Job
        from backend.models import JobLog
        
        with app.app_context():
            # Create test book
            book = Book(
                user_id="test-user-123",
                props={'title': 'Test Book', 'genre': 'Fiction'}
            )
            db.session.add(book)
            db.session.commit()
            
            # Create job record
            job_record = Job(
                book_id=book.book_id,
                job_type="create_foundation",
                props={
                    "brief": "A detective in a cyberpunk city investigates AI crimes.",
                    "style": "Dark sci-fi thriller with noir elements."
                },
                state="running"
            )
            db.session.add(job_record)
            db.session.commit()
            
            # Create and execute foundation job
            foundation_job = CreateFoundationJob(job_record)
            success = foundation_job.execute()
            
            assert success is True
            
            # Check that logs were created
            logs = JobLog.query.filter_by(job_id=job_record.job_id).all()
            assert len(logs) > 0
            
            # Check for expected log entries
            log_messages = [log.log_entry for log in logs]
            assert any("Starting Create Foundation job" in msg for msg in log_messages)
            assert any("completed successfully" in msg for msg in log_messages)
    
    def test_create_foundation_missing_props(self, app):
        """Test CreateFoundation job with missing required props."""
        from backend.jobs import CreateFoundationJob, Job
        from backend.models import JobLog
        
        with app.app_context():
            # Create test book
            book = Book(
                user_id="test-user-123",
                props={'title': 'Test Book', 'genre': 'Fiction'}
            )
            db.session.add(book)
            db.session.commit()
            
            # Create job record with missing 'style' prop
            job_record = Job(
                book_id=book.book_id,
                job_type="create_foundation",
                props={
                    "brief": "A story about time travel."
                    # Missing 'style' prop
                },
                state="running"
            )
            db.session.add(job_record)
            db.session.commit()
            
            # Execute should fail
            foundation_job = CreateFoundationJob(job_record)
            success = foundation_job.execute()
            
            assert success is False
            
            # Check error log
            logs = JobLog.query.filter_by(job_id=job_record.job_id).all()
            log_messages = [log.log_entry for log in logs]
            assert any("Missing required 'brief' and/or 'style'" in msg for msg in log_messages)
    
    def test_create_foundation_chunks_created(self, app):
        """Test that CreateFoundation job creates the expected chunks."""
        from backend.jobs import CreateFoundationJob, Job
        
        with app.app_context():
            # Create test book
            book = Book(
                user_id="test-user-123",
                props={'title': 'Test Book', 'genre': 'Fiction'}
            )
            db.session.add(book)
            db.session.commit()
            
            # Create job record
            job_record = Job(
                book_id=book.book_id,
                job_type="create_foundation",
                props={
                    "brief": "Space colonists discover an ancient alien artifact.",
                    "style": "Hard science fiction with exploration themes."
                },
                state="running"
            )
            db.session.add(job_record)
            db.session.commit()
            
            # Execute foundation job
            foundation_job = CreateFoundationJob(job_record)
            success = foundation_job.execute()
            
            assert success is True
            
            # Check that chunks were created
            chunks = Chunk.query.filter_by(book_id=book.book_id).all()
            
            # Should have at least: brief, style, outline, characters, settings, and some scenes
            chunk_types = [chunk.type for chunk in chunks]
            
            assert "brief" in chunk_types
            assert "style" in chunk_types
            assert "outline" in chunk_types
            assert "characters" in chunk_types
            assert "settings" in chunk_types
            assert "scene" in chunk_types  # Should have at least one scene
            
            # Check specific chunks
            brief_chunk = next((c for c in chunks if c.type == "brief"), None)
            assert brief_chunk is not None
            assert "Space colonists" in brief_chunk.text
            
            style_chunk = next((c for c in chunks if c.type == "style"), None)
            assert style_chunk is not None
            assert "Hard science fiction" in style_chunk.text
            
            outline_chunk = next((c for c in chunks if c.type == "outline"), None)
            assert outline_chunk is not None
            assert outline_chunk.props.get('scene_count', 0) > 0
            
            # Check scene chunks have proper props
            scene_chunks = [c for c in chunks if c.type == "scene"]
            assert len(scene_chunks) > 0
            
            for scene_chunk in scene_chunks:
                assert 'scene_id' in scene_chunk.props
                assert 'scene_title' in scene_chunk.props
                assert scene_chunk.props['scene_id'] is not None
    
    def test_create_foundation_run_function(self, app):
        """Test the run_create_foundation_job function directly."""
        from backend.jobs.create_foundation import run_create_foundation_job
        
        with app.app_context():
            # Create test book
            book = Book(
                user_id="test-user-123",
                props={'title': 'Test Book', 'genre': 'Fiction'}
            )
            db.session.add(book)
            db.session.commit()
            
            log_messages = []
            def test_log_callback(message):
                log_messages.append(message)
            
            # Test successful execution
            success = run_create_foundation_job(
                job_id="test-job-123",
                book_id=book.book_id,
                props={
                    "brief": "A magical library that exists between worlds.",
                    "style": "Contemporary fantasy with literary elements."
                },
                log_callback=test_log_callback
            )
            
            assert success is True
            assert len(log_messages) > 0
            assert any("Starting Create Foundation job" in msg for msg in log_messages)
            assert any("completed successfully" in msg for msg in log_messages)
            
            # Test with missing props
            log_messages.clear()
            success = run_create_foundation_job(
                job_id="test-job-456",
                book_id=book.book_id,
                props={"brief": "Only has brief"},  # Missing style
                log_callback=test_log_callback
            )
            
            assert success is False
            assert any("Missing required" in msg for msg in log_messages)
    
    def test_create_foundation_invalid_book(self, app):
        """Test CreateFoundation job with invalid book ID."""
        from backend.jobs.create_foundation import run_create_foundation_job
        
        with app.app_context():
            log_messages = []
            def test_log_callback(message):
                log_messages.append(message)
            
            success = run_create_foundation_job(
                job_id="test-job-789",
                book_id="non-existent-book-id",
                props={
                    "brief": "Test brief",
                    "style": "Test style"
                },
                log_callback=test_log_callback
            )
            
            assert success is False
            assert any("Book non-existent-book-id not found" in msg for msg in log_messages)


class TestBotManagerIntegration:
    """Test bot manager integration with CreateFoundation job."""
    
    def test_scene_extraction(self, app):
        """Test scene extraction from outline."""
        from backend.bot_manager import get_bot_manager
        
        # Sample outline with scene markers (correct format)
        outline_text = """
## Chapter 1: The Discovery

### Scene: Hero finds the artifact [[Scene 1]]
### Scene: First contact with aliens [[Scene 2]]

## Chapter 2: The Journey

### Scene: Departure from Earth [[Scene 3]]
### Scene: Space battle [[Scene 4]]
        """
        
        bot_manager = get_bot_manager()
        scenes = bot_manager.extract_scenes_from_outline(outline_text)
        
        assert len(scenes) == 4
        assert scenes[0]['scene_id'] == 'Scene 1'
        assert 'Hero finds the artifact' in scenes[0]['title']
        assert scenes[0]['chapter'] == 1
        
        assert scenes[2]['scene_id'] == 'Scene 3'
        assert 'Departure from Earth' in scenes[2]['title']
        assert scenes[2]['chapter'] == 2
    
    def test_scene_id_addition(self, app):
        """Test adding scene IDs to outline."""
        from backend.bot_manager import get_bot_manager
        
        outline_text = """
## Chapter 1: Beginning

### Scene: First major event happens
### Scene: Character development

## Chapter 2: Middle

### Scene: Conflict escalates
### Scene: Plot twist revealed
        """
        
        bot_manager = get_bot_manager()
        outline_with_ids, scene_ids = bot_manager.add_scene_ids(outline_text)
        
        assert len(scene_ids) > 0
        assert "[[Scene" in outline_with_ids
        
        # Should extract the scenes we just added
        extracted_scenes = bot_manager.extract_scenes_from_outline(outline_with_ids)
        assert len(extracted_scenes) == len(scene_ids)


class TestFoundationJobHelpers:
    """Test helper functions in the create_foundation module."""
    
    def test_chunk_creation_helper(self, app):
        """Test the _create_chunk helper function."""
        from backend.jobs.create_foundation import _create_chunk
        
        with app.app_context():
            # Create test book
            book = Book(
                user_id="test-user-123",
                props={'title': 'Test Book', 'genre': 'Fiction'}
            )
            db.session.add(book)
            db.session.commit()
            
            log_messages = []
            def test_log_callback(message):
                log_messages.append(message)
            
            chunk = _create_chunk(
                book_id=book.book_id,
                chunk_type="test_type",
                text="Test content for the chunk",
                chapter=1,
                order=1.5,
                props={"test_prop": "test_value"},
                log_callback=test_log_callback
            )
            
            assert chunk is not None
            assert chunk.type == "test_type"
            assert chunk.text == "Test content for the chunk"
            assert chunk.chapter == 1
            assert chunk.order == 1.5
            assert chunk.props["test_prop"] == "test_value"
            assert chunk.word_count > 0
            
            # Check log message
            assert any("Created test_type chunk" in msg for msg in log_messages)
    
    def test_llm_generation_helpers(self, app):
        """Test LLM generation helper functions."""
        from backend.jobs.create_foundation import (
            _generate_outline, _generate_characters, _generate_settings, _add_tags_to_content
        )
        
        with app.app_context():
            log_messages = []
            def test_log_callback(message):
                log_messages.append(message)
            
            book_props = {"title": "Test Book", "genre": "Fantasy"}
            user_props = {"name": "Test User"}
            brief = "A magical adventure"
            style = "Fantasy style"
            
            # Test outline generation
            outline = _generate_outline(book_props, user_props, brief, style, test_log_callback)
            assert outline is not None
            assert len(outline) > 0
            assert any("Outline generated" in msg for msg in log_messages)
            
            # Test characters generation
            log_messages.clear()
            characters = _generate_characters(book_props, user_props, brief, style, outline, test_log_callback)
            assert characters is not None
            assert len(characters) > 0
            assert any("Characters generated" in msg for msg in log_messages)
            
            # Test settings generation
            log_messages.clear()
            settings = _generate_settings(book_props, user_props, brief, style, outline, test_log_callback)
            assert settings is not None
            assert len(settings) > 0
            assert any("Settings generated" in msg for msg in log_messages)
            
            # Test content tagging
            log_messages.clear()
            tagged_content = _add_tags_to_content(outline, "outline", book_props, user_props, test_log_callback)
            assert tagged_content is not None
            assert len(tagged_content) > 0
            assert any("Tags added to outline" in msg for msg in log_messages)
