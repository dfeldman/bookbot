import unittest
import os
import shutil
import tempfile
import logging
import json
import time
from typing import Dict, Any

# Import the classes from your module - adjust this import as needed
# from doc_repository import Doc, DocRepo
# For the test, we'll assume the code is in a file named doc_repository.py
# If your module structure is different, adjust this accordingly
import sys
import os

# Add the parent directory to sys.path to import the module
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from doc import Doc, DocRepo

class TestDoc(unittest.TestCase):
    """Test cases for the Doc class."""
    
    def setUp(self):
        """Set up the test environment before each test."""
        # Create a temporary directory for tests
        self.test_dir = tempfile.mkdtemp()
        
        # Set up a logger for testing
        self.logger = logging.getLogger('test_logger')
        self.logger.setLevel(logging.DEBUG)
        
        # Create a console handler for the logger
        handler = logging.StreamHandler()
        handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        
        # Create a new document for testing
        self.doc_name = "test_doc"
        self.doc = Doc(self.doc_name, self.test_dir, self.logger)
    
    def tearDown(self):
        """Clean up after each test."""
        # Remove the temporary directory and its contents
        shutil.rmtree(self.test_dir)
    
    def test_init(self):
        """Test document initialization."""
        # Check if files were created
        md_file = os.path.join(self.test_dir, f"{self.doc_name}.md")
        json_file = os.path.join(self.test_dir, f"{self.doc_name}.json")
        history_dir = os.path.join(self.test_dir, "history")
        
        self.assertTrue(os.path.exists(md_file), "Markdown file should be created")
        self.assertTrue(os.path.exists(json_file), "JSON file should be created")
        self.assertTrue(os.path.isdir(history_dir), "History directory should be created")
        
        # Check default properties
        properties = self.doc.get_properties()
        self.assertEqual(properties["version"], 1, "Default version should be 1")
        self.assertEqual(properties["filename"], f"{self.doc_name}.md", "Filename property should be set")
        self.assertFalse(properties["complete"], "Document should not be marked as complete by default")
    
    def test_init_invalid_name(self):
        """Test initialization with invalid document name."""
        invalid_names = [
            "../traversal",  # Path traversal
            "test/doc",      # Contains path separator
            "test\\doc",     # Contains path separator (Windows)
            "test..",        # Suspicious name
            ".hidden",       # Starts with a dot
            "test*doc",      # Contains invalid character
            "test?doc",      # Contains invalid character
        ]
        
        for name in invalid_names:
            print("XXX", name)
            with self.assertRaises(ValueError, msg=f"Should reject invalid name: {name}"):
                Doc(name, self.test_dir, self.logger)
    
    def test_get_text(self):
        """Test getting document text."""
        # Initially, document should be empty
        self.assertEqual(self.doc.get_text(), "", "New document should have empty text")
        
        # Update text and check if get_text returns the updated content
        test_text = "This is a test document."
        self.doc.update_text(test_text)
        self.assertEqual(self.doc.get_text(), test_text, "get_text should return the document content")
    
    def test_get_properties(self):
        """Test getting document properties."""
        # Get initial properties
        properties = self.doc.get_properties()
        
        # Check if default properties exist
        self.assertIn("version", properties, "Properties should contain version")
        self.assertIn("creation_time", properties, "Properties should contain creation_time")
        self.assertIn("filename", properties, "Properties should contain filename")
        self.assertIn("complete", properties, "Properties should contain complete status")
        
        # Set a new property
        self.doc.set_property("test_prop", "test_value")
        
        # Check if the new property is in the properties
        updated_properties = self.doc.get_properties()
        self.assertEqual(updated_properties["test_prop"], "test_value", "Properties should include newly set property")
    
    def test_get_property(self):
        """Test getting a specific property."""
        # Set a property
        self.doc.set_property("test_prop", "test_value")
        
        # Get the property
        value = self.doc.get_property("test_prop")
        self.assertEqual(value, "test_value", "get_property should return the correct value")
        
        # Get a non-existent property with default
        value = self.doc.get_property("non_existent", "default_value")
        self.assertEqual(value, "default_value", "get_property should return the default value for non-existent property")
    
    def test_get_property_invalid_key(self):
        """Test getting a property with an invalid key."""
        invalid_keys = [
            "test/prop",    # Contains path separator
            "test\\prop",   # Contains path separator (Windows)
            "test*prop",    # Contains invalid character
            "test?prop",    # Contains invalid character
        ]
        
        for key in invalid_keys:
            with self.assertRaises(ValueError, msg=f"Should reject invalid property key: {key}"):
                self.doc.get_property(key)
    
    def test_has_property(self):
        """Test checking if a property exists."""
        # Set a property
        self.doc.set_property("test_prop", "test_value")
        
        # Check if the property exists
        self.assertTrue(self.doc.has_property("test_prop"), "has_property should return True for existing property")
        self.assertFalse(self.doc.has_property("non_existent"), "has_property should return False for non-existent property")
    
    def test_set_property(self):
        """Test setting a property."""
        # Set a new property
        self.doc.set_property("test_prop", "test_value")
        
        # Check if the property was set
        self.assertEqual(self.doc.get_property("test_prop"), "test_value", "Property should be set correctly")
        
        # Update the property
        self.doc.set_property("test_prop", "new_value")
        self.assertEqual(self.doc.get_property("test_prop"), "new_value", "Property should be updated correctly")
    
    def test_set_property_total(self):
        """Test setting a total_* property."""
        # Set an initial total property
        self.doc.set_property("total_count", 10)
        self.assertEqual(self.doc.get_property("total_count"), 10, "Initial total should be set correctly")
        
        # Update the total property - should be incremented
        self.doc.set_property("total_count", 5)
        self.assertEqual(self.doc.get_property("total_count"), 15, "Total property should be incremented")
    
    def test_update_text(self):
        """Test updating document text."""
        # Update text for the first time
        test_text1 = "This is the first version."
        self.doc.update_text(test_text1)
        self.assertEqual(self.doc.get_text(), test_text1, "Text should be updated correctly")
        self.assertEqual(self.doc.get_property("version"), 2, "Version should be incremented to 2")
        
        # Update text for the second time
        test_text2 = "This is the second version."
        self.doc.update_text(test_text2)
        self.assertEqual(self.doc.get_text(), test_text2, "Text should be updated correctly")
        self.assertEqual(self.doc.get_property("version"), 3, "Version should be incremented to 3")
        
        # Check that previous versions were archived
        history_dir = os.path.join(self.test_dir, "history")
        self.assertTrue(os.path.exists(os.path.join(history_dir, f"{self.doc_name}_v1.md")), "Version 1 should be archived")
        self.assertTrue(os.path.exists(os.path.join(history_dir, f"{self.doc_name}_v2.md")), "Version 2 should be archived")
    
    def test_append_text(self):
        """Test appending text to a document."""
        # Set initial text
        initial_text = "Initial text."
        self.doc.update_text(initial_text)
        
        # Append text
        append_text = " Appended text."
        self.doc.append_text(append_text)
        
        # Check if the text was appended
        self.assertEqual(self.doc.get_text(), initial_text + append_text, "Text should be appended correctly")
        
        # Version should not change when appending text
        self.assertEqual(self.doc.get_property("version"), 2, "Version should remain the same after append")
    
    def test_get_sections_with_tags(self):
        """Test getting sections with specific tags."""
        # Create a document with multiple sections and tags
        text = """## Section 1 #tag1 #tag2
This is section 1.

## Section 2 #tag2 #tag3
This is section 2.

## Section 3 #tag1 #tag3
This is section 3.

## Section 4 #tag4
This is section 4.
"""
        self.doc.update_text(text)
        
        # Get sections with tag1
        sections = self.doc.get_sections_with_tags(["tag1"])
        self.assertEqual(len(sections), 2, "Should find 2 sections with tag1")
        
        # Get sections with tag2 and tag3
        sections = self.doc.get_sections_with_tags(["tag2", "tag3"])
        self.assertEqual(len(sections), 1, "Should find 1 section with both tag2 and tag3")
        self.assertIn("Section 2", sections[0], "Should find the correct section")
        
        # Get sections with a non-existent tag
        sections = self.doc.get_sections_with_tags(["nonexistent"])
        self.assertEqual(len(sections), 0, "Should find 0 sections with non-existent tag")
    
    def test_get_sections_with_invalid_tags(self):
        """Test getting sections with invalid tags."""
        invalid_tags = [
            "tag/1",    # Contains path separator
            "tag\\1",   # Contains path separator (Windows)
            "tag*1",    # Contains invalid character
            "tag?1",    # Contains invalid character
        ]
        
        for tag in invalid_tags:
            with self.assertRaises(ValueError, msg=f"Should reject invalid tag: {tag}"):
                self.doc.get_sections_with_tags([tag])
    
    def test_add_tag_to_section(self):
        """Test adding a tag to a section."""
        # Create a document with a section
        text = """## Section 1 #tag1
This is section 1.

## Section 2
This is section 2.
"""
        self.doc.update_text(text)
        
        # Add a tag to Section 2
        result = self.doc.add_tag_to_section("Section 2", "tag2")
        self.assertTrue(result, "Adding tag should succeed")
        
        # Check if the tag was added
        sections = self.doc.get_sections_with_tags(["tag2"])
        self.assertEqual(len(sections), 1, "Should find 1 section with tag2")
        self.assertIn("Section 2", sections[0], "Should find the correct section")
        
        # Try to add a tag to a non-existent section
        result = self.doc.add_tag_to_section("Section 3", "tag3")
        self.assertFalse(result, "Adding tag to non-existent section should fail")
    
    def test_add_tag_invalid_tag(self):
        """Test adding an invalid tag to a section."""
        # Create a document with a section
        text = """## Section 1
This is section 1.
"""
        self.doc.update_text(text)
        
        invalid_tags = [
            "tag/1",    # Contains path separator
            "tag\\1",   # Contains path separator (Windows)
            "tag*1",    # Contains invalid character
            "tag?1",    # Contains invalid character
        ]
        
        for tag in invalid_tags:
            with self.assertRaises(ValueError, msg=f"Should reject invalid tag: {tag}"):
                self.doc.add_tag_to_section("Section 1", tag)
    
    def test_get_versions(self):
        """Test getting document versions."""
        # Initially, only version 1 should exist
        versions = self.doc.get_versions()
        self.assertEqual(versions, [1], "Initially, only version 1 should exist")
        
        # Update text to create new versions
        self.doc.update_text("Version 2")
        self.doc.update_text("Version 3")
        
        # Check if all versions are listed
        versions = self.doc.get_versions()
        self.assertEqual(versions, [1, 2, 3], "All versions should be listed")
    
    def test_get_version_text(self):
        """Test getting text of a specific version."""
        # Create multiple versions
        self.doc.update_text("Version 2 text")
        self.doc.update_text("Version 3 text")
        
        # Get text of each version
        self.assertEqual(self.doc.get_version_text(1), "", "Version 1 should have empty text")
        self.assertEqual(self.doc.get_version_text(2), "Version 2 text", "Should get correct text for version 2")
        self.assertEqual(self.doc.get_version_text(3), "Version 3 text", "Should get correct text for version 3")
        
        # Try to get text of a non-existent version
        with self.assertRaises(ValueError, msg="Should raise ValueError for non-existent version"):
            self.doc.get_version_text(4)
    
    def test_get_version_properties(self):
        """Test getting properties of a specific version."""
        # Set a property and create a new version
        self.doc.update_text("Version 2 text")
        self.doc.set_property("test_prop", "value1")

        
        # Change the property and create another version
        self.doc.update_text("Version 3 text")
        self.doc.set_property("test_prop", "value2")
        
        # Get properties of each version
        v1_props = self.doc.get_version_properties(1)
        v2_props = self.doc.get_version_properties(2)
        v3_props = self.doc.get_version_properties(3)
        
        self.assertNotIn("test_prop", v1_props, "Version 1 should not have test_prop")
        self.assertEqual(v2_props.get("test_prop"), "value1", "Version 2 should have correct property value")
        self.assertEqual(v3_props.get("test_prop"), "value2", "Version 3 should have correct property value")
    
    def test_revert_to_version(self):
        """Test reverting to a previous version."""
        # Create multiple versions
        self.doc.update_text("Version 2 text")
        self.doc.update_text("Version 3 text")
        
        # Revert to version 2
        self.doc.revert_to_version(2)
        
        # Check the current text and version
        self.assertEqual(self.doc.get_text(), "Version 2 text", "Text should be reverted to version 2")
        self.assertEqual(self.doc.get_property("version"), 4, "A new version should be created after revert")
        
        # Try to revert to a non-existent version
        with self.assertRaises(ValueError, msg="Should raise ValueError for non-existent version"):
            self.doc.revert_to_version(10)
    
    def test_get_json_data(self):
        """Test getting JSON data."""
        # Initially, JSON file should be empty
        data = self.doc.get_json_data()
        self.assertEqual(data, {}, "Initial JSON data should be empty")
        
        # Set JSON data
        test_data = {"key": "value", "nested": {"subkey": "subvalue"}}
        self.doc.set_json_data(test_data)
        
        # Get JSON data and check if it matches
        retrieved_data = self.doc.get_json_data()
        self.assertEqual(retrieved_data, test_data, "Retrieved JSON data should match what was set")
    
    def test_set_json_data(self):
        """Test setting JSON data."""
        # Set simple JSON data
        test_data1 = {"key1": "value1"}
        self.doc.set_json_data(test_data1)
        
        # Check if data was set correctly
        self.assertEqual(self.doc.get_json_data(), test_data1, "JSON data should be set correctly")
        
        # Set more complex JSON data
        test_data2 = {
            "key2": "value2",
            "nested": {
                "subkey": "subvalue",
                "list": [1, 2, 3]
            },
            "array": [
                {"item": "item1"},
                {"item": "item2"}
            ]
        }
        self.doc.set_json_data(test_data2)
        
        # Check if data was updated correctly
        self.assertEqual(self.doc.get_json_data(), test_data2, "JSON data should be updated correctly")
    
    def test_complete(self):
        """Test marking a document as complete."""
        # Check initial complete state
        self.assertFalse(self.doc.get_property("complete", False), "Document should initially be incomplete")
        
        # Mark as complete
        self.doc.complete()
        
        # Check if document is marked as complete
        self.assertTrue(self.doc.get_property("complete", False), "Document should be marked as complete")
    
    def test_rollback_complete(self):
        """Test rollback on a complete document."""
        # Create a new version
        self.doc.update_text("Version 2 text")
        
        # Mark as complete
        self.doc.complete()
        
        # Try to rollback
        result = self.doc.rollback()
        
        # Rollback should fail
        self.assertFalse(result, "Rollback should fail on a complete document")
        self.assertEqual(self.doc.get_text(), "Version 2 text", "Text should remain unchanged")
    
    def test_rollback_incomplete(self):
        """Test rollback on an incomplete document."""
        # Create multiple versions
        self.doc.update_text("Version 2 text")
        self.doc.update_text("Version 3 text")
        
        # Rollback
        result = self.doc.rollback()
        
        # Rollback should succeed
        self.assertTrue(result, "Rollback should succeed on an incomplete document")
        self.assertEqual(self.doc.get_text(), "Version 2 text", "Text should be rolled back to previous version")
    
    def test_rollback_first_version(self):
        """Test rollback on a document with only one version."""
        # Try to rollback without creating any new versions
        result = self.doc.rollback()
        
        # Rollback should fail
        self.assertFalse(result, "Rollback should fail on a document with only one version")
    
    def test_parse_property_value(self):
        """Test parsing of property values."""
        # Test parsing different value types
        self.assertEqual(self.doc._parse_property_value("42"), 42, "Should parse integer correctly")
        self.assertEqual(self.doc._parse_property_value("3.14"), 3.14, "Should parse float correctly")
        self.assertEqual(self.doc._parse_property_value("true"), True, "Should parse boolean true correctly")
        self.assertEqual(self.doc._parse_property_value("false"), False, "Should parse boolean false correctly")
        self.assertEqual(self.doc._parse_property_value("string"), "string", "Should keep string as is")


