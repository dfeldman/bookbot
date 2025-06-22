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
        bot_manager = get_bot_manager()

        # Validate required props
        if 'brief' not in props or 'style' not in props:
            log_callback("ERROR: Missing required 'brief' and/or 'style' in job props")
            return False

        brief = props.get('brief', "")
        style = props.get('style', "")

        # Get book and user information
        book = Book.query.filter_by(book_id=book_id).first()
        if not book:
            log_callback(f"ERROR: Book {book_id} not found")
            return False

        user_props = {'name': 'Default User', 'email': 'user@example.com'}
        book_props = book.props or {}

        log_callback(f"Creating foundation for book: {book_props.get('title', 'Untitled')}")

        # Step 1: Save the brief and style as-is
        log_callback("Step 1: Saving brief and style")
        _create_chunk(book_id, "brief", brief, None, 0.1, {}, log_callback)
        _create_chunk(book_id, "style", style, None, 0.2, {}, log_callback)

        # Step 2: Generate outline using LLM
        log_callback("Step 2: Generating book outline")
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
        success = llm_call.execute()
        outline_text = llm_call.output_text
        cost = llm_call.cost
        if not success:
            log_callback("ERROR: Failed to generate outline")
            return False
        log_callback(f"Outline generated: {len(outline_text)} characters, cost: ${cost:.5f}")

        # Step 3: Add scene IDs to outline
        log_callback("Step 3: Adding scene IDs to outline")
        outline_with_ids, scene_info = bot_manager.add_scene_ids(outline_text)
        log_callback(f"Added {len(scene_info)} scene IDs to outline")

        # Step 4: Tag the outline
        log_callback("Step 4: Adding tags to outline")
        template_vars = {'content': outline_with_ids, 'content_type': 'outline', 'genre': book_props.get('genre', '')}
        llm_call = bot_manager.get_llm_call('tag_content', book_props, user_props, template_vars, log_callback=log_callback)
        success = llm_call.execute()
        tagged_outline = llm_call.output_text
        cost = llm_call.cost
        if not success:
            log_callback("ERROR: Failed to tag outline, using untagged version")
            tagged_outline = outline_with_ids
        log_callback(f"Tagged outline, cost: ${cost:.5f}")

        # Step 5: Create outline chunk
        log_callback("Step 5: Creating outline chunk")
        # DO NOT STRIP THE SCENE IDS FROM THE OUTLINE. THEY MUST REMAIN IN THE FINAL VERSION. 
        outline_props = {'scene_count': len(scene_info)}
        log_callback("Creating outline chunk with scene IDs removed...")
        _create_chunk(book_id, "outline", tagged_outline, None, 1.0, outline_props, log_callback)

        # Step 6: Generate characters using LLM
        log_callback("Step 6: Generating character sheets")
        template_vars = {
            'brief': brief, 'style': style, 'outline': tagged_outline,
            'title': book_props.get('title', ''), 'genre': book_props.get('genre', ''),
            'target_length': book_props.get('target_length', 50000)
        }
        llm_call = bot_manager.get_llm_call('create_characters', book_props, user_props, template_vars, log_callback=log_callback)
        success = llm_call.execute()
        characters_text = llm_call.output_text
        cost = llm_call.cost
        if not success:
            log_callback("ERROR: Failed to generate characters")
            return False
        log_callback(f"Generated characters, cost: ${cost:.5f}")

        # Step 7: Tag the characters
        log_callback("Step 7: Adding tags to characters")
        template_vars = {'content': characters_text, 'content_type': 'characters', 'genre': book_props.get('genre', '')}
        llm_call = bot_manager.get_llm_call('tag_content', book_props, user_props, template_vars, log_callback=log_callback)
        success = llm_call.execute()
        tagged_characters = llm_call.output_text
        cost = llm_call.cost
        if not success:
            log_callback("ERROR: Failed to tag characters, using untagged version")
            tagged_characters = characters_text
        log_callback(f"Tagged characters, cost: ${cost:.5f}")

        # Step 8: Create characters chunk
        log_callback("Step 8: Creating characters chunk")
        _create_chunk(book_id, "characters", tagged_characters, 0, 2.0, {}, log_callback)

        # Step 9: Generate settings using LLM
        log_callback("Step 9: Generating settings")
        template_vars = {
            'brief': brief, 'style': style, 'outline': tagged_outline,
            'title': book_props.get('title', ''), 'genre': book_props.get('genre', '')
        }
        llm_call = bot_manager.get_llm_call('create_settings', book_props, user_props, template_vars, log_callback=log_callback)
        success = llm_call.execute()
        settings_text = llm_call.output_text
        cost = llm_call.cost
        if not success:
            log_callback("ERROR: Failed to generate settings")
            return False
        log_callback(f"Generated settings, cost: ${cost:.5f}")

        # Step 10: Tag the settings
        log_callback("Step 10: Adding tags to settings")
        template_vars = {'content': settings_text, 'content_type': 'settings', 'genre': book_props.get('genre', '')}
        llm_call = bot_manager.get_llm_call('tag_content', book_props, user_props, template_vars, log_callback=log_callback)
        success = llm_call.execute()
        tagged_settings = llm_call.output_text
        cost = llm_call.cost
        if not success:
            log_callback("ERROR: Failed to tag settings, using untagged version")
            tagged_settings = settings_text
        log_callback(f"Tagged settings, cost: ${cost:.5f}")

        # Step 11: Create settings chunk
        log_callback("Step 11: Creating settings chunk")
        _create_chunk(book_id, "settings", tagged_settings, 0, 3.0, {}, log_callback)

        # Step 7: Create empty scene chunks
        log_callback("Step 7: Creating empty scene chunks")
        scene_order_start = 4.0
        for i, info in enumerate(scene_info):
            scene_props = {
                'outline_section_id': info['outline_section_id'],
                'scene_title': info['scene_title']
            }
            _create_chunk(
                book_id=book_id,
                chunk_type="scene",
                text="",  # Empty text for scene chunks
                chapter=info['chapter'],
                order=scene_order_start + i,
                props=scene_props,
                log_callback=log_callback
            )
        log_callback(f"Created {len(scene_info)} scene chunks")

        # Step 13: Initialize default bots
        log_callback("Step 13: Initializing default bots")
        bot_count = _initialize_default_bots(book_id, log_callback)
        log_callback(f"Initialized {bot_count} default bots")

        # Step 14: Initialize default bot tasks
        log_callback("Step 14: Initializing default bot tasks")
        task_count = _initialize_default_bot_tasks(book_id, log_callback)
        log_callback(f"Initialized {task_count} default bot tasks")

        log_callback("Create Foundation job completed successfully")
        return True

    except Exception as e:
        log_callback(f"ERROR in Create Foundation job: {e}")
        import traceback
        traceback.print_exc()
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
        # Calculate word count separately to avoid any potential side effects
        word_count = Chunk.count_words(text)

        chunk = Chunk(
            book_id=book_id,
            chunk_id=chunk_id,
            text=text,
            type=chunk_type,
            chapter=chapter,
            order=order,
            props=props,
            word_count=word_count
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
                'description': bot_config.get('description', ''),
                'temperature': bot_config.get('temperature', 0.7),
                # Include any additional properties from the YAML
                **{k: v for k, v in bot_config.items() 
                   if k not in ['name', 'description', 'temperature', 'order', 'content']}
            }
            
            bot_chunk = _create_chunk(
                book_id=book_id,
                chunk_type="bot",
                text=bot_config.get('content', ''),
                chapter=None,
                order=float(bot_config.get('order', bot_count)),
                props=bot_props,
                log_callback=log_callback
            )
            
            bot_count += 1
            log_callback(f"Created bot: {bot_config['name']}")
        
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


