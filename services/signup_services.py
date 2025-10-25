# app/services/signup_service.py

from fastapi import Depends
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta
import uuid
from typing import Optional

# Assuming these imports are available in your project structure
from models.orm_models import User, Customer, Account 
from models.signup_models import SignUpRequest, LoginRequest, UserRole
from utility.logging import setup_logger 
from services.audit_services import create_audit_log

logger = setup_logger(__name__)

# --- Security Configuration ---
pwd_context = CryptContext(schemes=["sha256_crypt"], deprecated="auto")
SECRET_KEY = "YOUR-VERY-SECURE-SECRET" 
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def hash_password(password: str) -> str:
    """Hashes a plain text password using SHA256 (salting technique)."""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain text password against a hashed one."""
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Creates a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    logger.info(f"JWT created for user: {data.get('sub')}, Role: {data.get('role')}")
    return encoded_jwt

def register_user_orm(db: Session, user_data: SignUpRequest) -> uuid.UUID:
    """
    Registers a new user (Customer or Admin) and creates associated records 
    based on the role. Returns the new user_id.
    """
    try:
        new_user_id = uuid.uuid4() 
        hashed_pwd = hash_password(user_data.password)
        
        db_user = User(
            user_id=str(new_user_id),
            username=user_data.username,
            hashed_password=hashed_pwd,
            role=user_data.role.value,
        )
        db.add(db_user)
        db.flush()

        if user_data.role == UserRole.CUSTOMER:
            db_customer = Customer(
                customer_id=str(new_user_id),
                kyc_status=False
            )
            db.add(db_customer)
            db.flush()

            account_number = str(uuid.uuid4().int)[:16] 
            db_account = Account(
                customer_id=str(new_user_id),
                account_number=account_number,
                account_type=user_data.account_type, 
                current_balance=user_data.initial_deposit
            )
            db.add(db_account)
            
            db.commit() 
            action = f"{user_data.role.value.upper()} registered."
            details = {"username": user_data.username}
            create_audit_log(db, str(new_user_id), action, details=details)
            logger.info(f"Customer {user_data.username} registered (ID: {new_user_id}). Account created. KYC pending.")

        elif user_data.role == UserRole.ADMIN:
            db.commit() 
            logger.info(f"Admin {user_data.username} registered (ID: {new_user_id}).")
        elif user_data.role == UserRole.AUDITOR:
            db.commit()
            logger.info(f"Auditor {user_data.username} registered (ID: {new_user_id}).")
            
        else:
            db.rollback()
            raise ValueError("Invalid role specified.")
            
        return new_user_id

    except IntegrityError as e:
        db.rollback()
        logger.warning(f"{e}")
        logger.warning(f" (IntegrityError).{e}")
        raise ValueError("Username already exists.")
    except ValueError as ve:
        db.rollback()
        logger.error(f"Registration failed due to input validation: {ve}")
        raise
    except Exception as e:
        db.rollback()
        logger.critical(f"Critical ORM error during registration: {e}")
        raise

def get_user_by_username(db: Session, username: str) -> Optional[User]:
    """Retrieves a User object by username."""
    try:
        user = db.query(User).filter(User.username == username).first()
        return user
    except Exception as e:
        logger.error(f"Error querying user {username}: {e}")
        raise

def authenticate_user_orm(db: Session, login_data: LoginRequest) -> dict:
    """
    Authenticates a user based on username and password using ORM.
    Returns user data (id, role) upon success.
    """
    try:
        user = get_user_by_username(db, login_data.username) 
        
        if not user or not verify_password(login_data.password, user.hashed_password):
            logger.warning(f"Login attempt failed: Invalid credentials for {login_data.username}.")
            raise ValueError("Invalid username or password.")

        logger.info(f"User '{login_data.username}' authenticated successfully. Role: {user.role}")
        return {
            "user_id": user.user_id,
            "role": user.role
        }
    except Exception as e:
        logger.error(f"Error during ORM user authentication: {e}")
        raise

def create_jwt_response(auth_data: dict) -> dict:
    """
    Generates a JWT token and formats the final login response.
    """
    try:
        access_token = create_access_token(
            data={"sub": str(auth_data['user_id']), "role": auth_data['role']}
        )
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "role": auth_data['role']
        }
    except Exception as e:
        logger.critical(f"Error creating JWT response: {e}")
        raise