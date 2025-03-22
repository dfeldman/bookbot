
"""
BookBot LLM Writing Assistant Module (Doc-Based Version)

This module provides a system for generating book content using LLMs via the OpenRouter API.
It uses Doc objects for prompts, input variables, and generated content, leveraging the
existing Doc and DocRepo classes.

Components:
- BotType: Enumeration of different bot types with their required template variables
- PromptDoc: Adapter for using a Doc as a prompt template
- DocWriter: Handles the conversation with LLMs and document updates
- BookWriter: High-level interface for writing content using prompt docs

Requirements:
- Doc and DocRepo classes are assumed to be already implemented
- Doc must support get_text(), update_text(), append_text(), get_property(), set_property(),
  get_json_data(), and set_json_data() methods
"""

import os
import re
import time
import json
import logging
import requests
from datetime import datetime
from enum import Enum, auto
from typing import Dict, List, Set, Tuple, Optional, Any, Union
from pathlib import Path

# Configure logging
logger = logging.getLogger(__name__)

# Global configuration flags
DRY_RUN = os.environ.get("BOOKBOT_DRY_RUN", "").lower() in ("true", "1", "yes")
CHEAP_MODE = os.environ.get("BOOKBOT_CHEAP_MODE", "").lower() in ("true", "1", "yes")


class BotType(Enum):
    """
    Types of bots and their required template variables.
    
    Each bot type has specific template variables that must be provided
    when using the bot. The required_vars property returns the set of
    required variable names for each type.
    """
    DEFAULT = auto()           # No specific variables required
    WRITE_OUTLINE = auto()     # initial, setting, characters
    WRITE_SETTING = auto()     # initial
    WRITE_CHARACTERS = auto()  # initial, setting
    WRITE_CHAPTER = auto()     # chapter_number, outline, setting, characters, previous_chapter
    WRITE_SECTION = auto()     # section_number, chapter_number, section_outline, setting, characters, previous_section
    SPLIT_OUTLINE = auto()     # outline
    SPLIT_CHAPTER = auto()     # chapter_outline
    REVIEW_COMMONS = auto()    # initial, setting, characters, content
    REVIEW_CHAPTER = auto()    # content, outline, setting, characters
    EDIT_CHAPTER = auto()      # outline, setting, characters, review, content
    REVIEW_WHOLE = auto()      # content
    SELF_EDIT = auto()         # initial, characters, setting, content
    
    @property
    def required_vars(self) -> Set[str]:
        """
        Get required template variables for this bot type.
        
        Returns:
            Set[str]: Set of variable names required for this bot type
        """
        return {
            BotType.DEFAULT: set(),
            BotType.WRITE_OUTLINE: {"initial", "setting", "characters"},
            BotType.WRITE_SETTING: {"initial"},
            BotType.WRITE_CHARACTERS: {"initial", "setting"},
            BotType.WRITE_CHAPTER: {"chapter_number", "outline", "setting", "characters", "previous_chapter"},
            BotType.WRITE_SECTION: {"section_number", "chapter_number", "section_outline", "setting", "characters", "previous_section"},
            BotType.SPLIT_OUTLINE: {"outline"},
            BotType.SPLIT_CHAPTER: {"chapter_outline"},
            BotType.REVIEW_COMMONS: {"initial", "setting", "characters", "content"},
            BotType.REVIEW_CHAPTER: {"content", "outline", "setting", "characters"},
            BotType.EDIT_CHAPTER: {"outline", "setting", "characters", "review", "content"},
            BotType.REVIEW_WHOLE: {"content"},
            BotType.SELF_EDIT: {"initial", "characters", "setting", "content"}
        }[self]


class BookBotError(Exception):
    """Base exception for all BookBot errors"""
    pass


class LLMError(BookBotError):
    """
    Errors related to LLM API calls.
    
    This exception provides detailed information about API call failures,
    including the HTTP status code and response content when available.
    """
    def __init__(self, message: str, response: Optional[requests.Response] = None):
        super().__init__(message)
        self.response = response
        self.response_json = None
        
        if response is not None:
            try:
                self.response_json = response.json()
            except json.JSONDecodeError:
                self.response_text = response.text if response.text else None

    def __str__(self) -> str:
        """Create a detailed string representation including response details when available."""
        base_msg = super().__str__()
        if not self.response:
            return base_msg
            
        status = f"HTTP {self.response.status_code}"
        
        if self.response_json:
            if isinstance(self.response_json, dict):
                if 'error' in self.response_json:
                    error_msg = self.response_json['error'].get('message', 'Unknown error')
                    error_type = self.response_json['error'].get('type', 'Unknown type')
                    return f"{base_msg}: {status} - [{error_type}] {error_msg}"
                elif 'message' in self.response_json:
                    return f"{base_msg}: {status} - {self.response_json['message']}"
            return f"{base_msg}: {status} - {str(self.response_json)}"
        
        if hasattr(self, 'response_text') and self.response_text:
            return f"{base_msg}: {status} - {self.response_text[:200]}..."
            
        return f"{base_msg}: {status}"


