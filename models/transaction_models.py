# smart-bank-modular/models/transaction_models.py (NEW FILE)

from pydantic import BaseModel, Field
from typing import Optional
from decimal import Decimal
import uuid
from enum import Enum

# --- Enums ---
class TransactionStatus(str, Enum): 
    SUCCESS = "Success"
    FAILED = "Failed"
    PENDING = "Pending"
    
# Do the same for TransactionType if it exists in that file
class TransactionType(str, Enum): 
    TRANSFER = "Transfer"
    REPAYMENT = "Repayment"
    DEPOSIT = "Deposit"
    WITHDRAWAL = "Withdrawal"

# --- Customer Transaction Request ---

class TransactionRequest(BaseModel):
    """Input for initiating a fund transfer."""
    source_account_number: str = Field(..., description="The account number sending the funds.")
    target_account_number: str = Field(..., description="The account number receiving the funds.")
    amount: Decimal = Field(..., gt=Decimal(0), max_digits=15, decimal_places=2, description="Amount to transfer.")
    description: Optional[str] = Field(None, max_length=255)

# --- Transaction Response/Detail ---

class TransactionResponse(BaseModel):
    """Response after a successful transaction."""
    transaction_id: uuid.UUID
    status: TransactionStatus
    message: str
    
class AccountBalanceResponse(BaseModel):
    """Response model to show the balance of an account and current daily usage."""
    account_number: str
    current_balance: Decimal
    daily_transfer_limit: Decimal = Field(..., description="The global daily limit.")
    daily_transacted_amount_today: Decimal