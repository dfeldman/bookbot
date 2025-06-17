"""
Unit tests for YAML-based bot initialization functionality.

Tests the bot initialization system that loads bot configurations from
default_bots.yaml and creates bot chunks during the foundation job.
"""

import os
import tempfile
import yaml
import pytest
from unittest.mock import patch, mock_open

from backend.models import db, Book, Chunk, User
from backend.jobs.create_foundation import _initialize_default_bots
from app import create_app


class TestBotInitialization:
    """Test suite for bot initialization from YAML configuration."""
    
    @pytest.fixture
    def app(self):
        """Create test Flask app with in-memory database."""
        app = create_app()
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        
        with app.app_context():
            db.create_all()
            
            # Create test user
            user = User(
                user_id='test-user-123',
                props={'name': 'Test User', 'email': 'test@example.com'}
            )
            db.session.add(user)
            
            # Create test book
            book = Book(
                book_id='test-book-123',
                user_id='test-user-123',
                props={'title': 'Test Book', 'genre': 'Fiction'}
            )
            db.session.add(book)
            db.session.commit()
            
            yield app
            
            db.drop_all()
    
    @pytest.fixture
    def sample_bot_config(self):
        """Sample bot configuration for testing."""
        return {
            'bots': [
                {
                    'name': 'Test Writer Bot',
                    'llm_alias': 'Writer',
                    'description': 'A test writing bot',
                    'system_prompt': 'You are a test writing assistant.',
                    'temperature': 0.7,
                    'order': 0
                },
                {
                    'name': 'Test Creative Bot',
                    'llm_alias': 'Thinker',
                    'description': 'A test creative bot',
                    'system_prompt': 'You are a test creative assistant.',
                    'temperature': 0.9,
                    'order': 1,
                    'custom_field': 'custom_value'
                }
            ]
        }
    
    @pytest.fixture
    def log_messages(self):
        """Fixture to capture log messages."""
        messages = []
        def log_callback(message):
            messages.append(message)
        return messages, log_callback
    
    def test_initialize_bots_success(self, app, sample_bot_config, log_messages):
        """Test successful bot initialization from YAML."""
        messages, log_callback = log_messages
        
        with app.app_context():
            # Mock the YAML file reading
            yaml_content = yaml.dump(sample_bot_config)
            
            with patch('os.path.exists', return_value=True), \
                 patch('builtins.open', mock_open(read_data=yaml_content)):
                
                bot_count = _initialize_default_bots('test-book-123', log_callback)
                
                # Verify bot count
                assert bot_count == 2
                
                # Verify log messages
                assert any('Created bot: Test Writer Bot' in msg for msg in messages)
                assert any('Created bot: Test Creative Bot' in msg for msg in messages)
                
                # Verify bots were created in database
                bots = Chunk.query.filter_by(book_id='test-book-123', type='bot').all()
                assert len(bots) == 2
                
                # Verify first bot properties
                writer_bot = next(bot for bot in bots if bot.props.get('name') == 'Test Writer Bot')
                assert writer_bot.props['llm_alias'] == 'Writer'
                assert writer_bot.props['description'] == 'A test writing bot'
                assert writer_bot.props['system_prompt'] == 'You are a test writing assistant.'
                assert writer_bot.props['temperature'] == 0.7
                assert writer_bot.order == 0.0
                assert writer_bot.type == 'bot'
                assert writer_bot.text == ''
                assert writer_bot.chapter is None
                
                # Verify second bot properties (including custom field)
                creative_bot = next(bot for bot in bots if bot.props.get('name') == 'Test Creative Bot')
                assert creative_bot.props['llm_alias'] == 'Thinker'
                assert creative_bot.props['custom_field'] == 'custom_value'
                assert creative_bot.order == 1.0
    
    def test_initialize_bots_file_not_found(self, app, log_messages):
        """Test behavior when YAML file doesn't exist."""
        messages, log_callback = log_messages
        
        with app.app_context():
            with patch('os.path.exists', return_value=False):
                bot_count = _initialize_default_bots('test-book-123', log_callback)
                
                assert bot_count == 0
                assert any('Bot config file not found' in msg for msg in messages)
                
                # Verify no bots were created
                bots = Chunk.query.filter_by(book_id='test-book-123', type='bot').all()
                assert len(bots) == 0
    
    def test_initialize_bots_empty_config(self, app, log_messages):
        """Test behavior with empty or invalid YAML config."""
        messages, log_callback = log_messages
        
        with app.app_context():
            # Test empty config
            with patch('os.path.exists', return_value=True), \
                 patch('builtins.open', mock_open(read_data='{}')):
                
                bot_count = _initialize_default_bots('test-book-123', log_callback)
                
                assert bot_count == 0
                assert any('No bots found in configuration' in msg for msg in messages)
    
    def test_initialize_bots_invalid_yaml(self, app, log_messages):
        """Test behavior with invalid YAML syntax."""
        messages, log_callback = log_messages
        
        with app.app_context():
            invalid_yaml = "bots:\n  - name: 'Invalid\n    missing_quote"
            
            with patch('os.path.exists', return_value=True), \
                 patch('builtins.open', mock_open(read_data=invalid_yaml)):
                
                bot_count = _initialize_default_bots('test-book-123', log_callback)
                
                assert bot_count == 0
                assert any('Error initializing default bots' in msg for msg in messages)
    
    def test_initialize_bots_missing_name(self, app, log_messages):
        """Test behavior when bot configuration is missing required 'name' field."""
        messages, log_callback = log_messages
        
        config = {
            'bots': [
                {
                    'llm_alias': 'Writer',
                    'description': 'Bot without name'
                },
                {
                    'name': 'Valid Bot',
                    'llm_alias': 'Writer'
                }
            ]
        }
        
        with app.app_context():
            yaml_content = yaml.dump(config)
            
            with patch('os.path.exists', return_value=True), \
                 patch('builtins.open', mock_open(read_data=yaml_content)):
                
                bot_count = _initialize_default_bots('test-book-123', log_callback)
                
                # Should create only the valid bot
                assert bot_count == 1
                assert any("missing 'name' field, skipping" in msg for msg in messages)
                
                # Verify only valid bot was created
                bots = Chunk.query.filter_by(book_id='test-book-123', type='bot').all()
                assert len(bots) == 1
                assert bots[0].props['name'] == 'Valid Bot'
    
    def test_initialize_bots_default_values(self, app, log_messages):
        """Test that bots get proper default values for missing fields."""
        messages, log_callback = log_messages
        
        config = {
            'bots': [
                {
                    'name': 'Minimal Bot'
                    # Missing all other fields
                }
            ]
        }
        
        with app.app_context():
            yaml_content = yaml.dump(config)
            
            with patch('os.path.exists', return_value=True), \
                 patch('builtins.open', mock_open(read_data=yaml_content)):
                
                bot_count = _initialize_default_bots('test-book-123', log_callback)
                
                assert bot_count == 1
                
                bot = Chunk.query.filter_by(book_id='test-book-123', type='bot').first()
                assert bot.props['name'] == 'Minimal Bot'
                assert bot.props['llm_alias'] == 'Writer'  # Default value
                assert bot.props['description'] == ''  # Default value
                assert bot.props['system_prompt'] == ''  # Default value
                assert bot.props['temperature'] == 0.7  # Default value
                assert bot.order == 0.0  # Default order (bot_count = 0)
    
    def test_initialize_bots_order_handling(self, app, log_messages):
        """Test proper handling of bot ordering."""
        messages, log_callback = log_messages
        
        config = {
            'bots': [
                {
                    'name': 'Bot C',
                    'order': 2
                },
                {
                    'name': 'Bot A',
                    'order': 0
                },
                {
                    'name': 'Bot B'
                    # No order specified, should use bot_count (2)
                }
            ]
        }
        
        with app.app_context():
            yaml_content = yaml.dump(config)
            
            with patch('os.path.exists', return_value=True), \
                 patch('builtins.open', mock_open(read_data=yaml_content)):
                
                bot_count = _initialize_default_bots('test-book-123', log_callback)
                
                assert bot_count == 3
                
                # Verify ordering - use explicit order with secondary sort by name
                from sqlalchemy import text, cast, String
                bots = Chunk.query.filter_by(book_id='test-book-123', type='bot')\
                    .order_by(Chunk.order, cast(Chunk.props.op('->')('name'), String)).all()
                
                assert bots[0].props['name'] == 'Bot A'
                assert bots[0].order == 0.0
                assert bots[1].props['name'] == 'Bot B'
                assert bots[1].order == 2.0  # Uses bot_count when order not specified
                assert bots[2].props['name'] == 'Bot C'
                assert bots[2].order == 2.0
    
    def test_initialize_bots_custom_properties_preserved(self, app, log_messages):
        """Test that custom properties from YAML are preserved."""
        messages, log_callback = log_messages
        
        config = {
            'bots': [
                {
                    'name': 'Custom Bot',
                    'llm_alias': 'Writer',
                    'custom_prop1': 'value1',
                    'custom_prop2': 42,
                    'custom_prop3': ['list', 'of', 'values'],
                    'nested': {
                        'key': 'value'
                    }
                }
            ]
        }
        
        with app.app_context():
            yaml_content = yaml.dump(config)
            
            with patch('os.path.exists', return_value=True), \
                 patch('builtins.open', mock_open(read_data=yaml_content)):
                
                bot_count = _initialize_default_bots('test-book-123', log_callback)
                
                assert bot_count == 1
                
                bot = Chunk.query.filter_by(book_id='test-book-123', type='bot').first()
                assert bot.props['custom_prop1'] == 'value1'
                assert bot.props['custom_prop2'] == 42
                assert bot.props['custom_prop3'] == ['list', 'of', 'values']
                assert bot.props['nested'] == {'key': 'value'}
    
    def test_initialize_bots_utf8_encoding(self, app, log_messages):
        """Test that UTF-8 encoding is properly handled."""
        messages, log_callback = log_messages
        
        config = {
            'bots': [
                {
                    'name': 'Café Bot 🤖',
                    'description': 'Un bot qui parle français',
                    'system_prompt': 'You are a multilingual assistant. 你好! ¡Hola!'
                }
            ]
        }
        
        with app.app_context():
            yaml_content = yaml.dump(config, allow_unicode=True)
            
            with patch('os.path.exists', return_value=True), \
                 patch('builtins.open', mock_open(read_data=yaml_content)):
                
                bot_count = _initialize_default_bots('test-book-123', log_callback)
                
                assert bot_count == 1
                
                bot = Chunk.query.filter_by(book_id='test-book-123', type='bot').first()
                assert bot.props['name'] == 'Café Bot 🤖'
                assert bot.props['description'] == 'Un bot qui parle français'
                assert '你好' in bot.props['system_prompt']
                assert '¡Hola!' in bot.props['system_prompt']


