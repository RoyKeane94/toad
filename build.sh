#!/bin/bash
set -e

echo "🚀 Starting build process..."

# Check if npm is available
if command -v npm &> /dev/null; then
    echo "📦 Installing npm dependencies..."
    npm install
    
    echo "🔨 Building CSS and JavaScript..."
    npm run build:all
    
    echo "📁 Collecting static files..."
    python manage.py collectstatic --noinput
else
    echo "⚠️  npm not available, skipping asset build"
    echo "📁 Collecting static files without build..."
    python manage.py collectstatic --noinput
fi

echo "✅ Build complete!" 