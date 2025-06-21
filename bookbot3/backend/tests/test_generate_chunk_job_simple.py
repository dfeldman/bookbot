"""
Unit tests for GenerateChunkJob functionality.
"""

import pytest
import json
from unittest.mock import patch, MagicMock

from backend.models import db, User, Book, Chunk, Job, JobLog
from backend.jobs.generate_chunk import GenerateChunkJob
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
        yield app
        db.drop_all()


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


class TestGenerateChunkJob:
    """Test cases for GenerateChunkJob."""
    
    def setup_test_data(self, app):
        """Set up test data in the database."""
        with app.app_context():
            # Create a test user
            user = User(
                props={
                    'username': 'testuser',
                    'email': 'test@example.com'
                }
            )
            db.session.add(user)
            db.session.commit()  # Commit user first to get user_id
            
            # Create a test book
            book = Book(
                user_id=user.user_id,
                props={
                    'title': 'Test Book'
                }
            )
            db.session.add(book)
            db.session.commit()  # Commit book to get book_id
            
            # Create a test scene chunk
            scene_chunk = Chunk(
                book_id=book.book_id,
                props={
                    'title': 'Test Scene'
                },
                type='scene',
                text='Original scene content',
                is_locked=False
            )
            db.session.add(scene_chunk)
            
            # Create a test bot chunk
            bot_props = {
                'llm_alias': 'test-llm',
                'temperature': 0.7,
                'description': 'Test bot'
            }
            bot_chunk = Chunk(
                book_id=book.book_id,
                props={
                    'title': 'Test Bot',
                    **bot_props
                },
                type='bot',
                text='',
                is_locked=False
            )
            db.session.add(bot_chunk)
            
            db.session.commit()
            
            return {
                'user': user,
                'book': book,
                'scene_chunk': scene_chunk,
                'bot_chunk': bot_chunk,
                'user_id': user.user_id,
                'book_id': book.book_id,
                'scene_chunk_id': scene_chunk.chunk_id,
                'bot_chunk_id': bot_chunk.chunk_id
            }
    
    def test_job_initialization(self, app):
        """Test job initialization with valid parameters."""
        test_data = self.setup_test_data(app)
        
        with app.app_context():
            # Create a job record
            job_props = {
                'chunk_id': test_data['scene_chunk_id'],
                'bot_id': test_data['bot_chunk_id'],
                'mode': 'write',
                'options': {
                    'preserve_formatting': True,
                    'track_changes': False
                }
            }
            
            job = Job(
                job_id='test-job-1',
                book_id=test_data['book_id'],
                job_type='GenerateChunk',
                state='pending',
                props=job_props
            )
            db.session.add(job)
            db.session.commit()
            
            # Create GenerateChunkJob instance
            generate_job = GenerateChunkJob(job)
            
            assert generate_job.job == job
            assert generate_job.book.book_id == test_data['book_id']
            assert generate_job.chunk_id == test_data['scene_chunk_id']
            assert generate_job.bot_id == test_data['bot_chunk_id']
            assert generate_job.mode == 'write'
    
    def test_validate_valid_parameters(self, app):
        """Test parameter validation with valid mode."""
        test_data = self.setup_test_data(app)
        
        with app.app_context():
            job_props = {
                'chunk_id': test_data['scene_chunk_id'],
                'bot_id': test_data['bot_chunk_id'],
                'mode': 'rewrite',
                'options': {
                    'preserve_formatting': True,
                    'track_changes': False
                }
            }
            
            job = Job(
                job_id='test-job-1',
                book_id=test_data['book_id'],
                job_type='GenerateChunk',
                state='pending',
                props=job_props
            )
            db.session.add(job)
            db.session.commit()
            
            generate_job = GenerateChunkJob(job)
            
            # Should validate successfully
            assert generate_job.validate() == True
    
    def test_validate_invalid_mode(self, app):
        """Test parameter validation with invalid mode."""
        test_data = self.setup_test_data(app)
        
        with app.app_context():
            job_props = {
                'chunk_id': test_data['scene_chunk_id'],
                'bot_id': test_data['bot_chunk_id'],
                'mode': 'invalid_mode',
                'options': {
                    'preserve_formatting': True,
                    'track_changes': False
                }
            }
            
            job = Job(
                job_id='test-job-1',
                book_id=test_data['book_id'],
                job_type='GenerateChunk',
                state='pending',
                props=job_props
            )
            db.session.add(job)
            db.session.commit()
            
            generate_job = GenerateChunkJob(job)
            
            # Should fail validation
            assert generate_job.validate() == False
    
    def test_validate_missing_chunk(self, app):
        """Test validation with nonexistent chunk."""
        test_data = self.setup_test_data(app)
        
        with app.app_context():
            job_props = {
                'chunk_id': 'nonexistent-uuid',  # Nonexistent chunk
                'bot_id': test_data['bot_chunk_id'],
                'mode': 'write',
                'options': {}
            }
            
            job = Job(
                job_id='test-job-1',
                book_id=test_data['book_id'],
                job_type='GenerateChunk',
                state='pending',
                props=job_props
            )
            db.session.add(job)
            db.session.commit()
            
            generate_job = GenerateChunkJob(job)
            
            # Validation should pass since chunk_id is present (existence check happens in execute)
            assert generate_job.validate() == True
    
    def test_validate_missing_bot(self, app):
        """Test validation with nonexistent bot."""
        test_data = self.setup_test_data(app)
        
        with app.app_context():
            job_props = {
                'chunk_id': test_data['scene_chunk_id'],
                'bot_id': 'nonexistent-bot-uuid',  # Nonexistent bot
                'mode': 'write',
                'options': {}
            }
            
            job = Job(
                job_id='test-job-1',
                book_id=test_data['book_id'],
                job_type='GenerateChunk',
                state='pending',
                props=job_props
            )
            db.session.add(job)
            db.session.commit()
            
            generate_job = GenerateChunkJob(job)
            
            # Validation should pass since bot_id is present (existence check happens in execute)
            assert generate_job.validate() == True
    
    def test_validate_wrong_bot_type(self, app):
        """Test validation with wrong bot type."""
        test_data = self.setup_test_data(app)
        
        with app.app_context():
            job_props = {
                'chunk_id': test_data['scene_chunk_id'],
                'bot_id': test_data['scene_chunk_id'],  # Using scene chunk as bot
                'mode': 'write',
                'options': {}
            }
            
            job = Job(
                job_id='test-job-1',
                book_id=test_data['book_id'],
                job_type='GenerateChunk',
                state='pending',
                props=job_props
            )
            db.session.add(job)
            db.session.commit()
            
            generate_job = GenerateChunkJob(job)
            
            # Validation should pass since bot_id is present (type check happens in execute)
            assert generate_job.validate() == True
    
    def test_chunk_locking(self, app):
        """Test chunk locking during job execution."""
        test_data = self.setup_test_data(app)
        
        with app.app_context():
            job_props = {
                'chunk_id': test_data['scene_chunk_id'],
                'bot_id': test_data['bot_chunk_id'],
                'mode': 'write',
                'options': {}
            }
            
            job = Job(
                job_id='test-job-1',
                book_id=test_data['book_id'],
                job_type='GenerateChunk',
                state='pending',
                props=job_props
            )
            db.session.add(job)
            db.session.commit()
            
            generate_job = GenerateChunkJob(job)
            
            # Initially chunk should not be locked
            chunk = Chunk.query.filter_by(chunk_id=test_data['scene_chunk_id']).first()
            assert chunk.is_locked == False
            
            # Execute the job (which handles locking internally)
            generate_job.execute()
            
            # After execution, chunk should be unlocked
            db.session.refresh(chunk)
            assert chunk.is_locked == False
    
    def test_run_job_success(self, app):
        """Test successful job execution."""
        test_data = self.setup_test_data(app)
        
        with app.app_context():
            job_props = {
                'chunk_id': test_data['scene_chunk_id'],
                'bot_id': test_data['bot_chunk_id'],
                'mode': 'write',
                'options': {
                    'preserve_formatting': True,
                    'track_changes': False
                }
            }
            
            job = Job(
                job_id='test-job-1',
                book_id=test_data['book_id'],
                job_type='GenerateChunk',
                state='pending',
                props=job_props
            )
            db.session.add(job)
            db.session.commit()
            
            generate_job = GenerateChunkJob(job)
            
            # Run the job
            generate_job.execute()
            
            # Verify chunk content was updated
            chunk = Chunk.query.filter_by(chunk_id=test_data['scene_chunk_id']).first()
            assert chunk.text != 'Original scene content'
            assert 'Mode: write' in chunk.text
            assert 'Generated by Test Bot' in chunk.text
            
            # Verify chunk is unlocked after completion
            assert chunk.is_locked == False
            
            # Verify job state was updated
            db.session.refresh(job)
            assert job.state == 'completed'
    
    def test_all_generation_modes(self, app):
        """Test all generation modes."""
        test_data = self.setup_test_data(app)
        modes = ['write', 'rewrite', 'edit', 'copyedit', 'review']
        
        with app.app_context():
            for mode in modes:
                # Reset chunk content
                chunk = Chunk.query.filter_by(chunk_id=test_data['scene_chunk_id']).first()
                chunk.text = f'Original content for {mode} test'
                chunk.is_locked = False
                db.session.commit()
                
                job_props = {
                    'chunk_id': test_data['scene_chunk_id'],
                    'bot_id': test_data['bot_chunk_id'],
                    'mode': mode,
                    'options': {}
                }
                
                job = Job(
                    job_id=f'test-job-{mode}',
                    book_id=test_data['book_id'],
                    job_type='GenerateChunk',
                    state='pending',
                    props=job_props
                )
                db.session.add(job)
                db.session.commit()
                
                generate_job = GenerateChunkJob(job)
                generate_job.execute()
                
                # Verify content was updated with mode-specific content
                db.session.refresh(chunk)
                assert f'Mode: {mode}' in chunk.text
                assert 'Generated by Test Bot' in chunk.text
                
                # For modes other than 'write', should include original content
                if mode != 'write':
                    assert f'Original content for {mode} test' in chunk.text
    
    def test_job_cancellation(self, app):
        """Test job cancellation functionality."""
        test_data = self.setup_test_data(app)
        
        with app.app_context():
            job_props = {
                'chunk_id': test_data['scene_chunk_id'],
                'bot_id': test_data['bot_chunk_id'],
                'mode': 'write',
                'options': {}
            }
            
            job = Job(
                job_id='test-job-1',
                book_id=test_data['book_id'],
                job_type='GenerateChunk',
                state='pending',
                props=job_props
            )
            db.session.add(job)
            db.session.commit()
            
            generate_job = GenerateChunkJob(job)
            
            # Initially not cancelled
            assert generate_job.is_cancelled() == False
            
            # Cancel the job
            job.state = 'cancelled'
            db.session.commit()
            
            # Should detect cancellation
            assert generate_job.is_cancelled() == True
    
    def test_logging_functionality(self, app):
        """Test job logging functionality."""
        test_data = self.setup_test_data(app)
        
        with app.app_context():
            job_props = {
                'chunk_id': test_data['scene_chunk_id'],
                'bot_id': test_data['bot_chunk_id'],
                'mode': 'write',
                'options': {}
            }
            
            job = Job(
                job_id='test-job-1',
                book_id=test_data['book_id'],
                job_type='GenerateChunk',
                state='pending',
                props=job_props
            )
            db.session.add(job)
            db.session.commit()
            
            generate_job = GenerateChunkJob(job)
            
            # Log a test message
            generate_job.log('Test log message', 'INFO')
            
            # Verify log entry was created
            log_entries = JobLog.query.filter_by(job_id=job.job_id).all()
            assert len(log_entries) > 0
            assert any('Test log message' in entry.log_entry for entry in log_entries)
