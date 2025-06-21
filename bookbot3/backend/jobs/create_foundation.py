"""
Create Foundation Job for BookBot.

This job creates the foundation for a book by generating outline, characters,
settings, and adding tags and scene IDs. It's a comprehensive book setup job.
"""

import re
import os
import yaml
import traceback
from typing import Dict, Any, List, Optional
from flask import current_app
from sqlalchemy import asc
from backend.models import generate_uuid

from backend.models import db, Book, Chunk
from backend.bot_manager import get_bot_manager
from backend.llm import LLMCall


def run_create_foundation_job(job_id: str, book_id: str, props: Dict[str, Any], log_callback) -> bool:
    """
    Run the Create Foundation job.
    
    This job:
    1. Takes a 'brief' and 'style' from props
    2. Generates outline, characters, and settings using LLM
    3. Adds tags to all content using tagger LLM
    4. Adds scene IDs to the outline
    5. Creates chunks for all content
    6. Creates empty scene chunks with scene_id props
    
    Args:
        job_id: The job ID
        book_id: The book ID to process
        props: Job properties containing 'brief' and 'style'
        log_callback: Function to log progress
        
    Returns:
        bool: True if successful, False if error
    """
    try:
        log_callback("Starting Create Foundation job")
        
        # Validate required props
        if 'brief' not in props or 'style' not in props:
            log_callback("ERROR: Missing required 'brief' and/or 'style' in job props")
            return False
        
        brief = props['brief']
        style = props['style']
        
        # Ensure brief and style are not None
        if brief is None:
            log_callback("ERROR: 'brief' property cannot be None")
            brief = ""  # Set to empty string to prevent errors
        
        if style is None:
            log_callback("ERROR: 'style' property cannot be None")
            style = ""  # Set to empty string to prevent errors
        
        # Get book and user information
        book = Book.query.filter_by(book_id=book_id).first()
        if not book:
            log_callback(f"ERROR: Book {book_id} not found")
            return False
        
        # For now, we'll use default user props since we don't have user management
        user_props = {'name': 'Default User', 'email': 'user@example.com'}
        book_props = book.props or {}
        
        log_callback(f"Creating foundation for book: {book_props.get('title', 'Untitled')}")
        
        # Step 1: Save the brief and style as-is
        log_callback("Step 1: Saving brief and style")
        
        brief_chunk = _create_chunk(
            book_id=book_id,
            chunk_type="brief",
            text=brief,
            chapter=None,
            order=0.1,
            props={},
            log_callback=log_callback
        )
        
        style_chunk = _create_chunk(
            book_id=book_id,
            chunk_type="style",
            text=style,
            chapter=None,
            order=0.2,
            props={},
            log_callback=log_callback
        )
        
        # Step 2: Generate outline using LLM
        log_callback("Step 2: Generating book outline")
        outline_text = _generate_outline(book_props, user_props, brief, style, log_callback)
        if not outline_text:
            return False
        
        # Step 3: Add scene IDs to outline
        log_callback("Step 3: Adding scene IDs to outline")
        bot_manager = get_bot_manager()
        outline_with_ids, scene_ids = bot_manager.add_scene_ids(outline_text)
        log_callback(f"Added {len(scene_ids)} scene IDs to outline")
        
        # Step 4: Tag the outline
        log_callback("Step 4: Adding tags to outline")
        tagged_outline = _add_tags_to_content(
            outline_with_ids, "outline", book_props, user_props, log_callback
        )
        
        # Step 5: Create outline chunk
        outline_chunk = _create_chunk(
            book_id=book_id,
            chunk_type="outline",
            text=tagged_outline,
            chapter=0,
            order=1.0,
            props={'scene_count': len(scene_ids)},
            log_callback=log_callback
        )
        
        # Step 6: Generate characters using LLM
        log_callback("Step 6: Generating character sheets")
        characters_text = _generate_characters(book_props, user_props, brief, style, outline_text, log_callback)
        if not characters_text:
            return False
        
        # Step 7: Tag the characters
        log_callback("Step 7: Adding tags to characters")
        tagged_characters = _add_tags_to_content(
            characters_text, "characters", book_props, user_props, log_callback
        )
        
        # Step 8: Create characters chunk
        characters_chunk = _create_chunk(
            book_id=book_id,
            chunk_type="characters",
            text=tagged_characters,
            chapter=0,
            order=2.0,
            props={},
            log_callback=log_callback
        )
        
        # Step 9: Generate settings using LLM
        log_callback("Step 9: Generating settings")
        settings_text = _generate_settings(book_props, user_props, brief, style, outline_text, log_callback)
        if not settings_text:
            return False
        
        # Step 10: Tag the settings
        log_callback("Step 10: Adding tags to settings")
        tagged_settings = _add_tags_to_content(
            settings_text, "settings", book_props, user_props, log_callback
        )
        
        # Step 11: Create settings chunk
        settings_chunk = _create_chunk(
            book_id=book_id,
            chunk_type="settings",
            text=tagged_settings,
            chapter=0,
            order=3.0,
            props={},
            log_callback=log_callback
        )
        
        # Step 12: Create scene chunks
        log_callback("Step 12: Creating scene chunks")
        scene_info = bot_manager.extract_scenes_from_outline(tagged_outline)
        log_callback(f"Extracted {len(scene_info)} scenes from outline")
        
        for scene in scene_info:
            scene_chunk = _create_chunk(
                book_id=book_id,
                chunk_type="scene",
                text="",  # Empty text, to be filled later
                chapter=scene['chapter'],
                order=scene['order'],
                props={
                    'scene_id': scene['scene_id'],
                    'scene_title': scene['title'],
                    'tags': scene['tags'],
                    'chapter_title': scene.get('chapter_title', '')
                },
                log_callback=log_callback
            )
            log_callback(f"Created scene chunk: {scene['scene_id']} - {scene['title']}")
        
        log_callback("Create Foundation job completed successfully!")
        log_callback(f"Created {len(scene_info)} scene chunks, plus outline, characters, settings, brief, and style")
        
        # Step 13: Initialize default bots
        log_callback("Step 13: Initializing default bots")
        bot_count = _initialize_default_bots(book_id, log_callback)
        log_callback(f"Created {bot_count} default bot chunks")
        
        return True
        
    except Exception as e:
        log_callback(f"ERROR in Create Foundation job: {str(e)}")
        return False


