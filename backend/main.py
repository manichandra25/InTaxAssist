from dotenv import load_dotenv
load_dotenv()
from fastapi import FastAPI, File, UploadFile, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from typing import List, Optional, Dict, Any
import uvicorn
from pydantic import BaseModel
import asyncio
import logging
from datetime import datetime
from contextlib import asynccontextmanager
import io
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
from reportlab.lib.units import inch
from reportlab.lib import colors
import json
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

@app.post("/api/test-tax-calculation")
async def test_tax_calculation():
    """
    Test endpoint to verify tax calculation with known values
    Uses fixed test data to debug calculation logic
    """
    try:
        logger.info("Running test tax calculation with known values")
        
        from .models import FinancialData
        
        # Test case 1: Simple income of ₹1,000,000
        test_financial_data = FinancialData(
            basic_salary=1000000,
            hra=0,
            special_allowance=0,
            other_allowances=0,
            bonus=0,
            interest_income=0,
            rental_income=0,
            capital_gains=0,
            other_income=0,
            section_80c=100000,
            section_80d=0,
            section_80g=0,
            section_24=0,
            section_80ccd1b=0,
            section_80e=0,
            section_80tta=0,
            standard_deduction=50000,
            professional_tax=0,
            tds_deducted=0,
            advance_tax=0
        )
        
        result = tax_calculator.calculate_comprehensive_tax(
            financial_data=test_financial_data,
            assessment_year="2024-25"
        )
        
        logger.info("TEST RESULT:")
        logger.info(f"Total Income: ₹{test_financial_data.total_income:,.0f}")
        logger.info(f"Old Regime Tax: ₹{result.old_regime.total_tax:,.0f}")
        logger.info(f"New Regime Tax: ₹{result.new_regime.total_tax:,.0f}")
        logger.info(f"Recommended: {result.recommended_regime}")
        
        return {
            "test_case": "Simple Income ₹1,000,000",
            "gross_income": test_financial_data.total_income,
            "deductions": 150000,
            "result": {
                "old_regime": {
                    "total_tax": result.old_regime.total_tax,
                    "taxable_income": result.old_regime.taxable_income,
                    "effective_rate": result.old_regime.effective_tax_rate
                },
                "new_regime": {
                    "total_tax": result.new_regime.total_tax,
                    "taxable_income": result.new_regime.taxable_income,
                    "effective_rate": result.new_regime.effective_tax_rate
                }
            }
        }
        
    except Exception as e:
        logger.error(f"Test calculation error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/calculate-tax")
async def calculate_tax(request: Dict[str, Any]):
    """
    Calculate tax liability for both old and new regimes
    Returns detailed breakdown and comparison
    """
    try:
        logger.info("=" * 60)
        logger.info("DEBUGGING TAX CALCULATION")
        logger.info("=" * 60)
        
        logger.info(f"DEBUG: Received request: {request}")

        financial_data = request.get("financial_data", {})
        assessment_year = request.get("assessment_year", "2024-25")
        
        logger.info(f"DEBUG: Financial data keys: {list(financial_data.keys())}")
        logger.info(f"DEBUG: Financial data values:")
        for key, value in financial_data.items():
            logger.info(f"  {key}: {value}")

        if services_available:
            from .models import FinancialData
            fin_data = FinancialData(**financial_data)
            
            logger.info(f"DEBUG: FinancialData object created successfully")
            logger.info(f"DEBUG: gross_salary: {fin_data.gross_salary}")
            logger.info(f"DEBUG: total_income: {fin_data.total_income}")
            logger.info(f"DEBUG: Assessment year: {assessment_year}")
            
            result = tax_calculator.calculate_comprehensive_tax(
                financial_data=fin_data,
                assessment_year=assessment_year
            )
            
            logger.info(f"DEBUG: Old regime result:")
            logger.info(f"  gross_income: {result.old_regime.gross_income}")
            logger.info(f"  total_deductions: {result.old_regime.total_deductions}")
            logger.info(f"  taxable_income: {result.old_regime.taxable_income}")
            logger.info(f"  tax_before_cess: {result.old_regime.tax_before_cess}")
            logger.info(f"  cess: {result.old_regime.cess}")
            logger.info(f"  total_tax: {result.old_regime.total_tax}")
            
            logger.info(f"DEBUG: New regime result:")
            logger.info(f"  gross_income: {result.new_regime.gross_income}")
            logger.info(f"  total_deductions: {result.new_regime.total_deductions}")
            logger.info(f"  taxable_income: {result.new_regime.taxable_income}")
            logger.info(f"  tax_before_cess: {result.new_regime.tax_before_cess}")
            logger.info(f"  cess: {result.new_regime.cess}")
            logger.info(f"  total_tax: {result.new_regime.total_tax}")
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
        logger.info("=" * 60)
        return result

    except Exception as e:
        logger.error(f"Error in tax calculation: {str(e)}", exc_info=True)
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

