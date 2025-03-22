#!/usr/bin/env python3
"""
Comprehensive test suite for the Doc-Based BookBot System.

This test suite tests all components of the BookBot system without making
real LLM calls to save costs. It uses mock objects where necessary while
testing as much of the real code path as possible.

Test categories:
1. PromptDoc tests
2. DocWriter tests
3. BookWriter tests
4. End-to-end workflow tests
5. Error handling tests
"""

import unittest
import os
import json
import tempfile
import logging
from unittest.mock import MagicMock, patch
from datetime import datetime
from pathlib import Path
import requests 

# Import the BookBot module
from bot import (
    BotType, BookBotError, LLMError, PromptDoc, DocWriter, 
    MockDocWriter, BookWriter, extract_template_vars,
    format_price, create_prompt_doc_template, generate_content
)

# Configure logging - disable during tests unless debugging
logging.basicConfig(level=logging.CRITICAL)


class MockDoc:
    """Mock Doc class for testing."""
    
    def __init__(self, name="test_doc", content="", properties=None):
        self.name = name
        self._content = content
        self._properties = properties or {}
        self._json_data = {}
        self.update_count = 0
        self.append_count = 0
    
    def get_text(self):
        return self._content
    
    def update_text(self, text):
        self._content = text
        self.update_count += 1
        # Simulate version increment
        version = self._properties.get("version", 0)
        self._properties["version"] = version + 1
    
    def append_text(self, text):
        self._content += text
        self.append_count += 1
    
    def get_property(self, key, default=None):
        return self._properties.get(key, default)
    
    def set_property(self, key, value):
        self._properties[key] = value
    
    def get_json_data(self):
        return self._json_data
    
    def set_json_data(self, data):
        self._json_data = data


class MockDocRepo:
    """Mock DocRepo class for testing."""
    
    def __init__(self):
        self.docs = {}
    
    def get_doc(self, name):
        return self.docs.get(name)
    
    def create_doc(self, name, initial_properties=None, initial_text=""):
        if name in self.docs:
            return self.docs[name]
        
        doc = MockDoc(name, initial_text, initial_properties or {})
        self.docs[name] = doc
        return doc
    
    def list_docs(self):
        return list(self.docs.keys())


class TestBotType(unittest.TestCase):
    """Tests for the BotType enumeration."""
    
    def test_required_vars(self):
        """Test that each bot type has the correct required variables."""
        self.assertEqual(set(), BotType.DEFAULT.required_vars)
        self.assertEqual({"initial", "setting", "characters"}, BotType.WRITE_OUTLINE.required_vars)
        self.assertEqual({"chapter_number", "outline", "setting", "characters", "previous_chapter"}, 
                        BotType.WRITE_CHAPTER.required_vars)


