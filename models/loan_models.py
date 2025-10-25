# smart-bank-modular/models/loan_models.py

from pydantic import BaseModel, Field, field_validator
from typing import Optional
from enum import Enum
import uuid
from decimal import Decimal

# --- Enums ---

class LoanStatus(str, Enum):
    """Defines the possible states of a loan application."""
    PENDING = "Pending"
    APPROVED = "Approved"
    REJECTED = "Rejected"
    ACTIVE = "Active"
    PAID = "Paid"

# --- Customer Request Models ---

class EMICalculationRequest(BaseModel):
    """Input for calculating the estimated EMI."""
    principal: Decimal = Field(..., gt=Decimal(0), description="Loan amount (P)")
    annual_rate: Decimal = Field(..., gt=Decimal(0), description="Annual interest rate (R)")
    tenure_years: int = Field(..., gt=0, description="Loan tenure in years (N)")

class EMICalculationResponse(BaseModel):
    """Output for the estimated EMI."""
    monthly_emi: Decimal = Field(..., description="Calculated monthly EMI")
    total_interest: Decimal = Field(..., description="Total interest paid over the tenure")
    total_payment: Decimal = Field(..., description="Total amount paid (Principal + Interest)")

class LoanApplicationRequest(BaseModel):
    """Input for submitting a formal loan application."""
    loan_type: str = Field(..., description="E.g., Home, Personal, Auto")
    loan_amount: Decimal = Field(..., gt=Decimal(0))
    tenure_months: int = Field(..., gt=0)
    
    @field_validator('loan_type')
    @classmethod
    def check_loan_type(cls, v):
        if not v.strip():
            raise ValueError('Loan type cannot be empty.')
        return v

class LoanApplicationResponse(BaseModel):
    """Response after a successful loan application submission."""
    loan_id: uuid.UUID
    status: LoanStatus
    message: str

# --- Admin Request Models ---

class LoanApprovalRequest(BaseModel):
    """Input for admin to approve or reject a loan."""
    loan_status: LoanStatus = Field(..., description="Must be 'Approved' or 'Rejected'")
    emi_amount: Optional[Decimal] = Field(None, description="Final approved EMI, required for 'Approved'")
    
    @field_validator('loan_status')
    @classmethod
    def check_status(cls, v):
        if v not in [LoanStatus.APPROVED, LoanStatus.REJECTED]:
            raise ValueError("Loan status must be 'Approved' or 'Rejected' for this action.")
        return v
    
    @field_validator('emi_amount')
    @classmethod
    def check_emi_for_approval(cls, v, info):
        if info.data.get('loan_status') == LoanStatus.APPROVED and (v is None or v <= Decimal(0)):
            raise ValueError("EMI amount must be provided and positive when approving a loan.")
        return v
    
class LoanDetailResponse(BaseModel):
    """Detailed response model for a loan record."""
    loan_id: uuid.UUID
    customer_id: uuid.UUID
    loan_type: str
    loan_amount: Decimal
    tenure_months: int
    emi_amount: Optional[Decimal]
    loan_status: LoanStatus
    
    class Config:
        from_attributes = True

class LoanStatusListResponse(BaseModel):
    """Model for listing multiple loans."""
    loans: list[LoanDetailResponse]