@app.post("/api/export-tax-summary")
async def export_tax_summary(request: Dict[str, Any]):
    """
    Export tax summary in ITR-compatible format
    Supports JSON, PDF, CSV, and Excel formats
    """
    try:
        export_format = request.get("format", "json").lower()  # json, pdf, csv, excel, xlsx
        financial_data = request.get("financial_data", {})
        tax_calculation = request.get("tax_calculation", {})
        user_info = request.get("user_info", {})
        assessment_year = request.get("assessment_year", "2024-25")

        # Generate ITR summary
        summary = generate_itr_summary(financial_data, tax_calculation, user_info, assessment_year)

        if export_format == "pdf":
            pdf_bytes = generate_itr_pdf(summary)
            return StreamingResponse(
                iter([pdf_bytes]),
                media_type="application/pdf",
                headers={"Content-Disposition": f"attachment; filename=ITR_Summary_{assessment_year}.pdf"}
            )
        elif export_format == "csv":
            csv_data = generate_itr_csv(summary)
            return StreamingResponse(
                iter([csv_data.encode('utf-8')]),
                media_type="text/csv",
                headers={"Content-Disposition": f"attachment; filename=ITR_Summary_{assessment_year}.csv"}
            )
        elif export_format in ["excel", "xlsx"]:
            excel_bytes = generate_itr_excel(summary, assessment_year)
            return StreamingResponse(
                iter([excel_bytes]),
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={"Content-Disposition": f"attachment; filename=ITR_Summary_{assessment_year}.xlsx"}
            )
        else:  # JSON format
            return summary

    except Exception as e:
        logger.error(f"Error generating export: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Export error: {str(e)}")