class TestDocRepo(unittest.TestCase):
    """Test cases for the DocRepo class."""
    
    def setUp(self):
        """Set up the test environment before each test."""
        # Create a temporary directory for tests
        self.test_dir = tempfile.mkdtemp()
        
        # Set up a logger for testing
        self.logger = logging.getLogger('test_repo_logger')
        self.logger.setLevel(logging.DEBUG)
        
        # Create a console handler for the logger
        handler = logging.StreamHandler()
        handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        
        # Create a document repository for testing
        self.repo = DocRepo(self.test_dir, self.logger)
    
    def tearDown(self):
        """Clean up after each test."""
        # Remove the temporary directory and its contents
        shutil.rmtree(self.test_dir)
    
    def test_init(self):
        """Test repository initialization."""
        # Check if repository directory exists
        self.assertTrue(os.path.isdir(self.test_dir), "Repository directory should exist")
        
        # Check if history directory exists
        history_dir = os.path.join(self.test_dir, "history")
        self.assertTrue(os.path.isdir(history_dir), "History directory should exist")
    
    def test_create_doc(self):
        """Test creating a document."""
        # Create a document with initial properties and text
        doc = self.repo.create_doc(
            "test_doc",
            initial_properties={"type": "note", "author": "tester"},
            initial_text="Initial content."
        )
        
        # Check if the document was created properly
        self.assertEqual(doc.name, "test_doc", "Document name should be set correctly")
        self.assertEqual(doc.get_text(), "Initial content.", "Document text should be set correctly")
        self.assertEqual(doc.get_property("type"), "note", "Document property should be set correctly")
        self.assertEqual(doc.get_property("author"), "tester", "Document property should be set correctly")
        self.assertFalse(doc.get_property("complete"), "Document should not be marked as complete by default")
        
        # Check if the document files exist
        md_file = os.path.join(self.test_dir, "test_doc.md")
        json_file = os.path.join(self.test_dir, "test_doc.json")
        self.assertTrue(os.path.exists(md_file), "Markdown file should exist")
        self.assertTrue(os.path.exists(json_file), "JSON file should exist")
    
    def test_create_doc_with_explicit_complete(self):
        """Test creating a document with explicit complete property."""
        # Create a document with complete=True
        doc = self.repo.create_doc(
            "test_doc",
            initial_properties={"complete": True}
        )
        
        # Check if the complete property was set correctly
        self.assertTrue(doc.get_property("complete"), "Document should be marked as complete")
    
    def test_create_doc_invalid_name(self):
        """Test creating a document with invalid name."""
        invalid_names = [
            "../traversal",  # Path traversal
            "test/doc",      # Contains path separator
            "test\\doc",     # Contains path separator (Windows)
            "test*doc",      # Contains invalid character
        ]
        
        for name in invalid_names:
            with self.assertRaises(ValueError, msg=f"Should reject invalid name: {name}"):
                self.repo.create_doc(name)
    
    def test_delete_doc(self):
        """Test deleting a document."""
        # Create a document
        doc = self.repo.create_doc("test_doc")
        
        # Verify the document exists
        md_file = os.path.join(self.test_dir, "test_doc.md")
        json_file = os.path.join(self.test_dir, "test_doc.json")
        self.assertTrue(os.path.exists(md_file), "Markdown file should exist")
        self.assertTrue(os.path.exists(json_file), "JSON file should exist")
        
        # Delete the document
        result = self.repo.delete_doc("test_doc")
        
        # Check if deletion was successful
        self.assertTrue(result, "Deletion should succeed")
        self.assertFalse(os.path.exists(md_file), "Markdown file should be deleted")
        self.assertFalse(os.path.exists(json_file), "JSON file should be deleted")
        
        # Try to delete a non-existent document
        result = self.repo.delete_doc("nonexistent")
        self.assertFalse(result, "Deletion of non-existent document should fail")
    
    def test_delete_doc_invalid_name(self):
        """Test deleting a document with invalid name."""
        with self.assertRaises(ValueError, msg="Should reject invalid name"):
            self.repo.delete_doc("../traversal")
    
    def test_get_doc(self):
        """Test getting a document."""
        # Create a document
        self.repo.create_doc("test_doc")
        
        # Get the document
        doc = self.repo.get_doc("test_doc")
        
        # Check if the document was retrieved properly
        self.assertIsNotNone(doc, "Document should be retrieved")
        self.assertEqual(doc.name, "test_doc", "Document should have correct name")
        
        # Try to get a non-existent document
        doc = self.repo.get_doc("nonexistent")
        self.assertIsNone(doc, "Non-existent document should return None")
    
    def test_get_doc_invalid_name(self):
        """Test getting a document with invalid name."""
        with self.assertRaises(ValueError, msg="Should reject invalid name"):
            self.repo.get_doc("../traversal")
    
    def test_get_docs_by_type(self):
        """Test getting documents by type."""
        # Create documents with different types
        self.repo.create_doc("doc1", initial_properties={"type": "note"})
        self.repo.create_doc("doc2", initial_properties={"type": "note"})
        self.repo.create_doc("doc3", initial_properties={"type": "report"})
        self.repo.create_doc("doc4", initial_properties={"type": "memo"})
        
        # Get documents by type
        note_docs = self.repo.get_docs_by_type("note")
        report_docs = self.repo.get_docs_by_type("report")
        memo_docs = self.repo.get_docs_by_type("memo")
        nonexistent_docs = self.repo.get_docs_by_type("nonexistent")
        
        # Check if documents were retrieved properly
        self.assertEqual(len(note_docs), 2, "Should find 2 note documents")
        self.assertEqual(len(report_docs), 1, "Should find 1 report document")
        self.assertEqual(len(memo_docs), 1, "Should find 1 memo document")
        self.assertEqual(len(nonexistent_docs), 0, "Should find 0 nonexistent documents")
        
        # Check if document names are correct
        note_names = [doc.name for doc in note_docs]
        self.assertIn("doc1", note_names, "doc1 should be a note")
        self.assertIn("doc2", note_names, "doc2 should be a note")
    
    def test_get_sections_with_tags(self):
        """Test getting sections with tags across all documents."""
        # Create documents with sections and tags
        doc1 = self.repo.create_doc("doc1")
        doc1.update_text("""## Section 1 #tag1 #tag2
This is section 1 in doc1.

## Section 2 #tag2 #tag3
This is section 2 in doc1.
""")
        
        doc2 = self.repo.create_doc("doc2")
        doc2.update_text("""## Section 1 #tag1
This is section 1 in doc2.

## Section 2 #tag4
This is section 2 in doc2.
""")
        
        # Get sections with tag1
        sections = self.repo.get_sections_with_tags(["tag1"])
        
        # Check if sections were retrieved properly
        self.assertEqual(len(sections), 2, "Should find sections in 2 documents")
        self.assertIn("doc1", sections, "Should find sections in doc1")
        self.assertIn("doc2", sections, "Should find sections in doc2")
        self.assertEqual(len(sections["doc1"]), 1, "Should find 1 section in doc1")
        self.assertEqual(len(sections["doc2"]), 1, "Should find 1 section in doc2")
        
        # Get sections with tag2 and tag3
        sections = self.repo.get_sections_with_tags(["tag2", "tag3"])
        
        # Check if sections were retrieved properly
        self.assertEqual(len(sections), 1, "Should find sections in 1 document")
        self.assertIn("doc1", sections, "Should find sections in doc1")
        self.assertEqual(len(sections["doc1"]), 1, "Should find 1 section in doc1")
        self.assertIn("Section 2", sections["doc1"][0], "Should find Section 2")
    
    def test_get_sections_with_tags_invalid_tag(self):
        """Test getting sections with invalid tags."""
        with self.assertRaises(ValueError, msg="Should reject invalid tag"):
            self.repo.get_sections_with_tags(["tag/1"])
    
    def test_list_docs(self):
        """Test listing all documents."""
        # Initially, there should be no documents
        docs = self.repo.list_docs()
        self.assertEqual(docs, [], "Initially, there should be no documents")
        
        # Create some documents
        self.repo.create_doc("doc1")
        self.repo.create_doc("doc2")
        self.repo.create_doc("doc3")
        
        # List documents
        docs = self.repo.list_docs()
        
        # Check if all documents are listed
        self.assertEqual(len(docs), 3, "Should list 3 documents")
        self.assertIn("doc1", docs, "Should list doc1")
        self.assertIn("doc2", docs, "Should list doc2")
        self.assertIn("doc3", docs, "Should list doc3")
        
        # Delete a document
        self.repo.delete_doc("doc2")
        
        # List documents again
        docs = self.repo.list_docs()
        
        # Check if the document was removed from the list
        self.assertEqual(len(docs), 2, "Should list 2 documents after deletion")
        self.assertIn("doc1", docs, "Should still list doc1")
        self.assertIn("doc3", docs, "Should still list doc3")
        self.assertNotIn("doc2", docs, "Should not list deleted doc2")
    
    def test_list_all_tags(self):
        """Test listing all tags across all documents."""
        # Create documents with tags
        doc1 = self.repo.create_doc("doc1")
        doc1.update_text("""## Section 1 #tag1 #tag2
This is section 1.

## Section 2 #tag3
This is section 2.
""")
        
        doc2 = self.repo.create_doc("doc2")
        doc2.update_text("""## Section 1 #tag2 #tag4
This is section 1.

## Section 2 #tag5
This is section 2.
""")
        
        # List all tags
        tags = self.repo.list_all_tags()
        
        # Check if all tags are listed
        self.assertEqual(len(tags), 5, "Should list 5 tags")
        expected_tags = ["tag1", "tag2", "tag3", "tag4", "tag5"]
        for tag in expected_tags:
            self.assertIn(tag, tags, f"Should list {tag}")
    
    def test_list_property_values(self):
        """Test listing all unique values for a property."""
        # Create documents with different property values
        self.repo.create_doc("doc1", initial_properties={"status": "draft", "priority": 1})
        self.repo.create_doc("doc2", initial_properties={"status": "review", "priority": 2})
        self.repo.create_doc("doc3", initial_properties={"status": "final", "priority": 1})
        self.repo.create_doc("doc4", initial_properties={"status": "draft", "priority": 3})
        
        # List all status values
        status_values = self.repo.list_property_values("status")
        
        # Check if all unique values are listed
        self.assertEqual(len(status_values), 3, "Should list 3 unique status values")
        expected_values = ["draft", "review", "final"]
        for value in expected_values:
            self.assertIn(value, status_values, f"Should list status '{value}'")
        
        # List all priority values
        priority_values = self.repo.list_property_values("priority")
        
        # Check if all unique values are listed
        self.assertEqual(len(priority_values), 3, "Should list 3 unique priority values")
        self.assertEqual(priority_values, [1, 2, 3], "Should list priorities in order")
        
        # List values for a property that doesn't exist
        nonexistent_values = self.repo.list_property_values("nonexistent")
        self.assertEqual(nonexistent_values, [], "Should return empty list for non-existent property")
    
    def test_list_property_values_invalid_property(self):
        """Test listing values for an invalid property name."""
        with self.assertRaises(ValueError, msg="Should reject invalid property name"):
            self.repo.list_property_values("property/name")


