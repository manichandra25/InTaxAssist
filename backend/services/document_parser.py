import asyncio
import logging
from typing import Dict, Any, Optional, List
import time
from io import BytesIO
import re
import json

# LangChain imports with Groq support
try:
    from langchain_groq import ChatGroq
    from langchain_community.embeddings import HuggingFaceEmbeddings
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    from langchain.chains import LLMChain
    from langchain.prompts import PromptTemplate
    from langchain.schema import Document
    LANGCHAIN_AVAILABLE = True
except ImportError:
    print("LangChain or Groq dependencies not available. Install with: pip install langchain-groq langchain-community")
    LANGCHAIN_AVAILABLE = False

# Standard library imports
import tempfile
import os
from pathlib import Path

# Import models and config
try:
    from models import FinancialData, DocumentParseResponse
    from config import settings
except ImportError:
    print("Local imports not available. Using fallback parsing.")
    settings = None

logger = logging.getLogger(__name__)

class DocumentParserService:
    """Service for parsing financial documents using Groq with LangChain"""

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
        """Initialize LangChain components with Groq"""
        try:
            groq_api_key = getattr(settings, 'GROQ_API_KEY', None) if settings else None

            if LANGCHAIN_AVAILABLE and groq_api_key:
                # Initialize Groq with Llama model for document parsing
                self.llm = ChatGroq(
                    groq_api_key=groq_api_key,
                    model_name=getattr(settings, 'GROQ_MODEL', 'llama2-70b-4096'),
                    temperature=0.1,  # Low temperature for consistent extraction
                    max_tokens=1000
                )

                # Use HuggingFace embeddings (free alternative)
                self.embeddings = HuggingFaceEmbeddings(
                    model_name="sentence-transformers/all-MiniLM-L6-v2"
                )

                self._setup_extraction_chain()
                logger.info("Document parser initialized with Groq and Llama model")
            else:
                logger.warning("Groq API key not available or LangChain not installed. Using fallback parsing.")

        except Exception as e:
            logger.error(f"Error initializing document parser: {e}")
            logger.info("Using fallback document parsing")

    def _setup_extraction_chain(self):
        """Setup LangChain extraction chain with Groq"""

        extraction_prompt = PromptTemplate(
            input_variables=["document_text"],
            template="""You are an expert at extracting financial information from Indian tax documents including Form 16, salary slips, bank statements, and investment proofs.

Extract financial information from the following document text and return ONLY a valid JSON object with the extracted values.

Look for and extract these specific fields (set to 0 if not found):

**Salary Components:**
- basic_salary: Basic salary amount per year
- hra: House Rent Allowance per year
- special_allowance: Special allowance per year
- other_allowances: Other allowances per year
- bonus: Annual bonus amount

**Other Income:**
- interest_income: Interest from savings/FD
- rental_income: Rental income
- capital_gains: Capital gains

**Deductions and Investments:**
- section_80c: Section 80C investments (EPF, PPF, ELSS, NSC, life insurance, etc.)
- section_80d: Section 80D medical insurance premiums
- section_24: Home loan interest (Section 24)
- professional_tax: Professional tax paid

**Tax Information:**
- tds_deducted: Total TDS deducted
- advance_tax: Advance tax paid

**Important Instructions:**
1. Return ONLY valid JSON format - no additional text or explanations
2. Use exact field names as specified above
3. All values should be numbers (not strings)
4. If a value is not found, use 0
5. For annual amounts, convert monthly amounts to yearly by multiplying by 12
6. Look for keywords like "basic pay", "HRA", "special allowance", "PF", "insurance", "TDS", etc.

Document Text:
{document_text}

JSON Output:
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
        """Parse document and extract financial information using Groq"""

        start_time = time.time()

        try:
            # Extract text from document
            text_content = await self._extract_text(file_content, filename, content_type)

            # Extract financial data using Groq/LangChain or fallback
            if LANGCHAIN_AVAILABLE and self.extraction_chain and text_content:
                extracted_data = await self._extract_financial_data_groq(text_content)
                confidence_score = self._calculate_confidence(text_content, extracted_data)
            else:
                # Fallback: Use rule-based extraction
                extracted_data = self._rule_based_extraction(text_content)
                confidence_score = 0.6

            processing_time = time.time() - start_time

            # Generate warnings and suggestions
            warnings = self._generate_warnings(extracted_data, filename)
            suggestions = self._generate_suggestions(extracted_data, filename)

            # Create FinancialData object
            financial_data = FinancialData(**extracted_data) if hasattr(FinancialData, '__init__') else extracted_data

            return DocumentParseResponse(
                success=True,
                filename=filename,
                extracted_data=financial_data,
                confidence_score=confidence_score,
                extracted_text=text_content[:500] if text_content else "",  # First 500 chars
                processing_time=processing_time,
                warnings=warnings,
                suggestions=suggestions
            ) if hasattr(DocumentParseResponse, '__init__') else {
                "success": True,
                "filename": filename,
                "extracted_data": extracted_data,
                "confidence_score": confidence_score,
                "processing_time": processing_time,
                "warnings": warnings,
                "suggestions": suggestions
            }

        except Exception as e:
            logger.error(f"Error parsing document {filename}: {e}")
            processing_time = time.time() - start_time

            fallback_data = FinancialData() if hasattr(FinancialData, '__init__') else {}

            return DocumentParseResponse(
                success=False,
                filename=filename,
                extracted_data=fallback_data,
                confidence_score=0.0,
                processing_time=processing_time,
                warnings=[f"Error parsing document: {str(e)}"],
                suggestions=["Please try uploading a clearer document or different file format"]
            ) if hasattr(DocumentParseResponse, '__init__') else {
                "success": False,
                "filename": filename,
                "extracted_data": fallback_data,
                "confidence_score": 0.0,
                "processing_time": processing_time,
                "warnings": [f"Error parsing document: {str(e)}"]
            }

    async def _extract_text(self, file_content: bytes, filename: str, content_type: str) -> str:
        """Extract text from various file types"""

        try:
            if content_type == "text/plain":
                return file_content.decode('utf-8')

            # For this demo, we'll use enhanced mock extraction based on filename
            # In production, implement proper PDF/DOCX extraction using pypdf2, docx2txt, etc.

            filename_lower = filename.lower()

            # Enhanced mock extractions based on document type
            if any(keyword in filename_lower for keyword in ["form16", "form-16", "f16"]):
                return """Form 16 - Part B - Details of Salary Paid and Tax Deducted
Name: John Doe
PAN: ABCDE1234F
Assessment Year: 2024-25

SALARY DETAILS:
Basic Salary: Rs. 6,00,000
HRA: Rs. 2,40,000  
Special Allowance: Rs. 80,000
Other Allowances: Rs. 1,20,000
Bonus: Rs. 50,000
Gross Salary: Rs. 10,90,000

DEDUCTIONS:
Employee PF: Rs. 72,000
Professional Tax: Rs. 2,400
Total Deductions: Rs. 74,400

NET SALARY: Rs. 10,15,600

TAX COMPUTATION:
Gross Total Income: Rs. 10,90,000
Less: Standard Deduction u/s 16(ia): Rs. 50,000
Less: Deduction u/s 80C: Rs. 1,50,000
Less: Deduction u/s 80D: Rs. 25,000
Taxable Income: Rs. 8,65,000

TAX LIABILITY:
On Rs. 2,50,000 @ NIL: Rs. 0
On Rs. 2,50,000 @ 5%: Rs. 12,500
On Rs. 3,65,000 @ 20%: Rs. 73,000
Total Tax: Rs. 85,500
Add: Cess @ 4%: Rs. 3,420
Total Tax and Cess: Rs. 88,920

TDS DEDUCTED: Rs. 88,920"""

            elif any(keyword in filename_lower for keyword in ["salary", "payslip", "pay-slip"]):
                return """SALARY SLIP - March 2024
Employee: John Doe
Employee ID: EMP001

EARNINGS:
Basic Salary: Rs. 50,000
HRA: Rs. 20,000
Special Allowance: Rs. 6,667
Conveyance: Rs. 1,600
Medical: Rs. 1,250
Gross Salary: Rs. 79,517

DEDUCTIONS:
Employee PF: Rs. 6,000
Professional Tax: Rs. 200
Income Tax (TDS): Rs. 7,410
Total Deductions: Rs. 13,610

NET SALARY: Rs. 65,907

Year to Date (Apr 2023 - Mar 2024):
Gross Salary: Rs. 9,54,204
Total PF: Rs. 72,000  
Total TDS: Rs. 88,920"""

            elif any(keyword in filename_lower for keyword in ["investment", "80c", "80d", "proof"]):
                return """INVESTMENT PROOFS - AY 2024-25

SECTION 80C INVESTMENTS:
Employee Provident Fund: Rs. 72,000
Public Provident Fund: Rs. 50,000
ELSS Mutual Fund: Rs. 28,000
Total 80C: Rs. 1,50,000

SECTION 80D MEDICAL INSURANCE:
Premium for Self & Family: Rs. 25,000
Total 80D: Rs. 25,000

OTHER INVESTMENTS:
NPS Additional (80CCD1B): Rs. 50,000
Home Loan Principal: Rs. 2,00,000 (Under 80C)

BANK INTEREST:
Savings Account Interest: Rs. 8,500 (Under 80TTA)"""

            elif any(keyword in filename_lower for keyword in ["bank", "statement"]):
                return """BANK STATEMENT - HDFC Bank
Account: XXXXXXXXXX1234
Period: April 2023 to March 2024

INTEREST EARNED:
Savings Account Interest: Rs. 8,500
Fixed Deposit Interest: Rs. 15,000
Total Interest: Rs. 23,500

SALARY CREDITS:
Monthly Salary Credits: Rs. 65,907 x 12 months
Annual Salary: Rs. 7,90,884

INVESTMENT DEBITS:
PPF Contribution: Rs. 50,000
ELSS SIP: Rs. 28,000
Insurance Premium: Rs. 25,000"""

            else:
                # Generic financial document
                return f"""Financial Document: {filename}
Basic Salary: Rs. 6,00,000
HRA: Rs. 2,40,000
Special Allowance: Rs. 80,000
Section 80C: Rs. 1,50,000
Section 80D: Rs. 25,000
TDS Deducted: Rs. 88,920
Home Loan Interest: Rs. 1,80,000"""

        except Exception as e:
            logger.error(f"Error extracting text from {filename}: {e}")
            return ""

    async def _extract_financial_data_groq(self, text_content: str) -> Dict[str, Any]:
        """Extract financial data using Groq/LangChain"""

        try:
            if not self.extraction_chain:
                return self._rule_based_extraction(text_content)

            # Use Groq LangChain to extract data
            result = await asyncio.to_thread(
                self.extraction_chain.run,
                document_text=text_content
            )

            # Parse the JSON response from Llama model
            try:
                # Clean the response to extract JSON
                cleaned_result = result.strip()

                # Handle various JSON response formats
                if "```json" in cleaned_result:
                    cleaned_result = cleaned_result.split("```json")[1].split("```")[0].strip()
                elif "```" in cleaned_result:
                    cleaned_result = cleaned_result.split("```")[1].strip()
                elif "JSON Output:" in cleaned_result:
                    cleaned_result = cleaned_result.split("JSON Output:")[1].strip()

                # Try to find JSON-like content
                json_start = cleaned_result.find('{')
                json_end = cleaned_result.rfind('}') + 1

                if json_start >= 0 and json_end > json_start:
                    cleaned_result = cleaned_result[json_start:json_end]

                extracted_data = json.loads(cleaned_result)

                # Validate and clean the extracted data
                validated_data = self._validate_extracted_data(extracted_data)

                logger.info("Successfully extracted data using Groq")
                return validated_data

            except (json.JSONDecodeError, IndexError, ValueError) as e:
                logger.warning(f"Failed to parse Groq response as JSON: {e}. Response was: {result[:200]}...")
                logger.info("Falling back to rule-based extraction")
                return self._rule_based_extraction(text_content)

        except Exception as e:
            logger.error(f"Error in Groq extraction: {e}")
            return self._rule_based_extraction(text_content)

    def _validate_extracted_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and clean extracted data"""

        # Define all expected fields with defaults
        expected_fields = {
            "basic_salary": 0, "hra": 0, "special_allowance": 0, "other_allowances": 0,
            "bonus": 0, "interest_income": 0, "rental_income": 0, "capital_gains": 0,
            "other_income": 0, "section_80c": 0, "section_80d": 0, "section_80g": 0,
            "section_24": 0, "standard_deduction": 50000, "professional_tax": 0,
            "section_80ccd1b": 0, "section_80e": 0, "section_80tta": 0,
            "tds_deducted": 0, "advance_tax": 0
        }

        validated_data = {}

        for field, default_value in expected_fields.items():
            if field in data:
                try:
                    # Convert to float and ensure non-negative
                    value = float(data[field])
                    validated_data[field] = max(0, value)
                except (ValueError, TypeError):
                    validated_data[field] = default_value
            else:
                validated_data[field] = default_value

        # Apply validation rules
        validated_data["section_80c"] = min(validated_data["section_80c"], 150000)
        validated_data["section_80d"] = min(validated_data["section_80d"], 25000)
        validated_data["section_80ccd1b"] = min(validated_data["section_80ccd1b"], 50000)
        validated_data["section_80tta"] = min(validated_data["section_80tta"], 10000)
        validated_data["professional_tax"] = min(validated_data["professional_tax"], 2500)

        return validated_data

    def _rule_based_extraction(self, text_content: str) -> Dict[str, Any]:
        """Enhanced rule-based extraction as fallback"""

        # Define regex patterns for common financial terms
        patterns = {
            "basic_salary": [
                r"basic\s+salary[:\s]+(?:rs\.?\s*)?([\d,]+)",
                r"basic\s+pay[:\s]+(?:rs\.?\s*)?([\d,]+)",
                r"basic[:\s]+(?:rs\.?\s*)?([\d,]+)"
            ],
            "hra": [
                r"hra[:\s]+(?:rs\.?\s*)?([\d,]+)",
                r"house\s+rent\s+allowance[:\s]+(?:rs\.?\s*)?([\d,]+)"
            ],
            "special_allowance": [
                r"special\s+allowance[:\s]+(?:rs\.?\s*)?([\d,]+)",
                r"special\s+pay[:\s]+(?:rs\.?\s*)?([\d,]+)"
            ],
            "other_allowances": [
                r"other\s+allowance[s]?[:\s]+(?:rs\.?\s*)?([\d,]+)",
                r"conveyance[:\s]+(?:rs\.?\s*)?([\d,]+)",
                r"medical[:\s]+(?:rs\.?\s*)?([\d,]+)"
            ],
            "bonus": [
                r"bonus[:\s]+(?:rs\.?\s*)?([\d,]+)",
                r"incentive[:\s]+(?:rs\.?\s*)?([\d,]+)"
            ],
            "section_80c": [
                r"80c[:\s]+(?:rs\.?\s*)?([\d,]+)",
                r"section\s+80c[:\s]+(?:rs\.?\s*)?([\d,]+)",
                r"employee\s+pf[:\s]+(?:rs\.?\s*)?([\d,]+)",
                r"ppf[:\s]+(?:rs\.?\s*)?([\d,]+)",
                r"elss[:\s]+(?:rs\.?\s*)?([\d,]+)"
            ],
            "section_80d": [
                r"80d[:\s]+(?:rs\.?\s*)?([\d,]+)",
                r"section\s+80d[:\s]+(?:rs\.?\s*)?([\d,]+)",
                r"medical\s+insurance[:\s]+(?:rs\.?\s*)?([\d,]+)",
                r"health\s+insurance[:\s]+(?:rs\.?\s*)?([\d,]+)"
            ],
            "section_24": [
                r"section\s+24[:\s]+(?:rs\.?\s*)?([\d,]+)",
                r"home\s+loan\s+interest[:\s]+(?:rs\.?\s*)?([\d,]+)",
                r"housing\s+loan[:\s]+(?:rs\.?\s*)?([\d,]+)"
            ],
            "tds_deducted": [
                r"tds[:\s]+(?:rs\.?\s*)?([\d,]+)",
                r"tax\s+deducted[:\s]+(?:rs\.?\s*)?([\d,]+)",
                r"income\s+tax[:\s]+(?:rs\.?\s*)?([\d,]+)"
            ],
            "professional_tax": [
                r"professional\s+tax[:\s]+(?:rs\.?\s*)?([\d,]+)",
                r"pt[:\s]+(?:rs\.?\s*)?([\d,]+)"
            ],
            "interest_income": [
                r"interest[:\s]+(?:rs\.?\s*)?([\d,]+)",
                r"bank\s+interest[:\s]+(?:rs\.?\s*)?([\d,]+)",
                r"savings\s+interest[:\s]+(?:rs\.?\s*)?([\d,]+)"
            ]
        }

        extracted_data = {
            "basic_salary": 0, "hra": 0, "special_allowance": 0, "other_allowances": 0,
            "bonus": 0, "interest_income": 0, "rental_income": 0, "capital_gains": 0,
            "other_income": 0, "section_80c": 0, "section_80d": 0, "section_80g": 0,
            "section_24": 0, "standard_deduction": 50000, "professional_tax": 0,
            "section_80ccd1b": 0, "section_80e": 0, "section_80tta": 0,
            "tds_deducted": 0, "advance_tax": 0
        }

        text_lower = text_content.lower() if text_content else ""

        # Apply pattern matching
        for field, field_patterns in patterns.items():
            max_value = 0
            for pattern in field_patterns:
                matches = re.findall(pattern, text_lower, re.IGNORECASE)
                for match in matches:
                    try:
                        value = float(match.replace(',', ''))
                        max_value = max(max_value, value)
                    except (ValueError, AttributeError):
                        continue
            extracted_data[field] = max_value

        return extracted_data

    def _calculate_confidence(self, text_content: str, extracted_data: Dict[str, Any]) -> float:
        """Calculate confidence score for extraction"""

        # Count non-zero extracted fields
        non_zero_fields = sum(1 for value in extracted_data.values() if value > 0)
        total_fields = len(extracted_data)

        # Calculate field extraction rate
        field_confidence = non_zero_fields / total_fields if total_fields > 0 else 0

        # Check for financial keywords in text
        financial_keywords = [
            "salary", "allowance", "deduction", "tax", "income", "investment",
            "80c", "80d", "hra", "pf", "insurance", "tds", "form 16"
        ]
        keyword_count = sum(1 for keyword in financial_keywords 
                          if keyword.lower() in text_content.lower())
        keyword_confidence = min(keyword_count / len(financial_keywords), 1.0)

        # Text quality indicators
        text_length_confidence = min(len(text_content) / 1000, 1.0) if text_content else 0

        # Boost confidence if using Groq extraction
        groq_boost = 0.15 if self.extraction_chain else 0

        # Calculate overall confidence
        overall_confidence = (
            field_confidence * 0.4 +
            keyword_confidence * 0.3 +
            text_length_confidence * 0.15 +
            groq_boost
        )

        return min(max(overall_confidence, 0.1), 0.95)  # Clamp between 0.1 and 0.95

    def _generate_warnings(self, extracted_data: Dict[str, Any], filename: str) -> List[str]:
        """Generate warnings based on extracted data"""

        warnings = []

        # Check for unrealistic values
        if extracted_data.get("basic_salary", 0) > 50000000:  # 5 crores
            warnings.append("Basic salary seems unusually high. Please verify the extracted amount.")

        if extracted_data.get("section_80c", 0) > 150000:
            warnings.append("Section 80C amount exceeds maximum limit of ₹1,50,000. Will be capped at limit.")

        if extracted_data.get("section_80d", 0) > 25000:
            warnings.append("Section 80D amount exceeds standard limit of ₹25,000 for individuals.")

        # Check if no meaningful data was extracted
        total_extracted = sum(v for v in extracted_data.values() if v > 0)
        if total_extracted <= 50000:  # Only standard deduction
            warnings.append("Limited financial data could be extracted. Document quality may be poor or format not recognized.")

        # File-specific warnings
        if "form16" in filename.lower() and extracted_data.get("tds_deducted", 0) == 0:
            warnings.append("No TDS information found in Form 16. This is unusual for a salary certificate.")

        return warnings

    def _generate_suggestions(self, extracted_data: Dict[str, Any], filename: str) -> List[str]:
        """Generate suggestions based on extracted data and filename"""

        suggestions = []

        # Tax optimization suggestions
        section_80c = extracted_data.get("section_80c", 0)
        if section_80c < 150000:
            remaining = 150000 - section_80c
            suggestions.append(f"Consider investing ₹{remaining:,.0f} more in 80C instruments to maximize tax deduction.")

        if extracted_data.get("section_80d", 0) == 0:
            suggestions.append("Consider health insurance premium for 80D deduction (up to ₹25,000).")

        # Data quality suggestions
        if self.extraction_chain:
            suggestions.append("Document processed using Groq's AI for enhanced accuracy.")
        else:
            suggestions.append("For better extraction accuracy, ensure Groq API key is configured.")

        # Document-specific suggestions
        if "salary" in filename.lower() and extracted_data.get("basic_salary", 0) > 0:
            suggestions.append("Upload Form 16 for complete annual tax information.")

        if extracted_data.get("section_24", 0) > 0:
            suggestions.append("Home loan interest found. Ensure you have proper documentation from the bank.")

        # Always suggest verification
        suggestions.append("Please verify all extracted amounts before proceeding with tax calculation.")

        return suggestions
