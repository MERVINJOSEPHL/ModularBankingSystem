# app/controller/signup_login_controller.py

from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.orm import Session
# The pydantic models used for request/response
from models.signup_models import SignUpRequest, LoginRequest, SignUpResponse, LoginResponse 
# This imports the module signup_service which contains your functions
from services import signup_services as  signup_service 
from utility.database import get_db 
from utility.logging import setup_logger

router = APIRouter(tags=["Authentication"])
logger = setup_logger(__name__)

@router.post("/signup", response_model=SignUpResponse)
def signup_user(request: SignUpRequest, db: Session = Depends(get_db)):
    """
    Handles new user registration (Customer or Admin) using the ORM.
    """
    try:
        logger.info(f"Received signup request for username: {request.username}, role: {request.role.value}")
        
        # Access the function via the imported module name: signup_service.register_user_orm
        user_id = signup_service.register_user_orm(db, request)
        
        message = "Registration successful."
        if request.role.value == "customer":
            message += " Account created, KYC pending."
            
        return SignUpResponse(
            user_id=user_id,
            message=message
        )
    except ValueError as ve:
        logger.warning(f"Signup failed for {request.username}: {ve}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve)
        )
    except Exception as e:
        logger.critical(f"Unhandled ORM error during signup for {request.username}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during signup."
        )

@router.post("/login", response_model=LoginResponse)
def login_user(request: LoginRequest, db: Session = Depends(get_db)):
    """
    Authenticates user, considers the role, and returns a JWT token 
    along with the user's role in the response body.
    """
    try:
        logger.info(f"Received login request for username: {request.username}")
        
        # Access the function via the imported module name: signup_service.authenticate_user_orm
        auth_data = signup_service.authenticate_user_orm(db, request)

        # Access the function via the imported module name: signup_service.create_jwt_response
        response_data = signup_service.create_jwt_response(auth_data)

        return LoginResponse(**response_data) 
        
    except ValueError as ve:
        logger.warning(f"Login failed for {request.username}: Invalid credentials.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
    except Exception as e:
        logger.critical(f"Unhandled ORM error during login for {request.username}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during login."
        )