def generate_itr_summary(financial_data: Dict[str, Any], tax_calculation: Dict[str, Any], 
                         user_info: Dict[str, Any], assessment_year: str) -> Dict[str, Any]:
    """
    Generate ITR-format summary for tax filing
    """
    # Extract recommended regime data
    recommended_regime = tax_calculation.get("recommended_regime", "new")
    regime_data = tax_calculation.get(f"{recommended_regime}_regime", {})

    summary = {
        "itr_filing_summary": {
            "filing_type": "ITR-2" if regime_data.get("gross_income", 0) > 5000000 else "ITR-1",
            "assessment_year": assessment_year,
            "financial_year": f"{int(assessment_year[:4])-1}-{assessment_year[:4]}",
            "filing_date": datetime.now().isoformat(),
            "status": "DRAFT"
        },
        "personal_details": {
            "name": user_info.get("name", "[Taxpayer Name]"),
            "pan": user_info.get("pan", "[PAN]"),
            "aadhar": user_info.get("aadhar", "[Aadhar No.]"),
            "dob": user_info.get("dob", "[Date of Birth]"),
            "address": user_info.get("address", "[Address]"),
            "status": user_info.get("status", "Individual"),
            "residential_status": user_info.get("residential_status", "Resident"),
            "email": user_info.get("email", "[Email]"),
            "mobile": user_info.get("mobile", "[Mobile]")
        },
        "income_details": {
            "gross_salary": financial_data.get("basic_salary", 0) + 
                           financial_data.get("hra", 0) + 
                           financial_data.get("special_allowance", 0) + 
                           financial_data.get("other_allowances", 0) + 
                           financial_data.get("bonus", 0),
            "hra_received": financial_data.get("hra", 0),
            "special_allowance": financial_data.get("special_allowance", 0),
            "interest_income": financial_data.get("interest_income", 0),
            "rental_income": financial_data.get("rental_income", 0),
            "capital_gains": financial_data.get("capital_gains", 0),
            "other_income": financial_data.get("other_income", 0),
            "total_income_before_deductions": regime_data.get("gross_income", 0)
        },
        "deductions_and_exemptions": {
            "section_80c": financial_data.get("section_80c", 0) if recommended_regime == "old" else 0,
            "section_80d": financial_data.get("section_80d", 0) if recommended_regime == "old" else 0,
            "section_80e": financial_data.get("section_80e", 0) if recommended_regime == "old" else 0,
            "section_80g": financial_data.get("section_80g", 0) if recommended_regime == "old" else 0,
            "section_24": financial_data.get("section_24", 0) if recommended_regime == "old" else 0,
            "section_80ccd1b": financial_data.get("section_80ccd1b", 0) if recommended_regime == "old" else 0,
            "section_80tta": financial_data.get("section_80tta", 0) if recommended_regime == "old" else 0,
            "standard_deduction": financial_data.get("standard_deduction", 50000),
            "professional_tax": financial_data.get("professional_tax", 0),
            "total_deductions": regime_data.get("total_deductions", 0)
        },
        "tax_calculation": {
            "regime_selected": recommended_regime.upper(),
            "gross_total_income": regime_data.get("gross_income", 0),
            "total_deductions_claimed": regime_data.get("total_deductions", 0),
            "taxable_income": regime_data.get("taxable_income", 0),
            "tax_before_cess": regime_data.get("tax_before_cess", 0),
            "cess_4_percent": regime_data.get("cess", 0),
            "total_tax_liability": regime_data.get("total_tax", 0),
            "effective_tax_rate_percent": regime_data.get("effective_tax_rate", 0)
        },
        "tax_payment_and_refund": {
            "tds_deducted": tax_calculation.get("tds_deducted", financial_data.get("tds_deducted", 0)),
            "advance_tax_paid": financial_data.get("advance_tax", 0),
            "total_tax_paid": financial_data.get("tds_deducted", 0) + financial_data.get("advance_tax", 0),
            "total_tax_liability": regime_data.get("total_tax", 0),
            "refund_or_payable": regime_data.get("refund_or_payable", 0),
            "status": "REFUND" if regime_data.get("refund_or_payable", 0) < 0 else "PAYABLE"
        },
        "regime_comparison": {
            "old_regime_tax": tax_calculation.get("old_regime", {}).get("total_tax", 0),
            "new_regime_tax": tax_calculation.get("new_regime", {}).get("total_tax", 0),
            "recommended_regime": recommended_regime.upper(),
            "annual_savings": tax_calculation.get("savings_amount", 0),
            "reason": f"New regime provides lower tax at effective rate of {tax_calculation.get('new_regime', {}).get('effective_tax_rate', 0):.2f}%"
        },
        "verification_and_filing": {
            "verification_mode": "ELECTRONIC",
            "digital_signature": "[Digital Signature]",
            "filing_status": "READY_TO_FILE",
            "last_modified": datetime.now().isoformat(),
            "notes": "This is a draft ITR summary. Please review all details before official filing."
        }
    }

    return summary

