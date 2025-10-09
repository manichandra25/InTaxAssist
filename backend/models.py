from pydantic import BaseModel, Field, validator
from typing import List, Dict, Optional, Any, Union
from datetime import datetime
from enum import Enum

class TaxRegime(str, Enum):
    """Tax regime enumeration"""
    OLD = "old"
    NEW = "new"

class FinancialData(BaseModel):
    """Financial data model for tax calculations"""

    # Income components
    basic_salary: float = Field(default=0, ge=0, description="Basic salary amount")
    hra: float = Field(default=0, ge=0, description="House Rent Allowance")
    special_allowance: float = Field(default=0, ge=0, description="Special allowance")
    other_allowances: float = Field(default=0, ge=0, description="Other allowances")
    bonus: float = Field(default=0, ge=0, description="Bonus amount")

    # Other income sources
    interest_income: float = Field(default=0, ge=0, description="Interest from savings/FD")
    rental_income: float = Field(default=0, ge=0, description="Rental income")
    capital_gains: float = Field(default=0, ge=0, description="Capital gains")
    other_income: float = Field(default=0, ge=0, description="Other sources of income")

    # Deductions under old regime
    section_80c: float = Field(default=0, ge=0, le=150000, description="80C deductions (max ₹1.5L)")
    section_80d: float = Field(default=0, ge=0, le=25000, description="80D medical insurance (max ₹25K)")
    section_80g: float = Field(default=0, ge=0, description="80G donations")
    section_24: float = Field(default=0, ge=0, description="24 home loan interest")
    section_80ccd1b: float = Field(default=0, ge=0, le=50000, description="NPS additional ₹50K")
    section_80e: float = Field(default=0, ge=0, description="Education loan interest")
    section_80tta: float = Field(default=0, ge=0, le=10000, description="Interest on savings account")

    # Common deductions
    standard_deduction: float = Field(default=50000, description="Standard deduction")
    professional_tax: float = Field(default=0, ge=0, le=2500, description="Professional tax")

    # Tax payments
    tds_deducted: float = Field(default=0, ge=0, description="TDS already deducted")
    advance_tax: float = Field(default=0, ge=0, description="Advance tax paid")

    @validator('section_80c')
    def validate_80c_limit(cls, v):
        """Ensure 80C doesn't exceed limit"""
        return min(v, 150000)

    @validator('section_80d')
    def validate_80d_limit(cls, v):
        """Ensure 80D doesn't exceed limit for individuals"""
        return min(v, 25000)

    @property
    def gross_salary(self) -> float:
        """Calculate gross salary"""
        return (self.basic_salary + self.hra + self.special_allowance + 
                self.other_allowances + self.bonus)

    @property
    def total_income(self) -> float:
        """Calculate total income from all sources"""
        return (self.gross_salary + self.interest_income + 
                self.rental_income + self.capital_gains + self.other_income)

class TaxCalculationRequest(BaseModel):
    """Request model for tax calculation"""
    financial_data: FinancialData
    assessment_year: str = Field(default="2024-25", description="Assessment Year")
    preferred_regime: Optional[TaxRegime] = None
    calculate_both: bool = Field(default=True, description="Calculate both regimes")

class TaxSlabDetail(BaseModel):
    """Individual tax slab calculation detail"""
    min_amount: float = Field(description="Minimum amount for this slab")
    max_amount: Optional[float] = Field(description="Maximum amount for this slab")
    rate: float = Field(description="Tax rate percentage")
    tax_amount: float = Field(description="Tax calculated for this slab")

class RegimeTaxDetails(BaseModel):
    """Detailed tax calculation for a specific regime"""
    regime: TaxRegime
    gross_income: float
    taxable_income: float
    total_deductions: float
    tax_before_cess: float
    cess: float = Field(description="4% Health and Education Cess")
    total_tax: float
    tax_slabs: List[TaxSlabDetail] = []
    effective_tax_rate: float = Field(description="Effective tax rate percentage")

    # Payment details
    tds_deducted: float = 0
    advance_tax: float = 0
    refund_or_payable: float = Field(description="Positive = payable, Negative = refund")

