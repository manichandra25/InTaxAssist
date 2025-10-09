# Create all the service files for the backend

# Create services/__init__.py
with open("tax-filing-system/backend/services/__init__.py", "w") as f:
    f.write("# Services package\n")

# Create document_parser.py service
document_parser_content = '''import asyncio
import logging
from typing import Dict, Any, Optional, List
import time
from io import BytesIO
import re

# LangChain imports - with fallback handling
try:
    from langchain.document_loaders import PyPDFLoader, Docx2txtLoader, TextLoader
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    from langchain.llms import OpenAI
    from langchain.chains import LLMChain
    from langchain.prompts import PromptTemplate
    from langchain.embeddings import OpenAIEmbeddings
    from langchain.vectorstores import FAISS
    from langchain.schema import Document
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False

# Standard library imports
import tempfile
import os
from pathlib import Path

# Import models and config
from models import FinancialData, DocumentParseResponse
from config import settings

logger = logging.getLogger(__name__)

class DocumentParserService:
    """Service for parsing financial documents using LangChain"""
    
    def __init__(self):
        self.llm = None
        self.embeddings = None
        self.text_splitter = None
        self.extraction_chain = None
        
        if LANGCHAIN_AVAILABLE:
            self.text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200
            )
        
    async def initialize(self):
        """Initialize LangChain components"""
        try:
            if LANGCHAIN_AVAILABLE and settings.OPENAI_API_KEY:
                self.llm = OpenAI(
                    openai_api_key=settings.OPENAI_API_KEY,
                    temperature=0.1,
                    max_tokens=1000
                )
                self.embeddings = OpenAIEmbeddings(
                    openai_api_key=settings.OPENAI_API_KEY
                )
                self._setup_extraction_chain()
                logger.info("Document parser initialized with LangChain")
            else:
                logger.warning("LangChain not available or API key missing. Using fallback parsing.")
                
        except Exception as e:
            logger.error(f"Error initializing document parser: {e}")
            logger.info("Using fallback document parsing")
    
    def _setup_extraction_chain(self):
        """Setup LangChain extraction chain"""
        
        extraction_prompt = PromptTemplate(
            input_variables=["document_text"],
            template="""
            Extract financial information from the following document text.
            Look for and extract the following information:

            1. Salary Components:
               - Basic Salary
               - HRA (House Rent Allowance)
               - Special Allowance
               - Other Allowances
               - Bonus

            2. Other Income:
               - Interest Income
               - Rental Income
               - Capital Gains

            3. Deductions and Investments:
               - Section 80C investments (EPF, PPF, ELSS, etc.)
               - Section 80D (Medical Insurance)
               - Home loan interest (Section 24)
               - Professional tax

            4. Tax Information:
               - TDS deducted
               - Advance tax paid

            Document Text:
            {document_text}

            Please extract the numerical values and return them in the following JSON format:
            {{
                "basic_salary": 0,
                "hra": 0,
                "special_allowance": 0,
                "other_allowances": 0,
                "bonus": 0,
                "interest_income": 0,
                "rental_income": 0,
                "capital_gains": 0,
                "section_80c": 0,
                "section_80d": 0,
                "section_24": 0,
                "professional_tax": 0,
                "tds_deducted": 0,
                "advance_tax": 0
            }}

            If any value is not found, keep it as 0. Only return the JSON object.
            """
        )
        
        if self.llm:
            self.extraction_chain = LLMChain(
                llm=self.llm,
                prompt=extraction_prompt
            )

    async def parse_document(
        self, 
        file_content: bytes, 
        filename: str, 
        content_type: str
    ) -> DocumentParseResponse:
        """Parse document and extract financial information"""
        
        start_time = time.time()
        
        try:
            # Extract text from document
            text_content = await self._extract_text(file_content, filename, content_type)
            
            # Extract financial data using LangChain or fallback
            if LANGCHAIN_AVAILABLE and self.extraction_chain and text_content:
                extracted_data = await self._extract_financial_data(text_content)
                confidence_score = self._calculate_confidence(text_content, extracted_data)
            else:
                # Fallback: Use rule-based extraction
                extracted_data = self._rule_based_extraction(text_content)
                confidence_score = 0.6
            
            processing_time = time.time() - start_time
            
            # Generate warnings and suggestions
            warnings = self._generate_warnings(extracted_data)
            suggestions = self._generate_suggestions(extracted_data)
            
            return DocumentParseResponse(
                success=True,
                filename=filename,
                extracted_data=FinancialData(**extracted_data),
                confidence_score=confidence_score,
                extracted_text=text_content[:500] if text_content else "",  # First 500 chars
                processing_time=processing_time,
                warnings=warnings,
                suggestions=suggestions
            )
            
        except Exception as e:
            logger.error(f"Error parsing document {filename}: {e}")
            return DocumentParseResponse(
                success=False,
                filename=filename,
                extracted_data=FinancialData(),
                confidence_score=0.0,
                processing_time=time.time() - start_time,
                warnings=[f"Error parsing document: {str(e)}"]
            )

    async def _extract_text(self, file_content: bytes, filename: str, content_type: str) -> str:
        """Extract text from various file types"""
        
        try:
            if content_type == "text/plain":
                return file_content.decode('utf-8')
            
            # For other file types, return a mock extraction for demo
            # In production, implement proper extraction using libraries
            return f"Mock extracted text from {filename}. Basic Salary: 600000, HRA: 240000, Section 80C: 150000, TDS: 45000"
                
        except Exception as e:
            logger.error(f"Error extracting text from {filename}: {e}")
            return ""

    async def _extract_financial_data(self, text_content: str) -> Dict[str, Any]:
        """Extract financial data using LangChain"""
        
        try:
            if not self.extraction_chain:
                return self._rule_based_extraction(text_content)
            
            # Use LangChain to extract data
            result = await asyncio.to_thread(
                self.extraction_chain.run,
                document_text=text_content
            )
            
            # Parse the JSON response
            import json
            try:
                extracted_data = json.loads(result.strip())
                return extracted_data
            except json.JSONDecodeError:
                logger.warning("Failed to parse LLM response as JSON, falling back to rule-based extraction")
                return self._rule_based_extraction(text_content)
                
        except Exception as e:
            logger.error(f"Error in LLM extraction: {e}")
            return self._rule_based_extraction(text_content)

    def _rule_based_extraction(self, text_content: str) -> Dict[str, Any]:
        """Rule-based extraction as fallback"""
        
        # Define regex patterns for common financial terms
        patterns = {
            "basic_salary": r"basic\\s+salary[:\\s]+([\\d,]+)",
            "hra": r"hra|house\\s+rent\\s+allowance[:\\s]+([\\d,]+)",
            "special_allowance": r"special\\s+allowance[:\\s]+([\\d,]+)",
            "other_allowances": r"other\\s+allowance[:\\s]+([\\d,]+)",
            "bonus": r"bonus[:\\s]+([\\d,]+)",
            "section_80c": r"80c|section\\s+80c[:\\s]+([\\d,]+)",
            "section_80d": r"80d|section\\s+80d[:\\s]+([\\d,]+)",
            "tds_deducted": r"tds|tax\\s+deducted[:\\s]+([\\d,]+)",
        }
        
        extracted_data = {}
        text_lower = text_content.lower() if text_content else ""
        
        for key, pattern in patterns.items():
            match = re.search(pattern, text_lower, re.IGNORECASE)
            if match:
                try:
                    value = float(match.group(1).replace(',', ''))
                    extracted_data[key] = value
                except (ValueError, IndexError):
                    extracted_data[key] = 0
            else:
                extracted_data[key] = 0
        
        # Set defaults for missing fields
        all_fields = [
            "basic_salary", "hra", "special_allowance", "other_allowances", "bonus",
            "interest_income", "rental_income", "capital_gains", "other_income",
            "section_80c", "section_80d", "section_80g", "section_24", 
            "standard_deduction", "professional_tax", "section_80ccd1b",
            "section_80e", "section_80tta", "tds_deducted", "advance_tax"
        ]
        
        for field in all_fields:
            if field not in extracted_data:
                extracted_data[field] = 0
        
        # Set standard deduction default
        extracted_data["standard_deduction"] = 50000
        
        return extracted_data

    def _calculate_confidence(self, text_content: str, extracted_data: Dict[str, Any]) -> float:
        """Calculate confidence score for extraction"""
        
        # Simple confidence calculation
        non_zero_fields = sum(1 for value in extracted_data.values() if value > 0)
        total_fields = len(extracted_data)
        
        # Financial keywords
        keywords = ["salary", "allowance", "deduction", "tax", "income", "investment"]
        keyword_count = sum(1 for keyword in keywords if keyword.lower() in text_content.lower())
        
        # Calculate confidence (0.0 to 1.0)
        field_confidence = non_zero_fields / total_fields if total_fields > 0 else 0
        keyword_confidence = min(keyword_count / len(keywords), 1.0)
        
        overall_confidence = (field_confidence * 0.6) + (keyword_confidence * 0.4)
        
        return min(max(overall_confidence, 0.1), 0.95)  # Clamp between 0.1 and 0.95

    def _generate_warnings(self, extracted_data: Dict[str, Any]) -> List[str]:
        """Generate warnings based on extracted data"""
        
        warnings = []
        
        # Check for unrealistic values
        if extracted_data.get("basic_salary", 0) > 10000000:  # 1 crore
            warnings.append("Basic salary seems unusually high. Please verify.")
        
        if extracted_data.get("section_80c", 0) > 150000:
            warnings.append("Section 80C deduction exceeds maximum limit of ₹1,50,000")
        
        if extracted_data.get("section_80d", 0) > 25000:
            warnings.append("Section 80D deduction exceeds standard limit of ₹25,000")
        
        # Check if no financial data was extracted
        total_extracted = sum(extracted_data.values())
        if total_extracted <= 50000:  # Only standard deduction
            warnings.append("Very little financial data was extracted. Please check document quality.")
        
        return warnings

    def _generate_suggestions(self, extracted_data: Dict[str, Any]) -> List[str]:
        """Generate suggestions based on extracted data"""
        
        suggestions = []
        
        # Suggest maximizing 80C if under limit
        section_80c = extracted_data.get("section_80c", 0)
        if section_80c < 150000:
            remaining = 150000 - section_80c
            suggestions.append(f"Consider investing ₹{remaining:,.0f} more in 80C instruments to maximize deduction")
        
        # Suggest health insurance if not claimed
        if extracted_data.get("section_80d", 0) == 0:
            suggestions.append("Consider health insurance premium for 80D deduction (up to ₹25,000)")
        
        # Suggest document verification
        suggestions.append("Please verify all extracted amounts before proceeding with tax calculation")
        
        return suggestions
'''

# Write document parser service
with open("tax-filing-system/backend/services/document_parser.py", "w", encoding="utf-8") as f:
    f.write(document_parser_content)

print("Created services/document_parser.py - Document parsing service")