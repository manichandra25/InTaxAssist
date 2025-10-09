import pytest
import asyncio
from fastapi.testclient import TestClient
from backend.main import app
from backend.models import FinancialData, TaxCalculationRequest

# Test client
client = TestClient(app)

def test_health_check():
    """Test the health check endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    assert "Tax Filing Backend API" in response.json()["message"]

def test_tax_calculation():
    """Test tax calculation endpoint"""
    financial_data = {
        "basic_salary": 600000,
        "hra": 240000,
        "section_80c": 150000,
        "section_80d": 25000,
        "tds_deducted": 45000
    }

    request_data = {
        "financial_data": financial_data,
        "assessment_year": "2024-25"
    }

    response = client.post("/api/calculate-tax", json=request_data)
    assert response.status_code == 200

    result = response.json()
    assert "old_regime" in result
    assert "new_regime" in result
    assert "recommended_regime" in result

def test_tax_slabs():
    """Test tax slabs endpoint"""
    response = client.get("/api/tax-slabs/old?assessment_year=2024-25")
    assert response.status_code == 200

    result = response.json()
    assert result["regime"] == "old"
    assert "slabs" in result

def test_regime_comparison():
    """Test regime comparison endpoint"""
    financial_data = {
        "basic_salary": 800000,
        "section_80c": 100000,
        "section_80d": 20000
    }

    request_data = {
        "financial_data": financial_data,
        "assessment_year": "2024-25"
    }

    response = client.post("/api/compare-regimes", json=request_data)
    assert response.status_code == 200

    result = response.json()
    assert "old_regime_tax" in result
    assert "new_regime_tax" in result
    assert "recommended" in result

def test_chatbot_endpoint():
    """Test chatbot endpoint"""
    request_data = {
        "message": "What is Section 80C?",
        "user_id": "test_user"
    }

    response = client.post("/api/chatbot", json=request_data)
    assert response.status_code == 200

    result = response.json()
    assert "response" in result
    assert "confidence" in result
    assert len(result["response"]) > 0

@pytest.mark.asyncio
async def test_financial_data_validation():
    """Test FinancialData model validation"""
    # Test valid data
    data = FinancialData(
        basic_salary=500000,
        section_80c=160000  # Over limit
    )

    # Should clamp 80C to maximum limit
    assert data.section_80c == 150000

    # Test property calculations
    assert data.gross_salary == 500000
    assert data.total_income == 500000

if __name__ == "__main__":
    pytest.main([__file__])