class PromptDoc:
    """
    Adapter class for using a Doc as a prompt template.
    
    This class wraps a Doc object that contains bot configuration and prompts.
    It parses the document content to extract configuration values and prompt
    templates, providing a structured interface for working with prompt documents.
    
    The expected document format is:
    
    ```
    # Bot Configuration
    
    bot_type: WRITE_CHAPTER
    llm: writer
    temperature: 0.7
    
    # System Prompt
    
    You are an expert fiction writer...
    
    # Main Prompt
    
    Write Chapter {chapter_number}...
    
    # Continuation Prompt
    
    Continue writing Chapter {chapter_number}...
    ```
    """
    
    def __init__(self, doc):
        """
        Initialize a PromptDoc with an existing Doc object.
        
        Args:
            doc: The Doc object containing prompt configuration
            
        Raises:
            ValueError: If the Doc doesn't have a valid prompt structure
        """
        self.doc = doc
        self._parse_prompt_doc()
    
    def _parse_prompt_doc(self):
        """
        Parse the document content to extract configuration and prompts.
        
        Raises:
            ValueError: If the document doesn't have a valid prompt structure
        """
        text = self.doc.get_text()
        
        # Extract configuration section
        config_section = self._extract_section(text, "Bot Configuration")
        if not config_section:
            raise ValueError(f"Missing 'Bot Configuration' section in prompt document {self.doc.name}")
        
        # Parse configuration properties
        config = {}
        for line in config_section.strip().split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                config[key.strip()] = self._parse_value(value.strip())
        
        # Extract required bot_type
        if 'bot_type' not in config:
            raise ValueError(f"Missing 'bot_type' in prompt document {self.doc.name}")
        
        try:
            self.bot_type = BotType[config['bot_type'].upper()]
        except KeyError:
            raise ValueError(f"Invalid bot_type '{config['bot_type']}' in prompt document {self.doc.name}")
        
        # Set configuration properties
        self._raw_llm = config.get('llm', 'writer')
        self.llm = self._resolve_llm_alias(self._raw_llm)
        self.input_price = float(config.get('input_price', 0.5))
        self.output_price = float(config.get('output_price', 1.5))
        self.provider = config.get('provider')
        self.temperature = float(config.get('temperature', 0.7))
        self.expected_length = int(config.get('expected_length', 2000))
        self.context_window = int(config.get('context_window', 4096))
        self.max_continuations = int(config.get('max_continuations', 10))
        
        # Extract prompt sections
        self.system_prompt = self._extract_section(text, "System Prompt")
        self.main_prompt = self._extract_section(text, "Main Prompt")
        self.continuation_prompt = self._extract_section(text, "Continuation Prompt")
        
        # Validate required sections
        if not self.system_prompt:
            raise ValueError(f"Missing 'System Prompt' section in {self.doc.name}")
        if not self.main_prompt:
            raise ValueError(f"Missing 'Main Prompt' section in {self.doc.name}")
        if not self.continuation_prompt:
            raise ValueError(f"Missing 'Continuation Prompt' section in {self.doc.name}")
        
        # Validate template variables
        self._validate_template_vars()
    
    def _extract_section(self, text, section_name):
        """
        Extract a section from the document text.
        
        Args:
            text: The document text
            section_name: The section name to extract
            
        Returns:
            The section content or empty string if not found
        """
        pattern = rf'# {re.escape(section_name)}\s*\n(.*?)(?=\n# |\Z)'
        match = re.search(pattern, text, re.DOTALL)
        return match.group(1).strip() if match else ""
    
    def _parse_value(self, value):
        """
        Parse a configuration value string.
        
        Args:
            value: The value string
            
        Returns:
            The parsed value (bool, int, float, or str)
        """
        # Try boolean
        if value.lower() == 'true':
            return True
        if value.lower() == 'false':
            return False
        
        # Try number
        try:
            if '.' in value:
                return float(value)
            return int(value)
        except ValueError:
            # String
            return value
    
    def _resolve_llm_alias(self, llm):
        """
        Resolve LLM model aliases to actual model names.
        
        Args:
            llm: LLM identifier or alias
            
        Returns:
            Resolved LLM model name
        """
        if CHEAP_MODE:
            logger.info(f"CHEAP_MODE enabled, using Gemini Flash instead of {llm}")
            return "google/gemini-2.0-flash-001"
            
        # Handle specific aliases
        if llm == "longcontext":
            return "google/gemini-2.0-pro-001"
        elif llm == "writer":
            return "deepseek-ai/deepseek-coder-v2-r-chat"
        elif llm == "outliner":
            return "anthropic/claude-3-5-sonnet-20240620"
        
        # Use the original value if not an alias
        return llm
    
    def _validate_template_vars(self):
        """
        Validate that the prompt templates include all required variables.
        
        Raises:
            ValueError: If required variables are missing
        """
        main_vars = extract_template_vars(self.main_prompt)
        cont_vars = extract_template_vars(self.continuation_prompt)
        found_vars = main_vars.union(cont_vars)
        
        required_vars = self.bot_type.required_vars
        missing_vars = required_vars - found_vars
        
        if missing_vars:
            raise ValueError(f"Missing required template variables in {self.doc.name}: {missing_vars}")
    
    def validate_template_vars(self, variables):
        """
        Validate that all required template variables are provided.
        
        Args:
            variables: Dictionary of template variables
            
        Raises:
            ValueError: If required variables are missing
        """
        # Check for missing variables
        required = self.bot_type.required_vars
        missing = required - set(variables.keys())
        if missing:
            raise ValueError(f"Missing required template variables for {self.bot_type}: {missing}")
            
        # Check for empty variables
        empty_vars = []
        for key in required:
            if key not in variables:
                continue
                
            value = variables[key]
            if hasattr(value, 'get_text'):
                # It's a Doc object
                if not value.get_text().strip():
                    empty_vars.append(key)
            elif not str(value).strip():
                empty_vars.append(key)
                
        if empty_vars:
            raise ValueError(f"Empty required template variables for {self.bot_type}: {empty_vars}")
    
    def get_provider_config(self):
        """
        Get provider configuration for OpenRouter API.
        
        Returns:
            Provider configuration dictionary
        """
        if not self.provider:
            return {"sort": "price"}
        else:
            return {"order": [self.provider]}
    
    def to_dict(self):
        """
        Convert the prompt configuration to a dictionary.
        
        Returns:
            Dictionary with configuration details
        """
        return {
            "name": self.doc.name,
            "type": self.bot_type.name,
            "llm": self.llm,
            "raw_llm": self._raw_llm,
            "provider": self.provider,
            "input_price": self.input_price,
            "output_price": self.output_price,
            "temperature": self.temperature,
            "expected_length": self.expected_length,
            "context_window": self.context_window,
            "max_continuations": self.max_continuations,
            "required_vars": list(self.bot_type.required_vars),
            "version": self.doc.get_property("version", 1)
        }
    
    def __str__(self):
        """String representation of the prompt doc"""
        return f"PromptDoc({self.doc.name}, type={self.bot_type.name}, llm={self.llm}, version={self.doc.get_property('version', 1)})"


