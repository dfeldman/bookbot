#!/bin/bash

# BookBot Development Server Script
# This script kills any running instanceecho -e "${GREEN}   Frontend starting on http://localhost:3004${NC}" and starts both frontend and backend

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 BookBot Development Server${NC}"
echo "=================================="

# Function to kill processes by name
kill_processes() {
    local process_name=$1
    local pids=$(pgrep -f "$process_name" 2>/dev/null || true)
    
    if [ -n "$pids" ]; then
        echo -e "${YELLOW}🔄 Stopping existing $process_name processes...${NC}"
        echo "$pids" | xargs kill -TERM 2>/dev/null || true
        sleep 2
        
        # Force kill if still running
        local remaining_pids=$(pgrep -f "$process_name" 2>/dev/null || true)
        if [ -n "$remaining_pids" ]; then
            echo -e "${YELLOW}⚡ Force killing remaining $process_name processes...${NC}"
            echo "$remaining_pids" | xargs kill -KILL 2>/dev/null || true
        fi
    fi
}

# Kill existing processes
echo -e "${YELLOW}🧹 Cleaning up existing processes...${NC}"

# Kill Vite/Node processes (frontend)
kill_processes "vite"
kill_processes "node.*vite"

# Kill Flask/Python processes (backend)
kill_processes "python.*app.py"
kill_processes "flask"
kill_processes "python.*backend"

# Wait a moment for cleanup
sleep 1

# Check if we're in the right directory
if [ ! -f "app.py" ] || [ ! -d "frontend" ]; then
    echo -e "${RED}❌ Error: Please run this script from the bookbot3 root directory${NC}"
    echo "Expected files: app.py, frontend/"
    exit 1
fi

# Start backend
echo -e "${GREEN}🐍 Starting Flask backend...${NC}"
cd "$(dirname "$0")"  # Ensure we're in the script directory

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}📦 Creating virtual environment...${NC}"
    python3 -m venv venv
fi

# Activate virtual environment and start backend
source venv/bin/activate
pip install -q -r requirements.txt

echo -e "${GREEN}   Backend starting on http://localhost:5001${NC}"
python app.py &
BACKEND_PID=$!

# Give backend time to start
sleep 3

# Start frontend
echo -e "${GREEN}🎨 Starting Vite frontend...${NC}"
cd frontend

# Install dependencies if node_modules doesn't exist
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}📦 Installing frontend dependencies...${NC}"
    npm install
fi

echo -e "${GREEN}   Frontend starting on http://localhost:3004${NC}"
npm run dev &
FRONTEND_PID=$!

# Return to root directory
cd ..

# Function to cleanup on exit
cleanup() {
    echo -e "\n${YELLOW}🛑 Shutting down servers...${NC}"
    
    if [ -n "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null || true
    fi
    
    if [ -n "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null || true
    fi
    
    # Kill any remaining processes
    kill_processes "vite"
    kill_processes "python.*app.py"
    
    echo -e "${GREEN}✅ Cleanup complete${NC}"
    exit 0
}

# Set up trap to cleanup on script exit
trap cleanup SIGINT SIGTERM EXIT

# Wait a moment for servers to start
sleep 5

# Check if servers are running
echo -e "\n${BLUE}🔍 Server Status Check${NC}"
echo "------------------------"

# Check backend
if curl -s http://localhost:5001/api/config >/dev/null 2>&1; then
    echo -e "${GREEN}✅ Backend: Running on http://localhost:5001${NC}"
else
    echo -e "${RED}❌ Backend: Not responding${NC}"
fi

# Check frontend
if curl -s http://localhost:3004 >/dev/null 2>&1; then
    echo -e "${GREEN}✅ Frontend: Running on http://localhost:3004${NC}"
else
    echo -e "${YELLOW}⏳ Frontend: Still starting up...${NC}"
fi

echo -e "\n${GREEN}🎉 Development servers are running!${NC}"
echo "=================================="
echo -e "📱 Frontend: ${BLUE}http://localhost:3004${NC}"
echo -e "🔧 Backend:  ${BLUE}http://localhost:5001${NC}"
echo -e "📚 API Docs: ${BLUE}http://localhost:5001/api${NC}"
echo ""
echo -e "${YELLOW}💡 Tip: Press Ctrl+C to stop both servers${NC}"
echo ""

# Keep script running and display logs
echo -e "${BLUE}📝 Server Logs (Ctrl+C to stop):${NC}"
echo "=================================="

# Wait for processes to finish or be interrupted
wait
