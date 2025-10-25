# smart-bank-modular/services/loan_service.py

from sqlalchemy.orm import Session, joinedload
from sqlalchemy.sql import func
from fastapi import HTTPException, status
from decimal import Decimal, ROUND_HALF_UP, getcontext
from datetime import datetime
import uuid
from typing import List,Optional

from models.orm_models import Loan, Customer, Account, User # Ensure these are imported
from models.loan_models import (
    EMICalculationRequest, LoanApplicationRequest, LoanDetailResponse, 
    LoanStatus, LoanApprovalRequest
)
from utility.logging import setup_logger 

logger = setup_logger(__name__)

# Set Decimal precision high for financial calculations
getcontext().prec = 28

# --- EMI Calculation Logic ---

def calculate_emi_amount(principal: Decimal, annual_rate: Decimal, tenure_years: int) -> Decimal:
    """
    Calculates the monthly EMI using the formula:
    E = P * R * (1 + R)^N / ((1 + R)^N - 1)
    Where:
    P = Principal
    R = Monthly interest rate (Annual Rate / 1200)
    N = Total number of months (Tenure years * 12)
    """
    if annual_rate <= 0:
        # Simple non-interest calculation for 0%
        monthly_emi = principal / Decimal(tenure_years * 12)
        total_interest = Decimal(0)
    else:
        # R (Monthly Rate as a decimal)
        monthly_rate = annual_rate / Decimal(1200) 
        
        # N (Total number of payments/months)
        num_months = tenure_years * 12
        
        # (1 + R)^N
        rate_power_n = (Decimal(1) + monthly_rate) ** num_months
        
        # E = P * R * (1 + R)^N / ((1 + R)^N - 1)
        numerator = principal * monthly_rate * rate_power_n
        denominator = rate_power_n - Decimal(1)
        
        # Handle division by zero edge case (shouldn't happen with positive rate)
        if denominator == 0:
            raise ValueError("Invalid rate or tenure for EMI calculation.")
            
        monthly_emi = numerator / denominator

        # Calculate total interest (for the response model)
        total_payment = monthly_emi * Decimal(num_months)
        total_interest = total_payment - principal

    # Round EMI to two decimal places
    monthly_emi_rounded = monthly_emi.quantize(Decimal('.01'), rounding=ROUND_HALF_UP)
    total_interest_rounded = total_interest.quantize(Decimal('.01'), rounding=ROUND_HALF_UP)
    total_payment_rounded = (principal + total_interest_rounded).quantize(Decimal('.01'), rounding=ROUND_HALF_UP)
    
    return monthly_emi_rounded, total_interest_rounded, total_payment_rounded



def apply_for_loan(db: Session, customer_id: str, request: LoanApplicationRequest) -> uuid.UUID:
    """
    Creates a new loan application in the 'Pending' status.
    """
    customer = db.query(Customer).filter(Customer.customer_id == customer_id).first()
    if not customer:
        logger.warning(f"Loan application failed: Customer {customer_id} not found.")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer profile not found."
        )


    if not customer.kyc_status: 
        status_detail = "Approved" if customer.kyc_status else "Not Approved"
        logger.warning(f"Loan application blocked: Customer {customer_id} KYC not approved (Status: {status_detail}).")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="KYC not Approved. Cannot apply for loan transactions."
        )
        
    new_loan_id = str(uuid.uuid4())
    db_loan = Loan(
        loan_id=new_loan_id,
        customer_id=customer_id,
        loan_type=request.loan_type,
        loan_amount=request.loan_amount,
        tenure_months=request.tenure_months,
        loan_status=LoanStatus.PENDING.value 
    )
    
    try:
        db.add(db_loan)
        db.commit()
        logger.info(f"New loan application submitted: ID {new_loan_id} by Customer {customer_id}.")
        return uuid.UUID(new_loan_id)
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to submit loan application for {customer_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error during loan submission."
        )


# --- Admin Approval/Rejection Logic ---

def get_pending_loans(db: Session) -> List[LoanDetailResponse]:
    """
    Retrieves all loans currently in 'Pending' status, ordered by application date.
    """
    pending_loans = db.query(Loan).filter(Loan.loan_status == LoanStatus.PENDING.value).all()
    
    # Map ORM objects to Pydantic response models
    return [LoanDetailResponse.from_orm(loan) for loan in pending_loans]


def review_loan_application(db: Session, loan_id: uuid.UUID, request: LoanApprovalRequest) -> LoanDetailResponse:
    """
    Admin action to approve or reject a specific loan application.
    """
    loan = db.query(Loan).filter(Loan.loan_id == str(loan_id)).first()
    
    if not loan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Loan application not found.")
        
    if loan.loan_status != LoanStatus.PENDING.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Loan is already {loan.loan_status}. Cannot review."
        )

    # 1. Update loan status and details
    new_status = request.loan_status.value
    loan.loan_status = new_status
    
    if new_status == LoanStatus.APPROVED.value:
        # Set EMI amount and start date for approved loans
        loan.emi_amount = request.emi_amount
        loan.start_date = datetime.utcnow()
        message = f"Loan {loan_id} approved. EMI set to {request.emi_amount}."
        
        # *** Critical step: Transfer funds (In a real system, this would be a complex transaction) ***
        # Find a primary account for the customer
        account = db.query(Account).filter(Account.customer_id == loan.customer_id).first()
        if not account:
            db.rollback()
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Customer has no associated account for fund transfer.")
        
        account.current_balance += loan.loan_amount
        logger.info(f"Funds {loan.loan_amount} disbursed to account {account.account_number}.")
        
    elif new_status == LoanStatus.REJECTED.value:
        loan.emi_amount = None
        loan.start_date = None
        message = f"Loan {loan_id} rejected."
        
    try:
        db.commit()
        logger.info(message)
        # Return the updated loan detail
        return LoanDetailResponse.from_orm(loan)
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to update loan status for {loan_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error during loan review update."
        )


# --- Customer Listing Logic ---

def get_customer_loans_by_status(db: Session, customer_id: str, status_filter: Optional[LoanStatus]) -> List[LoanDetailResponse]:
    """
    Retrieves a customer's loans, optionally filtered by status.
    """
    query = db.query(Loan).filter(Loan.customer_id == customer_id)
    
    if status_filter:
        query = query.filter(Loan.loan_status == status_filter.value)
        
    customer_loans = query.all()
    
    # Map ORM objects to Pydantic response models
    return [LoanDetailResponse.from_orm(loan) for loan in customer_loans]