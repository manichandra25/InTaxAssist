# Create comprehensive README files and setup scripts

# Main project README
main_readme = '''# Interactive Tax Filing System

A comprehensive full-stack application for automated tax filing with document parsing, tax calculation, and AI-powered assistance.

## 🎯 Features

### Backend Features (FastAPI + LangChain)
- **Document Parsing**: Upload and parse financial documents (PDF, DOCX, images) using LangChain
- **Tax Calculation**: Calculate tax liability for both old and new regimes with detailed breakdowns
- **RAG Chatbot**: AI-powered chatbot for tax queries using LangChain and vector search
- **Regime Comparison**: Intelligent comparison and recommendations between tax regimes
- **Tax Optimization**: Personalized tax saving suggestions
- **API Documentation**: Automatic Swagger/OpenAPI documentation

### Frontend Features (Vanilla JS)
- **Interactive Dashboard**: Real-time tax calculation and visualization
- **File Upload**: Drag & drop document upload with parsing
- **Form Management**: Auto-filling forms from parsed documents
- **Charts & Analytics**: Interactive charts using Chart.js
- **Chatbot Interface**: Integrated AI assistant for tax help
- **Responsive Design**: Mobile-friendly responsive interface
- **Dark/Light Mode**: Theme toggle with system preference detection

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- Node.js (optional, for advanced frontend development)
- Docker & Docker Compose (for containerized deployment)

### Option 1: Docker Deployment (Recommended)

1. **Clone and Setup**
   ```bash
   git clone <repository-url>
   cd tax-filing-system
   ```

2. **Configure Environment**
   ```bash
   cp backend/.env.template backend/.env
   # Edit backend/.env and add your OpenAI API key
   ```

3. **Run with Docker Compose**
   ```bash
   docker-compose up --build
   ```

4. **Access Applications**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

### Option 2: Local Development

1. **Backend Setup**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\\Scripts\\activate
   pip install -r requirements.txt
   cp .env.template .env
   # Edit .env and add your OpenAI API key
   python main.py
   ```

2. **Frontend Setup**
   ```bash
   cd frontend
   # Serve with any local server
   python -m http.server 3000
   # Or use Node.js serve: npx serve -p 3000
   ```

## 📁 Project Structure

```
tax-filing-system/
├── backend/                    # FastAPI Backend
│   ├── services/              # Business logic services
│   │   ├── document_parser.py # LangChain document parsing
│   │   ├── tax_calculator.py  # Tax calculation engine
│   │   └── chatbot.py         # RAG chatbot service
│   ├── main.py               # FastAPI application
│   ├── models.py             # Pydantic models
│   ├── config.py             # Configuration & tax rules
│   ├── requirements.txt      # Python dependencies
│   └── .env.template         # Environment variables template
├── frontend/                  # Frontend Application
│   ├── index.html            # Main HTML file
│   ├── style.css             # Comprehensive styles
│   └── app.js                # JavaScript application
├── docker-compose.yml        # Docker orchestration
├── nginx.conf               # Nginx configuration
└── README.md                # This file
```

## 🔧 Configuration

### Backend Configuration

Edit `backend/.env`:

```env
# Required: OpenAI API Key for LangChain features
OPENAI_API_KEY=your_openai_api_key_here

# Optional: Server configuration
HOST=0.0.0.0
PORT=8000
DEBUG=true

# Optional: Security
SECRET_KEY=your-secret-key-here
```

### Tax Configuration

The system supports configurable tax rules in `backend/config.py`:

- **Tax Slabs**: Old and New regime slabs for different years
- **Deduction Limits**: Section-wise maximum deduction amounts
- **Knowledge Base**: Tax FAQ and guidance for chatbot

## 📚 API Documentation

### Key Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Health check |
| `/api/upload` | POST | Upload & parse documents |
| `/api/calculate-tax` | POST | Calculate tax for both regimes |
| `/api/compare-regimes` | POST | Compare old vs new regime |
| `/api/chatbot` | POST | AI chatbot queries |
| `/api/tax-slabs/{regime}` | GET | Get tax slab information |
| `/api/tax-saving-suggestions` | GET | Tax optimization tips |

### Interactive Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🤖 AI Features

### Document Parsing with LangChain
- Extracts financial data from various document formats
- Uses OpenAI GPT models for intelligent parsing
- Fallback to rule-based extraction when AI is unavailable
- Confidence scoring and extraction warnings

### RAG-Powered Chatbot
- Vector search through tax knowledge base
- Contextual responses based on user's financial data
- Follow-up question suggestions
- Conversation memory and context retention

## 💰 Tax Features

### Comprehensive Tax Calculation
- Support for both old and new tax regimes
- Progressive tax slab calculations with cess
- Detailed tax breakdowns and visualizations
- Effective tax rate calculations

### Tax Optimization
- Personalized tax saving suggestions
- Deduction maximization recommendations
- Regime comparison with savings analysis
- Investment planning guidance

## 🎨 Frontend Features

### Interactive Interface
- Real-time tax calculation previews
- Drag & drop document upload
- Auto-population from parsed documents
- Interactive charts and visualizations

### User Experience
- Responsive design for all devices
- Dark/light theme support
- Progress tracking and completion status
- Toast notifications and loading states

## 🧪 Testing

### Backend Tests
```bash
cd backend
pytest test_main.py -v
```

### Frontend Testing
- Manual testing through browser
- API integration testing
- Document upload testing

## 🚢 Deployment

### Production Deployment

1. **Environment Setup**
   ```bash
   # Set production environment variables
   export OPENAI_API_KEY=your_production_key
   export DEBUG=false
   export SECRET_KEY=your_secure_secret_key
   ```

2. **Docker Production**
   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```

3. **Manual Deployment**
   ```bash
   # Backend deployment with gunicorn
   cd backend
   gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker

   # Frontend deployment with nginx
   # Copy frontend files to nginx web root
   ```

## 🔒 Security Considerations

### Production Security
- Set strong SECRET_KEY in environment
- Use HTTPS in production
- Configure CORS properly for your domain
- Implement rate limiting
- Use environment-specific API keys
- Regular security updates

### Data Privacy
- Document processing is done locally/server-side
- No financial data stored permanently
- API keys secured through environment variables
- User sessions managed securely

## 🛠️ Development

### Adding New Features

1. **Backend Development**
   - Add new endpoints in `main.py`
   - Create service classes in `services/`
   - Update models in `models.py`
   - Add tests in `test_main.py`

2. **Frontend Development**
   - Add new components in `app.js`
   - Update styles in `style.css`
   - Add new sections in `index.html`

### Code Style
- Backend: Follow FastAPI and Python PEP 8 standards
- Frontend: ES6+ JavaScript with consistent formatting
- Use meaningful variable names and comments

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

For support and questions:
- Create an issue in the repository
- Check the API documentation at `/docs`
- Review the configuration guide above

## 🙏 Acknowledgments

- **FastAPI** - Modern, fast web framework for building APIs
- **LangChain** - Framework for developing applications with LLMs
- **Chart.js** - Simple yet flexible JavaScript charting library
- **OpenAI** - GPT models for document parsing and chatbot
- **Lucide Icons** - Beautiful & consistent icon pack

---

**Built for academic and educational purposes. Ensure compliance with local tax regulations when using for actual tax filing.**
'''

