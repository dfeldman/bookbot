# BookBot Makefile
# Manages both backend and frontend development

PYTHON = python3
PIP = pip3
VENV_DIR = venv
FRONTEND_DIR = frontend
BACKEND_DIR = backend

.PHONY: help setup install-backend install-frontend build-frontend run-backend run-frontend dev test clean

help:
	@echo "BookBot Development Commands"
	@echo "============================"
	@echo "setup              - Initial project setup (create venv, install dependencies)"
	@echo "install-backend    - Install Python backend dependencies"
	@echo "install-frontend   - Install Node.js frontend dependencies"
	@echo "build-frontend     - Build the Vue.js frontend for production"
	@echo "run-backend        - Run the Flask backend server"
	@echo "run-frontend       - Run the Vue.js frontend dev server"
	@echo "dev                - Run both backend and frontend in development mode"
	@echo "test               - Run all tests"
	@echo "test-backend       - Run backend unit tests"
	@echo "clean              - Clean build artifacts and caches"

# Setup and Installation
setup: $(VENV_DIR)/bin/activate install-backend
	@echo "Setup complete! Run 'make run-backend' to start the server."

$(VENV_DIR)/bin/activate:
	$(PYTHON) -m venv $(VENV_DIR)
	$(VENV_DIR)/bin/pip install --upgrade pip

install-backend: $(VENV_DIR)/bin/activate
	$(VENV_DIR)/bin/pip install -r requirements.txt

install-frontend:
	@if [ -d "$(FRONTEND_DIR)" ]; then \
		cd $(FRONTEND_DIR) && npm install; \
	else \
		echo "Frontend directory not found. Run 'make setup-frontend' first."; \
	fi

# Frontend setup (for future use)
setup-frontend:
	@echo "Setting up Vue.js frontend..."
	@mkdir -p $(FRONTEND_DIR)
	@echo "Frontend directory created. Add Vue.js project files here."

build-frontend:
	@if [ -d "$(FRONTEND_DIR)" ]; then \
		cd $(FRONTEND_DIR) && npm run build; \
		mkdir -p $(FRONTEND_DIR)/dist; \
		echo "Frontend built successfully"; \
	else \
		echo "No frontend to build yet"; \
		mkdir -p $(FRONTEND_DIR)/dist; \
		echo '<h1>Frontend will be here</h1>' > $(FRONTEND_DIR)/dist/index.html; \
	fi

# Running the application
run-backend: $(VENV_DIR)/bin/activate
	@echo "Starting BookBot backend server..."
	$(VENV_DIR)/bin/python app.py

run-frontend:
	@if [ -d "$(FRONTEND_DIR)" ] && [ -f "$(FRONTEND_DIR)/package.json" ]; then \
		cd $(FRONTEND_DIR) && npm run dev; \
	else \
		echo "Frontend not set up yet. Backend serves a placeholder page."; \
	fi

dev:
	@echo "Starting development servers..."
	@echo "Backend will run on http://localhost:5000"
	@make run-backend &
	@make run-frontend

# Testing
test: test-backend test-frontend

test-backend: $(VENV_DIR)/bin/activate
	$(VENV_DIR)/bin/python -m pytest $(BACKEND_DIR)/tests/ -v

test-frontend:
	@if [ -d "$(FRONTEND_DIR)" ] && [ -f "$(FRONTEND_DIR)/package.json" ]; then \
		cd $(FRONTEND_DIR) && npm test; \
	else \
		echo "Frontend not set up yet. Skipping frontend tests."; \
	fi

# Database management
db-init: $(VENV_DIR)/bin/activate
	$(VENV_DIR)/bin/python -c "from app import create_app; from backend.models import db; app = create_app(); app.app_context().push(); db.create_all(); print('Database initialized')"

db-reset: $(VENV_DIR)/bin/activate
	@echo "Resetting database..."
	rm -f bookbot.db
	@make db-init

# Utilities
clean:
	rm -rf $(VENV_DIR)
	rm -rf __pycache__
	rm -rf $(BACKEND_DIR)/__pycache__
	rm -rf $(BACKEND_DIR)/*/__pycache__
	rm -rf *.pyc
	rm -rf $(BACKEND_DIR)/*.pyc
	rm -rf $(BACKEND_DIR)/*/*.pyc
	@if [ -d "$(FRONTEND_DIR)" ]; then \
		cd $(FRONTEND_DIR) && rm -rf node_modules dist; \
	fi

format:
	$(VENV_DIR)/bin/black $(BACKEND_DIR)/ app.py config.py

lint:
	$(VENV_DIR)/bin/flake8 $(BACKEND_DIR)/ app.py config.py

# Development helpers
demo-job: $(VENV_DIR)/bin/activate
	$(VENV_DIR)/bin/python -c "from app import create_app; from backend.jobs import create_job; app = create_app(); app.app_context().push(); job = create_job('test-book', 'demo', {}); print(f'Created demo job: {job.job_id}')"

check-status:
	@echo "Checking BookBot status..."
	@curl -s http://localhost:5000/api/health || echo "Backend not running"

# Installation with development tools
install-dev: install-backend
	$(VENV_DIR)/bin/pip install pytest black flake8 pytest-cov
