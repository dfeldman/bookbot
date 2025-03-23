import unittest
import os
import tempfile
import shutil
from unittest import mock

# Import functions to test
from preview import (
    parse_markdown_properties,
    extract_tags_from_text,
    extract_document_refs,
    HTMLPreviewGenerator
)


class MockDoc:
    """Mock Doc class for testing."""
    
    def __init__(self, name, properties=None, text="", versions=None):
        self.name = name
        self._properties = properties or {}
        self._text = text
        self._versions = versions or [1]
    
    def get_properties(self):
        return self._properties
    
    def get_text(self):
        return self._text
    
    def get_versions(self):
        return self._versions
    
    def get_version_properties(self, version):
        if version in self._versions:
            return self._properties.copy()
        raise ValueError(f"Version {version} not found")
    
    def get_version_text(self, version):
        if version in self._versions:
            return f"{self._text} (Version {version})"
        raise ValueError(f"Version {version} not found")


class MockDocRepo:
    """Mock DocRepo class for testing."""
    
    def __init__(self, docs=None):
        self.docs = docs or {}
    
    def list_docs(self):
        return list(self.docs.keys())
    
    def get_doc(self, name):
        return self.docs.get(name)


class TestMarkdownParser(unittest.TestCase):
    """Test markdown parsing functions."""
    
    def test_parse_markdown_properties_with_delimiters(self):
        """Test parsing properties with --- delimiters."""
        content = """---
title: Test Document
author: John Doe
date: 2023-01-01
---
# Test Document

This is a test document."""
        
        properties, text = parse_markdown_properties(content)
        
        self.assertEqual(properties, {
            "title": "Test Document",
            "author": "John Doe",
            "date": "2023-01-01"
        })
        self.assertEqual(text, "# Test Document\n\nThis is a test document.")
    
    def test_parse_markdown_properties_without_delimiters(self):
        """Test parsing properties without --- delimiters."""
        content = """title: Test Document
author: John Doe
date: 2023-01-01

# Test Document

This is a test document."""
        
        properties, text = parse_markdown_properties(content)
        
        self.assertEqual(properties, {
            "title": "Test Document",
            "author": "John Doe",
            "date": "2023-01-01"
        })
        self.assertTrue(text.strip().startswith("# Test Document"))
    
    def test_parse_markdown_properties_with_mixed_format(self):
        """Test parsing properties with mixed format."""
        content = """title: Test Document
author: John Doe
date: 2023-01-01
---
# Test Document

This is a test document."""
        
        properties, text = parse_markdown_properties(content)
        
        self.assertEqual(properties, {
            "title": "Test Document",
            "author": "John Doe",
            "date": "2023-01-01"
        })
        self.assertEqual(text, "# Test Document\n\nThis is a test document.")


class TestTagExtraction(unittest.TestCase):
    """Test tag extraction functions."""
    
    def test_extract_tags(self):
        """Test extracting tags from text."""
        text = """# Heading

This is some text with #tag1 and #tag2 in it.
More text with #another_tag.

## Subheading with no tags

Text with #duplicate and #duplicate tags."""
        
        tags = extract_tags_from_text(text)
        
        self.assertEqual(tags, {"tag1", "tag2", "another_tag", "duplicate"})
    
    def test_extract_tags_ignore_heading_hashes(self):
        """Test that heading hashes are not extracted as tags."""
        text = """# Heading1

## Heading2

#Not a heading but a tag

This is some text with #tag1."""
        
        tags = extract_tags_from_text(text)
        
        self.assertEqual(tags, {"Not", "tag1"})  # Note: "Not" is included because it's a #tag at beginning of line


class TestDocumentRefs(unittest.TestCase):
    """Test document reference extraction functions."""
    
    def test_extract_document_refs(self):
        """Test extracting document references."""
        text = """This refers to doc1 and doc2 and doc3#5.
But not doc99 which doesn't exist."""
        
        doc_names = ["doc1", "doc2", "doc3", "doc4"]
        refs = extract_document_refs(text, doc_names)
        
        self.assertEqual(refs, {"doc1", "doc2", "doc3"})
    
    def test_extract_document_refs_boundaries(self):
        """Test document reference extraction with word boundaries."""
        text = """This refers to doc1 and doc1s but not doc1suffix.
Also doc2 and doc2#3 should be found."""
        
        doc_names = ["doc1", "doc2", "doc3"]
        refs = extract_document_refs(text, doc_names)
        
        self.assertEqual(refs, {"doc1", "doc2"})


class TestHTMLPreviewGenerator(unittest.TestCase):
    """Test HTMLPreviewGenerator class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary directory for testing
        self.test_dir = tempfile.mkdtemp()
        
        # Create mock documents
        self.chapter1 = MockDoc(
            name="chapter1",
            properties={"type": "chapter", "order": 1, "output_tokens": 1000},
            text="# Chapter 1\n\nThis is chapter 1 with #tag1 and #tag2.",
            versions=[1, 2, 3]
        )
        
        self.chapter2 = MockDoc(
            name="chapter2",
            properties={"type": "chapter", "order": 2, "output_tokens": 2000},
            text="# Chapter 2\n\nThis is chapter 2 with #tag2 and #tag3.\nRefers to chapter1.",
            versions=[1, 2]
        )
        
        self.outline = MockDoc(
            name="outline",
            properties={"type": "outline"},
            text="# Outline\n\nThis is the outline for chapter1 and chapter2.",
            versions=[1]
        )
        
        self.bot = MockDoc(
            name="test_bot",
            properties={"type": "prompt", "bot_type": "WRITE_CHAPTER"},
            text="""---
