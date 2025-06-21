"""
Flask API routes for LLM management.

This module provides Flask Blueprint routes for LLM selection and configuration.
"""
import logging
from typing import Dict, Any
from flask import Blueprint, request, jsonify, g

from backend.models import db, Book
from sqlalchemy.orm.attributes import flag_modified
from .models import LLMDefaults, LLMGroup
from .catalog import get_all_llms, get_llms_by_group, get_llm_by_id

logger = logging.getLogger(__name__)

# Create Blueprint for LLM picker API
llmpicker_api = Blueprint('llmpicker_api', __name__)


@llmpicker_api.route('/llms', methods=['GET'])
def list_llms():
    """
    List all available LLMs, optionally filtered by group.
    
    Args:
        group: Optional group to filter by
        
    Returns:
        List of LLM information objects
    """
    group = request.args.get('group')
    
    if group:
        llms = get_llms_by_group(group)
    else:
        llms = get_all_llms()

    # Use model_dump() to get dicts, then jsonify the whole payload
    llm_list = [llm.model_dump() for llm in llms]
    return jsonify({"llms": llm_list})


@llmpicker_api.route('/llms/books/<book_id>/defaults', methods=['GET'])
def get_book_llm_defaults(book_id):
    """
    Get LLM defaults for a specific book.
    
    Args:
        book_id: The book ID
        
    Returns:
        LLM defaults for the book or empty object if none set
    """
    book = Book.query.filter_by(book_id=book_id).first()
    if not book:
        return jsonify({'error': 'Book not found'}), 404
    
    # For test cases, return empty dict if no defaults are set
    if not book.props or "llm_defaults" not in book.props or not book.props["llm_defaults"]:
        return jsonify({})
    
    # Copy defaults but exclude None values
    result = {}
    for key, value in book.props["llm_defaults"].items():
        if value is not None:
            result[key] = value
            
    return jsonify(result)


@llmpicker_api.route('/llms/books/<book_id>/defaults', methods=['PUT'])
def set_book_llm_defaults(book_id):
    """
    Set the LLM defaults for a specific book.
    
    This will overwrite all existing group defaults for the book, but preserve
    the override setting.
        
    Args:
        book_id: The book ID
        
    Returns:
        Updated LLM defaults for the book
    """
    book = Book.query.filter_by(book_id=book_id).first()
    if not book:
        return jsonify({'error': 'Book not found'}), 404

    new_defaults = request.get_json()
    if not isinstance(new_defaults, dict):
        return jsonify({'error': 'Request body must be a JSON object of defaults'}), 400

    valid_groups = {group.value for group in LLMGroup} - {'override'}

    # Validate all incoming defaults before applying any
    for group, llm_id in new_defaults.items():
        if group not in valid_groups:
            return jsonify({'error': f"Invalid group provided: {group}"}), 400
        
        # A null or empty llm_id means we are unsetting the default
        if llm_id:
            llm = get_llm_by_id(llm_id)
            if not llm:
                return jsonify({'error': f'LLM with ID {llm_id} not found'}), 404
            if group not in llm.groups and "all" not in llm.groups:
                return jsonify({'error': f'LLM {llm.id} is not valid for group {group}'}), 400

    if not book.props:
        book.props = {}
    
    if "llm_defaults" not in book.props:
        book.props["llm_defaults"] = {}

    # Preserve existing override setting
    existing_override = book.props["llm_defaults"].get("override")
    
    # Set the new defaults from the request, filtering out any null/empty values
    book.props["llm_defaults"] = {k: v for k, v in new_defaults.items() if v}
    
    # Restore override if it existed
    if existing_override:
        book.props["llm_defaults"]["override"] = existing_override
    
    try:
        flag_modified(book, "props")
        db.session.commit()
        return jsonify({
            'status': 'success', 
            'message': f"Updated LLM defaults",
            'defaults': book.props.get("llm_defaults")
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error setting LLM defaults: {str(e)}")
        return jsonify({'error': 'Error updating book LLM defaults'}), 500


@llmpicker_api.route('/llms/books/<book_id>/override', methods=['GET'])
def get_book_llm_override(book_id):
    """
    Get the LLM override for a specific book if set.
    
    Args:
        book_id: The book ID
        
    Returns:
        LLM override info or None if not set
    """
    book = Book.query.filter_by(book_id=book_id).first()
    if not book:
        return jsonify({'error': 'Book not found'}), 404
    
    # Get the override from book props
    props = book.props or {}
    llm_defaults = props.get("llm_defaults", {})
    override_id = llm_defaults.get("override")
    
    result = {'override': override_id}
    
    # Add LLM info if override is set
    if override_id is not None:
        llm = get_llm_by_id(override_id)
        if llm:
            result['llm'] = llm.model_dump()
        else:
            result['llm'] = None
            result['warning'] = f'LLM with ID {override_id} not found in catalog'
    
    return jsonify(result)


@llmpicker_api.route('/llms/books/<book_id>/override', methods=['PUT'])
def set_book_llm_override(book_id):
    """
    Set the LLM override for a book.
    
    Args:
        book_id: The book ID
        
    Returns:
        Status message
    """
    # Get request data
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body required'}), 400
    
    llm_id = data.get('llm_id')
    if not llm_id:
        return jsonify({'error': 'llm_id is required'}), 400
    
    # Validate LLM ID
    llm = get_llm_by_id(llm_id)
    if not llm:
        return jsonify({'error': f'LLM not found: {llm_id}'}), 404
    
    # Verify the LLM is valid for override
    if "override" not in llm.groups and "all" not in llm.groups:
        return jsonify({'error': f'LLM {llm.id} is not valid for override use'}), 400
    
    book = Book.query.filter_by(book_id=book_id).first()
    if not book:
        return jsonify({'error': 'Book not found'}), 404
    
    # Update book props
    if not book.props:
        book.props = {}
    
    if "llm_defaults" not in book.props:
        book.props["llm_defaults"] = {}
    
    book.props["llm_defaults"]["override"] = llm_id
    
    try:
        flag_modified(book, "props")
        db.session.commit()
        return jsonify({'status': 'success', 'message': f'Override LLM set to {llm_id}'})
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error setting override LLM: {str(e)}")
        return jsonify({'error': 'Error updating override LLM'}), 500


@llmpicker_api.route('/llms/books/<book_id>/override', methods=['DELETE'])
def clear_book_llm_override(book_id):
    """
    Clear the LLM override for a book.
    
    Args:
        book_id: The book ID
        
    Returns:
        Status message
    """
    book = Book.query.filter_by(book_id=book_id).first()
    if not book:
        return jsonify({'error': 'Book not found'}), 404
    
    # Initialize props if needed
    if not book.props:
        book.props = {}
    
    if "llm_defaults" not in book.props:
        book.props["llm_defaults"] = {}
    
    # Test expects override to be explicitly set to None, not removed
    book.props["llm_defaults"]["override"] = None
    
    # Force flush to ensure changes are persisted
    db.session.flush()
    
    try:
        flag_modified(book, "props")
        db.session.commit()
        return jsonify({'status': 'success', 'message': 'Override LLM cleared'})
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error clearing override LLM: {str(e)}")
        return jsonify({'error': 'Error clearing override LLM'}), 500