class TestPromptDoc(unittest.TestCase):
    """Tests for the PromptDoc class."""
    
    def setUp(self):
        # Create a valid prompt document content
        self.valid_content = """
# Bot Configuration

bot_type: WRITE_CHAPTER
llm: writer
input_price: 0.5
output_price: 1.5
temperature: 0.7
expected_length: 2000

# System Prompt

You are an expert fiction writer.

# Main Prompt

Write Chapter {chapter_number} based on the following:
Outline: {outline}
Setting: {setting}
Characters: {characters}
Previous Chapter: {previous_chapter}

# Continuation Prompt

Continue writing Chapter {chapter_number}.
Current progress: {current_words} words out of {expected_words} expected words.
"""
        self.doc = MockDoc(name="test_prompt", content=self.valid_content, properties={"type": "prompt"})
    
    def test_parse_valid_prompt(self):
        """Test parsing a valid prompt document."""
        prompt_doc = PromptDoc(self.doc)
        
        # Check extracted values
        self.assertEqual(BotType.WRITE_CHAPTER, prompt_doc.bot_type)
        self.assertEqual("writer", prompt_doc._raw_llm)
        self.assertEqual(0.5, prompt_doc.input_price)
        self.assertEqual(1.5, prompt_doc.output_price)
        self.assertEqual(0.7, prompt_doc.temperature)
        self.assertEqual(2000, prompt_doc.expected_length)
        
        # Check prompt sections
        self.assertIn("expert fiction writer", prompt_doc.system_prompt)
        self.assertIn("{chapter_number}", prompt_doc.main_prompt)
        self.assertIn("{current_words}", prompt_doc.continuation_prompt)
    
    def test_missing_section(self):
        """Test that an error is raised if a required section is missing."""
        # Content missing System Prompt section
        content = """
# Bot Configuration

bot_type: WRITE_CHAPTER
llm: writer

# Main Prompt

Write Chapter {chapter_number}.

# Continuation Prompt

Continue writing.
"""
        doc = MockDoc(name="invalid_prompt", content=content, properties={"type": "prompt"})
        
        with self.assertRaises(ValueError) as context:
            PromptDoc(doc)
        
        self.assertIn("System Prompt", str(context.exception))
    
    def test_invalid_bot_type(self):
        """Test that an error is raised if the bot_type is invalid."""
        # Content with invalid bot_type
        content = """
# Bot Configuration

bot_type: INVALID_TYPE
llm: writer

# System Prompt

You are a writer.

# Main Prompt

Write something.

# Continuation Prompt

Continue writing.
"""
        doc = MockDoc(name="invalid_type", content=content, properties={"type": "prompt"})
        
        with self.assertRaises(ValueError) as context:
            PromptDoc(doc)
        
        self.assertIn("Invalid bot_type", str(context.exception))
    
    def test_missing_template_vars(self):
        """Test that validation detects missing template variables."""
        # Content missing required template variables
        content = """
# Bot Configuration

bot_type: WRITE_CHAPTER
llm: writer

# System Prompt

You are a writer.

# Main Prompt

Write Chapter {chapter_number}.
Setting: {setting}

# Continuation Prompt

Continue writing Chapter {chapter_number}.
"""
        doc = MockDoc(name="missing_vars", content=content, properties={"type": "prompt"})
        
        with self.assertRaises(ValueError) as context:
            PromptDoc(doc)
        
        error_msg = str(context.exception)
        self.assertIn("Missing required template variables", error_msg)
        self.assertIn("outline", error_msg)
        self.assertIn("characters", error_msg)
        self.assertIn("previous_chapter", error_msg)
    
    def test_validate_template_vars(self):
        """Test validating template variables."""
        prompt_doc = PromptDoc(self.doc)
        
        # Valid variables
        valid_vars = {
            "chapter_number": "1",
            "outline": "The outline",
            "setting": "The setting",
            "characters": "The characters",
            "previous_chapter": "Previous chapter"
        }
        
        # This should not raise an exception
        prompt_doc.validate_template_vars(valid_vars)
        
        # Missing variables
        missing_vars = {
            "chapter_number": "1",
            "setting": "The setting"
        }
        
        with self.assertRaises(ValueError) as context:
            prompt_doc.validate_template_vars(missing_vars)
        
        error_msg = str(context.exception)
        self.assertIn("Missing required template variables", error_msg)
    
    def test_empty_template_vars(self):
        """Test validating empty template variables."""
        prompt_doc = PromptDoc(self.doc)
        
        # Variables with empty values
        empty_vars = {
            "chapter_number": "1",
            "outline": "",
            "setting": "The setting",
            "characters": "The characters",
            "previous_chapter": ""
        }
        
        with self.assertRaises(ValueError) as context:
            prompt_doc.validate_template_vars(empty_vars)
        
        error_msg = str(context.exception)
        self.assertIn("Empty required template variables", error_msg)
        self.assertIn("outline", error_msg)
    
    def test_llm_alias_resolution(self):
        """Test resolution of LLM aliases."""
        # Create content with different llm values
        for llm_alias, expected_model in [
            ("writer", "deepseek-ai/deepseek-coder-v2-r-chat"),
            ("longcontext", "google/gemini-2.0-pro-001"),
            ("outliner", "anthropic/claude-3-5-sonnet-20240620"),
            ("custom-model", "custom-model")  # Non-alias should stay the same
        ]:
            content = f"""
# Bot Configuration

bot_type: DEFAULT
llm: {llm_alias}

# System Prompt

Test

# Main Prompt

Test

# Continuation Prompt

Test
"""
            doc = MockDoc(name=f"test_{llm_alias}", content=content, properties={"type": "prompt"})
            prompt_doc = PromptDoc(doc)
            
            self.assertEqual(expected_model, prompt_doc.llm)
            self.assertEqual(llm_alias, prompt_doc._raw_llm)


