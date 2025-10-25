# app/models/orm_models.py - CORRECTED

import uuid
from sqlalchemy import Column, String, Boolean, DateTime, CheckConstraint, ForeignKey, Text, BigInteger,UniqueConstraint,Date
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, NUMERIC, JSONB
from sqlalchemy.sql import func
from utility.database import Base # Corrected relative import for utility

# --- Utility Function Placeholder ---
# SQLAlchemy UUID type requires using UUID(as_uuid=True) and String conversion when passing data.

# --- Audit Model (Defined Early for Relationship Resolution) ---

class AuditLog(Base):
    """ORM Model for system activity and audit logging."""
    __tablename__ = "Audit_Log"

    # Using BigInteger + autoincrement=True for BIGSERIAL equivalent
    log_id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    # Corrected FK type
    user_id = Column(String(36), ForeignKey("User.user_id", ondelete="SET NULL")) 
    timestamp = Column(DateTime, server_default=func.now())
    action = Column(String(255), nullable=False)
    ip_address = Column(String(45))
    details = Column(JSONB)

    # Relationships
    user = relationship("User", back_populates="audit_logs")


# --- Base User/Customer Models ---

class User(Base):
    """ORM Model for the 'User' (Authentication) table."""
    __tablename__ = "User"

    # NOTE: Changing to String(36) for UUIDs to simplify consistency across different DBs/drivers
    user_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(Text, nullable=False)
    role = Column(String(10), nullable=False) # customer, admin, auditor
    last_login = Column(DateTime)

    __table_args__ = (
        CheckConstraint(role.in_(['customer', 'admin', 'auditor']), name='user_role_check'),
    )

    # Relationships: POINTING TO THE PYTHON CLASS NAME AuditLog
    customer_info = relationship("Customer", back_populates="user", uselist=False, cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="user") # FIX 1: Corrected string reference


class Customer(Base):
    """ORM Model for Customer details, linked 1:1 to User (KYC status)."""
    __tablename__ = "Customer"

    # customer_id is both the Primary Key and Foreign Key to User
    customer_id = Column(String(36), ForeignKey("User.user_id", ondelete="CASCADE"), primary_key=True)
    name = Column(String(255))
    phone_number = Column(String(20))
    address = Column(Text)
    kyc_status = Column(Boolean, default=False)

    # Relationships
    user = relationship("User", back_populates="customer_info")
    accounts = relationship("Account", back_populates="customer")
    loans = relationship("Loan", back_populates="customer")


class Account(Base):
    """ORM Model for Customer Bank Accounts (Saving, Current, FD)."""
    __tablename__ = "Account"

    account_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    customer_id = Column(String(36), ForeignKey("Customer.customer_id", ondelete="CASCADE"), nullable=False)
    account_number = Column(String(20), unique=True, nullable=False)
    account_type = Column(String(10), nullable=False)
    current_balance = Column(NUMERIC(15, 2), nullable=False, default=0.00)
    created_at = Column(DateTime, server_default=func.now())

    __table_args__ = (
        CheckConstraint(account_type.in_(['Saving', 'Current', 'FD']), name='account_type_check'),
    )

    # Relationships: Use string forward references for classes defined later
    customer = relationship("Customer", back_populates="accounts")
    source_transactions = relationship("Transaction", foreign_keys="[Transaction.source_account_id]", back_populates="source_account")
    target_transactions = relationship("Transaction", foreign_keys="[Transaction.target_account_id]", back_populates="target_account")


# --- Transaction & Fraud Models ---

class Transaction(Base):
    """ORM Model for all financial transactions."""
    __tablename__ = "Transaction"

    transaction_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    source_account_id = Column(String(36), ForeignKey("Account.account_id"), nullable=False)
    target_account_id = Column(String(36), ForeignKey("Account.account_id"), nullable=False)
    amount = Column(NUMERIC(15, 2), nullable=False)
    transaction_type = Column(String(10), nullable=False)
    timestamp = Column(DateTime, server_default=func.now())
    status = Column(String(10), nullable=False)

    __table_args__ = (
        CheckConstraint(transaction_type.in_(['Transfer', 'Repayment', 'Deposit', 'Withdrawal']), name='transaction_type_check'),
    )

    # Relationships
    source_account = relationship("Account", foreign_keys=[source_account_id], back_populates="source_transactions")
    target_account = relationship("Account", foreign_keys=[target_account_id], back_populates="target_transactions")
    fraud_flag = relationship("FraudFlag", back_populates="transaction", uselist=False, cascade="all, delete-orphan")
    loan_repayment_record = relationship("LoanRepayment", back_populates="transaction", uselist=False)


class FraudFlag(Base):
    """ORM Model for transactions flagged by the LLaMA ML Model."""
    __tablename__ = "Fraud_Flag"

    flag_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    transaction_id = Column(String(36), ForeignKey("Transaction.transaction_id", ondelete="CASCADE"), unique=True, nullable=False)
    flag_reason = Column(String(255))
    flagged_by_model = Column(Boolean, nullable=False)
    admin_reviewed = Column(Boolean, default=False)
    review_timestamp = Column(DateTime)

    # Relationships
    transaction = relationship("Transaction", back_populates="fraud_flag")


# --- Loan Models ---

class Loan(Base):
    """ORM Model for Loan applications and status."""
    __tablename__ = "Loan"

    loan_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    customer_id = Column(String(36), ForeignKey("Customer.customer_id", ondelete="CASCADE"), nullable=False)
    loan_type = Column(String(50), nullable=False)
    loan_amount = Column(NUMERIC(15, 2), nullable=False)
    tenure_months = Column(BigInteger, nullable=False)
    emi_amount = Column(NUMERIC(15, 2))
    start_date = Column(DateTime)
    loan_status = Column(String(20), nullable=False, default='Pending')

    __table_args__ = (
        CheckConstraint(loan_status.in_(['Pending', 'Approved', 'Rejected', 'Active', 'Paid']), name='loan_status_check'),
    )

    # Relationships
    customer = relationship("Customer", back_populates="loans")
    repayments = relationship("LoanRepayment", back_populates="loan")


class LoanRepayment(Base):
    """ORM Model for individual loan repayment records."""
    __tablename__ = "Loan_Repayment"

    repayment_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    loan_id = Column(String(36), ForeignKey("Loan.loan_id", ondelete="CASCADE"), nullable=False)
    repayment_date = Column(DateTime, nullable=False)
    amount_paid = Column(NUMERIC(15, 2), nullable=False)
    transaction_id = Column(String(36), ForeignKey("Transaction.transaction_id"), unique=True)

    # Relationships
    loan = relationship("Loan", back_populates="repayments")
    transaction = relationship("Transaction", back_populates="loan_repayment_record")


class DailyLimitTracker(Base):
    """
    ORM Model to track the aggregate transaction amount for an account on a specific date.
    Used for enforcing the fixed global daily transfer limit.
    """
    __tablename__ = "Daily_Limit_Tracker"

    tracker_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    account_id = Column(String(36), ForeignKey("Account.account_id", ondelete="CASCADE"), nullable=False)
    transaction_date = Column(Date, nullable=False, server_default=func.current_date())
    transacted_amount = Column(NUMERIC(15, 2), nullable=False, default=0.00) 
    __table_args__ = (
        UniqueConstraint('account_id', 'transaction_date', name='uq_account_date'),
    )

    account = relationship("Account")