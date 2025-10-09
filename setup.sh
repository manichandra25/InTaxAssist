#!/bin/bash

# Tax Filing System Setup Script
echo "🚀 Setting up Tax Filing System with Groq Integration..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed."
    exit 1
fi

# Setup backend
echo "📦 Setting up backend..."
cd backend

# Copy environment template
if [ ! -f .env ]; then
    cp .env.template .env
    echo "📝 Environment file created. Please edit backend/.env and add your Groq API key."
fi

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

echo "✅ Backend setup complete!"
echo ""
echo "🔑 IMPORTANT: Add your Groq API key to backend/.env"
echo "   Get your free API key from: https://console.groq.com/"
echo "   Edit backend/.env and add: GROQ_API_KEY=your_actual_key_here"
echo ""
echo "🚀 To start the system:"
echo "   1. Backend: cd backend && python main.py"
echo "   2. Frontend: Open frontend/index.html in your browser"
echo ""
echo "🌐 Access points:"
echo "   Frontend: http://localhost:3000 (if using live server)"
echo "   Backend: http://localhost:8000"
echo "   API Docs: http://localhost:8000/docs"
echo ""
echo "🎉 Setup complete! Your AI-powered tax system is ready!"
