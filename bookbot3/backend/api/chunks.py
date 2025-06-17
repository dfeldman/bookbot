"""
Chunk API endpoints for BookBot.
"""

from flask import Blueprint, request, jsonify, g
from typing import Dict, Any, Optional, List

from backend.models import db, Book, Chunk
from backend.auth import require_auth, require_read_access, require_edit_access
from backend.jobs.job_utils import get_chunk_context

chunk_api = Blueprint('chunk_api', __name__)


@chunk_api.route('/books/<book_id>/chunks', methods=['GET'])
@require_read_access()
def list_chunks(book_id: str):
    """List chunks for a book."""
    # Parse query parameters
    include_text = request.args.get('include_text', 'false').lower() == 'true'
    include_deleted = request.args.get('include_deleted', 'false').lower() == 'true'
    chapter = request.args.get('chapter', type=int)
    
    # Build query
    query = Chunk.query.filter_by(book_id=book_id, is_latest=True)
    
    if not include_deleted:
        query = query.filter_by(is_deleted=False)
    
    if chapter is not None:
        query = query.filter_by(chapter=chapter)
    
    chunks = query.order_by(Chunk.order, Chunk.created_at).all()
    
    return jsonify({
        'chunks': [chunk.to_dict(include_text=include_text) for chunk in chunks]
    })


@chunk_api.route('/books/<book_id>/chunks', methods=['POST'])
@require_edit_access()
def create_chunk(book_id: str):
    """Create a new chunk."""
    book = db.session.get(Book, book_id)
    if not book:
        return jsonify({'error': 'Book not found'}), 404
    
    if book.is_locked:
        return jsonify({'error': 'Book is locked by a running job'}), 423
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body required'}), 400
    
    # Calculate word count if text is provided
    text = data.get('text', '')
    word_count = Chunk.count_words(text)
    
    chunk = Chunk(
        book_id=book_id,
        props=data.get('props', {}),
        text=text,
        type=data.get('type'),
        order=data.get('order'),
        chapter=data.get('chapter'),
        word_count=word_count,
        version=1,
        is_latest=True
    )
    
    db.session.add(chunk)
    db.session.commit()
    
    return jsonify(chunk.to_dict(include_text=True)), 201


@chunk_api.route('/chunks/<chunk_id>', methods=['GET'])
def get_chunk(chunk_id: str):
    """Get a specific chunk by chunk_id (any version)."""
    version = request.args.get('version', type=int)
    
    query = Chunk.query.filter_by(chunk_id=chunk_id)
    
    if version is not None:
        query = query.filter_by(version=version)
    else:
        query = query.filter_by(is_latest=True)
    
    chunk = query.first()
    if not chunk:
        return jsonify({'error': 'Chunk not found'}), 404
    
    # Check read access to the book
    book = db.session.get(Book, chunk.book_id)
    if not book:
        return jsonify({'error': 'Book not found'}), 404
    
    # TODO: Add proper authorization check
    
    return jsonify(chunk.to_dict(include_text=True))


@chunk_api.route('/chunks/<chunk_id>', methods=['PUT'])
def update_chunk(chunk_id: str):
    """Update a chunk (creates a new version)."""
    # Get the latest version of the chunk
    current_chunk = Chunk.query.filter_by(
        chunk_id=chunk_id,
        is_latest=True
    ).first()
    
    if not current_chunk:
        return jsonify({'error': 'Chunk not found'}), 404
    
    # Check edit access to the book
    book = db.session.get(Book, current_chunk.book_id)
    if not book:
        return jsonify({'error': 'Book not found'}), 404
    
    # TODO: Add proper authorization check
    
    if book.is_locked or current_chunk.is_locked:
        return jsonify({'error': 'Chunk or book is locked by a running job'}), 423
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body required'}), 400
    
    # Calculate word count if text is provided
    text = data.get('text', current_chunk.text)
    word_count = Chunk.count_words(text)
    
    # Create new version
    new_chunk = Chunk(
        book_id=current_chunk.book_id,
        chunk_id=current_chunk.chunk_id,
        version=current_chunk.version + 1,
        is_latest=True,
        props=data.get('props', current_chunk.props),
        text=text,
        type=data.get('type', current_chunk.type),
        order=data.get('order', current_chunk.order),
        chapter=data.get('chapter', current_chunk.chapter),
        word_count=word_count
    )
    
    # Mark old version as not latest
    current_chunk.is_latest = False
    
    db.session.add(new_chunk)
    db.session.commit()
    
    return jsonify(new_chunk.to_dict(include_text=True))


