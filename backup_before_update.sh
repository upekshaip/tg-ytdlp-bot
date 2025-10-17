#!/bin/bash

# Backup script before updating
# Run this before UPDATE.sh to create a full backup

echo "🔄 Creating backup before update..."
echo "=================================="

# Create backup directory with timestamp
BACKUP_DIR="_backup_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

echo "📁 Creating backup in: $BACKUP_DIR"

# Backup important files
echo "📋 Backing up configuration files..."
cp -r CONFIG/ "$BACKUP_DIR/" 2>/dev/null || echo "⚠️ CONFIG/ not found"

echo "📋 Backing up helper files..."
cp -r HELPERS/ "$BACKUP_DIR/" 2>/dev/null || echo "⚠️ HELPERS/ not found"

echo "📋 Backing up command files..."
cp -r COMMANDS/ "$BACKUP_DIR/" 2>/dev/null || echo "⚠️ COMMANDS/ not found"

echo "📋 Backing up main files..."
cp magic.py "$BACKUP_DIR/" 2>/dev/null || echo "⚠️ magic.py not found"
cp requirements.txt "$BACKUP_DIR/" 2>/dev/null || echo "⚠️ requirements.txt not found"

echo "📋 Backing up logs..."
cp *.log "$BACKUP_DIR/" 2>/dev/null || echo "⚠️ No log files found"

echo "✅ Backup completed: $BACKUP_DIR"
echo "🔄 You can now run UPDATE.sh safely"
