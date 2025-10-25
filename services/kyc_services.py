# smart-bank-modular/services/kyc_services.py (NEW FILE)

from sqlalchemy.orm import Session
from fastapi import HTTPException, status
import uuid
from typing import List, Optional

from models.orm_models import Customer
from models.kyc_models import (
    KYCSubmissionRequest, KYCReviewRequest, 
    DerivedKYCStatus, KYCDocument
)
from utility.logging import setup_logger

logger = setup_logger(__name__)

def _get_derived_kyc_status(customer: Customer) -> DerivedKYCStatus:
    """Derives the logical KYC status from ORM fields."""
    if customer.kyc_status is True:
        return DerivedKYCStatus.APPROVED
    elif customer.name is not None and customer.name.strip() != "":
        return DerivedKYCStatus.IN_PROGRESS
    else:
        return DerivedKYCStatus.PENDING

# --- Customer Submission Logic ---

def submit_kyc_details(db: Session, customer_id: str, request: KYCSubmissionRequest) -> DerivedKYCStatus:
    """
    Updates the customer's profile with KYC details and implicitly sets status to 'In Progress'.
    """
    customer = db.query(Customer).filter(Customer.customer_id == customer_id).first()
    
    if not customer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer profile not found.")

    # 1. Block resubmission if already Approved
    if customer.kyc_status is True:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="KYC is already Approved. No resubmission is required."
        )

    # 2. Update fields
    customer.name = request.name
    customer.phone_number = request.phone_number
    customer.address = request.address
    # kyc_status remains False, which the derived status maps to 'In Progress'

    try:
        db.commit()
        db.refresh(customer)
        new_status = _get_derived_kyc_status(customer)
        logger.info(f"KYC details submitted for customer {customer_id}. Status: {new_status.value}.")
        return new_status
    except Exception as e:
        db.rollback()
        logger.error(f"Database error during KYC submission for {customer_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error during KYC submission."
        )

# --- Admin Review Logic ---

def get_kyc_for_review(db: Session) -> List[KYCDocument]:
    """
    Retrieves customers who have submitted data (name is not null) but are not yet approved (kyc_status=False).
    This corresponds to the 'In Progress' state.
    """
    # Filter for customers where data is present AND kyc_status is False
    in_progress_customers = (
        db.query(Customer)
        .filter(Customer.kyc_status == False)
        .filter(Customer.name.isnot(None))
        .all()
    )
    
    # Map ORM objects to Pydantic response models using the derived status
    kyc_records = []
    for customer in in_progress_customers:
        kyc_records.append(KYCDocument(
            customer_id=uuid.UUID(customer.customer_id),
            name=customer.name,
            phone_number=customer.phone_number,
            address=customer.address,
            kyc_status=_get_derived_kyc_status(customer)
        ))
        
    return kyc_records


def review_kyc_application(db: Session, customer_id: uuid.UUID, request: KYCReviewRequest) -> KYCDocument:
    """
    Admin action to approve (True) or revert (False) a KYC application.
    If False is passed, it reverts to the 'In Progress'/'Pending' state.
    """
    customer = db.query(Customer).filter(Customer.customer_id == str(customer_id)).first()
    
    if not customer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer profile not found.")
        
    current_status = _get_derived_kyc_status(customer)
    
    if current_status == DerivedKYCStatus.APPROVED and request.is_approved is True:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="KYC is already Approved."
        )

    if current_status == DerivedKYCStatus.PENDING and request.is_approved is False:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="KYC details have not been submitted yet (Pending)."
        )

    # Update KYC status (True=Approved, False=Revert to In Progress)
    customer.kyc_status = request.is_approved
    
    if customer.kyc_status is False:
        # Rejection means reverting the boolean status. The data stays.
        message = f"KYC for customer {customer_id} reverted to In Progress/Pending."
    else:
        message = f"KYC for customer {customer_id} set to Approved."
    
    try:
        db.commit()
        db.refresh(customer)
        logger.info(message)
        # Return the updated customer detail
        return KYCDocument(
            customer_id=uuid.UUID(customer.customer_id),
            name=customer.name,
            phone_number=customer.phone_number,
            address=customer.address,
            kyc_status=_get_derived_kyc_status(customer)
        )
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to update KYC status for {customer_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error during KYC review update."
        )