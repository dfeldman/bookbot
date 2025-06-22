import unittest
from unittest.mock import patch, MagicMock

from backend.models import Book, Chunk
from backend.jobs.template_resolver import build_placeholder_values

class TestTemplateResolver(unittest.TestCase):

    @patch('backend.jobs.template_resolver.get_chunk_context')
    @patch('backend.jobs.template_resolver._get_next_chunk')
    @patch('backend.jobs.template_resolver._get_previous_chunk')
    def test_build_placeholder_values_all_present(
        self, mock_get_previous, mock_get_next, mock_get_context
    ):
        # Arrange
        book = Book(book_id='book1', props={'brief': 'A test brief.', 'style_guide': 'Test style.'})
        
        prev_chunk = Chunk(chunk_id='prev1', text='Previous scene text.')
        current_chunk = Chunk(
            chunk_id='curr1',
            text='Current scene text.',
            props={'outline_section_id': 1, 'review_text': 'This is a review from props.'}
        )
        next_chunk = Chunk(chunk_id='next1', text='Next scene text.')

        # Configure mocks
        mock_get_previous.return_value = prev_chunk
        mock_get_next.return_value = next_chunk
        mock_get_context.return_value = {
            'outline_section': 'Test Outline Section',
            'characters_sections': ['Character 1', 'Character 2'],
            'settings_sections': ['Setting 1']
        }

        # Act
        placeholders = build_placeholder_values(current_chunk, book)

        # Assert
        self.assertEqual(placeholders['PreviousChunk'], 'Previous scene text.')
        self.assertEqual(placeholders['NextChunk'], 'Next scene text.')
        self.assertEqual(placeholders['CurrentVersion'], 'Current scene text.')
        self.assertEqual(placeholders['Review'], 'This is a review from props.')
        self.assertEqual(placeholders['Brief'], 'A test brief.')
        self.assertEqual(placeholders['Style'], 'Test style.')
        self.assertEqual(placeholders['OutlineSection'], 'Test Outline Section')
        self.assertEqual(placeholders['SettingsSections'], 'Setting 1')
        self.assertEqual(placeholders['CharactersSections'], 'Character 1\n\nCharacter 2')
        
        mock_get_previous.assert_called_once_with(current_chunk, book)
        mock_get_next.assert_called_once_with(current_chunk, book)
        mock_get_context.assert_called_once_with(book.id, 1)

    @patch('backend.jobs.template_resolver.get_chunk_context')
    @patch('backend.jobs.template_resolver._get_next_chunk')
    @patch('backend.jobs.template_resolver._get_previous_chunk')
    def test_build_placeholder_values_edges_and_missing(
        self, mock_get_previous, mock_get_next, mock_get_context
    ):
        # Arrange
        book = Book(book_id='book1', props={})
        # Chunk with no props (so no outline_section_id or review_text)
        current_chunk = Chunk(chunk_id='curr1', text='')

        # Configure mocks for missing data
        mock_get_previous.return_value = None
        mock_get_next.return_value = None

        # Act
        placeholders = build_placeholder_values(current_chunk, book)

        # Assert
        self.assertEqual(placeholders['PreviousChunk'], '')
        self.assertEqual(placeholders['NextChunk'], '')
        self.assertEqual(placeholders['CurrentVersion'], '')
        self.assertEqual(placeholders['Review'], '')
        self.assertEqual(placeholders['Brief'], '')
        self.assertEqual(placeholders['Style'], '')
        self.assertEqual(placeholders['OutlineSection'], '')
        self.assertEqual(placeholders['SettingsSections'], '')
        self.assertEqual(placeholders['CharactersSections'], '')

        # Assert that get_chunk_context was not called because there was no scene_id
        mock_get_context.assert_not_called()