with open("tax-filing-system/README.md", "w", encoding="utf-8") as f:
    f.write(main_readme)

# Create setup scripts
setup_script_unix = '''#!/bin/bash

echo "🚀 Setting up Interactive Tax Filing System..."

# Check if Docker is installed
if command -v docker &> /dev/null; then
    echo "✅ Docker found"
else
    echo "❌ Docker not found. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if command -v docker-compose &> /dev/null; then
    echo "✅ Docker Compose found"
else
    echo "❌ Docker Compose not found. Please install Docker Compose first."
    exit 1
fi

# Create .env file if it doesn't exist
if [ ! -f "backend/.env" ]; then
    echo "📝 Creating environment file..."
    cp backend/.env.template backend/.env
    echo ""
    echo "⚠️  IMPORTANT: Edit backend/.env and add your OpenAI API key!"
    echo "   You can get an API key from: https://platform.openai.com/api-keys"
    echo ""
    read -p "Press Enter after you've updated the .env file..."
fi

# Create necessary directories
mkdir -p backend/vector_db
mkdir -p backend/logs

echo "🔧 Building and starting services..."
docker-compose up --build -d

echo ""
echo "✅ Setup complete!"
echo ""
echo "🌐 Access your applications:"
echo "   Frontend:        http://localhost:3000"
echo "   Backend API:     http://localhost:8000"
echo "   API Docs:        http://localhost:8000/docs"
echo ""
echo "📚 To view logs: docker-compose logs -f"
echo "🛑 To stop: docker-compose down"
echo ""
'''

with open("tax-filing-system/setup.sh", "w", encoding="utf-8") as f:
    f.write(setup_script_unix)

# Make script executable
import os
os.chmod("tax-filing-system/setup.sh", 0o755)

# Windows setup script
setup_script_windows = '''@echo off
echo 🚀 Setting up Interactive Tax Filing System...

REM Check if Docker is installed
docker --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo ❌ Docker not found. Please install Docker Desktop first.
    pause
    exit /b 1
)

echo ✅ Docker found

REM Check if Docker Compose is installed
docker-compose --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo ❌ Docker Compose not found. Please install Docker Compose first.
    pause
    exit /b 1
)

echo ✅ Docker Compose found

REM Create .env file if it doesn't exist
if not exist "backend\\.env" (
    echo 📝 Creating environment file...
    copy "backend\\.env.template" "backend\\.env"
    echo.
    echo ⚠️  IMPORTANT: Edit backend\\.env and add your OpenAI API key!
    echo    You can get an API key from: https://platform.openai.com/api-keys
    echo.
    pause
)

REM Create necessary directories
if not exist "backend\\vector_db" mkdir "backend\\vector_db"
if not exist "backend\\logs" mkdir "backend\\logs"

echo 🔧 Building and starting services...
docker-compose up --build -d

echo.
echo ✅ Setup complete!
echo.
echo 🌐 Access your applications:
echo    Frontend:        http://localhost:3000
echo    Backend API:     http://localhost:8000
echo    API Docs:        http://localhost:8000/docs
echo.
echo 📚 To view logs: docker-compose logs -f
echo 🛑 To stop: docker-compose down
echo.
pause
'''

with open("tax-filing-system/setup.bat", "w", encoding="utf-8") as f:
    f.write(setup_script_windows)

# Create .gitignore
gitignore_content = '''# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# Virtual Environment
venv/
env/
ENV/
env.bak/
venv.bak/

# Environment Variables
.env
.env.local
.env.production

# IDEs
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Logs
*.log
logs/

# Database
*.db
*.sqlite3

# Vector Database
vector_db/

# Node modules (if using Node.js tools)
node_modules/

# Docker
.docker/

# Temporary files
*.tmp
temp/
tmp/

# Test coverage
.coverage
htmlcov/
.pytest_cache/

# Production builds
dist/
build/
'''

with open("tax-filing-system/.gitignore", "w", encoding="utf-8") as f:
    f.write(gitignore_content)

print("Created comprehensive documentation and setup scripts")