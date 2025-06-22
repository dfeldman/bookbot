"""
Unit tests for job_utils module.

Tests the get_chunk_context function and related utilities for extracting
relevant outline sections, characters, and settings based on scene IDs and tags.
"""

import pytest
from backend.models import db, Book, Chunk
from backend.jobs.job_utils import (
    get_chunk_context, 
    get_outline_sections_list,
    get_characters_list, 
    get_settings_list,
    _extract_outline_section_by_id,
    _extract_sections_by_tags
)
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
def test_book_with_chunks(app):
    """Create a test book with outline, characters, and settings chunks."""
    with app.app_context():
        # Create test book
        book = Book(
            user_id="test-user-123",
            props={'title': 'Test Book', 'genre': 'Fantasy'}
        )
        db.session.add(book)
        db.session.commit()
        
        # Store the book_id since the book object will be detached
        book_id = book.book_id
        
        # Create outline chunk
        outline_text = """
## Chapter 1: The Beginning

### Joe goes to the store #adventure #shopping #scene_id=1
Joe decides he needs groceries and heads to the local market.
He meets an old friend there.

### Joe comes home #adventure #home #scene_id=2
After shopping, Joe returns home with his groceries.
He discovers something strange in his house.

## Chapter 2: The Mystery

### Joe investigates #mystery #investigation #scene_id=3
Joe starts looking into the strange discovery.
He finds clues that lead him deeper into mystery.
        """
        
        outline_chunk = Chunk(
            book_id=book_id,
            text=outline_text.strip(),
            type="outline",
            chapter=0,
            order=1.0,
            props={},
            word_count=len(outline_text.split())
        )
        db.session.add(outline_chunk)
        
        # Create characters chunk
        characters_text = """
## Character: Joe #adventure #home #mystery
Joe is the main protagonist. He's curious and brave.
He lives alone in a small house.

## Character: Old Friend #adventure #shopping
A friendly character Joe meets at the store.
They haven't seen each other in years.

## Character: Detective Smith #mystery #investigation
A local detective who helps Joe with the investigation.
Very thorough and methodical.

## Character: Shopkeeper #shopping
Runs the local market where Joe shops.
"""
        
        characters_chunk = Chunk(
            book_id=book_id,
            text=characters_text.strip(),
            type="characters",
            chapter=0,
            order=2.0,
            props={},
            word_count=len(characters_text.split())
        )
        db.session.add(characters_chunk)
        
        # Create settings chunk
        settings_text = """
## Settings: Local Market #adventure #shopping
A small neighborhood grocery store.
Has fresh produce and friendly staff.

## Settings: Joe's House #adventure #home #mystery
A cozy single-story home with a small garden.
Recently something strange was discovered here.

## Settings: Police Station #mystery #investigation
Where Detective Smith works.
Modern building with good facilities.
"""
        
        settings_chunk = Chunk(
            book_id=book_id,
            text=settings_text.strip(),
            type="settings",
            chapter=0,
            order=3.0,
            props={},
            word_count=len(settings_text.split())
        )
        db.session.add(settings_chunk)
        
        db.session.commit()
        
        # Return a simple object with just the book_id
        class TestBook:
            def __init__(self, book_id):
                self.book_id = book_id
        
        return TestBook(book_id)