class TaxCalculationResponse(BaseModel):
    """Comprehensive tax calculation response"""
    old_regime: RegimeTaxDetails
    new_regime: RegimeTaxDetails
    recommended_regime: TaxRegime
    savings_amount: float = Field(description="Amount saved by choosing recommended regime")
    calculation_timestamp: datetime = Field(default_factory=datetime.now)

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
    confidence_score: float = Field(ge=0, le=1, description="Confidence in extraction accuracy")
    extracted_text: Optional[str] = Field(description="Sample extracted text")
    processing_time: float = Field(description="Processing time in seconds")
    warnings: List[str] = Field(default=[], description="Warnings during extraction")
    suggestions: List[str] = Field(default=[], description="Suggestions for improvement")

class ChatbotRequest(BaseModel):
    """Request model for chatbot queries"""
    message: str = Field(min_length=1, max_length=1000, description="User message")
    context: Optional[Dict[str, Any]] = Field(description="Additional context")
    user_id: Optional[str] = Field(description="User identifier")
    session_id: Optional[str] = Field(description="Session identifier")

class ChatbotResponse(BaseModel):
    """Response model for chatbot powered by Groq"""
    response: str = Field(description="AI-generated response")
    confidence: float = Field(ge=0, le=1, description="Response confidence score")
    sources: List[str] = Field(default=[], description="Information sources")
    follow_up_questions: List[str] = Field(default=[], description="Suggested follow-up questions")
    response_time: float = Field(description="Response generation time")

class TaxSavingSuggestion(BaseModel):
    """Tax saving suggestion model"""
    category: str = Field(description="Suggestion category")
    description: str = Field(description="Detailed suggestion description")
    potential_savings: float = Field(ge=0, description="Potential tax savings amount")
    implementation_difficulty: str = Field(description="Easy, Medium, or Hard")
    priority: int = Field(ge=1, le=5, description="Priority level (1=highest)")
    details: str = Field(description="Additional implementation details")

class ErrorResponse(BaseModel):
    """Standard error response model"""
    error: bool = True
    message: str
    details: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)

class HealthCheckResponse(BaseModel):
    """Health check response model"""
    status: str
    version: str
    timestamp: datetime
    services: Dict[str, bool]
    features: List[str]

# Additional utility models
class TaxSlabInfo(BaseModel):
    """Tax slab information"""
    regime: str
    assessment_year: str
    slabs: List[Dict[str, Any]]

class UserProfile(BaseModel):
    """User profile for personalized recommendations"""
    user_id: str
    name: Optional[str] = None
    email: Optional[str] = None
    preferred_regime: Optional[TaxRegime] = None
    risk_tolerance: str = Field(default="medium", description="low, medium, high")
    investment_experience: str = Field(default="beginner", description="beginner, intermediate, expert")
    financial_goals: List[str] = Field(default=[], description="List of financial goals")

class TaxPlanningRecommendation(BaseModel):
    """Comprehensive tax planning recommendation"""
    current_tax_liability: float
    optimized_tax_liability: float
    total_savings_potential: float
    recommendations: List[TaxSavingSuggestion]
    implementation_timeline: str
    risk_assessment: str

class DocumentType(str, Enum):
    """Supported document types"""
    FORM16 = "form16"
    SALARY_SLIP = "salary_slip"
    BANK_STATEMENT = "bank_statement"
    INVESTMENT_PROOF = "investment_proof"
    RENT_RECEIPT = "rent_receipt"
    LOAN_CERTIFICATE = "loan_certificate"
    OTHER = "other"

class UploadedDocument(BaseModel):
    """Uploaded document information"""
    document_id: str
    filename: str
    document_type: DocumentType
    upload_timestamp: datetime
    file_size: int
    confidence_score: float
    extracted_data: Optional[FinancialData] = None
    processing_status: str = Field(default="pending")  # pending, processing, completed, failed
