# smart-bank-modular/models/audit_models.py (NEW FILE)

from pydantic import BaseModel
from typing import Optional, Dict, List
from datetime import datetime
import uuid

class AuditLogEntry(BaseModel):
    """Pydantic model for presenting audit log data."""
    log_id: int
    user_id: Optional[uuid.UUID] 
    timestamp: datetime
    action: str
    ip_address: Optional[str]
    details: Dict
    
    class Config:
        from_attributes = True
        json_encoders = {
            uuid.UUID: str
        }

class AuditLogResponse(BaseModel):
    """Response model for fetching a list of audit logs."""
    logs: List[AuditLogEntry]
    total_count: int