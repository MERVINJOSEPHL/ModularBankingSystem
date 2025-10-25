# smart-bank-modular/services/transaction_services.py (NEW FILE)

from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from datetime import datetime, date
from decimal import Decimal, ROUND_HALF_UP
import uuid
from typing import Tuple, Optional
from services.audit_services import create_audit_log
from models.orm_models import Account, Transaction, Customer, DailyLimitTracker 
from models.transaction_models import TransactionRequest, TransactionStatus, TransactionType
from utility.logging import setup_logger 

logger = setup_logger(__name__)


DAILY_TRANSFER_LIMIT = Decimal('50000.00') 

def _get_daily_tracker(db: Session, account_id: str) -> DailyLimitTracker:
    """
    Fetches or creates the daily tracker record for the current day.
    """
    today = date.today()
    
    tracker = db.query(DailyLimitTracker).filter(
        DailyLimitTracker.account_id == account_id,
        DailyLimitTracker.transaction_date == today
    ).first()
    
    if not tracker:
        tracker = DailyLimitTracker(
            account_id=account_id,
            transaction_date=today,
            transacted_amount=Decimal('0.00')
        )
        db.add(tracker)
        db.flush() 
        
    return tracker

def process_fund_transfer(db: Session, customer_id: str, request: TransactionRequest) -> uuid.UUID:
    """
    Validates, processes, and logs a fund transfer between two accounts, checking the global daily limit.
    """
    amount = request.amount.quantize(Decimal('.01'), rounding=ROUND_HALF_UP)
    
    source_account = db.query(Account).filter(Account.account_number == request.source_account_number).first()
    target_account = db.query(Account).filter(Account.account_number == request.target_account_number).first()

    if not source_account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source account not found.")
    if not target_account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Target account not found.")
    
    if source_account.customer_id != customer_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not own the source account.")
    
    tracker = _get_daily_tracker(db, source_account.account_id)
    
    new_transacted_amount = tracker.transacted_amount + amount
    
    if new_transacted_amount > DAILY_TRANSFER_LIMIT:
        logger.warning(f"Transaction failed for {source_account.account_number}: Daily limit exceeded (Limit: {DAILY_TRANSFER_LIMIT}).")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail=f"Exceeding global daily transaction limit of ${DAILY_TRANSFER_LIMIT:,.2f}."
        )

    if source_account.current_balance < amount:
        logger.warning(f"Transaction failed for {source_account.account_number}: Insufficient funds.")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Insufficient funds in source account.")

    try:
        source_account.current_balance -= amount
        target_account.current_balance += amount
        
        tracker.transacted_amount = new_transacted_amount 
        
        new_transaction_id = str(uuid.uuid4())
        db_transaction = Transaction(
            transaction_id=new_transaction_id,
            source_account_id=source_account.account_id,
            target_account_id=target_account.account_id,
            amount=amount,
            transaction_type=TransactionType.TRANSFER,
            status=TransactionStatus.SUCCESS
        )
        db.add(db_transaction)
        action = f"Fund Transfer SUCCESS: {amount} to {target_account.account_number}"
        details = {
            "source": request.source_account_number, 
            "target": request.target_account_number,
            "amount": float(amount),
            "txn_id": new_transaction_id
        }
        # Logged by the customer_id performing the transaction
        create_audit_log(db, customer_id, action, details=details)
        db.commit()
        logger.info(f"Transaction {new_transaction_id}: {amount} transferred. Daily usage for {source_account.account_number} is now {new_transacted_amount}.")
        return uuid.UUID(new_transaction_id)
        
    except Exception as e:
        db.rollback()
        logger.error(f"Critical error during transaction processing: {e}")
        
        try:
             failed_transaction = Transaction(
                transaction_id=str(uuid.uuid4()),
                source_account_id=source_account.account_id,
                target_account_id=target_account.account_id,
                amount=amount,
                transaction_type=TransactionType.TRANSFER,
                status=TransactionStatus.FAILED
            )
             db.add(failed_transaction)
             action = f"Fund Transfer FAILED: {amount} to {target_account.account_number}"
             details = {
                 "source": request.source_account_number, 
                 "target": request.target_account_number,
                 "amount": float(amount),
                 "error": str(e)
             }
             create_audit_log(db, customer_id, action, details=details)
             db.commit()
        except:
             pass 
        
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An error occurred during transaction processing.")

def get_account_balance(db: Session, customer_id: str, account_number: str) -> Tuple[Account, Decimal]:
    """Retrieves the account object, plus today's transacted amount."""
    account = db.query(Account).filter(
        Account.account_number == account_number,
        Account.customer_id == customer_id
    ).first()
    
    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found or does not belong to the user.")


    tracker = db.query(DailyLimitTracker).filter(
        DailyLimitTracker.account_id == account.account_id,
        DailyLimitTracker.transaction_date == date.today()
    ).first()
    
    daily_usage = tracker.transacted_amount if tracker else Decimal('0.00')
    
    return account, daily_usage