def generate_itr_pdf(summary: Dict[str, Any]) -> bytes:
    """
    Generate ITR summary as PDF document
    """
    from datetime import datetime
    
    def format_date(date_str):
        """Format date string to readable format"""
        try:
            if isinstance(date_str, str):
                if 'T' in date_str:  # ISO format
                    return date_str.split('T')[0]
                return date_str[:10] if len(date_str) >= 10 else date_str
            return 'N/A'
        except:
            return 'N/A'
    
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=0.5*inch, leftMargin=0.5*inch,
                           topMargin=0.75*inch, bottomMargin=0.75*inch)
    
    story = []
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        textColor=colors.HexColor('#217F8D'),
        spaceAfter=12,
        alignment=1  # Center
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=12,
        textColor=colors.HexColor('#217F8D'),
        spaceAfter=8,
        spaceBefore=8,
        borderBottom=True
    )
    
    # Title
    filing_info = summary.get("itr_filing_summary", {})
    story.append(Paragraph(f"Income Tax Return ({filing_info.get('itr_filing_summary', 'ITR')}) Summary", title_style))
    story.append(Spacer(1, 0.2*inch))
    
    # Filing details with proper date formatting
    story.append(Paragraph("Assessment Year: " + filing_info.get('assessment_year', 'N/A'), styles['Normal']))
    story.append(Paragraph("Financial Year: " + filing_info.get('financial_year', 'N/A'), styles['Normal']))
    filing_date = format_date(filing_info.get('filing_date', 'N/A'))
    story.append(Paragraph("Filing Date: " + filing_date, styles['Normal']))
    story.append(Spacer(1, 0.2*inch))
    
    # Personal Details
    story.append(Paragraph("1. PERSONAL DETAILS", heading_style))
    personal = summary.get("personal_details", {})
    personal_data = [
        ["Name", personal.get("name", "N/A")],
        ["PAN", personal.get("pan", "N/A")],
        ["Aadhar", personal.get("aadhar", "N/A")],
        ["Residential Status", personal.get("residential_status", "N/A")],
        ["Email", personal.get("email", "N/A")],
        ["Mobile", personal.get("mobile", "N/A")]
    ]
    
    personal_table = Table(personal_data, colWidths=[1.5*inch, 4*inch])
    personal_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#E8F4F7')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey)
    ]))
    story.append(personal_table)
    story.append(Spacer(1, 0.2*inch))
    
    # Income Details
    story.append(Paragraph("2. INCOME DETAILS", heading_style))
    income = summary.get("income_details", {})
    income_data = [
        ["Description", "Amount (₹)"],
        ["Gross Salary", f"₹{income.get('gross_salary', 0):,.0f}"],
        ["HRA Received", f"₹{income.get('hra_received', 0):,.0f}"],
        ["Interest Income", f"₹{income.get('interest_income', 0):,.0f}"],
        ["Rental Income", f"₹{income.get('rental_income', 0):,.0f}"],
        ["Capital Gains", f"₹{income.get('capital_gains', 0):,.0f}"],
        ["Other Income", f"₹{income.get('other_income', 0):,.0f}"],
        ["Total Income", f"₹{income.get('total_income_before_deductions', 0):,.0f}"]
    ]
    
    income_table = Table(income_data, colWidths=[2.5*inch, 3*inch])
    income_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#217F8D')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey)
    ]))
    story.append(income_table)
    story.append(Spacer(1, 0.2*inch))
    
    # Deductions
    story.append(Paragraph("3. DEDUCTIONS & EXEMPTIONS", heading_style))
    deductions = summary.get("deductions_and_exemptions", {})
    deductions_data = [
        ["Description", "Amount (₹)"],
        ["Section 80C", f"₹{deductions.get('section_80c', 0):,.0f}"],
        ["Section 80D (Health Insurance)", f"₹{deductions.get('section_80d', 0):,.0f}"],
        ["Section 24 (Home Loan Interest)", f"₹{deductions.get('section_24', 0):,.0f}"],
        ["Standard Deduction", f"₹{deductions.get('standard_deduction', 0):,.0f}"],
        ["Professional Tax", f"₹{deductions.get('professional_tax', 0):,.0f}"],
        ["Total Deductions", f"₹{deductions.get('total_deductions', 0):,.0f}"]
    ]
    
    deductions_table = Table(deductions_data, colWidths=[3*inch, 2.5*inch])
    deductions_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#32B8C6')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey)
    ]))
    story.append(deductions_table)
    story.append(Spacer(1, 0.2*inch))
    
    # Tax Calculation
    story.append(Paragraph("4. TAX CALCULATION", heading_style))
    tax_calc = summary.get("tax_calculation", {})
    tax_data = [
        ["Description", "Amount (₹)"],
        ["Gross Total Income", f"₹{tax_calc.get('gross_total_income', 0):,.0f}"],
        ["Total Deductions", f"₹{tax_calc.get('total_deductions_claimed', 0):,.0f}"],
        ["Taxable Income", f"₹{tax_calc.get('taxable_income', 0):,.0f}"],
        ["Tax Before Cess", f"₹{tax_calc.get('tax_before_cess', 0):,.0f}"],
        ["Cess (4%)", f"₹{tax_calc.get('cess_4_percent', 0):,.0f}"],
        ["Total Tax Liability", f"₹{tax_calc.get('total_tax_liability', 0):,.0f}"],
        ["Effective Tax Rate", f"{tax_calc.get('effective_tax_rate_percent', 0):.2f}%"]
    ]
    
    tax_table = Table(tax_data, colWidths=[3*inch, 2.5*inch])
    tax_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#D4573B')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey)
    ]))
    story.append(tax_table)
    story.append(Spacer(1, 0.2*inch))
    
    # TDS and Refund
    story.append(Paragraph("5. TAX PAYMENT & REFUND STATUS", heading_style))
    payment = summary.get("tax_payment_and_refund", {})
    payment_data = [
        ["Description", "Amount (₹)"],
        ["TDS Deducted", f"₹{payment.get('tds_deducted', 0):,.0f}"],
        ["Advance Tax Paid", f"₹{payment.get('advance_tax_paid', 0):,.0f}"],
        ["Total Tax Paid", f"₹{payment.get('total_tax_paid', 0):,.0f}"],
        ["Total Tax Liability", f"₹{payment.get('total_tax_liability', 0):,.0f}"],
        ["Refund/Payable", f"₹{abs(payment.get('refund_or_payable', 0)):,.0f} ({payment.get('status', 'N/A')})"],
    ]
    
    payment_table = Table(payment_data, colWidths=[3*inch, 2.5*inch])
    payment_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#217F8D')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey)
    ]))
    story.append(payment_table)
    story.append(Spacer(1, 0.2*inch))
    
    # Regime Recommendation
    story.append(Paragraph("6. REGIME ANALYSIS & RECOMMENDATION", heading_style))
    regime = summary.get("regime_comparison", {})
    recommendation_text = f"""
    <b>Recommended Regime:</b> {regime.get('recommended_regime', 'N/A')}<br/>
    <b>Old Regime Tax:</b> ₹{regime.get('old_regime_tax', 0):,.0f}<br/>
    <b>New Regime Tax:</b> ₹{regime.get('new_regime_tax', 0):,.0f}<br/>
    <b>Annual Savings:</b> ₹{regime.get('annual_savings', 0):,.0f}<br/>
    <b>Reason:</b> {regime.get('reason', 'N/A')}
    """
    story.append(Paragraph(recommendation_text, styles['Normal']))
    story.append(Spacer(1, 0.2*inch))
    
    # Disclaimer
    story.append(PageBreak())
    story.append(Paragraph("DISCLAIMER & IMPORTANT NOTES", heading_style))
    disclaimer = """
    This is a <b>DRAFT</b> ITR summary generated by InTaxAssist for planning purposes only. <br/><br/>
    <b>Important:</b><br/>
    • This document should be reviewed by a qualified Chartered Accountant before filing<br/>
    • Ensure all financial data entered is accurate and verified<br/>
    • PAN, Aadhar, and personal details must be correct before official filing<br/>
    • TDS and Advance Tax figures must match with actual bank records and Form 16<br/>
    • Deductions claimed should be supported by proper documentation<br/>
    • Filing can be done on Income Tax Department's e-filing portal (www.incometax.gov.in)<br/>
    • The assessment year mentioned is the year for which the return is being filed<br/>
    • Keep supporting documents for at least 6 years as per Income Tax Act<br/>
    <br/>
    <b>Generated on:</b> {datetime.now().strftime('%d-%b-%Y %H:%M:%S')}<br/>
    <b>System:</b> InTaxAssist - Smart Tax Filing and Advisory System
    """
    story.append(Paragraph(disclaimer, styles['Normal']))
    story.append(Spacer(1, 0.2*inch))
    story.append(Paragraph("For any assistance, contact your tax advisor or CA.", styles['Normal']))
    
    # Build PDF
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()

