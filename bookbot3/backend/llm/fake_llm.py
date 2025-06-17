"""
Fake LLM implementation for BookBot.

This module provides a fake LLM that generates lorem ipsum text
for testing and development purposes.
"""

import random
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
        log_callback: Optional[Callable[[str], None]] = None
    ):
        """
        Initialize a fake LLM call.
        
        Args:
            model: The model name (ignored in fake implementation)
            api_key: The API key (ignored in fake implementation)
            target_word_count: Target number of words to generate
            log_callback: Optional callback for logging progress
        """
        self.model = model
        self.api_key = api_key
        self.target_word_count = target_word_count
        self.log_callback = log_callback
        
        # Optional prompt for more intelligent generation
        self.prompt: Optional[str] = None
        
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
            
            # Simulate some processing time
            time.sleep(random.uniform(0.5, 2.0))
            
            # Generate content based on prompt if available
            if hasattr(self, 'prompt') and self.prompt:
                self.output_text = self._generate_smart_content()
                words = self.output_text.split()  # For token counting
            else:
                # Generate lorem ipsum text
                words = []
                for _ in range(self.target_word_count):
                    words.append(random.choice(self.LOREM_WORDS))
                    
                    # Add some punctuation occasionally
                    if random.random() < 0.1:
                        words[-1] += random.choice(['.', ',', '!', '?'])
                    
                    # Add paragraph breaks occasionally
                    if len(words) > 20 and random.random() < 0.05:
                        words.append('\n\n')
                
                self.output_text = ' '.join(words)
            
            # Simulate token counts and costs
            self.input_tokens = random.randint(50, 200)
            self.output_tokens = len(self.output_text.split())
            self.cost = round((self.input_tokens * 0.00001 + self.output_tokens * 0.00002), 6)
            self.stop_reason = "length" if len(words) >= self.target_word_count else "stop"
            
            if self.log_callback:
                self.log_callback(f"Generated {len(words)} words, cost: ${self.cost}")
            
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
        """Generate generic structured text."""
        sections = [
            "Introduction",
            "Main Content",
            "Development",
            "Conclusion"
        ]
        
        content = []
        for section in sections:
            content.append(f"## {section}")
            content.append("")
            content.append("Lorem ipsum dolor sit amet, consectetur adipiscing elit. This section contains important information relevant to the overall structure and development of the content.")
            content.append("")
        
        return "\n".join(content)


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
