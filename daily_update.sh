#!/bin/bash

# Daily GitHub Update Script
# Runs every day to update the repository

echo "🔄 Starting daily GitHub update at $(date)"

# Navigate to project directory
cd /root/.openclaw/workspace/propaganda-pipeline

# Pull latest changes
echo "📥 Pulling latest changes..."
git pull origin main

# Check if there are any changes
if git diff --quiet; then
    echo "✅ Repository is up to date"
else
    echo "📝 Changes detected, committing..."
    
    # Add all changes
    git add .
    
    # Commit with timestamp
    git commit -m "Daily update - $(date '+%Y-%m-%d %H:%M:%S')"
    
    # Push changes
    echo "📤 Pushing changes to GitHub..."
    git push origin main
    
    echo "✅ Daily update completed successfully"
fi

echo "✨ Daily update completed at $(date)"
echo "----------------------------------------"