class DocWriter:
    """
    Handles the conversation with an LLM and updates a document with generated content.
    
    This class uses a PromptDoc for the configuration and templates, processes
    template variables (including Doc objects), makes API calls to OpenRouter,
    and updates the output document with the generated content and metadata.
    """
    
    def __init__(self, prompt_doc, output_doc, api_key, template_vars, command="generate"):
        """
        Initialize a DocWriter.
        
        Args:
            prompt_doc: PromptDoc containing configuration and templates
            output_doc: Doc to write output to
            api_key: OpenRouter API key
            template_vars: Dictionary of template variables (strings or Doc objects)
            command: Command name for logging
        """
        self.prompt_doc = prompt_doc
        self.output_doc = output_doc
        self.api_key = api_key
        self.template_vars = template_vars
        self.command = command
        self.messages = []
        self.stats = {
            "input_tokens": 0,
            "output_tokens": 0,
            "time": 0,
            "calls": []
        }
        self.error = None
        self.processed_vars = {}
        self.doc_references = {}
        
        # Process template variables
        self._process_template_vars()
        
        # Load existing document stats
        self._load_existing_stats()
        
        logger.info(f"Initialized DocWriter with prompt '{prompt_doc.doc.name}' for output '{output_doc.name}'")
    
    def _process_template_vars(self):
        """
        Process template variables, extracting content from Doc objects.
        
        This also records document references with versions.
        """
        # Store reference to the prompt doc
        prompt_version = self.prompt_doc.doc.get_property('version', 1)
        self.doc_references["prompt"] = f"{self.prompt_doc.doc.name}#{prompt_version}"
        
        # Process each template variable
        for key, value in self.template_vars.items():
            if hasattr(value, 'get_text') and callable(getattr(value, 'get_text')):
                # It's a Doc object
                doc_obj = value
                doc_version = doc_obj.get_property('version', 1)
                
                # Store reference with version
                self.doc_references[key] = f"{doc_obj.name}#{doc_version}"
                
                # Get text content
                self.processed_vars[key] = doc_obj.get_text()
            else:
                # It's a string or other value
                self.processed_vars[key] = str(value)
        
        # Log document references
        if self.doc_references:
            logger.info(f"Document references: {self.doc_references}")
            references_str = ", ".join([f"{k}: {v}" for k, v in self.doc_references.items()])
            self.output_doc.set_property("references", references_str)
    
    def _load_existing_stats(self):
        """Load existing statistics from the output document."""
        self.stats["previous_input_tokens"] = self.output_doc.get_property("input_tokens", 0)
        self.stats["previous_output_tokens"] = self.output_doc.get_property("output_tokens", 0)
        self.stats["previous_time"] = self.output_doc.get_property("total_time", 0)
        self.stats["previous_continuation_count"] = self.output_doc.get_property("total_continuation_count", 0)
    
    def _update_doc_stats(self):
        """Update document properties with current statistics."""
        # Update document properties
        self.output_doc.set_property("input_tokens", self.stats["input_tokens"])
        self.output_doc.set_property("output_tokens", self.stats["output_tokens"])
        self.output_doc.set_property("time", self.stats["time"])
        self.output_doc.set_property("continuation_count", len(self.stats["calls"]))
        self.output_doc.set_property("command", self.command)
        self.output_doc.set_property("prompt_doc", self.prompt_doc.doc.name)
        self.output_doc.set_property("llm", self.prompt_doc.llm)
        self.output_doc.set_property("timestamp", datetime.now().isoformat())
        
        # Update cumulative stats
        self.output_doc.set_property("total_input_tokens", 
                             self.stats.get("previous_input_tokens", 0) + self.stats["input_tokens"])
        self.output_doc.set_property("total_output_tokens", 
                             self.stats.get("previous_output_tokens", 0) + self.stats["output_tokens"])
        self.output_doc.set_property("total_time", 
                             self.stats.get("previous_time", 0) + self.stats["time"])
        self.output_doc.set_property("total_continuation_count", 
                             self.stats.get("previous_continuation_count", 0) + len(self.stats["calls"]))
    
    def _update_doc_json(self):
        """Update the document's JSON data with messages, stats, and references."""
        json_data = self.output_doc.get_json_data()
        
        # Store conversation history
        json_data["messages"] = self.messages
        json_data["stats"] = self.stats
        
        # Store document references
        json_data["doc_references"] = self.doc_references
        
        # Store template variables
        json_data["template_vars"] = self.processed_vars
        
        # Store prompt information
        json_data["prompt"] = {
            "name": self.prompt_doc.doc.name,
            "type": self.prompt_doc.bot_type.name,
            "llm": self.prompt_doc.llm,
            "version": self.prompt_doc.doc.get_property("version", 1)
        }
        
        self.output_doc.set_json_data(json_data)
    
    def _clean_content(self, content):
        """
        Clean continuation markers and think tags from content.
        
        Args:
            content: Raw content to clean
            
        Returns:
            Cleaned content
        """
        if not content:
            return ""
            
        # Remove CONTINUE markers at end
        continuation_markers = ["CONTINUE\n", "**CONTINUE**\n", "CONTINUE", "**CONTINUE**"]
        for marker in continuation_markers:
            if content.endswith(marker):
                content = content[:-len(marker)].strip()
                break
            
        # Remove think tags if present
        content = re.sub(r'<think>.*?</think>\n?', '', content, flags=re.DOTALL)
        
        return content.strip()
    
    def _call_openrouter_api(self, messages, retry=0):
        """
        Call the OpenRouter API with retry logic.
        
        Args:
            messages: List of message dictionaries
            retry: Current retry count
            
        Returns:
            Tuple of (content, input_tokens, output_tokens, finish_reason, generation_id)
            
        Raises:
            LLMError: If the API call fails after max retries
        """
        max_retries = 3
        api_url = "https://openrouter.ai/api/v1/chat/completions"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "http://localhost:3000",
            "X-Title": "BookBot",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": self.prompt_doc.llm,
            "messages": messages,
            "temperature": self.prompt_doc.temperature,
            "provider": self.prompt_doc.get_provider_config()
        }
        
        try:
            logger.info(f"Making OpenRouter API call ({self.command})")
            logger.debug(f"Request data: {json.dumps(data, indent=2)}")
            
            # Check if we're in dry run mode
            if DRY_RUN:
                logger.info("DRY_RUN mode enabled, simulating API response")
                
                # Simulate token counts based on input length
                prompt_tokens = sum(len(m.get('content', '').split()) for m in messages)
                
                # Generate a simulated response based on bot type
                bot_type = self.prompt_doc.bot_type.name
                simulated_content = f"[DRY RUN] Simulated content for {bot_type} bot, command: {self.command}\n\n"
                
                if "WRITE" in bot_type:
                    simulated_content += "# Generated Content\n\nThis is simulated output for a writing task.\n\n"
                    simulated_content += "Lorem ipsum dolor sit amet, consectetur adipiscing elit.\n\n"
                    simulated_content += "THE END"
                elif "REVIEW" in bot_type:
                    simulated_content += "# Review Comments\n\n- Point one: This is good\n- Point two: Consider improving this\n\nTHE END"
                elif "OUTLINE" in bot_type:
                    simulated_content += "# Outline\n\n## Chapter 1\n- Introduction\n\n## Chapter 2\n- Plot development\n\nTHE END"
                else:
                    simulated_content += "Generic simulated content for testing purposes.\n\nTHE END"
                
                # Calculate simulated token counts
                completion_tokens = len(simulated_content.split())
                
                # Return the simulated response
                return simulated_content, prompt_tokens, completion_tokens, "stop", "dry-run-gen-id"
            
            # Make the actual API call
            start_time = time.time()
            response = requests.post(
                api_url,
                headers=headers,
                json=data,
                timeout=60
            )
            elapsed = time.time() - start_time
            
            # Handle non-200 responses
            if response.status_code != 200:
                if response.status_code == 429 and retry < max_retries:  # Rate limit
                    wait_time = int(response.headers.get('Retry-After', 5 * (retry + 1)))
                    logger.warning(f"Rate limited. Waiting {wait_time}s (retry {retry + 1}/{max_retries})")
                    #time.sleep(wait_time) #Disable wait for now. TODO add back while fixing tests
                    return self._call_openrouter_api(messages, retry + 1)
                else:
                    raise LLMError(f"Error response ({response.status_code})", response)
            
            # Parse JSON response
            try:
                result = response.json()
            except json.JSONDecodeError:
                if retry < max_retries:
                    wait_time = 2 ** retry
                    logger.warning(f"Invalid JSON response. Retrying in {wait_time}s (retry {retry + 1}/{max_retries})")
                    #time.sleep(wait_time)mTODO #Disable wait for now. TODO add back while fixing tests
                    return self._call_openrouter_api(messages, retry + 1)
                raise LLMError("Invalid JSON response", response)
            
            # Check for API errors
            if result.get("error"):
                error_message = result["error"].get("message", "Unknown API error")
                
                # Handle out of credits error
                if "more credits are required" in error_message.lower():
                    logger.error("Out of credits. Please add credits to your OpenRouter account.")
                    raise LLMError("Out of credits. Please add credits to your OpenRouter account.", response)
                
                # Handle other API errors with retry
                if retry < max_retries:
                    wait_time = 2 ** retry
                    logger.warning(f"API error: {error_message}. Retrying in {wait_time}s (retry {retry + 1}/{max_retries})")
                    #time.sleep(wait_time)
                    return self._call_openrouter_api(messages, retry + 1)
                raise LLMError(f"API error: {error_message}", response)
            
            # Extract content from response
            if not result.get('choices'):
                if retry < max_retries:
                    wait_time = 2 ** retry
                    logger.warning(f"No choices in response. Retrying in {wait_time}s (retry {retry + 1}/{max_retries})")
                    #time.sleep(wait_time)
                    return self._call_openrouter_api(messages, retry + 1)
                raise LLMError("No choices in API response", response)
            
            content = result["choices"][0]["message"].get("content", "")
            if not content or content.isspace():
                if retry < max_retries:
                    wait_time = 2 ** retry
                    logger.warning(f"Empty content received. Retrying in {wait_time}s (retry {retry + 1}/{max_retries})")
                    #time.sleep(wait_time)
                    return self._call_openrouter_api(messages, retry + 1)
                raise LLMError("Empty response content", response)
            
            # Get finish reason
            finish_reason = result["choices"][0].get("finish_reason", 
                           result["choices"][0].get("native_finish_reason", "unknown"))
            
            # Get token counts
            usage = result.get("usage", {})
            input_tokens = usage.get("prompt_tokens", 0)
            output_tokens = usage.get("completion_tokens", 0)
            
            # Get generation ID
            generation_id = result.get("id")
            
            # Log success details
            words = len(content.split())
            logger.info(f"Response stats: {len(content)}b/{words}w/{output_tokens}t in {elapsed:.1f}s")
            
            # Record call stats
            call_stats = {
                "timestamp": datetime.now().isoformat(),
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "elapsed": elapsed,
                "retry": retry,
                "provider": result.get("provider", "unknown"),
                "model": result.get("model", self.prompt_doc.llm),
                "generation_id": generation_id
            }
            self.stats["calls"].append(call_stats)
            self.stats["input_tokens"] += input_tokens
            self.stats["output_tokens"] += output_tokens
            self.stats["time"] += elapsed
            
            return content, input_tokens, output_tokens, finish_reason, generation_id
            
        except requests.exceptions.Timeout:
            if retry < max_retries:
                wait_time = 5 * (retry + 1)
                logger.warning(f"API request timed out. Retrying in {wait_time}s (retry {retry + 1}/{max_retries})")
                # time.sleep(wait_time) #TODO add back
                return self._call_openrouter_api(messages, retry + 1)
            raise LLMError("API request timed out after multiple retries")
        
        except requests.exceptions.ConnectionError:
            if retry < max_retries:
                wait_time = 5 * (retry + 1)
                logger.warning(f"Connection error. Retrying in {wait_time}s (retry {retry + 1}/{max_retries})")
                #time.sleep(wait_time) #TODO add back
                return self._call_openrouter_api(messages, retry + 1)
            raise LLMError("Connection error persisted after multiple retries")
        
        except Exception as e:
            if retry < max_retries:
                wait_time = 2 ** retry
                logger.warning(f"Unexpected error: {str(e)}. Retrying in {wait_time}s (retry {retry + 1}/{max_retries})")
                # time.sleep(wait_time) #TODO add back
                return self._call_openrouter_api(messages, retry + 1)
            raise LLMError(f"Failed to call OpenRouter API: {str(e)}")
    
    def _query_generation_cost(self, generation_id):
        """
        Query the OpenRouter API for the cost of a specific generation.
        
        Args:
            generation_id: Generation ID to query
            
        Returns:
            Cost in dollars or 0 if unavailable
        """
        if DRY_RUN:
            logger.info("DRY_RUN mode enabled, skipping cost query")
            return 0.0
            
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            url = f"https://openrouter.ai/api/v1/generation?id={generation_id}"
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                cost = data.get("data", {}).get("total_cost", 0)
                logger.info(f"Generation cost: ${cost:.6f}")
                return cost
            else:
                logger.warning(f"Failed to get generation cost: HTTP {response.status_code}")
                return 0.0
                
        except Exception as e:
            logger.warning(f"Error querying generation cost: {str(e)}")
            return 0.0
    
    def generate(self):
        """
        Generate content using the prompt doc and update the output doc.
        
        Returns:
            The generated content
            
        Raises:
            ValueError: If template variables are invalid
            LLMError: If the API call fails
        """
        try:
            # Validate template variables
            self.prompt_doc.validate_template_vars(self.template_vars)
            
            # Initialize messages with system prompt
            self.messages = [
                {"role": "system", "content": self.prompt_doc.system_prompt},
                {"role": "user", "content": (
                    self.prompt_doc.main_prompt.format(**self.processed_vars) +
                    f"\n\nWrite one chunk of content. Write as much as you wish, and end your output with CONTINUE to have the chance to " +
                    "continue writing in a new chunk of content. CONTINUE must be at the end of your message if you want to write more than one chunk of content. " +
                    f"Write THE END if this chunk concludes the section. You can write as much or as little as you wish, but typically aim for around {self.prompt_doc.expected_length} words. " +
                    "If you CONTINUE, you'll get a current word count of how much you've written so far. You should ALWAYS write at least two chunks."
                )}
            ]
            
            # Track accumulated content
            accumulated_content = []
            continuation_count = 0
            generation_ids = []
            
            # Update the output document with initial status
            self.output_doc.set_property("status", "generating")
            self.output_doc.set_property("start_time", datetime.now().isoformat())
            
            # Generate content through multiple API calls if needed
            while continuation_count < self.prompt_doc.max_continuations:
                continuation_count += 1
                logger.info(f"Making API call {continuation_count}/{self.prompt_doc.max_continuations} for {self.command}")
                
                # Make API call
                content, input_tokens, output_tokens, finish_reason, generation_id = self._call_openrouter_api(self.messages)
                
                # Store generation ID for cost query
                if generation_id:
                    generation_ids.append(generation_id)
                
                # Clean the content
                cleaned_content = self._clean_content(content)
                accumulated_content.append(cleaned_content)
                
                # Calculate total words written
                total_words = sum(len(chunk.split()) for chunk in accumulated_content)
                logger.info(f"Total words written: {total_words}")
                
                # Update conversation history
                self.messages.append({"role": "assistant", "content": content})
                
                # Update output document with current content
                full_content = "\n".join(accumulated_content)
                if continuation_count == 1:
                    # First iteration: set the content
                    self.output_doc.update_text(full_content)
                else:
                    # Subsequent iterations: update the content
                    # Note: Using update_text instead of append_text to create proper version history
                    self.output_doc.update_text(full_content)
                
                # Update document properties
                self.output_doc.set_property("word_count", total_words)
                self.output_doc.set_property("continuation_count", continuation_count)
                self._update_doc_stats()
                
                # Update document JSON with messages and references
                self._update_doc_json()
                
                # Check if we're done
                if "THE END" in content or finish_reason in ["stop", "length", "content_filter"]:
                    logger.info(f"Finished generation: {finish_reason}")
                    break
                
                # If not done, add continuation prompt
                continuation_prompt = self.prompt_doc.continuation_prompt.format(
                    current_words=total_words,
                    expected_words=self.prompt_doc.expected_length,
                    **self.processed_vars  # Include all template variables for the continuation
                )
                continuation_prompt += (
                    "\n\nWhen you're done with this chunk of text, write CONTINUE, and then end your message. " +
                    "Then you'll get a new prompt to continue writing. " +
                    "Don't write CONTINUE in the middle of your output, that *WILL NOT* help you write more. " +
                    "Only write it at the end of your output in order to get a new prompt where you can continue writing. " +
                    "Write THE END when you're done writing. CONTINUE or THE END *MUST* be at the end of your output."
                )
                self.messages.append({"role": "user", "content": continuation_prompt})
                logger.info("Added continuation prompt")
            
            # Clean and store final text
            if accumulated_content:
                final_text = "\n".join(accumulated_content)
                
                # Make any final tweaks to the text
                if "THE END" in final_text:
                    final_text = final_text.split("THE END")[0].strip()
                
                # Update the document with final content
                self.output_doc.update_text(final_text)
                
                # Update final stats
                self.output_doc.set_property("word_count", len(final_text.split()))
                self.output_doc.set_property("status", "complete")
                self.output_doc.set_property("end_time", datetime.now().isoformat())
                self._update_doc_stats()
                
                # Final update to document JSON
                self._update_doc_json()
                
                # Try to get the cost
                if not DRY_RUN and generation_ids:
                    # Get the generation ID from the first response
                    generation_id = generation_ids[0]
                    cost = self._query_generation_cost(generation_id)
                    self.output_doc.set_property("cost", cost)
                
                # Log final statistics
                logger.info(f"Generation complete for {self.command}")
                logger.info(f"Final length: {len(final_text.split())} words")
                logger.info(f"Total tokens: {self.stats['input_tokens']} in, {self.stats['output_tokens']} out")
                
                return final_text
            else:
                error_msg = "No content was generated"
                logger.error(error_msg)
                self.output_doc.set_property("status", "error")
                self.output_doc.set_property("error", error_msg)
                
                # Update document JSON with error
                json_data = self.output_doc.get_json_data()
                json_data["error"] = error_msg
                self.output_doc.set_json_data(json_data)
                
                raise LLMError(error_msg)
            
        except Exception as e:
            logger.error(f"Error in generation: {str(e)}")
            self.error = e
            
            # Update document with error information
            self.output_doc.set_property("status", "error")
            self.output_doc.set_property("error", str(e))
            self.output_doc.set_property("end_time", datetime.now().isoformat())
            
            # Update document JSON with error
            json_data = self.output_doc.get_json_data()
            json_data["error"] = str(e)
            json_data["messages"] = self.messages
            json_data["stats"] = self.stats
            self.output_doc.set_json_data(json_data)
            
            raise


