"""
Bot Manager for BookBot.

This module manages LLM task configuration, prompts, and parameters.
In the future, this will retrieve custom prompts for individual users
and tasks. For now, it provides default prompts and LLM settings.
"""

import re
from typing import Dict, Any, Optional
from backend.llm import LLMCall


class BotManager:
    """Manages LLM tasks, prompts, and model configurations."""
    
    # Default model settings for different task types
    TASK_CONFIGS = {
        'create_outline': {
            'model': 'claude-3-haiku',
            'target_word_count': 800,
            'temperature': 0.7,
            'max_tokens': 2000,
        },
        'create_characters': {
            'model': 'claude-3-haiku',
            'target_word_count': 600,
            'temperature': 0.8,
            'max_tokens': 1500,
        },
        'create_settings': {
            'model': 'claude-3-haiku',
            'target_word_count': 400,
            'temperature': 0.7,
            'max_tokens': 1000,
        },
        'tag_content': {
            'model': 'claude-3-haiku',
            'target_word_count': 100,
            'temperature': 0.3,
            'max_tokens': 500,
        }
    }
    
    # Prompt templates for different tasks
    PROMPT_TEMPLATES = {
        'create_outline': """You are a professional book outline creator. Create a detailed chapter-by-chapter outline for a book based on the brief and style provided.

BRIEF:
{brief}

STYLE GUIDE:
{style}

BOOK DETAILS:
Title: {title}
Genre: {genre}
Target Length: {target_length} words

INSTRUCTIONS:
1. Create a compelling chapter-by-chapter outline
2. Each chapter should have 2-4 scenes
3. Include character development arcs
4. Ensure proper pacing and story structure
5. Make each scene description detailed enough to guide writing
6. Use markdown formatting with ## for chapters and ### for scenes
7. Each scene should be 1-2 paragraphs describing what happens

Example format:
## Chapter 1: The Beginning
### Scene: Character introduction and inciting incident
Description of what happens in this scene...

### Scene: First plot development
Description of the next scene...

Create a complete outline now:""",
        
        'create_characters': """You are a professional character developer. Create detailed character sheets for the main characters in this book based on the brief, style, and outline provided.

BRIEF:
{brief}

STYLE GUIDE:
{style}

OUTLINE:
{outline}

BOOK DETAILS:
Title: {title}
Genre: {genre}

INSTRUCTIONS:
1. Identify 3-6 main characters from the outline
2. Create detailed character sheets with:
   - Name and basic demographics
   - Physical description
   - Personality traits and quirks
   - Background and history
   - Goals and motivations
   - Character arc throughout the story
   - Relationships with other characters
3. Use markdown formatting with ## for each character
4. Make characters feel real and three-dimensional
5. Ensure characters fit the genre and style

Create detailed character sheets now:""",
        
        'create_settings': """You are a professional world-builder. Create detailed setting descriptions for this book based on the brief, style, and outline provided.

BRIEF:
{brief}

STYLE GUIDE:
{style}

OUTLINE:
{outline}

BOOK DETAILS:
Title: {title}
Genre: {genre}

INSTRUCTIONS:
1. Identify key locations from the outline
2. Create detailed setting descriptions including:
   - Physical appearance and atmosphere
   - History and significance
   - Cultural and social elements
   - Important details that affect the story
   - Sensory details (sights, sounds, smells)
3. Consider the genre and ensure settings match the tone
4. Use markdown formatting with ## for each major location
5. Include both macro settings (cities, regions) and micro settings (specific buildings, rooms)

Create detailed setting descriptions now:""",
        
        'tag_content': """You are a content tagger. Add relevant hashtags to the provided content to help with future search and organization.

CONTENT TO TAG:
{content}

CONTENT TYPE: {content_type}
GENRE: {genre}

INSTRUCTIONS:
1. Add 3-6 relevant hashtags to each major section
2. Use hashtags for themes, genres, character types, settings, plot elements
3. Place hashtags at the end of section headers
4. Use lowercase with underscores for multi-word tags
5. Be specific and useful for future search
6. Don't change the content, only add hashtags

Example:
## Chapter 1: The Beginning #action #mystery #urban_setting
### Scene: Detective arrives at crime scene #investigation #police #tension

Add hashtags to the content now, preserving all original text:"""
    }
    
    def __init__(self):
        """Initialize the bot manager."""
        pass
    
    def get_llm_call(
        self,
        task_id: str,
        book_props: Dict[str, Any],
        user_props: Dict[str, Any],
        template_vars: Dict[str, Any],
        api_key: str = "fake-key",
        log_callback: Optional[callable] = None
    ) -> LLMCall:
        """
        Get a configured LLM call for a specific task.
        
        Args:
            task_id: The task identifier (e.g., 'create_outline')
            book_props: Book properties for context
            user_props: User properties for future customization
            template_vars: Variables to substitute in the prompt template
            api_key: API key for the LLM provider
            log_callback: Optional logging callback
            
        Returns:
            LLMCall: Configured LLM call ready to execute
        """
        if task_id not in self.TASK_CONFIGS:
            raise ValueError(f"Unknown task ID: {task_id}")
        
        if task_id not in self.PROMPT_TEMPLATES:
            raise ValueError(f"No prompt template for task: {task_id}")
        
        # Get task configuration
        config = self.TASK_CONFIGS[task_id].copy()
        
        # Get and format the prompt
        prompt_template = self.PROMPT_TEMPLATES[task_id]
        prompt = self._format_prompt(prompt_template, template_vars)
        
        # Create LLM call with the formatted prompt
        llm_call = LLMCall(
            model=config['model'],
            api_key=api_key,
            target_word_count=config['target_word_count'],
            model_mode="fake",  # For now, always use fake
            log_callback=log_callback
        )
        
        # Set the prompt for the LLM call
        llm_call.set_prompt(prompt)
        
        return llm_call
    
    def _format_prompt(self, template: str, variables: Dict[str, Any]) -> str:
        """
        Format a prompt template with the provided variables.
        
        Args:
            template: The prompt template string
            variables: Variables to substitute
            
        Returns:
            str: Formatted prompt
        """
        try:
            return template.format(**variables)
        except KeyError as e:
            raise ValueError(f"Missing template variable: {e}")
    
    def add_scene_ids(self, outline_text: str) -> tuple[str, list[str]]:
        """
        Add scene IDs to an outline and extract scene information.
        
        Args:
            outline_text: The outline text to process
            
        Returns:
            tuple: (modified_outline_text, list_of_scene_ids)
        """
        lines = outline_text.split('\n')
        modified_lines = []
        scene_ids = []
        scene_counter = 1
        
        for line in lines:
            # Check if this is a scene line (starts with ### Scene)
            if line.strip().startswith('### Scene'):
                # Add scene ID if not already present
                if '[[Scene' not in line:
                    scene_id = f"Scene {scene_counter}"
                    scene_ids.append(scene_id)
                    
                    # Add the scene ID at the end of the line
                    modified_line = f"{line.rstrip()} [[{scene_id}]]"
                    modified_lines.append(modified_line)
                    scene_counter += 1
                else:
                    # Extract existing scene ID
                    match = re.search(r'\[\[(Scene \d+)\]\]', line)
                    if match:
                        scene_ids.append(match.group(1))
                    modified_lines.append(line)
            else:
                modified_lines.append(line)
        
        return '\n'.join(modified_lines), scene_ids
    
    def extract_scenes_from_outline(self, outline_text: str) -> list[Dict[str, Any]]:
        """
        Extract scene information from an outline for creating scene chunks.
        
        Args:
            outline_text: The outline text with scene IDs
            
        Returns:
            list: Scene information dictionaries
        """
        scenes = []
        lines = outline_text.split('\n')
        current_chapter = None
        chapter_number = 0
        scene_order = 0
        
        for line in lines:
            line = line.strip()
            
            # Track current chapter
            if line.startswith('## ') and 'Chapter' in line:
                # Extract chapter number
                chapter_match = re.search(r'Chapter (\d+)', line)
                if chapter_match:
                    chapter_number = int(chapter_match.group(1))
                else:
                    chapter_number += 1
                current_chapter = line
                scene_order = 0
            
            # Extract scene information
            elif line.startswith('### Scene') and '[[Scene' in line:
                scene_order += 1
                
                # Extract scene ID
                scene_id_match = re.search(r'\[\[(Scene \d+)\]\]', line)
                scene_id = scene_id_match.group(1) if scene_id_match else f"Scene {len(scenes) + 1}"
                
                # Extract scene title (remove Scene ID)
                scene_title = re.sub(r'\s*\[\[Scene \d+\]\]', '', line)
                scene_title = re.sub(r'^### Scene:\s*', '', scene_title)
                
                # Extract tags
                tags = re.findall(r'#(\w+)', scene_title)
                scene_title_clean = re.sub(r'\s*#\w+', '', scene_title).strip()
                
                scenes.append({
                    'scene_id': scene_id,
                    'title': scene_title_clean,
                    'chapter': chapter_number,
                    'order': float(scene_order),
                    'tags': tags,
                    'chapter_title': current_chapter
                })
        
        return scenes


# Global instance
bot_manager = BotManager()


def get_bot_manager() -> BotManager:
    """Get the global bot manager instance."""
    return bot_manager
