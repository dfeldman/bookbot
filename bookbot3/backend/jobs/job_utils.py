"""
Job utilities for BookBot.

This module provides utilities for extracting relevant context for chunks,
including outline sections, characters, and settings based on scene IDs and tags.
"""

import re
from typing import Dict, Any, List, Optional, Tuple
from backend.models import Chunk


def get_chunk_context(book_id: str, scene_id: str) -> Dict[str, Any]:
    """
    Get relevant context for a chunk based on its scene_id.
    
    Retrieves:
    - The matching outline section for the scene_id
    - All character sections that share tags with the outline section
    - All settings sections that share tags with the outline section
    
    Args:
        book_id: The book ID
        scene_id: The scene ID to find context for (e.g., "Scene 1")
        
    Returns:
        Dict containing:
        - outline_section: The relevant outline section text
        - characters_sections: List of relevant character sections
        - settings_sections: List of relevant settings sections
        - tags: List of tags found in the outline section
    """
    # Get the foundation chunks for this book
    outline_chunk = _get_chunk_by_type(book_id, "outline")
    characters_chunk = _get_chunk_by_type(book_id, "characters")
    settings_chunk = _get_chunk_by_type(book_id, "settings")
    
    if not outline_chunk:
        return {
            'outline_section': '',
            'characters_sections': [],
            'settings_sections': [],
            'tags': []
        }
    
    # Extract the relevant outline section and its tags
    outline_section, tags = _extract_outline_section_by_scene_id(outline_chunk.text, scene_id)
    
    # Extract relevant character and settings sections based on tags
    characters_sections = []
    if characters_chunk and tags:
        characters_sections = _extract_sections_by_tags(characters_chunk.text, tags, "Character")
    
    settings_sections = []
    if settings_chunk and tags:
        settings_sections = _extract_sections_by_tags(settings_chunk.text, tags, "Settings")
    
    return {
        'outline_section': outline_section,
        'characters_sections': characters_sections,
        'settings_sections': settings_sections,
        'tags': tags
    }


def _get_chunk_by_type(book_id: str, chunk_type: str) -> Optional[Chunk]:
    """Get the latest chunk of a specific type for a book."""
    return Chunk.query.filter_by(
        book_id=book_id,
        type=chunk_type,
        is_latest=True,
        is_deleted=False
    ).first()


def _extract_outline_section_by_scene_id(outline_text: str, scene_id: str) -> Tuple[str, List[str]]:
    """
    Extract the outline section that matches the given scene_id.
    
    Args:
        outline_text: The full outline text
        scene_id: The scene ID to match (e.g., "Scene 1")
        
    Returns:
        Tuple of (section_text, tags_list)
    """
    if not outline_text or not scene_id:
        return '', []
    
    lines = outline_text.split('\n')
    section_lines = []
    tags = []
    in_target_section = False
    
    for i, line in enumerate(lines):
        line = line.strip()
        
        # Check if this is a section header (level 2 or 3)
        if re.match(r'^#{2,3}\s+', line):
            # Check if this line contains our target scene_id
            scene_match = re.search(r'\[\[' + re.escape(scene_id) + r'\]\]', line)
            
            if scene_match:
                # Found our target section
                in_target_section = True
                section_lines = [line]
                
                # Extract tags from this line
                tags = re.findall(r'#(\w+)', line)
                
                # Get the content until the next section header
                for j in range(i + 1, len(lines)):
                    next_line = lines[j].strip()
                    
                    # Stop if we hit another level-2 or level-3 section header
                    if re.match(r'^#{2,3}\s+', next_line):
                        break
                    
                    section_lines.append(next_line)
                
                break
            elif in_target_section:
                # We were in the target section but hit another header, stop
                break
    
    final_section = '\n'.join(section_lines)
    return final_section, tags


def _extract_sections_by_tags(content_text: str, tags: List[str], section_type: str) -> List[str]:
    """
    Extract all sections from content that contain any of the given tags.
    
    Args:
        content_text: The full content text (characters or settings)
        tags: List of tags to match
        section_type: Type hint for section headers (e.g., "Character", "Settings")
        
    Returns:
        List of section texts that contain any of the tags
    """
    if not content_text or not tags:
        return []
    
    lines = content_text.split('\n')
    sections = []
    current_section = []
    in_matching_section = False
    
    for i, line in enumerate(lines):
        line_stripped = line.strip()
        
        # Check if this is a section header (level 2 or 3)
        if re.match(r'^#{2,3}\s+', line_stripped):
            # If we were building a matching section, save it
            if in_matching_section and current_section:
                sections.append('\n'.join(current_section))
            
            # Check if this new section contains any of our tags
            section_tags = re.findall(r'#(\w+)', line_stripped)
            has_matching_tag = any(tag in tags for tag in section_tags)
            
            if has_matching_tag:
                in_matching_section = True
                current_section = [line_stripped]
            else:
                in_matching_section = False
                current_section = []
        
        elif in_matching_section:
            # Add content to the current matching section
            current_section.append(line_stripped)
    
    # Don't forget the last section if it was matching
    if in_matching_section and current_section:
        sections.append('\n'.join(current_section))
    
    return sections


