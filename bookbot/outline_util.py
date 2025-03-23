"""
Outline Utility Module for the LLM-based Book Writing System

This module provides utility functions for processing and manipulating outlines,
including renumbering chapters, extracting chapter content, and retrieving relevant
character and setting information for specific chapters.
"""

import re
import logging
from typing import Dict, List, Optional, Tuple, Set

# Configure logging
logger = logging.getLogger(__name__)

def renumber_chapters(outline_text: str) -> str:
    """
    Renumber all chapters in the outline sequentially.
    
    This function finds all lines starting with '## Chapter' and renumbers them
    consecutively, regardless of their original numbers or which section they're in.
    
    Args:
        outline_text (str): The original outline text
        
    Returns:
        str: The outline with chapters renumbered sequentially
    """
    # Regular expression to match chapter headings
    chapter_pattern = re.compile(r'^(## Chapter\s+)(\d+)(.*?)$', re.MULTILINE)
    
    # Find all chapter headings
    matches = list(chapter_pattern.finditer(outline_text))
    
    if not matches:
        logger.warning("No chapters found in the outline to renumber.")
        return outline_text
    
    # Create a copy of the text that we'll modify
    new_text = outline_text
    
    # Process matches in reverse order to avoid position shifts
    for i, match in reversed(list(enumerate(matches))):
        chapter_num = i + 1  # New chapter number (1-based)
        
        # Replace the old chapter heading with the new one
        prefix = match.group(1)  # '## Chapter '
        suffix = match.group(3)  # Everything after the number
        
        new_heading = f"{prefix}{chapter_num}{suffix}"
        new_text = new_text[:match.start()] + new_heading + new_text[match.end():]
    
    logger.info(f"Renumbered {len(matches)} chapters in the outline.")
    return new_text

def count_chapters(outline_text: str) -> int:
    """
    Count the number of chapters in the outline.
    
    Args:
        outline_text (str): The outline text
        
    Returns:
        int: The number of chapters found in the outline
    """
    # Regular expression to match chapter headings
    chapter_pattern = re.compile(r'^## Chapter\s+\d+', re.MULTILINE)
    
    # Find all chapter headings
    matches = list(chapter_pattern.finditer(outline_text))
    chapter_count = len(matches)
    
    logger.info(f"Found {chapter_count} chapters in the outline.")
    return chapter_count

def extract_tags(chapter_heading: str) -> Tuple[int, Set[str]]:
    """
    Extract the chapter number and tags from a chapter heading.
    
    Args:
        chapter_heading (str): The chapter heading line
        
    Returns:
        Tuple[int, Set[str]]: The chapter number and a set of tags
    """
    # Regular expression to match chapter number
    chapter_num_pattern = re.compile(r'^## Chapter\s+(\d+)')
    chapter_match = chapter_num_pattern.search(chapter_heading)
    
    if not chapter_match:
        logger.error(f"Could not extract chapter number from heading: {chapter_heading}")
        return 0, set()
    
    chapter_num = int(chapter_match.group(1))
    
    # Extract tags (words that start with #, excluding the initial ## for the heading)
    tags = set()
    tag_pattern = re.compile(r'#(\w+(?:-\w+)*)')
    
    for match in tag_pattern.finditer(chapter_heading):
        tag = match.group(1)
        # Skip tags that are just the heading level marker
        if tag != '#':
            tags.add(tag)
    
    return chapter_num, tags

def find_chapter_heading(outline_text: str, chapter_num: int) -> Optional[str]:
    """
    Find the heading line for a specific chapter number.
    
    Args:
        outline_text (str): The outline text
        chapter_num (int): The chapter number to find
        
    Returns:
        Optional[str]: The chapter heading line if found, None otherwise
    """
    # Regular expression to match the specific chapter heading
    chapter_pattern = re.compile(f'^## Chapter\\s+{chapter_num}.*?$', re.MULTILINE)
    
    match = chapter_pattern.search(outline_text)
    if match:
        return match.group(0)
    
    logger.warning(f"Chapter {chapter_num} not found in outline.")
    return None

def find_chapter_content(outline_text: str, chapter_num: int) -> Optional[Tuple[str, str, str]]:
    """
    Find the content for a specific chapter, including its heading, content, and preceding section.
    
    Args:
        outline_text (str): The outline text
        chapter_num (int): The chapter number to find
        
    Returns:
        Optional[Tuple[str, str, str]]: A tuple containing:
            - The chapter heading
            - The chapter content
            - The preceding section or content
        Returns None if the chapter is not found.
    """
    # Split the outline into lines
    lines = outline_text.split('\n')
    
    # Find the line number of the requested chapter
    chapter_line_idx = -1
    for i, line in enumerate(lines):
        if re.match(f'^## Chapter\\s+{chapter_num}\\b', line):
            chapter_line_idx = i
            break
    
    if chapter_line_idx == -1:
        logger.warning(f"Chapter {chapter_num} not found in outline.")
        return None
    
    # Get the chapter heading
    chapter_heading = lines[chapter_line_idx]
    
    # Find the end of the chapter content
    end_idx = len(lines)
    for i in range(chapter_line_idx + 1, len(lines)):
        # Stop at the next chapter or section heading
        if re.match(r'^#+ ', lines[i]):
            end_idx = i
            break
    
    # Extract the chapter content
    chapter_content = '\n'.join(lines[chapter_line_idx + 1:end_idx])
    
    # Find the preceding section or content
    preceding_content = ""
    section_start_idx = -1
    
    # Look backward to find the containing section, if any
    for i in range(chapter_line_idx - 1, -1, -1):
        if re.match(r'^# ', lines[i]):
            section_start_idx = i
            break
    
    # If this is the first chapter in a section, get content between section heading and chapter
    if section_start_idx != -1:
        # Find the previous chapter in the same section, if any
        prev_chapter_idx = -1
        for i in range(chapter_line_idx - 1, section_start_idx, -1):
            if re.match(r'^## Chapter', lines[i]):
                prev_chapter_idx = i
                break
        
        if prev_chapter_idx != -1:
            # There's a previous chapter in this section
            # Get content from the end of that chapter to the start of this one
            prev_chapter_end_idx = -1
            for i in range(prev_chapter_idx + 1, chapter_line_idx):
                if re.match(r'^#+ ', lines[i]):
                    prev_chapter_end_idx = i - 1
                    break
            
            if prev_chapter_end_idx == -1:
                # No subsections found, use all content
                preceding_content = '\n'.join(lines[prev_chapter_idx:chapter_line_idx])
            else:
                preceding_content = '\n'.join(lines[prev_chapter_idx:prev_chapter_end_idx + 1])
        else:
            # This is the first chapter in the section, get section intro
            preceding_content = '\n'.join(lines[section_start_idx:chapter_line_idx])
    
    return chapter_heading, chapter_content, preceding_content

