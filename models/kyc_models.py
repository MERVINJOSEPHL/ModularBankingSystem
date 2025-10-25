# smart-bank-modular/models/kyc_models.py (NEW FILE)

from pydantic import BaseModel, Field, field_validator
from enum import Enum
import uuid
from typing import List, Optional

class DerivedKYCStatus(str, Enum):
    """Derived states based on boolean kyc_status and data presence."""
    PENDING = "Pending"
    IN_PROGRESS = "In Progress"
    APPROVED = "Approved"


class KYCSubmissionRequest(BaseModel):
    """Customer input for submitting KYC details."""
    name: str = Field(..., max_length=255, description="Full legal name.")
    phone_number: str = Field(..., max_length=20, description="Contact phone number.")
    address: str = Field(..., description="Full residential address.")

class KYCSubmissionResponse(BaseModel):
    """Response after a successful KYC submission."""
    kyc_status: DerivedKYCStatus
    message: str


class KYCDocument(BaseModel):
    """Model for listing a customer's basic KYC information."""
    customer_id: uuid.UUID
    name: str
    phone_number: str
    address: str
    kyc_status: DerivedKYCStatus
    
    class Config:
        from_attributes = True 

class KYCListResponse(BaseModel):
    """Model for Admin to list multiple KYC records."""
    kyc_records: List[KYCDocument]
    

class KYCReviewRequest(BaseModel):
    """Admin input for approving or rejecting a KYC application."""
    is_approved: bool = Field(..., description="Set to True for Approval, False for Rejection/Revert.")