# smart-bank-modular/services/auditor_services.py (NEW FILE)

from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List

from models.orm_models import AuditLog
from models.audit_models import AuditLogEntry 
from utility.logging import setup_logger

logger = setup_logger(__name__)

def get_recent_audit_logs(db: Session, limit: int = 100) -> List[AuditLogEntry]:
    """
    Retrieves the most recent audit logs. Only accessible by the Auditor role.
    """
    try:
        logs = (
            db.query(AuditLog)
            .order_by(desc(AuditLog.timestamp))
            .limit(limit)
            .all()
        )
        
        return [AuditLogEntry.from_orm(log) for log in logs]
        
    except Exception as e:
        logger.error(f"Error fetching audit logs: {e}")
        return []