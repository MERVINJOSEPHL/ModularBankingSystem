# smart-bank-modular/controller/transaction_controller.py (NEW FILE)

from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.orm import Session
from decimal import Decimal
import uuid
from models.transaction_models import (
    TransactionRequest, TransactionResponse, 
    TransactionStatus, AccountBalanceResponse
)
from services import transaction_services as transaction_service
from utility.database import get_db
from utility.auth import CUSTOMER_AUTH # Requires CUSTOMER role
from utility.logging import setup_logger

router = APIRouter(tags=["Transactions"])
logger = setup_logger(__name__)

@router.post(
    "/customer/transfer",
    response_model=TransactionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Process a fund transfer between two accounts"
)
def transfer_funds(
    request: TransactionRequest,
    db: Session = Depends(get_db),
    customer_id: str = Depends(CUSTOMER_AUTH) # Requires CUSTOMER role
):
    """
    Handles internal fund transfers, validating sender balance and the global daily limit.
    """
    try:
        transaction_id = transaction_service.process_fund_transfer(db, customer_id, request)
        return TransactionResponse(
            transaction_id=transaction_id,
            status=TransactionStatus.SUCCESS,
            message="Funds transferred successfully."
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.critical(f"Unhandled error during fund transfer for customer {customer_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred during the transfer.")

@router.get(
    "/customer/balance/{account_number}",
    response_model=AccountBalanceResponse,
    summary="Get current account balance and daily limit status"
)
def get_balance(
    account_number: str,
    db: Session = Depends(get_db),
    customer_id: str = Depends(CUSTOMER_AUTH)
):
    """
    Retrieves the current balance, the global daily transfer limit, and today's usage.
    """
    try:
        # Get the account object and the daily usage from the service
        account, daily_usage = transaction_service.get_account_balance(db, customer_id, account_number)
        
        return AccountBalanceResponse(
            account_number=account.account_number,
            current_balance=account.current_balance,
            daily_transfer_limit=transaction_service.DAILY_TRANSFER_LIMIT, # Use the global constant
            daily_transacted_amount_today=daily_usage 
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.critical(f"Unhandled error fetching balance for account {account_number}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred.")