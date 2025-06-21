# BookBot Frontend Documentation

## Table of Contents
1. [Architecture Overview](#architecture-overview)
2. [Technology Stack](#technology-stack)
3. [Project Structure](#project-structure)
4. [Core Components](#core-components)
5. [State Management](#state-management)
6. [API Integration](#api-integration)
7. [User Journeys](#user-journeys)
8. [Markdown Editor](#markdown-editor)
9. [Best Practices](#best-practices)
10. [Deployment](#deployment)

## Architecture Overview

BookBot's frontend is built with Vue 3 using the Composition API, providing a modern, reactive, and component-based architecture. The application follows a standard Vue project structure, with separate directories for components, views, services, and stores.

The frontend communicates with the backend API through RESTful endpoints and uses server-sent events for real-time job tracking. State management is handled via Pinia stores, which provide a clean and type-safe way to manage application state.

### Key Architectural Principles:

- **Component-Based Design**: UI is constructed from reusable components
- **Single Responsibility**: Each component handles one specific aspect of the UI
- **Composition API**: Leverages Vue 3's reactive system for clean, reusable code
- **Type Safety**: Uses TypeScript for improved developer experience and fewer runtime errors
- **Centralized State Management**: Uses Pinia for predictable state management
- **RESTful Communication**: Standard API patterns for backend interaction

## Technology Stack

- **Framework**: Vue 3 with Composition API
- **Routing**: Vue Router
- **State Management**: Pinia
- **HTTP Client**: Axios
- **UI Framework**: Custom components with CSS
- **Rich Text Editing**: TipTap (built on ProseMirror)
- **Build Tool**: Vite

## Project Structure

```
frontend/
├── public/             # Static assets
├── src/
│   ├── assets/         # Images, fonts, etc.
│   ├── components/     # Reusable UI components
│   │   ├── MarkdownEditor.vue  # Custom markdown editor
│   │   └── ...
│   ├── views/          # Page components
│   │   ├── Welcome.vue
│   │   ├── Dashboard.vue
│   │   ├── BookViewer.vue
│   │   ├── ChunkEditor.vue
│   │   └── ...
│   ├── services/       # API and other services
│   │   └── api.ts      # API client
│   ├── stores/         # Pinia stores
│   │   ├── app.ts      # Application state
│   │   ├── book.ts     # Book management
│   │   └── jobStore.ts # Job tracking
│   ├── utils/          # Helper functions
│   ├── App.vue         # Root component
│   └── main.ts         # Application entry point
├── package.json        # Dependencies
└── vite.config.js      # Build configuration
```

## Core Components

### Views (Pages)

- **Welcome.vue**: Landing page
- **Dashboard.vue**: Main hub showing books and ongoing activities
- **BookWizard.vue**: Interface for creating new books
- **BookViewer.vue**: Displays book structure and chunks
- **ChunkEditor.vue**: Edit individual book chunks
- **JobsViewer.vue**: Monitor and manage AI jobs
- **JobLogsViewer.vue**: Detailed logs for AI jobs
- **JobDetailsViewer.vue**: Individual job information
- **EditorDemo.vue**: Demonstration of the editor capabilities

### Key Components

- **MarkdownEditor.vue**: Custom rich text editor that:
  - Supports markdown formatting (headings, bold, italic)
  - Highlights tags and scene references
  - Provides both viewing and editing modes
  - Maintains cursor position during typing
  - Displays word count
  - Handles undo/redo operations

## State Management

The application uses Pinia for state management, with several specialized stores:

### App Store (app.ts)
Manages global application state including:
- Authentication status
- UI themes and preferences
- Global notifications and alerts
- API key configuration

### Book Store (book.ts)
Handles all book-related state:
- Current active book
- Book metadata
- Chunks and their organization
- Book editing operations

### Job Store (jobStore.ts)
Manages AI job processing:
- Tracks running jobs
- Stores job history
- Monitors job progress
- Handles job cancellation

## API Integration

All backend communication is handled through the `apiService` in `services/api.ts`, which provides:

### Key API Endpoints:

#### Book Management
- `getBooks()`: Retrieve all books
- `getBook(bookId)`: Get a specific book
- `createBook(data)`: Create a new book
- `updateBook(bookId, data)`: Update book details
- `deleteBook(bookId)`: Delete a book

#### Chunk Management
- `getChunks(bookId)`: Get all chunks in a book
- `getChunk(chunkId)`: Get a specific chunk
- `createChunk(bookId, data)`: Create a new chunk
- `updateChunk(chunkId, data)`: Update chunk content
- `deleteChunk(chunkId)`: Delete a chunk
- `getChunkContext(bookId, chunkId)`: Get surrounding context

#### Job Management
- `getJobs(bookId)`: Get jobs for a specific book
- `getJob(jobId)`: Get details of a job
- `getJobLogs(jobId)`: Get execution logs
- `createJob(bookId, data)`: Create a new AI job
- `cancelJob(jobId)`: Cancel a running job
- `getRunningJobs()`: Get all currently running jobs
- `getAllJobs()`: Get all historical jobs
- `getTotalCostAllJobs()`: Calculate total API costs

### Real-time Updates
- `createJobEventSource(bookId)`: Creates an EventSource for server-sent events to track job progress in real-time

## User Journeys

### 1. Book Creation Journey

1. **Start**: User lands on Welcome page (`/`)
2. User clicks "Create New Book" button
3. **BookWizard** (`/wizard`):
   - User enters book title and description
   - Sets initial parameters for AI generation
   - Creates book outline structure
4. Book is created via `apiService.createBook()`
5. User is redirected to **BookViewer** (`/books/:bookId`)

### 2. Writing & Editing Journey

1. **Start**: User navigates to Dashboard (`/dashboard`)
2. User selects a book from the list
3. **BookViewer** (`/books/:bookId`):
   - Displays book structure and chunks
   - User can view chunk summaries
4. User clicks on a chunk to edit
5. **ChunkEditor** (`/books/:bookId/chunks/:chunkId/edit`):
   - MarkdownEditor component loads with chunk content
   - User reads content in display mode
   - User clicks on text to enter edit mode
   - Toolbar appears with formatting options
   - User edits content with rich text controls
   - Hashtags and scene references are automatically highlighted
   - Word count updates as user types
6. User finishes editing and clicks away to exit edit mode
7. Changes are saved via `apiService.updateChunk()`

### 3. AI Generation Journey

1. **Start**: User is in ChunkEditor viewing a chunk
2. User clicks "Generate" or "Improve" button
3. Generation parameters form appears:
   - User sets AI parameters (creativity, length, etc.)
   - User submits generation request
4. Job is created via `apiService.createJob()`
5. **Job Progress**:
   - Real-time updates via EventSource connection
   - Progress displayed in UI
   - User can view running job in JobsViewer
6. When job completes:
   - Content is updated in the editor
   - User can edit or regenerate as needed

### 4. Job Monitoring Journey

1. **Start**: User navigates to Jobs page (`/jobs`)
2. **JobsViewer**:
   - Displays all jobs with status (pending, complete, error)
   - Shows costs and resource usage statistics
3. User clicks on a specific job
4. **JobDetailsViewer** (`/jobs/:jobId`):
   - Shows detailed job information
   - Displays input parameters and results
5. User clicks "View Logs"
6. **JobLogsViewer** (`/jobs/:jobId/logs`):
   - Shows detailed execution logs
   - Helps with debugging failed jobs

## Markdown Editor

The custom MarkdownEditor component (`components/MarkdownEditor.vue`) is a key feature of the application, providing a rich editing experience with dual display/edit modes.

### Key Features

- **Click-to-Edit Interface**: Users can click anywhere on the display text to activate editing
- **Rich Text Toolbar**: Format text with headings, bold, and italic
- **Undo/Redo**: Full history management
- **Tag Highlighting**: Automatically highlights #tags and [[Scene XXX]] references
- **Word Count**: Shows total word count during editing
- **Responsive Design**: Adapts to different screen sizes
- **Consistent Cursor Behavior**: Maintains cursor position during typing

### Technical Implementation

- Built on TipTap/ProseMirror for robust rich text editing
- Custom extensions for special content like scene references
- Uses Vue 3 Composition API for reactivity
- Converts between HTML and Markdown seamlessly
- Prevents layout shifts when toggling between modes

### Usage Example

```vue
<template>
  <MarkdownEditor
    v-model="content"
    placeholder="Start writing..."
    :readonly="isLocked"
    :showToolbar="true"
    :showWordCount="true"
    :fontFamily="'Georgia, serif'"
    :fontSize="'18px'"
    @edit-mode-change="handleEditModeChange"
  />
</template>

<script setup>
import { ref } from 'vue'
import MarkdownEditor from '@/components/MarkdownEditor.vue'

const content = ref('# Hello World\nThis is an example.')
const isLocked = ref(false)

const handleEditModeChange = (isEditing) => {
  console.log('Editor mode changed:', isEditing ? 'editing' : 'viewing')
}
</script>
```

## Best Practices

### Performance Optimization

- **Lazy Loading**: Routes use Vue Router's lazy loading for better initial load times
- **Component Reuse**: Shared functionality extracted into reusable components
- **Debounced Updates**: Text input changes are debounced to reduce unnecessary API calls
- **Cached Data**: Pinia stores cache API results to minimize redundant requests

### State Management

- **Single Source of Truth**: All shared state managed through Pinia stores
- **Atomic Updates**: State changes are discrete and predictable
- **Computed Properties**: Derived state is calculated with Vue's reactive system

### Error Handling

- **Global Error Interceptor**: API service includes response interceptors to catch and process errors
- **User Feedback**: Errors are displayed through a notification system
- **Graceful Degradation**: Components handle missing data gracefully

## Deployment

The frontend is built with Vite, which generates optimized static assets for deployment.

### Build Process

1. Frontend code is compiled with `npm run build`
2. Generated assets are placed in the `dist` directory
3. Static assets can be served by any HTTP server

### Development Setup

1. Install dependencies: `npm install`
2. Run development server: `npm run dev`
3. Access development version at `http://localhost:5173`

---

This documentation provides a comprehensive overview of the BookBot frontend architecture. For specific implementation details, refer to the code comments and TypeScript interfaces within each file.
