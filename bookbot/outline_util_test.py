"""
Unit tests for the outline_util module.

This module tests all functions in outline_util.py, including edge cases and error handling.
"""

import unittest
from unittest.mock import patch, MagicMock
import logging
import re
import sys
import os

# Add parent directory to path to make imports work in test environment
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import outline_util

class TestOutlineUtil(unittest.TestCase):
    """Test cases for outline_util module functions."""

    def setUp(self):
        """Set up test fixtures."""
        # Sample outline with some common patterns and edge cases
        self.sample_outline = """# Section 1: Introduction

This is the introduction to the story, setting up the main themes.

## Chapter 1: The Beginning #john #mary #home
SETTING: John's home, living room
CHARACTERS: John Smith, Mary Johnson
TIMEFRAME: Monday morning, 9 AM

John wakes up and prepares for his day. Mary visits him to discuss their plans.

## Chapter 2: The Journey Begins #john #mary #train-station
SETTING: Central Train Station
CHARACTERS: John Smith, Mary Johnson, Ticket Seller
TIMEFRAME: Monday afternoon, 2 PM

John and Mary head to the train station to begin their adventure.

# Section 2: Development

The plot thickens as the characters face their first challenges.

## Chapter 3: Arrival #john #mary #bob #hotel
SETTING: Grand Hotel, lobby
CHARACTERS: John Smith, Mary Johnson, Bob Williams (hotel manager)
TIMEFRAME: Monday evening, 7 PM

The pair arrive at their destination and check into the hotel.

## Chapter 3: The Mistake #john #mysterious-package
SETTING: Hotel room
CHARACTERS: John Smith
TIMEFRAME: Monday night, 11 PM

John discovers a mysterious package in his luggage that doesn't belong to him.

## Chapter 5: The Chase #john #mary #bob #city-streets
SETTING: Downtown city streets
CHARACTERS: John Smith, Mary Johnson, Bob Williams, Unknown Pursuer
TIMEFRAME: Tuesday morning, 10 AM

John and Mary are pursued through the city by someone wanting the package.
"""

        # Sample character sheets
        self.sample_characters = """# John Smith #john
Age: 35
Occupation: Professor of archaeology
Description: Tall with brown hair and glasses, always wears a tweed jacket.

# Mary Johnson #mary
Age: 28
Occupation: Journalist
Description: Athletic build with short blonde hair, carries a notebook everywhere.

# Bob Williams #bob
Age: 42
Occupation: Hotel Manager
Description: Balding with a friendly smile, wears a formal uniform.

# Susan Parker #susan
Age: 31
Occupation: Museum Curator
Description: Long black hair, serious demeanor, dresses elegantly.
"""

        # Sample setting profiles
        self.sample_settings = """# John's Home #home
A cozy suburban house with a small garden.
Located in a quiet neighborhood with tree-lined streets.
The living room has comfortable furniture and walls lined with books.

# Central Train Station #train-station
A bustling transportation hub with high arched ceilings and marble floors.
Multiple platforms with trains arriving and departing regularly.
Crowds of travelers move through the main concourse at all hours.

# Grand Hotel #hotel
A luxury hotel in the heart of the city with art deco architecture.
The lobby features crystal chandeliers, marble columns, and plush seating.
Well-staffed with attentive employees in crisp uniforms.

# Downtown City Streets #city-streets
Busy urban thoroughfares with tall buildings and heavy traffic.
Narrow alleyways connect the main streets, offering shortcuts and hiding places.
Street vendors and cafes line the sidewalks.

# Mysterious Package #mysterious-package
A small leather-bound box with brass fittings.
Shows signs of age with worn edges and a patina on the metal.
Bears an unusual symbol embossed on the lid.
"""

    def test_renumber_chapters(self):
        """Test the renumber_chapters function with various inputs."""
        # Test normal case
        result = outline_util.renumber_chapters(self.sample_outline)
        
        # There should be 5 chapters numbered 1 through 5
        self.assertIn("## Chapter 1: The Beginning", result)
        self.assertIn("## Chapter 2: The Journey Begins", result)
        self.assertIn("## Chapter 3: Arrival", result)
        self.assertIn("## Chapter 4: The Mistake", result)
        self.assertIn("## Chapter 5: The Chase", result)
        
        # The original duplicate Chapter 3 should now be Chapter 4
        self.assertNotIn("## Chapter 3: The Mistake", result)
        
        # Test empty outline
        result = outline_util.renumber_chapters("")
        self.assertEqual("", result)
        
        # Test outline with no chapters
        no_chapters = "# Section 1\nThis is content without any chapters."
        result = outline_util.renumber_chapters(no_chapters)
        self.assertEqual(no_chapters, result)
        
        # Test outline with non-consecutive chapter numbers
        non_consecutive = """# Section 1
## Chapter 1: First
Content
## Chapter 5: Second
Content
## Chapter 10: Third
Content
"""
        result = outline_util.renumber_chapters(non_consecutive)
        self.assertIn("## Chapter 1: First", result)
        self.assertIn("## Chapter 2: Second", result)
        self.assertIn("## Chapter 3: Third", result)

    def test_count_chapters(self):
        """Test the count_chapters function with various inputs."""
        # Test normal case
        count = outline_util.count_chapters(self.sample_outline)
        self.assertEqual(5, count)
        
        # Test empty outline
        count = outline_util.count_chapters("")
        self.assertEqual(0, count)
        
        # Test outline with no chapters
        no_chapters = "# Section 1\nThis is content without any chapters."
        count = outline_util.count_chapters(no_chapters)
        self.assertEqual(0, count)

    def test_extract_tags(self):
        """Test the extract_tags function with various inputs."""
        # Test normal case with multiple tags
        chapter_heading = "## Chapter 1: The Beginning #john #mary #home"
        chapter_num, tags = outline_util.extract_tags(chapter_heading)
        self.assertEqual(1, chapter_num)
        self.assertEqual({"john", "mary", "home"}, tags)
        
        # Test with hyphenated tag
        chapter_heading = "## Chapter 2: Journey #train-station #john"
        chapter_num, tags = outline_util.extract_tags(chapter_heading)
        self.assertEqual(2, chapter_num)
        self.assertEqual({"train-station", "john"}, tags)
        
        # Test with no tags
        chapter_heading = "## Chapter 3: No Tags"
        chapter_num, tags = outline_util.extract_tags(chapter_heading)
        self.assertEqual(3, chapter_num)
        self.assertEqual(set(), tags)
        
        # Test with invalid heading
        chapter_heading = "# Section 1: Not a chapter"
        chapter_num, tags = outline_util.extract_tags(chapter_heading)
        self.assertEqual(0, chapter_num)
        self.assertEqual(set(), tags)

    def test_find_chapter_heading(self):
        """Test the find_chapter_heading function with various inputs."""
        # Test normal case
        heading = outline_util.find_chapter_heading(self.sample_outline, 1)
        self.assertEqual("## Chapter 1: The Beginning #john #mary #home", heading)
        
        # Test chapter that doesn't exist
        heading = outline_util.find_chapter_heading(self.sample_outline, 10)
        self.assertIsNone(heading)
        
        # Test with empty outline
        heading = outline_util.find_chapter_heading("", 1)
        self.assertIsNone(heading)

    def test_find_chapter_content(self):
        """Test the find_chapter_content function with various inputs."""
        # Test normal case (middle chapter)
        result = outline_util.find_chapter_content(self.sample_outline, 2)
        self.assertIsNotNone(result)
        heading, content, preceding = result
        
        self.assertEqual("## Chapter 2: The Journey Begins #john #mary #train-station", heading)
        self.assertTrue(content.startswith("SETTING: Central Train Station"))
        self.assertTrue(preceding.startswith("## Chapter 1: The Beginning"))
        
        # Test first chapter in a section
        result = outline_util.find_chapter_content(self.sample_outline, 1)
        self.assertIsNotNone(result)
        heading, content, preceding = result
        
        self.assertEqual("## Chapter 1: The Beginning #john #mary #home", heading)
        self.assertTrue(content.startswith("SETTING: John's home"))
        self.assertTrue(preceding.startswith("# Section 1: Introduction"))
        
        # Test first chapter in a later section
        result = outline_util.find_chapter_content(self.sample_outline, 3)
        self.assertIsNotNone(result)
        heading, content, preceding = result
        
        self.assertEqual("## Chapter 3: Arrival #john #mary #bob #hotel", heading)
        self.assertTrue(content.startswith("SETTING: Grand Hotel"))
        self.assertTrue(preceding.startswith("# Section 2: Development"))
        
        # Test chapter that doesn't exist
        result = outline_util.find_chapter_content(self.sample_outline, 10)
        self.assertIsNone(result)

    def test_get_character_profiles(self):
        """Test the get_character_profiles function with various inputs."""
        # Test normal case with multiple existing tags
        tags = {"john", "mary"}
        profiles = outline_util.get_character_profiles(self.sample_characters, tags)
        
        self.assertEqual(2, len(profiles))
        self.assertIn("john", profiles)
        self.assertIn("mary", profiles)
        self.assertTrue(profiles["john"].startswith("# John Smith #john"))
        self.assertTrue(profiles["mary"].startswith("# Mary Johnson #mary"))
        
        # Test with one existing and one missing tag
        tags = {"john", "nonexistent"}
        with self.assertLogs(level='WARNING') as log:
            profiles = outline_util.get_character_profiles(self.sample_characters, tags)
            
        self.assertEqual(1, len(profiles))
        self.assertIn("john", profiles)
        self.assertNotIn("nonexistent", profiles)
        self.assertTrue(any("nonexistent" in msg for msg in log.output))
        
        # Test with all missing tags
        tags = {"nonexistent1", "nonexistent2"}
        with self.assertLogs(level='WARNING') as log:
            profiles = outline_util.get_character_profiles(self.sample_characters, tags)
            
        self.assertEqual(0, len(profiles))
        self.assertTrue(any("nonexistent1" in msg for msg in log.output))
        
        # Test with empty tags
        tags = set()
        profiles = outline_util.get_character_profiles(self.sample_characters, tags)
        self.assertEqual(0, len(profiles))

    def test_get_setting_profiles(self):
        """Test the get_setting_profiles function with various inputs."""
        # Test normal case with multiple existing tags
        tags = {"home", "hotel"}
        profiles = outline_util.get_setting_profiles(self.sample_settings, tags)
        
        self.assertEqual(2, len(profiles))
        self.assertIn("home", profiles)
        self.assertIn("hotel", profiles)
        self.assertTrue(profiles["home"].startswith("# John's Home #home"))
        self.assertTrue(profiles["hotel"].startswith("# Grand Hotel #hotel"))
        
        # Test with one existing and one missing tag
        tags = {"hotel", "nonexistent"}
        with self.assertLogs(level='WARNING') as log:
            profiles = outline_util.get_setting_profiles(self.sample_settings, tags)
            
        self.assertEqual(1, len(profiles))
        self.assertIn("hotel", profiles)
        self.assertNotIn("nonexistent", profiles)
        self.assertTrue(any("nonexistent" in msg for msg in log.output))
        
        # Test with hyphenated tag
        tags = {"train-station"}
        profiles = outline_util.get_setting_profiles(self.sample_settings, tags)
        self.assertEqual(1, len(profiles))
        self.assertIn("train-station", profiles)
        self.assertTrue(profiles["train-station"].startswith("# Central Train Station #train-station"))
        
        # Test with empty tags
        tags = set()
        profiles = outline_util.get_setting_profiles(self.sample_settings, tags)
        self.assertEqual(0, len(profiles))

    def test_get_chapter_content(self):
        """Test the get_chapter_content function with various inputs."""
        # Test normal case
        with self.assertLogs(level='INFO') as log:
            result = outline_util.get_chapter_content(
                self.sample_outline, 1, self.sample_characters, self.sample_settings
            )
        
        self.assertIn('chapter_heading', result)
        self.assertIn('chapter_content', result)
        self.assertIn('preceding_content', result)
        self.assertIn('characters', result)
        self.assertIn('settings', result)
        self.assertIn('all_content', result)
        
        self.assertEqual("## Chapter 1: The Beginning #john #mary #home", result['chapter_heading'])
        self.assertTrue(result['chapter_content'].startswith("SETTING: John's home"))
        self.assertTrue("# John Smith #john" in result['characters'])
        self.assertTrue("# Mary Johnson #mary" in result['characters'])
        self.assertTrue("# John's Home #home" in result['settings'])
        
        # Test with missing tags
        with self.assertLogs(level='WARNING') as log:
            result = outline_util.get_chapter_content(
                self.sample_outline, 5, self.sample_characters, self.sample_settings
            )
        
        self.assertTrue("Unknown Pursuer" in result['chapter_content'])
        self.assertTrue(any("Pursuer" in msg for msg in log.output) or any("unknown" in msg.lower() for msg in log.output))
        
        # Test with non-existent chapter
        with self.assertRaises(ValueError), self.assertLogs(level='ERROR') as log:
            outline_util.get_chapter_content(
                self.sample_outline, 10, self.sample_characters, self.sample_settings
            )
        
        self.assertTrue(any("Chapter 10" in msg for msg in log.output))

    @patch('outline_util.find_chapter_content')
    def test_get_chapter_content_exception_handling(self, mock_find):
        """Test exception handling in get_chapter_content."""
        # Setup mock to raise an exception
        mock_find.side_effect = Exception("Test exception")
        
        # Test exception handling
        with self.assertRaises(Exception), self.assertLogs(level='ERROR') as log:
            outline_util.get_chapter_content(
                self.sample_outline, 1, self.sample_characters, self.sample_settings
            )
        
        self.assertTrue(any("Test exception" in msg for msg in log.output))

if __name__ == '__main__':
    unittest.main()
    