# Additional integration tests

class TestDocRepoIntegration(unittest.TestCase):
    """Integration tests for Doc and DocRepo classes."""
    
    def setUp(self):
        """Set up the test environment before each test."""
        # Create a temporary directory for tests
        self.test_dir = tempfile.mkdtemp()
        
        # Set up a logger for testing
        self.logger = logging.getLogger('test_integration_logger')
        self.logger.setLevel(logging.DEBUG)
        
        # Create a document repository for testing
        self.repo = DocRepo(self.test_dir, self.logger)
    
    def tearDown(self):
        """Clean up after each test."""
        # Remove the temporary directory and its contents
        shutil.rmtree(self.test_dir)
    
    def test_complete_and_rollback_workflow(self):
        """Test complete and rollback in a typical workflow."""
        # Create a document
        doc = self.repo.create_doc("test_doc", 
                                 initial_properties={"type": "note"},
                                 initial_text="Initial content.")
        
        # Check initial state
        self.assertFalse(doc.get_property("complete"), "Document should start as incomplete")
        self.assertEqual(doc.get_property("version"), 1, "Document should start at version 1")
        
        # Simulate LLM processing - first update
        try:
            # Successful LLM update
            doc.update_text("Updated by LLM: First update.")
            doc.set_property("status", "processed")
            
            # Mark as complete
            doc.complete()
            self.assertTrue(doc.get_property("complete"), "Document should be marked as complete")
        except Exception:
            # If error occurs, rollback
            success = doc.rollback()
            self.assertTrue(success, "Rollback should succeed")
        
        # Document should be complete and at version 2
        self.assertTrue(doc.get_property("complete"), "Document should still be complete")
        self.assertEqual(doc.get_property("version"), 2, "Document should be at version 2")
        
        # Try another update and then roll back
        doc.set_property("complete", False)  # Make document incomplete again
        
        try:
            # Simulate a failed LLM update
            doc.update_text("Updated by LLM: This will be rolled back.")
            raise Exception("Simulated LLM error")
        except Exception:
            # Rollback should succeed since doc is incomplete
            success = doc.rollback()
            self.assertTrue(success, "Rollback should succeed")
        
        # Document should be back to previous state
        self.assertEqual(doc.get_text(), "Updated by LLM: First update.", 
                         "Document content should be rolled back")
        self.assertEqual(doc.get_property("version"), 2, 
                         "Document version should remain at 2 after rollback")
    
    def test_multiple_documents_with_shared_tags(self):
        """Test working with multiple documents that share tags."""
        # Create multiple documents with shared tags
        doc1 = self.repo.create_doc("meeting_notes")
        doc1.update_text("""## Team Meeting #meeting #team #important
Discussed project timeline.

## Action Items #action #team
1. Complete feature X
2. Review pull requests
""")
        
        doc2 = self.repo.create_doc("project_plan")
        doc2.update_text("""## Overview #project #important
Project scope and objectives.

## Timeline #project #schedule
Milestones and deadlines.

## Team Members #team
List of team members and roles.
""")
        
        doc3 = self.repo.create_doc("research_notes")
        doc3.update_text("""## Research Findings #research
Key findings from the literature.

## Future Work #research #action
Potential directions for future research.
""")
        
        # Find all important sections
        important_sections = self.repo.get_sections_with_tags(["important"])
        self.assertEqual(len(important_sections), 2, "Should find important sections in 2 documents")
        self.assertIn("meeting_notes", important_sections, "Should find in meeting_notes")
        self.assertIn("project_plan", important_sections, "Should find in project_plan")
        
        # Find all team-related sections
        team_sections = self.repo.get_sections_with_tags(["team"])
        self.assertEqual(len(team_sections), 2, "Should find team sections in 2 documents")
        self.assertEqual(len(team_sections["meeting_notes"]), 2, "Should find 2 team sections in meeting_notes")
        self.assertEqual(len(team_sections["project_plan"]), 1, "Should find 1 team section in project_plan")
        
        # Find all action items
        action_sections = self.repo.get_sections_with_tags(["action"])
        self.assertEqual(len(action_sections), 2, "Should find action sections in 2 documents")
        
        # Test adding a new tag to a section
        doc1.add_tag_to_section("Action Items", "priority")
        
        # Find sections with both action and priority tags
        action_priority_sections = self.repo.get_sections_with_tags(["action", "priority"])
        self.assertEqual(len(action_priority_sections), 1, "Should find section with both tags")
        self.assertIn("meeting_notes", action_priority_sections, "Should find in meeting_notes")
    
    def test_document_versioning_and_reversion(self):
        """Test document versioning and reversion in a complex scenario."""
        # Create a document
        doc = self.repo.create_doc("versioned_doc")
        
        # Create several versions with different content and properties
        versions_content = {
            1: "",  # Initial empty content
            2: "Version 2 content.",
            3: "Version 3 content with more details.",
            4: "Version 4 with even more content and revisions."
        }
        
        versions_properties = {
            1: {},
            2: {"status": "draft"},
            3: {"status": "review", "reviewer": "John"},
            4: {"status": "final", "reviewer": "Jane", "approved": True}
        }
        
        # Create the versions
        for version in range(2, 5):  # Versions 2-4
            doc.update_text(versions_content[version])
            for key, value in versions_properties[version].items():
                doc.set_property(key, value)
        
        # Verify current state
        self.assertEqual(doc.get_text(), versions_content[4], "Current content should be version 4")
        self.assertEqual(doc.get_property("status"), "final", "Status should be final")
        self.assertEqual(doc.get_property("approved"), True, "Document should be approved")
        
        # Get all versions
        all_versions = doc.get_versions()
        self.assertEqual(set(all_versions), {1, 2, 3, 4}, "Should have versions 1-4")
        
        # Check content of each version
        for version in range(1, 5):
            self.assertEqual(doc.get_version_text(version), versions_content[version],
                            f"Content of version {version} should match")
        
        # Check properties of each version
        for version in range(1, 5):
            props = doc.get_version_properties(version)
            
            # Check each expected property
            for key, expected_value in versions_properties[version].items():
                self.assertEqual(props.get(key), expected_value,
                                f"Property {key} of version {version} should match")
        
        # Revert to version 2
        doc.revert_to_version(2)
        
        # Verify state after reversion
        self.assertEqual(doc.get_text(), versions_content[2], "Content should be reverted to version 2")
        self.assertEqual(doc.get_property("status"), "draft", "Status should be reverted to draft")
        self.assertNotIn("reviewer", doc.get_properties(), "Reviewer property should be gone")
        self.assertNotIn("approved", doc.get_properties(), "Approved property should be gone")
        
        # Version should be incremented
        self.assertEqual(doc.get_property("version"), 5, "Version should be incremented to 5 after revert")


if __name__ == '__main__':
    unittest.main()