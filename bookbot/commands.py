import os
import logging
import traceback
from typing import Dict, List, Any, Optional, Set

from action import Command, CommandRegistry
from doc import Doc, DocRepo
import outline_util

logger = logging.getLogger(__name__)


class WriteOutlineCommand(Command):
    """
    Command to generate just an outline for a book from an initial concept document.
    
    This command:
    1. Generates an outline using the outliner bot
    2. Ensures chapters are numbered correctly
    """
    
    @property
    def name(self) -> str:
        return "write-outline"
    
    @property
    def description(self) -> str:
        return "Generate a book outline from an initial concept"
    
    @property
    def usage(self) -> str:
        return "write-outline <initial_doc> [<output_name>]"
    
    @classmethod
    def get_arg_info(cls) -> Dict[str, str]:
        return {
            "initial_doc": "Name of document containing the initial book concept",
            "output_name": "Optional name for the output outline document (default: 'outline')"
        }
    
    def execute(self, args: List[str]) -> bool:
        """
        Execute the command to generate an outline.
        
        Args:
            args: Command arguments [initial_doc, output_name(optional)]
            
        Returns:
            True if successful, False otherwise
        """
        # Validate arguments
        if len(args) < 1:
            logger.error(f"Not enough arguments. Usage: {self.usage}")
            return False
        
        # Parse arguments
        initial_doc_name = args[0]
        output_name = args[1] if len(args) > 1 else "outline"
        
        # Get initial document
        initial_doc = self.doc_repo.get_doc(initial_doc_name)
        if not initial_doc:
            logger.error(f"Initial document '{initial_doc_name}' not found")
            return False
        
        # Record input document
        if hasattr(self, 'action'):
            self.action.record_input_doc(initial_doc_name)
        
        self.update_status(f"Generating outline from '{initial_doc_name}' to '{output_name}'")
        
        try:
            # Set up template variables
            template_vars = {
                "initial": initial_doc
            }
            
            # Generate the outline
            self.generate_content(
                output_doc_name=output_name,
                prompt_doc_name="bot_outliner",
                template_vars=template_vars,
                command=f"generate_outline_{output_name}"
            )
            
            # Record output document
            if hasattr(self, 'action'):
                self.action.record_output_doc(output_name)
            
            # Renumber chapters
            outline_doc = self.doc_repo.get_doc(output_name)
            if outline_doc:
                outline_text = outline_doc.get_text()
                
                # Renumber chapters
                fixed_outline = outline_util.renumber_chapters(outline_text)
                
                # Count chapters for information
                chapter_count = outline_util.count_chapters(fixed_outline)
                self.update_status(f"Outline contains {chapter_count} chapters")
                
                # Update the document
                outline_doc.update_text(fixed_outline)
            else:
                logger.warning(f"Could not renumber chapters: document '{output_name}' not found after generation")
            
            self.update_status(f"Successfully generated outline '{output_name}'")
            return True
            
        except Exception as e:
            self.update_status(f"Error generating outline: {str(e)}")
            logger.error(traceback.format_exc())
            return False


