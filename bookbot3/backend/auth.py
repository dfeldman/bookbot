"""
Authentication and authorization module for BookBot.

This module provides decorators and functions for handling user authentication
and authorization. Currently returns True for all operations but provides
infrastructure for future Google OAuth integration.
"""

from functools import wraps
from typing import Optional, Callable, Any
from flask import request, jsonify, g


def get_current_user_id() -> Optional[str]:
    """
    Get the current user ID from the request.
    
    In the future, this will extract the user ID from the JWT token
    or session. For now, it returns a default user ID.
    
    Returns:
        str: The current user ID, or None if not authenticated
    """
    # TODO: Implement actual authentication
    # For now, return a default user ID
    return "default-user-123"


def is_authorized_to_read(book_id: str, user_id: Optional[str] = None) -> bool:
    """
    Check if the user is authorized to read the specified book.
    
    Args:
        book_id: The ID of the book to check
        user_id: The user ID (optional, will use current user if not provided)
    
    Returns:
        bool: True if authorized, False otherwise
    """
    # TODO: Implement actual authorization logic
    # For now, always return True
    return True


def is_authorized_to_edit(book_id: str, user_id: Optional[str] = None) -> bool:
    """
    Check if the user is authorized to edit the specified book.
    
    Args:
        book_id: The ID of the book to check
        user_id: The user ID (optional, will use current user if not provided)
    
    Returns:
        bool: True if authorized, False otherwise
    """
    # TODO: Implement actual authorization logic
    # For now, always return True
    return True


def require_auth(f: Callable) -> Callable:
    """
    Decorator to require authentication for an endpoint.
    
    Args:
        f: The function to decorate
    
    Returns:
        Callable: The decorated function
    """
    @wraps(f)
    def decorated_function(*args, **kwargs) -> Any:
        user_id = get_current_user_id()
        if not user_id:
            return jsonify({'error': 'Authentication required'}), 401
        
        g.current_user_id = user_id
        return f(*args, **kwargs)
    
    return decorated_function


def require_read_access(book_id_param: str = 'book_id') -> Callable:
    """
    Decorator to require read access to a book.
    
    Args:
        book_id_param: The name of the parameter containing the book ID
    
    Returns:
        Callable: The decorator function
    """
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args, **kwargs) -> Any:
            user_id = get_current_user_id()
            if not user_id:
                return jsonify({'error': 'Authentication required'}), 401
            
            # Get book_id from request parameters
            book_id = kwargs.get(book_id_param)
            if not book_id and request.is_json and request.json:
                book_id = request.json.get(book_id_param)
            if not book_id:
                return jsonify({'error': 'Book ID required'}), 400
            
            if not is_authorized_to_read(book_id, user_id):
                return jsonify({'error': 'Not authorized to read this book'}), 403
            
            g.current_user_id = user_id
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator


def require_edit_access(book_id_param: str = 'book_id') -> Callable:
    """
    Decorator to require edit access to a book.
    
    Args:
        book_id_param: The name of the parameter containing the book ID
    
    Returns:
        Callable: The decorator function
    """
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args, **kwargs) -> Any:
            user_id = get_current_user_id()
            if not user_id:
                return jsonify({'error': 'Authentication required'}), 401
            
            # Get book_id from request parameters
            book_id = kwargs.get(book_id_param)
            if not book_id and request.is_json and request.json:
                book_id = request.json.get(book_id_param)
            if not book_id:
                return jsonify({'error': 'Book ID required'}), 400
            
            if not is_authorized_to_edit(book_id, user_id):
                return jsonify({'error': 'Not authorized to edit this book'}), 403
            
            g.current_user_id = user_id
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator


def is_admin_request() -> bool:
    """
    Check if the current request is from an admin user.
    
    Returns:
        bool: True if the request has admin privileges
    """
    from config import Config
    
    # Check for admin API key in headers
    admin_key = request.headers.get('X-Admin-Key')
    return admin_key == Config.ADMIN_API_KEY
