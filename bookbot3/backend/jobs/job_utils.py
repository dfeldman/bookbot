"""
Job utilities for BookBot.

This module provides utilities for extracting relevant context for chunks,
including outline sections, characters, and settings based on scene IDs and tags.
"""

import re
from typing import Dict, Any, List, Optional, Tuple
from backend.models import Chunk


def get_chunk_context(book_id: str, outline_section_id: int) -> Dict[str, Any]:
    """
    Get relevant context for a chunk based on its outline_section_id.

    Retrieves:
    - The matching outline section for the outline_section_id
    - All character sections that share tags with the outline section
    - All settings sections that share tags with the outline section

    Args:
        book_id: The book ID
        outline_section_id: The scene ID to find context for (e.g., 1)

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
    outline_section, tags = _extract_outline_section_by_id(outline_chunk.text, outline_section_id)

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


def _extract_outline_section_by_id(outline_text: str, outline_section_id: int) -> Tuple[str, List[str]]:
    """
    Extract the outline section that matches the given outline_section_id.
    A valid section header starts with '## ' or '### '.

    Args:
        outline_text: The full text of the outline.
        outline_section_id: The scene ID to match (e.g., 1)

    Returns:
        A tuple containing the matched section text and any tags found.
    """
    if not outline_text or not outline_section_id:
        return "", []

    lines = outline_text.split('\n')
    section_content = []
    in_section = False
    tags = []

    id_marker = f"#scene_id={outline_section_id}"

    for line in lines:
        line_stripped = line.strip()
        # A valid header is level 2 or 3
        is_header = re.match(r'^#{2,3}\s+', line_stripped)

        if in_section:
            # If we've reached the next header (of any level), stop.
            if line_stripped.startswith('#'):
                break
            section_content.append(line)
        elif is_header and id_marker in line:
            in_section = True
            # Clean the line to remove the scene marker for the final output
            cleaned_line = line.replace(id_marker, '').strip()
            section_content.append(cleaned_line)

            # Extract tags from the line
            tag_matches = re.findall(r'#(\w+)', line)
            # Filter out the scene_id tag from the returned list
            tags.extend([tag for tag in tag_matches if not tag.startswith('scene_id')])

    return '\n'.join(section_content).strip(), tags


def _get_chunk_by_type(book_id: str, chunk_type: str) -> Optional[Chunk]:
    """Get the latest chunk of a specific type for a book."""
    return Chunk.query.filter_by(
        book_id=book_id,
        type=chunk_type,
        is_latest=True,
        is_deleted=False
    ).first()


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
    
    sections = []
    lines = content_text.split('\n')
    current_section_lines = []
    in_matching_section = False
    
    tag_set = set(tags)
    
    for i, line in enumerate(lines):
        line_stripped = line.strip()
        
        # Check if this is a section header (level 2 or 3)
        if re.match(r'^#{2,3}\s+', line_stripped):
            # If we were in a matching section, save it before starting a new one
            if in_matching_section and current_section_lines:
                sections.append('\n'.join(current_section_lines))
            
            # Reset for the new section
            current_section_lines = [line]
            
            # Check if this new section has any of the target tags
            line_tags = re.findall(r'#(\w+)', line_stripped)
            if tag_set.intersection(line_tags):
                in_matching_section = True
            else:
                in_matching_section = False
        
        elif in_matching_section:
            # Add content to the current matching section
            current_section_lines.append(line)
            
    # Add the last section if it was matching
    if in_matching_section and current_section_lines:
        sections.append('\n'.join(current_section_lines))
        
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
            scene_id_match = re.search(r'#scene_id=(\d+)', line_stripped)
            scene_id = int(scene_id_match.group(1)) if scene_id_match else None
            
            # Extract title (remove scene ID and tags)
            title = re.sub(r'\s*#scene_id=\d+', '', line_stripped)
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
