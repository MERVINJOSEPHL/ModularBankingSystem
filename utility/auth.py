# smart-bank-modular/utility/auth.py

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from typing import Optional
from datetime import datetime
from sqlalchemy.orm import Session
import uuid

# Assuming these imports are available in your project structure
from utility.database import get_db
from models.orm_models import User # Need to import the User ORM model
from utility.logging import setup_logger

logger = setup_logger(__name__)

# Re-use setup from signup_service (ensure SECRET_KEY matches)
SECRET_KEY = "YOUR-VERY-SECURE-SECRET" 
ALGORITHM = "HS256"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

class TokenData(dict):
    """Simple container for decoded JWT payload."""
    user_id: str
    role: str

# 1. New Dependency: Get the authenticated and VALIDATED user/role
def get_authenticated_user_and_role(
    db: Session = Depends(get_db), 
    token: str = Depends(oauth2_scheme)
) -> TokenData:
    """
    Decodes the JWT token AND verifies the user/role against the database.
    This enables real-time user existence checks and simple revocation.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials or user no longer exists",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Decode the token payload
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        role: str = payload.get("role")
        
        if user_id is None or role is None:
            raise credentials_exception

    except JWTError as e:
        logger.warning(f"JWT Decoding Error: {e}")
        raise credentials_exception
    
    # 2. Database Validation (The Critical Missing Step)
    try:
        # Check if the user ID from the token still exists in the database
        user = db.query(User).filter(User.user_id == user_id).first()
        
        if user is None:
            # User was likely deleted after token was issued
            logger.warning(f"Authentication failed: User ID {user_id} from token not found in DB.")
            raise credentials_exception
            
        if user.role != role:
            # Role was changed after token was issued (simple revocation)
            logger.warning(f"Authentication failed: Role mismatch for {user_id}. Token role: {role}, DB role: {user.role}")
            raise credentials_exception

    except Exception as e:
        # Catch any ORM errors during the lookup
        logger.error(f"Database error during user validation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Server authentication error."
        )

    # If all checks pass, return the validated data
    return TokenData(user_id=user_id, role=role)


# 2. Updated Dependency Function to use the new validation step
def authorize_roles(allowed_roles: list[str]):
    """
    FastAPI dependency function to check if the current user has one of the allowed roles 
    using the fully validated user data.
    """
    def role_checker(
        current_user: TokenData = Depends(get_authenticated_user_and_role)
    ):
        if current_user['role'] not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation not permitted for role: {current_user['role']}"
            )
        # Return just the user_id for convenience in the controller functions
        return current_user['user_id'] 

    return role_checker

# Pre-defined role dependencies remain the same, but now use the database-backed logic
CUSTOMER_AUTH = authorize_roles(['customer'])
ADMIN_AUTH = authorize_roles(['admin'])