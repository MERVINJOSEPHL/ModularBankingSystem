# smart-bank-modular/services/audit_services.py (NEW FILE)

from sqlalchemy.orm import Session
from datetime import datetime
import json
from typing import Optional, Dict

from models.orm_models import AuditLog
from utility.logging import setup_logger

logger = setup_logger(__name__)

def create_audit_log(
    db: Session, 
    user_id: Optional[str], 
    action: str, 
    ip_address: Optional[str] = None, 
    details: Optional[Dict] = None
):
    """
    Creates and commits a new entry to the AuditLog table.
    NOTE: This runs outside the main transaction to ensure the log is created even if the operation fails.
    """
    try:
        # Convert user_id to string if it's a UUID object
        user_id_str = str(user_id) if user_id else None
        
        db_log = AuditLog(
            user_id=user_id_str,
            action=action,
            ip_address=ip_address,
            # SQLAlchemy handles JSONB automatically, but ensure details is serializable
            details=details if details is not None else {}
        )
        
        # Use a separate session/commit if necessary, but here we rely on the caller's session 
        # and commit it immediately so the log exists independent of the main operation's rollback.
        db.add(db_log)
        db.commit()
        
    except Exception as e:
        db.rollback()
        logger.error(f"FATAL: Failed to create audit log for action '{action}': {e}")