def generate_itr_csv(summary: Dict[str, Any]) -> str:
    """
    Generate ITR summary as CSV format for import to tax filing portals
    """
    def format_value(value, key_name=""):
        """Format value safely for CSV, handling non-numeric types"""
        if value is None:
            return "N/A"
        if isinstance(value, (int, float)):
            if 'percent' in key_name.lower() or 'rate' in key_name.lower():
                return f"{value:.2f}%"
            else:
                return f"{value:,.0f}"
        if isinstance(value, bool):
            return "Yes" if value else "No"
        return str(value)
    
    csv_content = "ITR Summary Export - InTaxAssist\n\n"
    
    # Filing Information
    csv_content += "FILING INFORMATION\n"
    filing = summary.get("itr_filing_summary", {})
    csv_content += f"Filing Type,Assessment Year,Financial Year,Status\n"
    csv_content += f"{filing.get('filing_type', 'ITR-1')},{filing.get('assessment_year', 'N/A')},{filing.get('financial_year', 'N/A')},{filing.get('status', 'DRAFT')}\n\n"
    
    # Personal Details
    csv_content += "PERSONAL DETAILS\n"
    csv_content += "Field,Value\n"
    personal = summary.get("personal_details", {})
    for key, value in personal.items():
        csv_content += f"{key.replace('_', ' ').title()},{format_value(value)}\n"
    csv_content += "\n"
    
    # Income Details
    csv_content += "INCOME DETAILS\n"
    csv_content += "Description,Amount\n"
    income = summary.get("income_details", {})
    for key, value in income.items():
        csv_content += f"{key.replace('_', ' ').title()},{format_value(value, key)}\n"
    csv_content += "\n"
    
    # Deductions
    csv_content += "DEDUCTIONS & EXEMPTIONS\n"
    csv_content += "Description,Amount\n"
    deductions = summary.get("deductions_and_exemptions", {})
    for key, value in deductions.items():
        csv_content += f"{key.replace('_', ' ').title()},{format_value(value, key)}\n"
    csv_content += "\n"
    
    # Tax Calculation
    csv_content += "TAX CALCULATION\n"
    csv_content += "Description,Amount\n"
    tax_calc = summary.get("tax_calculation", {})
    for key, value in tax_calc.items():
        csv_content += f"{key.replace('_', ' ').title()},{format_value(value, key)}\n"
    csv_content += "\n"
    
    # Tax Payment & Refund
    csv_content += "TAX PAYMENT & REFUND\n"
    csv_content += "Description,Amount\n"
    payment = summary.get("tax_payment_and_refund", {})
    for key, value in payment.items():
        csv_content += f"{key.replace('_', ' ').title()},{format_value(value, key)}\n"
    csv_content += "\n"
    
    # Regime Comparison
    csv_content += "REGIME COMPARISON\n"
    csv_content += "Description,Value\n"
    regime = summary.get("regime_comparison", {})
    for key, value in regime.items():
        csv_content += f"{key.replace('_', ' ').title()},{format_value(value, key)}\n"
    
    return csv_content

