import pytest
from unittest.mock import patch, MagicMock
from backend.models import db, Book, Chunk
from backend.jobs.create_foundation import run_create_foundation_job

@pytest.mark.parametrize(
    "outline_content",
    [
        "Chapter 1\n- Scene 1\n- Scene 2",
        "Part 1\n\nChapter 1\n\n- Introduction\n- Climax\n- Resolution"
    ]
)
def test_run_create_foundation_job_preserves_newlines(app, outline_content):
    with app.app_context():
        book = Book(user_id="test_user", props={'title': 'Test Book'})
        db.session.add(book)
        db.session.commit()

        mock_bot_manager = MagicMock()

        outline_with_ids = f"{outline_content}\n\n[[Scene 1]]"

        # Mocks for different LLM calls
        mock_create_outline = MagicMock(execute=MagicMock(return_value=True), output_text=outline_content, cost=0.001)
        mock_tag_content = MagicMock(execute=MagicMock(return_value=True), output_text=outline_with_ids, cost=0.001)
        mock_generate_chars = MagicMock(execute=MagicMock(return_value=True), output_text="Some characters", cost=0.001)
        mock_tag_chars = MagicMock(execute=MagicMock(return_value=True), output_text="Tagged characters", cost=0.001)
        mock_generate_settings = MagicMock(execute=MagicMock(return_value=True), output_text="Some settings", cost=0.001)
        mock_tag_settings = MagicMock(execute=MagicMock(return_value=True), output_text="Tagged settings", cost=0.001)

        def get_llm_call_side_effect(task_id, book_props, user_props, template_vars, log_callback=None):
            if task_id == 'create_outline':
                return mock_create_outline
            elif task_id == 'create_characters':
                return mock_generate_chars
            elif task_id == 'create_settings':
                return mock_generate_settings
            elif task_id == 'tag_content':
                content_type = template_vars['content_type']
                if content_type == 'outline':
                    assert '[[Scene 1]]' in template_vars['content']
                    return mock_tag_content
                elif content_type == 'characters':
                    return mock_tag_chars
                elif content_type == 'settings':
                    return mock_tag_settings
            
            # Fallback for any other calls
            return MagicMock(execute=MagicMock(return_value=True), output_text="Default mock", cost=0.0)

        mock_bot_manager.get_llm_call.side_effect = get_llm_call_side_effect
        mock_bot_manager.add_scene_ids.return_value = (outline_with_ids, [{'outline_section_id': 1, 'chapter': 1, 'scene_title': 'A Scene'}])
        mock_bot_manager.remove_scene_ids.return_value = outline_content

        with patch('backend.jobs.create_foundation.get_bot_manager', return_value=mock_bot_manager):
            run_create_foundation_job(
                job_id="test_job",
                book_id=book.book_id,
                props={'brief': 'Test Brief', 'style': 'Test Style'},
                log_callback=lambda msg: None
            )

        outline_chunk = Chunk.query.filter_by(book_id=book.book_id, type="outline").first()
        assert outline_chunk is not None
        assert "[[Scene 1]]" in outline_chunk.text
        # The crucial check: newlines should be preserved
        assert "\n" in outline_chunk.text
        