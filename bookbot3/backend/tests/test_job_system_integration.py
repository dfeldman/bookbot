"""
Unit tests for job system integration and GenerateTextJob registration.
"""

import pytest
import json
import os
from unittest.mock import patch, MagicMock

from backend.models import db, User, Book, Chunk, Job, JobLog
from backend.jobs.generate_text import GenerateTextJob
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
        
        # Check that 'generate_text' is in registered job types
        assert 'generate_text' in processor.job_types
        
        # Check that it maps to the correct class
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
            
            # Create job through processor
            generate_job = processor.create_job_instance(job)
            
            # Verify it's the correct type
            assert isinstance(generate_job, GenerateTextJob)
            assert generate_job.job == job
    
    def test_job_processor_run_generate_text_job(self, app):
        """Test running GenerateTextJob through the job processor."""
        test_data = self.setup_test_data(app)
        
        with app.app_context():
            # Get fresh objects from database
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
            
            # Create and execute the job
            processor = get_job_processor()
            job_class = processor.job_types['generate_text']
            job_instance = job_class(job)
            
            # Mock the LLM call to avoid external dependencies
            with patch('backend.jobs.generate_text.LLMCall') as mock_llm:
                mock_llm.return_value.execute.return_value = True
                mock_llm.return_value.output_text = "REWRITE: This is the rewritten content"
                mock_llm.return_value.cost = 0.001
                
                # Execute the job
                success = job_instance.execute()
                
                # Verify execution was successful
                assert success, "Job should execute successfully"
                
                # Refresh chunk from database
                db.session.refresh(scene_chunk)
                
                # Verify chunk was updated
                assert "REWRITE" in scene_chunk.text, "Chunk content should be updated"
                assert not scene_chunk.is_locked, "Chunk should be unlocked after job completion"
    
    def test_invalid_job_type(self, app):
        """Test handling of invalid job type."""
        processor = get_job_processor()
        
        # Test that invalid job type is not in registry
        assert 'invalid_job_type' not in processor.job_types
        
        # Test that getting invalid job class returns None
        job_class = processor.job_types.get('invalid_job_type')
        assert job_class is None
    
    def test_all_generation_modes_through_processor(self, app):
        """Test all generation modes through the job processor."""
        test_data = self.setup_test_data(app)
        
        with app.app_context():
            modes = ['write', 'rewrite', 'edit', 'copyedit', 'review']
            
            for mode in modes:
                # Get fresh objects from database
                book = db.session.get(Book, test_data['book_id'])
                scene_chunk = Chunk.query.filter_by(chunk_id=test_data['scene_chunk_id']).first()
                bot_chunk = Chunk.query.filter_by(chunk_id=test_data['bot_chunk_id']).first()

                # Reset chunk content for each test
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
                
                # Create and execute the job
                processor = get_job_processor()
                job_class = processor.job_types['generate_text']
                job_instance = job_class(job)
                
                # Mock the LLM call
                with patch('backend.jobs.generate_text.LLMCall') as mock_llm:
                    mock_llm.return_value.execute.return_value = True
                    mock_llm.return_value.output_text = f"{mode.upper()}: Generated content for {mode}"
                    mock_llm.return_value.cost = 0.001
                    
                    # Execute the job
                    success = job_instance.execute()
                    
                    # Verify execution was successful
                    assert success, f"Job for mode {mode} should execute successfully"
                    
                    # Refresh chunk from database
                    db.session.refresh(scene_chunk)
                    
                    # Verify content was updated with mode-specific content
                    assert mode.upper() in scene_chunk.text, f"Chunk should contain {mode} content"


