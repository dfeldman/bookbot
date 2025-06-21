# BookBot API Documentation

## Overview

BookBot is an AI-powered book writing assistant that provides a REST API for managing books, chapters (chunks), and AI-generated content. The API is built with Flask and provides comprehensive book authoring capabilities.

## Base URL

```
http://localhost:5001/api
```

## Authentication

Currently, authentication is implemented but returns `true` for all operations to support development. Future versions will implement Google OAuth integration.

### Authentication Requirements

Endpoints are protected by different authentication levels:

- **require_auth**: Basic authentication required
- **require_read_access**: Book read permission required
- **require_edit_access**: Book edit permission required

## API Endpoints

### Configuration

#### GET /config
Get configuration information for the SPA client.

**Response:**
```json
{
  "api_url": "http://localhost:5000",
  "app_name": "BookBot",
  "version": "1.0.0",
  "debug": true
}
```

#### GET /health
Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0", 
  "database": "connected"
}
```

### Books

#### GET /books
List all books for the current user.

**Response:**
```json
{
  "books": [
    {
      "book_id": "uuid",
      "user_id": "uuid", 
      "props": {
        "title": "My Book",
        "genre": "Fiction"
      },
      "is_locked": false,
      "job": null,
      "created_at": "2025-06-13T10:00:00Z",
      "updated_at": "2025-06-13T10:00:00Z",
      "chunk_count": 5,
      "word_count": 1250
    }
  ]
}
```

#### POST /books
Create a new book.

**Request:**
```json
{
  "props": {
    "title": "New Book",
    "genre": "Science Fiction",
    "model_mode": "fake"
  }
}
```

**Response:** Returns the created book object with `201` status.

#### GET /books/{book_id}
Get a specific book by ID.

**Response:** Returns the book object with statistics.

#### PUT /books/{book_id}
Update a book's properties.

**Request:**
```json
{
  "props": {
    "title": "Updated Title",
    "genre": "Fantasy"
  }
}
```

**Response:** Returns the updated book object.

#### DELETE /books/{book_id}
Delete a book and all associated data (chunks, jobs, output files).

**Response:**
```json
{
  "message": "Book deleted successfully"
}
```

#### GET /books/{book_id}/status
Get comprehensive status information for a book.

**Response:**
```json
{
  "book_id": "uuid",
  "chunk_count": 10,
  "word_count": 2500,
  "latest_job": {
    "job_id": "uuid",
    "job_type": "demo",
    "state": "complete",
    "created_at": "2025-06-13T10:00:00Z"
  },
  "api_token_balance": 25.50,
  "is_locked": false
}
```

### Jobs
Background jobs handle LLM content generation and other time-consuming operations. Jobs can be:
- **Chunk jobs**: Process individual chunks
- **Book jobs**: Process entire books
- **Export jobs**: Generate output files

## Endpoints

### Core Configuration

#### Get Configuration
```http
GET /api/config
```

Returns configuration data for the SPA client.

**Response:**
```json
{
  "api_url": "http://localhost:5000",
  "app_name": "BookBot",
  "version": "1.0.0",
  "debug": true
}
```

#### Health Check
```http
GET /api/health
```

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "database": "connected"
}
```

### Books

#### List Books
```http
GET /api/books
```

Returns all books for the current user with statistics.

**Response:**
```json
{
  "books": [
    {
      "book_id": "uuid",
      "user_id": "uuid", 
      "props": {},
      "is_locked": false,
      "job": null,
      "chunk_count": 5,
      "word_count": 1250,
      "created_at": "2025-06-13T10:00:00Z",
      "updated_at": "2025-06-13T10:00:00Z"
    }
  ]
}
```

#### Create Book
```http
POST /api/books
Content-Type: application/json

{
  "props": {
    "title": "My Book",
    "genre": "Fiction",
    "api_key": "your-llm-api-key"
  }
}
```

#### Get Book
```http
GET /api/books/{book_id}
```

#### Update Book
```http
PUT /api/books/{book_id}
Content-Type: application/json

{
  "props": {
    "title": "Updated Title"
  }
}
```

#### Delete Book
```http
DELETE /api/books/{book_id}
```

Permanently deletes the book and all associated chunks, jobs, and logs.

#### Get Book Status
```http
GET /api/books/{book_id}/status
```

Returns comprehensive status information including job status, token balance, and statistics.

**Response:**
```json
{
  "book_id": "uuid",
  "chunk_count": 5,
  "word_count": 1250,
  "latest_job": {
    "job_id": "uuid",
    "job_type": "demo",
    "state": "complete",
    "created_at": "2025-06-13T10:00:00Z"
  },
  "api_token_balance": 25.50,
  "is_locked": false
}
```

