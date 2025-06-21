"""
Unit tests for job system integration and GenerateChunkJob registration.
"""

import pytest
import json
from unittest.mock import patch, MagicMock

from backend.models import db, User, Book, Chunk, Job, JobLog
from backend.jobs.generate_chunk import GenerateChunkJob
from backend.jobs import get_job_processor
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
    
    def test_generate_text_job_registered(self):
        """Test that generate_text job type is properly registered."""
        processor = get_job_processor()
        
        # Check that 'GenerateChunk' is in registered job types
        assert 'GenerateChunk' in processor.job_types
        
        # Check that it maps to the correct class
        assert processor.job_types['GenerateChunk'] == GenerateChunkJob
    
    def test_job_processor_creates_generate_text_job(self, app):
        """Test that job processor can create GenerateChunkJob instances."""
        test_data = self.setup_test_data(app)
        
        with app.app_context():
            # Get fresh objects from database using chunk_ids
            book = db.session.get(Book, test_data['book_id'])
            scene_chunk = Chunk.query.filter_by(chunk_id=test_data['scene_chunk_id']).first()
            bot_chunk = Chunk.query.filter_by(chunk_id=test_data['bot_chunk_id']).first()

            job_props = {
                'chunk_id': scene_chunk.chunk_id,
                'bot_id': bot_chunk.chunk_id,
                'mode': 'write',
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
            
            # Check that job type is registered
            assert 'GenerateChunk' in processor.job_types
            job_class = processor.job_types['GenerateChunk']
            
            # Create job instance directly
            generate_job = job_class(job)
            
            # Verify it's the correct type
            assert isinstance(generate_job, GenerateChunkJob)
            assert generate_job.job == job
    
    def test_all_generation_modes_through_processor(self, app):
        """Test all generation modes through the job processor."""
        test_data = self.setup_test_data(app)
        modes = ['write', 'rewrite', 'edit', 'copyedit', 'review']
        
        with app.app_context():
            processor = get_job_processor()
            
            for mode in modes:
                # Reset chunk content for each test
                chunk = Chunk.query.filter_by(chunk_id=test_data['scene_chunk_id']).first()
                chunk.text = f'Original content for {mode} test'
                chunk.is_locked = False
                db.session.commit()
                
                job_props = {
                    'chunk_id': test_data['scene_chunk_id'],
                    'bot_id': test_data['bot_chunk_id'],
                    'mode': mode,
                    'options': {
                        'preserve_formatting': True,
                        'track_changes': False
                    }
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
                
                # Create and run job through processor
                job_class = processor.job_types['GenerateChunk']
                generate_job = job_class(job)
                generate_job.execute()
                
                # Verify content was updated with mode-specific content
                db.session.refresh(chunk)
                assert f'Mode: {mode}' in chunk.text
                assert 'Generated by Test Bot' in chunk.text
    
    def test_job_processor_handles_invalid_job_type(self, app):
        """Test handling of invalid job type."""
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
                job_type='invalid_job_type',
                state='pending',
                props=job_props
            )
            db.session.add(job)
            db.session.commit()
            
            processor = get_job_processor()
            
            # Should handle invalid job type gracefully
            with pytest.raises(ValueError, match="Unknown job type"):
                job_class = processor.job_types.get(job.job_type)
                if not job_class:
                    raise ValueError(f"Unknown job type: {job.job_type}")
                job_class(job)


class TestGenerateChunkJobEdgeCases:
    """Test edge cases and error conditions for GenerateChunkJob."""
    
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
            db.session.commit()
            
            return {
                'user': user,
                'book': book,
                'user_id': user.user_id,
                'book_id': book.book_id
            }
    
    def test_empty_content_chunk(self, app):
        """Test handling of chunk with empty content."""
        test_data = self.setup_test_data(app)
        
        with app.app_context():
            # Create chunk with empty content
            empty_chunk = Chunk(
                book_id=test_data['book_id'],
                props={'title': 'Empty Scene'},
                type='scene',
                text='',
                is_locked=False
            )
            db.session.add(empty_chunk)
            
            # Create test bot
            bot_chunk = Chunk(
                book_id=test_data['book_id'],
                props={
                    'title': 'Test Bot',
                    'llm_alias': 'test-llm'
                },
                type='bot',
                text='',
                is_locked=False
            )
            db.session.add(bot_chunk)
            
            db.session.commit()
            
            job_props = {
                'chunk_id': empty_chunk.chunk_id,
                'bot_id': bot_chunk.chunk_id,
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
            
            # Should handle empty content gracefully
            generate_job.execute()
            
            # Verify content was generated
            db.session.refresh(empty_chunk)
            assert len(empty_chunk.text) > 0
            assert 'Mode: write' in empty_chunk.text
    
    def test_special_characters_in_content(self, app):
        """Test handling of special characters in content."""
        test_data = self.setup_test_data(app)
        
        with app.app_context():
            # Content with special characters
            special_content = "Content with special chars: üñíçødé 中文 🎭 \"quotes\" 'apostrophes' & symbols!"
            
            special_chunk = Chunk(
                book_id=test_data['book_id'],
                props={"title": 'Special Scene'},
                type='scene',
                text=special_content,
                is_locked=False
            )
            db.session.add(special_chunk)
            
            bot_chunk = Chunk(
                book_id=test_data['book_id'],
                props={
                    'title': 'Test Bot',
                    'llm_alias': 'test-llm'
                },
                type='bot',
                text='',
                is_locked=False
            )
            db.session.add(bot_chunk)
            
            db.session.commit()
            
            job_props = {
                'chunk_id': special_chunk.chunk_id,
                'bot_id': bot_chunk.chunk_id,
                'mode': 'copyedit',
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
            
            # Should handle special characters
            generate_job.execute()
            
            # Verify content includes special characters
            db.session.refresh(special_chunk)
            # Should contain some of the original special characters or reference them
            assert 'üñíçødé' in special_chunk.text or 'Content with special' in special_chunk.text
    
    def test_complex_bot_configuration(self, app):
        """Test bot with complex properties configuration."""
        test_data = self.setup_test_data(app)
        
        with app.app_context():
            scene_chunk = Chunk(
                book_id=test_data['book_id'],
                props={"title": 'Test Scene'},
                type='scene',
                text='Original content',
                is_locked=False
            )
            db.session.add(scene_chunk)
            
            # Bot with complex properties
            complex_props = {
                'llm_alias': 'advanced-gpt',
                'temperature': 0.8,
                'max_tokens': 2000,
                'top_p': 0.9,
                'frequency_penalty': 0.1,
                'presence_penalty': 0.1,
                'description': 'Advanced creative writing bot',
                'system_prompt': 'You are a master storyteller with decades of experience.',
                'custom_settings': {
                    'style': 'literary',
                    'voice': 'third_person',
                    'tense': 'past'
                }
            }
            
            # Merge title with complex props
            merged_props = {"title": 'Advanced Bot'}
            merged_props.update(complex_props)
            
            complex_bot = Chunk(
                book_id=test_data['book_id'],
                props=json.dumps(merged_props),
                type='bot',
                text='',
                is_locked=False
            )
            db.session.add(complex_bot)
            
            db.session.commit()
            
            job_props = {
                'chunk_id': scene_chunk.chunk_id,
                'bot_id': complex_bot.chunk_id,
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
            
            # Should handle complex bot configuration
            generate_job.execute()
            
            # Verify job completed successfully
            db.session.refresh(scene_chunk)
            assert 'Generated by Advanced Bot' in scene_chunk.text
    
    def test_malformed_bot_props(self, app):
        """Test handling of malformed bot properties JSON."""
        test_data = self.setup_test_data(app)
        
        with app.app_context():
            scene_chunk = Chunk(
                book_id=test_data['book_id'],
                props={"title": 'Test Scene'},
                type='scene',
                text='Original content',
                is_locked=False
            )
            db.session.add(scene_chunk)
            
            # Bot with malformed JSON props - just use the malformed props directly
            broken_bot = Chunk(
                book_id=test_data['book_id'],
                props='{"invalid": json}',  # Invalid JSON
                type='bot',
                text='',
                is_locked=False
            )
            db.session.add(broken_bot)
            
            db.session.commit()
            
            job_props = {
                'chunk_id': scene_chunk.chunk_id,
                'bot_id': broken_bot.chunk_id,
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
            
            # Should handle malformed JSON gracefully
            generate_job.execute()
            
            # Job should still complete (with default bot behavior)
            db.session.refresh(job)
            # The job might fail validation or complete with default behavior
            assert job.state in ['completed', 'failed']
