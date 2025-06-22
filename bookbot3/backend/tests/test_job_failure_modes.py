import pytest
from unittest.mock import patch

from backend.models import db, Job, Chunk, JobLog, User, Book
from backend.jobs import get_job_processor
from backend.jobs.generate_chunk import GenerateChunkJob
from backend.models import utcnow

# TODO: Import or define necessary fixtures (app, db_session, init_test_db, etc.)
# For now, assume they will be available from conftest.py or similar

class TestJobFailureModes:

    def setup_test_data(self, app, book_id_val='test-book-failure') -> dict:
        """Helper to set up common test data."""
        with app.app_context():
            # User
            user = User.query.filter(User.props.op('->>')('email') == 'test@example.com').first()
            if not user:
                user = User(user_id='test-user-failure', props={'email': 'test@example.com', 'name': 'Test User'})
                db.session.add(user)
                db.session.commit()

            # Book
            # book = Book.query.filter_by(book_id=book_id_val).first()
            # if not book:
            #     book = Book(book_id=book_id_val, title="Failure Test Book", user_id=user.user_id)
            #     db.session.add(book)
            #     db.session.commit()
            # else:
            #     # Clean up existing jobs and logs for this book to avoid conflicts
            #     JobLog.query.filter(JobLog.job_id.in_(
            #         db.session.query(Job.job_id).filter_by(book_id=book_id_val)
            #     )).delete(synchronize_session=False)
            #     Job.query.filter_by(book_id=book_id_val).delete(synchronize_session=False)
            #     db.session.commit()

            # Chunks
            scene_chunk = Chunk(
                book_id=book_id_val,
                props={'chunk_id': 'scene-chunk-failure'},
                text='Initial scene content for failure tests.',
                type='SCENE',
                is_latest=True,
                is_deleted=False,
                version=1
            )
            bot_chunk = Chunk(
                book_id=book_id_val,
                props={'chunk_id': 'bot-chunk-failure', 'title': 'Failure Test Bot', 'model_name': 'test-model'},
                text='Bot definition for failure tests.',
                type='BOT',
                is_latest=True,
                is_deleted=False,
                version=1
            )
            db.session.add_all([scene_chunk, bot_chunk])
            db.session.commit()
            return {
                'user_id': user.user_id,
                'book_id': book_id_val,
                'scene_chunk_id': scene_chunk.chunk_id,
                'bot_chunk_id': bot_chunk.chunk_id
            }

    def test_placeholder_failure_test(self, app):
        """A placeholder test to ensure the suite runs."""
        test_data = self.setup_test_data(app)
        with app.app_context():
            job = Job(
                job_id='failure-placeholder-job',
                book_id=test_data['book_id'],
                job_type='GenerateChunk',
                state='pending',
                props={'chunk_id': test_data['scene_chunk_id'], 'bot_id': test_data['bot_chunk_id']}
            )
            db.session.add(job)
            db.session.commit()

            assert job.state == 'pending'
            # In a real failure test, we would run the job and check for 'failed' state and logs
            # For now, just a basic assertion
            retrieved_job = db.session.get(Job, 'failure-placeholder-job')
            assert retrieved_job is not None
            assert retrieved_job.state == 'pending'

    def test_generate_text_job_fails_on_missing_chunk_id(self, app):
        """Test GenerateChunkJob validation fails if chunk_id is missing in props."""
        test_data = self.setup_test_data(app)
        with app.app_context():
            job_props_missing_chunk_id = {
                # 'chunk_id': test_data['scene_chunk_id'], # Intentionally missing
                'bot_id': test_data['bot_chunk_id'],
                'mode': 'write'
            }
            job = Job(
                job_id='failure-missing-chunk-id',
                book_id=test_data['book_id'],
                job_type='GenerateChunk',
                state='pending',
                props=job_props_missing_chunk_id
            )
            db.session.add(job)
            db.session.commit()

            job_instance = GenerateChunkJob(job)

            # Test validation directly
            assert not job_instance.validate(), "Validation should fail without chunk_id"

            # Test execute path (which should also fail due to validation)
            success = job_instance.execute()
            assert not success, "Execute should fail if validation fails"

            retrieved_job = db.session.get(Job, 'failure-missing-chunk-id')
            assert retrieved_job.state == 'failed', "Job state should be 'failed'"

            # Check for error log
            log_entry = JobLog.query.filter_by(job_id=job.job_id, log_level='ERROR').first()
            assert log_entry is not None, "Error log should be created"
            assert "Error: chunk_id is required in job props." in log_entry.log_entry, \
                f"Log entry missing expected message. Got: {log_entry.log_entry}"

    def test_failing_job_unlocks_book(self, app, job_processor):
        """Test that a job that fails unlocks the book it was operating on."""
        with app.app_context():
            # 1. Setup a book
            user = User.query.first()
            if not user:
                user = User(user_id='test-user-unlock', props={'email': 'unlock@example.com', 'name': 'Unlock Test User'})
                db.session.add(user)
                db.session.commit()

            book = Book(book_id='test-book-unlock', user_id=user.user_id, props={'title': 'Unlock Test Book'})
            db.session.add(book)
            db.session.commit()

            # 2. Create and queue the FailingJob
            job = Job(
                job_id='failing-job-unlock-test',
                book_id=book.book_id,
                job_type='failing_job',
                state='waiting',
                props={}
            )
            db.session.add(job)
            db.session.commit()

            # 3. Process the job
            job_processor.running = True  # Manually set running state for test
            job_processor._process_waiting_jobs()  # Manually trigger processing for testing

            # 4. Assertions
            # Re-fetch from DB to get the latest state
            processed_job = db.session.get(Job, 'failing-job-unlock-test')
            unlocked_book = db.session.get(Book, book.book_id)

            assert processed_job.state == 'error', f"Job should be in 'error' state, but was '{processed_job.state}'"
            assert 'This job is designed to fail for testing.' in processed_job.error_message, \
                f"Job error message was not set correctly. Got: '{processed_job.error_message}'"
            
            assert unlocked_book.job is None, \
                f"Book should be unlocked, but is still locked by job '{unlocked_book.job}'"
            assert unlocked_book.is_locked is False, \
                f"Book's is_locked flag should be False, but is '{unlocked_book.is_locked}'"


    # More test methods for specific failure modes will be added here