class TestDocWriter(unittest.TestCase):
    """Tests for the DocWriter class."""
    
    def setUp(self):
        # Create mock documents
        self.prompt_content = """
# Bot Configuration

bot_type: WRITE_CHAPTER
llm: writer
input_price: 0.5
output_price: 1.5
temperature: 0.7
expected_length: 2000

# System Prompt

You are an expert fiction writer.

# Main Prompt

Write Chapter {chapter_number} based on the following:
Outline: {outline}
Setting: {setting}
Characters: {characters}
Previous Chapter: {previous_chapter}

# Continuation Prompt

Continue writing Chapter {chapter_number}.
Current progress: {current_words} words out of {expected_words} expected words.
"""
        self.prompt_doc = MockDoc(name="write_chapter", content=self.prompt_content, 
                                properties={"type": "prompt", "version": 1})
        self.output_doc = MockDoc(name="chapter1", properties={"version": 1})
        
        # Create referenced docs
        self.outline_doc = MockDoc(name="outline", content="Chapter 1: Introduction", properties={"version": 2})
        self.setting_doc = MockDoc(name="setting", content="Fantasy world", properties={"version": 1})
        
        # Create template variables
        self.template_vars = {
            "chapter_number": "1",
            "outline": self.outline_doc,
            "setting": self.setting_doc,
            "characters": "Character list",
            "previous_chapter": "previous chapter goes here"
        }
        
        # Create PromptDoc
        self.prompt_doc_obj = PromptDoc(self.prompt_doc)
    
    @patch('requests.post')
    def test_call_openrouter_api(self, mock_post):
        """Test calling the OpenRouter API with mocked response."""
        # Mock the API response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "gen-123456",
            "choices": [
                {
                    "message": {
                        "content": "Generated content\n\nTHE END"
                    },
                    "finish_reason": "stop"
                }
            ],
            "usage": {
                "prompt_tokens": 100,
                "completion_tokens": 50
            }
        }
        mock_post.return_value = mock_response
        
        # Create DocWriter
        writer = DocWriter(
            prompt_doc=self.prompt_doc_obj,
            output_doc=self.output_doc,
            api_key="test_api_key",
            template_vars=self.template_vars,
            command="test_command"
        )
        
        # Call the API
        messages = [
            {"role": "system", "content": "Test system prompt"},
            {"role": "user", "content": "Test user message"}
        ]
        content, input_tokens, output_tokens, finish_reason, gen_id = writer._call_openrouter_api(messages)
        
        # Check that the API was called correctly
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        self.assertEqual("https://openrouter.ai/api/v1/chat/completions", args[0])
        self.assertEqual("test_api_key", kwargs["headers"]["Authorization"].split()[-1])
        self.assertEqual(self.prompt_doc_obj.llm, kwargs["json"]["model"])
        self.assertEqual(messages, kwargs["json"]["messages"])
        
        # Check the returned values
        self.assertEqual("Generated content\n\nTHE END", content)
        self.assertEqual(100, input_tokens)
        self.assertEqual(50, output_tokens)
        self.assertEqual("stop", finish_reason)
    
    @patch('requests.post')
    def test_generate_content(self, mock_post):
        """Test generating content with mocked API response."""
        # Mock the API response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "gen-123456",
            "choices": [
                {
                    "message": {
                        "content": "Generated chapter content\n\nTHE END"
                    },
                    "finish_reason": "stop"
                }
            ],
            "usage": {
                "prompt_tokens": 100,
                "completion_tokens": 50
            }
        }
        mock_post.return_value = mock_response
        
        # Create DocWriter
        writer = DocWriter(
            prompt_doc=self.prompt_doc_obj,
            output_doc=self.output_doc,
            api_key="test_api_key",
            template_vars=self.template_vars,
            command="test_command"
        )
        
        # Generate content
        content = writer.generate()
        
        # Check that the API was called
        mock_post.assert_called_once()
        
        # Check the generated content
        self.assertEqual("Generated chapter content", content)
        
        # Check that the document was updated
        self.assertEqual("Generated chapter content", self.output_doc.get_text())
        # Must update at least once. Exact count doesn't matter.
        self.assertLess(0, self.output_doc.update_count)
        
        # Check that document properties were updated
        self.assertEqual("complete", self.output_doc.get_property("status"))
        self.assertEqual(100, self.output_doc.get_property("input_tokens"))
        self.assertEqual(50, self.output_doc.get_property("output_tokens"))
        
        # Check that document references were recorded
        self.assertIn("references", self.output_doc._properties)
        refs = self.output_doc.get_property("references")
        self.assertIn("outline: outline#2", refs)
        self.assertIn("setting: setting#1", refs)
        
        # Check JSON data
        json_data = self.output_doc.get_json_data()
        self.assertIn("messages", json_data)
        self.assertIn("stats", json_data)
        self.assertIn("doc_references", json_data)
        self.assertEqual("outline#2", json_data["doc_references"]["outline"])
    
    def test_mock_doc_writer(self):
        """Test the MockDocWriter class."""
        # Create MockDocWriter
        writer = MockDocWriter(
            prompt_doc=self.prompt_doc_obj,
            output_doc=self.output_doc,
            api_key="test_api_key",
            template_vars=self.template_vars,
            command="test_command"
        )
        
        # Generate content
        content = writer.generate()
        
        # Check that content was generated
        self.assertIn("Mock content", content)
        
        # Check that the document was updated
        self.assertEqual(content, self.output_doc.get_text())
        
        # Check that document properties were updated
        self.assertEqual("complete", self.output_doc.get_property("status"))
        self.assertEqual(100, self.output_doc.get_property("input_tokens"))
        self.assertEqual(200, self.output_doc.get_property("output_tokens"))
        
        # Check that document references were recorded
        self.assertIn("references", self.output_doc._properties)
        refs = self.output_doc.get_property("references")
        self.assertIn("outline: outline#2", refs)
        self.assertIn("setting: setting#1", refs)
        
        # Check JSON data
        json_data = self.output_doc.get_json_data()
        self.assertIn("messages", json_data)
        self.assertIn("stats", json_data)
        self.assertIn("doc_references", json_data)
        self.assertEqual("outline#2", json_data["doc_references"]["outline"])


