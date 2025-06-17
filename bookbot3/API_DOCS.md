# BookBot API Documentation

## Overview

BookBot is an AI-powered book writing assistant that provides a REST API for managing books, chapters (chunks), and AI-generated content. The API is built with Flask and provides comprehensive book authoring capabilities.

## Base URL

```
http://localhost:5000/api
```

## Authentication

Currently, authentication is implemented but returns `true` for all operations to support development. Future versions will implement Google OAuth integration.

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

### Jobs

#### List Jobs
```http
GET /api/books/{book_id}/jobs?state=running
```

**Query Parameters:**
- `state`: Filter by job state (waiting, running, complete, error, cancelled)

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

#### Get Job
```http
GET /api/jobs/{job_id}
```

#### Cancel Job
```http
DELETE /api/jobs/{job_id}
```

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
      "log_entry": "Starting demo job",
      "log_level": "INFO",
      "created_at": "2025-06-13T10:00:00Z"
    }
  ]
}
```

#### Stream Job Updates (Server-Sent Events)
```http
GET /api/books/{book_id}/jobs/stream
```

Returns a stream of job updates for real-time monitoring.

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

#### demo
A demonstration job that generates lorem ipsum text and tests the job system.

**Props:**
```json
{
  "target_word_count": 100
}
```

### Custom Job Types

Additional job types can be registered with the job processor. Jobs are categorized as:

- **Chunk Jobs**: Inherit from `ChunkJob`, require `chunk_id` in props
- **Book Jobs**: Inherit from `BookJob`, operate on entire books  
- **Export Jobs**: Inherit from `ExportJob`, generate output files

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
