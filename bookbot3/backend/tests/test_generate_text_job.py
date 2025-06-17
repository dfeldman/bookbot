"""
Unit tests for GenerateTextJob functionality.
"""

import pytest
import json
from unittest.mock import patch, MagicMock

from backend.models import db, User, Book, Chunk, Job, JobLog
from backend.jobs.generate_text import GenerateTextJob
from app import create_app


class TestConfig:
    """Test configuration."""
    TESTING = True
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


class TestGenerateTextJob:
    """Test cases for GenerateTextJob."""

    def setup_test_data(self, app):
        """Set up test data in the database."""
        with app.app_context():
            user = User(props={'username': 'testuser', 'email': 'test@example.com'})
            db.session.add(user)
            db.session.commit()

            book = Book(user_id=user.user_id, props={'title': 'Test Book'})
            db.session.add(book)
            db.session.commit()

            scene_chunk = Chunk(book_id=book.book_id, props={'title': 'Test Scene'}, type='scene', text='Original scene content', is_locked=False)
            db.session.add(scene_chunk)

            bot_props = {'title': 'Test Bot', 'llm_alias': 'test-llm'}
            bot_chunk = Chunk(book_id=book.book_id, props=bot_props, type='bot', text='')
            db.session.add(bot_chunk)
            db.session.commit()

            job_props = {'chunk_id': scene_chunk.chunk_id, 'bot_id': bot_chunk.chunk_id, 'mode': 'write'}
            job_record = Job(job_id='test-job-1', book_id=book.book_id, job_type='generate_text', state='pending', props=job_props)
            db.session.add(job_record)
            db.session.commit()

            return {
                'user_id': user.user_id,
                'book_id': book.book_id,
                'scene_chunk_id': scene_chunk.chunk_id,
                'bot_chunk_id': bot_chunk.chunk_id,
                'job_id': job_record.job_id
            }

    def test_job_initialization(self, app):
        """Test job initialization with a valid job record."""
        test_data = self.setup_test_data(app)
        with app.app_context():
            job_record = db.session.get(Job, test_data['job_id'])
            job = GenerateTextJob(job_record)
            assert job.job == job_record
            assert job.chunk_id == test_data['scene_chunk_id']
            assert job.bot_id == test_data['bot_chunk_id']
            assert job.mode == 'write'

    def test_lock_and_unlock_chunk(self, app):
        """Test chunk locking and unlocking functionality."""
        test_data = self.setup_test_data(app)
        with app.app_context():
            job_record = db.session.get(Job, test_data['job_id'])
            job = GenerateTextJob(job_record)
            chunk_id = test_data['scene_chunk_id']

            job._lock_chunk(chunk_id)
            chunk = Chunk.query.filter_by(chunk_id=chunk_id).first()
            assert chunk.is_locked is True

            job._unlock_chunk(chunk_id)
            chunk = Chunk.query.filter_by(chunk_id=chunk_id).first()
            assert chunk.is_locked is False

    def test_generate_placeholder_text_all_modes(self, app):
        """Test placeholder text generation for all modes."""
        test_data = self.setup_test_data(app)
        with app.app_context():
            job_record = db.session.get(Job, test_data['job_id'])
            job = GenerateTextJob(job_record)
            chunk = Chunk.query.filter_by(chunk_id=test_data['scene_chunk_id']).first()
            bot_chunk = Chunk.query.filter_by(chunk_id=test_data['bot_chunk_id']).first()

            modes = ['write', 'rewrite', 'edit', 'copyedit', 'review']
            for mode in modes:
                job.props['mode'] = mode
                placeholder_text = job._generate_placeholder_text(chunk, bot_chunk)
                assert f"Mode: {mode}" in placeholder_text
                assert "Test Bot" in placeholder_text

    @patch('backend.jobs.generate_text.LLMCall')
    def test_run_job_success(self, mock_llm_call, app):
        """Test successful job execution."""
        test_data = self.setup_test_data(app)
        with app.app_context():
            mock_llm_instance = mock_llm_call.return_value
            mock_llm_instance.execute.return_value = True
            mock_llm_instance.output_text = "Generated text"
            mock_llm_instance.cost = 0.01

            job_record = db.session.get(Job, test_data['job_id'])
            job = GenerateTextJob(job_record)
            result = job.run()

            assert result is True
            assert job.job.state == 'completed'
            chunk = Chunk.query.filter_by(chunk_id=test_data['scene_chunk_id']).first()
            assert chunk.is_locked is False
            assert chunk.text == "Generated text"

    @patch('backend.jobs.generate_text.LLMCall')
    def test_run_job_with_llm_error_uses_placeholder(self, mock_llm_call, app):
        """Test that placeholder text is used when the LLM call fails."""
        test_data = self.setup_test_data(app)
        with app.app_context():
            mock_llm_instance = mock_llm_call.return_value
            mock_llm_instance.execute.return_value = False # LLM fails

            job_record = db.session.get(Job, test_data['job_id'])
            job = GenerateTextJob(job_record)
            result = job.run()

            assert result is True # The job itself completes, but uses placeholder
            assert job.job.state == 'completed'
            chunk = Chunk.query.filter_by(chunk_id=test_data['scene_chunk_id']).first()
            assert chunk.is_locked is False
            assert "Generated by Test Bot" in chunk.text # Check for placeholder

    def test_run_job_validation_error(self, app):
        """Test job execution with a validation error."""
        test_data = self.setup_test_data(app)
        with app.app_context():
            job_record = db.session.get(Job, test_data['job_id'])
            job_record.props['mode'] = 'invalid_mode' # Set invalid mode
            
            job = GenerateTextJob(job_record)
            result = job.run()
            
            assert result is False
            db.session.refresh(job_record)
            assert job_record.state == 'failed'
            chunk = Chunk.query.filter_by(chunk_id=test_data['scene_chunk_id']).first()
            assert chunk.is_locked is False # Ensure chunk is unlocked on failure
            logs = JobLog.query.filter_by(job_id=job_record.job_id).all()
            assert any("Job validation failed" in log.log_entry for log in logs)

    @patch('backend.jobs.generate_text.LLMCall')
    def test_run_job_fails_on_exception(self, mock_llm_call, app):
        """Test that the job fails gracefully when an unexpected exception occurs."""
        test_data = self.setup_test_data(app)
        with app.app_context():
            mock_llm_call.side_effect = Exception("Unexpected API error")

            job_record = db.session.get(Job, test_data['job_id'])
            job = GenerateTextJob(job_record)
            result = job.run()

            assert result is False
            assert job.job.state == 'failed'
            chunk = Chunk.query.filter_by(chunk_id=test_data['scene_chunk_id']).first()
            assert chunk.is_locked is False # Ensure chunk is unlocked on failure
            logs = JobLog.query.filter_by(job_id=job_record.job_id).all()
            assert any("Unexpected API error" in log.log_entry for log in logs)