### Chunks

#### List Chunks
```http
GET /api/books/{book_id}/chunks?include_text=true&include_deleted=false&chapter=1
```

**Query Parameters:**
- `include_text` (boolean): Include chunk text content
- `include_deleted` (boolean): Include soft-deleted chunks  
- `chapter` (integer): Filter by chapter number

#### Create Chunk
```http
POST /api/books/{book_id}/chunks
Content-Type: application/json

{
  "props": {
    "tags": ["outline", "chapter1"]
  },
  "text": "# Chapter 1\n\nThis is the first chapter...",
  "type": "chapter",
  "order": 1.0,
  "chapter": 1
}
```

#### Get Chunk
```http
GET /api/chunks/{chunk_id}?version=2
```

Gets a specific version of a chunk. Omit version to get the latest.

#### Update Chunk
```http
PUT /api/chunks/{chunk_id}
Content-Type: application/json

{
  "text": "Updated chapter content...",
  "props": {
    "tags": ["revised", "chapter1"]
  }
}
```

Creates a new version of the chunk. The previous version is preserved.

#### Delete Chunk
```http
DELETE /api/chunks/{chunk_id}
```

Soft deletes all versions of the chunk.

#### List Chunk Versions
```http
GET /api/chunks/{chunk_id}/versions
```

#### Cleanup Old Versions
```http
POST /api/chunks/{chunk_id}/cleanup-old-versions
Content-Type: application/json

{
  "keep_versions": 3
}
```

#### Cleanup Deleted Chunks
```http
POST /api/books/{book_id}/chunks/cleanup-deleted
```

#### Get Chunk Context
```http
GET /api/books/{book_id}/chunks/{chunk_id}/context
```

**Authentication:** Requires read access to the book

**Description:** Gets relevant context for a chunk, including outline, character, and setting information. This is primarily used for scene chunks to help with content generation.

**Response Example** (when context is available):
```json
{
  "outline_section": "In this chapter, the protagonist discovers the hidden temple...",
  "characters_sections": [
    {
      "name": "John Smith",
      "description": "The main character, a 35-year-old archaeologist with..."
    },
    {
      "name": "Maria Lopez",
      "description": "John's research assistant and close friend..."
    }
  ],
  "settings_sections": [
    {
      "name": "Hidden Temple",
      "description": "An ancient stone structure covered in vines..."
    }
  ],
  "tags": ["discovery", "adventure", "ancient artifacts"],
  "available": true
}
```

**Response** (when context is not available):
```json
{
  "outline_section": "",
  "characters_sections": [],
  "settings_sections": [],
  "tags": [],
  "available": false
}
```

**Errors:**
- 404: Chunk not found
- 500: Failed to get context

### Jobs

#### List Jobs for Book
```http
GET /api/books/{book_id}/jobs?state=running
```

**Authentication:** Requires read access to the book

**Query Parameters:**
- `state`: Filter by job state (waiting, running, complete, error, cancelled)

**Response:**
```json
{
  "jobs": [
    {
      "job_id": "uuid",
      "book_id": "uuid",
      "job_type": "create_foundation",
      "props": {},
      "state": "complete",
      "total_cost": 0.05,
      "created_at": "2025-06-20T15:30:00Z",
      "started_at": "2025-06-20T15:30:05Z",
      "completed_at": "2025-06-20T15:35:00Z",
      "error_message": null
    }
  ]
}
```

#### List All Jobs
```http
GET /api/jobs?state=running&job_type=create_foundation&limit=100
```

**Authentication:** Requires basic authentication

**Query Parameters:**
- `state`: Filter by job state (waiting, running, complete, error, cancelled)
- `job_type`: Filter by job type (e.g., create_foundation, generate_text)
- `limit`: Maximum number of jobs to return (default: 100)

**Response:** Same format as List Jobs for Book

#### List Running Jobs
```http
GET /api/jobs/running
```

**Authentication:** Requires basic authentication

**Response:** Same format as List Jobs for Book

#### Get Total Job Cost
```http
GET /api/jobs/total_cost
```

**Authentication:** Requires basic authentication

**Response:** 
```json
{
  "total_cost": 0.567
}
```

#### Create Job
```http
POST /api/books/{book_id}/jobs
Content-Type: application/json

{
  "job_type": "demo",
  "props": {
    "chunk_id": "uuid",
    "target_word_count": 500
  }
}
```

**Authentication:** Requires edit access to the book

