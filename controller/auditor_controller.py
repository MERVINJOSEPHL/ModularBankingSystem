# smart-bank-modular/controller/auditor_controller.py (NEW FILE)

from fastapi import APIRouter, status, Depends, HTTPException
from sqlalchemy.orm import Session
from models.audit_models import AuditLogResponse
from services import auditor_services as auditor_service
from utility.database import get_db
from utility.auth import AUDITOR_AUTH
from utility.logging import setup_logger

router = APIRouter(tags=["Auditor (Secure Audit Logs)"])
logger = setup_logger(__name__)

@router.get(
    "/audit-logs",
    response_model=AuditLogResponse,
    summary="Retrieve the most recent system audit logs"
)
def fetch_audit_logs(
    db: Session = Depends(get_db),
    # Requires the AUDITOR role
    auditor_id: str = Depends(AUDITOR_AUTH) 
):
    """
    Retrieves a list of recent critical system activity logs, accessible only by users with the 'auditor' role.
    """
    try:
        logs = auditor_service.get_recent_audit_logs(db)
        
        return AuditLogResponse(
            logs=logs,
            total_count=len(logs)
        )
    except Exception as e:
        logger.critical(f"Unhandled error fetching audit logs for auditor {auditor_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while fetching audit logs."
        )