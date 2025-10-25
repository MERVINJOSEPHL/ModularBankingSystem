import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from unittest.mock import MagicMock, patch
from decimal import Decimal
import uuid
from jose import jwt 
from fastapi import HTTPException, status 

# Import the main FastAPI application and dependencies
from main import app
from utility.database import get_db

# Use the test client for making requests
client = TestClient(app)

# --- MOCK SETUP & FIXTURES ---

# IDs for testing roles
CUSTOMER_ID = str(uuid.uuid4())
ADMIN_ID = str(uuid.uuid4())
AUDITOR_ID = str(uuid.uuid4())
LOAN_ID = str(uuid.uuid4())
TXN_ID = str(uuid.uuid4())
ACCOUNT_NUMBER = "ACC-12345"

# Global Test Data
CUSTOMER_SIGNUP_DATA = {
    "username": "testcustomer", "password": "securepassword", "role": "customer",
    "account_type": "Saving", "initial_deposit": 500.00
}
AUDITOR_SIGNUP_DATA = {"username": "testauditor", "password": "securepassword", "role": "auditor"}
KYC_SUBMISSION_DATA = {"name": "Jane Doe", "phone_number": "1234567890", "address": "123 Test St."}
LOAN_APPLICATION_DATA = {"loan_type": "Home", "loan_amount": 100000.00, "tenure_months": 120}

@pytest.fixture(autouse=True)
def mock_external_dependencies(mocker):
    """Mocks global dependencies like database setup and the JWT decode failure."""
    mocker.patch('main.create_tables')
    mocker.patch('main.engine')
    # Patch jwt.decode to return a dummy payload, satisfying the JWT format check
    mocker.patch('jose.jwt.decode', return_value={'sub': 'dummy', 'role': 'dummy'})

@pytest.fixture
def mock_db_session(mocker):
    """
    Fixture to create a mock SQLAlchemy Session and override get_db. 
    Yields the mock session object.
    """
    mock_session = MagicMock(spec=Session)
    
    def override_get_db():
        yield mock_session
        
    app.dependency_overrides[get_db] = override_get_db
    yield mock_session
    app.dependency_overrides.clear()


def mock_successful_db_user_lookup(mock_session: MagicMock, role: str, user_id: str):
    """Sets up the mock session to return a valid User object for the given role/ID."""
    mock_user = MagicMock(user_id=user_id, role=role)
    # Set up the chain: .query(User).filter(id).first() returns the mock_user
    mock_session.query.return_value.filter.return_value.first.return_value = mock_user
    # Ensure other ORM calls (like filter().all()) return an empty list by default
    mock_session.query.return_value.filter.return_value.all.return_value = []
    return mock_session


@pytest.fixture
def auth_headers():
    """Returns a factory function to create headers with role embedded."""
    def _create_headers(role: str, user_id: str = CUSTOMER_ID):
        # We use a unique string for the token that the mocked dependency reads.
        token_data = f"Bearer VALID_TOKEN_{role.upper()}_{user_id}" 
        return {"Authorization": token_data, "Content-Type": "application/json"}
    return _create_headers


@pytest.fixture(autouse=True)
def mock_auth_resolver(mocker, mock_db_session):
    """
    Mocks the dependency that resolves user/role (get_authenticated_user_and_role).
    CRITICALLY: It mocks the ORM query result *before* the test endpoint is called.
    """
    mock_session = mock_db_session
    
    def mock_get_authenticated_user_and_role(token: str):
        # 1. Determine intended role/ID from the token string
        if 'CUSTOMER' in token:
            user_id, role = CUSTOMER_ID, 'customer'
        elif 'ADMIN' in token:
            user_id, role = ADMIN_ID, 'admin'
        elif 'AUDITOR' in token:
            user_id, role = AUDITOR_ID, 'auditor'
        else:
            raise HTTPException(status_code=401, detail="Not authenticated (Mocked failure)")

        # 2. Set up the ORM mock to return a user with the matching role/ID
        mock_successful_db_user_lookup(mock_session, role, user_id)
        
        # 3. Return the payload data (which passes the rest of the auth checks)
        return {'user_id': user_id, 'role': role}

    # Patch the function that resolves the user from the token/DB
    mocker.patch(
        'utility.auth.get_authenticated_user_and_role',
        side_effect=mock_get_authenticated_user_and_role
    )


