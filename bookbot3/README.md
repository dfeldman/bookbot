# BookBot - AI-Powered Book Writing Assistant

BookBot is a comprehensive full-stack application for AI-powered book writing. It features a Flask backend with REST APIs, background job processing, and a modern Vue 3 frontend with a professional user interface.

## 🚀 Features

### Backend
- **Book Management**: Complete CRUD operations for books with flexible metadata
- **Chunk System**: Versioned content management with soft deletion
- **Background Jobs**: Asynchronous processing for AI content generation (CreateFoundation job)
- **LLM Integration**: Pluggable LLM system with fake implementation for testing
- **Real-time Monitoring**: Server-sent events for job status updates
- **Comprehensive API**: RESTful endpoints with proper error handling
- **Database Flexibility**: SQLite for development, easy migration to PostgreSQL

### Frontend
- **Modern Vue 3 UI**: Professional welcome screen and book creation wizard
- **User Onboarding**: API token setup with real-time validation
- **3-Step Book Wizard**: Streamlined book creation with style selection
- **Dashboard**: Real-time job monitoring and book management
- **Responsive Design**: Works seamlessly on desktop and mobile
- **Professional Styling**: Modern gradients, cards, and smooth animations

## 📁 Project Structure

```
bookbot3/
├── app.py                 # Main Flask application
├── config.py             # Configuration management
├── requirements.txt      # Python dependencies
├── Makefile             # Build and development commands
├── demo.py              # System demonstration script
├── API_DOCS.md          # Complete API documentation
├── backend/
│   ├── models/          # Database models
│   ├── api/             # REST API endpoints
│   ├── jobs/            # Background job processing
│   │   ├── create_foundation.py  # Complete book foundation generation
│   │   └── job_utils.py          # Context extraction utilities
│   ├── llm/             # LLM integration layer
│   ├── auth.py          # Authentication & authorization
│   └── tests/           # Comprehensive unit tests
├── frontend/            # Vue 3 Frontend Application
│   ├── src/
│   │   ├── views/       # Main application views
│   │   │   ├── Welcome.vue    # Welcome/onboarding screen
│   │   │   ├── BookWizard.vue # Book creation wizard
│   │   │   └── Dashboard.vue  # Main dashboard
│   │   ├── stores/      # Pinia state management
│   │   ├── services/    # API integration layer
│   │   └── components/  # Reusable Vue components
│   ├── package.json     # Frontend dependencies
│   └── README.md        # Frontend documentation
├── cli/                 # Command-line interface
└── output_files/        # Generated file storage
```

## 🛠️ Setup & Installation

### Prerequisites
- Python 3.13+
- Node.js 18+
- pip and venv
- npm

### Quick Start

1. **Clone and setup the project:**
   ```bash
   git clone <repository-url>
   cd bookbot3
   make setup
   ```

2. **Set up the frontend:**
   ```bash
   cd frontend
   npm install
   npm run build
   cd ..
   ```

3. **Run both backend and frontend:**
   ```bash
   # Terminal 1: Backend (Flask)
   make run-backend
   
   # Terminal 2: Frontend (Vite dev server)
   cd frontend && npm run dev
   ```

4. **Access the application:**
   - Frontend: http://localhost:3000
   - Backend: http://localhost:5002
   - API Docs: See API_DOCS.md

### Available Commands

#### Backend
```bash
make setup              # Initial project setup
make run-backend        # Start the Flask development server
make test-backend       # Run unit tests
make db-reset          # Reset the database
make clean             # Clean build artifacts
```

#### Frontend
```bash
cd frontend
npm install            # Install dependencies
npm run dev           # Start development server
npm run build         # Build for production
npm run preview       # Preview production build
```

## 🔧 Configuration

The application can be configured via environment variables:

```bash
export DATABASE_URL="sqlite:///bookbot.db"
export SECRET_KEY="your-secret-key"
export DEBUG="True"
export ADMIN_API_KEY="admin-key-123"
```

## 📚 API Usage

### Base URL
```
http://localhost:5000/api
```

### Quick Examples

**Create a Book:**
```bash
curl -X POST http://localhost:5000/api/books \
  -H "Content-Type: application/json" \
  -d '{"props": {"title": "My Novel", "genre": "Fiction"}}'
```

**Add a Chapter:**
```bash
curl -X POST http://localhost:5000/api/books/{book_id}/chunks \
  -H "Content-Type: application/json" \
  -d '{"text": "# Chapter 1\n\nOnce upon a time...", "type": "chapter", "chapter": 1}'
```

**Start an AI Job:**
```bash
curl -X POST http://localhost:5000/api/books/{book_id}/jobs \
  -H "Content-Type: application/json" \
  -d '{"job_type": "demo", "props": {"target_word_count": 100}}'
```

See [API_DOCS.md](API_DOCS.md) for complete API documentation.

## 🧪 Testing

The project includes comprehensive unit tests:

```bash
make test-backend
```

Test coverage includes:
- Database models and relationships
- API endpoints and error handling
- Job processing system
- LLM integration
- Authentication and authorization

## 🔄 Background Jobs

BookBot supports three types of background jobs:

1. **Chunk Jobs**: Operate on individual chunks
2. **Book Jobs**: Process entire books
3. **Export Jobs**: Generate output files

Jobs are processed asynchronously with comprehensive logging and can be monitored in real-time via Server-Sent Events.

## 🤖 LLM Integration

The LLM system is designed to be pluggable:

- **Current**: Fake LLM for development and testing
- **Planned**: OpenRouter integration for multiple LLM providers
- **Features**: Token tracking, cost calculation, progress logging

## 📊 Database Schema

### Core Tables
- **Users**: User accounts and preferences
- **Books**: Book metadata and properties
- **Chunks**: Versioned content with word counting
- **Jobs**: Background task management
- **JobLogs**: Detailed execution logging
- **OutputFiles**: Generated export files

All models use flexible JSON props fields for extensibility.

## 🚦 System Status

The system provides comprehensive status monitoring:

- Health check endpoint
- Real-time job monitoring
- Book statistics (word count, chunk count)
- API token balance tracking

## 🔐 Security

- CSRF protection (configurable)
- Authentication framework (Google OAuth ready)
- Authorization decorators for all endpoints
- Admin API key for system management

## 🌐 Frontend Integration

The backend is designed to serve a Vue.js SPA:

- Static file serving
- Configuration endpoint for SPA setup
- CORS enabled for development
- Client-side routing support

## 📈 Future Enhancements

- [ ] Google OAuth integration
- [ ] Real LLM provider support (OpenRouter)
- [ ] PostgreSQL migration
- [ ] Multiple user collaboration
- [ ] Advanced job types
- [ ] File export (PDF, DOCX, etc.)
- [ ] Advanced search and filtering
- [ ] Workflow automation

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Run the test suite
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🆘 Support

For questions or issues:
1. Check the API documentation
2. Run the demo script to verify functionality
3. Check the logs for error details
4. Open an issue with reproduction steps

---

**BookBot** - Empowering authors with AI-assisted writing tools.
