# Create tax calculator service
tax_calculator_content = '''import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from models import (
    FinancialData, RegimeTaxDetails, TaxCalculationResponse, 
    TaxRegimeComparison, TaxSavingSuggestion, TaxSlabDetail, TaxRegime
)
from config import TAX_SLABS, DEDUCTION_LIMITS

logger = logging.getLogger(__name__)

class TaxCalculatorService:
    """Service for comprehensive tax calculations"""
    
    def __init__(self):
        self.current_year = "2024-25"
        self.cess_rate = 0.04  # 4% Health and Education Cess
        
    def calculate_comprehensive_tax(
        self, 
        financial_data: FinancialData, 
        assessment_year: str = "2024-25"
    ) -> TaxCalculationResponse:
        """Calculate tax for both regimes and provide comparison"""
        
        try:
            # Calculate old regime tax
            old_regime_details = self._calculate_regime_tax(
                financial_data, TaxRegime.OLD, assessment_year
            )
            
            # Calculate new regime tax
            new_regime_details = self._calculate_regime_tax(
                financial_data, TaxRegime.NEW, assessment_year
            )
            
            # Determine recommendation
            if old_regime_details.total_tax <= new_regime_details.total_tax:
                recommended_regime = TaxRegime.OLD
                savings_amount = new_regime_details.total_tax - old_regime_details.total_tax
            else:
                recommended_regime = TaxRegime.NEW
                savings_amount = old_regime_details.total_tax - new_regime_details.total_tax
            
            return TaxCalculationResponse(
                old_regime=old_regime_details,
                new_regime=new_regime_details,
                recommended_regime=recommended_regime,
                savings_amount=savings_amount
            )
            
        except Exception as e:
            logger.error(f"Error in comprehensive tax calculation: {e}")
            raise

    def _calculate_regime_tax(
        self, 
        financial_data: FinancialData, 
        regime: TaxRegime,
        assessment_year: str
    ) -> RegimeTaxDetails:
        """Calculate tax for specific regime"""
        
        # Calculate gross income
        gross_income = financial_data.total_income
        
        # Calculate deductions based on regime
        if regime == TaxRegime.OLD:
            total_deductions = self._calculate_old_regime_deductions(financial_data)
        else:
            total_deductions = self._calculate_new_regime_deductions(financial_data)
        
        # Calculate taxable income
        taxable_income = max(0, gross_income - total_deductions)
        
        # Get tax slabs for the regime
        tax_slabs = self.get_tax_slabs(regime.value, assessment_year)
        
        # Calculate tax using slabs
        tax_calculation = self._calculate_slab_tax(taxable_income, tax_slabs)
        
        # Calculate cess (4% of income tax)
        cess = tax_calculation["total_tax"] * self.cess_rate
        
        # Total tax including cess
        total_tax = tax_calculation["total_tax"] + cess
        
        # Calculate effective tax rate
        effective_tax_rate = (total_tax / gross_income * 100) if gross_income > 0 else 0
        
        # Calculate refund/payable
        taxes_paid = financial_data.tds_deducted + financial_data.advance_tax
        refund_or_payable = total_tax - taxes_paid
        
        return RegimeTaxDetails(
            regime=regime,
            gross_income=gross_income,
            taxable_income=taxable_income,
            total_deductions=total_deductions,
            tax_before_cess=tax_calculation["total_tax"],
            cess=cess,
            total_tax=total_tax,
            tax_slabs=tax_calculation["slab_details"],
            effective_tax_rate=round(effective_tax_rate, 2),
            tds_deducted=financial_data.tds_deducted,
            advance_tax=financial_data.advance_tax,
            refund_or_payable=refund_or_payable
        )

    def _calculate_old_regime_deductions(self, financial_data: FinancialData) -> float:
        """Calculate total deductions for old regime"""
        
        deductions = 0
        
        # Standard deduction
        deductions += financial_data.standard_deduction
        
        # Section 80C (max 1.5 lakh)
        deductions += min(financial_data.section_80c, DEDUCTION_LIMITS["section_80c"])
        
        # Section 80D (medical insurance)
        deductions += min(financial_data.section_80d, DEDUCTION_LIMITS["section_80d"]["individual"])
        
        # Section 80G (donations)
        deductions += financial_data.section_80g
        
        # Section 24 (home loan interest)
        deductions += financial_data.section_24
        
        # Section 80CCD(1B) - NPS additional deduction (max 50k)
        deductions += min(financial_data.section_80ccd1b, DEDUCTION_LIMITS["section_80ccd1b"])
        
        # Section 80E (education loan interest)
        deductions += financial_data.section_80e
        
        # Section 80TTA (interest on savings account)
        deductions += min(financial_data.section_80tta, DEDUCTION_LIMITS["section_80tta"])
        
        # Professional tax
        deductions += financial_data.professional_tax
        
        return deductions

    def _calculate_new_regime_deductions(self, financial_data: FinancialData) -> float:
        """Calculate total deductions for new regime (very limited)"""
        
        deductions = 0
        
        # Standard deduction (available in new regime)
        deductions += financial_data.standard_deduction
        
        # Professional tax
        deductions += financial_data.professional_tax
        
        return deductions

    def _calculate_slab_tax(self, taxable_income: float, tax_slabs: List[Dict]) -> Dict:
        """Calculate tax using progressive slabs"""
        
        total_tax = 0
        slab_details = []
        remaining_income = taxable_income
        
        for slab in tax_slabs:
            min_amount = slab["min"]
            max_amount = slab["max"] if slab["max"] else float('inf')
            rate = slab["rate"]
            
            if remaining_income <= 0:
                break
            
            # Calculate taxable amount in this slab
            slab_range = max_amount - min_amount if max_amount != float('inf') else remaining_income
            slab_taxable = min(remaining_income, slab_range)
            
            # Calculate tax for this slab
            slab_tax = slab_taxable * (rate / 100)
            total_tax += slab_tax
            
            # Add to slab details
            slab_details.append(TaxSlabDetail(
                min_amount=min_amount,
                max_amount=max_amount if max_amount != float('inf') else None,
                rate=rate,
                tax_amount=slab_tax
            ))
            
            remaining_income -= slab_taxable
            
            if remaining_income <= 0 or max_amount == float('inf'):
                break
        
        return {
            "total_tax": total_tax,
            "slab_details": slab_details
        }

    def get_tax_slabs(self, regime: str, assessment_year: str = "2024-25") -> List[Dict]:
        """Get tax slabs for specified regime and year"""
        
        try:
            return TAX_SLABS[assessment_year][regime]
        except KeyError:
            logger.warning(f"Tax slabs not found for {regime} regime in {assessment_year}")
            # Return current year slabs as fallback
            return TAX_SLABS["2024-25"][regime]

    def compare_regimes(
        self, 
        financial_data: FinancialData, 
        assessment_year: str = "2024-25"
    ) -> TaxRegimeComparison:
        """Compare old vs new tax regime"""
        
        try:
            # Calculate comprehensive tax
            result = self.calculate_comprehensive_tax(financial_data, assessment_year)
            
            old_tax = result.old_regime.total_tax
            new_tax = result.new_regime.total_tax
            difference = abs(old_tax - new_tax)
            
            # Determine recommendation and reason
            if old_tax < new_tax:
                recommended = TaxRegime.OLD
                reason = f"Old regime saves ₹{difference:,.0f} due to available deductions"
            elif new_tax < old_tax:
                recommended = TaxRegime.NEW
                reason = f"New regime saves ₹{difference:,.0f} due to lower tax rates"
            else:
                recommended = TaxRegime.OLD  # Default to old if equal
                reason = "Both regimes result in similar tax liability"
            
            # Create detailed breakdown
            breakdown = {
                "old_regime": {
                    "gross_income": result.old_regime.gross_income,
                    "total_deductions": result.old_regime.total_deductions,
                    "taxable_income": result.old_regime.taxable_income,
                    "tax_liability": result.old_regime.total_tax,
                    "effective_rate": result.old_regime.effective_tax_rate
                },
                "new_regime": {
                    "gross_income": result.new_regime.gross_income,
                    "total_deductions": result.new_regime.total_deductions,
                    "taxable_income": result.new_regime.taxable_income,
                    "tax_liability": result.new_regime.total_tax,
                    "effective_rate": result.new_regime.effective_tax_rate
                }
            }
            
            return TaxRegimeComparison(
                old_regime_tax=old_tax,
                new_regime_tax=new_tax,
                difference=difference,
                recommended=recommended,
                reason=reason,
                breakdown=breakdown
            )
            
        except Exception as e:
            logger.error(f"Error comparing regimes: {e}")
            raise

    def get_tax_saving_suggestions(
        self, 
        income: float, 
        current_deductions: Dict[str, float],
        regime: str = "old"
    ) -> List[TaxSavingSuggestion]:
        """Provide personalized tax saving suggestions"""
        
        suggestions = []
        
        if regime == "old":
            # Section 80C suggestions
            current_80c = current_deductions.get("section_80c", 0)
            if current_80c < DEDUCTION_LIMITS["section_80c"]:
                remaining = DEDUCTION_LIMITS["section_80c"] - current_80c
                tax_saved = remaining * 0.30  # Assuming 30% tax bracket
                
                suggestions.append(TaxSavingSuggestion(
                    category="Section 80C Investment",
                    description=f"Invest ₹{remaining:,.0f} more in 80C instruments (PPF, ELSS, NSC, etc.)",
                    potential_savings=tax_saved,
                    implementation_difficulty="Easy",
                    priority=1,
                    details="Popular options: PPF (15-year lock-in), ELSS (3-year lock-in), NSC (5-year)"
                ))
            
            # Section 80D suggestions
            current_80d = current_deductions.get("section_80d", 0)
            if current_80d < DEDUCTION_LIMITS["section_80d"]["individual"]:
                remaining = DEDUCTION_LIMITS["section_80d"]["individual"] - current_80d
                tax_saved = remaining * 0.30
                
                suggestions.append(TaxSavingSuggestion(
                    category="Health Insurance (80D)",
                    description=f"Increase health insurance premium by ₹{remaining:,.0f}",
                    potential_savings=tax_saved,
                    implementation_difficulty="Easy",
                    priority=2,
                    details="Consider family floater plans or top-up insurance for better coverage"
                ))
            
            # NPS suggestions
            current_nps = current_deductions.get("section_80ccd1b", 0)
            if current_nps < DEDUCTION_LIMITS["section_80ccd1b"]:
                remaining = DEDUCTION_LIMITS["section_80ccd1b"] - current_nps
                tax_saved = remaining * 0.30
                
                suggestions.append(TaxSavingSuggestion(
                    category="NPS Investment (80CCD1B)",
                    description=f"Additional NPS contribution of ₹{remaining:,.0f}",
                    potential_savings=tax_saved,
                    implementation_difficulty="Medium",
                    priority=3,
                    details="Long-term retirement planning with tax benefits. Lock-in till 60 years."
                ))
        
        else:  # New regime
            suggestions.append(TaxSavingSuggestion(
                category="Regime Comparison",
                description="Compare with old regime if you have significant deductions",
                potential_savings=0,
                implementation_difficulty="Easy",
                priority=1,
                details="New regime has lower rates but limited deductions. Compare annually."
            ))
        
        # Sort by priority
        suggestions.sort(key=lambda x: x.priority)
        
        return suggestions
'''

# Write tax calculator service
with open("tax-filing-system/backend/services/tax_calculator.py", "w", encoding="utf-8") as f:
    f.write(tax_calculator_content)

print("Created services/tax_calculator.py - Tax calculation service")