# --- 26 TEST CASES (5 per Scenario + Root) ---

def test_read_root():
    """Test the basic root endpoint."""
    response = client.get("/")
    assert response.status_code == 200

# -----------------------------------------------------------------
# 1. AUTHENTICATION & SIGNUP TESTS (5 Cases)
# -----------------------------------------------------------------

@patch('services.signup_services.register_user_orm')
def test_signup_success_register_auditor(mock_register_user_orm, mock_db_session):
    """#1 Success: Register Auditor."""
    mock_register_user_orm.return_value = AUDITOR_ID
    response = client.post("/api/auth/signup", json=AUDITOR_SIGNUP_DATA)
    assert response.status_code == 200
    assert "Registration successful." == response.json()["message"]

@patch('services.signup_services.register_user_orm')
def test_signup_failure_short_username(mock_register_user_orm, mock_db_session):
    """#2 Failure: Short Username (Pydantic)."""
    invalid_data = CUSTOMER_SIGNUP_DATA.copy()
    invalid_data["username"] = "ab" 
    response = client.post("/api/auth/signup", json=invalid_data)
    assert response.status_code == 422
    assert "at least 3 characters long" in response.json()["detail"][0]["msg"]

@patch('services.signup_services.register_user_orm')
def test_signup_failure_duplicate_username(mock_register_user_orm, mock_db_session):
    """#3 Failure: Duplicate Username."""
    mock_register_user_orm.side_effect = ValueError("Username already exists.")
    response = client.post("/api/auth/signup", json=CUSTOMER_SIGNUP_DATA)
    assert response.status_code == 400
    assert response.json()["detail"] == "Username already exists."
    
@patch('services.signup_services.create_jwt_response')
@patch('services.signup_services.authenticate_user_orm')
def test_login_success_valid_admin_login(mock_authenticate_user_orm, mock_create_jwt_response, mock_db_session):
    """#4 Success: Valid Admin Login (Form data FIX)."""
    auth_data = {"user_id": ADMIN_ID, "role": "admin"}
    mock_authenticate_user_orm.return_value = auth_data
    expected_response = {"access_token": "mock.admin.token", "token_type": "bearer", "role": "admin"}
    mock_create_jwt_response.return_value = expected_response
    login_data = {"username": "admin", "password": "pwd"}
    response = client.post("/api/auth/login", data=login_data)
    assert response.status_code == 200
    assert response.json()["role"] == "admin"
    
@patch('services.signup_services.authenticate_user_orm')
def test_login_failure_invalid_password(mock_authenticate_user_orm, mock_db_session):
    """#5 Failure: Invalid Password (Form data FIX)."""
    mock_authenticate_user_orm.side_effect = ValueError("Invalid username or password.")
    login_data = {"username": "user", "password": "wrong"}
    response = client.post("/api/auth/login", data=login_data)
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid username or password"

# -----------------------------------------------------------------
# 2. KYC ENDPOINTS TESTS (5 Cases)
# -----------------------------------------------------------------

@patch('services.kyc_services.submit_kyc_details')
def test_kyc_submit_success_first_submission(mock_submit_kyc, mock_db_session, auth_headers):
    """#6 Success: First Submission."""
    mock_submit_kyc.return_value = "In Progress"
    response = client.post("/api/kyc/customer/submit", headers=auth_headers('customer'), json=KYC_SUBMISSION_DATA)
    assert response.status_code == 200

def test_kyc_submit_failure_unauthorized_role(mock_db_session, auth_headers):
    """#7 Failure: Unauthorized Role (Admin)."""
    response = client.post("/api/kyc/customer/submit", headers=auth_headers('admin'), json=KYC_SUBMISSION_DATA)
    assert response.status_code == 403
    assert "Operation not permitted" in response.json()["detail"]

def test_kyc_submit_failure_invalid_name(mock_db_session, auth_headers):
    """#8 Failure: Missing Name (Pydantic)."""
    invalid_data = KYC_SUBMISSION_DATA.copy()
    invalid_data["name"] = "" 
    response = client.post("/api/kyc/customer/submit", headers=auth_headers('customer'), json=invalid_data)
    assert response.status_code == 422
    
