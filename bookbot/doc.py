import os
import json
import re
import shutil
import datetime
import logging
import tempfile
from typing import Dict, List, Any, Optional, Set, Tuple, Union


class Doc:
    def __init__(self, name: str, repo_path: str, logger: Optional[logging.Logger] = None):
        """
        Initialize a Doc object.
        
        Args:
            name (str): Name of the document without extension (e.g., 'chapter1')
            repo_path (str): Path to the repository directory
            logger (Optional[logging.Logger]): Logger instance for logging operations
        
        Raises:
            ValueError: If the document name contains invalid characters
        """
        # Validate document name to prevent path traversal
        self._validate_name(name)
        
        self.name = name
        self.repo_path = os.path.abspath(repo_path)  # Use absolute path
        self.md_file = os.path.join(self.repo_path, f"{name}.md")
        self.json_file = os.path.join(self.repo_path, f"{name}.json")
        self.history_dir = os.path.join(self.repo_path, "history")
        self.logger = logger or logging.getLogger(__name__)
        
        # Create history directory if it doesn't exist
        try:
            os.makedirs(self.history_dir, exist_ok=True)
            self.logger.debug(f"Ensured history directory exists at {self.history_dir}")
        except OSError as e:
            self.logger.error(f"Failed to create history directory: {e}")
            raise RuntimeError(f"Failed to create history directory: {e}") from e
        
        # Initialize files if they don't exist
        if not os.path.exists(self.md_file):
            # Create a new document with default properties
            self.logger.debug(f"Creating new document {self.md_file}")
            timestamp = datetime.datetime.now().isoformat()
            default_properties = {
                "filename": f"{name}.md",
                "version": 1,
                "creation_time": timestamp,
                "complete": False  # Initial state is incomplete
            }
            try:
                self._save_properties_and_text(default_properties, "")
            except Exception as e:
                self.logger.error(f"Failed to initialize document {name}: {e}")
                raise RuntimeError(f"Failed to initialize document {name}: {e}") from e
        
        if not os.path.exists(self.json_file):
            # Create empty JSON file
            self.logger.debug(f"Creating new JSON file {self.json_file}")
            try:
                with open(self.json_file, 'w') as f:
                    json.dump({}, f, indent=2)
            except Exception as e:
                self.logger.error(f"Failed to initialize JSON file for {name}: {e}")
                raise RuntimeError(f"Failed to initialize JSON file for {name}: {e}") from e
    
    @staticmethod
    def _validate_name(name: str) -> None:
        """
        Validate document name to prevent path traversal and ensure valid filename.
        
        Args:
            name (str): The document name to validate
            
        Raises:
            ValueError: If the document name contains invalid characters
        """
        print("validate name", name)
        # Check for path traversal attempts
        if os.path.sep in name or (os.path.altsep and os.path.altsep in name):
            raise ValueError(f"Invalid document name: {name} (contains path separators)")
        
        # Check for valid filename characters (allow letters, numbers, underscore, hyphen, period)
        if not re.match(r'^[\w\-\.]+$', name):
            raise ValueError(f"Invalid document name: {name} (contains invalid characters)")
        
        # Check if name starts with a dot (hidden file)
        if name.startswith('.'):
            raise ValueError(f"Invalid document name: {name} (cannot start with a dot)")
        
        if name.endswith('.'):
            raise ValueError(f"Invalid document name: {name} (cannot end with a dot)")
    
    @staticmethod
    def _validate_property_key(key: str) -> None:
        """
        Validate property key to ensure it contains valid characters.
        
        Args:
            key (str): The property key to validate
            
        Raises:
            ValueError: If the property key contains invalid characters
        """
        if not re.match(r'^[\w\-\.]+$', key):
            raise ValueError(f"Invalid property key: {key} (contains invalid characters)")
    
    @staticmethod
    def _validate_tag(tag: str) -> None:
        """
        Validate tag to ensure it contains valid characters.
        
        Args:
            tag (str): The tag to validate (with or without # prefix)
            
        Raises:
            ValueError: If the tag contains invalid characters
        """
        tag = tag.lstrip('#')
        if not re.match(r'^\w+$', tag):
            raise ValueError(f"Invalid tag: {tag} (must contain only alphanumeric characters and underscore)")
    
    def get_text(self) -> str:
        """
        Get the text content of the current version (excluding properties).
        
        Returns:
            str: The document text content
        
        Raises:
            RuntimeError: If there's an error reading the document
        """
        try:
            properties, text = self._load_properties_and_text()
            self.logger.debug(f"Retrieved text content for {self.name}")
            return text
        except Exception as e:
            self.logger.error(f"Error retrieving text for {self.name}: {e}")
            raise RuntimeError(f"Error retrieving text for {self.name}: {e}") from e
    
    def get_properties(self) -> Dict[str, Any]:
        """
        Get all properties of the current version as a dictionary.
        
        Returns:
            Dict[str, Any]: Document properties
        
        Raises:
            RuntimeError: If there's an error reading the document properties
        """
        try:
            properties, _ = self._load_properties_and_text()
            self.logger.debug(f"Retrieved properties for {self.name}")
            return properties
        except Exception as e:
            self.logger.error(f"Error retrieving properties for {self.name}: {e}")
            raise RuntimeError(f"Error retrieving properties for {self.name}: {e}") from e
    
    def get_property(self, key: str, default: Any = None) -> Any:
        """
        Get a specific property value.
        
        Args:
            key (str): The property key
            default (Any, optional): Default value if property doesn't exist
            
        Returns:
            Any: Property value or default if not found
        
        Raises:
            ValueError: If the property key is invalid
        """
        self._validate_property_key(key)
        properties = self.get_properties()
        value = properties.get(key, default)
        self.logger.debug(f"Retrieved property {key}={value} for {self.name}")
        return value
    
    def has_property(self, key: str) -> bool:
        """
        Check if a specific property exists.
        
        Args:
            key (str): The property key to check
            
        Returns:
            bool: True if property exists, False otherwise
        
        Raises:
            ValueError: If the property key is invalid
        """
        self._validate_property_key(key)
        properties = self.get_properties()
        exists = key in properties
        self.logger.debug(f"Checked if property {key} exists for {self.name}: {exists}")
        return exists
    
    def set_property(self, key: str, value: Any) -> None:
        """
        Set a property value.
        
        Args:
            key (str): The property key
            value (Any): The property value
        
        Raises:
            ValueError: If the property key is invalid
            RuntimeError: If there's an error saving the property
        """
        self._validate_property_key(key)
        
        try:
            properties, text = self._load_properties_and_text()
            
            # Handle special case for total_* properties
            if key.startswith("total_") and key in properties and isinstance(value, (int, float)) and isinstance(properties[key], (int, float)):
                properties[key] += value
                self.logger.debug(f"Incremented property {key} by {value} for {self.name}")
            else:
                properties[key] = value
                self.logger.debug(f"Set property {key}={value} for {self.name}")
            
            self._save_properties_and_text(properties, text)
        except Exception as e:
            self.logger.error(f"Error setting property {key} for {self.name}: {e}")
            raise RuntimeError(f"Error setting property {key} for {self.name}: {e}") from e
    
    def update_text(self, new_text: str, incr_version: bool = True) -> None:
        """
        Update the text content, creating a new version.
        
        Args:
            new_text (str): New text content for the document
        
        Raises:
            RuntimeError: If there's an error updating the text
        """
        try:
            properties, _ = self._load_properties_and_text()
            
            # Archive the current version
            current_version = properties.get("version", 0)
            self._archive_current_version(current_version)
            
            # Update version number
            if incr_version:
                properties["version"] = current_version + 1
            
            # Save new version
            self._save_properties_and_text(properties, new_text)
            self.logger.debug(f"Updated text for {self.name}, new version: {current_version + 1}")
        except Exception as e:
            self.logger.error(f"Error updating text for {self.name}: {e}")
            raise RuntimeError(f"Error updating text for {self.name}: {e}") from e
    
    def append_text(self, text_to_append: str) -> None:
        """
        Append text to the document and save it.
        
        Args:
            text_to_append (str): Text to append to the document
        
        Raises:
            RuntimeError: If there's an error appending text
        """
        try:
            properties, text = self._load_properties_and_text()
            new_text = text + text_to_append
            self._save_properties_and_text(properties, new_text)
            self.logger.debug(f"Appended {len(text_to_append)} characters to {self.name}")
        except Exception as e:
            self.logger.error(f"Error appending text to {self.name}: {e}")
            raise RuntimeError(f"Error appending text to {self.name}: {e}") from e
    
    def get_sections_with_tags(self, tags: List[str]=None) -> List[str]:
        """
        Get sections that contain all specified tags.
        
        Args:
            tags (List[str]): List of tags to search for. 
        
        Returns:
            List[str]: List of section texts that match the tags
        
        Raises:
            ValueError: If any of the tags are invalid
        """
        # Validate tags
        for tag in tags:
            self._validate_tag(tag)
        
        try:
            _, text = self._load_properties_and_text()
            
            # Normalize tags to make comparison case-insensitive
            normalize = lambda tag: tag.lower().strip('#')
            normalized_tags = [normalize(tag) for tag in tags]
            
            # Extract sections using regular expressions
            # Looking for Markdown headers followed by content
            sections = []
            
            # Match headers (## Header #tag1 #tag2) and their content
            pattern = r'(#+\s+.*?(?:\s+#\w+)*?)(?=\n#+\s+|\n*$)(.*?)(?=\n#+\s+|\n*$)'
            matches = re.finditer(pattern, text, re.DOTALL)
            
            for match in matches:
                header = match.group(1).strip()
                content = match.group(2).strip()
                
                # Extract tags from the header
                header_tags = re.findall(r'#(\w+)', header)
                normalized_header_tags = [normalize(tag) for tag in header_tags]
                
                # Check if all requested tags are in the section
                if all(tag in normalized_header_tags for tag in normalized_tags):
                    sections.append(f"{header}\n{content}")
            
            self.logger.debug(f"Found {len(sections)} sections with tags {tags} in {self.name}")
            return sections
        except Exception as e:
            self.logger.error(f"Error getting sections with tags {tags} in {self.name}: {e}")
            raise RuntimeError(f"Error getting sections with tags {tags} in {self.name}: {e}") from e
    
    def add_tag_to_section(self, section_header: str, tag: str) -> bool:
        """
        Add a tag to a specific section.
        
        Args:
            section_header (str): The section header text to identify the section
            tag (str): The tag to add (without the # symbol)
        
        Returns:
            bool: True if successful, False if section not found
        
        Raises:
            ValueError: If the tag is invalid
            RuntimeError: If there's an error updating the document
        """
        self._validate_tag(tag)
        
        # Ensure tag format
        tag = tag.strip()
        if not tag.startswith('#'):
            tag = f"#{tag}"
        
        try:
            properties, text = self._load_properties_and_text()
            
            # Find the section header
            # This regex looks for the exact section header
            pattern = f"(#+\\s+{re.escape(section_header.strip())}(?:\\s+#\\w+)*)"
            match = re.search(pattern, text)
            
            if not match:
                self.logger.debug(f"Section header '{section_header}' not found in {self.name}")
                return False
            
            header = match.group(1)
            
            # Check if tag already exists
            if tag.lower() in header.lower():
                self.logger.debug(f"Tag {tag} already exists in section '{section_header}' in {self.name}")
                return True
            
            # Add tag to the header
            new_header = f"{header} {tag}"
            new_text = text.replace(header, new_header)
            
            # Save modified text
            self._save_properties_and_text(properties, new_text)
            self.logger.debug(f"Added tag {tag} to section '{section_header}' in {self.name}")
            return True
        except Exception as e:
            self.logger.error(f"Error adding tag {tag} to section '{section_header}' in {self.name}: {e}")
            raise RuntimeError(f"Error adding tag {tag} to section '{section_header}' in {self.name}: {e}") from e
    
    def get_versions(self) -> List[int]:
        """
        Get list of all available versions.
        
        Returns:
            List[int]: List of version numbers
        
        Raises:
            RuntimeError: If there's an error accessing the history directory
        """
        try:
            versions = []
            # Check current version
            properties, _ = self._load_properties_and_text()
            current_version = properties.get("version", 1)
            versions.append(current_version)
            
            # Check archived versions
            pattern = f"{self.name}_v(\\d+)\\.md"
            for filename in os.listdir(self.history_dir):
                match = re.match(pattern, filename)
                if match:
                    versions.append(int(match.group(1)))
            
            self.logger.debug(f"Retrieved {len(versions)} versions for {self.name}: {versions}")
            return sorted(versions)
        except Exception as e:
            self.logger.error(f"Error retrieving versions for {self.name}: {e}")
            raise RuntimeError(f"Error retrieving versions for {self.name}: {e}") from e
    
    def get_version_text(self, version: int) -> str:
        """
        Get text content of a specific version.
        
        Args:
            version (int): Version number
        
        Returns:
            str: Text content of the specified version
        
        Raises:
            ValueError: If version not found
            RuntimeError: If there's an error reading the version
        """
        try:
            properties, _ = self._load_properties_and_text()
            current_version = properties.get("version", 1)
            
            if version == current_version:
                return self.get_text()
            
            # Look in history directory
            version_md_file = os.path.join(self.history_dir, f"{self.name}_v{version}.md")
            
            if not os.path.exists(version_md_file):
                error_msg = f"Version {version} not found for {self.name}"
                self.logger.error(error_msg)
                raise ValueError(error_msg)
            
            _, text = self._load_properties_and_text_from_file(version_md_file)
            self.logger.debug(f"Retrieved text for version {version} of {self.name}")
            return text
        except ValueError:
            raise
        except Exception as e:
            self.logger.error(f"Error retrieving text for version {version} of {self.name}: {e}")
            raise RuntimeError(f"Error retrieving text for version {version} of {self.name}: {e}") from e
    
    def get_version_properties(self, version: int) -> Dict[str, Any]:
        """
        Get properties of a specific version.
        
        Args:
            version (int): Version number
        
        Returns:
            Dict[str, Any]: Properties of the specified version
        
        Raises:
            ValueError: If version not found
            RuntimeError: If there's an error reading the version properties
        """
        try:
            properties, _ = self._load_properties_and_text()
            current_version = properties.get("version", 1)
            
            if version == current_version:
                return properties
            
            # Look in history directory
            version_md_file = os.path.join(self.history_dir, f"{self.name}_v{version}.md")
            
            if not os.path.exists(version_md_file):
                error_msg = f"Version {version} not found for {self.name}"
                self.logger.error(error_msg)
                raise ValueError(error_msg)
            
            props, _ = self._load_properties_and_text_from_file(version_md_file)
            self.logger.debug(f"Retrieved properties for version {version} of {self.name}")
            return props
        except ValueError:
            raise
        except Exception as e:
            self.logger.error(f"Error retrieving properties for version {version} of {self.name}: {e}")
            raise RuntimeError(f"Error retrieving properties for version {version} of {self.name}: {e}") from e
        
    def revert_to_version(self, version: int) -> None:
        """
        Revert to a previous version, creating a new version with the same content and properties.
        
        Args:
            version (int): Version number to revert to
        
        Raises:
            ValueError: If version not found
            RuntimeError: If there's an error reverting to the version
        """
        try:
            if version not in self.get_versions():
                error_msg = f"Version {version} not found for {self.name}"
                self.logger.error(error_msg)
                raise ValueError(error_msg)
            
            # Get the properties and text of the version to revert to
            old_props = self.get_version_properties(version)
            old_text = self.get_version_text(version)
            
            # Archive current version
            current_properties, _ = self._load_properties_and_text()
            current_version = current_properties.get("version", 1)
            self._archive_current_version(current_version)
            
            # Increment version number for the new revision
            new_version = current_version + 1
            # Prepare reverted properties: copy the properties from the archived version,
            # but update the version number to the new version
            reverted_props = old_props.copy()
            reverted_props["version"] = new_version
            
            # Save the new version with reverted properties and text
            self._save_properties_and_text(reverted_props, old_text)
            self.logger.debug(f"Reverted {self.name} to version {version}, new version is {new_version}")
        except ValueError:
            raise
        except Exception as e:
            self.logger.error(f"Error reverting {self.name} to version {version}: {e}")
            raise RuntimeError(f"Error reverting {self.name} to version {version}: {e}") from e

    def complete(self) -> None:
        """
        Mark a document as complete, which prevents further rollbacks.
        
        Raises:
            RuntimeError: If there's an error marking the document as complete
        """
        try:
            self.set_property("complete", True)
            self.logger.debug(f"Marked document {self.name} as complete")
        except Exception as e:
            self.logger.error(f"Error marking document {self.name} as complete: {e}")
            raise RuntimeError(f"Error marking document {self.name} as complete: {e}") from e
            
    def rollback(self) -> bool:
        """
        Rollback the most recent changes if the document is not marked as complete.
        This replaces the current version with the most recent history version.
        
        Returns:
            bool: True if rollback was successful, False if document is already complete
                  or there are no previous versions to roll back to
        
        Raises:
            RuntimeError: If there's an error during rollback
        """
        try:
            # Check if document is marked as complete
            if self.get_property("complete", False):
                self.logger.warning(f"Cannot rollback document {self.name} because it is marked as complete")
                return False
            
            # Get current version number
            properties, _ = self._load_properties_and_text()
            current_version = properties.get("version", 1)
            
            # If this is the first version, nothing to roll back to
            if current_version <= 1:
                self.logger.warning(f"Cannot rollback document {self.name} because it has no previous versions")
                return False
            
            # Get the previous version
            previous_version = current_version - 1
            
            # Path to the most recent history version
            version_md_file = os.path.join(self.history_dir, f"{self.name}_v{previous_version}.md")
            version_json_file = os.path.join(self.history_dir, f"{self.name}_v{previous_version}.json")
            
            # Check if history files exist
            if not (os.path.exists(version_md_file) and os.path.exists(version_json_file)):
                self.logger.error(f"Cannot rollback {self.name}: history files for version {previous_version} not found")
                return False
            
            # Copy history files to current files (without creating a new version)
            shutil.copy2(version_md_file, self.md_file)
            shutil.copy2(version_json_file, self.json_file)
            
            self.logger.debug(f"Rolled back document {self.name} from version {current_version} to {previous_version}")
            return True
        except Exception as e:
            self.logger.error(f"Error rolling back document {self.name}: {e}")
            raise RuntimeError(f"Error rolling back document {self.name}: {e}") from e
    
    def get_json_data(self) -> Dict[str, Any]:
        """
        Get the contents of the companion JSON file as a Python object.
        
        Returns:
            Dict[str, Any]: JSON file contents
        
        Raises:
            RuntimeError: If there's an error reading the JSON file
        """
        try:
            with open(self.json_file, 'r') as f:
                data = json.load(f)
            self.logger.debug(f"Retrieved JSON data for {self.name}")
            return data
        except json.JSONDecodeError as e:
            self.logger.warning(f"JSON decode error for {self.name}, returning empty dict: {e}")
            return {}
        except FileNotFoundError:
            self.logger.warning(f"JSON file not found for {self.name}, returning empty dict")
            return {}
        except Exception as e:
            self.logger.error(f"Error retrieving JSON data for {self.name}: {e}")
            raise RuntimeError(f"Error retrieving JSON data for {self.name}: {e}") from e
    
    def set_json_data(self, data: Dict[str, Any]) -> None:
        """
        Set the contents of the companion JSON file.
        
        Args:
            data (Dict[str, Any]): A Python structure to be JSON serialized
        
        Raises:
            RuntimeError: If there's an error saving the JSON data
        """
        try:
            # Create a temporary file for atomic write
            temp_fd, temp_path = tempfile.mkstemp(dir=os.path.dirname(self.json_file))
            try:
                with os.fdopen(temp_fd, 'w') as f:
                    json.dump(data, f, indent=2)
                # Atomic replace
                os.replace(temp_path, self.json_file)
                self.logger.debug(f"Saved JSON data for {self.name}")
            except Exception as e:
                # Clean up the temp file if an error occurs
                os.unlink(temp_path)
                raise e
        except Exception as e:
            self.logger.error(f"Error saving JSON data for {self.name}: {e}")
            raise RuntimeError(f"Error saving JSON data for {self.name}: {e}") from e
    
    def _archive_current_version(self, version: int) -> None:
        """
        Archive the current version of the document.
        
        Args:
            version (int): Current version number
        
        Raises:
            RuntimeError: If there's an error archiving the current version
        """
        try:
            # Copy current files to history directory
            version_md_file = os.path.join(self.history_dir, f"{self.name}_v{version}.md")
            version_json_file = os.path.join(self.history_dir, f"{self.name}_v{version}.json")
            
            shutil.copy2(self.md_file, version_md_file)
            shutil.copy2(self.json_file, version_json_file)
            self.logger.debug(f"Archived version {version} of {self.name}")
        except Exception as e:
            self.logger.error(f"Error archiving version {version} of {self.name}: {e}")
            raise RuntimeError(f"Error archiving version {version} of {self.name}: {e}") from e
    
    def _load_properties_and_text(self) -> Tuple[Dict[str, Any], str]:
        """
        Load properties and text from the markdown file.
        
        Returns:
            Tuple[Dict[str, Any], str]: Properties and text content
        
        Raises:
            RuntimeError: If there's an error loading properties and text
        """
        return self._load_properties_and_text_from_file(self.md_file)
    
    def _load_properties_and_text_from_file(self, file_path: str) -> Tuple[Dict[str, Any], str]:
        """
        Load properties and text from a specific markdown file.
        
        Args:
            file_path (str): Path to the markdown file
            
        Returns:
            Tuple[Dict[str, Any], str]: Properties and text content
        
        Raises:
            RuntimeError: If there's an error loading properties and text from the file
        """
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Split properties and text
            parts = content.split('---', 1)
            
            if len(parts) == 2:
                properties_text, text = parts
                # Parse properties
                properties = {}
                for line in properties_text.strip().split('\n'):
                    if line.strip():
                        try:
                            key, value = line.split(':', 1)
                            properties[key.strip()] = self._parse_property_value(value.strip())
                        except ValueError:
                            self.logger.warning(f"Skipping invalid property line: {line}")
                return properties, text.strip()
            else:
                # No properties section
                return {}, content.strip()
        except FileNotFoundError:
            self.logger.warning(f"File not found: {file_path}, returning empty properties and text")
            return {}, ""
        except Exception as e:
            self.logger.error(f"Error loading properties and text from {file_path}: {e}")
            raise RuntimeError(f"Error loading properties and text from {file_path}: {e}") from e
    
    def _parse_property_value(self, value: str) -> Any:
        """
        Parse property value, attempting to convert to appropriate type.
        
        Args:
            value (str): String value to parse
            
        Returns:
            Any: Parsed value (int, float, bool, or str)
        """
        # Try to convert to numeric or boolean
        try:
            if value.lower() == 'true':
                return True
            elif value.lower() == 'false':
                return False
            elif '.' in value:
                return float(value)
            else:
                return int(value)
        except (ValueError, AttributeError):
            return value
    
    def _save_properties_and_text(self, properties: Dict[str, Any], text: str) -> None:
        """
        Save properties and text to the markdown file using safe atomic writes.
        
        Args:
            properties (Dict[str, Any]): Properties to save
            text (str): Text content to save
        
        Raises:
            RuntimeError: If there's an error saving properties and text
        """
        try:
            # Format properties section
            properties_text = '\n'.join([f"{key}: {value}" for key, value in properties.items()])
            
            # Combine properties and text
            content = f"{properties_text}\n---\n{text}"
            
            # Create a temporary file in the same directory
            temp_fd, temp_path = tempfile.mkstemp(dir=os.path.dirname(self.md_file))
            try:
                with os.fdopen(temp_fd, 'w') as f:
                    f.write(content)
                # Atomic replace
                os.replace(temp_path, self.md_file)
            except Exception as e:
                # Clean up the temp file if an error occurs
                os.unlink(temp_path)
                raise e
        except Exception as e:
            self.logger.error(f"Error saving properties and text for {self.name}: {e}")
            raise RuntimeError(f"Error saving properties and text for {self.name}: {e}") from e


    def get_all_tags(self) -> List[str]:
        """
        Get all unique tags used in the document.
        Only includes tags that aren't at the start of a line (excludes Markdown headers).
        
        Returns:
            List[str]: Sorted list of unique tags (without the # symbol)
        
        Raises:
            RuntimeError: If there's an error reading the document
        """
        try:
            text = self.get_text()
            
            # Find all tags that aren't at the start of a line
            # This regex matches a # that has a non-whitespace character before it
            # or is preceded by whitespace but not at the beginning of a line
            #TODO Use one regex for everything 
            tags = re.findall(r'(?<=\S)#(\w+)|(?<=\s)#(\w+)', text)
            
            # The regex will return tuples of (match1, match2) where one is empty
            # We need to flatten this list and remove empty strings
            flat_tags = []
            for match_pair in tags:
                flat_tags.extend([tag for tag in match_pair if tag])
            
            # Get unique tags and sort them
            unique_tags = sorted(set(flat_tags))
            
            self.logger.debug(f"Found {len(unique_tags)} unique tags in document {self.name}")
            return unique_tags
        except Exception as e:
            self.logger.error(f"Error getting tags for document {self.name}: {e}")
            raise RuntimeError(f"Error getting tags for document {self.name}: {e}") from e