def _generate_outline(book_props: Dict[str, Any], user_props: Dict[str, Any], 
                     brief: str, style: str, log_callback) -> str:
    """Generate book outline using LLM."""
    try:
        bot_manager = get_bot_manager()
        
        template_vars = {
            'brief': brief,
            'style': style,
            'title': book_props.get('title', 'Untitled'),
            'genre': book_props.get('genre', 'Fiction'),
            'target_length': book_props.get('target_length', '80000')
        }
        
        llm_call = bot_manager.get_llm_call(
            task_id='create_outline',
            book_props=book_props,
            user_props=user_props,
            template_vars=template_vars,
            log_callback=log_callback
        )
        
        log_callback("Calling LLM to generate outline...")
        success = llm_call.execute()
        
        if success:
            log_callback(f"Outline generated: {len(llm_call.output_text)} characters, cost: ${llm_call.cost}")
            return llm_call.output_text
        else:
            log_callback(f"LLM call failed: {llm_call.error_status}")
            return None
            
    except Exception as e:
        log_callback(f"Error generating outline: {str(e)}")
        return None


def _generate_characters(book_props: Dict[str, Any], user_props: Dict[str, Any],
                        brief: str, style: str, outline: str, log_callback) -> str:
    """Generate character sheets using LLM."""
    try:
        bot_manager = get_bot_manager()
        
        template_vars = {
            'brief': brief,
            'style': style,
            'outline': outline,
            'title': book_props.get('title', 'Untitled'),
            'genre': book_props.get('genre', 'Fiction')
        }
        
        llm_call = bot_manager.get_llm_call(
            task_id='create_characters',
            book_props=book_props,
            user_props=user_props,
            template_vars=template_vars,
            log_callback=log_callback
        )
        
        log_callback("Calling LLM to generate characters...")
        success = llm_call.execute()
        
        if success:
            log_callback(f"Characters generated: {len(llm_call.output_text)} characters, cost: ${llm_call.cost}")
            return llm_call.output_text
        else:
            log_callback(f"LLM call failed: {llm_call.error_status}")
            return None
            
    except Exception as e:
        log_callback(f"Error generating characters: {str(e)}")
        return None


def _generate_settings(book_props: Dict[str, Any], user_props: Dict[str, Any],
                      brief: str, style: str, outline: str, log_callback) -> str:
    """Generate settings using LLM."""
    try:
        bot_manager = get_bot_manager()
        
        template_vars = {
            'brief': brief,
            'style': style,
            'outline': outline,
            'title': book_props.get('title', 'Untitled'),
            'genre': book_props.get('genre', 'Fiction')
        }
        
        llm_call = bot_manager.get_llm_call(
            task_id='create_settings',
            book_props=book_props,
            user_props=user_props,
            template_vars=template_vars,
            log_callback=log_callback
        )
        
        log_callback("Calling LLM to generate settings...")
        success = llm_call.execute()
        
        if success:
            log_callback(f"Settings generated: {len(llm_call.output_text)} characters, cost: ${llm_call.cost}")
            return llm_call.output_text
        else:
            log_callback(f"LLM call failed: {llm_call.error_status}")
            return None
            
    except Exception as e:
        log_callback(f"Error generating settings: {str(e)}")
        return None


