# BookBot CLI Tool

A comprehensive command-line interface for BookBot administration, debugging, and maintenance operations.

## Features

- 🔐 **Admin Authentication**: Uses admin API key for privileged operat# Check final status
./cli/bookbot books status <book_id>

# Export the completed book as HTML
./cli/bookbot books export <book_id>
```s
- 📚 **Complete CRUD**: All book, chunk, and job operations
- 🎯 **Developer Friendly**: Perfect for debugging and testing
- 📊 **Rich Output**: Colorful, informative command output
- 🔧 **Flexible**: Can target any BookBot server instance

## Installation

The CLI tool is included with BookBot. No additional installation required.

## Quick Start

1. **Start the BookBot server:**
   ```bash
   make run-backend
   ```

2. **Check server health:**
   ```bash
   ./cli/bookbot health
   ```

3. **Create a book:**
   ```bash
   ./cli/bookbot books create "My First Novel" --genre "Fiction"
   ```

## Authentication

The CLI tool uses an admin API key for authentication. You can provide it in several ways:

1. **Environment variable** (recommended):
   ```bash
   export BOOKBOT_ADMIN_KEY="your-admin-key"
   ./cli/bookbot health
   ```

2. **Command line argument:**
   ```bash
   ./cli/bookbot --admin-key "your-admin-key" health
   ```

3. **Default key**: If not specified, uses the default development key `admin-key-123`

## Commands

### Server Commands

```bash
# Check server health
./cli/bookbot health

# Get server configuration
./cli/bookbot config
```

### Book Operations

```bash
# List all books
./cli/bookbot books list

# Get a specific book
./cli/bookbot books get <book_id>

# Create a new book
./cli/bookbot books create "Book Title" --genre "Genre"
./cli/bookbot books create "My Novel" --props '{"author": "John Doe", "year": 2025}'

# Update a book
./cli/bookbot books update <book_id> --props '{"title": "New Title"}'

# Delete a book
./cli/bookbot books delete <book_id>

# Get book status (word count, chunks, jobs, etc.)
./cli/bookbot books status <book_id>

# Export book as HTML
./cli/bookbot books export <book_id>
./cli/bookbot books export <book_id> --output "my_book.html"
```

### Chunk Operations

```bash
# List chunks for a book
./cli/bookbot chunks list <book_id>

# List chunks with text content
./cli/bookbot chunks list <book_id> --text

# List chunks including deleted ones
./cli/bookbot chunks list <book_id> --deleted

# Filter chunks by chapter
./cli/bookbot chunks list <book_id> --chapter 1

# Get a specific chunk
./cli/bookbot chunks get <chunk_id>

# Get a specific version of a chunk
./cli/bookbot chunks get <chunk_id> --version 2

# Create a new chunk
./cli/bookbot chunks create <book_id> "# Chapter 1\n\nContent goes here..."
./cli/bookbot chunks create <book_id> "Text" --type "chapter" --chapter 1 --order 1.0

# Update a chunk (creates new version)
./cli/bookbot chunks update <chunk_id> --text "New content"
./cli/bookbot chunks update <chunk_id> --props '{"tags": ["revised"]}'

# Delete a chunk (soft delete)
./cli/bookbot chunks delete <chunk_id>

# List all versions of a chunk
./cli/bookbot chunks versions <chunk_id>
```

### Job Operations

```bash
# List jobs for a book
./cli/bookbot jobs list --book-id <book_id>

# List all running jobs
./cli/bookbot jobs list

# Filter jobs by state
./cli/bookbot jobs list --state "complete"

# Get a specific job
./cli/bookbot jobs get <job_id>

# Create a new job
./cli/bookbot jobs create <book_id> demo
./cli/bookbot jobs create <book_id> demo --props '{"target_word_count": 200}'

# Cancel a job
./cli/bookbot jobs cancel <job_id>

# Get job logs
./cli/bookbot jobs logs <job_id>

# Get last 10 log entries
./cli/bookbot jobs logs <job_id> --tail 10
```

## Advanced Usage

### Different Server URL

Target a different BookBot server:

```bash
./cli/bookbot --url "http://production-server:5000" health
```

### JSON Output

For scripting and automation:

```bash
./cli/bookbot --json books list
```

### Combining Commands

Create a complete workflow:

```bash
# Create a book
BOOK_ID=$(./cli/bookbot books create "Test Book" | grep "Book ID:" | cut -d' ' -f3)

