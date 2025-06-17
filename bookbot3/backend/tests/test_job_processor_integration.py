import pytest
import json
from unittest.mock import patch, MagicMock

from backend.models import db, User, Book, Chunk, Job, JobLog
from backend.jobs.generate_text import GenerateTextJob
from backend.jobs import get_job_processor

class TestJobSystemIntegration:
    """Test cases for job system integration with GenerateTextJob."""
    
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
        assert 'generate_text' in processor.job_types
        assert processor.job_types['generate_text'] == GenerateTextJob
    
    def test_job_processor_creates_generate_text_job(self, app):
        """Test that job processor can create GenerateTextJob instances."""
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
                job_type='generate_text',
                state='pending',
                props=job_props
            )
            db.session.add(job)
            db.session.commit()
            
            processor = get_job_processor()
            generate_job = processor.create_job_instance(job)
            
            assert isinstance(generate_job, GenerateTextJob)
            assert generate_job.job == job
    
    def test_job_processor_run_generate_text_job(self, app):
        """Test running GenerateTextJob through the job processor."""
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
                job_type='generate_text',
                state='pending',
                props=job_props
            )
            db.session.add(job)
            db.session.commit()
            
            processor = get_job_processor()
            job_class = processor.job_types['generate_text']
            job_instance = job_class(job)
            
            with patch('backend.jobs.generate_text.LLMCall') as mock_llm:
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
                    job_type='generate_text',
                    state='pending',
                    props=job_props
                )
                db.session.add(job)
                db.session.commit()
                
                processor = get_job_processor()
                job_class = processor.job_types['generate_text']
                job_instance = job_class(job)
                
                with patch('backend.jobs.generate_text.LLMCall') as mock_llm:
                    mock_llm.return_value.execute.return_value = True
                    mock_llm.return_value.output_text = f"{mode.upper()}: Generated content for {mode}"
                    mock_llm.return_value.cost = 0.001
                    
                    success = job_instance.execute()
                    
                    assert success, f"Job for mode {mode} should execute successfully"
                    
                    db.session.refresh(scene_chunk)
                    
                    assert mode.upper() in scene_chunk.text, f"Chunk should contain {mode} content"