class MockDocWriter:
    """
    Mock version of DocWriter for testing without making API calls.
    
    This class implements the same interface as DocWriter but doesn't
    actually call any external API, making it suitable for testing.
    """
    
    def __init__(self, prompt_doc, output_doc, api_key, template_vars, command="generate"):
        """
        Initialize a MockDocWriter.
        
        Args:
            prompt_doc: PromptDoc containing configuration and templates
            output_doc: Doc to write output to
            api_key: OpenRouter API key (not used)
            template_vars: Dictionary of template variables (strings or Doc objects)
            command: Command name for logging
        """
        self.prompt_doc = prompt_doc
        self.output_doc = output_doc
        self.api_key = api_key
        self.template_vars = template_vars
        self.command = command
        self.messages = []
        self.stats = {
            "input_tokens": 100,
            "output_tokens": 200,
            "time": 1.5,
            "calls": [
                {
                    "timestamp": datetime.now().isoformat(),
                    "input_tokens": 100,
                    "output_tokens": 200,
                    "elapsed": 1.5,
                    "retry": 0,
                    "provider": "test-provider",
                    "model": "test-model"
                }
            ]
        }
        self.error = None
        self.processed_vars = {}
        self.doc_references = {}
        
        # Process template variables
        self._process_template_vars()
        
        logger.info(f"Initialized MockDocWriter for {output_doc.name}")
    
    def _process_template_vars(self):
        """
        Process template variables, extracting content from Doc objects.
        
        This also records document references with versions.
        """
        # Store reference to the prompt doc
        prompt_version = self.prompt_doc.doc.get_property('version', 1)
        self.doc_references["prompt"] = f"{self.prompt_doc.doc.name}#{prompt_version}"
        
        # Process each template variable
        for key, value in self.template_vars.items():
            if hasattr(value, 'get_text') and callable(getattr(value, 'get_text')):
                # It's a Doc object
                doc_obj = value
                doc_version = doc_obj.get_property('version', 1)
                
                # Store reference with version
                self.doc_references[key] = f"{doc_obj.name}#{doc_version}"
                
                # Get text content
                self.processed_vars[key] = doc_obj.get_text()
            else:
                # It's a string or other value
                self.processed_vars[key] = str(value)
        
        # Log document references
        if self.doc_references:
            logger.info(f"Document references: {self.doc_references}")
            references_str = ", ".join([f"{k}: {v}" for k, v in self.doc_references.items()])
            self.output_doc.set_property("references", references_str)
    
    def generate(self):
        """
        Generate mock content without making API calls.
        
        Returns:
            Mock generated content
            
        Raises:
            ValueError: If template variables are invalid
        """
        # Validate template variables
        self.prompt_doc.validate_template_vars(self.template_vars)
        
        # Generate mock content based on bot type
        bot_type = self.prompt_doc.bot_type.name
        content = f"Mock content for {bot_type} bot.\n\n"
        
        if "WRITE" in bot_type:
            # [DRY RUN] is used in the unit test to check this code is running
            content += "# Generated Content\n\n[DRY RUN] This is mock output for a writing task.\n\n"
            content += "Lorem ipsum dolor sit amet, consectetur adipiscing elit.\n\n"
        elif "REVIEW" in bot_type:
            content += "# Review Comments\n\n- Point one: Good structure\n- Point two: Improve descriptions\n\nOverall rating: 7/10\n\n"
        elif "OUTLINE" in bot_type:
            content += "# Outline\n\n## Chapter 1\n- Setup\n\n## Chapter 2\n- Conflict\n\n"
        
        # Create mock system and user messages
        self.messages = [
            {"role": "system", "content": self.prompt_doc.system_prompt},
            {"role": "user", "content": self.prompt_doc.main_prompt.format(**self.processed_vars)},
            {"role": "assistant", "content": content}
        ]
        
        # Update the document
        self.output_doc.update_text(content)
        
        # Update document properties
        self.output_doc.set_property("word_count", len(content.split()))
        self.output_doc.set_property("status", "complete")
        self.output_doc.set_property("input_tokens", self.stats["input_tokens"])
        self.output_doc.set_property("output_tokens", self.stats["output_tokens"])
        self.output_doc.set_property("time", self.stats["time"])
        self.output_doc.set_property("prompt_doc", self.prompt_doc.doc.name)
        self.output_doc.set_property("command", self.command)
        
        # Update document JSON
        json_data = self.output_doc.get_json_data()
        json_data["messages"] = self.messages
        json_data["stats"] = self.stats
        json_data["doc_references"] = self.doc_references
        json_data["template_vars"] = self.processed_vars
        json_data["prompt"] = {
            "name": self.prompt_doc.doc.name,
            "type": self.prompt_doc.bot_type.name,
            "llm": self.prompt_doc.llm,
            "version": self.prompt_doc.doc.get_property("version", 1)
        }
        self.output_doc.set_json_data(json_data)
        
        return content