def get_outline_sections_list(book_id: str) -> List[Dict[str, Any]]:
    """
    Get a list of all outline sections with their scene IDs and tags.
    
    Useful for understanding the structure of a book's outline.
    
    Args:
        book_id: The book ID
        
    Returns:
        List of dicts with keys: scene_id, title, tags, content
    """
    outline_chunk = _get_chunk_by_type(book_id, "outline")
    if not outline_chunk:
        return []
    
    sections = []
    lines = outline_chunk.text.split('\n')
    current_section = None
    
    for i, line in enumerate(lines):
        line_stripped = line.strip()
        
        # Check if this is a section header (level 2 or 3)
        if re.match(r'^#{2,3}\s+', line_stripped):
            # Save previous section if exists
            if current_section:
                sections.append(current_section)
            
            # Extract scene ID
            scene_id_match = re.search(r'\[\[([^]]+)\]\]', line_stripped)
            scene_id = scene_id_match.group(1) if scene_id_match else None
            
            # Extract title (remove scene ID and tags)
            title = re.sub(r'\s*\[\[[^]]+\]\]', '', line_stripped)
            title = re.sub(r'^#{2,3}\s+', '', title)
            title = re.sub(r'\s*#\w+', '', title).strip()
            
            # Extract tags
            tags = re.findall(r'#(\w+)', line_stripped)
            
            current_section = {
                'scene_id': scene_id,
                'title': title,
                'tags': tags,
                'content': [line_stripped]
            }
        
        elif current_section:
            # Add content to current section
            current_section['content'].append(line_stripped)
    
    # Don't forget the last section
    if current_section:
        sections.append(current_section)
    
    # Convert content lists to strings
    for section in sections:
        section['content'] = '\n'.join(section['content'])
    
    return sections


def get_characters_list(book_id: str) -> List[Dict[str, Any]]:
    """
    Get a list of all character sections with their names and tags.
    
    Args:
        book_id: The book ID
        
    Returns:
        List of dicts with keys: name, tags, content
    """
    characters_chunk = _get_chunk_by_type(book_id, "characters")
    if not characters_chunk:
        return []
    
    return _parse_sections_list(characters_chunk.text, "Character")


def get_settings_list(book_id: str) -> List[Dict[str, Any]]:
    """
    Get a list of all settings sections with their names and tags.
    
    Args:
        book_id: The book ID
        
    Returns:
        List of dicts with keys: name, tags, content
    """
    settings_chunk = _get_chunk_by_type(book_id, "settings")
    if not settings_chunk:
        return []
    
    return _parse_sections_list(settings_chunk.text, "Settings")


def _parse_sections_list(content_text: str, section_type: str) -> List[Dict[str, Any]]:
    """Parse content into sections with names and tags."""
    if not content_text:
        return []
    
    sections = []
    lines = content_text.split('\n')
    current_section = None
    
    for i, line in enumerate(lines):
        line_stripped = line.strip()
        
        # Check if this is a section header (level 2 or 3)
        if re.match(r'^#{2,3}\s+', line_stripped):
            # Save previous section if exists
            if current_section:
                sections.append(current_section)
            
            # Extract name (remove section type prefix and tags)
            name = re.sub(r'^#{2,3}\s+' + re.escape(section_type) + r':\s*', '', line_stripped)
            name = re.sub(r'\s*#\w+', '', name).strip()
            
            # Extract tags
            tags = re.findall(r'#(\w+)', line_stripped)
            
            current_section = {
                'name': name,
                'tags': tags,
                'content': [line_stripped]
            }
        
        elif current_section:
            # Add content to current section
            current_section['content'].append(line_stripped)
    
    # Don't forget the last section
    if current_section:
        sections.append(current_section)
    
    # Convert content lists to strings
    for section in sections:
        section['content'] = '\n'.join(section['content'])
    
    return sections