class TestBookWriter(unittest.TestCase):
    """Tests for the BookWriter class."""
    
    def setUp(self):
        # Create mock DocRepo
        self.doc_repo = MockDocRepo()
        
        # Add some initial prompt docs
        prompt_content = """
# Bot Configuration

bot_type: WRITE_CHAPTER
llm: writer
input_price: 0.5
output_price: 1.5
temperature: 0.7
expected_length: 2000

# System Prompt

You are an expert fiction writer.

# Main Prompt

Write Chapter {chapter_number} based on the following:
Outline: {outline}
Setting: {setting}
Characters: {characters}
Previous Chapter: {previous_chapter}

# Continuation Prompt

Continue writing Chapter {chapter_number}.
Current progress: {current_words} words out of {expected_words} expected words.
"""
        prompt_doc = self.doc_repo.create_doc(
            "write_chapter", 
            initial_properties={"type": "prompt", "version": 1},
            initial_text=prompt_content
        )
        
        # Create BookWriter
        self.writer = BookWriter(
            doc_repo=self.doc_repo,
            api_key="test_api_key"
        )
    
    def test_get_prompt_doc(self):
        """Test getting a prompt document."""
        # Get existing prompt doc
        prompt_doc = self.writer.get_prompt_doc("write_chapter")
        
        # Check that it was loaded correctly
        self.assertIsNotNone(prompt_doc)
        self.assertEqual(BotType.WRITE_CHAPTER, prompt_doc.bot_type)
        
        # Non-existent prompt
        self.assertIsNone(self.writer.get_prompt_doc("non_existent"))
        
        # Non-prompt document
        self.doc_repo.create_doc("regular_doc", initial_properties={"type": "content"})
        with self.assertRaises(ValueError):
            self.writer.get_prompt_doc("regular_doc")
    
    def test_create_prompt(self):
        """Test creating a prompt document."""
        # Create a new prompt
        prompt_doc = self.writer.create_prompt("new_prompt", BotType.WRITE_OUTLINE)
        
        # Check that it was created correctly
        self.assertEqual(BotType.WRITE_OUTLINE, prompt_doc.bot_type)
        self.assertEqual("new_prompt", prompt_doc.doc.name)
        
        # Get the document from the repo and check its type
        doc = self.doc_repo.get_doc("new_prompt")
        self.assertEqual("prompt", doc.get_property("type"))
        
        # Creating with same name should fail
        with self.assertRaises(ValueError):
            self.writer.create_prompt("new_prompt", BotType.DEFAULT)
        
        # Creating with string bot type
        prompt_doc = self.writer.create_prompt("string_type", "WRITE_SETTING")
        self.assertEqual(BotType.WRITE_SETTING, prompt_doc.bot_type)
        
        # Invalid string bot type
        with self.assertRaises(ValueError):
            self.writer.create_prompt("invalid_type", "INVALID_TYPE")
    
    def test_list_prompts(self):
        """Test listing prompt documents."""
        # Add a few more prompts
        self.writer.create_prompt("prompt1", BotType.DEFAULT)
        self.writer.create_prompt("prompt2", BotType.WRITE_SETTING)
        
        # Add a non-prompt document
        self.doc_repo.create_doc("regular_doc", initial_properties={"type": "content"})
        
        # List prompts
        prompts = self.writer.list_prompts()
        
        # Check results
        self.assertEqual(3, len(prompts))
        self.assertIn("write_chapter", prompts)
        self.assertIn("prompt1", prompts)
        self.assertIn("prompt2", prompts)
        self.assertNotIn("regular_doc", prompts)
    
    def test_write_content(self):
        """Test writing content using a prompt."""
        # Create necessary documents
        outline_doc = self.doc_repo.create_doc("outline", initial_text="Chapter 1 outline")
        setting_doc = self.doc_repo.create_doc("setting", initial_text="Fantasy setting")
        
        # Create template variables
        template_vars = {
            "chapter_number": "1",
            "outline": outline_doc,
            "setting": setting_doc,
            "characters": "Character list",
            "previous_chapter": "previous chapter content"
        }
        
        # Write content with mock
        content = self.writer.write_content(
            output_doc_name="chapter1",
            prompt_doc_name="write_chapter",
            template_vars=template_vars,
            command="test_command",
            use_mock=True
        )
        
        # Check the output
        self.assertIn("Mock content", content)
        
        # Check that the output document was created
        output_doc = self.doc_repo.get_doc("chapter1")
        self.assertIsNotNone(output_doc)
        self.assertEqual(content, output_doc.get_text())
        
        # Check properties
        self.assertEqual("write_chapter", output_doc.get_property("prompt_doc"))
        self.assertEqual("WRITE_CHAPTER", output_doc.get_property("bot_type"))
        
        # Check that document references were recorded
        self.assertIn("references", output_doc._properties)
        refs = output_doc.get_property("references")
        self.assertIn("outline", refs)
        self.assertIn("setting", refs)
    
    def test_validate_prompt(self):
        """Test validating a prompt document."""
        # Valid prompt
        is_valid, error = self.writer.validate_prompt("write_chapter")
        self.assertTrue(is_valid)
        self.assertIsNone(error)
        
        # Create an invalid prompt (missing required vars)
        invalid_content = """
# Bot Configuration

bot_type: WRITE_CHAPTER
llm: writer

# System Prompt

You are a writer.

# Main Prompt

Write Chapter {chapter_number}.
Setting: {setting}

# Continuation Prompt

Continue writing.
"""
        self.doc_repo.create_doc(
            "invalid_prompt", 
            initial_properties={"type": "prompt"},
            initial_text=invalid_content
        )
        
        # Validate the invalid prompt
        is_valid, error = self.writer.validate_prompt("invalid_prompt")
        self.assertFalse(is_valid)
        self.assertIn("Missing required template variables", error)
        
        # Non-existent prompt
        is_valid, error = self.writer.validate_prompt("non_existent")
        self.assertFalse(is_valid)
        self.assertIn("not found", error)
    
    def test_validate_all_prompts(self):
        """Test validating all prompt documents."""
        # Add a valid and an invalid prompt
        valid_content = """
# Bot Configuration

bot_type: DEFAULT
llm: writer

# System Prompt

Test

# Main Prompt

Test

# Continuation Prompt

Test
"""
        invalid_content = """
# Bot Configuration

bot_type: WRITE_CHAPTER
llm: writer

# System Prompt

Test

# Main Prompt

Test

# Continuation Prompt

Test
"""
        self.doc_repo.create_doc(
            "valid_prompt", 
            initial_properties={"type": "prompt"},
            initial_text=valid_content
        )
        self.doc_repo.create_doc(
            "invalid_prompt", 
            initial_properties={"type": "prompt"},
            initial_text=invalid_content
        )
        
        # Validate all prompts
        results = self.writer.validate_all_prompts()
        
        # Check results
        self.assertEqual(3, len(results))
        
        # write_chapter is valid
        self.assertTrue(results["write_chapter"][0])
        
        # valid_prompt is valid
        self.assertTrue(results["valid_prompt"][0])
        
        # invalid_prompt is invalid
        self.assertFalse(results["invalid_prompt"][0])
        self.assertIn("Missing required template variables", results["invalid_prompt"][1])


