# smart-bank-modular/controller/loan_controller.py

from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.orm import Session
from decimal import Decimal
import uuid
from typing import Optional
from models.loan_models import (
    EMICalculationRequest, EMICalculationResponse, 
    LoanApplicationRequest, LoanApplicationResponse,
    LoanApprovalRequest, LoanDetailResponse, LoanStatusListResponse,
    LoanStatus # Import the Enum for use in query parameter
)
from services import loan_services as loan_service
from utility.database import get_db
from utility.auth import CUSTOMER_AUTH, ADMIN_AUTH # Import our new security dependencies
from utility.logging import setup_logger

router = APIRouter(tags=["Loan Management"])
logger = setup_logger(__name__)

# =================================================================
#                         CUSTOMER ROUTES
# =================================================================

@router.post(
    "/customer/emi-calc", 
    response_model=EMICalculationResponse,
    status_code=status.HTTP_200_OK,
    summary="Calculate Estimated Monthly EMI"
)
def calculate_emi(request: EMICalculationRequest):
    """
    Allows a user to calculate the estimated Monthly EMI, Total Interest, 
    and Total Payment based on principal, annual rate, and tenure.
    """
    try:
        emi, interest, total = loan_service.calculate_emi_amount(
            request.principal, request.annual_rate, request.tenure_years
        )
        return EMICalculationResponse(
            monthly_emi=emi, 
            total_interest=interest, 
            total_payment=total
        )
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve)
        )

@router.post(
    "/customer/apply",
    response_model=LoanApplicationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit a new loan application"
)
def apply_loan(
    request: LoanApplicationRequest, 
    db: Session = Depends(get_db),
    customer_id: str = Depends(CUSTOMER_AUTH) # Requires CUSTOMER role and extracts user_id
):
    """
    Submits a new loan application under the currently logged-in customer's ID.
    """
    try:
        loan_id = loan_service.apply_for_loan(db, customer_id, request)
        return LoanApplicationResponse(
            loan_id=loan_id,
            status=LoanStatus.PENDING,
            message="Loan application submitted successfully. Pending Admin review."
        )
    except HTTPException:
        # Re-raise explicit HTTPExceptions from the service (e.g., 403 KYC)
        raise
    except Exception as e:
        logger.critical(f"Unhandled error during loan application for {customer_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred.")


@router.get(
    "/customer/my-loans",
    response_model=LoanStatusListResponse,
    summary="List customer's loans with optional status filter"
)
def list_customer_loans(
    db: Session = Depends(get_db),
    status_filter: Optional[LoanStatus] = None, # Optional query parameter
    customer_id: str = Depends(CUSTOMER_AUTH) # Requires CUSTOMER role
):
    """
    Lists all loans associated with the logged-in customer, optionally filtered by status.
    """
    loans = loan_service.get_customer_loans_by_status(db, customer_id, status_filter)
    
    if not loans:
        return LoanStatusListResponse(loans=[], message="No loans found matching the criteria.")
        
    return LoanStatusListResponse(loans=loans)


# =================================================================
#                            ADMIN ROUTES
# =================================================================

@router.get(
    "/admin/pending-loans",
    response_model=LoanStatusListResponse,
    summary="List all pending loan applications"
)
def list_pending_loans_admin(
    db: Session = Depends(get_db),
    admin_id: str = Depends(ADMIN_AUTH) # Requires ADMIN role
):
    """
    Retrieves a list of all loan applications awaiting review.
    """
    loans = loan_service.get_pending_loans(db)
    return LoanStatusListResponse(loans=loans)

@router.post(
    "/admin/{loan_id}/review",
    response_model=LoanDetailResponse,
    summary="Approve or reject a loan application"
)
def review_loan(
    loan_id: uuid.UUID,
    request: LoanApprovalRequest,
    db: Session = Depends(get_db),
    admin_id: str = Depends(ADMIN_AUTH) # Requires ADMIN role
):
    """
    Allows an Admin to change the status of a pending loan to 'Approved' or 'Rejected'. 
    If approved, funds are notionally disbursed.
    """
    try:
        updated_loan = loan_service.review_loan_application(db, loan_id, request)
        return updated_loan
    except HTTPException:
        raise
    except Exception as e:
        logger.critical(f"Unhandled error during admin review of loan {loan_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred during review.")