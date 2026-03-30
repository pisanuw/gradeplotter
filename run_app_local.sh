#!/bin/bash
# Run the gradeplotter v2 Flask app locally, killing any previous running versions

set -e

APP_SCRIPT="run_v2_app.py"
VENV_DIR=".venv"

# Kill any previous running versions of the app
PIDS=$(ps aux | grep "$APP_SCRIPT" | grep -v grep | awk '{print $2}')
if [ ! -z "$PIDS" ]; then
  echo "Killing previous gradeplotter app processes: $PIDS"
  kill $PIDS
fi

# Activate virtual environment
if [ -d "$VENV_DIR" ]; then
  source "$VENV_DIR/bin/activate"
else
  echo "Virtual environment not found. Please run setup instructions in README."
  exit 1
fi

# Run the app
python "$APP_SCRIPT"
