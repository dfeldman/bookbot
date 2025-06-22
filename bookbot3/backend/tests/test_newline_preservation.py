import pytest
from backend.models import db, Book, Chunk, User

def test_db_preserves_newlines_in_chunk(app):
    """
    Tests if the database layer (SQLAlchemy + SQLite) correctly
    stores and retrieves multiline strings.
    """
    multiline_text = "This is line one.\nThis is line two.\n\nThis is line four."

    with app.app_context():
        # Create a book for the test
        book = Book(
            book_id='newline-test-book',
            user_id='test-user-123',  # Assumes the app fixture creates this user
            props={'title': 'Newline Test Book'}
        )
        db.session.add(book)

        # Create a chunk directly
        chunk = Chunk(
            book_id=book.book_id,
            type='brief',
            text=multiline_text,
            is_latest=True
        )
        db.session.add(chunk)
        db.session.commit()

        # Retrieve the chunk using the modern, recommended API
        retrieved_chunk = db.session.get(Chunk, chunk.id)

        # Assert that newlines are preserved
        assert retrieved_chunk is not None
        assert retrieved_chunk.text == multiline_text
        assert "\n" in retrieved_chunk.text