class TestUtilityFunctions(unittest.TestCase):
    """Tests for utility functions."""
    
    def test_extract_template_vars(self):
        """Test extracting template variables from text."""
        text = "Hello {name}, your order {order_id} will arrive on {date}."
        vars = extract_template_vars(text)
        
        self.assertEqual({"name", "order_id", "date"}, vars)
        
        # No variables
        text = "Plain text without variables."
        vars = extract_template_vars(text)
        self.assertEqual(set(), vars)
        
        # Repeated variables
        text = "Hello {name}, nice to meet you {name}!"
        vars = extract_template_vars(text)
        self.assertEqual({"name"}, vars)
    
    def test_format_price(self):
        """Test formatting price based on token usage."""
        price = format_price(1000, 2000, 5.0, 15.0)
        self.assertEqual("$0.035000 ($0.005000 + $0.030000)", price)
        
        # Zero tokens
        price = format_price(0, 0, 5.0, 15.0)
        self.assertEqual("$0.000000 ($0.000000 + $0.000000)", price)
    
    def test_create_prompt_doc_template(self):
        """Test creating a prompt document template."""
        doc_repo = MockDocRepo()
        doc = create_prompt_doc_template(doc_repo, "test_prompt", BotType.WRITE_CHAPTER)
        
        # Check that the document was created
        self.assertEqual("test_prompt", doc.name)
        self.assertEqual("prompt", doc.get_property("type"))
        self.assertEqual("WRITE_CHAPTER", doc.get_property("bot_type"))
        
        # Check content
        content = doc.get_text()
        self.assertIn("bot_type: WRITE_CHAPTER", content)
        self.assertIn("# System Prompt", content)
        self.assertIn("# Main Prompt", content)
        self.assertIn("# Continuation Prompt", content)
        
        # Check that template variables are included
        self.assertIn("{chapter_number}", content)
        self.assertIn("{outline}", content)
        self.assertIn("{setting}", content)
        self.assertIn("{characters}", content)
        self.assertIn("{previous_chapter}", content)


