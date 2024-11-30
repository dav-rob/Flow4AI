#!/bin/bash

# Get the absolute path to the virtual environment
VENV_PATH="$(pwd)/.venv"
VENV_BIN="$VENV_PATH/bin"

# Activate virtual environment and add it to PATH
source "$VENV_BIN/activate"
export PATH="$VENV_BIN:$PATH"

# Launch Windsurf with the updated environment
/Applications/Windsurf.app/Contents/Resources/app/bin/windsurf .
