import os
from typing import List, Dict, Any
from pydantic import BaseSettings

class Settings(BaseSettings):
    """Application settings with Groq integration"""

    # FastAPI settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True

    # API settings
    API_V1_STR: str = "/api"
    PROJECT_NAME: str = "Tax Filing System with Groq AI"
    VERSION: str = "1.0.0"

    # Groq API settings (Primary AI provider)
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama2-70b-4096")
    # Available Groq models: llama2-70b-4096, mixtral-8x7b-32768, gemma-7b-it
    MAX_TOKENS: int = int(os.getenv("MAX_TOKENS", "1024"))

    # # Fallback OpenAI settings (optional, for compatibility)
    # OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    # OPENAI_MODEL: str = "gpt-3.5-turbo"

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
    CESS_RATE: float = 0.04  # 4% Health and Education Cess

    # Chatbot settings
    CHATBOT_TEMPERATURE: float = 0.7
    MAX_CHAT_HISTORY: int = 10

    # Security settings
    SECRET_KEY: str = os.getenv("SECRET_KEY", "tax-filing-system-secret-key-change-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # CORS settings
    ALLOWED_HOSTS: List[str] = ["*"]  # Configure properly for production

    # Logging settings
    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = ".env"
        case_sensitive = True

# Tax slab configurations for different assessment years
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
    },
    "2023-24": {
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
        "senior_citizen": 50000,
        "super_senior_citizen": 50000
    },
    "section_80ccd1b": 50000,  # Additional NPS deduction
    "section_80tta": 10000,    # Interest on savings account
    "section_80e": None,       # Education loan interest (no limit)
    "section_80g": None,       # Donations (varies by organization)
    "standard_deduction": 50000,
    "professional_tax": 2500,
    "hra_metro_rate": 0.50,    # 50% for metro cities
    "hra_non_metro_rate": 0.40  # 40% for non-metro cities
}