# Add some content
./cli/bookbot chunks create $BOOK_ID "# Chapter 1\n\nThe story begins..."
./cli/bookbot chunks create $BOOK_ID "# Chapter 2\n\nThe plot thickens..."

# Start an AI job
./cli/bookbot jobs create $BOOK_ID demo --props '{"target_word_count": 150}'

# Check status
./cli/bookbot books status $BOOK_ID
```

## Examples

### Complete Book Creation Workflow

```bash
# 1. Create a new book
./cli/bookbot books create "The AI Chronicles" --genre "Science Fiction" --props '{"author": "BookBot", "year": 2025}'

# 2. Get the book ID from the output, then add outline
./cli/bookbot chunks create <book_id> "# Book Outline\n\n1. Introduction\n2. Rising Action\n3. Climax\n4. Resolution" --type "outline" --chapter 0

# 3. Add first chapter
./cli/bookbot chunks create <book_id> "# Chapter 1: The Beginning\n\nIn a world where AI had become commonplace..." --type "chapter" --chapter 1 --order 1.0

# 4. Start AI content generation
./cli/bookbot jobs create <book_id> demo --props '{"target_word_count": 500}'

# 5. Monitor the job
./cli/bookbot jobs logs <job_id>

# 6. Check final status
./cli/bookbot books status <book_id>
```

### Debugging and Maintenance

```bash
# Check what jobs are currently running
./cli/bookbot jobs list --state "running"

# Find books with many chunks
./cli/bookbot books list | grep "Chunks:"

# Clean up: delete old books
./cli/bookbot books list
./cli/bookbot books delete <old_book_id>

# Examine chunk history
./cli/bookbot chunks versions <chunk_id>

# Review job execution logs
./cli/bookbot jobs logs <job_id> --tail 20

# Export a book for review
./cli/bookbot books export <book_id>
```

### Book Export

The CLI includes an HTML export feature perfect for debugging and reviewing book content:

```bash
# Export book with auto-generated filename
./cli/bookbot books export <book_id>
# Creates: Book_Title_bookid.html

# Export with custom filename
./cli/bookbot books export <book_id> --output "my_book.html"
```

**Export Features:**
- 📚 **Complete Book**: All chunks in chapter/order sequence
- 🎨 **Styled Output**: Clean, readable HTML with CSS styling
- 📊 **Metadata**: Book and chunk properties, statistics, timestamps
- 🔍 **Debug Info**: Chunk IDs, versions, status indicators
- 📖 **Table of Contents**: Automatic chapter navigation
- 🏷️ **Type Highlighting**: Different styling for outlines, chapters, etc.
- 🗑️ **Deleted Content**: Shows deleted chunks (if any) with special styling
- 🔒 **Status Indicators**: Locked chunks, version info, etc.

The exported HTML is perfect for:
- Reviewing book structure and content
- Debugging chunk organization
- Sharing drafts with others
- Creating backups of book content
- Analyzing writing progress

## Tips

1. **Use environment variables** for the admin key to avoid typing it repeatedly
2. **Pipe commands** for automation: `./cli/bookbot books list | grep "Title"`
3. **Check server health** before running other commands
4. **Use --help** on any command to see all options: `./cli/bookbot books create --help`
5. **JSON props** must be valid JSON strings with double quotes

## Troubleshooting

### Connection Issues
```bash
# Check if server is running
./cli/bookbot health

# Check different URL
./cli/bookbot --url "http://localhost:5001" health
```

### Authentication Issues
```bash
# Verify admin key
export BOOKBOT_ADMIN_KEY="correct-admin-key"
./cli/bookbot health
```

### Invalid JSON Props
```bash
# ❌ Wrong: single quotes
./cli/bookbot books create "Test" --props "{'key': 'value'}"

# ✅ Correct: double quotes
./cli/bookbot books create "Test" --props '{"key": "value"}'
```

The CLI tool provides a powerful interface for all BookBot operations, making it easy to manage books, debug issues, and automate workflows.
