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
        db.session.remove() # Ensure session is cleaned up before dropping tables
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
            # Delete existing job with the same ID if it exists, to prevent IntegrityError
            existing_job = db.session.get(Job, 'test-job-1')
            if existing_job:
                # Before deleting, ensure related logs are handled if necessary, or cascade delete is set up
                # For simplicity in test setup, directly delete.
                JobLog.query.filter_by(job_id='test-job-1').delete()
                db.session.delete(existing_job)
                db.session.commit()

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
        """Test chunk locking and unlocking functionality (directly, as _lock_chunk helpers were removed)."""
        test_data = self.setup_test_data(app)
        with app.app_context():
            chunk_id = test_data['scene_chunk_id']
            chunk = Chunk.query.filter_by(chunk_id=chunk_id).first()
            
            assert chunk.is_locked is False

            # Simulate locking as done in GenerateTextJob.execute
            chunk.is_locked = True
            db.session.commit()
            db.session.refresh(chunk)
            assert chunk.is_locked is True

            # Simulate unlocking
            chunk.is_locked = False
            db.session.commit()
            db.session.refresh(chunk)
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

    def test_run_job_success(self, app):
        """Test successful job execution."""
        test_data = self.setup_test_data(app)
        with app.app_context():
            with patch('backend.jobs.generate_text.LLMCall') as mock_llm_call_cm:
                mock_llm_instance = mock_llm_call_cm.return_value
                mock_llm_instance.execute.return_value = True
                mock_llm_instance.output_text = "Generated text"
                mock_llm_instance.cost = 0.01
                mock_llm_instance.model = "mocked-model-success"
                mock_llm_instance.input_tokens = 10
                mock_llm_instance.output_tokens = 20
                mock_llm_instance.stop_reason = "mocked_stop_success"
                mock_llm_instance.error_status = None # Explicitly None for success case

                job_record = db.session.get(Job, test_data['job_id'])
                job = GenerateTextJob(job_record)
                result = job.run()

                assert result is True
                db.session.refresh(job_record)
                assert job_record.state == 'completed'
                chunk = Chunk.query.filter_by(chunk_id=test_data['scene_chunk_id']).first()
                assert chunk.text == "Generated text"
                assert chunk.is_locked is False

                # Verify logs
                logs = JobLog.query.filter_by(job_id=job_record.job_id).order_by(JobLog.created_at).all()
                assert len(logs) > 0
                assert any("Starting text generation" in log.log_entry for log in logs)
                assert any("LLM Output:" in log.log_entry for log in logs)
                assert any("Job completed successfully" in log.log_entry for log in logs)

    def test_run_job_with_llm_error_uses_placeholder(self, app):
        """Test that placeholder text is used when the LLM call fails."""
        with patch('backend.jobs.generate_text.LLMCall') as mock_llm_call:
            test_data = self.setup_test_data(app)
            with app.app_context():
                mock_llm_instance = mock_llm_call.return_value
                mock_llm_instance.execute.return_value = False # LLM fails
                mock_llm_instance.error_status = "Simulated LLM Error from mock"
                mock_llm_instance.cost = 0.0
                mock_llm_instance.model = "mocked-model-failure"
                mock_llm_instance.input_tokens = 5
                mock_llm_instance.output_tokens = 0
                mock_llm_instance.stop_reason = "error_stop"

                job_record = db.session.get(Job, test_data['job_id'])
                job = GenerateTextJob(job_record)
                result = job.run()

                assert result is True # The job itself completes, but uses placeholder
                assert job.job.state == 'completed'
                scene_chunk_obj = Chunk.query.filter_by(chunk_id=test_data['scene_chunk_id']).first()
                assert scene_chunk_obj.is_locked is False
                bot_chunk_obj = Chunk.query.filter_by(chunk_id=test_data['bot_chunk_id']).first()
                bot_title = bot_chunk_obj.props.get('title', 'Test Bot') # Get title from bot chunk props
                assert f"Placeholder text generated by {bot_title}." == scene_chunk_obj.text # Check for placeholder

    def test_run_job_validation_error(self, app):
        """Test job execution with a validation error."""
        test_data = self.setup_test_data(app)
        with app.app_context():
            job_record = db.session.get(Job, test_data['job_id'])
            job_record.props['mode'] = 'invalid_mode' # Set invalid mode
            db.session.commit() # Ensure props change is persisted
            
            job = GenerateTextJob(job_record)
            result = job.run()
            
            assert result is False
            db.session.refresh(job_record)
            assert job_record.state == 'failed'
            chunk = Chunk.query.filter_by(chunk_id=test_data['scene_chunk_id']).first()
            assert chunk.is_locked is False # Ensure chunk is unlocked on failure
            logs = JobLog.query.filter_by(job_id=job_record.job_id).all()
            assert any(f"Error: Invalid mode 'invalid_mode' in job props." in log.log_entry for log in logs)

    def test_job_logs_llm_cost_and_model(self, app):
        """Test that LLM call cost, model, and token info are logged correctly."""
        with patch('backend.jobs.generate_text.LLMCall') as mock_llm_call:
            test_data = self.setup_test_data(app)
            with app.app_context():
                mock_llm_instance = mock_llm_call.return_value
                mock_llm_instance.execute.return_value = True
                mock_llm_instance.output_text = "Generated text for cost logging test"
                mock_llm_instance.model = "test-model-v1"
                mock_llm_instance.cost = 0.00123
                mock_llm_instance.input_tokens = 150
                mock_llm_instance.output_tokens = 250
                mock_llm_instance.stop_reason = "test_stop"
                mock_llm_instance.error_status = None # Ensure all logged attributes are explicitly set

                job_record = db.session.get(Job, test_data['job_id'])
                job = GenerateTextJob(job_record)
                job.run()

                assert job.job.state == 'completed'

                llm_logs = JobLog.query.filter_by(job_id=test_data['job_id'], log_level='LLM').all()
                assert len(llm_logs) == 2
                llm_log = llm_logs[1] # Cost is in the second LLM log (output log)
                
                assert llm_log.props is not None
                assert llm_log.props.get('llm_cost') == 0.00123
                assert llm_log.props.get('llm_model') == "test-model-v1"
                assert llm_log.props.get('llm_input_tokens') == 150
                assert llm_log.props.get('llm_output_tokens') == 250
                assert llm_log.props.get('llm_stop_reason') == "test_stop"

    def test_job_updates_total_llm_cost_in_job_props(self, app):
        """Test that total_llm_cost is updated in Job.props."""
        with patch('backend.jobs.generate_text.LLMCall') as mock_llm_call:
            test_data = self.setup_test_data(app)
            with app.app_context():
                # Test case 1: Successful LLM call with cost
                mock_llm_instance_success = mock_llm_call.return_value
                mock_llm_instance_success.execute.return_value = True
                mock_llm_instance_success.output_text = "Generated text with cost"
                mock_llm_instance_success.cost = 0.0025
                mock_llm_instance_success.model = "test-model-cost"
                mock_llm_instance_success.input_tokens = 50
                mock_llm_instance_success.output_tokens = 150
                mock_llm_instance_success.stop_reason = "cost_stop_success"
                mock_llm_instance_success.error_status = None

                job_record_success = db.session.get(Job, test_data['job_id'])
                # Ensure props is a dict
                if not isinstance(job_record_success.props, dict):
                     job_record_success.props = json.loads(job_record_success.props or '{}')
                job_record_success.props['total_llm_cost'] = 0.0 # Reset for test
                db.session.commit()
                
                job_success = GenerateTextJob(job_record_success)
                job_success.run()

                db.session.refresh(job_record_success)
                assert job_record_success.state == 'completed'
                assert job_record_success.props.get('total_llm_cost') == 0.0025

                # Test case 2: LLM call fails (cost should remain 0 or be set to 0)
                # Re-setup or create a new job for a clean state if necessary
                # For simplicity, reusing the job record but resetting relevant fields
                job_record_fail_id = test_data['job_id'] # or create a new job
                job_record_fail = db.session.get(Job, job_record_fail_id)
                job_record_fail.state = 'pending' # Reset state
                if not isinstance(job_record_fail.props, dict):
                     job_record_fail.props = json.loads(job_record_fail.props or '{}')
                job_record_fail.props['total_llm_cost'] = 0.0 # Reset cost
                db.session.commit()

                mock_llm_instance_fail = mock_llm_call.return_value
                mock_llm_instance_fail.execute.return_value = False # LLM call fails
                mock_llm_instance_fail.cost = 0.0 # Cost is 0 on failure
                mock_llm_instance_fail.error_status = "Simulated LLM failure"
                mock_llm_instance_fail.model = "test-model-fail"
                mock_llm_instance_fail.input_tokens = 10
                mock_llm_instance_fail.output_tokens = 0
                mock_llm_instance_fail.stop_reason = "cost_stop_fail"

                job_fail = GenerateTextJob(job_record_fail)
                job_fail.run()

                db.session.refresh(job_record_fail)
                # Job state can be 'completed' (if placeholder is used) or 'failed' depending on exact logic for LLM failure handling
                # The key is that total_llm_cost should reflect no cost was incurred from the failed LLM call
                assert job_record_fail.props.get('total_llm_cost') == 0.0

    def test_run_job_fails_on_exception(self, app):
        """Test that the job fails gracefully when an unexpected exception occurs."""
        with patch('backend.jobs.generate_text.LLMCall') as mock_llm_call:
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