# Enhanced tax knowledge base for Groq-powered chatbot
TAX_KNOWLEDGE_BASE = [
    {
        "topic": "Tax Regimes Overview",
        "content": """
        India offers two tax regime options for individual taxpayers:

        OLD REGIME:
        - Higher tax rates with extensive deduction options
        - Allows deductions under sections 80C (₹1.5L), 80D (₹25K), 24, etc.
        - Suitable for individuals with significant eligible investments/expenses
        - Standard deduction: ₹50,000

        NEW REGIME:
        - Lower tax rates with limited deduction options
        - Only standard deduction and employer NPS contribution allowed
        - Simpler tax structure, fewer documentation requirements
        - Better for individuals with minimal deductible investments

        Choice Strategy: Compare both regimes annually as salaried individuals can switch each year.
        """
    },
    {
        "topic": "Section 80C Investments",
        "content": """
        Section 80C allows tax deduction up to ₹1,50,000 for specified investments:

        INVESTMENT OPTIONS:
        - Employee Provident Fund (EPF): Automatic deduction from salary
        - Public Provident Fund (PPF): 15-year lock-in, tax-free returns
        - Equity Linked Savings Scheme (ELSS): 3-year lock-in, market-linked
        - National Savings Certificate (NSC): 5-year fixed income
        - Life Insurance Premiums: Up to 10% of sum assured
        - Principal repayment of home loan
        - Tax Saving Fixed Deposits: 5-year lock-in
        - Unit Linked Insurance Plans (ULIPs)
        - Sukanya Samriddhi Scheme: For girl child education

        STRATEGY: Diversify across instruments based on risk appetite and liquidity needs.
        """
    },
    {
        "topic": "Section 80D Health Insurance",
        "content": """
        Section 80D provides deduction for health insurance premiums:

        DEDUCTION LIMITS:
        - Self, spouse, children (below 60): Up to ₹25,000
        - Self, spouse, children (senior citizen): Up to ₹50,000
        - Parents (below 60): Additional ₹25,000
        - Parents (senior citizen): Additional ₹50,000
        - Preventive health check-ups: Additional ₹5,000

        ELIGIBLE PREMIUMS:
        - Medical insurance premiums for family
        - Contribution to Central Government Health Scheme
        - Mediclaim policies from general insurance companies

        NOTE: Preventive health check-ups are sub-limit within the main limits.
        """
    },
    {
        "topic": "HRA Calculation Rules",
        "content": """
        House Rent Allowance (HRA) exemption calculation:

        EXEMPTION = MINIMUM OF:
        1. Actual HRA received from employer
        2. 50% of basic salary (metro cities: Mumbai, Delhi, Kolkata, Chennai)
           40% of basic salary (non-metro cities)
        3. Rent paid minus 10% of basic salary

        REQUIRED DOCUMENTS:
        - Rent receipts for amounts paid
        - Rental agreement copy
        - Landlord's PAN card (if annual rent > ₹1,00,000)
        - Property tax receipts (if any)

        METRO CITIES: Mumbai, Delhi, Kolkata, Chennai qualify for 50% rate.
        All other cities get 40% of basic salary consideration.
        """
    },
    {
        "topic": "Section 24 Home Loan Benefits",
        "content": """
        Section 24 allows deduction for home loan interest:

        DEDUCTION LIMITS:
        - Self-occupied property: Up to ₹2,00,000 per year
        - Let-out property: No limit (full interest amount)
        - Pre-construction period: Interest spread over 5 years post completion

        ELIGIBLE LOANS:
        - Home purchase loan
        - Home construction loan
        - Home improvement/renovation loan

        REQUIRED DOCUMENTS:
        - Home loan interest certificate from bank
        - Property registration documents
        - Possession certificate (for new properties)

        ADDITIONAL BENEFIT: Principal repayment qualifies for 80C deduction.
        """
    },
    {
        "topic": "National Pension System (NPS)",
        "content": """
        NPS offers multiple tax deduction opportunities:

        SECTION 80CCD(1): Employee contribution
        - Up to 10% of salary for salaried individuals
        - Up to 20% of gross income for self-employed
        - Included within ₹1.5 lakh limit of Section 80C

        SECTION 80CCD(1B): Additional deduction
        - Up to ₹50,000 over and above 80C limit
        - Available for voluntary NPS contributions
        - Total tax benefit can reach ₹2 lakh (80C + 80CCD1B)

        SECTION 80CCD(2): Employer contribution
        - Up to 10% of salary (14% for government employees)
        - No limit for tax deduction
        - Not counted in employee's taxable income

        WITHDRAWAL: 60% lump sum tax-free at retirement, 40% must be annuitized.
        """
    },
    {
        "topic": "ITR Filing Requirements",
        "content": """
        Income Tax Return filing guidelines:

        FILING DEADLINES:
        - Individuals/HUFs (non-audit): July 31st
        - Audit cases: September 30th
        - Revised return: December 31st of assessment year

        ITR FORM SELECTION:
        - ITR-1 (Sahaj): Salary income up to ₹50 lakh, one house property
        - ITR-2: Capital gains, multiple properties, foreign income
        - ITR-3: Business/professional income
        - ITR-4 (Sugam): Presumptive business income

        MANDATORY DOCUMENTS:
        - Form 16 from employer
        - Bank account statements
        - Investment proofs (80C, 80D, etc.)
        - Property tax receipts
        - Capital gains statements
        - Interest certificates

        LATE FILING PENALTY:
        - ₹5,000 (income > ₹5 lakh)
        - ₹1,000 (income ≤ ₹5 lakh)
        """
    },
    {
        "topic": "TDS on Salary",
        "content": """
        Tax Deducted at Source (TDS) on salary mechanism:

        CALCULATION BASIS:
        - Projected annual salary income
        - Declared investments and deductions
        - Chosen tax regime (old/new)
        - Previous employer's TDS (if job changed)

        EMPLOYEE RESPONSIBILITIES:
        - Submit Form 12BB with investment declarations
        - Provide proof of investments by January
        - Inform about other income sources
        - Submit Form 12B for previous employer details

        EMPLOYER OBLIGATIONS:
        - Deduct TDS based on projected liability
        - Issue Form 16 annually
        - Deposit TDS to government account
        - Provide quarterly TDS certificates

        OPTIMIZATION: Regular monitoring and proof submission helps minimize excess TDS deduction.
        """
    },
    {
        "topic": "Groq AI Integration",
        "content": """
        This tax assistant leverages Groq's advanced AI infrastructure:

        GROQ ADVANTAGES:
        - Ultra-fast inference (10-100x faster than traditional GPU)
        - High accuracy with Llama 2 70B parameter model
        - Cost-effective processing for complex tax queries
        - Real-time document parsing and analysis

        LLAMA MODEL CAPABILITIES:
        - Understanding complex Indian tax scenarios
        - Processing multiple deduction combinations
        - Contextual regime recommendations
        - Personalized tax planning advice

        RAG IMPLEMENTATION:
        - Vector search through comprehensive tax knowledge base
        - Document context integration
        - Conversation memory for follow-up questions
        - Source attribution for transparency

        FEATURES POWERED BY GROQ:
        - Intelligent document parsing
        - Contextual chatbot responses
        - Tax optimization suggestions
        - Regime comparison analysis
        """
    }
]

# Create settings instance
settings = Settings()

# Tax calculation helper functions
def get_tax_slabs(regime: str, assessment_year: str = "2024-25") -> List[Dict]:
    """Get tax slabs for specified regime and year"""
    return TAX_SLABS.get(assessment_year, TAX_SLABS["2024-25"]).get(regime, [])

def get_deduction_limit(section: str, category: str = "individual") -> float:
    """Get deduction limit for specified section"""
    limit = DEDUCTION_LIMITS.get(section)
    if isinstance(limit, dict):
        return limit.get(category, 0)
    return limit or 0

def is_metro_city(city: str) -> bool:
    """Check if city qualifies for metro HRA rate"""
    metro_cities = ["mumbai", "delhi", "kolkata", "chennai", "bangalore", "hyderabad", "pune"]
    return city.lower() in metro_cities

# Validation helpers
def validate_assessment_year(year: str) -> bool:
    """Validate assessment year format"""
    import re
    pattern = r"^20\d{2}-\d{2}$"
    return bool(re.match(pattern, year))

def validate_financial_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate and clean financial data"""
    cleaned_data = {}
    for key, value in data.items():
        if isinstance(value, (int, float)) and value >= 0:
            cleaned_data[key] = float(value)
        else:
            cleaned_data[key] = 0.0
    return cleaned_data

# Export commonly used items
__all__ = [
    "settings",
    "TAX_SLABS", 
    "DEDUCTION_LIMITS",
    "TAX_KNOWLEDGE_BASE",
    "get_tax_slabs",
    "get_deduction_limit",
    "is_metro_city",
    "validate_assessment_year",
    "validate_financial_data"
]