class WriteCommonCommand(Command):
    """
    Command to generate the common files (outline, characters, settings) for a book
    from an initial concept document.

    This will OVERWRITE the outline if it was already written!
    
    This command runs a sequence of operations:
    1. Generate an outline using the outliner bot
    2. Generate character sheets using the character_sheet bot
    3. Generate setting profiles using the settings bot
    4. Renumber chapters in the outline
    5. Update the outline with tags for characters and settings
    """
    
    @property
    def name(self) -> str:
        return "write-common"
    
    @property
    def description(self) -> str:
        return "Generate outline, character sheets, and settings from an initial concept"
    
    @property
    def usage(self) -> str:
        return "write-common <initial_doc>"
    
    @classmethod
    def get_arg_info(cls) -> Dict[str, str]:
        return {
            "initial_doc": "Name of document containing the initial book concept"
        }
    
    def execute(self, args: List[str]) -> bool:
        """
        Execute the command to generate common book files.
        
        Args:
            args: Command arguments [initial_doc]
            
        Returns:
            True if successful, False otherwise
        """
        # Validate arguments
        if len(args) < 1:
            logger.error(f"Not enough arguments. Usage: {self.usage}")
            return False
        
        # Parse arguments
        initial_doc_name = args[0]
        
        # Get initial document
        initial_doc = self.doc_repo.get_doc(initial_doc_name)
        if not initial_doc:
            logger.error(f"Initial document '{initial_doc_name}' not found")
            return False
        
        # Record input document
        if hasattr(self, 'action'):
            self.action.record_input_doc(initial_doc_name)
        
        try:
            # Step 1: Generate outline
            if not self._generate_outline(initial_doc):
                return False
            
            # Step 2: Generate character sheets
            if not self._generate_characters():
                return False
            
            # Step 3: Generate settings
            if not self._generate_settings():
                return False
            
            # Step 4: Renumber chapters
            if not self._renumber_chapters():
                return False
            
            # Step 5: Tag chapters
            if not self._tag_chapters():
                return False
            
            self.update_status("Successfully generated all common files")
            return True
            
        except Exception as e:
            self.update_status(f"Error generating common files: {str(e)}")
            logger.error(traceback.format_exc())
            return False
    
    def _generate_outline(self, initial_doc: Doc) -> bool:
        """
        Generate the outline document using the outliner bot.
        
        Args:
            initial_doc: Initial concept document
            
        Returns:
            True if successful, False otherwise
        """
        self.update_status("Generating outline document")
        
        try:
            # Check if outline already exists
            existing_outline = self.doc_repo.get_doc("outline")
            if existing_outline:
                logger.info("Outline document already exists, updating with new content")
            
            # Set up template variables
            template_vars = {
                "initial": initial_doc
            }
            
            # Generate the outline
            self.generate_content(
                output_doc_name="outline",
                prompt_doc_name="bot_outliner",
                template_vars=template_vars,
                command="generate_outline"
            )
            
            # Record output document
            if hasattr(self, 'action'):
                self.action.record_output_doc("outline")
            
            self.update_status("Successfully generated outline")
            return True
            
        except Exception as e:
            self.update_status(f"Error generating outline: {str(e)}")
            logger.error(traceback.format_exc())
            return False
    
    def _generate_characters(self) -> bool:
        """
        Generate the character sheets document using the character_sheet bot.
        
        Returns:
            True if successful, False otherwise
        """
        self.update_status("Generating character sheets")
        
        try:
            # Get the outline document
            outline_doc = self.doc_repo.get_doc("outline")
            if not outline_doc:
                logger.error("Outline document not found")
                return False
            
            # Set up template variables
            template_vars = {
                "outline": outline_doc,
                "initial": outline_doc  # character_sheet bot expects 'initial' as a fallback
            }
            
            # Generate the character sheets
            self.generate_content(
                output_doc_name="characters",
                prompt_doc_name="bot_character_sheet",
                template_vars=template_vars,
                command="generate_characters"
            )
            
            # Record output document
            if hasattr(self, 'action'):
                self.action.record_output_doc("characters")
            
            self.update_status("Successfully generated character sheets")
            return True
            
        except Exception as e:
            self.update_status(f"Error generating character sheets: {str(e)}")
            logger.error(traceback.format_exc())
            return False
    
    def _generate_settings(self) -> bool:
        """
        Generate the settings document using the settings bot.
        
        Returns:
            True if successful, False otherwise
        """
        self.update_status("Generating settings profiles")
        
        try:
            # Get the outline document
            outline_doc = self.doc_repo.get_doc("outline")
            if not outline_doc:
                logger.error("Outline document not found")
                return False
            
            # Set up template variables
            template_vars = {
                "outline": outline_doc,
                "initial": outline_doc  # settings bot expects 'initial' as a fallback
            }
            
            # Generate the settings
            self.generate_content(
                output_doc_name="settings",
                prompt_doc_name="bot_settings",
                template_vars=template_vars,
                command="generate_settings"
            )
            
            # Record output document
            if hasattr(self, 'action'):
                self.action.record_output_doc("settings")
            
            self.update_status("Successfully generated settings profiles")
            return True
            
        except Exception as e:
            self.update_status(f"Error generating settings profiles: {str(e)}")
            logger.error(traceback.format_exc())
            return False
    
    def _renumber_chapters(self) -> bool:
        """
        Renumber chapters in the outline document.
        
        Returns:
            True if successful, False otherwise
        """
        self.update_status("Renumbering chapters in outline")
        
        try:
            # Get the outline document
            outline_doc = self.doc_repo.get_doc("outline")
            if not outline_doc:
                logger.error("Outline document not found")
                return False
            
            # Get the text content
            outline_text = outline_doc.get_text()
            
            # Renumber chapters
            fixed_outline = outline_util.renumber_chapters(outline_text)
            
            # Count chapters for information
            chapter_count = outline_util.count_chapters(fixed_outline)
            self.update_status(f"Outline contains {chapter_count} chapters")
            
            # Update the document
            outline_doc.update_text(fixed_outline)
            
            self.update_status("Successfully renumbered chapters")
            return True
            
        except Exception as e:
            self.update_status(f"Error renumbering chapters: {str(e)}")
            logger.error(traceback.format_exc())
            return False
    
    def _tag_chapters(self) -> bool:
        """
        Update the outline with tags for characters and settings.
        
        Returns:
            True if successful, False otherwise
        """
        self.update_status("Tagging chapters in outline")
        
        try:
            # Get the necessary documents
            outline_doc = self.doc_repo.get_doc("outline")
            characters_doc = self.doc_repo.get_doc("characters")
            settings_doc = self.doc_repo.get_doc("settings")
            
            if not outline_doc:
                logger.error("Outline document not found")
                return False
            if not characters_doc:
                logger.error("Characters document not found")
                return False
            if not settings_doc:
                logger.error("Settings document not found")
                return False
            
            # Set up template variables
            template_vars = {
                "outline": outline_doc,
                "characters": characters_doc,
                "setting": settings_doc
            }
            
            # Generate the tagged outline
            self.generate_content(
                output_doc_name="outline",
                prompt_doc_name="bot_tagger",
                template_vars=template_vars,
                command="tag_outline"
            )
            
            self.update_status("Successfully tagged chapters in outline")
            return True
            
        except Exception as e:
            self.update_status(f"Error tagging chapters: {str(e)}")
            logger.error(traceback.format_exc())
            return False


# Register the command
CommandRegistry.register(WriteCommonCommand)
CommandRegistry.register(WriteOutlineCommand)
