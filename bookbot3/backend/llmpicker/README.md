# LLM Picker Module

The LLM Picker module provides a system for managing Large Language Models (LLMs) in the BookBot application. It enables selecting the appropriate LLM for different job types based on defaults, overrides, and group assignments.

## Overview

All LLM calls are routed through OpenRouter, and this module helps determine which specific LLM to use for each call based on:

1. The job type's requirements
2. Book-specific default preferences
3. Optional book-level or job-level overrides

## LLM Groups

LLMs are categorized into the following functional groups:

- **writer**: For text generation tasks
- **editor**: For text editing and correction
- **explicit**: For dealing with adult or sensitive content
- **tagger**: For content classification and tagging
- **thinker**: For analytical tasks like planning and reasoning
- **reviewer**: For reviewing and evaluating content
- **override**: Special group for LLMs that can be used as overrides

Each job type specifies which group(s) it requires access to via the `allowed_llm_group` class attribute.

## LLM Catalog

LLM metadata is stored in a static JSON file (`llms.json`) containing information about each LLM:

```json
{
  "id": "anthropic/claude-3-haiku",
  "input_cost_per_mtok": 0.25,
  "output_cost_per_mtok": 1.25,
  "seconds_per_output_mtok": 30,
  "router": "openrouter",
  "name": "Claude 3 Haiku",
  "description": "Fast and compact model for everyday tasks",
  "company": "Anthropic",
  "context_length": 200000,
  "valid_groups": ["writer", "editor", "tagger", "thinker", "reviewer"],
  "quality_score": 8
}
```

## API Endpoints

### LLM Listing

- **GET /api/llms/**  
  List all available LLMs
  
- **GET /api/llms/?group={group_name}**  
  List LLMs filtered by group

### Book LLM Defaults

- **GET /api/llms/books/{book_id}/defaults**  
  Get LLM defaults for a specific book
  
- **PUT /api/llms/books/{book_id}/defaults/{group}**  
  Set the default LLM for a specific group in a book
  
- **DELETE /api/llms/books/{book_id}/defaults/{group}**  
  Clear the default LLM for a specific group in a book

### Book LLM Override

- **GET /api/llms/books/{book_id}/override**  
  Get the current LLM override for a book
  
- **PUT /api/llms/books/{book_id}/override**  
  Set the LLM override for a book
  
- **DELETE /api/llms/books/{book_id}/override**  
  Clear the LLM override for a book

## Integration with Job System

Each job class should specify the LLM group it requires:

```python
class ExampleJob:
    allowed_llm_group = "writer"  # This job uses writer LLMs
```

When executing a job, use the `select_llm_for_job` utility to determine the appropriate LLM:

```python
from backend.llmpicker.catalog import select_llm_for_job

def execute(self):
    llm = select_llm_for_job(self.__class__, book, job_props)
    # Use llm.id in your LLM call
```

## Overrides

1. **Book-level override**:  
   Setting a book's override LLM forces all jobs for that book to use the specified LLM.
   
2. **Job-specific override**:  
   A job can specify an LLM through its `props` dictionary (`"llm_id": "model-name"`).

## Selection Priority

When selecting an LLM, the following priority is observed:

1. Book's override LLM (if set)
2. Job-specific LLM in job props (if specified)
3. Book's default LLM for the job's group (if set)
4. Highest quality LLM valid for the job's group