class TestGetChunkContext:
    """Test the main get_chunk_context function."""
    
    def test_get_context_scene_1(self, app, test_book_with_chunks):
        """Test getting context for Scene 1."""
        with app.app_context():
            context = get_chunk_context(test_book_with_chunks.book_id, 1)
            
            # Check outline section
            assert "Joe goes to the store" in context['outline_section']
            assert "#scene_id=1" not in context['outline_section']
            assert "Joe decides he needs groceries" in context['outline_section']
            
            # Check tags
            assert "adventure" in context['tags']
            assert "shopping" in context['tags']
            assert len(context['tags']) == 2
            
            # Check characters - should include those with adventure or shopping tags
            assert len(context['characters_sections']) == 3  # Joe, Old Friend, Shopkeeper
            character_text = '\n'.join(context['characters_sections'])
            assert "Character: Joe" in character_text
            assert "Character: Old Friend" in character_text
            assert "Character: Shopkeeper" in character_text
            assert "Detective Smith" not in character_text  # No shared tags
            
            # Check settings - should include those with adventure or shopping tags
            assert len(context['settings_sections']) == 2  # Local Market, Joe's House
            settings_text = '\n'.join(context['settings_sections'])
            assert "Local Market" in settings_text
            assert "Joe's House" in settings_text
            assert "Police Station" not in settings_text  # No shared tags
    
    def test_get_context_scene_2(self, app, test_book_with_chunks):
        """Test getting context for Scene 2."""
        with app.app_context():
            context = get_chunk_context(test_book_with_chunks.book_id, 2)
            
            # Check outline section
            assert "Joe comes home" in context['outline_section']
            assert "#scene_id=2" not in context['outline_section']
            assert "After shopping, Joe returns home" in context['outline_section']
            
            # Check tags
            assert "adventure" in context['tags']
            assert "home" in context['tags']
            assert len(context['tags']) == 2
            
            # Check characters - should include those with adventure or home tags
            character_text = '\n'.join(context['characters_sections'])
            assert "Character: Joe" in character_text  # Has both tags
            assert "Character: Old Friend" in character_text  # Has adventure tag
            assert "Detective Smith" not in character_text  # No shared tags
            assert "Shopkeeper" not in character_text  # No shared tags
            
            # Check settings
            settings_text = '\n'.join(context['settings_sections'])
            assert "Joe's House" in settings_text  # Has both tags
            assert "Local Market" in settings_text  # Has adventure tag
            assert "Police Station" not in settings_text  # No shared tags
    
    def test_get_context_scene_3(self, app, test_book_with_chunks):
        """Test getting context for Scene 3."""
        with app.app_context():
            context = get_chunk_context(test_book_with_chunks.book_id, 3)
            
            # Check outline section
            assert "Joe investigates" in context['outline_section']
            assert "#scene_id=3" not in context['outline_section']
            
            # Check tags
            assert "mystery" in context['tags']
            assert "investigation" in context['tags']
            
            # Check characters
            character_text = '\n'.join(context['characters_sections'])
            assert "Character: Joe" in character_text  # Has mystery tag
            assert "Detective Smith" in character_text  # Has both tags
            assert "Old Friend" not in character_text  # No shared tags
            
            # Check settings
            settings_text = '\n'.join(context['settings_sections'])
            assert "Joe's House" in settings_text  # Has mystery tag
            assert "Police Station" in settings_text  # Has both tags
            assert "Local Market" not in settings_text  # No shared tags
    
    def test_get_context_nonexistent_scene(self, app, test_book_with_chunks):
        """Test getting context for a nonexistent scene."""
        with app.app_context():
            context = get_chunk_context(test_book_with_chunks.book_id, 99)
            
            assert context['outline_section'] == ''
            assert context['tags'] == []
            assert context['characters_sections'] == []
            assert context['settings_sections'] == []
    
    def test_get_context_nonexistent_book(self, app):
        """Test getting context for a nonexistent book."""
        with app.app_context():
            context = get_chunk_context("nonexistent-book-id", 1)
            
            assert context['outline_section'] == ''
            assert context['tags'] == []
            assert context['characters_sections'] == []
            assert context['settings_sections'] == []


