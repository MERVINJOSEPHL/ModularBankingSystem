# smart-bank-modular/controller/kyc_controller.py (NEW FILE)

from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.orm import Session
import uuid
from models.kyc_models import (
    KYCSubmissionRequest, KYCSubmissionResponse, 
    KYCListResponse, KYCReviewRequest, KYCDocument
)
from services import kyc_services as kyc_service
from utility.database import get_db 
from utility.auth import CUSTOMER_AUTH, ADMIN_AUTH
from utility.logging import setup_logger

router = APIRouter(tags=["KYC Management"])
logger = setup_logger(__name__)


@router.post(
    "/customer/submit",
    response_model=KYCSubmissionResponse,
    status_code=status.HTTP_200_OK,
    summary="Submit initial KYC registration details (Name, Phone, Address)"
)
def submit_kyc(
    request: KYCSubmissionRequest,
    db: Session = Depends(get_db),
    customer_id: str = Depends(CUSTOMER_AUTH) # Requires CUSTOMER role
):
    """
    Submits the required customer details. Sets the status implicitly to 'In Progress'.
    """
    try:
        new_status = kyc_service.submit_kyc_details(db, customer_id, request)
        return KYCSubmissionResponse(
            kyc_status=new_status,
            message=f"KYC details submitted successfully. Status: {new_status.value}. Awaiting Admin review."
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.critical(f"Unhandled error during KYC submission for {customer_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred.")



@router.get(
    "/admin/for-review",
    response_model=KYCListResponse,
    summary="List all KYC applications awaiting review ('In Progress')"
)
def list_kyc_for_review_admin(
    db: Session = Depends(get_db),
    admin_id: str = Depends(ADMIN_AUTH)
):
    """
    Retrieves a list of all customer KYC applications with status 'In Progress' 
    (data submitted but not yet approved).
    """
    kyc_records = kyc_service.get_kyc_for_review(db)
    
    if not kyc_records:
        return KYCListResponse(kyc_records=[], message="No KYC applications awaiting review.")
        
    return KYCListResponse(kyc_records=kyc_records)


@router.post(
    "/admin/{customer_id}/review",
    response_model=KYCDocument,
    summary="Approve or Revert a KYC application"
)
def review_kyc(
    customer_id: uuid.UUID,
    request: KYCReviewRequest,
    db: Session = Depends(get_db),
    admin_id: str = Depends(ADMIN_AUTH) 
):
    """
    Allows an Admin to change the KYC status:
    - Set is_approved=True: Sets kyc_status=True (Approved).
    - Set is_approved=False: Sets kyc_status=False (Revert to In Progress/Pending).
    """
    try:
        updated_kyc = kyc_service.review_kyc_application(db, customer_id, request)
        return updated_kyc
    except HTTPException:
        raise
    except Exception as e:
        logger.critical(f"Unhandled error during admin review of KYC for {customer_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred during review.")