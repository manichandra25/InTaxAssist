from dotenv import load_dotenv
load_dotenv()
from fastapi import FastAPI, File, UploadFile, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import List, Optional, Dict, Any
import uvicorn
from pydantic import BaseModel
import asyncio
import logging
from datetime import datetime
from contextlib import asynccontextmanager
# Import our modules
try:
    from .models import (
        TaxCalculationRequest, TaxCalculationResponse, 
        ChatbotRequest, ChatbotResponse, DocumentParseResponse,
        FinancialData, TaxRegimeComparison
    )
    from .services.document_parser import DocumentParserService
    from .services.tax_calculator import TaxCalculatorService
    from .services.chatbot import ChatbotService
    from .config import settings
except ImportError as e:
    print(f"Import error: {e}")
    print("Using fallback imports")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize and cleanup services using lifespan context"""
    logger.info("Starting Tax Filing Backend API...")
    # print(services_available)
    if services_available:
        print("--- EXECUTING LIFESPAN STARTUP ---")
        try:
            await document_parser.initialize()
            await chatbot.initialize()
            logger.info("Services initialized successfully")
        except Exception as e:
            logger.error(f"Service initialization error: {e}")

    logger.info("API is ready!")

    # Everything after yield runs on shutdown
    yield

    logger.info("Shutting down Tax Filing Backend API...")

app = FastAPI(
    title="Tax Filing Backend API",
    description="Comprehensive tax filing system with document parsing, tax calculation, and AI chatbot powered by Groq",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
try:
    document_parser = DocumentParserService()
    tax_calculator = TaxCalculatorService()
    chatbot = ChatbotService()
    services_available = True
except Exception as e:
    logger.warning(f"Services initialization failed: {e}")
    services_available = False

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "Tax Filing Backend API with Groq Integration",
        "version": "1.0.0",
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "features": [
            "Document parsing with AI (Groq + Llama)",
            "Tax calculation for both regimes",
            "RAG-powered chatbot",
            "Comprehensive tax planning"
        ]
    }

@app.get("/api/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "services": {
            "document_parser": services_available,
            "tax_calculator": services_available,
            "chatbot": services_available
        },
        "timestamp": datetime.now().isoformat()
    }

@app.post("/api/upload")
async def upload_and_parse_document(
    file: UploadFile = File(...),
    user_id: Optional[str] = None
):
    """
    Upload and parse financial documents using Groq AI
    Supports PDF, DOCX, images, and text files
    """
    try:
        logger.info(f"Processing upload: {file.filename}")

        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")

        allowed_types = [
            "application/pdf",
            "application/msword", 
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "image/jpeg",
            "image/png",
            "text/plain"
        ]

        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported file type: {file.content_type}"
            )

        # Read file content
        content = await file.read()

        if services_available:
            # Parse document using Groq
            parsed_data = await document_parser.parse_document(
                content, file.filename, file.content_type
            )
        else:
            # Fallback response
            from .models import FinancialData, DocumentParseResponse
            parsed_data = DocumentParseResponse(
                success=True,
                filename=file.filename,
                extracted_data=FinancialData(),
                confidence_score=0.5,
                processing_time=0.1,
                warnings=["Service not available - using demo mode"],
                suggestions=["Upload your Groq API key to enable AI parsing"]
            )

        logger.info(f"Successfully processed {file.filename}")
        return parsed_data

    except Exception as e:
        logger.error(f"Error processing upload: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/calculate-tax")
async def calculate_tax(request: Dict[str, Any]):
    """
    Calculate tax liability for both old and new regimes
    Returns detailed breakdown and comparison
    """
    try:
        logger.info("Calculating tax for both regimes")

        financial_data = request.get("financial_data", {})
        assessment_year = request.get("assessment_year", "2024-25")

        if services_available:
            from .models import FinancialData
            fin_data = FinancialData(**financial_data)
            result = tax_calculator.calculate_comprehensive_tax(
                financial_data=fin_data,
                assessment_year=assessment_year
            )
        else:
            # Mock calculation for demo
            result = {
                "old_regime": {
                    "total_tax": 95000,
                    "effective_tax_rate": 15.8,
                    "refund_or_payable": 50000
                },
                "new_regime": {
                    "total_tax": 87000,
                    "effective_tax_rate": 14.5,
                    "refund_or_payable": 42000
                },
                "recommended_regime": "new",
                "savings_amount": 8000
            }

        logger.info("Tax calculation completed successfully")
        return result

    except Exception as e:
        logger.error(f"Error in tax calculation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chatbot")
async def chatbot_query(request: Dict[str, Any]):
    """
    Handle chatbot queries using Groq with LangChain RAG
    Provides contextual responses based on tax knowledge
    """
    try:
        message = request.get("message", "")
        user_id = request.get("user_id")
        context = request.get("context")

        logger.info(f"Processing chatbot query: {message[:50]}...")

        if services_available:
            response = await chatbot.process_query(
                query=message,
                context=context,
                user_id=user_id
            )
        else:
            # Fallback response
            response = {
                "response": f"I understand you're asking: '{message}'. I'm powered by Groq's Llama model for fast tax assistance. Please add your Groq API key to enable full functionality.",
                "confidence": 0.7,
                "sources": ["Fallback Response"],
                "follow_up_questions": [
                    "How do I set up Groq API key?",
                    "What tax documents do I need?",
                    "Should I use old or new regime?"
                ],
                "response_time": 0.1
            }

        logger.info("Chatbot response generated successfully")
        return response

    except Exception as e:
        logger.error(f"Error in chatbot processing: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/tax-slabs/{regime}")
async def get_tax_slabs(regime: str, assessment_year: str = "2024-25"):
    """
    Get tax slab information for specified regime
    """
    try:
        if regime == "old":
            slabs = [
                {"min": 0, "max": 250000, "rate": 0},
                {"min": 250000, "max": 500000, "rate": 5},
                {"min": 500000, "max": 1000000, "rate": 20},
                {"min": 1000000, "max": None, "rate": 30}
            ]
        else:  # new regime
            slabs = [
                {"min": 0, "max": 300000, "rate": 0},
                {"min": 300000, "max": 600000, "rate": 5},
                {"min": 600000, "max": 900000, "rate": 10},
                {"min": 900000, "max": 1200000, "rate": 15},
                {"min": 1200000, "max": 1500000, "rate": 20},
                {"min": 1500000, "max": None, "rate": 30}
            ]

        return {
            "regime": regime, 
            "assessment_year": assessment_year, 
            "slabs": slabs
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/compare-regimes")
async def compare_tax_regimes(request: Dict[str, Any]):
    """
    Compare old vs new tax regime and provide recommendation
    """
    try:
        financial_data = request.get("financial_data", {})

        # Mock comparison for demo
        comparison = {
            "old_regime_tax": 95000,
            "new_regime_tax": 87000,
            "difference": 8000,
            "recommended": "new",
            "reason": "New regime saves ₹8,000 due to lower tax rates",
            "breakdown": {
                "old_regime": {
                    "gross_income": 1000000,
                    "total_deductions": 200000,
                    "taxable_income": 800000,
                    "tax_liability": 95000,
                    "effective_rate": 15.8
                },
                "new_regime": {
                    "gross_income": 1000000,
                    "total_deductions": 50000,
                    "taxable_income": 950000,
                    "tax_liability": 87000,
                    "effective_rate": 14.5
                }
            }
        }

        return comparison
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/tax-saving-suggestions")
async def get_tax_saving_suggestions(
    income: float = 1000000,
    regime: str = "old"
):
    """
    Provide personalized tax saving suggestions
    """
    try:
        suggestions = [
            {
                "category": "Section 80C Investment",
                "description": "Maximize your 80C deductions with PPF, ELSS, or NSC",
                "potential_savings": 46800,
                "implementation_difficulty": "Easy",
                "priority": 1,
                "details": "Invest ₹1.5 lakh in tax-saving instruments"
            },
            {
                "category": "Health Insurance (80D)",
                "description": "Get comprehensive health insurance for tax benefits",
                "potential_savings": 7500,
                "implementation_difficulty": "Easy",
                "priority": 2,
                "details": "Health insurance premiums up to ₹25,000 qualify for deduction"
            },
            {
                "category": "NPS Investment (80CCD1B)",
                "description": "Additional ₹50,000 deduction through NPS",
                "potential_savings": 15000,
                "implementation_difficulty": "Medium",
                "priority": 3,
                "details": "Invest in NPS for retirement planning with tax benefits"
            }
        ]

        return {"suggestions": suggestions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": True, "message": exc.detail, "timestamp": datetime.now().isoformat()}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"error": True, "message": "Internal server error", "timestamp": datetime.now().isoformat()}
    )

if __name__ == "__main__":
    import uvicorn

    # Get settings
    HOST = "0.0.0.0"
    PORT = 8000
    DEBUG = True

    print("🚀 Starting Tax Filing System Backend...")
    print(f"🌐 Server will run at: http://{HOST}:{PORT}")
    print("📖 API Documentation: http://localhost:8000/docs")
    print("🤖 Powered by Groq + Llama for AI features")

    uvicorn.run(
        "main:app",
        host=HOST,
        port=PORT,
        reload=DEBUG
    )
