# Copy all the backend files and create the complete project structure

import shutil
import os

# Copy all the previously created files to their proper locations

# Backend files to copy
backend_files = {
    "models.py": '''from pydantic import BaseModel, Field, validator
from typing import List, Dict, Optional, Any, Union
from datetime import datetime
from enum import Enum

class TaxRegime(str, Enum):
    OLD = "old"
    NEW = "new"

class FinancialData(BaseModel):
    """Financial data model for tax calculations"""
    
    # Income components
    basic_salary: float = Field(default=0, description="Basic salary amount")
    hra: float = Field(default=0, description="House Rent Allowance")
    special_allowance: float = Field(default=0, description="Special allowance")
    other_allowances: float = Field(default=0, description="Other allowances")
    bonus: float = Field(default=0, description="Bonus amount")
    
    # Other income
    interest_income: float = Field(default=0, description="Interest from savings/FD")
    rental_income: float = Field(default=0, description="Rental income")
    capital_gains: float = Field(default=0, description="Capital gains")
    other_income: float = Field(default=0, description="Other sources of income")
    
    # Deductions
    section_80c: float = Field(default=0, description="80C deductions (max 150000)")
    section_80d: float = Field(default=0, description="80D medical insurance")
    section_80g: float = Field(default=0, description="80G donations")
    section_24: float = Field(default=0, description="24 home loan interest")
    standard_deduction: float = Field(default=50000, description="Standard deduction")
    professional_tax: float = Field(default=0, description="Professional tax")
    
    # Additional deductions (old regime only)
    section_80ccd1b: float = Field(default=0, description="NPS additional 50k")
    section_80e: float = Field(default=0, description="Education loan interest")
    section_80tta: float = Field(default=0, description="Interest on savings account")
    
    # Tax paid
    tds_deducted: float = Field(default=0, description="TDS already deducted")
    advance_tax: float = Field(default=0, description="Advance tax paid")
    
    @validator('section_80c')
    def validate_80c(cls, v):
        return min(v, 150000)  # Max limit for 80C
    
    @validator('section_80d')
    def validate_80d(cls, v):
        return min(v, 25000)  # Max limit for 80D (individuals)
    
    @property
    def gross_salary(self) -> float:
        return (self.basic_salary + self.hra + self.special_allowance + 
                self.other_allowances + self.bonus)
    
    @property
    def total_income(self) -> float:
        return (self.gross_salary + self.interest_income + 
                self.rental_income + self.capital_gains + self.other_income)

class TaxCalculationRequest(BaseModel):
    """Request model for tax calculation"""
    financial_data: FinancialData
    assessment_year: str = Field(default="2024-25", description="Assessment Year")
    preferred_regime: Optional[TaxRegime] = None
    calculate_both: bool = Field(default=True, description="Calculate both regimes")

class TaxSlabDetail(BaseModel):
    """Individual tax slab detail"""
    min_amount: float
    max_amount: Optional[float]
    rate: float
    tax_amount: float
    
class RegimeTaxDetails(BaseModel):
    """Tax calculation details for a regime"""
    regime: TaxRegime
    gross_income: float
    taxable_income: float
    total_deductions: float
    tax_before_cess: float
    cess: float
    total_tax: float
    tax_slabs: List[TaxSlabDetail]
    effective_tax_rate: float
    
    # Additional fields
    tds_deducted: float = 0
    advance_tax: float = 0
    refund_or_payable: float = 0

class TaxCalculationResponse(BaseModel):
    """Response model for tax calculation"""
    old_regime: RegimeTaxDetails
    new_regime: RegimeTaxDetails
    recommended_regime: TaxRegime
    savings_amount: float
    calculation_date: datetime = Field(default_factory=datetime.now)

class TaxRegimeComparison(BaseModel):
    """Detailed comparison between tax regimes"""
    old_regime_tax: float
    new_regime_tax: float
    difference: float
    recommended: TaxRegime
    reason: str
    breakdown: Dict[str, Any]

class DocumentParseResponse(BaseModel):
    """Response model for document parsing"""
    success: bool
    filename: str
    extracted_data: FinancialData
    confidence_score: float = Field(description="Confidence in extraction accuracy")
    extracted_text: Optional[str] = None
    processing_time: float
    warnings: List[str] = []
    suggestions: List[str] = []

class ChatbotRequest(BaseModel):
    """Request model for chatbot queries"""
    message: str = Field(min_length=1, max_length=1000)
    context: Optional[Dict[str, Any]] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    financial_data: Optional[FinancialData] = None

class ChatbotResponse(BaseModel):
    """Response model for chatbot"""
    response: str
    confidence: float = Field(ge=0, le=1)
    sources: List[str] = []
    follow_up_questions: List[str] = []
    response_time: float
    
class TaxSavingSuggestion(BaseModel):
    """Tax saving suggestion model"""
    category: str
    description: str
    potential_savings: float
    implementation_difficulty: str  # Easy, Medium, Hard
    priority: int  # 1 (high) to 5 (low)
    details: str

class ErrorResponse(BaseModel):
    """Error response model"""
    error: bool = True
    message: str
    details: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)
''',

    "config.py": '''from pydantic import BaseSettings
from typing import List
import os

class Settings(BaseSettings):
    """Application settings"""
    
    # FastAPI settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True
    
    # API settings
    API_V1_STR: str = "/api"
    PROJECT_NAME: str = "Tax Filing Backend API"
    
    # OpenAI API settings (for LangChain)
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = "gpt-3.5-turbo"
    
    # Vector database settings
    VECTOR_DB_TYPE: str = "faiss"  # Options: faiss, chroma, pinecone
    VECTOR_DB_PATH: str = "./vector_db"
    
    # Document processing settings
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_FILE_TYPES: List[str] = [
        "application/pdf",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "image/jpeg",
        "image/png",
        "text/plain"
    ]
    
    # Tax calculation settings
    CURRENT_ASSESSMENT_YEAR: str = "2024-25"
    STANDARD_DEDUCTION: float = 50000
    
    # Chatbot settings
    CHATBOT_TEMPERATURE: float = 0.7
    MAX_CHAT_HISTORY: int = 10
    
    # Security settings
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # CORS settings
    ALLOWED_HOSTS: List[str] = ["*"]
    
    # Logging settings
    LOG_LEVEL: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Tax slab configurations
TAX_SLABS = {
    "2024-25": {
        "old": [
            {"min": 0, "max": 250000, "rate": 0},
            {"min": 250000, "max": 500000, "rate": 5},
            {"min": 500000, "max": 1000000, "rate": 20},
            {"min": 1000000, "max": None, "rate": 30}
        ],
        "new": [
            {"min": 0, "max": 300000, "rate": 0},
            {"min": 300000, "max": 600000, "rate": 5},
            {"min": 600000, "max": 900000, "rate": 10},
            {"min": 900000, "max": 1200000, "rate": 15},
            {"min": 1200000, "max": 1500000, "rate": 20},
            {"min": 1500000, "max": None, "rate": 30}
        ]
    }
}

# Deduction limits and configurations
DEDUCTION_LIMITS = {
    "section_80c": 150000,
    "section_80d": {
        "individual": 25000,
        "senior_citizen": 50000
    },
    "section_80ccd1b": 50000,
    "section_80tta": 10000,
    "standard_deduction": 50000
}

# Tax knowledge base for chatbot
TAX_KNOWLEDGE_BASE = [
    {
        "topic": "Tax Regimes",
        "content": """
        India has two tax regimes:
        1. Old Regime: Allows various deductions under sections 80C, 80D, etc.
        2. New Regime: Lower tax rates but limited deductions
        """
    },
    {
        "topic": "Section 80C",
        "content": """
        Section 80C allows deduction up to ₹1,50,000 for investments in:
        - EPF, PPF, NSC, ELSS, Life Insurance premiums, etc.
        """
    },
    {
        "topic": "HRA Calculation",
        "content": """
        HRA exemption is minimum of:
        1. Actual HRA received
        2. 50% of salary (metro) or 40% (non-metro)
        3. Rent paid minus 10% of salary
        """
    }
]

settings = Settings()
''',

    "requirements.txt": '''# FastAPI and web framework
fastapi==0.104.1
uvicorn[standard]==0.24.0
python-multipart==0.0.6
pydantic==2.5.0

# LangChain and AI/ML
langchain==0.0.350
openai==1.3.5
faiss-cpu==1.7.4
tiktoken==0.5.2

# Document processing
PyPDF2==3.0.1
python-docx==0.8.11
docx2txt==0.8
pytesseract==0.3.10  # For OCR (optional)
Pillow==10.1.0

# Database and storage (optional)
chromadb==0.4.18
pinecone-client==2.2.4

# Utilities
python-dotenv==1.0.0
aiofiles==23.2.1
httpx==0.25.2

# Development and testing
pytest==7.4.3
pytest-asyncio==0.21.1
black==23.11.0
flake8==6.1.0

# Logging and monitoring
structlog==23.2.0
''',

    ".env.template": '''# Environment Variables Template
# Copy this file to .env and fill in your actual values

# OpenAI API Configuration
OPENAI_API_KEY=your_openai_api_key_here

# FastAPI Configuration
HOST=0.0.0.0
PORT=8000
DEBUG=true

# Security
SECRET_KEY=your-secret-key-here-change-in-production

# Vector Database (Optional - for advanced RAG features)
# PINECONE_API_KEY=your_pinecone_api_key_here
# PINECONE_ENVIRONMENT=your_pinecone_environment

# Logging
LOG_LEVEL=INFO

# CORS Settings (configure for production)
ALLOWED_HOSTS=*
'''
}

# Create backend files
for filename, content in backend_files.items():
    with open(f"tax-filing-system/backend/{filename}", "w", encoding="utf-8") as f:
        f.write(content)

print("Created backend configuration files")