**Request Body:**
- `job_type` (string, required): The type of job to create (e.g., demo, create_foundation, generate_text)
- `props` (object): Job-specific properties depending on the job type

**Response:** Returns the created job object with HTTP status 201
```json
{
  "job_id": "uuid",
  "book_id": "uuid",
  "job_type": "demo",
  "props": {
    "chunk_id": "uuid",
    "target_word_count": 500
  },
  "state": "waiting",
  "total_cost": 0,
  "created_at": "2025-06-20T15:30:00Z",
  "started_at": null,
  "completed_at": null,
  "error_message": null
}
```

**Errors:**
- 400: Bad request (missing job_type or unknown job_type)
- 404: Book not found

#### Get Job
```http
GET /api/jobs/{job_id}
```

**Response:**
```json
{
  "job_id": "uuid",
  "book_id": "uuid",
  "job_type": "create_foundation",
  "props": {},
  "state": "complete",
  "total_cost": 0.05,
  "created_at": "2025-06-20T15:30:00Z",
  "started_at": "2025-06-20T15:30:05Z",
  "completed_at": "2025-06-20T15:35:00Z",
  "error_message": null
}
```

**Errors:**
- 404: Job not found

#### Cancel Job
```http
DELETE /api/jobs/{job_id}
```

**Response:**
```json
{
  "message": "Job cancelled successfully"
}
```

**Errors:**
- 400: Job cannot be cancelled (already completed/failed)
- 404: Job not found

#### Get Job Logs
```http
GET /api/jobs/{job_id}/logs
```

**Response:**
```json
{
  "logs": [
    {
      "id": 1,
      "job_id": "uuid",
      "log_entry": "Starting job",
      "log_level": "INFO",
      "props": {},
      "created_at": "2025-06-20T15:30:00Z"
    },
    {
      "id": 2,
      "job_id": "uuid",
      "log_entry": "Processing chunk 1",
      "log_level": "INFO",
      "props": {"chunk_id": "uuid"},
      "created_at": "2025-06-20T15:30:05Z"
    },
    {
      "id": 3,
      "job_id": "uuid",
      "log_entry": "API call to LLM service",
      "log_level": "LLM",
      "props": {
        "model": "gpt-4",
        "prompt_tokens": 1024,
        "completion_tokens": 512,
        "llm_cost": 0.05,
        "stop_reason": "length"
      },
      "created_at": "2025-06-20T15:31:00Z"
    },
    {
      "id": 4,
      "job_id": "uuid",
      "log_entry": "Job completed successfully",
      "log_level": "INFO",
      "props": {},
      "created_at": "2025-06-20T15:35:00Z"
    }
  ]
}
```

**Errors:**
- 404: Job not found

#### Stream Job Updates (Server-Sent Events)
```http
GET /api/books/{book_id}/jobs/stream
```

**Authentication:** Requires read access to the book

**Description:** Returns a stream of job updates for real-time monitoring using Server-Sent Events (SSE) protocol. The connection remains open and the server pushes updates as they occur.

**Response:** Server-sent events in the following format:

```
data: {"type":"job_update","job":{"job_id":"uuid","state":"running","started_at":"2025-06-20T15:30:05Z"}}

data: {"type":"heartbeat","timestamp":1719096702.45}

data: {"type":"job_update","job":{"job_id":"uuid","state":"complete","completed_at":"2025-06-20T15:35:00Z"}}
```

**Notes:**
- The server sends heartbeat events every 2 seconds to keep the connection alive
- Event types include `job_update` and `heartbeat`
- Client should implement SSE protocol to consume these events

#### List Running Jobs
```http
GET /api/jobs/running
```

### LLM Token Status

#### Check Token Status
```http
POST /api/token-status
Content-Type: application/json

{
  "api_key": "your-llm-api-key"
}
```

**Response:**
```json
{
  "valid": true,
  "balance": 25.50,
  "currency": "USD"
}
```

## Data Models

### Book
```json
{
  "book_id": "string (UUID)",
  "user_id": "string (UUID)",
  "props": "object (flexible metadata)",
  "is_locked": "boolean",
  "job": "string (UUID, nullable)",
  "created_at": "string (ISO 8601)",
  "updated_at": "string (ISO 8601)"
}
```

### Chunk
```json
{
  "id": "integer (auto-increment)",
  "book_id": "string (UUID)",
  "chunk_id": "string (UUID)",
  "version": "integer",
  "is_latest": "boolean",
  "props": "object (flexible metadata)",
  "text": "string (Markdown content)",
  "type": "string",
  "is_locked": "boolean", 
  "is_deleted": "boolean",
  "job": "string (UUID, nullable)",
  "order": "float",
  "chapter": "integer",
  "word_count": "integer",
  "created_at": "string (ISO 8601)",
  "updated_at": "string (ISO 8601)"
}
```

