"""
Fake LLM implementation for BookBot.

This module provides a fake LLM that generates lorem ipsum text
for testing and development purposes.
"""
import os
import random
import re
import time
from typing import Optional, Callable


class FakeLLMCall:
    """Fake LLM call that generates lorem ipsum text."""
    
    LOREM_WORDS = [
        "lorem", "ipsum", "dolor", "sit", "amet", "consectetur", "adipiscing", "elit",
        "sed", "do", "eiusmod", "tempor", "incididunt", "ut", "labore", "et", "dolore",
        "magna", "aliqua", "enim", "ad", "minim", "veniam", "quis", "nostrud",
        "exercitation", "ullamco", "laboris", "nisi", "aliquip", "ex", "ea", "commodo",
        "consequat", "duis", "aute", "irure", "in", "reprehenderit", "voluptate",
        "velit", "esse", "cillum", "fugiat", "nulla", "pariatur", "excepteur", "sint",
        "occaecat", "cupidatat", "non", "proident", "sunt", "culpa", "qui", "officia",
        "deserunt", "mollit", "anim", "id", "est", "laborum", "book", "chapter",
        "story", "narrative", "character", "plot", "scene", "dialogue", "description",
        "setting", "conflict", "resolution", "theme", "metaphor", "writing", "text"
    ]
    
    def __init__(
        self,
        model: str,
        api_key: str,
        target_word_count: int,
        prompt: Optional[str] = None,  # Added prompt here
        system_prompt: Optional[str] = None,  # Added system_prompt
        llm_params: Optional[dict] = None,  # Added generic params
        log_callback: Optional[Callable[[str], None]] = None
    ):
        """
        Initialize a fake LLM call.

        Args:
            model: The model name (ignored in fake implementation)
            api_key: The API key (ignored in fake implementation)
            target_word_count: Target number of words to generate
            prompt: The user prompt for the LLM.
            system_prompt: The system prompt for the LLM.
            llm_params: Other parameters for the LLM call (e.g., temperature).
            log_callback: Optional callback for logging progress
        """
        self.model = model
        self.api_key = api_key
        self.target_word_count = target_word_count
        self.prompt = prompt  # Store prompt
        self.system_prompt = system_prompt  # Store system_prompt
        self.llm_params = llm_params if llm_params is not None else {}  # Store other params
        self.log_callback = log_callback

        # Optional prompt for more intelligent generation - this line is now covered by self.prompt
        # self.prompt: Optional[str] = None
        
        # Results (set after execute())
        self.output_text: Optional[str] = None
        self.input_tokens: int = 0
        self.output_tokens: int = 0
        self.cost: float = 0.0
        self.stop_reason: str = ""
        self.execution_time: float = 0.0
        self.error_status: Optional[str] = None
    
    def execute(self) -> bool:
        """
        Execute the fake LLM call.
        
        Returns:
            bool: True if successful, False if error
        """
        start_time = time.time()
        
        try:
            if self.log_callback:
                self.log_callback(f"Starting fake LLM generation for {self.target_word_count} words")
            
            # Simulate some processing time if not inside a unit test
            if not "PYTEST_CURRENT_TEST" in os.environ:
                custom_sleep = False
                if self.prompt:
                    match = re.search(r"seconds: (\d+)", self.prompt, re.IGNORECASE)
                    if match:
                        try:
                            sleep_duration = int(match.group(1))
                            if self.log_callback:
                                self.log_callback(f"Prompt contains 'seconds: {sleep_duration}', sleeping for {sleep_duration} seconds.")
                            time.sleep(sleep_duration)
                            custom_sleep = True
                        except ValueError:
                            if self.log_callback:
                                self.log_callback(f"Could not parse sleep duration from prompt: {match.group(1)}")
                
                if not custom_sleep:
                    time.sleep(random.uniform(0.5, 2.0))
            
            # Always attempt to generate smart content; _generate_smart_content will handle
            # empty/generic prompts by falling back to _generate_structured_text.
            self.output_text = self._generate_smart_content()
            words = self.output_text.split()  # For token counting
            
            # Simulate token counts
            input_text_for_token_calc = ""
            if self.prompt:
                input_text_for_token_calc += self.prompt
            if self.system_prompt:
                input_text_for_token_calc += (" " if input_text_for_token_calc else "") + self.system_prompt
            
            # Estimate tokens by splitting by space; add a small base if no input text
            self.input_tokens = len(input_text_for_token_calc.split()) if input_text_for_token_calc.strip() else random.randint(10, 50)
            self.output_tokens = len(self.output_text.split())
            self.stop_reason = "completed"

            # Simulate cost calculation (rates are placeholders)
            # Cost in USD, e.g., $0.000001 per input token, $0.000005 per output token
            simulated_input_token_cost_rate = 0.000001
            simulated_output_token_cost_rate = 0.000005
            self.cost = round((self.input_tokens * simulated_input_token_cost_rate) + \
                              (self.output_tokens * simulated_output_token_cost_rate), 8)
            
            # Simulate execution time
            self.execution_time = time.time() - start_time
            
            if self.log_callback:
                self.log_callback(f"Fake LLM generation complete. Output: {len(self.output_text)} chars, {self.output_tokens} tokens. Cost: ${self.cost:.6f}. Time: {self.execution_time:.2f}s")
            return True
            
        except Exception as e:
            self.error_status = str(e)
            if self.log_callback:
                self.log_callback(f"Error in fake LLM: {e}")
            return False
            
        finally:
            self.execution_time = time.time() - start_time
    
    def to_dict(self) -> dict:
        """Convert the LLM call results to a dictionary."""
        return {
            'model': self.model,
            'target_word_count': self.target_word_count,
            'output_text': self.output_text,
            'input_tokens': self.input_tokens,
            'output_tokens': self.output_tokens,
            'cost': self.cost,
            'stop_reason': self.stop_reason,
            'execution_time': self.execution_time,
            'error_status': self.error_status
        }
    
    def _generate_smart_content(self) -> str:
        """Generate content based on the prompt for more realistic testing."""
        prompt_lower = self.prompt.lower()
        
        # Detect what type of content to generate based on prompt
        if 'outline' in prompt_lower and 'chapter' in prompt_lower:
            return self._generate_outline()
        elif 'character' in prompt_lower and 'sheet' in prompt_lower:
            return self._generate_characters()
        elif 'setting' in prompt_lower or 'world' in prompt_lower:
            return self._generate_settings()
        elif 'tag' in prompt_lower and '#' in prompt_lower:
            return self._generate_tagged_content()
        else:
            # Default to structured text
            return self._generate_structured_text()
    
    def _generate_outline(self) -> str:
        """Generate a fake book outline."""
        chapters = [
            ("The Beginning", ["Hero introduced in ordinary world", "Inciting incident occurs", "Hero refuses the call"]),
            ("The Journey Starts", ["Hero accepts the call", "Mentor appears", "First threshold crossed"]),
            ("Trials and Challenges", ["Hero faces initial challenges", "New allies and enemies", "Skills are tested"]),
            ("The Ordeal", ["Major crisis point", "Hero faces greatest fear", "Apparent failure"]),
            ("Transformation", ["Hero gains new insight", "Final preparation", "Resolution begins"]),
            ("Return Home", ["Hero returns changed", "New world order", "Wisdom shared"])
        ]
        
        content = []
        scene_counter = 1
        
        for i, (chapter_title, scenes) in enumerate(chapters, 1):
            content.append(f"## Chapter {i}: {chapter_title}")
            content.append("")
            
            for scene in scenes:
                content.append(f"### Scene: {scene} [[Scene {scene_counter}]]")
                content.append(f"In this scene, the story develops as {scene.lower()}. The characters face new challenges and the plot advances significantly.")
                content.append("")
                scene_counter += 1
        
        return "\n".join(content)
    
    def _generate_characters(self) -> str:
        """Generate fake character sheets."""
        characters = [
            {
                "name": "Alex Chen",
                "role": "Protagonist",
                "age": "28",
                "description": "A determined software engineer with a mysterious past",
                "traits": "Intelligent, stubborn, compassionate",
                "goal": "To uncover the truth about their family history"
            },
            {
                "name": "Dr. Sarah Mitchell",
                "role": "Mentor",
                "age": "45",
                "description": "An experienced researcher and Alex's guide",
                "traits": "Wise, patient, secretive",
                "goal": "To help Alex while protecting dangerous secrets"
            },
            {
                "name": "Marcus Volkov",
                "role": "Antagonist",
                "age": "52",
                "description": "A powerful figure with hidden motivations",
                "traits": "Charismatic, ruthless, intelligent",
                "goal": "To maintain control and prevent the truth from emerging"
            }
        ]
        
        content = []
        for char in characters:
            content.append(f"## {char['name']} - {char['role']}")
            content.append("")
            content.append(f"**Age:** {char['age']}")
            content.append(f"**Description:** {char['description']}")
            content.append(f"**Personality:** {char['traits']}")
            content.append(f"**Primary Goal:** {char['goal']}")
            content.append("")
            content.append("**Background:** Lorem ipsum dolor sit amet, consectetur adipiscing elit. Detailed background and history will be developed here.")
            content.append("")
            content.append("**Character Arc:** The character will grow and change throughout the story, facing challenges that test their core beliefs.")
            content.append("")
        
        return "\n".join(content)
    
    def _generate_settings(self) -> str:
        """Generate fake setting descriptions."""
        settings = [
            {
                "name": "New Tokyo",
                "type": "Major City",
                "description": "A sprawling metropolis where tradition meets cutting-edge technology"
            },
            {
                "name": "The Underground Labs",
                "type": "Secret Facility",
                "description": "Hidden research complex beneath the city streets"
            },
            {
                "name": "Chen Family Apartment",
                "type": "Personal Space",
                "description": "A modest apartment filled with memories and hidden clues"
            }
        ]
        
        content = []
        for setting in settings:
            content.append(f"## {setting['name']} - {setting['type']}")
            content.append("")
            content.append(f"{setting['description']}")
            content.append("")
            content.append("**Physical Description:** Lorem ipsum dolor sit amet, consectetur adipiscing elit. Detailed visual description with sensory details.")
            content.append("")
            content.append("**Atmosphere:** The mood and feeling of this location, how it affects characters emotionally.")
            content.append("")
            content.append("**Significance:** Why this location is important to the story and character development.")
            content.append("")
        
        return "\n".join(content)
    
    def _generate_tagged_content(self) -> str:
        """Generate content with hashtags added."""
        # For tagging, we'll just add some sample tags to existing content
        sample_tags = ["#mystery", "#technology", "#family_secrets", "#urban_setting", "#character_development"]
        
        content = [
            "## Chapter 1: The Discovery #mystery #technology",
            "",
            "### Scene: Alex finds the hidden files #investigation #secrets",
            "In this scene, Alex discovers mysterious files that change everything.",
            "",
            "### Scene: First confrontation with Marcus #conflict #antagonist",
            "The first meeting between protagonist and antagonist sets the stakes.",
            "",
            "## Chapter 2: The Investigation #mystery #family_secrets",
            "",
            "### Scene: Meeting Dr. Mitchell #mentor #guidance",
            "Alex meets their mentor and begins to understand the bigger picture."
        ]
        
        return "\n".join(content)
    
    def _generate_structured_text(self) -> str:
        """Generate generic structured text, incorporating mode, bot title, and original prompt if available."""
        content_parts = []

        # Try to get mode from llm_params passed by GenerateTextJob
        mode = self.llm_params.get('mode')
        if mode:
            content_parts.append(f"Mode: {mode}")

        # Use self.prompt (original chunk text) if available, otherwise use lorem ipsum sections
        if self.prompt and self.prompt.strip():
            content_parts.append(self.prompt)
        else:
            sections = [
                "Introduction",
                "Main Content",
                "Development",
                "Conclusion"
            ]
            lorem_section_content = []
            for section in sections:
                lorem_section_content.append(f"## {section}")
                lorem_section_content.append("")
                lorem_section_content.append("Lorem ipsum dolor sit amet, consectetur adipiscing elit. This section contains important information relevant to the overall structure and development of the content.")
            content_parts.append("\n".join(lorem_section_content))

        # Try to get bot title from llm_params (specifically bot_specific_props within it)
        bot_specific_props = self.llm_params.get('bot_specific_props', {})
        bot_title = bot_specific_props.get('title', 'Unknown Bot') # Default to 'Unknown Bot' if not found
        # Ensure bot_title is a string, as it might be an object in some test setups
        if not isinstance(bot_title, str):
            # Attempt to extract common title attributes if it's an object
            if hasattr(bot_title, 'title') and isinstance(getattr(bot_title, 'title'), str):
                bot_title = getattr(bot_title, 'title')
            elif hasattr(bot_title, 'name') and isinstance(getattr(bot_title, 'name'), str):
                bot_title = getattr(bot_title, 'name')
            else:
                bot_title = 'Unknown Bot (from object)'

        content_parts.append(f"Generated by {bot_title}")
        
        return "\n\n".join(filter(None, content_parts)) # Join with double newline, filter out empty strings


def get_fake_api_token_status(api_key: str) -> dict:
    """
    Get fake API token status.
    
    Args:
        api_key: The API key to check
    
    Returns:
        dict: Status information including balance
    """
    if not api_key or api_key == "invalid":
        return {
            'valid': False,
            'error': 'Invalid API key'
        }
    
    # Return fake but realistic balance
    return {
        'valid': True,
        'balance': round(random.uniform(5.0, 100.0), 2),
        'currency': 'USD'
    }