class TestGenerateTextJobEdgeCases:
    """Test edge cases and error conditions for GenerateTextJob."""
    
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
    
    def test_empty_content_chunk(self, app):
        """Test handling of chunk with empty content."""
        test_data = self.setup_test_data(app)
        
        with app.app_context():
            # Get scene chunk and set it to empty content
            scene_chunk = Chunk.query.filter_by(chunk_id=test_data['scene_chunk_id']).first()
            scene_chunk.text = ''
            db.session.commit()
            
            # Create job for empty chunk
            job_props = {
                'chunk_id': scene_chunk.chunk_id,
                'bot_id': test_data['bot_chunk_id'],
                'mode': 'write',
                'options': {}
            }
            
            job = Job(
                job_id='test-empty-content',
                book_id=test_data['book_id'],
                job_type='generate_text',
                state='pending',
                props=job_props
            )
            db.session.add(job)
            db.session.commit()
            
            # Execute job
            processor = get_job_processor()
            job_class = processor.job_types['generate_text']
            job_instance = job_class(job)
            
            with patch('backend.jobs.generate_text.LLMCall') as mock_llm:
                mock_llm.return_value.execute.return_value = True
                mock_llm.return_value.output_text = "Generated content for empty chunk"
                mock_llm.return_value.cost = 0.001
                
                success = job_instance.execute()
                assert success, "Job should handle empty content"
                
                db.session.refresh(scene_chunk)
                assert len(scene_chunk.text) > 0, "Content should be generated"
    
    def test_special_characters_in_content(self, app):
        """Test handling of special characters in content."""
        test_data = self.setup_test_data(app)
        
        with app.app_context():
            # Get scene chunk and set special character content
            scene_chunk = Chunk.query.filter_by(chunk_id=test_data['scene_chunk_id']).first()
            scene_chunk.text = "Content with special chars: üñíçødé 中文 🎭 \"quotes\" & symbols!"
            db.session.commit()
            
            # Create job
            job_props = {
                'chunk_id': scene_chunk.chunk_id,
                'bot_id': test_data['bot_chunk_id'],
                'mode': 'edit',
                'options': {}
            }
            
            job = Job(
                job_id='test-special-chars',
                book_id=test_data['book_id'],
                job_type='generate_text',
                state='pending',
                props=job_props
            )
            db.session.add(job)
            db.session.commit()
            
            # Execute job
            processor = get_job_processor()
            job_class = processor.job_types['generate_text']
            job_instance = job_class(job)
            
            with patch('backend.jobs.generate_text.LLMCall') as mock_llm:
                mock_llm.return_value.execute.return_value = True
                mock_llm.return_value.output_text = "EDIT: Processed content with special characters preserved"
                mock_llm.return_value.cost = 0.001
                
                success = job_instance.execute()
                assert success, "Job should handle special characters"
                
                db.session.refresh(scene_chunk)
                assert "EDIT" in scene_chunk.text, "Content should be updated"
    
    def test_bot_with_complex_props(self, app):
        """Test bot with complex properties configuration."""
        test_data = self.setup_test_data(app)
        
        with app.app_context():
            # Get bot chunk and set complex properties
            bot_chunk = Chunk.query.filter_by(chunk_id=test_data['bot_chunk_id']).first()
            bot_chunk.props = {
                'title': 'Advanced Bot',
                'llm_alias': 'advanced-gpt',
                'temperature': 0.8,
                'max_tokens': 2000,
                'description': 'Advanced creative writing bot',
                'system_prompt': 'You are a master storyteller.',
                'custom_settings': {
                    'style': 'literary',
                    'voice': 'third_person'
                }
            }
            db.session.commit()
            
            # Create job
            job_props = {
                'chunk_id': test_data['scene_chunk_id'],
                'bot_id': bot_chunk.chunk_id,
                'mode': 'rewrite',
                'options': {}
            }
            
            job = Job(
                job_id='test-complex-bot',
                book_id=test_data['book_id'],
                job_type='generate_text',
                state='pending',
                props=job_props
            )
            db.session.add(job)
            db.session.commit()
            
            # Execute job
            processor = get_job_processor()
            job_class = processor.job_types['generate_text']
            job_instance = job_class(job)
            
            with patch('backend.jobs.generate_text.LLMCall') as mock_llm:
                mock_llm.return_value.execute.return_value = True
                mock_llm.return_value.output_text = "REWRITE: Content generated by advanced bot"
                mock_llm.return_value.cost = 0.001
                
                success = job_instance.execute()
                assert success, "Job should handle complex bot properties"
                
                scene_chunk = Chunk.query.filter_by(chunk_id=test_data['scene_chunk_id']).first()
                assert "REWRITE" in scene_chunk.text, "Content should be updated by advanced bot"
    
    def test_malformed_bot_props(self, app):
        """Test handling of malformed bot properties."""
        test_data = self.setup_test_data(app)
        
        with app.app_context():
            # Get bot chunk and set minimal valid properties
            bot_chunk = Chunk.query.filter_by(chunk_id=test_data['bot_chunk_id']).first()
            bot_chunk.props = {
                'title': 'Simple Bot',
                # Missing llm_alias - should use defaults
            }
            db.session.commit()
            
            # Create job
            job_props = {
                'chunk_id': test_data['scene_chunk_id'],
                'bot_id': bot_chunk.chunk_id,
                'mode': 'write',
                'options': {}
            }
            
            job = Job(
                job_id='test-minimal-bot',
                book_id=test_data['book_id'],
                job_type='generate_text',
                state='pending',
                props=job_props
            )
            db.session.add(job)
            db.session.commit()
            
            # Execute job
            processor = get_job_processor()
            job_class = processor.job_types['generate_text']
            job_instance = job_class(job)
            
            with patch('backend.jobs.generate_text.LLMCall') as mock_llm:
                mock_llm.return_value.execute.return_value = True
                mock_llm.return_value.output_text = "WRITE: Content with minimal bot config"
                mock_llm.return_value.cost = 0.001
                
                success = job_instance.execute()
                assert success, "Job should handle minimal bot properties gracefully"
                
                scene_chunk = Chunk.query.filter_by(chunk_id=test_data['scene_chunk_id']).first()
                assert "WRITE" in scene_chunk.text, "Content should be generated with default settings"