def get_character_profiles(character_text: str, tags: Set[str]) -> Dict[str, str]:
    """
    Extract character profiles for the specified tags.
    
    Args:
        character_text (str): The full character sheets text
        tags (Set[str]): The set of character tags to extract
        
    Returns:
        Dict[str, str]: Dictionary mapping character tags to their profiles
    """
    character_profiles = {}
    
    # Regular expression to find character sections
    # Match from a level 1 heading with a tag to the next level 1 heading or end of text
    pattern = re.compile(r'^# [^#]+#(\w+(?:-\w+)*)\s*$(.*?)(?=^# |\Z)', re.MULTILINE | re.DOTALL)
    
    for match in pattern.finditer(character_text):
        tag = match.group(1)
        if tag in tags:
            profile = match.group(0)
            character_profiles[tag] = profile
    
    missing_tags = tags - set(character_profiles.keys())
    if missing_tags:
        logger.warning(f"Could not find character profiles for tags: {missing_tags}")
    
    return character_profiles

def get_setting_profiles(setting_text: str, tags: Set[str]) -> Dict[str, str]:
    """
    Extract setting profiles for the specified tags.
    
    Args:
        setting_text (str): The full setting profiles text
        tags (Set[str]): The set of setting tags to extract
        
    Returns:
        Dict[str, str]: Dictionary mapping setting tags to their profiles
    """
    setting_profiles = {}
    
    # Regular expression to find setting sections
    # Match from a level 1 heading with a tag to the next level 1 heading or end of text
    pattern = re.compile(r'^# [^#]+#(\w+(?:-\w+)*)\s*$(.*?)(?=^# |\Z)', re.MULTILINE | re.DOTALL)
    
    for match in pattern.finditer(setting_text):
        tag = match.group(1)
        if tag in tags:
            profile = match.group(0)
            setting_profiles[tag] = profile
    
    missing_tags = tags - set(setting_profiles.keys())
    if missing_tags:
        logger.warning(f"Could not find setting profiles for tags: {missing_tags}")
    
    return setting_profiles

def get_chapter_content(outline_text: str, chapter_num: int, 
                        character_text: str, setting_text: str) -> Dict[str, str]:
    """
    Get the complete content needed to write a specific chapter.
    
    This includes:
    - The chapter heading and description
    - The preceding section or content
    - Character profiles for all tagged characters
    - Setting profiles for all tagged settings
    
    Args:
        outline_text (str): The outline text
        chapter_num (int): The chapter number to get content for
        character_text (str): The full character sheets text
        setting_text (str): The full setting profiles text
        
    Returns:
        Dict[str, str]: Dictionary with the following keys:
            - 'chapter_heading': The chapter heading
            - 'chapter_content': The chapter description
            - 'preceding_content': The relevant preceding content
            - 'characters': Combined text of all relevant character profiles
            - 'settings': Combined text of all relevant setting profiles
            - 'all_content': All of the above combined
    
    Raises:
        ValueError: If the chapter number is not found in the outline
    """
    try:
        # Find the chapter content
        chapter_info = find_chapter_content(outline_text, chapter_num)
        if not chapter_info:
            raise ValueError(f"Chapter {chapter_num} not found in outline.")
        
        chapter_heading, chapter_content, preceding_content = chapter_info
        
        # Extract tags from the chapter heading
        _, tags = extract_tags(chapter_heading)
        
        # Get character and setting profiles
        character_profiles = get_character_profiles(character_text, tags)
        setting_profiles = get_setting_profiles(setting_text, tags)
        
        # Combine character profiles
        characters_text = "\n\n".join(character_profiles.values())
        
        # Combine setting profiles
        settings_text = "\n\n".join(setting_profiles.values())
        
        # Create the result dictionary
        result = {
            'chapter_heading': chapter_heading,
            'chapter_content': chapter_content,
            'preceding_content': preceding_content,
            'characters': characters_text,
            'settings': settings_text,
            'all_content': f"{preceding_content}\n\n{chapter_heading}\n{chapter_content}\n\n" + 
                          f"CHARACTERS:\n{characters_text}\n\n" +
                          f"SETTINGS:\n{settings_text}"
        }
        
        return result
    
    except Exception as e:
        logger.error(f"Error getting content for chapter {chapter_num}: {e}")
        raise
    