@patch('services.kyc_services.get_kyc_for_review')
def test_admin_kyc_list_pending(mock_get_kyc, mock_db_session, auth_headers):
    """#9 Success: List Pending."""
    mock_get_kyc.return_value = [{"customer_id": CUSTOMER_ID, "name": "Jane", "kyc_status": "In Progress"}]
    response = client.get("/api/kyc/admin/for-review", headers=auth_headers('admin'))
    assert response.status_code == 200

@patch('services.kyc_services.review_kyc_application')
def test_admin_kyc_review_approve_success(mock_review_kyc, mock_db_session, auth_headers):
    """#10 Success: Approve KYC."""
    mock_review_kyc.return_value = {"customer_id": CUSTOMER_ID, "name": "Jane", "kyc_status": "Approved"}
    review_data = {"new_status": "Approved"}
    response = client.post(f"/api/kyc/admin/{CUSTOMER_ID}/review", headers=auth_headers('admin'), json=review_data)
    assert response.status_code == 200
    assert response.json()["kyc_status"] == "Approved"

# -----------------------------------------------------------------
# 3. LOAN ENDPOINTS TESTS (5 Cases)
# -----------------------------------------------------------------

@patch('services.loan_services.apply_for_loan')
def test_customer_loan_apply_success(mock_apply_loan, mock_db_session, auth_headers):
    """#11 Success: Valid Application."""
    mock_apply_loan.return_value = LOAN_ID
    response = client.post("/api/loan/customer/apply", headers=auth_headers('customer'), json=LOAN_APPLICATION_DATA)
    assert response.status_code == 201

def test_customer_loan_apply_failure_invalid_amount(mock_db_session, auth_headers):
    """#12 Failure: Invalid Amount (Pydantic)."""
    invalid_data = LOAN_APPLICATION_DATA.copy()
    invalid_data["loan_amount"] = 0.00
    response = client.post("/api/loan/customer/apply", headers=auth_headers('customer'), json=invalid_data)
    assert response.status_code == 422
    assert "greater than 0" in response.json()["detail"][0]["msg"]

@patch('services.loan_services.apply_for_loan')
def test_customer_loan_apply_failure_kyc_not_approved(mock_apply_loan, mock_db_session, auth_headers):
    """#13 Failure: KYC Not Approved."""
    mock_apply_loan.side_effect = HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="KYC not Approved. Cannot apply for loan.")
    response = client.post("/api/loan/customer/apply", headers=auth_headers('customer'), json=LOAN_APPLICATION_DATA)
    assert response.status_code == 403
    assert "KYC not Approved" in response.json()["detail"]

@patch('services.loan_services.review_loan_application')
def test_admin_loan_review_reject_success(mock_review_loan, mock_db_session, auth_headers):
    """#14 Success: Reject Loan."""
    mock_review_loan.return_value = {"loan_id": LOAN_ID, "loan_status": "Rejected"}
    review_data = {"loan_status": "Rejected"}
    response = client.post(f"/api/loan/admin/{LOAN_ID}/review", headers=auth_headers('admin'), json=review_data)
    assert response.status_code == 200

@patch('services.loan_services.review_loan_application')
def test_admin_loan_review_failure_missing_emi(mock_review_loan, mock_db_session, auth_headers):
    """#15 Failure: Missing EMI on Approval (Pydantic)."""
    review_data = {"loan_status": "Approved"} # Missing emi_amount
    response = client.post(f"/api/loan/admin/{LOAN_ID}/review", headers=auth_headers('admin'), json=review_data)
    assert response.status_code == 422
    assert "EMI amount must be provided and positive" in response.json()["detail"][0]["msg"]

# -----------------------------------------------------------------
# 4. TRANSACTION ENDPOINT TESTS (5 Cases)
# -----------------------------------------------------------------

@patch('services.transaction_services.process_fund_transfer')
def test_customer_transfer_funds_success(mock_process_transfer, mock_db_session, auth_headers):
    """#16 Success: Valid Transfer."""
    mock_process_transfer.return_value = TXN_ID
    transfer_data = {"source_account_number": ACCOUNT_NUMBER, "target_account_number": "ACC-56789", "amount": 100.00}
    response = client.post("/api/transactions/customer/transfer", headers=auth_headers('customer'), json=transfer_data)
    assert response.status_code == 201