def generate_itr_excel(summary: Dict[str, Any], assessment_year: str) -> bytes:
    """
    Generate ITR summary as Excel (XLSX) format using openpyxl
    """
    try:
        from openpyxl import Workbook
        from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    except ImportError:
        logger.warning("openpyxl not available, using CSV fallback for Excel export")
        return generate_itr_csv(summary).encode('utf-8')
    
    def format_value(value, key_name=""):
        """Format value for Excel"""
        if value is None:
            return "N/A"
        if isinstance(value, bool):
            return "Yes" if value else "No"
        return value
    
    wb = Workbook()
    ws = wb.active
    ws.title = "Tax Summary"
    
    # Define styles
    header_fill = PatternFill(start_color="217F8D", end_color="217F8D", fill_type="solid")
    header_font = Font(bold=True, color="FFFFFF", size=12)
    subheader_fill = PatternFill(start_color="E8F4F7", end_color="E8F4F7", fill_type="solid")
    subheader_font = Font(bold=True, size=11)
    border = Border(left=Side(style='thin'), right=Side(style='thin'), 
                    top=Side(style='thin'), bottom=Side(style='thin'))
    
    row = 1
    
    # Title
    ws[f'A{row}'] = f"ITR Summary - Assessment Year {assessment_year}"
    ws[f'A{row}'].font = Font(bold=True, size=14, color="217F8D")
    row += 2
    
    # Filing Information
    ws[f'A{row}'] = "FILING INFORMATION"
    ws[f'A{row}'].font = subheader_font
    ws[f'A{row}'].fill = subheader_fill
    row += 1
    
    filing = summary.get("itr_filing_summary", {})
    ws[f'A{row}'] = "Assessment Year"
    ws[f'B{row}'] = filing.get('assessment_year', 'N/A')
    row += 1
    ws[f'A{row}'] = "Financial Year"
    ws[f'B{row}'] = filing.get('financial_year', 'N/A')
    row += 1
    ws[f'A{row}'] = "Filing Status"
    ws[f'B{row}'] = filing.get('status', 'DRAFT')
    row += 2
    
    # Personal Details
    ws[f'A{row}'] = "PERSONAL DETAILS"
    ws[f'A{row}'].font = subheader_font
    ws[f'A{row}'].fill = subheader_fill
    row += 1
    
    personal = summary.get("personal_details", {})
    for key, value in personal.items():
        ws[f'A{row}'] = key.replace('_', ' ').title()
        ws[f'B{row}'] = format_value(value)
        row += 1
    row += 1
    
    # Income Details
    ws[f'A{row}'] = "INCOME DETAILS"
    ws[f'A{row}'].font = subheader_font
    ws[f'A{row}'].fill = subheader_fill
    row += 1
    
    income = summary.get("income_details", {})
    for key, value in income.items():
        ws[f'A{row}'] = key.replace('_', ' ').title()
        ws[f'B{row}'] = format_value(value, key)
        if isinstance(value, (int, float)):
            ws[f'B{row}'].number_format = '#,##0'
        row += 1
    row += 1
    
    # Deductions
    ws[f'A{row}'] = "DEDUCTIONS & EXEMPTIONS"
    ws[f'A{row}'].font = subheader_font
    ws[f'A{row}'].fill = subheader_fill
    row += 1
    
    deductions = summary.get("deductions_and_exemptions", {})
    for key, value in deductions.items():
        ws[f'A{row}'] = key.replace('_', ' ').title()
        ws[f'B{row}'] = format_value(value, key)
        if isinstance(value, (int, float)):
            ws[f'B{row}'].number_format = '#,##0'
        row += 1
    row += 1
    
    # Tax Calculation
    ws[f'A{row}'] = "TAX CALCULATION"
    ws[f'A{row}'].font = subheader_font
    ws[f'A{row}'].fill = subheader_fill
    row += 1
    
    tax_calc = summary.get("tax_calculation", {})
    for key, value in tax_calc.items():
        ws[f'A{row}'] = key.replace('_', ' ').title()
        ws[f'B{row}'] = format_value(value, key)
        if isinstance(value, (int, float)):
            if 'percent' in key.lower() or 'rate' in key.lower():
                ws[f'B{row}'].number_format = '0.00"%"'
            else:
                ws[f'B{row}'].number_format = '#,##0'
        row += 1
    row += 1
    
    # Tax Payment & Refund
    ws[f'A{row}'] = "TAX PAYMENT & REFUND"
    ws[f'A{row}'].font = subheader_font
    ws[f'A{row}'].fill = subheader_fill
    row += 1
    
    payment = summary.get("tax_payment_and_refund", {})
    for key, value in payment.items():
        ws[f'A{row}'] = key.replace('_', ' ').title()
        ws[f'B{row}'] = format_value(value, key)
        if isinstance(value, (int, float)):
            ws[f'B{row}'].number_format = '#,##0'
        row += 1
    
    # Adjust column widths
    ws.column_dimensions['A'].width = 35
    ws.column_dimensions['B'].width = 20
    
    # Save to bytes
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    return output.getvalue()