class DocRepo:
    def __init__(self, repo_path: str, logger: Optional[logging.Logger] = None):
        """
        Initialize a DocRepo object.
        
        Args:
            repo_path (str): Path to the repository directory
            logger (Optional[logging.Logger]): Logger instance for logging operations
        
        Raises:
            RuntimeError: If the repository cannot be initialized
        """
        self.repo_path = os.path.abspath(repo_path)
        self.logger = logger or logging.getLogger(__name__)
        
        try:
            os.makedirs(repo_path, exist_ok=True)
            os.makedirs(os.path.join(repo_path, "history"), exist_ok=True)
            self.logger.debug(f"Initialized repository at {self.repo_path}")
        except OSError as e:
            self.logger.error(f"Failed to initialize repository: {e}")
            raise RuntimeError(f"Failed to initialize repository: {e}") from e
    
    def create_doc(self, name: str, initial_properties: Optional[Dict[str, Any]] = None, 
                  initial_text: str = "") -> Doc:
        """
        Create a new document and return the Doc object.
        
        Args:
            name (str): Document name without extension
            initial_properties (Dict[str, Any], optional): Initial properties
            initial_text (str, optional): Initial text content
            
        Returns:
            Doc: The created document object
        
        Raises:
            ValueError: If the document name is invalid
            RuntimeError: If the document cannot be created
        """
        try:
            doc = Doc(name, self.repo_path, self.logger)
            
            # Ensure the 'complete' property is set
            if initial_properties is None:
                initial_properties = {}
            if 'complete' not in initial_properties:
                initial_properties['complete'] = False
            
            # Set initial properties if provided
            for key, value in initial_properties.items():
                doc.set_property(key, value)
            
            # Set initial text if provided
            if initial_text:
                doc.update_text(initial_text, incr_version=False)
            
            self.logger.debug(f"Created document {name}")
            return doc
        except ValueError:
            # Re-raise validation errors
            raise
        except Exception as e:
            self.logger.error(f"Error creating document {name}: {e}")
            raise RuntimeError(f"Error creating document {name}: {e}") from e
    
    def delete_doc(self, name: str) -> bool:
        """
        Delete a document and all its versions.
        
        Args:
            name (str): Document name without extension
            
        Returns:
            bool: True if document was deleted, False if not found
        
        Raises:
            ValueError: If the document name is invalid
            RuntimeError: If the document cannot be deleted
        """
        # Validate document name
        Doc._validate_name(name)
        
        md_file = os.path.join(self.repo_path, f"{name}.md")
        json_file = os.path.join(self.repo_path, f"{name}.json")
        
        try:
            # Check if files exist
            if not (os.path.exists(md_file) or os.path.exists(json_file)):
                self.logger.debug(f"Document {name} not found for deletion")
                return False
            
            # Delete main files
            if os.path.exists(md_file):
                os.remove(md_file)
            if os.path.exists(json_file):
                os.remove(json_file)
            
            # Delete history files
            history_dir = os.path.join(self.repo_path, "history")
            for filename in os.listdir(history_dir):
                if filename.startswith(f"{name}_v") and (filename.endswith(".md") or filename.endswith(".json")):
                    os.remove(os.path.join(history_dir, filename))
            
            self.logger.debug(f"Deleted document {name} and its history")
            return True
        except Exception as e:
            self.logger.error(f"Error deleting document {name}: {e}")
            raise RuntimeError(f"Error deleting document {name}: {e}") from e
    
    def get_doc(self, name: str) -> Optional[Doc]:
        """
        Get a document by name and return the Doc object.
        
        Args:
            name (str): Document name without extension
            
        Returns:
            Optional[Doc]: The document object or None if not found
        
        Raises:
            ValueError: If the document name is invalid
        """
        # Validate document name
        try:
            Doc._validate_name(name)
        except ValueError as e:
            self.logger.error(f"Invalid document name in get_doc: {e}")
            raise
        
        md_file = os.path.join(self.repo_path, f"{name}.md")
        if not os.path.exists(md_file):
            self.logger.debug(f"Document {name} not found")
            return None
        
        self.logger.debug(f"Retrieved document {name}")
        return Doc(name, self.repo_path, self.logger)
    
    def get_docs_by_type(self, doc_type: str) -> List[Doc]:
        """
        Get all documents with a specific type property.
        
        Args:
            doc_type (str): The type value to filter by
        
        Returns:
            List[Doc]: List of Doc objects with the specified type
        """
        docs = []
        
        try:
            for name in self.list_docs():
                doc = self.get_doc(name)
                if doc and doc.get_property("type") == doc_type:
                    docs.append(doc)
            
            self.logger.debug(f"Found {len(docs)} documents with type '{doc_type}'")
            return docs
        except Exception as e:
            self.logger.error(f"Error getting documents by type '{doc_type}': {e}")
            raise RuntimeError(f"Error getting documents by type '{doc_type}': {e}") from e
    
    def get_sections_with_tags(self, tags: List[str]) -> Dict[str, List[str]]:
        """
        Get all sections from all documents that contain all specified tags.
        
        Args:
            tags (List[str]): List of tags to search for
            
        Returns:
            Dict[str, List[str]]: Format {'docname': [section1, section2, ...], ...}
        
        Raises:
            ValueError: If any of the tags are invalid
        """
        # Validate tags
        for tag in tags:
            Doc._validate_tag(tag)
        
        result = {}
        
        try:
            for name in self.list_docs():
                doc = self.get_doc(name)
                if doc:
                    sections = doc.get_sections_with_tags(tags)
                    
                    if sections:
                        result[name] = sections
            
            total_sections = sum(len(sections) for sections in result.values())
            self.logger.debug(f"Found {total_sections} sections with tags {tags} across {len(result)} documents")
            return result
        except ValueError:
            # Re-raise validation errors
            raise
        except Exception as e:
            self.logger.error(f"Error getting sections with tags {tags}: {e}")
            raise RuntimeError(f"Error getting sections with tags {tags}: {e}") from e
    
    def list_docs(self) -> List[str]:
        """
        List all document names in the repo.
        
        Returns:
            List[str]: List of document names without extensions
        
        Raises:
            RuntimeError: If there's an error accessing the repository
        """
        try:
            docs = set()
            
            for filename in os.listdir(self.repo_path):
                if filename.endswith(".md") and os.path.isfile(os.path.join(self.repo_path, filename)):
                    docs.add(filename[:-3])  # Remove .md extension
            
            result = sorted(list(docs))
            self.logger.debug(f"Listed {len(result)} documents in the repository")
            return result
        except Exception as e:
            self.logger.error(f"Error listing documents: {e}")
            raise RuntimeError(f"Error listing documents: {e}") from e
        
    def list_all_tags(self) -> List[str]:
        """
        List all unique tags used across all documents.
        Only includes tags that aren't at the start of a line (excludes Markdown headers).
        
        Returns:
            List[str]: List of unique tags
        
        Raises:
            RuntimeError: If there's an error accessing the documents
        """
        all_tags = set()
        
        try:
            for name in self.list_docs():
                doc = self.get_doc(name)
                if doc:
                    # Use the document's get_all_tags method
                    doc_tags = doc.get_all_tags()
                    all_tags.update(doc_tags)
            
            result = sorted(list(all_tags))
            self.logger.debug(f"Found {len(result)} unique tags across all documents")
            return result
        except Exception as e:
            self.logger.error(f"Error listing all tags: {e}")
            raise RuntimeError(f"Error listing all tags: {e}") from e

    def list_property_values(self, property_name: str) -> List[Any]:
        """
        List all unique values for a given property across all documents.
        
        Args:
            property_name (str): The property name to get values for
            
        Returns:
            List[Any]: List of unique values for the property
        
        Raises:
            ValueError: If the property name is invalid
            RuntimeError: If there's an error accessing the documents
        """
        # Validate property name
        Doc._validate_property_key(property_name)
        
        try:
            values = set()
            
            for name in self.list_docs():
                doc = self.get_doc(name)
                if doc:
                    value = doc.get_property(property_name)
                    
                    if value is not None:
                        values.add(value)
            
            result = sorted(list(values), key=lambda x: str(x))
            self.logger.debug(f"Found {len(result)} unique values for property '{property_name}'")
            return result
        except ValueError:
            # Re-raise validation errors
            raise
        except Exception as e:
            self.logger.error(f"Error listing property values for '{property_name}': {e}")
            raise RuntimeError(f"Error listing property values for '{property_name}': {e}") from e