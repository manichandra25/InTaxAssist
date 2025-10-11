#
# file: backend/services/document_parser.py
#
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
    print("LangChain or Groq dependencies not available.")
    LANGCHAIN_AVAILABLE = False

# Document processing library imports
try:
    from pypdf import PdfReader
    import docx
    LIBRARIES_AVAILABLE = True
except ImportError:
    print("Document processing libraries not available. Install with: pip install pypdf python-docx")
    LIBRARIES_AVAILABLE = False


# Import models and config using relative imports
try:
    from ..models import FinancialData, DocumentParseResponse
    from ..config import settings
except ImportError:
    print("Local imports not available. Using fallback parsing.")
    settings = None
    class DocumentParseResponse: pass
    class FinancialData: pass


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
                self.llm = ChatGroq(
                    groq_api_key=groq_api_key,
                    model_name=getattr(settings, 'GROQ_MODEL', 'llama-3.3-70b-versatile'),
                    temperature=0.1,
                    max_tokens=1000
                )
                self._setup_extraction_chain()
                logger.info("Document parser initialized with Groq model.")
            else:
                logger.warning("Groq API key not available or LangChain not installed. Using fallback.")

        except Exception as e:
            logger.error(f"Error initializing document parser: {e}")

    def _setup_extraction_chain(self):
        """Setup LangChain extraction chain with Groq"""

        extraction_prompt = PromptTemplate(
            input_variables=["document_text"],
            template="""You are an expert at extracting financial information from Indian tax documents like Form 16.

From the following document text, extract the financial values and return ONLY a valid JSON object.

**Fields to extract (set to 0 if not found):**
- **basic_salary**: The value for "Salary as per provisions contained in section 17(1)".
- **hra**: The value for "House rent allowance under section 10(13A)".
- **special_allowance**: The value for "Special allowance". If not found, set to 0.
- **professional_tax**: The value for "Tax on employment under section 16(iii)".
- **section_80c**: The deductible amount for "Deduction in respect of life insurance premia... under section 80C".
- **section_80d**: The deductible amount for "Deduction in respect of health insurance premia under section 80D".
- **tds_deducted**: The total tax deducted. Look for a total amount in a summary table.

**Instructions:**
1.  Return ONLY a valid JSON object. No other text.
2.  All values must be numbers, without commas.
3.  If a value is not found, use 0.

**Document Text:**
{document_text}

**JSON Output:**
"""
        )

        if self.llm:
            self.extraction_chain = LLMChain(
                llm=self.llm,
                prompt=extraction_prompt
            )

    # --- NEW METHOD ADDED ---
    def _preprocess_text_for_extraction(self, text: str) -> str:
        """
        Cleans and preprocesses extracted PDF text to make it more understandable for the LLM.
        - Removes excessive newlines and whitespace.
        - Tries to join labels and values that were split across lines.
        """
        # Remove lines that are just numbers or short codes, which are often page numbers or noise
        lines = [line for line in text.split('\n') if not re.match(r'^\s*[\d\s\W]+\s*$', line)]
        
        # Reduce multiple spaces to one and join lines into a coherent block
        # This helps the LLM associate labels with values that were on different lines
        clean_text = re.sub(r'\s+', ' ', ' '.join(lines)).strip()
        
        return clean_text

    async def parse_document(
        self,
        file_content: bytes,
        filename: str,
        content_type: str
    ) -> DocumentParseResponse:
        """Parse document and extract financial information using Groq"""
        start_time = time.time()
        try:
            # 1. Extract raw text from the document
            raw_text_content = await self._extract_text(file_content, filename, content_type)

            if not raw_text_content:
                raise ValueError("Text extraction from document failed or returned empty.")

            # 2. Pre-process and clean the raw text (THIS IS THE FIX)
            text_content = self._preprocess_text_for_extraction(raw_text_content)
            
            # 3. Extract financial data using the cleaned text
            if LANGCHAIN_AVAILABLE and self.extraction_chain and text_content:
                extracted_data = await self._extract_financial_data_groq(text_content)
                confidence_score = self._calculate_confidence(text_content, extracted_data)
            else:
                extracted_data = self._rule_based_extraction(text_content)
                confidence_score = 0.6
            
            processing_time = time.time() - start_time
            warnings = self._generate_warnings(extracted_data, filename)
            suggestions = self._generate_suggestions(extracted_data, filename)
            financial_data = FinancialData(**extracted_data)

            return DocumentParseResponse(
                success=True, filename=filename, extracted_data=financial_data,
                confidence_score=confidence_score, extracted_text=text_content[:500],
                processing_time=processing_time, warnings=warnings, suggestions=suggestions
            )
        except Exception as e:
            logger.error(f"Error parsing document {filename}: {e}")
            return DocumentParseResponse(
                success=False, filename=filename, extracted_data=FinancialData(),
                confidence_score=0.0, processing_time=time.time() - start_time,
                warnings=[f"Error parsing document: {str(e)}"],
                suggestions=["Please try uploading a clearer document."]
            )


    async def _extract_text(self, file_content: bytes, filename: str, content_type: str) -> str:
        """
        Extract text from various file types.
        """
        try:
            if not LIBRARIES_AVAILABLE:
                logger.error("Document processing libraries (pypdf, python-docx) are not installed.")
                return ""

            text = ""
            file_stream = BytesIO(file_content)

            if content_type == "application/pdf":
                reader = PdfReader(file_stream)
                for page in reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
                return text
            elif content_type in ["application/msword", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]:
                document = docx.Document(file_stream)
                for para in document.paragraphs:
                    text += para.text + "\n"
                return text
            elif content_type == "text/plain":
                return file_content.decode('utf-8')
            else:
                logger.warning(f"Unsupported content type for text extraction: {content_type}")
                return ""
        except Exception as e:
            logger.error(f"Error extracting text from {filename} ({content_type}): {e}")
            return ""

    async def _extract_financial_data_groq(self, text_content: str) -> Dict[str, Any]:
        """Extract financial data using Groq/LangChain"""
        try:
            if not self.extraction_chain:
                return self._rule_based_extraction(text_content)

            result = await asyncio.to_thread(self.extraction_chain.run, document_text=text_content)

            try:
                cleaned_result = result.strip()
                json_match = re.search(r'\{.*\}', cleaned_result, re.DOTALL)
                if json_match:
                    cleaned_result = json_match.group(0)
                else:
                    raise json.JSONDecodeError("No JSON object found in LLM response", cleaned_result, 0)

                extracted_data = json.loads(cleaned_result)
                validated_data = self._validate_extracted_data(extracted_data)
                logger.info("Successfully extracted data using Groq.")
                return validated_data
            except (json.JSONDecodeError, IndexError, ValueError) as e:
                logger.warning(f"Failed to parse Groq response as JSON: {e}. Falling back to rules.")
                return self._rule_based_extraction(text_content)
        except Exception as e:
            logger.error(f"Error in Groq extraction: {e}")
            return self._rule_based_extraction(text_content)

    def _validate_extracted_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and clean extracted data"""
        expected_fields = {
            "basic_salary": 0, "hra": 0, "special_allowance": 0, "professional_tax": 0,
            "section_80c": 0, "section_80d": 0, "tds_deducted": 0
        }
        validated_data = {}
        for field, default_value in expected_fields.items():
            value = data.get(field, default_value)
            try:
                validated_data[field] = max(0, float(value))
            except (ValueError, TypeError):
                validated_data[field] = default_value
        return validated_data

    def _rule_based_extraction(self, text_content: str) -> Dict[str, Any]:
        """Enhanced rule-based extraction as fallback"""
        # This will be less effective on complex formats but is a good fallback
        patterns = {
            "basic_salary": [r"salary as per.*?section 17\(1\).*?([\d,.]+)"],
            "hra": [r"house rent allowance.*?([\d,.]+)"],
            "professional_tax": [r"tax on employment.*?([\d,.]+)"],
            "section_80c": [r"section 80c.*?([\d,.]+)"],
            "tds_deducted": [r"tax deducted at source.*?([\d,.]+)"],
        }
        extracted_data = {}
        text_lower = text_content.lower().replace('\n', ' ')
        for field, field_patterns in patterns.items():
            value = 0
            for pattern in field_patterns:
                match = re.search(pattern, text_lower, re.IGNORECASE)
                if match:
                    try:
                        value = float(match.group(1).replace(',', ''))
                        break
                    except (ValueError, AttributeError):
                        continue
            extracted_data[field] = value
        return extracted_data

    def _calculate_confidence(self, text_content: str, extracted_data: Dict[str, Any]) -> float:
        """Calculate confidence score for extraction"""
        if not any(extracted_data.values()): return 0.1
        non_zero_fields = sum(1 for value in extracted_data.values() if value > 0)
        field_confidence = non_zero_fields / len(extracted_data) if extracted_data else 0
        return min(max(field_confidence * 0.8 + 0.15, 0.1), 0.95)

    def _generate_warnings(self, extracted_data: Dict[str, Any], filename: str) -> List[str]:
        """Generate warnings based on extracted data"""
        warnings = []
        if not any(v > 0 for k, v in extracted_data.items()):
            warnings.append("Could not extract any financial data. Document may be unreadable or empty.")
        return warnings

    def _generate_suggestions(self, extracted_data: Dict[str, Any], filename: str) -> List[str]:
        """Generate suggestions based on extracted data"""
        suggestions = []
        if extracted_data.get("section_80c", 0) < 150000:
            suggestions.append("You may have more room for tax-saving investments under Section 80C.")
        suggestions.append("Please double-check all extracted amounts for accuracy.")
        return suggestions