### Job
```json
{
  "job_id": "string (UUID)",
  "book_id": "string (UUID)", 
  "job_type": "string",
  "props": "object (job-specific data)",
  "state": "string (waiting|running|complete|error|cancelled)",
  "created_at": "string (ISO 8601)",
  "started_at": "string (ISO 8601, nullable)",
  "completed_at": "string (ISO 8601, nullable)"
}
```

## Error Responses

All endpoints return consistent error responses:

```json
{
  "error": "Error message description"
}
```

Common HTTP status codes:
- `400 Bad Request`: Invalid request data
- `401 Unauthorized`: Authentication required
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `423 Locked`: Resource is locked by a running job
- `500 Internal Server Error`: Server error

## Job Types

### Built-in Job Types

The BookBot system includes several pre-defined job types, each handling specific tasks within the book creation and editing workflow.

#### demo
A demonstration job that generates lorem ipsum text and tests the job system.

**Props:**
```json
{
  "target_word_count": 100
}
```

#### create_foundation
Creates the initial foundation structure for a book, including chapters, sections, and basic content.

**Props:**
```json
{
  "title": "Book Title",
  "genre": "Fiction",
  "style": "Contemporary",
  "brief": "A brief description of what the book should be about"
}
```

#### generate_text
Generates or regenerates text for a specific chunk using an LLM.

**Props:**
```json
{
  "chunk_id": "uuid",
  "prompt_template": "optional custom prompt template",
  "context_items": ["characters", "settings", "outline"],
  "style": "descriptive"
}
```

### Custom Job Types

Additional job types can be registered with the job processor. Jobs are categorized as:

- **Chunk Jobs**: Inherit from `ChunkJob`, require `chunk_id` in props
- **Book Jobs**: Inherit from `BookJob`, operate on entire books  
- **Export Jobs**: Inherit from `ExportJob`, generate output files

## Client Integration

### TypeScript Interfaces

```typescript
// Book interfaces
interface Book {
  book_id: string;
  user_id: string;
  props: Record<string, any>;
  is_locked: boolean;
  job: string | null;
  created_at: string;
  updated_at: string;
  chunk_count?: number;
  word_count?: number;
}

// Chunk interfaces
interface Chunk {
  id: number;
  book_id: string;
  chunk_id: string;
  version: number;
  is_latest: boolean;
  is_locked: boolean;
  is_deleted: boolean;
  props: Record<string, any>;
  text?: string;
  type: string;
  order: number;
  chapter: number;
  word_count: number;
  created_at: string;
  updated_at: string;
}

// Job interfaces
interface Job {
  job_id: string;
  book_id: string;
  job_type: string;
  props: Record<string, any>;
  state: 'waiting' | 'running' | 'complete' | 'error' | 'cancelled';
  total_cost: number;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
  error_message: string | null;
}

interface JobLog {
  id: number;
  job_id: string;
  log_entry: string;
  log_level: 'DEBUG' | 'INFO' | 'WARNING' | 'ERROR' | 'LLM';
  props: Record<string, any>;
  created_at: string;
}
```

### cURL Examples

#### List books
```bash
curl -X GET "http://localhost:5001/api/books" \
  -H "Authorization: Bearer YOUR_AUTH_TOKEN"
```

#### Create a book
```bash
curl -X POST "http://localhost:5001/api/books" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_AUTH_TOKEN" \
  -d '{"props": {"title": "My New Book", "genre": "Science Fiction", "model_mode": "fake"}}'
```

#### Create a job
```bash
curl -X POST "http://localhost:5001/api/books/YOUR_BOOK_ID/jobs" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_AUTH_TOKEN" \
  -d '{"job_type": "create_foundation", "props": {"title": "My Book Title", "genre": "Fantasy", "brief": "A story about a young wizard"}}'
```

#### Get job logs
```bash
curl -X GET "http://localhost:5001/api/jobs/YOUR_JOB_ID/logs" \
  -H "Authorization: Bearer YOUR_AUTH_TOKEN"
```

## Development

### Running the Backend
```bash
make setup
make run-backend
```

### Creating a Demo Job
```bash
make demo-job
```

### Database Management
```bash
make db-init    # Initialize database
make db-reset   # Reset database
```

### Testing
```bash
make test-backend
```

For more development commands, see the Makefile.