class TestEndToEndWorkflow(unittest.TestCase):
    """End-to-end tests of the BookBot system."""
    
    def setUp(self):
        # Create mock DocRepo
        self.doc_repo = MockDocRepo()
        
        # Create BookWriter
        self.writer = BookWriter(
            doc_repo=self.doc_repo,
            api_key="test_api_key"
        )
    
    def test_full_workflow(self):
        """Test a complete workflow from creating prompts to generating content."""
        # 1. Create prompts
        write_outline = self.writer.create_prompt("write_outline", BotType.WRITE_OUTLINE)
        write_chapter = self.writer.create_prompt("write_chapter", BotType.WRITE_CHAPTER)
        
        # 2. Create initial documents
        initial_doc = self.doc_repo.create_doc("initial", initial_text="Initial story idea")
        setting_doc = self.doc_repo.create_doc("setting", initial_text="Fantasy setting")
        characters_doc = self.doc_repo.create_doc("characters", initial_text="Character list")
        
        # 3. Generate outline
        outline_content = self.writer.write_content(
            output_doc_name="outline",
            prompt_doc_name="write_outline",
            template_vars={
                "initial": initial_doc,
                "setting": setting_doc,
                "characters": characters_doc
            },
            command="generate_outline",
            use_mock=True
        )
        
        # Check outline
        self.assertIn("Mock content", outline_content)
        outline_doc = self.doc_repo.get_doc("outline")
        self.assertEqual(outline_content, outline_doc.get_text())
        
        # Check outline references
        outline_refs = outline_doc.get_property("references")
        self.assertIn("initial:", outline_refs)
        self.assertIn("setting:", outline_refs)
        self.assertIn("characters:", outline_refs)
        
        # 4. Generate chapter using the outline
        chapter_content = self.writer.write_content(
            output_doc_name="chapter1",
            prompt_doc_name="write_chapter",
            template_vars={
                "chapter_number": "1",
                "outline": outline_doc,
                "setting": setting_doc,
                "characters": characters_doc,
                "previous_chapter": "previous chapter content"
            },
            command="generate_chapter1",
            use_mock=True
        )
        
        # Check chapter
        self.assertIn("Mock content", chapter_content)
        chapter_doc = self.doc_repo.get_doc("chapter1")
        self.assertEqual(chapter_content, chapter_doc.get_text())
        
        # Check chapter references
        chapter_refs = chapter_doc.get_property("references")
        self.assertIn("outline:", chapter_refs)
        self.assertIn("setting:", chapter_refs)
        self.assertIn("characters:", chapter_refs)
        
        # Check JSON data
        chapter_json = chapter_doc.get_json_data()
        self.assertIn("doc_references", chapter_json)
        self.assertIn("outline", chapter_json["doc_references"])
        self.assertIn("messages", chapter_json)
        self.assertIn("prompt", chapter_json)
        self.assertEqual("write_chapter", chapter_json["prompt"]["name"])


