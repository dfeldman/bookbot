"""
This module handles the resolution of template variables for prompts.
"""

from backend.models import Chunk, Book, db
from backend.jobs.job_utils import get_chunk_context
from typing import Optional

def _get_previous_chunk(chunk: Chunk, book: Book) -> Optional[Chunk]:
    """Helper to get the previous chunk based on order."""
    if chunk.order is None:
        return None
    return db.session.query(Chunk).filter(
        Chunk.book_id == book.id,
        Chunk.order < chunk.order,
        Chunk.is_deleted == False,
        Chunk.type == 'scene' # Only consider scene chunks for sequence
    ).order_by(Chunk.order.desc()).first()

def _get_next_chunk(chunk: Chunk, book: Book) -> Optional[Chunk]:
    """Helper to get the next chunk based on order."""
    if chunk.order is None:
        return None
    return db.session.query(Chunk).filter(
        Chunk.book_id == book.id,
        Chunk.order > chunk.order,
        Chunk.is_deleted == False,
        Chunk.type == 'scene' # Only consider scene chunks for sequence
    ).order_by(Chunk.order.asc()).first()

def build_placeholder_values(chunk: Chunk, book: Book) -> dict:
    """
    Builds a dictionary of placeholder values for template resolution.

    Args:
        chunk: The current chunk being processed.
        book: The book containing the chunk.

    Returns:
        A dictionary of placeholder values.
    """
    placeholder_values = {}

    # Previous and Next Chunks
    previous_chunk = _get_previous_chunk(chunk, book)
    placeholder_values['PreviousChunk'] = previous_chunk.text if previous_chunk else ''

    next_chunk = _get_next_chunk(chunk, book)
    placeholder_values['NextChunk'] = next_chunk.text if next_chunk else ''

    # Current Version
    placeholder_values['CurrentVersion'] = chunk.text or ''

    # Review (from props)
    chunk_props = chunk.props or {}
    placeholder_values['Review'] = chunk_props.get('review_text', '')

    # Book-level properties
    book_props = book.props or {}
    placeholder_values['Brief'] = book_props.get('brief', '')
    placeholder_values['Style'] = book_props.get('style_guide', '')

    # Outline, Characters, and Settings Sections from job_utils
    outline_section_id = chunk_props.get('outline_section_id')
    if outline_section_id:
        context = get_chunk_context(book.id, outline_section_id)
        if context:
            placeholder_values['OutlineSection'] = context.get('outline_section', '')
            placeholder_values['CharactersSections'] = "\n\n".join(context.get('characters_sections', []))
            placeholder_values['SettingsSections'] = "\n\n".join(context.get('settings_sections', []))
    else:
        placeholder_values['OutlineSection'] = ''
        placeholder_values['CharactersSections'] = ''
        placeholder_values['SettingsSections'] = ''

    return placeholder_values