@app.post("/api/tax-saving-suggestions")
async def get_tax_saving_suggestions(request: Dict[str, Any]):
    """
    Provide personalized tax saving suggestions
    """
    try:
        income = request.get("income", 0)
        current_deductions = request.get("current_deductions", {})
        regime = request.get("regime", "old")

        # Calculate remaining deduction potential
        max_80c = 150000
        max_80d = 25000
        current_80c = current_deductions.get("section_80c", 0)
        current_80d = current_deductions.get("section_80d", 0)
        
        suggestions = []
        
        # Only suggest if in old regime or there's potential for savings
        if regime == "old":
            # 80C suggestion
            if current_80c < max_80c:
                remaining_80c = max_80c - current_80c
                potential_savings = (remaining_80c * 0.3)  # Assuming 30% tax bracket
                suggestions.append({
                    "category": "Section 80C Investment",
                    "description": f"You can invest ₹{remaining_80c:,.0f} more in 80C instruments",
                    "potential_savings": potential_savings,
                    "implementation_difficulty": "Easy",
                    "priority": 1,
                    "details": "Consider PPF (15-year), ELSS (3-year), or NSC (5-year)"
                })

            # 80D suggestion
            if current_80d < max_80d:
                remaining_80d = max_80d - current_80d
                potential_savings = (remaining_80d * 0.3)  # Assuming 30% tax bracket
                suggestions.append({
                    "category": "Health Insurance (80D)",
                    "description": f"Increase health insurance coverage by ₹{remaining_80d:,.0f}",
                    "potential_savings": potential_savings,
                    "implementation_difficulty": "Easy",
                    "priority": 2,
                    "details": "Health insurance for family provides tax benefits and protection"
                })

            # NPS suggestion (if not maxed out)
            current_nps = current_deductions.get("section_80ccd1b", 0)
            if current_nps < 50000:
                remaining_nps = 50000 - current_nps
                potential_savings = (remaining_nps * 0.3)
                suggestions.append({
                    "category": "NPS Investment (80CCD1B)",
                    "description": f"Invest ₹{remaining_nps:,.0f} more in NPS for additional tax benefits",
                    "potential_savings": potential_savings,
                    "implementation_difficulty": "Medium",
                    "priority": 3,
                    "details": "NPS offers extra ₹50,000 deduction under 80CCD(1B)"
                })
        else:
            # For new regime
            suggestions.append({
                "category": "Regime Comparison",
                "description": "You're in the new tax regime",
                "potential_savings": 0,
                "implementation_difficulty": "Easy",
                "priority": 1,
                "details": "New regime has lower tax rates but limited deductions. Compare annually based on your investments."
            })

        return suggestions
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