class TestErrorHandling(unittest.TestCase):
    """Tests for error handling in the BookBot system."""
    
    def setUp(self):
        # Create mock DocRepo
        self.doc_repo = MockDocRepo()
        
        # Create valid prompt
        prompt_content = """
# Bot Configuration

bot_type: WRITE_CHAPTER
llm: writer
input_price: 0.5
output_price: 1.5

# System Prompt

You are an expert fiction writer.

# Main Prompt

Write Chapter {chapter_number} based on the following:
Outline: {outline}
Setting: {setting}
Characters: {characters}
Previous Chapter: {previous_chapter}

# Continuation Prompt

Continue writing Chapter {chapter_number}.
Current progress: {current_words} words out of {expected_words} expected words.
"""
        self.prompt_doc = self.doc_repo.create_doc(
            "write_chapter", 
            initial_properties={"type": "prompt", "version": 1},
            initial_text=prompt_content
        )
        
        # Create output document
        self.output_doc = self.doc_repo.create_doc("chapter1")
        
        # Create BookWriter
        self.writer = BookWriter(
            doc_repo=self.doc_repo,
            api_key="test_api_key"
        )
    
    @patch('requests.post')
    def test_api_error_handling(self, mock_post):
        """Test handling of API errors."""
        # Mock an API error response
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.json.return_value = {
            "error": {
                "message": "Invalid request parameters",
                "type": "invalid_request"
            }
        }
        mock_post.return_value = mock_response
        
        # Create template variables with missing required var
        template_vars = {
            "chapter_number": "1",
            "outline": "Outline content",
            "setting": "Setting content",
            "characters": "Characters content",
            "previous_chapter": "previous chapter content"
        }
        
        # Attempt to generate content
        with self.assertRaises(LLMError) as context:
            # Use actual DocWriter (not mock) to test error handling
            prompt_doc = PromptDoc(self.prompt_doc)
            writer = DocWriter(
                prompt_doc=prompt_doc,
                output_doc=self.output_doc,
                api_key="test_api_key",
                template_vars=template_vars
            )
            writer.generate()
        
        # Check error message
        error_msg = str(context.exception)
        self.assertIn("Error response", error_msg)
        self.assertIn("Invalid request parameters", error_msg)
        
        # Check that the document was updated with error info
        self.assertEqual("error", self.output_doc.get_property("status"))
        self.assertIn("Error", self.output_doc.get_property("error"))
        
        # Check that error info was added to JSON data
        json_data = self.output_doc.get_json_data()
        self.assertIn("error", json_data)
    
    def test_missing_template_vars(self):
        """Test handling of missing template variables."""
        # Missing required variables
        template_vars = {
            "chapter_number": "1",
            "setting": "Setting content",
            # Missing outline, characters, previous_chapter
        }
        
        # Attempt to generate content
        with self.assertRaises(ValueError) as context:
            self.writer.write_content(
                output_doc_name="error_chapter",
                prompt_doc_name="write_chapter",
                template_vars=template_vars,
                use_mock=True
            )
        
        # Check error message
        error_msg = str(context.exception)
        self.assertIn("Missing required template variables", error_msg)
    
    def test_missing_prompt_doc(self):
        """Test handling of missing prompt document."""
        # Attempt to use a non-existent prompt
        with self.assertRaises(ValueError) as context:
            self.writer.write_content(
                output_doc_name="error_chapter",
                prompt_doc_name="non_existent_prompt",
                template_vars={},
                use_mock=True
            )
        
        # Check error message
        error_msg = str(context.exception)
        self.assertIn("not found", error_msg)
    
    @patch('requests.post')
    def test_empty_response_handling(self, mock_post):
        """Test handling of empty API responses."""
        # Mock an empty content response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [
                {
                    "message": {
                        "content": ""
                    },
                    "finish_reason": "stop"
                }
            ],
            "usage": {
                "prompt_tokens": 100,
                "completion_tokens": 0
            }
        }
        mock_post.return_value = mock_response
        
        # Create valid template variables
        template_vars = {
            "chapter_number": "1",
            "outline": "Outline content",
            "setting": "Setting content",
            "characters": "Characters content",
            "previous_chapter": "previous chapter content"
        }
        
        # Attempt to generate content - this should retry and eventually fail
        with self.assertRaises(LLMError) as context:
            prompt_doc = PromptDoc(self.prompt_doc)
            writer = DocWriter(
                prompt_doc=prompt_doc,
                output_doc=self.output_doc,
                api_key="test_api_key",
                template_vars=template_vars
            )
            writer.generate()
        
        # Check that multiple attempts were made (retries)
        self.assertGreaterEqual(mock_post.call_count, 2)
        
        # Check error message
        error_msg = str(context.exception)
        self.assertIn("Empty response", error_msg)
    
    @patch('requests.post')
    def test_timeout_handling(self, mock_post):
        """Test handling of API timeouts."""
        # Mock a timeout exception
        mock_post.side_effect = requests.exceptions.Timeout("Request timed out")
        
        # Create valid template variables
        template_vars = {
            "chapter_number": "1",
            "outline": "Outline content",
            "setting": "Setting content",
            "characters": "Characters content",
            "previous_chapter": "previous chapter content"
        }
        
        # Attempt to generate content - this should retry and eventually fail
        with self.assertRaises(LLMError) as context:
            prompt_doc = PromptDoc(self.prompt_doc)
            writer = DocWriter(
                prompt_doc=prompt_doc,
                output_doc=self.output_doc,
                api_key="test_api_key",
                template_vars=template_vars
            )
            writer.generate()
        
        # Check that multiple attempts were made (retries)
        self.assertGreaterEqual(mock_post.call_count, 2)
        
        # Check error message
        error_msg = str(context.exception)
        self.assertIn("timed out", error_msg)
    
    @patch('requests.post')
    def test_connection_error_handling(self, mock_post):
        """Test handling of connection errors."""
        # Mock a connection error
        mock_post.side_effect = requests.exceptions.ConnectionError("Connection error")
        
        # Create valid template variables
        template_vars = {
            "chapter_number": "1",
            "outline": "Outline content",
            "setting": "Setting content",
            "characters": "Characters content",
            "previous_chapter": "previous chapter content"
        }
        
        # Attempt to generate content - this should retry and eventually fail
        with self.assertRaises(LLMError) as context:
            prompt_doc = PromptDoc(self.prompt_doc)
            writer = DocWriter(
                prompt_doc=prompt_doc,
                output_doc=self.output_doc,
                api_key="test_api_key",
                template_vars=template_vars
            )
            writer.generate()
        
        # Check that multiple attempts were made (retries)
        self.assertGreaterEqual(mock_post.call_count, 2)
        
        # Check error message
        error_msg = str(context.exception)
        self.assertIn("Connection error", error_msg)


