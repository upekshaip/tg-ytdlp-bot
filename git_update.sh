#!/bin/bash

# Git Update Script for tg-ytdlp-NEW project
# This script performs git add, commit, and force push to newdesign branch

echo "🚀 Starting git update process..."

# Get current directory
CURRENT_DIR=$(pwd)
echo "📍 Current directory: $CURRENT_DIR"

# Check if we're in a git repository
if [ ! -d ".git" ]; then
    echo "❌ Error: Not a git repository. Please run this script from the project root directory."
    exit 1
fi

# Check git status
echo "📊 Checking git status..."
git status --porcelain

# Check if there are any changes to commit
if [ -z "$(git status --porcelain)" ]; then
    echo "ℹ️  No changes to commit. Repository is clean."
    exit 0
fi

# Remove any files that should be ignored but are still tracked
echo "🧹 Cleaning up ignored files..."
if [ -f "update.sh" ]; then
    git rm --cached "update.sh" 2>/dev/null || true
fi
if [ -d "_cursor" ]; then
    git rm --cached -r "_cursor" 2>/dev/null || true
fi
if [ -d "TXT" ]; then
    git rm --cached -r "TXT" 2>/dev/null || true
fi

# Add all changes
echo "➕ Adding all changes..."
git add .

# Check if add was successful
if [ $? -ne 0 ]; then
    echo "❌ Error: Failed to add changes to git"
    exit 1
fi

# Commit changes
echo "💾 Committing changes..."
git commit -m "update code"

# Check if commit was successful
if [ $? -ne 0 ]; then
    echo "❌ Error: Failed to commit changes"
    exit 1
fi

# Force push to newdesign branch
echo "🚀 Force pushing to newdesign branch..."
git push origin newdesign --force

# Check if push was successful
if [ $? -ne 0 ]; then
    echo "❌ Error: Failed to push to newdesign branch"
    exit 1
fi

echo "✅ Git update completed successfully!"
echo "📅 Last commit: $(git log -1 --format='%H - %s (%cr)')"
