# Documentation for BookBot



## Table of Contents
- [Document System](#document-system)
  - [Doc Class](#doc-class)
  - [DocRepo Class](#docrepo-class)
- [Bot System](#bot-system)
  - [BotType Enum](#bottype-enum)
  - [PromptDoc Class](#promptdoc-class)
  - [DocWriter Class](#docwriter-class)
  - [MockDocWriter Class](#mockdocwriter-class)
  - [BookWriter Class](#bookwriter-class)
  - [Utility Functions](#utility-functions)
- [Global Configuration](#global-configuration)
- [Error Handling](#error-handling)
- [Complete Example Workflow](#complete-example-workflow)
- [Command System](#command-system)
   - [Command Base Class](#command-base-class)
   - [CommandRegistry](#commandregistry)
   - [Creating New Commands](#creating-new-commands)
- [Action System](#action-system)
   - [Action Class](#action-class)
   - [Action Status](#action-status)
   - [Action Management Functions](#action-management-functions)
- [Outline Utilities](#outline-utilities)
   - [Chapter Management](#chapter-management)
   - [Tag Extraction](#tag-extraction)
   - [Content Retrieval](#content-retrieval)



## Document System

The Document system provides version-controlled document storage with properties and JSON data.

### Doc Class

The `Doc` class represents a single document with versioning capabilities, properties, and JSON data.

#### Constructor

```python
Doc(name: str, repo_path: str, logger: Optional[logging.Logger] = None)
```

- `name`: Document name without extension (e.g., 'chapter1')
- `repo_path`: Path to the repository directory
- `logger`: Optional logger instance

#### Methods

##### Text Operations

```python
get_text() -> str
```
- Returns the document text content.

```python
update_text(new_text: str) -> None
```
- Updates the text content, creating a new version.

```python
append_text(text_to_append: str) -> None
```
- Appends text to the document.

##### Property Operations

```python
get_property(key: str, default: Any = None) -> Any
```
- Gets a specific property value.

```python
set_property(key: str, value: Any) -> None
```
- Sets a property value.

```python
has_property(key: str) -> bool
```
- Checks if a specific property exists.

```python
get_properties() -> Dict[str, Any]
```
- Gets all properties as a dictionary.

##### JSON Operations

```python
get_json_data() -> Dict[str, Any]
```
- Gets the document's JSON data.

```python
set_json_data(data: Dict[str, Any]) -> None
```
- Sets the document's JSON data.

##### Version Operations

```python
get_versions() -> List[int]
```
- Gets list of all available versions.

```python
get_version_text(version: int) -> str
```
- Gets text content of a specific version.

```python
get_version_properties(version: int) -> Dict[str, Any]
```
- Gets properties of a specific version.

```python
revert_to_version(version: int) -> None
```
- Reverts to a previous version, creating a new version with the same content.

```python
complete() -> None
```
- Marks a document as complete, which prevents further rollbacks.

```python
rollback() -> bool
```
- Rolls back the most recent changes if the document is not complete.

##### Content Operations

```python
get_sections_with_tags(tags: List[str]) -> List[str]
```
- Gets sections containing all specified tags.

```python
add_tag_to_section(section_header: str, tag: str) -> bool
```
- Adds a tag to a specific section.

```python
get_all_tags() -> List[str]
```
- Gets all unique tags used in the document.

#### Example Usage

```python
# Create or access a document
doc = Doc("chapter1", "/path/to/repo")

# Update document content
doc.update_text("# Chapter 1\n\nOnce upon a time...")

# Add properties
doc.set_property("status", "draft")
doc.set_property("word_count", len(doc.get_text().split()))

# Store JSON data
doc.set_json_data({
    "metadata": {
        "author": "Jane Doe",
        "created_at": "2025-03-15"
    }
})

# Access versions
versions = doc.get_versions()
old_text = doc.get_version_text(1)
```

#### Nuance of this API:
update_text completely replaces the document text and increments the version number. 
set_property KEEPS ALL EXISTING PROPERTIES and does not update the version number, so it is 
not consistent. 
If you intend version 2 to have a property that version 1 does not, you have to set it AFTER 
updating the text. Or you could update the text with the empty string, set the property, then 
update it with the real text. 


### DocRepo Class

The `DocRepo` class manages a collection of `Doc` objects in a repository.

#### Constructor

```python
DocRepo(repo_path: str, logger: Optional[logging.Logger] = None)
```

- `repo_path`: Path to the repository directory
- `logger`: Optional logger instance

#### Methods

##### Document Operations

```python
create_doc(name: str, initial_properties: Optional[Dict[str, Any]] = None, initial_text: str = "") -> Doc
```
- Creates a new document and returns the Doc object.

```python
get_doc(name: str) -> Optional[Doc]
```
- Gets a document by name and returns the Doc object.

```python
delete_doc(name: str) -> bool
```
- Deletes a document and all its versions.

```python
list_docs() -> List[str]
```
- Lists all document names in the repo.

##### Repository-wide Operations

```python
get_docs_by_type(doc_type: str) -> List[Doc]
```
- Gets all documents with a specific type property.

```python
get_sections_with_tags(tags: List[str]) -> Dict[str, List[str]]
```
- Gets all sections from all documents that contain all specified tags.

```python
list_all_tags() -> List[str]
```
- Lists all unique tags used across all documents.

```python
list_property_values(property_name: str) -> List[Any]
```
- Lists all unique values for a given property across all documents.

#### Example Usage

```python
# Initialize repository
repo = DocRepo("/path/to/repo")

# Create a new document
doc = repo.create_doc("chapter1", {"type": "chapter", "status": "draft"}, "# Chapter 1\n\nOnce upon a time...")

# Get an existing document
doc = repo.get_doc("chapter1")

# List all documents
all_docs = repo.list_docs()

# Get all documents of a specific type
chapters = repo.get_docs_by_type("chapter")

# Find sections with specific tags
sections = repo.get_sections_with_tags(["character", "protagonist"])
```

## Bot System

The Bot system uses the Document system to create and manage prompts for LLM content generation.

### BotType Enum

The `BotType` enum defines different types of bots and their required template variables.

#### Values

- `DEFAULT`: No specific variables required
- `WRITE_OUTLINE`: Requires initial, setting, characters
- `WRITE_SETTING`: Requires initial
- `WRITE_CHARACTERS`: Requires initial, setting
- `WRITE_CHAPTER`: Requires chapter_number, outline, setting, characters, previous_chapter
- `WRITE_SECTION`: Requires section_number, chapter_number, section_outline, setting, characters, previous_section
- `SPLIT_OUTLINE`: Requires outline
- `SPLIT_CHAPTER`: Requires chapter_outline
- `REVIEW_COMMONS`: Requires initial, setting, characters, content
- `REVIEW_CHAPTER`: Requires content, outline, setting, characters
- `EDIT_CHAPTER`: Requires outline, setting, characters, review, content
- `REVIEW_WHOLE`: Requires content
- `SELF_EDIT`: Requires initial, characters, setting, content

#### Properties

```python
required_vars -> Set[str]
```
- Returns the set of required template variables for this bot type.

#### Example Usage

```python
# Get required variables for a bot type
required_vars = BotType.WRITE_CHAPTER.required_vars
print(required_vars)  # {'chapter_number', 'outline', 'setting', 'characters', 'previous_chapter'}
```

### PromptDoc Class

The `PromptDoc` class adapts a `Doc` object to serve as a prompt template.

#### Constructor

```python
PromptDoc(doc: Doc)
```

- `doc`: A Doc object that contains prompt configuration and templates

#### Properties

- `doc`: The underlying Doc object
- `bot_type`: BotType enum value derived from the document content
- `llm`: Resolved LLM model name (after alias resolution)
- `_raw_llm`: Original LLM name or alias
- `input_price`: Price per million input tokens
- `output_price`: Price per million output tokens
- `provider`: Optional provider preference
- `temperature`: Temperature setting for generation
- `expected_length`: Expected output length in words
- `context_window`: Context window size in tokens
- `max_continuations`: Maximum number of continuation calls
- `system_prompt`: System prompt extracted from the document
- `main_prompt`: Main prompt template extracted from the document
- `continuation_prompt`: Continuation prompt template extracted from the document

#### Methods

```python
validate_template_vars(variables: Dict[str, Union[str, Doc]]) -> None
```
- Validates that all required template variables are provided.

```python
get_provider_config() -> Dict
```
- Gets provider configuration for OpenRouter API.

```python
to_dict() -> Dict[str, Any]
```
- Converts the prompt configuration to a dictionary for UI rendering.

#### Expected Document Format

The PromptDoc expects a Doc with the following format:

```markdown
# Bot Configuration

bot_type: WRITE_CHAPTER
llm: writer
input_price: 0.5
output_price: 1.5
temperature: 0.7
expected_length: 2000
context_window: 8192
max_continuations: 5

# System Prompt

You are an expert fiction writer...

# Main Prompt

Write Chapter {chapter_number} based on...

# Continuation Prompt

Continue writing Chapter {chapter_number}...
```

#### Example Usage

```python
# Get a prompt document
doc = doc_repo.get_doc("write_chapter")

# Create a PromptDoc
prompt_doc = PromptDoc(doc)

# Validate template variables
template_vars = {
    "chapter_number": "1",
    "outline": outline_doc,  # Doc object
    "setting": setting_doc,  # Doc object
    "characters": "Character descriptions",
    "previous_chapter": ""
}
prompt_doc.validate_template_vars(template_vars)

# Access prompt properties
print(f"Bot type: {prompt_doc.bot_type.name}")
print(f"LLM: {prompt_doc.llm}")
print(f"Expected length: {prompt_doc.expected_length} words")
```

### DocWriter Class

The `DocWriter` class handles interaction with the LLM API and updates a document with generated content.

#### Constructor

```python
DocWriter(prompt_doc: PromptDoc, output_doc: Doc, api_key: str, template_vars: Dict[str, Union[str, Doc]], command: str = "generate")
```

- `prompt_doc`: PromptDoc containing configuration and templates
- `output_doc`: Doc to write output to
- `api_key`: OpenRouter API key
- `template_vars`: Dictionary of template variables (strings or Doc objects)
- `command`: Command name for logging

#### Methods

```python
generate() -> str
```
- Generates content using the prompt doc and updates the output doc.
- Returns the generated content.

#### Example Usage

```python
# Create DocWriter
writer = DocWriter(
    prompt_doc=prompt_doc,
    output_doc=output_doc,
    api_key="your_api_key",
    template_vars={
        "chapter_number": "1",
        "outline": outline_doc,
        "setting": setting_doc,
        "characters": characters_doc,
        "previous_chapter": ""
    },
    command="write_chapter1"
)

# Generate content
content = writer.generate()
```

### MockDocWriter Class

The `MockDocWriter` class provides a mock implementation of `DocWriter` for testing without making real API calls.

#### Constructor

```python
MockDocWriter(prompt_doc: PromptDoc, output_doc: Doc, api_key: str, template_vars: Dict[str, Union[str, Doc]], command: str = "generate")
```

- Same parameters as DocWriter

#### Methods

```python
generate() -> str
```
- Generates mock content without making API calls.
- Returns the mock content.

#### Example Usage

```python
# Create MockDocWriter
mock_writer = MockDocWriter(
    prompt_doc=prompt_doc,
    output_doc=output_doc,
    api_key="your_api_key",
    template_vars={
        "chapter_number": "1",
        "outline": outline_doc,
        "setting": setting_doc,
        "characters": characters_doc,
        "previous_chapter": ""
    },
    command="write_chapter1"
)

# Generate mock content
content = mock_writer.generate()
```

### BookWriter Class

The `BookWriter` class provides a high-level interface for managing prompt documents and generating content.

#### Constructor

```python
BookWriter(doc_repo: DocRepo, api_key: Optional[str] = None, logger: Optional[logging.Logger] = None)
```

- `doc_repo`: Document repository (DocRepo instance)
- `api_key`: OpenRouter API key (if None, will look for OPENROUTER_API_KEY env var)
- `logger`: Optional logger instance

#### Methods

##### Prompt Management

```python
get_prompt_doc(name: str) -> Optional[PromptDoc]
```
- Gets a prompt document by name.

```python
create_prompt(name: str, bot_type: Union[str, BotType]) -> PromptDoc
```
- Creates a new prompt document with the specified bot type.

```python
list_prompts() -> List[str]
```
- Lists all prompt documents in the repository.

```python
get_prompt_info(prompt_name: str) -> Dict[str, Any]
```
- Gets information about a specific prompt document.

```python
validate_prompt(prompt_name: str) -> Tuple[bool, Optional[str]]
```
- Validates a prompt document.

```python
validate_all_prompts() -> Dict[str, Tuple[bool, Optional[str]]]
```
- Validates all prompt documents in the repository.

##### Content Generation

```python
write_content(output_doc_name: str, prompt_doc_name: str, template_vars: Dict[str, Union[str, Doc]], command: str = "", use_mock: bool = False) -> str
```
- Generates content using a prompt document and saves to an output document.

#### Example Usage

```python
# Initialize BookWriter
writer = BookWriter(doc_repo, api_key="your_api_key")

# Create a prompt
prompt_doc = writer.create_prompt("write_chapter", BotType.WRITE_CHAPTER)

# List available prompts
prompts = writer.list_prompts()

# Generate content
content = writer.write_content(
    output_doc_name="chapter1",
    prompt_doc_name="write_chapter",
    template_vars={
        "chapter_number": "1",
        "outline": outline_doc,  # Doc object
        "setting": setting_doc,  # Doc object
        "characters": characters_doc,  # Doc object
        "previous_chapter": ""
    },
    command="write_chapter1"
)

# Validate prompts
results = writer.validate_all_prompts()
for name, (is_valid, error) in results.items():
    print(f"{name}: {'✓' if is_valid else '✗'} {error or ''}")
```

### Utility Functions

#### Template Variables

```python
extract_template_vars(text: str) -> Set[str]
```
- Extracts all template variables from a text string.
- Variables are in the format `{variable_name}`.

#### Price Formatting

```python
format_price(input_tokens: int, output_tokens: int, input_price: float, output_price: float) -> str
```
- Formats price based on token usage.

#### Prompt Template Creation

```python
create_prompt_doc_template(doc_repo: DocRepo, name: str, bot_type: BotType) -> Doc
```
- Creates a template prompt document with the specified bot type.

#### Convenience Function

```python
generate_content(output_doc_name: str, prompt_doc_name: str, template_vars: Dict[str, Union[str, Doc]], doc_repo: DocRepo, api_key: Optional[str] = None, command: str = "", use_mock: bool = False) -> str
```
- Generates content using a prompt document and saves to an output document.
- Convenience function that wraps BookWriter.write_content.

#### Example Usage

```python
# Extract template variables
variables = extract_template_vars("Hello {name}, welcome to {service}!")
# Returns {'name', 'service'}

# Format price
price = format_price(1000, 2000, 5.0, 15.0)
# Returns "$0.035000 ($0.005000 + $0.030000)"

# Use convenience function
content = generate_content(
    output_doc_name="chapter1",
    prompt_doc_name="write_chapter",
    template_vars={
        "chapter_number": "1",
        "outline": outline_doc,
        "setting": setting_doc,
        "characters": characters_doc,
        "previous_chapter": ""
    },
    doc_repo=doc_repo,
    api_key="your_api_key"
)
```

## Global Configuration

The following environment variables are available for configuration:

- `OPENROUTER_API_KEY`: API key for OpenRouter
- `BOOKBOT_DRY_RUN`: If set to "true", "1", or "yes", enables dry run mode which avoids making real API calls
- `BOOKBOT_CHEAP_MODE`: If set to "true", "1", or "yes", uses a cheaper LLM model (Gemini Flash) regardless of the configured model

## Error Handling

The Bot system includes several error classes:

- `BookBotError`: Base exception for all BookBot errors
- `LLMError`: Errors related to LLM API calls, includes detailed information about API failures

The system includes retry logic for transient errors like timeouts and rate limits, but will raise an exception after multiple failures.

## Complete Example Workflow

Here's a complete example of how to use both systems together:

```python
# Initialize repository
doc_repo = DocRepo("/path/to/repo")

# Create BookWriter
writer = BookWriter(doc_repo, api_key="your_api_key")

# Create a prompt document if it doesn't exist
if "write_chapter" not in writer.list_prompts():
    prompt_doc = writer.create_prompt("write_chapter", BotType.WRITE_CHAPTER)

# Create or get input documents
outline_doc = doc_repo.get_doc("outline")
if not outline_doc:
    outline_doc = doc_repo.create_doc("outline", {"type": "outline"}, "# Story Outline\n\n## Chapter 1\n- Introduction")

setting_doc = doc_repo.get_doc("setting")
if not setting_doc:
    setting_doc = doc_repo.create_doc("setting", {"type": "setting"}, "# World Setting\n\nA medieval fantasy kingdom...")

characters_doc = doc_repo.get_doc("characters")
if not characters_doc:
    characters_doc = doc_repo.create_doc("characters", {"type": "characters"}, "# Characters\n\n## Protagonist\n- Description")

# Generate a chapter
content = writer.write_content(
    output_doc_name="chapter1",
    prompt_doc_name="write_chapter",
    template_vars={
        "chapter_number": "1",
        "outline": outline_doc,
        "setting": setting_doc,
        "characters": characters_doc,
        "previous_chapter": ""
    },
    command="write_chapter1"
)

# Access the generated document
chapter_doc = doc_repo.get_doc("chapter1")

# Display information
print(f"Chapter references: {chapter_doc.get_property('references')}")
print(f"Word count: {chapter_doc.get_property('word_count')}")
print(f"Token usage: {chapter_doc.get_property('input_tokens')} in, {chapter_doc.get_property('output_tokens')} out")

# Get JSON data
json_data = chapter_doc.get_json_data()
print(f"Document references: {json_data.get('doc_references', {})}")





# Command System

The Command system provides a standardized way to create, register, and execute operations within the BookBot system.

## Command Base Class

```python
class Command(ABC):
```

The `Command` class is an abstract base class that all custom commands must inherit from. It provides the basic structure and interface for command execution.

#### Properties

| Property | Type | Description |
|----------|------|-------------|
| `name` | `str` | The command name used to invoke it from the CLI |
| `description` | `str` | A brief description of what the command does |
| `usage` | `str` | Usage instructions shown in help text |

#### Methods

| Method | Parameters | Returns | Description |
|--------|------------|---------|-------------|
| `__init__` | `doc_repo`, `api_key=None` | None | Initialize a Command with a document repository and API key |
| `execute` | `args: List[str]` | `bool` | Execute the command with the given arguments |
| `update_status` | `status: str` | None | Update the current status of the command |
| `get_status` | None | `str` | Get the current status of the command |
| `get_token_usage` | None | `Dict[str, int]` | Get the current token usage statistics |
| `generate_content` | `**kwargs` | `str` | Generate content using the LLM, tracking token usage |
| `get_arg_info` | None | `Dict[str, str]` | Class method to get information about required arguments |

#### Example Implementation

```python
class WriteOutlineCommand(Command):
    @property
    def name(self) -> str:
        return "write-outline"
    
    @property
    def description(self) -> str:
        return "Generate a book outline from an initial concept"
    
    @property
    def usage(self) -> str:
        return "write-outline <output_name> <initial_concept_doc>"
    
    @classmethod
    def get_arg_info(cls) -> Dict[str, str]:
        return {
            "output_name": "Name for the generated outline document",
            "initial_concept_doc": "Document containing the initial book concept"
        }
    
    def execute(self, args: List[str]) -> bool:
        # Validate arguments
        if len(args) < 2:
            logger.error(f"Not enough arguments. Usage: {self.usage}")
            return False
        
        # Parse arguments
        outline_name = args[0]
        concept_doc_name = args[1]
        
        # Update status
        self.update_status(f"Starting to write outline {outline_name}")
        
        # Get required document
        concept_doc = self.doc_repo.get_doc(concept_doc_name)
        if not concept_doc:
            logger.error(f"Concept document '{concept_doc_name}' not found")
            return False
        
        # Set up template variables
        template_vars = {
            "initial": concept_doc
        }
        
        # Generate the outline
        self.update_status("Generating outline content")
        try:
            content = self.generate_content(
                output_doc_name=outline_name,
                prompt_doc_name="bot_outliner",  # Uses the outliner bot
                template_vars=template_vars,
                command=f"write_outline_{outline_name}"
            )
            
            self.update_status("Successfully wrote outline")
            return True
            
        except Exception as e:
            self.update_status(f"Error generating outline: {str(e)}")
            return False
```

### CommandRegistry

```python
class CommandRegistry:
```

The `CommandRegistry` manages command registration and creation, allowing command discovery and instantiation.

#### Methods

| Method | Parameters | Returns | Description |
|--------|------------|---------|-------------|
| `register` | `command_class: Type[Command]` | None | Register a command class |
| `get_command_class` | `name: str` | `Optional[Type[Command]]` | Get a command class by name |
| `create_command` | `name: str`, `doc_repo`, `api_key=None` | `Optional[Command]` | Create a command instance by name |
| `get_all_commands` | None | `Dict[str, Dict[str, Any]]` | Get information about all registered commands |

#### Example Usage

```python
# Register a custom command
CommandRegistry.register(WriteOutlineCommand)

# Create a command instance
doc_repo = DocRepo("./book_repo")
outline_cmd = CommandRegistry.create_command("write-outline", doc_repo)

# Execute command
outline_cmd.execute(["my_outline", "initial_concept"])
```

### Creating New Commands

To create a new command:

1. **Create a new class** that inherits from `Command`
2. **Implement required properties**: `name`, `description`, `usage`
3. **Implement the `execute` method** with your command's logic
4. **Implement `get_arg_info`** to define required arguments
5. **Register your command** with `CommandRegistry.register(YourCommand)`

Your command should:
- Update its status regularly using `self.update_status()`
- Track document input/output using the Action system
- Handle errors gracefully
- Return `True` for success or `False` for failure

# Action System

The Action system tracks command execution, providing logging, history, and state management.

### Action Class

```python
class Action:
```

The `Action` class represents a running `Command` with metadata, tracking execution progress and results.

#### Methods

| Method | Parameters | Returns | Description |
|--------|------------|---------|-------------|
| `__init__` | `command: Command`, `args: List[str]`, `actions_dir=DEFAULT_ACTIONS_DIR` | None | Initialize an Action |
| `update_state_file` | None | None | Update the state file with current action information |
| `record_input_doc` | `doc_name: str` | None | Record an input document used by this action |
| `record_output_doc` | `doc_name: str` | None | Record an output document produced by this action |
| `save_log` | None | None | Save the action log to a JSON file |
| `run` | None | `bool` | Run the command and track its execution |

#### Properties

| Property | Type | Description |
|----------|------|-------------|
| `command` | `Command` | The command being executed |
| `args` | `List[str]` | Command arguments |
| `pid` | `int` | Process ID of the running action |
| `start_time` | `str` | ISO-formatted start time |
| `end_time` | `str` | ISO-formatted end time (or None if running) |
| `status` | `str` | Current status (running, success, failure) |
| `input_docs` | `List[str]` | List of input document names |
| `output_docs` | `List[str]` | List of output document names |
| `log_file` | `str` | Path to the log file |

#### Example Usage

```python
# Create and run an action
cmd = WriteOutlineCommand(doc_repo)
action = Action(cmd, ["my_outline", "initial_concept"])
success = action.run()
```

### Action Status

```python
class ActionStatus:
```

The `ActionStatus` class defines status values for Actions.

#### Constants

| Constant | Value | Description |
|----------|-------|-------------|
| `RUNNING` | `"running"` | Action is currently executing |
| `SUCCESS` | `"success"` | Action completed successfully |
| `FAILURE` | `"failure"` | Action failed or was interrupted |

### Action Management Functions

Several utility functions help manage action state and history:

| Function | Parameters | Returns | Description |
|----------|------------|---------|-------------|
| `is_action_running` | None | `Optional[Dict[str, Any]]` | Check if an action is currently running |
| `kill_running_action` | None | `bool` | Kill a currently running action |
| `get_recent_actions` | `count=10`, `actions_dir=DEFAULT_ACTIONS_DIR` | `List[Dict[str, Any]]` | Get a list of recent actions |
| `render_action_log_as_text` | `action_data: Dict[str, Any]` | `str` | Render an action log as formatted text |
| `render_action_log_as_html` | `action_data: Dict[str, Any]` | `str` | Render an action log as HTML |

#### Example Usage

```python
# Check if an action is running
running_action = is_action_running()
if running_action:
    print(f"Action {running_action['command']} is currently running")
    
# Get recent action history
recent_actions = get_recent_actions(5)
for action in recent_actions:
    print(f"{action['command']} ({action['status']})")
    
# Render action log details
action_details = render_action_log_as_text(recent_actions[0])
print(action_details)
```

## Outline Utilities

The `outline_util` module provides functions for manipulating and extracting information from outlines, including chapter management and content retrieval.

### Chapter Management

| Function | Parameters | Returns | Description |
|----------|------------|---------|-------------|
| `renumber_chapters` | `outline_text: str` | `str` | Renumber all chapters in the outline sequentially |
| `count_chapters` | `outline_text: str` | `int` | Count the number of chapters in the outline |

#### Example Usage

```python
# Get the outline text
outline_doc = doc_repo.get_doc("my_outline")
outline_text = outline_doc.get_text()

# Count chapters
chapter_count = outline_util.count_chapters(outline_text)
print(f"The outline contains {chapter_count} chapters")

# Renumber chapters
fixed_outline = outline_util.renumber_chapters(outline_text)
outline_doc.update_text(fixed_outline)
```

### Tag Extraction

| Function | Parameters | Returns | Description |
|----------|------------|---------|-------------|
| `extract_tags` | `chapter_heading: str` | `Tuple[int, Set[str]]` | Extract the chapter number and tags from a chapter heading |
| `get_character_profiles` | `character_text: str`, `tags: Set[str]` | `Dict[str, str]` | Extract character profiles for specified tags |
| `get_setting_profiles` | `setting_text: str`, `tags: Set[str]` | `Dict[str, str]` | Extract setting profiles for specified tags |

#### Example Usage

```python
# Extract tags from a chapter heading
chapter_heading = "## Chapter 3: The Meeting #john #mary #cafe"
chapter_num, tags = outline_util.extract_tags(chapter_heading)
print(f"Chapter {chapter_num} involves tags: {tags}")

# Get character profiles for these tags
characters_doc = doc_repo.get_doc("characters")
character_text = characters_doc.get_text()
profiles = outline_util.get_character_profiles(character_text, tags)

for tag, profile in profiles.items():
    print(f"Character {tag}:\n{profile[:100]}...")
```

### Content Retrieval

| Function | Parameters | Returns | Description |
|----------|------------|---------|-------------|
| `find_chapter_heading` | `outline_text: str`, `chapter_num: int` | `Optional[str]` | Find the heading for a specific chapter |
| `find_chapter_content` | `outline_text: str`, `chapter_num: int` | `Optional[Tuple[str, str, str]]` | Find content for a chapter (heading, content, preceding section) |
| `get_chapter_content` | `outline_text: str`, `chapter_num: int`, `character_text: str`, `setting_text: str` | `Dict[str, str]` | Get complete content needed to write a chapter |

#### Example Usage

```python
# Get all content needed to write Chapter 3
chapter_content = outline_util.get_chapter_content(
    outline_text,
    3,
    character_text,
    setting_text
)

print("Chapter heading:", chapter_content['chapter_heading'])
print("Chapter content:", chapter_content['chapter_content'][:100], "...")
print("Characters:", chapter_content['characters'][:100], "...")
print("Settings:", chapter_content['settings'][:100], "...")

# Use all content for LLM prompt
all_content = chapter_content['all_content']
```

## Creating a Complete Write-Outline Command

Here's a full example of creating a command to write an outline from an initial concept:

```python
class WriteOutlineCommand(Command):
    """Command to generate a full book outline from an initial concept."""
    
    @property
    def name(self) -> str:
        return "write-outline"
    
    @property
    def description(self) -> str:
        return "Generate a book outline from an initial concept"
    
    @property
    def usage(self) -> str:
        return "write-outline <output_name> <initial_concept_doc> [<sections_count>]"
    
    @classmethod
    def get_arg_info(cls) -> Dict[str, str]:
        return {
            "output_name": "Name for the generated outline document",
            "initial_concept_doc": "Document containing the initial book concept",
            "sections_count": "Optional number of sections (default: 3)"
        }
    
    def execute(self, args: List[str]) -> bool:
        # Validate arguments
        if len(args) < 2:
            logger.error(f"Not enough arguments. Usage: {self.usage}")
            return False
        
        # Parse arguments
        outline_name = args[0]
        concept_doc_name = args[1]
        sections_count = int(args[2]) if len(args) > 2 else 3
        
        # Update status
        self.update_status(f"Starting to write outline {outline_name} with {sections_count} sections")
        
        # Get required document
        concept_doc = self.doc_repo.get_doc(concept_doc_name)
        if not concept_doc:
            logger.error(f"Concept document '{concept_doc_name}' not found")
            return False
            
        # Record input document (for the Action log)
        self.action.record_input_doc(concept_doc_name)
        
        # Set up template variables
        template_vars = {
            "initial": concept_doc,
            "sections_count": sections_count
        }
        
        # Generate the outline
        self.update_status("Generating outline content")
        try:
            content = self.generate_content(
                output_doc_name=outline_name,
                prompt_doc_name="bot_outliner",
                template_vars=template_vars,
                command=f"write_outline_{outline_name}"
            )
            
            # Record output document
            self.action.record_output_doc(outline_name)
            
            # Renumber chapters to ensure consistency
            outline_doc = self.doc_repo.get_doc(outline_name)
            if outline_doc:
                fixed_outline = outline_util.renumber_chapters(outline_doc.get_text())
                outline_doc.update_text(fixed_outline)
                
                # Count chapters for information
                chapter_count = outline_util.count_chapters(fixed_outline)
                self.update_status(f"Successfully wrote outline with {chapter_count} chapters")
            
            return True
            
        except Exception as e:
            self.update_status(f"Error generating outline: {str(e)}")
            logger.error(traceback.format_exc())
            return False
```

To use this command:

1. Save it in your commands module (e.g., `commands.py`)
2. Register it with `CommandRegistry.register(WriteOutlineCommand)`
3. Run it from the CLI: `python cli.py write-outline my_outline initial_concept 5`

The command will:
1. Read the initial concept document
2. Generate an outline using the outliner bot
3. Renumber chapters to ensure consistency
4. Report the number of chapters generated
5. Record all inputs, outputs, and token usage
```