#!/usr/bin/env python
"""
Preview Demo Script

This script creates a simulated DocRepo with various documents and actions,
then generates a preview website to demonstrate all features of the HTML
preview generator.
"""

import os
import sys
import json
import logging
import datetime
import tempfile
import shutil
from typing import Dict, List, Any, Optional, Set

# Configure logging
logging.basicConfig(level=logging.INFO, 
                  format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Create mock objects for the demo
class MockDoc:
    """Mock implementation of the Doc class."""
    
    def __init__(self, name, properties=None, text="", versions=None):
        self.name = name
        self._properties = properties or {}
        self._text = text
        self._versions = versions or [1]
        self._version_properties = {}
        self._version_texts = {}
        
        # Initialize version 1
        self._version_properties[1] = self._properties.copy()
        self._version_texts[1] = self._text
        
        # Initialize other versions if specified
        for version in self._versions:
            if version != 1:
                self._version_properties[version] = self._properties.copy()
                self._version_properties[version]["version"] = version
                self._version_texts[version] = f"{self._text}\n\nThis is version {version} content."
    
    def get_property(self, key, default=None):
        return self._properties.get(key, default)
    
    def set_property(self, key, value):
        self._properties[key] = value
    
    def get_properties(self):
        return self._properties.copy()
    
    def get_text(self):
        return self._text
    
    def get_versions(self):
        return sorted(self._versions)
    
    def get_version_properties(self, version):
        if version in self._version_properties:
            return self._version_properties[version].copy()
        raise ValueError(f"Version {version} not found")
    
    def get_version_text(self, version):
        if version in self._version_texts:
            return self._version_texts[version]
        raise ValueError(f"Version {version} not found")
    
    def get_json_data(self):
        return {}
    
    def set_json_data(self, data):
        pass
    
    def get_all_tags(self):
        """Extract all tags from the text."""
        import re
        tags = re.findall(r'(?<!\n)#(\w+)', self._text)
        return sorted(set(tags))


class MockDocRepo:
    """Mock implementation of the DocRepo class."""
    
    def __init__(self):
        self.docs = {}
    
    def get_doc(self, name):
        return self.docs.get(name)
    
    def list_docs(self):
        return sorted(self.docs.keys())
    
    def add_doc(self, doc):
        """Add a document to the repository."""
        self.docs[doc.name] = doc
    
    def list_all_tags(self):
        """List all tags across all documents."""
        all_tags = set()
        for doc in self.docs.values():
            all_tags.update(doc.get_all_tags())
        return sorted(all_tags)


def create_mock_action(command, args=None, status="success", input_docs=None, output_docs=None):
    """Create a mock action record."""
    args = args or []
    input_docs = input_docs or []
    output_docs = output_docs or []
    
    now = datetime.datetime.now()
    start_time = (now - datetime.timedelta(minutes=30)).isoformat()
    end_time = now.isoformat() if status != "running" else None
    
    return {
        "command": command,
        "args": args,
        "status": status,
        "pid": 12345,
        "start_time": start_time,
        "end_time": end_time,
        "input_docs": input_docs,
        "output_docs": output_docs,
        "token_usage": {
            "input_tokens": 1000,
            "output_tokens": 2000
        }
    }


def create_mock_state_file(file_path, command="write-chapter", args=None):
    """Create a mock state.json file for a running action."""
    args = args or ["chapter3", "write_chapter_prompt", "3"]
    
    state = {
        "pid": os.getpid(),  # Use current process ID
        "command": command,
        "args": args,
        "start_time": datetime.datetime.now().isoformat(),
        "status": "running",
        "current_step": "Generating content...",
        "log_file": "actions/20250322_123456_write-chapter.json"
    }
    
    with open(file_path, 'w') as f:
        json.dump(state, f, indent=2)


def create_mock_actions_dir(actions_dir):
    """Create mock action log files in the actions directory."""
    os.makedirs(actions_dir, exist_ok=True)
    
    # Create some action logs
    actions = [
        create_mock_action(
            "write-chapter", 
            ["chapter1", "write_chapter_prompt", "1"],
            "success",
            ["outline", "settings", "characters"],
            ["chapter1"]
        ),
        create_mock_action(
            "write-chapter", 
            ["chapter2", "write_chapter_prompt", "2"],
            "success",
            ["outline", "settings", "characters", "chapter1"],
            ["chapter2"]
        ),
        create_mock_action(
            "edit-chapter", 
            ["chapter1", "edit_notes"],
            "failure",
            ["chapter1"],
            ["edit_notes"]
        ),
        create_mock_action(
            "review-chapter", 
            ["chapter2", "review_notes"],
            "success",
            ["chapter2"],
            ["review_notes"]
        ),
        create_mock_action(
            "write-outline", 
            ["outline"],
            "success",
            ["setting", "characters"],
            ["outline"]
        )
    ]
    
    # Write action logs with timestamps in filenames
    for i, action in enumerate(actions):
        # Create timestamps going backwards from now
        timestamp = datetime.datetime.now() - datetime.timedelta(hours=i)
        filename = timestamp.strftime("%Y-%m-%d_%H-%M-%S") + f"_{action['command']}.json"
        filepath = os.path.join(actions_dir, filename)
        
        with open(filepath, 'w') as f:
            json.dump(action, f, indent=2)
    
    logger.info(f"Created {len(actions)} mock action logs in {actions_dir}")


def create_demo_docs():
    """Create a set of demo documents for the repository."""
    # Create outline document
    outline = MockDoc(
        name="outline",
        properties={
            "type": "outline",
            "version": 2,
            "creation_time": "2025-03-01T10:00:00",
            "word_count": 500,
            "input_tokens": 800,
            "output_tokens": 2000
        },
        text="""# Story Outline

## Chapter 1: The Beginning
- Introduce the main character, Alex #protagonist
- Set up the world and its rules #worldbuilding
- End with the inciting incident #plot

## Chapter 2: The Journey Begins
- Alex leaves home #journey
- Meets the mentor character, Dr. Chen #character
- Discovers the first clue #plot

## Chapter 3: Complications
- Alex faces the first major obstacle #challenge
- The antagonist is revealed #antagonist
- References to chapter1 and their experiences there

This outline refers to characters and setting.
""",
        versions=[1, 2]
    )
    
    # Create settings document
    setting = MockDoc(
        name="setting",
        properties={
            "type": "setting",
            "version": 3,
            "creation_time": "2025-03-01T09:00:00",
            "word_count": 800,
            "input_tokens": 1200,
            "output_tokens": 3000
        },
        text="""# World Setting

## Geography
The story takes place in Neo-Seattle, a futuristic version of the city built after the Great Quake of 2098 #worldbuilding #future

## Technology
- Neural implants allow direct brain interfaces #technology
- Automated drone delivery systems #technology
- Climate control domes protect from the harsh weather #environment

## Social Structure
- The society is divided into three tiers #society
- Upper tier: Corporate executives and government officials
- Middle tier: Knowledge workers and specialists
- Lower tier: Service workers and manual laborers

This setting document will be referenced by chapter1 and chapter2.
""",
        versions=[1, 2, 3]
    )
    
    # Create characters document
    characters = MockDoc(
        name="characters",
        properties={
            "type": "characters",
            "version": 2,
            "creation_time": "2025-03-01T09:30:00",
            "word_count": 700,
            "input_tokens": 1000,
            "output_tokens": 2500
        },
        text="""# Characters

## Alex Chen #protagonist
- 28 years old, neural interface designer
- Curious and determined, but sometimes impulsive
- Special skill: Can intuitively understand complex systems

## Dr. Maya Rivera #mentor
- 52 years old, former corporate researcher
- Wise but secretive about her past
- Guides Alex but has her own agenda

## Director Elias Stone #antagonist
- 45 years old, head of corporate security
- Cold, calculating, and ruthlessly efficient
- Believes the ends justify the means

## Supporting Characters
- Theo, Alex's roommate and best friend #supporting
- Captain Lin, security officer with divided loyalties #supporting
- The Architect, mysterious figure pulling strings #mystery

These characters will appear in chapter1 and chapter2.
""",
        versions=[1, 2]
    )
    
    # Create chapter documents
    chapter1 = MockDoc(
        name="chapter1",
        properties={
            "type": "chapter",
            "version": 3,
            "order": 1,
            "creation_time": "2025-03-10T14:00:00",
            "word_count": 2500,
            "input_tokens": 3000,
            "output_tokens": 8000,
            "references": "outline#2, setting#3, characters#2",
            "prompt_doc": "write_chapter_prompt"
        },
        text="""# Chapter 1: The Beginning

Alex Chen stared at the pulsing neural interface on the workbench, its soft blue glow illuminating the dimly lit lab #technology #protagonist

"It's not working," Alex muttered, running a hand through disheveled hair. Three days without sleep, and the prototype still rejected every connection attempt. The quarterly review was tomorrow, and without results, the project would be terminated.

The sprawling skyline of Neo-Seattle #worldbuilding glittered beyond the lab windows, environmental domes capturing the last rays of sunset. From this high up in the Nexus Tower, Alex could almost forget about the struggles of the lower tiers below.

A notification pinged on Alex's retinal display: "URGENT: MEETING REQUESTED - DR. RIVERA, SUBLEVEL 42"

That was odd. Maya Rivera #mentor had left the company years ago after the incident nobody talked about. What was she doing back at Nexus?

Twenty minutes later, Alex stepped out of the elevator into Sublevel 42, a restricted area that required security clearances Alex shouldn't have had. Yet the doors had opened anyway.

"I was hoping you'd come," said a voice from the shadows. Dr. Rivera stepped forward, looking exactly as she had three years ago when she'd disappeared from public view.

"How did you get me access?" Alex asked.

"I didn't," Maya replied with a thin smile. "The system recognized you because it was meant to. Some paths are laid out long before we walk them, Alex."

She gestured to a sealed container on a nearby table. "What do you see?"

"A neural interface module. Different from our current models."

"It's not different," Maya said. "It's what yours will become. I need your help, but first, you need to understand what's really happening at Nexus."

As Maya explained the truth about the neural interface project and its real purpose, Alex realized that everything was about to change. The comfortable life in the upper tier, the prestigious job at Nexus - all of it built on carefully constructed lies.

At that moment, a security alert blared throughout the sublevel.

"He's found us sooner than I expected," Maya said, quickly gathering her materials. "Director Stone #antagonist is very good at his job."

"What do we do?" Alex asked, heart pounding.

Maya handed over a small device. "This contains everything you need to know. Find Theo, he's been expecting you. And Alex," her eyes were intense, "trust no one else."

As security drones filled the corridor outside, Maya showed Alex to a maintenance shaft. "This will take you to the lower levels. Go now."

"What about you?"

"I'll buy you time," she said with a smile that didn't reach her eyes. "This was always how it had to be."

As Alex crawled through the dusty shaft, the sounds of security forces breaching the lab echoed behind. The neural interface prototype was still clutched tightly in one hand, its blue glow now seeming less like innovation and more like a beacon leading into darkness.

The real journey was just beginning.
""",
        versions=[1, 2, 3]
    )
    
    chapter2 = MockDoc(
        name="chapter2",
        properties={
            "type": "chapter",
            "version": 2,
            "order": 2,
            "creation_time": "2025-03-15T16:00:00",
            "word_count": 2700,
            "input_tokens": 3500,
            "output_tokens": 9000,
            "references": "outline#2, setting#3, characters#2, chapter1#3",
            "prompt_doc": "write_chapter_prompt"
        },
        text="""# Chapter 2: The Journey Begins

The lower tiers of Neo-Seattle were nothing like the corporate promotional videos #worldbuilding. Alex stepped out of the maintenance tunnel into a world of shadows and noise, where the protective domes above were just distant shimmer through layers of makeshift infrastructure.

Three hours had passed since the escape from Nexus Tower. Alex had ditched the corporate uniform in favor of nondescript clothing purchased from a street vendor who didn't ask questions. The neural interface prototype was wrapped in cloth and tucked securely in a worn backpack.

"First time down in the depths?" a voice asked.

Alex turned to see a woman leaning against a wall, her eyes shielded by outdated retinal displays.

"Is it that obvious?" Alex replied.

"Upper tier written all over you," she said with a shrug. "Word of advice: don't make eye contact, don't show tech, and get where you're going quickly."

"I'm looking for someone named Theo #supporting."

The woman's posture changed subtly. "Lots of Theos down here."

"This one would know Dr. Maya Rivera #mentor."

"Follow me," she said after a pause. "And keep that backpack close."

They navigated through crowded markets and narrow alleys where unlicensed tech dealers hawked their wares. Occasionally, security drones would pass overhead, their scanning beams sweeping the streets. Each time, Alex's guide would duck into a doorway or under an awning until they passed.

"Those aren't regular security patterns," she noted. "They're looking for someone specific today."

Alex thought of the security alert at Nexus Tower and walked a little faster.

Eventually, they arrived at a recycling facility. The air was thick with the smell of melted plastics and ozone. Workers in protective gear barely glanced up as they passed.

At the back of the facility, behind stacks of discarded tech components, was a small office. The woman knocked twice, paused, then three times more.

The door opened to reveal a tall man with dark hair streaked with silver. "I told you not to come back here, Lin."

"Special circumstances," the woman – apparently Captain Lin #supporting – replied. "This one's looking for you, mentioned Rivera."

Theo's eyes widened as he looked at Alex. "You actually came. Maya said you might, but I didn't..." He trailed off, then stepped aside. "Get in, quickly."

As Alex entered, Lin remained at the door. "We're even now," she said to Theo.

"More than even," he agreed. "Watch yourself, Lin. Stone has his people everywhere #antagonist."

"Tell me something I don't know," she replied before disappearing back into the labyrinth of the recycling facility.

Inside the small office, Theo quickly secured multiple locks on the door. The space was cramped but organized, with screens showing security feeds from around the facility.

"You brought it?" Theo asked, nodding to the backpack.

Alex removed the wrapped prototype. "Maya said you were expecting me."

"For three years," Theo confirmed, carefully taking the device. "Ever since she discovered what they were really building." He activated a hidden panel in the wall, revealing a concealed room filled with technical equipment.

"What is all this?" Alex asked.

"The real resistance," Theo explained. "Maya was just the most visible part." He connected the prototype to his equipment. "This is the key we've been waiting for, the proof we needed."

"Proof of what?"

Theo looked up, his expression grave. "That the neural interfaces aren't just for communication and entertainment. They're for control. Nexus isn't just collecting data – they're conducting a massive, unauthorized experiment in mass neural modification."

On the screens, complex data patterns emerged from the prototype's programming.

"These patterns," Alex said, recognizing the code. "They're similar to what we were working on, but more advanced."

"And more insidious," Theo added. "This is phase three of their project. Phase one was distribution – getting the interfaces into as many people as possible. Phase two was data collection. Phase three..."

"Is manipulation," Alex finished, horrified at the implications. "But why?"

"That's what we need to find out," Theo said. "And we'll need to get into their central data core to do it."

"That's impossible. It's beneath the Nexus Tower, the most secure location in Neo-Seattle."

Theo smiled grimly. "Not entirely impossible. Not with what Maya gave you."

Alex felt something in the pocket of the borrowed jacket – a small data drive that hadn't been there before.

"The access codes?" Alex asked.

"And the location of someone who can help us use them," Theo confirmed. "The Architect #mystery."

Outside, a security drone passed closer than the others, its scanners lingering on the recycling facility. An alert chimed softly on one of Theo's monitors.

"We need to move," he said urgently, gathering essential equipment. "They've tracked the neural pattern of the prototype."

"Where are we going?"

"To the only place in Neo-Seattle where we can hide from their scanners," Theo said, opening a concealed floor panel. "The old city. The real Seattle, buried beneath the new."

As they descended into the darkness below, Alex thought of Maya and wondered if she was still alive. The comfortable life at Nexus Tower now seemed like a distant dream, replaced by the harsh reality of a fight against an enemy whose true reach was only beginning to become clear.

The journey that had begun in chapter1 was now taking a darker, more dangerous turn.
""",
        versions=[1, 2]
    )
    
    # Create edit notes document
    edit_notes = MockDoc(
        name="edit_notes",
        properties={
            "type": "edit",
            "version": 1,
            "creation_time": "2025-03-18T10:00:00",
            "word_count": 400,
            "input_tokens": 600,
            "output_tokens": 1200,
            "references": "chapter1#3",
            "prompt_doc": "edit_chapter_prompt"
        },
        text="""# Edit Notes for Chapter 1

## Strengths
- Strong introduction of the protagonist Alex #protagonist
- Good establishment of the Neo-Seattle setting #worldbuilding
- Effective mystery setup with Dr. Rivera #mentor

## Areas for Improvement
- Need more sensory details in the lab scene
- The transition to Sublevel 42 feels rushed
- Director Stone #antagonist is mentioned but needs more presence or impact
- The technology descriptions could be more specific

## Specific Suggestions
1. Add a paragraph describing the sights, sounds, and smells of the lab
2. Expand the elevator journey to Sublevel 42 to build tension
3. Include a brief flashback or memory about Director Stone to establish his threat
4. Clarify exactly what the neural interface does and how it works

Overall, the chapter is on the right track but needs more depth in character relationships and setting details. The references to the outline and setting documents are well-incorporated.
""",
        versions=[1]
    )
    
    # Create review notes document
    review_notes = MockDoc(
        name="review_notes",
        properties={
            "type": "review",
            "version": 1,
            "creation_time": "2025-03-20T11:00:00",
            "word_count": 450,
            "input_tokens": 700,
            "output_tokens": 1400,
            "references": "chapter2#2",
            "prompt_doc": "review_chapter_prompt"
        },
        text="""# Review Notes for Chapter 2

## Summary
Chapter 2 follows Alex's journey into the lower tiers of Neo-Seattle after escaping from Nexus Tower. Alex meets Captain Lin, who leads the way to Theo. Theo reveals the truth about the neural interfaces and the conspiracy behind them. The chapter ends with Alex and Theo preparing to journey to the buried old city.

## Strengths
- Excellent contrast between upper and lower tiers of Neo-Seattle #worldbuilding
- Good development of new characters (Lin, Theo) #character
- Strong continuation from chapter1 events
- Effective buildup of the central conspiracy plot #plot

## Weaknesses
- The relationship between Lin and Theo could use more clarification
- The explanation of the neural interface conspiracy is somewhat technical and may lose some readers
- Alex's emotional reaction to the revelations could be deeper

## Recommendations
- Add more background on the Lin-Theo connection
- Simplify the technical explanation while keeping the stakes high
- Include more of Alex's internal thoughts about betrayal and the new reality

Overall rating: 8/10 - A strong continuation that successfully expands the world and deepens the plot.
""",
        versions=[1]
    )
    
    # Create prompt documents
    write_chapter_prompt = MockDoc(
        name="write_chapter_prompt",
        properties={
            "type": "prompt",
            "bot_type": "WRITE_CHAPTER",
            "version": 1,
            "creation_time": "2025-02-15T08:00:00"
        },
        text="""# Bot Configuration

bot_type: WRITE_CHAPTER
llm: writer
input_price: 0.5
output_price: 1.5
temperature: 0.7
expected_length: 2500
context_window: 8192
max_continuations: 5

# System Prompt

You are an expert fiction writer specializing in creating engaging, immersive chapters for science fiction novels. You excel at character development, world-building, and plot advancement.

# Main Prompt

Write Chapter {chapter_number} based on the following information:

OUTLINE: {outline}

SETTING: {setting}

CHARACTERS: {characters}

PREVIOUS CHAPTER (if applicable): {previous_chapter}

Create a compelling chapter that advances the story while maintaining consistency with the established setting and characters. Include engaging dialogue, descriptive prose, and meaningful character development. End the chapter with a hook that leads into the next part of the story.

# Continuation Prompt

Continue writing Chapter {chapter_number} based on what you've written so far. You've written {current_words} words out of approximately {expected_words}.

Keep consistent characterization and maintain the established tone and style. Make sure to reference earlier elements from the chapter for continuity.
""",
        versions=[1]
    )
    
    edit_chapter_prompt = MockDoc(
        name="edit_chapter_prompt",
        properties={
            "type": "prompt",
            "bot_type": "EDIT_CHAPTER",
            "version": 1,
            "creation_time": "2025-02-15T09:00:00"
        },
        text="""# Bot Configuration

bot_type: EDIT_CHAPTER
llm: editor
input_price: 0.3
output_price: 0.9
temperature: 0.4
expected_length: 500
context_window: 16384
max_continuations: 2

# System Prompt

You are an expert fiction editor with a keen eye for narrative structure, character development, pacing, and prose quality. Your feedback is specific, actionable, and supportive.

# Main Prompt

Review the following chapter and provide detailed editorial feedback:

CHAPTER CONTENT: {content}

OUTLINE: {outline}

SETTING: {setting}

CHARACTERS: {characters}

Provide comprehensive edit notes including:
1. Strengths of the chapter
2. Areas for improvement
3. Specific suggestions for revisions
4. Notes on consistency with the outlined plot, setting, and characters

Your feedback should be constructive and specific, pointing to exact sections or elements that could be improved while also acknowledging what works well.

# Continuation Prompt

Continue your editorial assessment based on what you've written so far. You've written {current_words} words out of approximately {expected_words}.

Focus on providing additional specific examples and suggestions that weren't covered in your initial notes.
""",
        versions=[1]
    )
    
    review_chapter_prompt = MockDoc(
        name="review_chapter_prompt",
        properties={
            "type": "prompt",
            "bot_type": "REVIEW_CHAPTER",
            "version": 1,
            "creation_time": "2025-02-15T10:00:00"
        },
        text="""# Bot Configuration

bot_type: REVIEW_CHAPTER
llm: critic
input_price: 0.2
output_price: 0.6
temperature: 0.5
expected_length: 500
context_window: 16384
max_continuations: 1

# System Prompt

You are a literary critic and reviewer who analyzes fiction with a focus on narrative cohesion, character development, thematic elements, and reader engagement. Your reviews are balanced, insightful, and fair.

# Main Prompt

Review the following chapter:

CONTENT: {content}

OUTLINE: {outline}

SETTING: {setting}

CHARACTERS: {characters}

Provide a comprehensive review including:
1. Brief summary of the chapter
2. Analysis of strengths
3. Analysis of weaknesses
4. Specific recommendations
5. Overall assessment/rating

Your review should evaluate how effectively the chapter advances the story, develops characters, and engages the reader. Consider both technical elements (prose, dialogue, description) and storytelling aspects (plot progression, character arcs, themes).

# Continuation Prompt

Continue your review based on what you've written so far. You've written {current_words} words out of approximately {expected_words}.

Focus on any important aspects you haven't covered yet and develop your overall assessment.
""",
        versions=[1]
    )
    
    # Return all created documents
    return [
        outline, setting, characters, 
        chapter1, chapter2, 
        edit_notes, review_notes,
        write_chapter_prompt, edit_chapter_prompt, review_chapter_prompt
    ]


def main():
    """Main function to create the demo and generate preview."""
    # Create a temporary directory for the demo
    demo_dir = tempfile.mkdtemp()
    preview_dir = os.path.join(demo_dir, "preview")
    actions_dir = os.path.join(demo_dir, "actions")
    
    try:
        # Create DocRepo with demo documents
        repo = MockDocRepo()
        for doc in create_demo_docs():
            repo.add_doc(doc)
        
        logger.info(f"Created mock DocRepo with {len(repo.list_docs())} documents")
        
        # Create mock actions directory
        create_mock_actions_dir(actions_dir)
        
        # Create mock state file for a currently running action
        state_file = os.path.join(demo_dir, "state.json")
        create_mock_state_file(state_file)
        
        # Import the preview generator
        from preview import generate_preview
        
        # Monkey patch for the demo
        import preview
        preview.STATE_FILE = state_file
        preview.get_recent_actions = lambda count=10, actions_dir=actions_dir: [
            json.load(open(os.path.join(actions_dir, f))) 
            for f in sorted(os.listdir(actions_dir), reverse=True)[:count]
            if f.endswith('.json')
        ]
        
        # Generate the preview
        logger.info("Generating HTML preview...")
        preview_path = generate_preview(repo, preview_dir)
        
        # Print success message
        print(f"\nPreview generated successfully in: {preview_path}")
        print(f"Open {os.path.join(preview_path, 'index.html')} in a web browser to view")
        
        # Keep the files if requested
        if len(sys.argv) > 1 and sys.argv[1] == "--keep":
            print(f"Files will be kept in {demo_dir}")
            # Set this to prevent cleanup
            demo_dir = None
        else:
            print("Run with --keep flag to keep the generated files")
            print(f"Temporary files will be deleted when this script exits")
    
    finally:
        # Clean up temporary directory if it exists
        if demo_dir and os.path.exists(demo_dir):
            shutil.rmtree(demo_dir)


if __name__ == "__main__":
    main()
