@echo off
echo 🚀 Setting up Tax Filing System with Groq Integration...

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is required but not installed.
    pause
    exit /b 1
)

REM Setup backend
echo 📦 Setting up backend...
cd backend

REM Copy environment template
if not exist .env (
    copy .env.template .env
    echo 📝 Environment file created. Please edit backend\.env and add your Groq API key.
)

REM Create virtual environment
python -m venv venv
call venv\Scripts\activate

REM Install dependencies
python -m pip install --upgrade pip
pip install -r requirements.txt

echo ✅ Backend setup complete!
echo.
echo 🔑 IMPORTANT: Add your Groq API key to backend\.env
echo    Get your free API key from: https://console.groq.com/
echo    Edit backend\.env and add: GROQ_API_KEY=your_actual_key_here
echo.
echo 🚀 To start the system:
echo    1. Backend: cd backend ^&^& python main.py
echo    2. Frontend: Open frontend\index.html in your browser
echo.
echo 🌐 Access points:
echo    Frontend: http://localhost:3000 (if using live server)
echo    Backend: http://localhost:8000
echo    API Docs: http://localhost:8000/docs
echo.
echo 🎉 Setup complete! Your AI-powered tax system is ready!
pause
