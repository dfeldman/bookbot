import pytest
import json
from unittest.mock import patch, MagicMock

from backend.models import db, User, Book, Chunk, Job, JobLog
from backend.jobs.generate_chunk import GenerateChunkJob
from backend.jobs import get_job_processor, BaseJob

# Helper class for testing processor state commits
class MockJob(BaseJob):
    def __init__(self, job, success=True, error=None):
        super().__init__(job)
        self.should_succeed = success
        self.error_to_raise = error

    def execute(self):
        self.log("MockJob execute started.")
        if self.error_to_raise:
            self.log(f"MockJob raising error: {self.error_to_raise}")
            raise self.error_to_raise
        if self.should_succeed:
            self.log("MockJob execute finished successfully.")
            return True
        else:
            self.log("MockJob execute finished with failure.")
            self.job.error_message = "Mock job failed as requested."
            return False

class TestJobSystemIntegration:
    """Test cases for job system integration with GenerateChunkJob."""
    
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
            db.session.commit()
            
            book = Book(
                user_id=user.user_id,
                props={
                    'title': 'Test Book'
                }
            )
            db.session.add(book)
            db.session.commit()
            
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
            
            bot_props = {
                'title': 'Test Bot',
                'llm_alias': 'test-llm',
                'temperature': 0.7,
                'description': 'Test bot'
            }
            bot_chunk = Chunk(
                book_id=book.book_id,
                props=bot_props,
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
    
    def test_generate_text_job_registered(self):
        """Test that generate_text job type is properly registered."""
        processor = get_job_processor()
        assert 'GenerateChunk' in processor.job_types
        assert processor.job_types['GenerateChunk'] == GenerateChunkJob
    
    def test_job_processor_creates_generate_text_job(self, app):
        """Test that job processor can create GenerateChunkJob instances."""
        test_data = self.setup_test_data(app)
        
        with app.app_context():
            job_props = {
                'chunk_id': test_data['scene_chunk'].id,
                'bot_id': test_data['bot_chunk'].id,
                'mode': 'write',
                'options': {
                    'preserve_formatting': True,
                    'track_changes': False
                }
            }
            
            job = Job(
                job_id='test-job-1',
                book_id=test_data['book'].id,
                job_type='GenerateChunk',
                state='pending',
                props=job_props
            )
            db.session.add(job)
            db.session.commit()
            
            processor = get_job_processor()
            generate_job = processor.create_job_instance(job)
            
            assert isinstance(generate_job, GenerateChunkJob)
            assert generate_job.job == job
    
    def test_job_processor_run_generate_text_job(self, app):
        """Test running GenerateChunkJob through the job processor."""
        test_data = self.setup_test_data(app)
        
        with app.app_context():
            book = db.session.get(Book, test_data['book_id'])
            scene_chunk = Chunk.query.filter_by(chunk_id=test_data['scene_chunk_id']).first()
            bot_chunk = Chunk.query.filter_by(chunk_id=test_data['bot_chunk_id']).first()

            job_props = {
                'chunk_id': scene_chunk.chunk_id,
                'bot_id': bot_chunk.chunk_id,
                'mode': 'rewrite',
                'options': {
                    'preserve_formatting': True,
                    'track_changes': False
                }
            }
            
            job = Job(
                job_id='test-job-1',
                book_id=book.book_id,
                job_type='GenerateChunk',
                state='pending',
                props=job_props
            )
            db.session.add(job)
            db.session.commit()
            
            processor = get_job_processor()
            job_class = processor.job_types['GenerateChunk']
            job_instance = job_class(job)
            
            with patch('backend.jobs.generate_chunk.LLMCall') as mock_llm:
                mock_llm.return_value.execute.return_value = True
                mock_llm.return_value.output_text = "REWRITE: This is the rewritten content"
                mock_llm.return_value.cost = 0.001
                
                success = job_instance.execute()
                
                assert success, "Job should execute successfully"
                
                db.session.refresh(scene_chunk)
                
                assert "REWRITE" in scene_chunk.text, "Chunk content should be updated"
                assert not scene_chunk.is_locked, "Chunk should be unlocked after job completion"
    
    def test_invalid_job_type(self, app):
        """Test handling of invalid job type."""
        processor = get_job_processor()
        assert 'invalid_job_type' not in processor.job_types
        job_class = processor.job_types.get('invalid_job_type')
        assert job_class is None
    
    def test_all_generation_modes_through_processor(self, app):
        """Test all generation modes through the job processor."""
        test_data = self.setup_test_data(app)
        
        with app.app_context():
            modes = ['write', 'rewrite', 'edit', 'copyedit', 'review']
            
            for mode in modes:
                book = db.session.get(Book, test_data['book_id'])
                scene_chunk = Chunk.query.filter_by(chunk_id=test_data['scene_chunk_id']).first()
                bot_chunk = Chunk.query.filter_by(chunk_id=test_data['bot_chunk_id']).first()

                scene_chunk.text = f"Original content for {mode} test"
                scene_chunk.is_locked = False
                db.session.commit()

                job_props = {
                    'chunk_id': scene_chunk.chunk_id,
                    'bot_id': bot_chunk.chunk_id,
                    'mode': mode,
                    'options': {
                        'preserve_formatting': True,
                        'track_changes': False
                    }
                }
                
                job = Job(
                    job_id=f'test-job-{mode}',
                    book_id=book.book_id,
                    job_type='GenerateChunk',
                    state='pending',
                    props=job_props
                )
                db.session.add(job)
                db.session.commit()
                
                processor = get_job_processor()
                job_class = processor.job_types['GenerateChunk']
                job_instance = job_class(job)
                
                with patch('backend.jobs.generate_chunk.LLMCall') as mock_llm:
                    mock_llm.return_value.execute.return_value = True
                    mock_llm.return_value.output_text = f"{mode.upper()}: Generated content for {mode}"
                    mock_llm.return_value.cost = 0.001
                    
                    success = job_instance.execute()
                    
                    assert success, f"Job for mode {mode} should execute successfully"
                    
                    db.session.refresh(scene_chunk)
                    
                    assert mode.upper() in scene_chunk.text, f"Chunk should contain {mode} content"

    class MockJob(BaseJob):
        def execute(self) -> bool:
            """Execute mock job based on job.props."""
            test_case = self.job.props.get('test_case')

            if test_case == 'success':
                self.log("MockJob executed successfully.")
                return True
            
            if test_case == 'failure':
                self.log("MockJob failed as requested.", level='ERROR')
                return False

            if test_case == 'exception':
                error_message = self.job.props.get('error_message', "Execution exploded")
                raise ValueError(error_message)

            # Default behavior if test_case is not set
            self.log("MockJob executed with no test_case specified, returning True.", level='WARNING')
            return True

    def test_process_job_success_state_commit(self, app):
        """Test that _process_job commits 'completed' state and logs."""
        test_data = self.setup_test_data(app)

        with app.app_context():
            job = Job(
                job_id='test-commit-success',
                book_id=test_data['book_id'],
                job_type='mock_job',
                state='waiting',
                props={'test_case': 'success'}
            )
            db.session.add(job)
            db.session.commit()
            job_pk = job.job_id

        processor = get_job_processor()
        processor.register('mock_job', self.MockJob)

        processor._process_job(job)

        with app.app_context():
            processed_job = db.session.get(Job, job_pk)
            assert processed_job.state == 'completed'
            assert processed_job.completed_at is not None
            logs = JobLog.query.filter_by(job_id=job_pk).all()
            assert any("MockJob executed successfully." in log.log_entry for log in logs)

    def test_process_job_failure_state_commit(self, app):
        """Test that _process_job commits 'failed' state and logs."""
        test_data = self.setup_test_data(app)

        with app.app_context():
            job = Job(
                job_id='test-commit-failure',
                book_id=test_data['book_id'],
                job_type='mock_job',
                state='waiting',
                props={'test_case': 'failure'}
            )
            db.session.add(job)
            db.session.commit()
            job_pk = job.job_id

        processor = get_job_processor()
        processor.register('mock_job', self.MockJob)

        processor._process_job(job)

        with app.app_context():
            processed_job = db.session.get(Job, job_pk)
            assert processed_job.state == 'failed'
            assert processed_job.completed_at is not None
            logs = JobLog.query.filter_by(job_id=job_pk).all()
            assert any("MockJob failed as requested." in log.log_entry for log in logs)

    def test_process_job_exception_state_commit(self, app):
        """Test that _process_job commits 'error' state on exception."""
        test_data = self.setup_test_data(app)

        with app.app_context():
            job = Job(
                job_id='test-commit-exception',
                book_id=test_data['book_id'],
                job_type='mock_job',
                state='waiting',
                props={'test_case': 'exception', 'error_message': 'Execution exploded'}
            )
            db.session.add(job)
            db.session.commit()
            job_pk = job.job_id

        processor = get_job_processor()
        processor.register('mock_job', self.MockJob)

        processor._process_job(job)

        with app.app_context():
            processed_job = db.session.get(Job, job_pk)
            assert processed_job.state == 'error'
            assert processed_job.completed_at is not None
            
            # In case of an exception, the error is stored in the job's error_message field,
            # not in separate JobLog entries.
            assert "ValueError: Execution exploded" in processed_job.error_message