class TestGenerateContentFunction(unittest.TestCase):
    """Tests for the generate_content convenience function."""
    
    def setUp(self):
        # Create mock DocRepo
        self.doc_repo = MockDocRepo()
        
        # Create a valid prompt document
        prompt_content = """
# Bot Configuration

bot_type: WRITE_CHAPTER
llm: writer
input_price: 0.5
output_price: 1.5

# System Prompt

You are an expert fiction writer.

# Main Prompt

Write Chapter {chapter_number} based on the following:
Outline: {outline}
Setting: {setting}
Characters: {characters}
Previous Chapter: {previous_chapter}

# Continuation Prompt

Continue writing Chapter {chapter_number}.
Current progress: {current_words} words out of {expected_words} expected words.
"""
        self.doc_repo.create_doc(
            "write_chapter", 
            initial_properties={"type": "prompt", "version": 1},
            initial_text=prompt_content
        )
        
        # Create reference documents
        self.outline_doc = self.doc_repo.create_doc("outline", initial_text="Outline content")
        self.setting_doc = self.doc_repo.create_doc("setting", initial_text="Setting content")
    
    def test_generate_content(self):
        """Test the generate_content convenience function."""
        # Create template variables
        template_vars = {
            "chapter_number": "1",
            "outline": self.outline_doc,
            "setting": self.setting_doc,
            "characters": "Characters content",
            "previous_chapter": "previous chapter goes here"
        }
        
        # Generate content
        content = generate_content(
            output_doc_name="chapter1",
            prompt_doc_name="write_chapter",
            template_vars=template_vars,
            doc_repo=self.doc_repo,
            api_key="test_api_key",
            command="test_command",
            use_mock=True
        )
        
        # Check the output
        self.assertIn("Mock content", content)
        
        # Check that the output document was created
        output_doc = self.doc_repo.get_doc("chapter1")
        self.assertIsNotNone(output_doc)
        self.assertEqual(content, output_doc.get_text())
        
        # Check properties
        self.assertEqual("write_chapter", output_doc.get_property("prompt_doc"))
        self.assertEqual("WRITE_CHAPTER", output_doc.get_property("bot_type"))
        
        # Check that document references were recorded
        self.assertIn("references", output_doc._properties)


class TestDryRunMode(unittest.TestCase):
    """Tests for the DRY_RUN mode which should avoid API calls."""
    
    def setUp(self):
        # Create mock DocRepo
        self.doc_repo = MockDocRepo()
        
        # Create a valid prompt document
        prompt_content = """
# Bot Configuration

bot_type: WRITE_CHAPTER
llm: writer
input_price: 0.5
output_price: 1.5

# System Prompt

You are an expert fiction writer.

# Main Prompt

Write Chapter {chapter_number} based on the following:
Outline: {outline}
Setting: {setting}
Characters: {characters}
Previous Chapter: {previous_chapter}

# Continuation Prompt

Continue writing Chapter {chapter_number}.
Current progress: {current_words} words out of {expected_words} expected words.
"""
        self.doc_repo.create_doc(
            "write_chapter", 
            initial_properties={"type": "prompt", "version": 1},
            initial_text=prompt_content
        )
        
        # Create template variables
        self.template_vars = {
            "chapter_number": "1",
            "outline": "Outline content",
            "setting": "Setting content",
            "characters": "Characters content",
            "previous_chapter": "previous chapter content"
        }
        
        # Create BookWriter
        self.writer = BookWriter(
            doc_repo=self.doc_repo,
            api_key="test_api_key"
        )
    
    @patch('bot.DRY_RUN', True)
    @patch('requests.post')
    def test_dry_run_mode(self, mock_post):
        """Test that DRY_RUN mode prevents actual API calls."""
        # Generate content with DRY_RUN enabled but use_mock=False
        # This should still use the mock internally due to DRY_RUN
        content = self.writer.write_content(
            output_doc_name="dry_run_chapter",
            prompt_doc_name="write_chapter",
            template_vars=self.template_vars,
            command="test_dry_run",
            use_mock=False  # Should still use mock due to DRY_RUN
        )
        
        # Check that no API calls were made
        mock_post.assert_not_called()
        
        # Check that simulated content was generated
        self.assertIn("[DRY RUN]", content)
        
        # Check that the document was updated
        output_doc = self.doc_repo.get_doc("dry_run_chapter")
        self.assertEqual(content, output_doc.get_text())


if __name__ == '__main__':
    unittest.main()