@patch('services.transaction_services.process_fund_transfer')
def test_customer_transfer_funds_failure_limit_exceeded(mock_process_transfer, mock_db_session, auth_headers):
    """#17 Failure: Exceeding Daily Limit."""
    mock_process_transfer.side_effect = HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Exceeding daily transaction limit.")
    transfer_data = {"source_account_number": ACCOUNT_NUMBER, "target_account_number": "ACC-56789", "amount": 60000.00}
    response = client.post("/api/transactions/customer/transfer", headers=auth_headers('customer'), json=transfer_data)
    assert response.status_code == 403

@patch('services.transaction_services.process_fund_transfer')
def test_customer_transfer_funds_failure_insufficient_funds(mock_process_transfer, mock_db_session, auth_headers):
    """#18 Failure: Insufficient Funds."""
    mock_process_transfer.side_effect = HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Insufficient funds in source account.")
    transfer_data = {"source_account_number": ACCOUNT_NUMBER, "target_account_number": "ACC-56789", "amount": 1000000.00}
    response = client.post("/api/transactions/customer/transfer", headers=auth_headers('customer'), json=transfer_data)
    assert response.status_code == 400

@patch('services.transaction_services.get_account_balance')
@patch('services.transaction_services.DAILY_TRANSFER_LIMIT', new=Decimal('50000.00'))
def test_customer_get_balance_success(mock_get_balance, mock_db_session, auth_headers):
    """#19 Success: Check Balance."""
    mock_account = MagicMock(account_number=ACCOUNT_NUMBER, current_balance=Decimal('5000.00'))
    mock_usage = Decimal('1000.00')
    mock_get_balance.return_value = (mock_account, mock_usage)
    response = client.get(f"/api/transactions/customer/balance/{ACCOUNT_NUMBER}", headers=auth_headers('customer'))
    assert response.status_code == 200
    assert float(response.json()["current_balance"]) == 5000.00

@patch('services.transaction_services.get_account_balance')
def test_customer_get_balance_failure_non_existent(mock_get_balance, mock_db_session, auth_headers):
    """#20 Failure: Non-existent Account."""
    mock_get_balance.side_effect = HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found.")
    response = client.get("/api/transactions/customer/balance/ACC_FAKE", headers=auth_headers('customer'))
    assert response.status_code == 404

# -----------------------------------------------------------------
# 5. AUDITOR & AUTHORIZATION BOUNDARY TESTS (5 Cases)
# -----------------------------------------------------------------

@patch('services.auditor_services.get_recent_audit_logs')
def test_auditor_get_logs_success(mock_get_logs, mock_db_session, auth_headers):
    """#21 Success: Auditor Access."""
    mock_logs = [{"log_id": 1, "timestamp": "2025-10-25T10:00:00Z", "action": "Loan Approved", "details": {}}]
    mock_get_logs.return_value = mock_logs
    response = client.get("/api/auditor/audit-logs", headers=auth_headers('auditor'))
    assert response.status_code == 200
    assert response.json()["total_count"] == 1

def test_auditor_access_failure_admin_access(mock_db_session, auth_headers):
    """#22 Failure: Admin Access."""
    response = client.get("/api/auditor/audit-logs", headers=auth_headers('admin'))
    assert response.status_code == 403

def test_auditor_access_failure_customer_access(mock_db_session, auth_headers):
    """#23 Failure: Customer Access."""
    response = client.get("/api/auditor/audit-logs", headers=auth_headers('customer'))
    assert response.status_code == 403

def test_admin_access_failure_auditor_role(mock_db_session, auth_headers):
    """#24 Failure: Auditor attempts Admin Endpoint."""
    response = client.get("/api/loan/admin/pending-loans", headers=auth_headers('auditor'))
    assert response.status_code == 403

def test_transfer_failure_unauthenticated_access(mock_db_session):
    """#25 Failure: Unauthenticated Access."""
    transfer_data = {"source_account_number": ACCOUNT_NUMBER, "target_account_number": "ACC-56789", "amount": 100.00}
    response = client.post("/api/transactions/customer/transfer", json=transfer_data)
    assert response.status_code == 401