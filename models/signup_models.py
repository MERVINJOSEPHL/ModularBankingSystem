# models/signup_models.py (Complete)

from pydantic import BaseModel, field_validator
from typing import Optional
from enum import Enum
import uuid

class UserRole(str, Enum):
    """Defines the possible user roles."""
    CUSTOMER = "customer"
    ADMIN = "admin"


class SignUpRequest(BaseModel):
    username: str
    password: str
    role: UserRole = UserRole.CUSTOMER 
    

    initial_deposit: Optional[float] = None
    account_type: Optional[str] = None

    @field_validator('username')
    @classmethod
    def validate_username_length(cls, v):
        if len(v) < 3:
            raise ValueError('Username must be at least 3 characters long')
        return v
    
    @field_validator('password')
    @classmethod
    def validate_password_length(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v

    @field_validator('initial_deposit', 'account_type')
    @classmethod
    def check_customer_fields(cls, v, info):
        
        if info.data.get('role') == UserRole.CUSTOMER:
            if info.field_name == 'initial_deposit' and (v is None or v <= 0):
                raise ValueError("Initial deposit is required and must be greater than zero for a customer.")
            if info.field_name == 'account_type' and v is None:
                raise ValueError("Account type is required for a customer.")
        return v
    
class LoginRequest(BaseModel):
    """Model for user login credentials."""
    username: str
    password: str


class SignUpResponse(BaseModel):
    """Model for a successful signup response."""
    user_id: uuid.UUID
    message: str

class LoginResponse(BaseModel):
    """Model for a successful login response, including JWT and role."""
    access_token: str
    token_type: str
    role: UserRole