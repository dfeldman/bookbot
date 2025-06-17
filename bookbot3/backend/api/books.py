"""
Book API endpoints for BookBot.
"""

from flask import Blueprint, request, jsonify, g
from typing import Dict, Any, Optional

from backend.models import db, Book, Chunk, OutputFile
from backend.auth import require_auth, require_read_access, require_edit_access, get_current_user_id
from backend.jobs import create_job

book_api = Blueprint('book_api', __name__)


@book_api.route('/books', methods=['GET'])
@require_auth
def list_books():
    """List all books for the current user."""
    user_id = g.current_user_id
    books = Book.query.filter_by(user_id=user_id).all()
    
    return jsonify({
        'books': [book.to_dict(include_stats=True) for book in books]
    })


@book_api.route('/books', methods=['POST'])
@require_auth
def create_book():
    """Create a new book."""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body required'}), 400
    
    user_id = g.current_user_id
    props = data.get('props', {})
    
    book = Book(
        user_id=user_id,
        props=props
    )
    
    db.session.add(book)
    db.session.commit()
    
    return jsonify(book.to_dict(include_stats=True)), 201


@book_api.route('/books/<book_id>', methods=['GET'])
@require_read_access()
def get_book(book_id: str):
    """Get a specific book."""
    book = db.session.get(Book, book_id)
    if not book:
        return jsonify({'error': 'Book not found'}), 404
    
    return jsonify(book.to_dict(include_stats=True))


@book_api.route('/books/<book_id>', methods=['PUT'])
@require_edit_access()
def update_book(book_id: str):
    """Update a book."""
    book = db.session.get(Book, book_id)
    if not book:
        return jsonify({'error': 'Book not found'}), 404
    
    if book.is_locked:
        return jsonify({'error': 'Book is locked by a running job'}), 423
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body required'}), 400
    
    if 'props' in data:
        book.props = data['props']
    
    db.session.commit()
    
    return jsonify(book.to_dict(include_stats=True))


@book_api.route('/books/<book_id>', methods=['DELETE'])
@require_edit_access()
def delete_book(book_id: str):
    """Delete a book and all its associated data."""
    book = db.session.get(Book, book_id)
    if not book:
        return jsonify({'error': 'Book not found'}), 404
    
    if book.is_locked:
        return jsonify({'error': 'Book is locked by a running job'}), 423
    
    # Delete the book (cascading will handle chunks, jobs, etc.)
    db.session.delete(book)
    db.session.commit()
    
    return jsonify({'message': 'Book deleted successfully'})


@book_api.route('/books/<book_id>/status', methods=['GET'])
@require_read_access()
def get_book_status(book_id: str):
    """Get comprehensive status information for a book."""
    from backend.llm import get_api_token_status
    
    book = db.session.get(Book, book_id)
    if not book:
        return jsonify({'error': 'Book not found'}), 404
    
    # Get latest chunks for word count
    latest_chunks = Chunk.query.filter_by(
        book_id=book_id,
        is_latest=True,
        is_deleted=False
    ).all()
    
    chunk_count = len(latest_chunks)
    total_word_count = sum(chunk.word_count or 0 for chunk in latest_chunks)
    
    # Get most recent job
    latest_job = Job.query.filter_by(book_id=book_id).order_by(Job.created_at.desc()).first()
    
    # Get API token balance (if available)
    api_token_balance = None
    api_key = book.props.get('api_key')
    if api_key:
        token_status = get_api_token_status(api_key)
        if token_status.get('valid'):
            api_token_balance = token_status.get('balance')
    
    return jsonify({
        'book_id': book_id,
        'chunk_count': chunk_count,
        'word_count': total_word_count,
        'latest_job': latest_job.to_dict() if latest_job else None,
        'api_token_balance': api_token_balance,
        'is_locked': book.is_locked
    })
