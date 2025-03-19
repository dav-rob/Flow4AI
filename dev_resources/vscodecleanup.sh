#!/bin/bash

# VSCode Cache Cleanup Script for Intel Mac
# ----------------------------------------

echo "🧹 VSCode Cache Cleanup Script for macOS 🧹"
echo "==========================================="


# Check if VSCode is running and warn user
if pgrep -x "Code" > /dev/null; then
    echo "⚠️  WARNING: VSCode appears to be running."
    echo "Please close VSCode before continuing."
    read -p "Continue anyway? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Exiting script. Please close VSCode and try again."
        exit 1
    fi
fi

# ... rest of your cleanup script ...

echo "Creating backup directory..."
BACKUP_DIR=~/vscode_cache_backup_$(date +%Y%m%d_%H%M%S)
mkdir -p "$BACKUP_DIR"
echo "Backup directory created at: $BACKUP_DIR"

# Function to safely clear a directory
clear_directory() {
    local dir="$1"
    local name="$2"
    
    if [ -d "$dir" ]; then
        echo "Backing up $name..."
        cp -R "$dir" "$BACKUP_DIR/" 2>/dev/null
        
        echo "Clearing $name..."
        rm -rf "$dir"/* 2>/dev/null
        echo "✅ $name cleared successfully."
    else
        echo "⚠️ $name directory not found at $dir"
    fi
}

# Main cleanup process
echo -e "\n🔍 Starting cleanup process...\n"

# 1. Workspace Storage
WORKSPACE_STORAGE="$HOME/Library/Application Support/Code/User/workspaceStorage"
clear_directory "$WORKSPACE_STORAGE" "Workspace Storage"

# 2. Python Extension Global Storage
PYTHON_STORAGE="$HOME/Library/Application Support/Code/User/globalStorage/ms-python.python"
clear_directory "$PYTHON_STORAGE" "Python Extension Storage"

# 3. Pylance Extension Storage
PYLANCE_STORAGE="$HOME/Library/Application Support/Code/User/globalStorage/ms-python.vscode-pylance"
clear_directory "$PYLANCE_STORAGE" "Pylance Extension Storage"

# 4. Extension Host Storage
EXTHOST_STORAGE="$HOME/Library/Application Support/Code/exthost Crash Reports"
clear_directory "$EXTHOST_STORAGE" "Extension Host Crash Reports"

# 5. Code Cache
CODE_CACHE="$HOME/Library/Application Support/Code/CachedData"
clear_directory "$CODE_CACHE" "Code Cache"

# 6. Code Storage (more cautious, just clear logs)
CODE_STORAGE="$HOME/Library/Application Support/Code/logs"
clear_directory "$CODE_STORAGE" "Code Logs"

# Check for VSCodium as well
if [ -d "$HOME/Library/Application Support/VSCodium" ]; then
    echo -e "\n🔍 VSCodium detected, cleaning its caches as well...\n"
    
    WORKSPACE_STORAGE="$HOME/Library/Application Support/VSCodium/User/workspaceStorage"
    clear_directory "$WORKSPACE_STORAGE" "VSCodium Workspace Storage"
    
    PYTHON_STORAGE="$HOME/Library/Application Support/VSCodium/User/globalStorage/ms-python.python"
    clear_directory "$PYTHON_STORAGE" "VSCodium Python Extension Storage"
    
    PYLANCE_STORAGE="$HOME/Library/Application Support/VSCodium/User/globalStorage/ms-python.vscode-pylance"
    clear_directory "$PYLANCE_STORAGE" "VSCodium Pylance Extension Storage"
    
    CODE_CACHE="$HOME/Library/Application Support/VSCodium/CachedData"
    clear_directory "$CODE_CACHE" "VSCodium Cache"
    
    CODE_STORAGE="$HOME/Library/Application Support/VSCodium/logs"
    clear_directory "$CODE_STORAGE" "VSCodium Logs"
fi

echo -e "\n🎉 Cache cleanup completed successfully!"
echo "A backup of your cache has been saved to: $BACKUP_DIR"
echo "If you experience any issues, you can restore from this backup."
echo -e "\n📋 Next steps:"
echo "1. Restart your Mac (recommended)"
echo "2. Open VSCode and let the extensions reinstall/reconfigure"
echo "3. Verify your Python virtual environment is correctly set up"
echo -e "\nHappy coding! 🚀\n"