class TestOutlineSectionExtraction:
    """Test outline section extraction functionality."""
    
    def test_extract_outline_section_level_2_headers(self, app):
        """Test extraction with level 2 headers."""
        outline_text = """
## Chapter 1

## Scene 1: First scene #tag1 #tag2 #scene_id=1
This is the content of scene 1.
More content here.

## Scene 2: Second scene #tag3 #scene_id=2
This is scene 2 content.
"""
        
        section, tags = _extract_outline_section_by_id(outline_text, 1)
        
        assert "Scene 1: First scene" in section
        assert "#scene_id=1" not in section
        assert "This is the content of scene 1" in section
        assert "More content here" in section
        assert "Scene 2" not in section  # Should stop at next header
        
        assert sorted(tags) == sorted(["tag1", "tag2"])
    
    def test_extract_outline_section_level_3_headers(self, app):
        """Test extraction with level 3 headers."""
        outline_text = """
## Chapter 1

### Scene 1: First scene #tag1 #scene_id=1
Content for scene 1.

### Scene 2: Second scene #tag2 #scene_id=2
Content for scene 2.
"""
        
        section, tags = _extract_outline_section_by_id(outline_text, 2)
        
        assert "Scene 2: Second scene" in section
        assert "#scene_id=2" not in section
        assert "Content for scene 2" in section
        assert "Scene 1" not in section
        
        assert sorted(tags) == sorted(["tag2"])
    
    def test_extract_outline_section_mixed_headers(self, app):
        """Test extraction with mixed level headers."""
        outline_text = """
## Chapter 1

### Scene with level 3 #tag1 #scene_id=10
Level 3 content.

## Scene with level 2 #tag2 #scene_id=20
Level 2 content.
"""
        
        # Test level 3
        section, tags = _extract_outline_section_by_id(outline_text, 10)
        assert "Scene with level 3" in section
        assert sorted(tags) == sorted(["tag1"])
        
        # Test level 2
        section, tags = _extract_outline_section_by_id(outline_text, 20)
        assert "Scene with level 2" in section
        assert sorted(tags) == sorted(["tag2"])
    
    def test_extract_outline_section_no_tags(self, app):
        """Test extraction when section has no tags."""
        outline_text = """
### Scene without tags #scene_id=1
Some content here.
"""
        
        section, tags = _extract_outline_section_by_id(outline_text, 1)
        
        assert "Scene without tags" in section
        assert tags == []


class TestSectionsByTags:
    """Test extraction of sections by tags."""
    
    def test_extract_characters_by_tags(self, app):
        """Test extracting character sections by tags."""
        characters_text = """
## Character: Alice #adventure #magic
Alice is a young wizard.

## Character: Bob #adventure #sword
Bob is a warrior.

## Character: Carol #mystery
Carol is a detective.
        """
        
        sections = _extract_sections_by_tags(characters_text, ["adventure"], "Character")
        
        assert len(sections) == 2
        section_text = '\n'.join(sections)
        assert "Alice" in section_text
        assert "Bob" in section_text
        assert "Carol" not in section_text
    
    def test_extract_settings_by_tags(self, app):
        """Test extracting settings sections by tags."""
        settings_text = """
## Settings: Castle #magic #adventure
A grand castle.

## Settings: Forest #adventure
Dark woods.

## Settings: City #modern
Urban setting.
        """
        
        sections = _extract_sections_by_tags(settings_text, ["magic"], "Settings")
        
        assert len(sections) == 1
        assert "Castle" in sections[0]
        assert "grand castle" in sections[0]
    
    def test_extract_sections_multiple_tags(self, app):
        """Test extracting sections with multiple matching tags."""
        content_text = """
### Section A #tag1 #tag2
Content A

### Section B #tag2 #tag3
Content B

### Section C #tag4
Content C
        """
        
        sections = _extract_sections_by_tags(content_text, ["tag1", "tag3"], "Section")
        
        assert len(sections) == 2
        section_text = '\n'.join(sections)
        assert "Section A" in section_text
        assert "Section B" in section_text
        assert "Section C" not in section_text


