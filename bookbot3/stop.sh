#!/bin/bash

# BookBot Stop Script
# Stops all running BookBot development servers

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}🛑 Stopping BookBot Development Servers${NC}"
echo "========================================"

# Function to kill processes by name
kill_processes() {
    local process_name=$1
    local pids=$(pgrep -f "$process_name" 2>/dev/null || true)
    
    if [ -n "$pids" ]; then
        echo -e "${YELLOW}🔄 Stopping $process_name processes...${NC}"
        echo "$pids" | xargs kill -TERM 2>/dev/null || true
        sleep 2
        
        # Force kill if still running
        local remaining_pids=$(pgrep -f "$process_name" 2>/dev/null || true)
        if [ -n "$remaining_pids" ]; then
            echo -e "${YELLOW}⚡ Force killing remaining $process_name processes...${NC}"
            echo "$remaining_pids" | xargs kill -KILL 2>/dev/null || true
        fi
        echo -e "${GREEN}✅ Stopped $process_name${NC}"
    else
        echo -e "${GREEN}✅ No $process_name processes running${NC}"
    fi
}

# Stop frontend (Vite/Node)
kill_processes "vite"
kill_processes "node.*vite"

# Stop backend (Flask/Python)
kill_processes "python.*app.py"
kill_processes "flask"
kill_processes "python.*backend"

echo -e "\n${GREEN}🎉 All BookBot servers stopped!${NC}"
