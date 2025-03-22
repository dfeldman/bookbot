# Document and Bot Systems API Documentation

This document provides comprehensive API documentation for both the Document system and the Bot system, which work together to provide a powerful content generation platform.

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
```