class TestListFunctions:
    """Test the list parsing functions."""
    
    def test_get_outline_sections_list(self, app, test_book_with_chunks):
        """Test getting outline sections as a list."""
        with app.app_context():
            sections = get_outline_sections_list(test_book_with_chunks.book_id)
            
            assert len(sections) == 5  # 2 chapters + 3 scenes
            
            # Check a scene
            scene1 = next(s for s in sections if s['title'] == 'Joe goes to the store')
            assert scene1['scene_id'] == 1
            assert sorted(scene1['tags']) == sorted(['adventure', 'shopping', 'scene_id'])
            assert "Joe decides he needs groceries" in scene1['content']
            
            # Check a chapter
            chapter_sections = [s for s in sections if s['scene_id'] is None]
            assert len(chapter_sections) == 2
            assert any("Chapter 1" in s['title'] for s in chapter_sections)
            assert any("Chapter 2" in s['title'] for s in chapter_sections)
    
    def test_get_characters_list(self, app, test_book_with_chunks):
        """Test getting characters as a list."""
        with app.app_context():
            characters = get_characters_list(test_book_with_chunks.book_id)
            
            assert len(characters) == 4
            
            # Check Joe
            joe = next(c for c in characters if c['name'] == 'Joe')
            assert sorted(joe['tags']) == sorted(['adventure', 'home', 'mystery'])
            assert "main protagonist" in joe['content']
            
            # Check Old Friend
            friend = next(c for c in characters if c['name'] == 'Old Friend')
            assert sorted(friend['tags']) == sorted(['adventure', 'shopping'])
    
    def test_get_settings_list(self, app, test_book_with_chunks):
        """Test getting settings as a list."""
        with app.app_context():
            settings = get_settings_list(test_book_with_chunks.book_id)
            
            assert len(settings) == 3
            
            # Check Local Market
            market = next(s for s in settings if s['name'] == 'Local Market')
            assert sorted(market['tags']) == sorted(['adventure', 'shopping'])
            assert "grocery store" in market['content']
    
    def test_list_functions_empty_book(self, app):
        """Test list functions with a book that has no chunks."""
        with app.app_context():
            # Create empty book
            book = Book(user_id="test-user", props={})
            db.session.add(book)
            db.session.commit()
            
            assert get_outline_sections_list(book.book_id) == []
            assert get_characters_list(book.book_id) == []
            assert get_settings_list(book.book_id) == []


class TestEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_empty_inputs(self, app):
        """Test functions with empty inputs."""
        section, tags = _extract_outline_section_by_id("", 1)
        assert section == ""
        assert tags == []
        
        sections = _extract_sections_by_tags("", ["tag1"], "Character")
        assert sections == []
        
        section, tags = _extract_outline_section_by_id("Some text", 0)
        assert section == ""
        assert tags == []
    
    def test_malformed_headers(self, app):
        """Test with malformed headers."""
        outline_text = """
# Single hash header #scene_id=1
This shouldn't match.

#### Four hash header #tag1 #scene_id=2
This also shouldn't match.

### Proper header #tag2 #scene_id=3
This should match.
        """
        
        # Scene 1 and 2 shouldn't be found (wrong header levels)
        section, tags = _extract_outline_section_by_id(outline_text, 1)
        assert section == ""
        
        section, tags = _extract_outline_section_by_id(outline_text, 2)
        assert section == ""
        
        # Scene 3 should be found
        section, tags = _extract_outline_section_by_id(outline_text, 3)
        assert "Proper header" in section
        assert sorted(tags) == sorted(["tag2"])
    
    def test_scene_id_variations(self, app):
        """Test different scene ID formats."""
        outline_text = """
### Scene with space #scene_id= 1
Content 1

### Scene with equals #scene_id = 2
Content 2

### Scene with no value #scene_id=
Content 3
        """
        
        # All of these are technically malformed and shouldn't be found by the current regex
        section, tags = _extract_outline_section_by_id(outline_text, 1)
        assert section == ""
        
        section, tags = _extract_outline_section_by_id(outline_text, 2)
        assert section == ""
        
        section, tags = _extract_outline_section_by_id(outline_text, 3)
        assert section == ""
