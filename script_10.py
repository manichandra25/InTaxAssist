# Create additional backend files and project documentation

# Create Dockerfile
dockerfile_content = '''FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    gcc \\
    g++ \\
    curl \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better Docker layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create directory for vector database
RUN mkdir -p vector_db

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \\
    CMD curl -f http://localhost:8000/ || exit 1

# Run the application
CMD ["python", "main.py"]
'''

with open("tax-filing-system/backend/Dockerfile", "w", encoding="utf-8") as f:
    f.write(dockerfile_content)

# Create docker-compose.yml
docker_compose_content = '''version: '3.8'

services:
  tax-backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - HOST=0.0.0.0
      - PORT=8000
      - DEBUG=true
    env_file:
      - ./backend/.env
    volumes:
      - ./backend/vector_db:/app/vector_db
      - ./backend/logs:/app/logs
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/"]
      interval: 30s
      timeout: 10s
      retries: 3

  tax-frontend:
    image: nginx:alpine
    ports:
      - "3000:80"
    volumes:
      - ./frontend:/usr/share/nginx/html
      - ./nginx.conf:/etc/nginx/conf.d/default.conf
    depends_on:
      - tax-backend
    restart: unless-stopped

  # Optional: Add Redis for caching
  # redis:
  #   image: redis:7-alpine
  #   ports:
  #     - "6379:6379"
  #   restart: unless-stopped
'''

with open("tax-filing-system/docker-compose.yml", "w", encoding="utf-8") as f:
    f.write(docker_compose_content)

# Create nginx.conf for frontend
nginx_conf = '''server {
    listen 80;
    server_name localhost;
    
    root /usr/share/nginx/html;
    index index.html;

    # Enable gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;

    # Serve static files
    location / {
        try_files $uri $uri/ /index.html;
        
        # Cache static assets
        location ~* \\.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
            expires 1y;
            add_header Cache-Control "public, no-transform";
        }
    }

    # Proxy API requests to backend
    location /api/ {
        proxy_pass http://tax-backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Enable CORS for development
    location /api {
        if ($request_method = OPTIONS) {
            add_header Access-Control-Allow-Origin *;
            add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS";
            add_header Access-Control-Allow-Headers "Authorization, Content-Type";
            add_header Content-Length 0;
            add_header Content-Type text/plain;
            return 200;
        }
    }
}
'''

with open("tax-filing-system/nginx.conf", "w", encoding="utf-8") as f:
    f.write(nginx_conf)

# Create test files
test_content = '''import pytest
import asyncio
from fastapi.testclient import TestClient
from backend.main import app
from backend.models import FinancialData, TaxCalculationRequest

# Test client
client = TestClient(app)

def test_health_check():
    """Test the health check endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    assert "Tax Filing Backend API" in response.json()["message"]

def test_tax_calculation():
    """Test tax calculation endpoint"""
    financial_data = {
        "basic_salary": 600000,
        "hra": 240000,
        "section_80c": 150000,
        "section_80d": 25000,
        "tds_deducted": 45000
    }
    
    request_data = {
        "financial_data": financial_data,
        "assessment_year": "2024-25"
    }
    
    response = client.post("/api/calculate-tax", json=request_data)
    assert response.status_code == 200
    
    result = response.json()
    assert "old_regime" in result
    assert "new_regime" in result
    assert "recommended_regime" in result

def test_tax_slabs():
    """Test tax slabs endpoint"""
    response = client.get("/api/tax-slabs/old?assessment_year=2024-25")
    assert response.status_code == 200
    
    result = response.json()
    assert result["regime"] == "old"
    assert "slabs" in result

def test_regime_comparison():
    """Test regime comparison endpoint"""
    financial_data = {
        "basic_salary": 800000,
        "section_80c": 100000,
        "section_80d": 20000
    }
    
    request_data = {
        "financial_data": financial_data,
        "assessment_year": "2024-25"
    }
    
    response = client.post("/api/compare-regimes", json=request_data)
    assert response.status_code == 200
    
    result = response.json()
    assert "old_regime_tax" in result
    assert "new_regime_tax" in result
    assert "recommended" in result

def test_chatbot_endpoint():
    """Test chatbot endpoint"""
    request_data = {
        "message": "What is Section 80C?",
        "user_id": "test_user"
    }
    
    response = client.post("/api/chatbot", json=request_data)
    assert response.status_code == 200
    
    result = response.json()
    assert "response" in result
    assert "confidence" in result
    assert len(result["response"]) > 0

@pytest.mark.asyncio
async def test_financial_data_validation():
    """Test FinancialData model validation"""
    # Test valid data
    data = FinancialData(
        basic_salary=500000,
        section_80c=160000  # Over limit
    )
    
    # Should clamp 80C to maximum limit
    assert data.section_80c == 150000
    
    # Test property calculations
    assert data.gross_salary == 500000
    assert data.total_income == 500000

if __name__ == "__main__":
    pytest.main([__file__])
'''

with open("tax-filing-system/backend/test_main.py", "w", encoding="utf-8") as f:
    f.write(test_content)

print("Created additional project files (Dockerfile, docker-compose, nginx, tests)")