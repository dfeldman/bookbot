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
        
        'tag_content': """You are a content tagger. Your task is to add relevant hashtags to the provided content, preserving the original text and formatting completely.

CONTENT TO TAG:
{content}

CONTENT TYPE: {content_type}
GENRE: {genre}

INSTRUCTIONS:
1. Add 3-6 relevant hashtags to each major section header (lines starting with ## or ###).
2. Place the hashtags at the end of the header lines.
3. Use hashtags for themes, genres, character types, settings, plot elements.
4. Use lowercase with underscores for multi-word tags (e.g., #urban_fantasy).
5. Be specific and useful for future search.
6. CRITICAL: You MUST NOT change, reformat, or remove any part of the original content. The output must be identical to the input, with only the hashtags added to the headers. Preserve all newlines and whitespace exactly as they appear in the original content.

Example of what to do:

INPUT:
## Chapter 1: The Beginning
The story starts here.

### Scene: A new hero
A hero is introduced.
They are brave.

OUTPUT:
## Chapter 1: The Beginning #prologue #hero_introduction
The story starts here.

### Scene: A new hero #character_moment #origin_story
A hero is introduced.
They are brave.

Now, add hashtags to the content, preserving all original text and formatting perfectly."""
    }
    
    def __init__(self):
        """Initialize the bot manager."""
        pass

    def add_scene_ids(self, outline_text: str):
        """
        Parses an outline to find scene definitions. If a scene does not have an ID,
        it adds a unique one in the format [[Scene ...]]. It returns the modified
        outline along with information about each scene.

        This function is designed to be idempotent and handle outlines that may
        already contain scene IDs.

        Args:
            outline_text: The book outline with markdown formatting.

        Returns:
            A tuple containing:
            - The modified outline text with scene IDs added or preserved.
            - A list of dicts, each with 'outline_section_id', 'chapter', and 'scene_title'.
        """
        lines = outline_text.split('\n')
        new_lines = []
        scene_info = []
        current_chapter = 0

        # Find the highest existing ID to ensure new IDs are unique
        existing_ids = [int(i) for i in re.findall(r'\[\[Scene\s+(\d+)\]\]', outline_text)]
        scene_counter = max(existing_ids) + 1 if existing_ids else 1

        # Regex for scenes that already have an ID
        scene_with_id_regex = re.compile(r"###\s*Scene:\s*(.*?)(?:\s*\[\[Scene\s*(\d+)\]\])?$", re.IGNORECASE)
        scene_without_id_regex = re.compile(r"###\s*Scene:\s*(.*)", re.IGNORECASE)

        for line in lines:
            line_stripped = line.strip()
            chapter_match = re.match(r'^##\s+Chapter\s+(\d+)', line_stripped)
            
            if chapter_match:
                current_chapter = int(chapter_match.group(1))
                new_lines.append(line)
                continue

            # First, try to match a scene that already has an ID. This is more specific.
            scene_match_with_id = scene_with_id_regex.match(line_stripped)
            if scene_match_with_id and current_chapter > 0:
                scene_title = scene_match_with_id.group(1).strip()
                # This regex will match scenes with or without an ID already present.
                # group(2) will be the ID if it exists.
                if scene_match_with_id.group(2):
                    outline_section_id = int(scene_match_with_id.group(2))
                    new_lines.append(line) # Preserve original line
                else:
                    outline_section_id = scene_counter
                    scene_counter += 1
                    new_line_with_id = f"{line.rstrip()} [[Scene {outline_section_id}]]"
                    new_lines.append(new_line_with_id)

                scene_info.append({
                    'outline_section_id': outline_section_id,
                    'chapter': current_chapter,
                    'scene_title': scene_title
                })
                continue

            # This second check is now redundant with the improved regex, but kept for safety.
            scene_match_without_id = scene_without_id_regex.match(line_stripped)
            if scene_match_without_id and current_chapter > 0:
                scene_title = scene_match_without_id.group(1).strip()
                outline_section_id = scene_counter
                scene_counter += 1
                new_line_with_id = f"{line.rstrip()} [[Scene {outline_section_id}]]"
                new_lines.append(new_line_with_id)
                scene_info.append({
                    'outline_section_id': outline_section_id,
                    'chapter': current_chapter,
                    'scene_title': scene_title
                })
                continue

            new_lines.append(line)

        return '\n'.join(new_lines), scene_info

    def remove_scene_ids(self, outline_text: str) -> str:
        """
        Removes scene IDs (e.g., [[Scene 123]]) from the outline text.

        Args:
            outline_text: The outline text, potentially with scene IDs.

        Returns:
            The outline text with all scene IDs removed.
        """
        # This regex finds the scene ID pattern and the whitespace before it
        # to ensure the line is cleaned up nicely.
        scene_id_regex = re.compile(r'\s*\[\[Scene\s*\d+\]\]')
        return scene_id_regex.sub('', outline_text)
    
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
    



# Global instance
bot_manager = BotManager()


def get_bot_manager() -> BotManager:
    """Get the global bot manager instance."""
    return bot_manager