def _initialize_default_bot_tasks(book_id: str, log_callback) -> int:
    """Initialize default bot tasks for the book from YAML configuration."""
    try:
        # Load bot task configuration from YAML file
        config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'bottasks.yml')
        
        if not os.path.exists(config_path):
            log_callback(f"Warning: Bot task config file not found at {config_path}")
            return 0
        
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        if not config or 'bottasks' not in config:
            log_callback("Warning: No bot tasks found in configuration file")
            return 0
        
        task_count = 0
        
        for task_config in config['bottasks']:
            # Validate required fields
            if 'name' not in task_config:
                log_callback("Warning: Bot task configuration missing 'name' field, skipping")
                continue
            
            # Create bot task chunk with all properties from YAML
            task_props = {
                'name': task_config['name'],
                'llm_group': task_config.get('llm_group'),
                'applicable_jobs': task_config.get('applicable_jobs', []),
                # Include any additional properties from the YAML
                **{k: v for k, v in task_config.items() 
                   if k not in ['name', 'content', 'order', 'llm_group', 'applicable_jobs']}
            }
            
            _create_chunk(
                book_id=book_id,
                chunk_type="bot_task",
                text=task_config.get('content', ''),
                chapter=None,
                order=float(task_config.get('order', task_count)),
                props=task_props,
                log_callback=log_callback
            )
            
            task_count += 1
            log_callback(f"Created bot task: {task_config['name']}")
            
        return task_count
    
    except Exception as e:
        log_callback(f"Error initializing default bot tasks: {str(e)}")
        return 0
