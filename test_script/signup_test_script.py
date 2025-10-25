import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from unittest.mock import MagicMock, patch

# Import the main FastAPI application and the dependency function
from main import app
from utility.database import get_db

# Use the test client for making requests
client = TestClient(app)

# --- Mocking Fixtures and Setup ---

# FIX 1: Ensure the global engine in main.py is mocked. 
# We need to patch the actual dependency/global variable referenced in the code.
@pytest.fixture(autouse=True)
def mock_db_setup(mocker):
    """Mocks database table creation to prevent actual DB interaction during tests."""
    mocker.patch('main.create_tables')
    # Patch the global engine in main.py to prevent the deepcopy error 
    # and connection attempts in /health and on client initialization.
    mocker.patch('main.engine') 

@pytest.fixture
def mock_db_session(mocker):
    """
    Fixture to create a mock SQLAlchemy Session and override the get_db dependency.
    """
    mock_session = MagicMock(spec=Session)
    
    # Mock the `get_db` dependency to yield our mock session
    def override_get_db():
        try:
            yield mock_session
        finally:
            # We don't need to call close() on a mock, but can leave this
            pass 

    # Apply the mock to the FastAPI app's dependency injector
    app.dependency_overrides[get_db] = override_get_db
    
    yield mock_session

    # Clean up the dependency override after the test
    app.dependency_overrides.clear()

# --- Endpoint Health & Root Tests ---

def test_read_root():
    """Test the basic root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Smart Bank API is running."}
# --- Signup Endpoint Tests ---

@patch('services.signup_services.register_user_orm')
def test_signup_success_customer(mock_register_user_orm, mock_db_session):
    """Test successful customer signup."""
    
    expected_user_id = "1a2b3c4d-5e6f-7080-9a0b-c1d2e3f4a5b6"
    mock_register_user_orm.return_value = expected_user_id
    
    customer_data = {
        "username": "testcustomer",
        "password": "securepassword",
        "role": "customer",
        "account_type": "Saving",
        "initial_deposit": 500.00
    }
    
    response = client.post("/api/auth/signup", json=customer_data)
    
    assert response.status_code == 200
    assert response.json()["user_id"] == expected_user_id
    assert "Account created, KYC pending" in response.json()["message"]
    
    # FIX 2: Correct assertion syntax
    mock_register_user_orm.assert_called_once()
    
@patch('services.signup_services.register_user_orm')
def test_signup_failure_existing_user(mock_register_user_orm, mock_db_session):
    """Test signup failure when username already exists (IntegrityError simulated via ValueError)."""
    
    mock_register_user_orm.side_effect = ValueError("Username already exists.")
    
    customer_data = {
        "username": "existinguser",
        "password": "securepassword",
        "role": "customer",
        "account_type": "Saving",
        "initial_deposit": 500.00
    }
    
    response = client.post("/api/auth/signup", json=customer_data)
    
    assert response.status_code == 400
    assert response.json()["detail"] == "Username already exists."
    
    # FIX 2: Correct assertion syntax
    mock_register_user_orm.assert_called_once()

def test_signup_failure_invalid_data(mock_db_session):
    """Test signup failure due to Pydantic validation (e.g., missing required fields)."""
    
    invalid_data = {
        "password": "securepassword",
        "account_type": "Saving",
        "initial_deposit": 500.00
    }
    
    response = client.post("/api/auth/signup", json=invalid_data)
    
    assert response.status_code == 422 # Unprocessable Entity (Pydantic validation error)
    # FIX 3: Correct case sensitivity in the expected error message
    assert "Field required" in response.json()["detail"][0]["msg"]
    
# --- Login Endpoint Tests ---

@patch('services.signup_services.create_jwt_response')
@patch('services.signup_services.authenticate_user_orm')
def test_login_success(mock_authenticate_user_orm, mock_create_jwt_response, mock_db_session):
    """Test successful user login."""
    
    auth_data = {"user_id": "1a2b3c4d-5e6f-7080-9a0b-c1d2e3f4a5b6", "role": "customer"}
    mock_authenticate_user_orm.return_value = auth_data
    
    expected_response = {
        "access_token": "mocked.jwt.token",
        "token_type": "bearer",
        "role": "customer"
    }
    mock_create_jwt_response.return_value = expected_response
    
    login_data = {
        "username": "testuser",
        "password": "securepassword"
    }
    
    response = client.post("/api/auth/login", json=login_data)
    
    assert response.status_code == 200
    assert response.json() == expected_response
    
    # FIX 2: Correct assertion syntax
    mock_authenticate_user_orm.assert_called_once()
    mock_create_jwt_response.assert_called_once_with(auth_data)

@patch('services.signup_services.authenticate_user_orm')
def test_login_failure_invalid_credentials(mock_authenticate_user_orm, mock_db_session):
    """Test login failure due to invalid username or password."""
    
    mock_authenticate_user_orm.side_effect = ValueError("Invalid username or password.")
    
    login_data = {
        "username": "wronguser",
        "password": "wrongpassword"
    }
    
    response = client.post("/api/auth/login", json=login_data)
    
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid username or password"
    
    # FIX 2: Correct assertion syntax
    mock_authenticate_user_orm.assert_called_once()

@patch('services.signup_services.authenticate_user_orm')
def test_login_failure_internal_error(mock_authenticate_user_orm, mock_db_session):
    """Test login failure due to an unhandled internal exception."""
    
    mock_authenticate_user_orm.side_effect = Exception("DB Timeout")
    
    login_data = {
        "username": "testuser",
        "password": "securepassword"
    }
    
    response = client.post("/api/auth/login", json=login_data)
    
    assert response.status_code == 500
    assert response.json()["detail"] == "An unexpected error occurred during login."
    mock_authenticate_user_orm.assert_called_once()