class TestBotInitializationIntegration:
    """Integration tests for bot initialization within the foundation job."""
    
    @pytest.fixture
    def app(self):
        """Create test Flask app with in-memory database."""
        app = create_app()
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        
        with app.app_context():
            db.create_all()
            
            # Create test user
            user = User(
                user_id='test-user-123',
                props={'name': 'Test User', 'email': 'test@example.com'}
            )
            db.session.add(user)
            
            # Create test book
            book = Book(
                book_id='test-book-123',
                user_id='test-user-123',
                props={'title': 'Test Book', 'genre': 'Fiction'}
            )
            db.session.add(book)
            db.session.commit()
            
            yield app
            
            db.drop_all()
    
    def test_foundation_job_creates_bots(self, app):
        """Test that foundation job includes bot initialization."""
        # This would test the full foundation job integration
        # For now, we'll test that the bot initialization step is called
        
        with app.app_context():
            from backend.jobs.create_foundation import run_create_foundation_job
            
            # Mock the YAML file with a simple config
            simple_config = {
                'bots': [
                    {
                        'name': 'Foundation Test Bot',
                        'llm_alias': 'Writer'
                    }
                ]
            }
            
            yaml_content = yaml.dump(simple_config)
            
            with patch('os.path.exists', return_value=True), \
                 patch('builtins.open', mock_open(read_data=yaml_content)), \
                 patch('backend.jobs.create_foundation._generate_outline', return_value='Test outline'), \
                 patch('backend.jobs.create_foundation._generate_characters', return_value='Test characters'), \
                 patch('backend.jobs.create_foundation._generate_settings', return_value='Test settings'), \
                 patch('backend.jobs.create_foundation._add_tags_to_content', side_effect=lambda x, *args: x), \
                 patch('backend.jobs.create_foundation.get_bot_manager') as mock_bot_manager:
                
                # Mock bot manager methods
                mock_bot_manager.return_value.add_scene_ids.return_value = ('Tagged outline', ['scene1', 'scene2'])
                mock_bot_manager.return_value.extract_scenes_from_outline.return_value = [
                    {'scene_id': 'scene1', 'title': 'Scene 1', 'chapter': 1, 'order': 1.0, 'tags': []}
                ]
                
                log_messages = []
                def log_callback(message):
                    log_messages.append(message)
                
                # Run foundation job
                result = run_create_foundation_job(
                    job_id='test-job-123',
                    book_id='test-book-123',
                    props={
                        'brief': 'Test brief',
                        'style': 'Test style'
                    },
                    log_callback=log_callback
                )
                
                assert result is True
                
                # Verify bot initialization was called
                assert any('Step 13: Initializing default bots' in msg for msg in log_messages)
                assert any('Created bot: Foundation Test Bot' in msg for msg in log_messages)
                assert any('Created 1 default bot chunks' in msg for msg in log_messages)
                
                # Verify bot was actually created
                bots = Chunk.query.filter_by(book_id='test-book-123', type='bot').all()
                assert len(bots) == 1
                assert bots[0].props['name'] == 'Foundation Test Bot'


if __name__ == '__main__':
    pytest.main([__file__])