@chunk_api.route('/chunks/<chunk_id>', methods=['DELETE'])
def delete_chunk(chunk_id: str):
    """Soft delete a chunk (all versions)."""
    chunks = Chunk.query.filter_by(chunk_id=chunk_id).all()
    
    if not chunks:
        return jsonify({'error': 'Chunk not found'}), 404
    
    # Check edit access to the book
    book = db.session.get(Book, chunks[0].book_id)
    if not book:
        return jsonify({'error': 'Book not found'}), 404
    
    # TODO: Add proper authorization check
    
    if book.is_locked:
        return jsonify({'error': 'Book is locked by a running job'}), 423
    
    # Check if any version is locked
    for chunk in chunks:
        if chunk.is_locked:
            return jsonify({'error': 'Chunk is locked by a running job'}), 423
    
    # Soft delete all versions
    for chunk in chunks:
        chunk.is_deleted = True
    
    db.session.commit()
    
    return jsonify({'message': 'Chunk deleted successfully'})


@chunk_api.route('/chunks/<chunk_id>/versions', methods=['GET'])
def list_chunk_versions(chunk_id: str):
    """List all versions of a chunk."""
    chunks = Chunk.query.filter_by(chunk_id=chunk_id).order_by(Chunk.version.desc()).all()
    
    if not chunks:
        return jsonify({'error': 'Chunk not found'}), 404
    
    # Check read access to the book
    book = db.session.get(Book, chunks[0].book_id)
    if not book:
        return jsonify({'error': 'Book not found'}), 404
    
    # TODO: Add proper authorization check
    
    return jsonify({
        'versions': [chunk.to_dict(include_text=False) for chunk in chunks]
    })


@chunk_api.route('/chunks/<chunk_id>/cleanup-old-versions', methods=['POST'])
def cleanup_old_versions(chunk_id: str):
    """Delete old versions of a chunk, keeping the latest N versions."""
    data = request.get_json() or {}
    keep_versions = data.get('keep_versions', 3)
    
    chunks = Chunk.query.filter_by(chunk_id=chunk_id).order_by(Chunk.version.desc()).all()
    
    if not chunks:
        return jsonify({'error': 'Chunk not found'}), 404
    
    # Check edit access to the book
    book = db.session.get(Book, chunks[0].book_id)
    if not book:
        return jsonify({'error': 'Book not found'}), 404
    
    # TODO: Add proper authorization check
    
    if len(chunks) <= keep_versions:
        return jsonify({'message': 'No old versions to clean up', 'deleted_count': 0})
    
    # Delete old versions
    old_chunks = chunks[keep_versions:]
    deleted_count = 0
    
    for chunk in old_chunks:
        if not chunk.is_locked:
            db.session.delete(chunk)
            deleted_count += 1
    
    db.session.commit()
    
    return jsonify({
        'message': f'Deleted {deleted_count} old versions',
        'deleted_count': deleted_count
    })


@chunk_api.route('/books/<book_id>/chunks/cleanup-deleted', methods=['POST'])
@require_edit_access()
def cleanup_deleted_chunks(book_id: str):
    """Permanently delete soft-deleted chunks."""
    deleted_chunks = Chunk.query.filter_by(book_id=book_id, is_deleted=True).all()
    
    deleted_count = 0
    for chunk in deleted_chunks:
        if not chunk.is_locked:
            db.session.delete(chunk)
            deleted_count += 1
    
    db.session.commit()
    
    return jsonify({
        'message': f'Permanently deleted {deleted_count} chunks',
        'deleted_count': deleted_count
    })


@chunk_api.route('/books/<book_id>/chunks/<chunk_id>/context', methods=['GET'])
@require_read_access()
def get_chunk_context_api(book_id: str, chunk_id: str):
    """Get relevant context for a chunk (outline, characters, settings)."""
    chunk = Chunk.query.filter_by(
        chunk_id=chunk_id,
        book_id=book_id,
        is_latest=True,
        is_deleted=False
    ).first()
    
    if not chunk:
        return jsonify({'error': 'Chunk not found'}), 404
    
    # Only provide context for scene chunks with a scene_id
    if chunk.type != 'scene' or not chunk.props.get('scene_id'):
        return jsonify({
            'outline_section': '',
            'characters_sections': [],
            'settings_sections': [],
            'tags': [],
            'available': False
        })
    
    try:
        context = get_chunk_context(book_id, chunk.props['scene_id'])
        context['available'] = True
        return jsonify(context)
    except Exception as e:
        return jsonify({
            'error': f'Failed to get context: {str(e)}',
            'available': False
        }), 500