def extract_template_vars(text):
    """
    Extract all template variables from a text string.
    Variables are in the format {variable_name}
    
    Args:
        text: The text containing template variables
        
    Returns:
        Set of variable names found in the text
    """
    import re
    matches = re.findall(r'\{([^}]+)\}', text)
    return set(matches)


def format_price(input_tokens, output_tokens, input_price, output_price):
    """
    Format price based on token usage.
    
    Args:
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens
        input_price: Price per million input tokens
        output_price: Price per million output tokens
        
    Returns:
        Formatted price string
    """
    input_cost = input_tokens * (input_price / 1000000)
    output_cost = output_tokens * (output_price / 1000000)
    total_cost = input_cost + output_cost
    return f"${total_cost:.6f} (${input_cost:.6f} + ${output_cost:.6f})"


def create_prompt_doc_template(doc_repo, name, bot_type):
    """
    Create a template prompt document with the specified bot type.
    
    Args:
        doc_repo: Document repository
        name: Name for the new prompt document
        bot_type: Type of bot to create (BotType enum)
        
    Returns:
        Created Doc object
    """
    props = {
        "type": "prompt",
        "bot_type": bot_type.name
    }
    
    # Create the document with template content
    doc = doc_repo.create_doc(name, initial_properties=props)
    
    # Determine variable placeholders based on bot type
    var_examples = {}
    for var in bot_type.required_vars:
        var_examples[var] = f"{{{var}}}"
    
    # Create template content
    content = f"""# Bot Configuration

bot_type: {bot_type.name}
llm: writer
input_price: 0.5
output_price: 1.5
temperature: 0.7
expected_length: 2000
context_window: 8192
max_continuations: 5

# System Prompt

You are an assistant specialized in {bot_type.name.lower().replace('_', ' ')} tasks.
Provide helpful, high-quality content based on the provided inputs.

# Main Prompt

{' '.join(f"{k}: {v}" for k, v in var_examples.items())}

# Continuation Prompt

Continue writing based on the above information and what you've already written.
Current progress: {{current_words}} words out of {{expected_words}} expected words.
"""
    
    # Update the document with the template content
    doc.update_text(content)
    
    return doc


