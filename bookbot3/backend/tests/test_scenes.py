import pytest
import re
from backend.models import db, Book, Chunk, Job
from backend.bot_manager import BotManager
from backend.jobs.create_foundation import run_create_foundation_job

@pytest.fixture
def scene_test_data():
    """Provides a sample outline with various scene definitions."""
    return """
## Chapter 1: The Discovery

### Scene: The Signal [[Scene 1]]
An old satellite dish picks up a strange signal.

### Scene: The Team Assembles [[Scene 2]]
Dr. Aris Thorne gathers his team of experts.

## Chapter 2: The Journey

### Scene: Lift-off [[Scene 3]]
The team launches into space.

### Scene: A Close Call [[Scene 4]]
An unexpected solar flare tests their ship's defenses.

### Scene: Another Scene Title [[Scene 6]]
This is just another scene.

## Chapter 3: Arrival

This chapter has no scenes yet.
"""

class TestSceneHandling:
    """Tests for scene parsing and chunk creation logic."""

    def test_add_scene_ids_parsing(self, scene_test_data):
        """Test that add_scene_ids correctly parses titles, IDs, and chapters."""
        bot_manager = BotManager()
        cleaned_outline, scene_info = bot_manager.add_scene_ids(scene_test_data)

        assert len(scene_info) == 5

        # Test scene 1
        assert scene_info[0]['outline_section_id'] == 1
        assert scene_info[0]['scene_title'] == "The Signal"
        assert scene_info[0]['chapter'] == 1

        # Test scene 2
        assert scene_info[1]['outline_section_id'] == 2
        assert scene_info[1]['scene_title'] == "The Team Assembles"
        assert scene_info[1]['chapter'] == 1

        # Test scene 3 (new chapter)
        assert scene_info[2]['outline_section_id'] == 3
        assert scene_info[2]['scene_title'] == "Lift-off"
        assert scene_info[2]['chapter'] == 2

        # Test scene 4
        assert scene_info[3]['outline_section_id'] == 4
        assert scene_info[3]['scene_title'] == "A Close Call"
        assert scene_info[3]['chapter'] == 2

        # Test scene 6 (scene 5 is skipped)
        assert scene_info[4]['outline_section_id'] == 6
        assert scene_info[4]['scene_title'] == "Another Scene Title"
        assert scene_info[4]['chapter'] == 2

    def test_add_scene_ids_idempotency_and_format(self, scene_test_data):
        """Test that add_scene_ids correctly preserves existing IDs and adds new ones."""
        bot_manager = BotManager()
        # Run once on data that already has IDs. There are 5 scenes.
        processed_outline, info1 = bot_manager.add_scene_ids(scene_test_data)
        assert len(info1) == 5
        assert processed_outline.count('[[Scene') == 5

        # Run again on the processed output to test idempotency
        reprocessed_outline, info2 = bot_manager.add_scene_ids(processed_outline)
        assert reprocessed_outline == processed_outline
        assert info1 == info2

        # Test on an outline without any IDs
        outline_no_ids = re.sub(r'\s*\[\[Scene\s+\d+\]\]', '', scene_test_data)
        new_outline, info3 = bot_manager.add_scene_ids(outline_no_ids)
        
        # Should find 5 scenes and add IDs 1 through 5
        assert len(info3) == 5
        assert new_outline.count('[[Scene') == 5
        assert '[[Scene 1]]' in new_outline
        assert '[[Scene 5]]' in new_outline
        
        # Check that the new IDs are linear
        assert info3[0]['outline_section_id'] == 1
        assert info3[4]['outline_section_id'] == 5

    def test_create_foundation_with_scenes(self, app, monkeypatch):
        """Test the end-to-end CreateFoundationJob creates correct scene chunks."""
        from unittest.mock import MagicMock

        outline_text = """## Chapter 1: Test Chapter\n\n### Scene: A Test Scene [[Scene 1]]\nDescription here.\n\n### Scene: Another Test Scene [[Scene 2]]\nAnother description."""

        def mock_get_llm_call(self, task_id, book_props, user_props, template_vars, api_key="fake-key", log_callback=None):
            mock_llm = MagicMock()
            mock_llm.execute.return_value = True
            
            if task_id == 'create_outline':
                mock_llm.output_text = outline_text
                mock_llm.cost = 0.001
            elif task_id == 'create_characters':
                mock_llm.output_text = "Characters..."
                mock_llm.cost = 0.001
            elif task_id == 'create_settings':
                mock_llm.output_text = "Settings..."
                mock_llm.cost = 0.001
            elif task_id == 'tag_content':
                mock_llm.output_text = template_vars['content']
                mock_llm.cost = 0.001
            
            return mock_llm
            
        monkeypatch.setattr('backend.bot_manager.BotManager.get_llm_call', mock_get_llm_call)

        with app.app_context():
            book = Book(user_id="test-user-scenes", props={'title': 'Scene Test Book'})
            db.session.add(book)
            db.session.commit()

            job_props = {"brief": "A test brief.", "style": "A test style."}

            # Run the job
            success = run_create_foundation_job(job_id="test-job", book_id=book.book_id, props=job_props, log_callback=lambda x: None)

            assert success is True

            # Verify chunks
            chunks = Chunk.query.filter_by(book_id=book.book_id).order_by(Chunk.order).all()
            scene_chunks = [c for c in chunks if c.type == 'scene']

            assert len(scene_chunks) == 2

            # Check first scene chunk
            assert scene_chunks[0].props['outline_section_id'] == 1
            assert scene_chunks[0].props['scene_title'] == "A Test Scene"
            assert scene_chunks[0].chapter == 1
            assert scene_chunks[0].text == ""

            # Check second scene chunk
            assert scene_chunks[1].props['outline_section_id'] == 2
            assert scene_chunks[1].props['scene_title'] == "Another Test Scene"
            assert scene_chunks[1].chapter == 1


