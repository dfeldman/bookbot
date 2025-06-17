# BookBot Development Quick Start

## 🚀 Running the Development Environment

The easiest way to start both frontend and backend development servers:

```bash
./dev.sh
```

This script will:
- Kill any existing BookBot processes
- Create/activate Python virtual environment
- Install Python dependencies
- Start Flask backend on port 5001
- Install Node.js dependencies (if needed)
- Start Vite frontend on port 3004
- Show server status and logs

## 🛑 Stopping Development Servers

To stop all BookBot development servers:

```bash
./stop.sh
```

## 🔗 Development URLs

- **Frontend Application**: http://localhost:3004
- **Backend API**: http://localhost:5001
- **API Documentation**: http://localhost:5001/api

## 📱 Features

### ✅ Completed Features
- **Welcome Screen** with API token setup
- **Book Dashboard** with book management
- **Book Creation Wizard** for new books
- **Book Viewer** with 4-tab interface:
  - **Index**: Chapter/chunk organization with edit capabilities
  - **Read**: Reading interface with font customization
  - **Export**: Multiple format export (HTML, Markdown, Text)
  - **Settings**: Book configuration and statistics
- **Chunk Editor** for individual content editing
- **Jobs Viewer** for monitoring background tasks
- **Job Logs Viewer** for detailed job debugging
- **Status Bar** with job monitoring and navigation

### 🔧 Technical Stack
- **Frontend**: Vue 3 + TypeScript + Vite
- **Backend**: Flask + SQLAlchemy + SQLite
- **AI Integration**: OpenRouter API support
- **Job System**: Background task processing
- **Real-time Updates**: Auto-refresh for active jobs

## 🎯 Quick Development Tips

1. **First Run**: Visit http://localhost:3004 and set up your OpenRouter API token
2. **Create Books**: Use the wizard to create your first book
3. **Monitor Jobs**: Click the "Jobs" link in the status bar to view background tasks
4. **Edit Content**: Click any chunk in the Index tab to edit its content
5. **Export Books**: Use the Export tab to generate finished books in multiple formats

## 🛠️ Development Commands

```bash
# Start development (both frontend + backend)
./dev.sh

# Stop all development servers
./stop.sh

# Backend only (manual)
cd bookbot3
source venv/bin/activate
python app.py

# Frontend only (manual)
cd frontend
npm run dev
```

## 📝 Project Structure

```
bookbot3/
├── dev.sh              # Development startup script
├── stop.sh             # Stop all servers script
├── app.py              # Flask application entry point
├── backend/            # Python backend code
│   ├── api/           # REST API endpoints
│   ├── jobs/          # Background job system
│   ├── models/        # Database models
│   └── llm/           # AI/LLM integration
├── frontend/          # Vue.js frontend
│   ├── src/views/     # Main application views
│   ├── src/components/ # Reusable components
│   └── src/stores/    # State management
└── instance/          # SQLite database
```

## 🚨 Troubleshooting

- **Port conflicts**: The script automatically kills existing processes
- **Missing dependencies**: Run `pip install -r requirements.txt` and `npm install` in frontend/
- **API token issues**: Make sure you have a valid OpenRouter API token
- **Database issues**: Delete `instance/bookbot.db` to reset the database