class BookWriter:
    """
    High-level interface for generating book content using prompt documents.
    
    This class manages prompt documents and content generation, providing
    methods for creating prompts and generating content with them.
    """
    
    def __init__(self, doc_repo, api_key=None, logger=None):
        """
        Initialize a BookWriter.
        
        Args:
            doc_repo: Document repository (DocRepo instance)
            api_key: OpenRouter API key (if None, will look for OPENROUTER_API_KEY env var)
            logger: Optional logger instance
        """
        self.doc_repo = doc_repo
        self.api_key = api_key or os.environ.get("OPENROUTER_API_KEY")
        self.logger = logger or logging.getLogger(__name__)
        
        if not self.api_key:
            self.logger.warning("No OpenRouter API key provided. Set OPENROUTER_API_KEY environment variable or pass api_key parameter.")
    
    def get_prompt_doc(self, name):
        """
        Get a prompt document by name.
        
        Args:
            name: Name of the prompt document
            
        Returns:
            PromptDoc instance or None if not found
            
        Raises:
            ValueError: If the document exists but is not a valid prompt document
        """
        doc = self.doc_repo.get_doc(name)
        if not doc:
            return None
        
        # Verify that it's a prompt document
        if doc.get_property("type") != "prompt":
            raise ValueError(f"Document '{name}' exists but is not a prompt document")
        
        try:
            return PromptDoc(doc)
        except ValueError as e:
            self.logger.error(f"Invalid prompt document '{name}': {str(e)}")
            raise ValueError(f"Document '{name}' is not a valid prompt document: {str(e)}")
    
    def create_prompt(self, name, bot_type):
        """
        Create a new prompt document with the specified bot type.
        
        Args:
            name: Name for the new prompt document
            bot_type: Type of bot to create (string or BotType enum)
            
        Returns:
            PromptDoc instance for the new prompt
        """
        # Convert string to BotType enum if needed
        if isinstance(bot_type, str):
            try:
                bot_type = BotType[bot_type.upper()]
            except KeyError:
                raise ValueError(f"Invalid bot type: {bot_type}")
        
        # Check if the document already exists
        existing_doc = self.doc_repo.get_doc(name)
        if existing_doc:
            raise ValueError(f"Document '{name}' already exists")
        
        # Create template prompt document
        doc = create_prompt_doc_template(self.doc_repo, name, bot_type)
        
        # Return as PromptDoc
        return PromptDoc(doc)
    
    def list_prompts(self):
        """
        List all prompt documents in the repository.
        
        Returns:
            List of prompt document names
        """
        all_docs = self.doc_repo.list_docs()
        prompt_docs = []
        
        for name in all_docs:
            doc = self.doc_repo.get_doc(name)
            if doc and doc.get_property("type") == "prompt":
                prompt_docs.append(name)
        
        return prompt_docs
    
    def write_content(self, output_doc_name, prompt_doc_name, template_vars, command="", use_mock=False):
        """
        Generate content using a prompt document and save to an output document.
        
        Args:
            output_doc_name: Name of the output document
            prompt_doc_name: Name of the prompt document
            template_vars: Variables to fill in the prompt templates (strings or Doc objects)
            command: Command name for logging (optional)
            use_mock: Whether to use MockDocWriter instead of real API calls
            
        Returns:
            The generated content
            
        Raises:
            ValueError: If parameters are invalid
            LLMError: If content generation fails
        """
        if not self.api_key and not use_mock:
            raise ValueError("No OpenRouter API key provided")
        
        # Get the prompt document
        prompt_doc = self.get_prompt_doc(prompt_doc_name)
        if not prompt_doc:
            raise ValueError(f"Prompt document '{prompt_doc_name}' not found")
        
        # Get or create the output document
        output_doc = self.doc_repo.get_doc(output_doc_name)
        if not output_doc:
            output_doc = self.doc_repo.create_doc(output_doc_name)
        
        # Set initial document properties
        output_doc.set_property("prompt_doc", prompt_doc_name)
        output_doc.set_property("bot_type", prompt_doc.bot_type.name)
        output_doc.set_property("command", command or f"write_{output_doc_name}")
        
        # Initialize DocWriter or MockDocWriter
        if use_mock or DRY_RUN:
            self.logger.info(f"Using MockDocWriter for {output_doc_name} with prompt {prompt_doc_name}")
            writer = MockDocWriter(
                prompt_doc=prompt_doc,
                output_doc=output_doc,
                api_key=self.api_key or "mock_api_key",
                template_vars=template_vars,
                command=command or f"write_{output_doc_name}"
            )
        else:
            writer = DocWriter(
                prompt_doc=prompt_doc,
                output_doc=output_doc,
                api_key=self.api_key,
                template_vars=template_vars,
                command=command or f"write_{output_doc_name}"
            )
        
        # Generate content
        content = writer.generate()
        
        return content
    
    def get_prompt_info(self, prompt_name):
        """
        Get information about a specific prompt document.
        
        Args:
            prompt_name: Name of the prompt document
            
        Returns:
            Dictionary with prompt information
        """
        prompt_doc = self.get_prompt_doc(prompt_name)
        if not prompt_doc:
            raise ValueError(f"Prompt document '{prompt_name}' not found")
        
        return prompt_doc.to_dict()
    
    def validate_prompt(self, prompt_name):
        """
        Validate a prompt document.
        
        Args:
            prompt_name: Name of the prompt document
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            prompt_doc = self.get_prompt_doc(prompt_name)
            if not prompt_doc:
                return False, f"Prompt document '{prompt_name}' not found"
                
            # PromptDoc constructor already validates the document structure
            # Just check for any missing template variables
            main_vars = extract_template_vars(prompt_doc.main_prompt)
            continuation_vars = extract_template_vars(prompt_doc.continuation_prompt)
            found_vars = main_vars.union(continuation_vars)
            
            required_vars = prompt_doc.bot_type.required_vars
            missing_vars = required_vars - found_vars
            
            if missing_vars:
                return False, f"Missing required template variables: {missing_vars}"
                
            return True, None
            
        except Exception as e:
            return False, str(e)
    
    def validate_all_prompts(self):
        """
        Validate all prompt documents in the repository.
        
        Returns:
            Dictionary mapping prompt names to (is_valid, error_message) tuples
        """
        results = {}
        for name in self.list_prompts():
            results[name] = self.validate_prompt(name)
        return results


# Main entry point for using the document-based system
def generate_content(output_doc_name, prompt_doc_name, template_vars, 
                   doc_repo, api_key=None, command="", use_mock=False):
    """
    Generate content using a prompt document and save to an output document.
    
    Args:
        output_doc_name: Name of the output document
        prompt_doc_name: Name of the prompt document
        template_vars: Variables to fill in the prompt templates (strings or Doc objects)
        doc_repo: Document repository (DocRepo instance)
        api_key: OpenRouter API key (if None, will use OPENROUTER_API_KEY env var)
        command: Command name for logging (optional)
        use_mock: Whether to use MockDocWriter instead of real API calls
        
    Returns:
        The generated content
    """
    writer = BookWriter(
        doc_repo=doc_repo,
        api_key=api_key
    )
    
    content = writer.write_content(
        output_doc_name=output_doc_name,
        prompt_doc_name=prompt_doc_name,
        template_vars=template_vars,
        command=command or f"generate_{output_doc_name}",
        use_mock=use_mock
    )
    
    return content