bot_type: WRITE_CHAPTER
llm: writer
temperature: 0.7
---
# System Prompt

You are an expert writer.

# Main Prompt

Write chapter {chapter_number}.

# Continuation Prompt

Continue writing chapter {chapter_number}.""",
            versions=[1]
        )
        
        # Create mock repository
        self.doc_repo = MockDocRepo({
            "chapter1": self.chapter1,
            "chapter2": self.chapter2,
            "outline": self.outline,
            "test_bot": self.bot
        })
        
        # Initialize preview generator
        self.preview_dir = os.path.join(self.test_dir, "preview")
        self.generator = HTMLPreviewGenerator(self.doc_repo, self.preview_dir)
    
    def tearDown(self):
        """Clean up after tests."""
        shutil.rmtree(self.test_dir)
    
    def test_initialization(self):
        """Test that the generator initializes correctly."""
        self.assertEqual(self.generator.doc_repo, self.doc_repo)
        self.assertEqual(self.generator.preview_dir, self.preview_dir)
        
        # Check that directories were created
        self.assertTrue(os.path.exists(self.preview_dir))
        self.assertTrue(os.path.exists(os.path.join(self.preview_dir, "static")))
        self.assertTrue(os.path.exists(os.path.join(self.preview_dir, "docs")))
    
    def test_convert_markdown_to_html(self):
        """Test converting markdown to HTML."""
        markdown_text = "# Test\n\nThis is **bold** and *italic*."
        html = self.generator._convert_markdown_to_html(markdown_text)
        
        self.assertIn("<h1>Test</h1>", html)
        self.assertIn("<strong>bold</strong>", html)
        self.assertIn("<em>italic</em>", html)
    
    def test_process_document_links(self):
        """Test processing document links in HTML."""
        # Set up doc cache
        self.generator.doc_cache = {
            "chapter1": {"properties": {}, "text": "", "versions": [1]},
            "chapter2": {"properties": {}, "text": "", "versions": [1]},
            "outline": {"properties": {}, "text": "", "versions": [1]}
        }
        
        html = "<p>This refers to chapter1 and chapter2 and outline.</p>"
        processed_html = self.generator._process_document_links(html)
        
        self.assertIn('<a href="../docs/chapter1.html">chapter1</a>', processed_html)
        self.assertIn('<a href="../docs/chapter2.html">chapter2</a>', processed_html)
        self.assertIn('<a href="../docs/outline.html">outline</a>', processed_html)
    
    def test_process_tags(self):
        """Test processing tags in HTML."""
        html = "<p>This has #tag1 and #tag2.</p>"
        processed_html = self.generator._process_tags(html)
        
        self.assertIn('<a href="../tags/tag1.html" class="tag">#tag1</a>', processed_html)
        self.assertIn('<a href="../tags/tag2.html" class="tag">#tag2</a>', processed_html)
        self.assertEqual(self.generator.all_tags, {"tag1", "tag2"})
    
    def test_convert_doc_refs_to_links(self):
        """Test converting document references to links."""
        # Set up doc cache
        self.generator.doc_cache = {
            "chapter1": {"properties": {}, "text": "", "versions": [1]},
            "chapter2": {"properties": {}, "text": "", "versions": [1]},
        }
        
        text = "This refers to chapter1 and chapter2#3."
        processed_text = self.generator._convert_doc_refs_to_links(text)
        
        self.assertIn('<a href="../docs/chapter1.html">chapter1</a>', processed_text)
        self.assertIn('<a href="../revisions/chapter2_v3.html">chapter2#3</a>', processed_text)
    
    @mock.patch('preview.is_action_running')
    def test_generate_preview(self, mock_is_action_running):
        """Test generating the complete preview."""
        # Mock action status
        mock_is_action_running.return_value = None
        
        # Generate preview
        self.generator.generate_preview()
        
        # Check that index.html was created
        index_path = os.path.join(self.preview_dir, "index.html")
        self.assertTrue(os.path.exists(index_path))
        
        # Check that document pages were created
        for doc_name in self.doc_repo.list_docs():
            doc_path = os.path.join(self.preview_dir, "docs", f"{doc_name}.html")
            self.assertTrue(os.path.exists(doc_path), f"Missing document page: {doc_path}")
        
        # Check that tag pages were created
        tags_index_path = os.path.join(self.preview_dir, "tags", "index.html")
        self.assertTrue(os.path.exists(tags_index_path))
        
        # Check that actions index was created
        actions_index_path = os.path.join(self.preview_dir, "actions", "index.html")
        self.assertTrue(os.path.exists(actions_index_path))


if __name__ == "__main__":
    unittest.main()
    