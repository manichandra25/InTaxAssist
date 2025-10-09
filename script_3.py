# Now copy all the backend files to the backend directory

# Create main.py
main_py_content = '''
from fastapi import FastAPI, File, UploadFile, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import List, Optional, Dict, Any
import uvicorn
from pydantic import BaseModel
import asyncio
import logging
from datetime import datetime

# Import our modules
from models import (
    TaxCalculationRequest, TaxCalculationResponse, 
    ChatbotRequest, ChatbotResponse, DocumentParseResponse,
    FinancialData, TaxRegimeComparison
)
from services.document_parser import DocumentParserService
from services.tax_calculator import TaxCalculatorService
from services.chatbot import ChatbotService
from config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Tax Filing Backend API",
    description="Comprehensive tax filing system with document parsing, tax calculation, and AI chatbot",
    version="1.0.0"
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
document_parser = DocumentParserService()
tax_calculator = TaxCalculatorService()
chatbot = ChatbotService()

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("Starting Tax Filing Backend API...")
    await document_parser.initialize()
    await chatbot.initialize()
    logger.info("Services initialized successfully")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down Tax Filing Backend API...")

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "Tax Filing Backend API",
        "version": "1.0.0",
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }

@app.post("/api/upload", response_model=DocumentParseResponse)
async def upload_and_parse_document(
    file: UploadFile = File(...),
    user_id: Optional[str] = None
):
    """
    Upload and parse financial documents
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
        
        # Parse document using LangChain
        parsed_data = await document_parser.parse_document(
            content, file.filename, file.content_type
        )
        
        logger.info(f"Successfully parsed {file.filename}")
        return parsed_data
        
    except Exception as e:
        logger.error(f"Error processing upload: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/calculate-tax", response_model=TaxCalculationResponse)
async def calculate_tax(request: TaxCalculationRequest):
    """
    Calculate tax liability for both old and new regimes
    Returns detailed breakdown and comparison
    """
    try:
        logger.info("Calculating tax for both regimes")
        
        # Calculate tax for both regimes
        result = tax_calculator.calculate_comprehensive_tax(
            financial_data=request.financial_data,
            assessment_year=request.assessment_year
        )
        
        logger.info("Tax calculation completed successfully")
        return result
        
    except Exception as e:
        logger.error(f"Error in tax calculation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chatbot", response_model=ChatbotResponse)
async def chatbot_query(request: ChatbotRequest):
    """
    Handle chatbot queries using LangChain RAG
    Provides contextual responses based on uploaded documents and tax knowledge
    """
    try:
        logger.info(f"Processing chatbot query: {request.message[:50]}...")
        
        # Process query with RAG
        response = await chatbot.process_query(
            query=request.message,
            context=request.context,
            user_id=request.user_id
        )
        
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
        slabs = tax_calculator.get_tax_slabs(regime, assessment_year)
        return {"regime": regime, "assessment_year": assessment_year, "slabs": slabs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/compare-regimes", response_model=TaxRegimeComparison)
async def compare_tax_regimes(request: TaxCalculationRequest):
    """
    Compare old vs new tax regime and provide recommendation
    """
    try:
        comparison = tax_calculator.compare_regimes(
            financial_data=request.financial_data,
            assessment_year=request.assessment_year
        )
        return comparison
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/tax-saving-suggestions")
async def get_tax_saving_suggestions(
    income: float,
    current_deductions: Dict[str, float],
    regime: str = "old"
):
    """
    Provide personalized tax saving suggestions
    """
    try:
        suggestions = tax_calculator.get_tax_saving_suggestions(
            income, current_deductions, regime
        )
        return {"suggestions": suggestions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
'''

# Copy all previously created files to the backend directory
backend_files = {
    "main.py": main_py_content,
}

# Copy the backend files
for filename, content in backend_files.items():
    with open(f"tax-filing-system/backend/{filename}", "w", encoding="utf-8") as f:
        f.write(content)

print("Created backend main.py")