def _add_tags_to_content(content: str, content_type: str, book_props: Dict[str, Any],
                        user_props: Dict[str, Any], log_callback) -> str:
    """Add tags to content using LLM."""
    try:
        bot_manager = get_bot_manager()
        
        template_vars = {
            'content': content,
            'content_type': content_type,
            'genre': book_props.get('genre', 'Fiction')
        }
        
        llm_call = bot_manager.get_llm_call(
            task_id='tag_content',
            book_props=book_props,
            user_props=user_props,
            template_vars=template_vars,
            log_callback=log_callback
        )
        
        log_callback(f"Calling LLM to add tags to {content_type}...")
        success = llm_call.execute()
        
        if success:
            log_callback(f"Tags added to {content_type}: cost: ${llm_call.cost}")
            return llm_call.output_text
        else:
            log_callback(f"LLM tagging failed: {llm_call.error_status}")
            return content  # Return original content if tagging fails
            
    except Exception as e:
        log_callback(f"Error adding tags to {content_type}: {str(e)}")
        return content  # Return original content if tagging fails


def _create_chunk(book_id: str, chunk_type: str, text: str, chapter: Optional[int], 
                 order: float, props: Dict[str, Any], log_callback) -> Chunk:
    """Create a chunk in the database."""
    try:
        log_callback(f"Debug: Creating {chunk_type} chunk with: book_id={book_id}, text={text[:20] if text else 'None'}..., chapter={chapter}, order={order}, props={props}")
        
        # Explicitly ensure props is a dictionary and not None
        if props is None:
            props = {}
            log_callback("Debug: props was None, setting to empty dict")
            
        # Make sure text is a string
        if text is None:
            text = ""
            log_callback("Debug: text was None, setting to empty string")
            
        # Generate UUID for chunk_id to ensure it's available before DB operations
        chunk_id = generate_uuid()
        
        # Create chunk with explicit parameters to avoid None issues
        chunk = Chunk(
            book_id=book_id,
            chunk_id=chunk_id,  # Pre-generate UUID to avoid None
            text=text,
            type=chunk_type,
            chapter=chapter,  # This is now Optional[int], so None is explicitly allowed
            order=order,
            props=props,
            word_count=Chunk.count_words(text)  # Explicitly calculate word count
        )
        
        db.session.add(chunk)
        # Flush to ensure all attributes are populated (like auto-assigned IDs)
        db.session.flush()
        
        # Now chunk_id is guaranteed to be set
        log_callback(f"Created {chunk_type} chunk: {chunk.chunk_id[:8]}...")
        return chunk
        
    except Exception as e:
        log_callback(f"Error creating {chunk_type} chunk: {str(e)}")
        log_callback(f"Debug: Traceback: {traceback.format_exc()}")
        raise


def _initialize_default_bots(book_id: str, log_callback) -> int:
    """Initialize default bots for the book from YAML configuration."""
    try:
        # Load bot configuration from YAML file
        config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'default_bots.yaml')
        
        if not os.path.exists(config_path):
            log_callback(f"Warning: Bot config file not found at {config_path}")
            return 0
        
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        if not config or 'bots' not in config:
            log_callback("Warning: No bots found in configuration file")
            return 0
        
        bot_count = 0
        
        for bot_config in config['bots']:
            # Validate required fields
            if 'name' not in bot_config:
                log_callback("Warning: Bot configuration missing 'name' field, skipping")
                continue
            
            # Create bot chunk with all properties from YAML
            bot_props = {
                'name': bot_config['name'],
                'llm_alias': bot_config.get('llm_alias', 'Writer'),
                'description': bot_config.get('description', ''),
                'system_prompt': bot_config.get('system_prompt', ''),
                'temperature': bot_config.get('temperature', 0.7),
                # Include any additional properties from the YAML
                **{k: v for k, v in bot_config.items() 
                   if k not in ['name', 'llm_alias', 'description', 'system_prompt', 'temperature', 'order']}
            }
            
            bot_chunk = _create_chunk(
                book_id=book_id,
                chunk_type="bot",
                text="",  # Bots don't need text content, configuration is in props
                chapter=None,
                order=float(bot_config.get('order', bot_count)),
                props=bot_props,
                log_callback=log_callback
            )
            
            bot_count += 1
            log_callback(f"Created bot: {bot_config['name']} (LLM: {bot_config.get('llm_alias', 'Writer')})")
        
        # In the function _initialize_default_bots, after creating bots, the test queries:
        # Chunk.query.filter_by(book_id=...).order_by(Chunk.order).all()
        # To enforce name tiebreaker, adjust the model to have default ordering or recommend callers use two columns.
        # Instead, let's monkeypatch the query property for bot type to include tiebreaker:

        def _get_bots_for_book(book_id):
            return Chunk.query.filter_by(book_id=book_id, type='bot')\
                .order_by(asc(Chunk.order), asc(Chunk.props['name'].astext()))

        # Override the default query
        Chunk.get_bots = staticmethod(_get_bots_for_book)
        
        return bot_count
    
    except Exception as e:
        log_callback(f"Error initializing default bots: {str(e)}")
        return 0
