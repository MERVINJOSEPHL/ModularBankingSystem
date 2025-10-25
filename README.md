# 🏦 Smart Bank Modular Banking System (Final PoC Scope)

## 1. Project Goal and Core Flow

This Proof of Concept (PoC) establishes a secure, modular banking system focused on the essential Customer and Admin workflows, driven by robust **JWT authentication** and cutting-edge **LLaMA-powered fraud detection**.

### Key System Flow
1.  **Customer Onboarding:** Sign up -> KYC Verification -> Account Creation (Saving/Deposit Type).
2.  **Customer Actions:** Login via JWT -> Request Loan OR -> Make Transaction.
3.  **Real-time Security:** **LLaMA Fraud Detection** runs instantly during transactions.
4.  **Admin Oversight:** Admin reviews all transactions and fraud flags.

---

## 2. Architecture & Tech Stack

| Component | Technology | Role & Security Focus |
| :--- | :--- | :--- |
| **Backend API** | **FastAPI** | High-speed API for data handling and logic. |
| **Database** | **PostgreSQL** | Stores all financial data (Users, Accounts, Transactions). |
| **Data Validation**| **Pydantic** | Enforces strict validation for KYC, Transactions, and Loan requests. |
| **Frontend UI** | **Streamlit** | Provides simple, secure UI for Customer and Admin login/dashboards. |
| **Authentication**| **JWT** & **Password Hashing** | Secures all API routes with token-based access and strong password encryption. |
| **Fraud Model** | **LLaMA (Offline/Local)** | Securely processes transaction data at runtime to flag fraud, ensuring **data residency**. |

---

## 3. Core Features & Role-Based Access

The system is defined by distinct roles and their authorization via JWT.

### 3.1. 👨‍💻 Customer Flow (Authorized via JWT)

| Feature | Description | Key Action |
| :--- | :--- | :--- |
| **Onboarding** | Sign-up, automatic **KYC verification** status, and designation of initial **Saving/Deposit** type. | Creation of `User` and `Account` records. |
| **Transaction** | Initiate fund transfers or deposits. | Data is sent for immediate **LLaMA fraud check**. |
| **Loan Request** | Submit a request for a loan. | Request is logged and sent to the Admin dashboard. |

### 3.2. 💼 Bank Admin Flow (Authorized via JWT)

| Feature | Description | Key Action |
| :--- | :--- | :--- |
| **Transaction Monitoring** | View all historical and real-time customer transactions. | Accesses the `Transaction` table. |
| **Fraud Detection Review**| Review transactions that were flagged by the **LLaMA model at the time of the transaction**. | Reviews records in the `Fraud_Flag` table. |
| **Loan Approval** | Manually approve or reject pending loan requests. | Updates the `Loan` record status. |

---

## 4. Key Security & Integrity Points

* **Offline LLaMA:** The LLM runs locally to ensure transaction data never leaves the controlled environment.
* **Pydantic Validation:** Used on all inputs (KYC, Account creation, Transactions) to prevent data corruption.
* **JWT Authorization:** Every request from both the Customer and Admin must carry a valid JWT token.
* **Audit Logging:** Every critical action (login, transaction, approval) will be logged to satisfy the **Auditor** role requirement.

---

## 5. Installation and Setup

### Prerequisites
* Python 3.10+
* PostgreSQL running locally.
* Local LLaMA configuration (or a mock function to simulate its secure, offline output).

### Instructions (Simplified)

1.  **Clone & Setup:**
    ```bash
    git clone [repository_url]
    cd smart-bank-modular
    pip install -r requirements.txt
    ```
2.  **Configure & Migrate:** Set up database connection details and run migration scripts to create all necessary tables.
3.  **Start Services:**
    ```bash
    # Backend
    uvicorn app.main:app --reload

    # Frontend
    streamlit run ui/app.py
    ```

---

## 6. Complete API Specification

This section details the necessary CRUD API endpoints, defining the inputs (using **Pydantic**) and outputs for all core functionality demonstrated in the PoC. All endpoints are hosted by **FastAPI** and secured by **JWT** unless marked Public.

### 6.1. Authentication Endpoints (Public)

These manage user registration and token issuance.

| Method | Endpoint | Description | Input Parameters | Output Parameters |
| :--- | :--- | :--- | :--- | :--- |
| `POST` | `/api/auth/signup` | Register a new user (`customer` role) and initiate account structure. | **Pydantic Model:** `username: str`, `password: str`, `initial_deposit: float`, `account_type: str` ('Saving'/'Deposit') | `user_id: uuid`, `message: str` ("Registration successful, KYC pending") |
| `POST` | `/api/auth/login` | Authenticate credentials and issue a JWT. | **Pydantic Model:** `username: str`, `password: str` | `access_token: str` (JWT), `token_type: str`, `role: str` |

### 6.2. Customer Endpoints (Authorized by JWT - Role: 'customer')

These require a valid Customer JWT for access.

| Method | Endpoint | Description | Input Parameters | Output Parameters |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/api/accounts/balance` | Fetch the current account balance and status. | *(None, uses user\_id from JWT)* | **Pydantic Model:** `balance: float`, `account_type: str`, `kyc_status: bool` |
| `GET` | `/api/transactions/history` | Retrieve a list of the customer's transactions. | `limit: int` (Optional), `offset: int` (Optional) | **List[Pydantic Model]:** `transaction_id`, `amount`, `type`, `timestamp` |
| `POST` | `/api/transactions/transfer` | Initiate a fund transfer. **Triggers LLaMA fraud check.** | **Pydantic Model:** `target_account_number: str`, `amount: float`, `description: str` | `transaction_id: uuid`, `status: str` ("Pending Fraud Check" or "Flagged") |
| `POST` | `/api/loans/request` | Submit a new loan request. | **Pydantic Model:** `loan_type: str`, `amount: float`, `tenure_months: int` | `loan_id: uuid`, `status: str` ("Pending Admin Approval") |
| `GET` | `/api/loans/status/{loan_id}` | Check the status of a specific loan request. | `loan_id: uuid` (Path Parameter) | **Pydantic Model:** `loan_id`, `status: str`, `emi_amount: float` (if approved) |

### 6.3. Admin Endpoints (Authorized by JWT - Role: 'admin')

These endpoints demonstrate administrative oversight and require an Admin JWT.

| Method | Endpoint | Description | Input Parameters | Output Parameters |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/api/admin/transactions/all` | View all customer transactions across the system. | *(None)* | **List[Pydantic Model]:** Full transaction list, including `customer_id` |
| `GET` | `/api/admin/fraud/flagged` | View all transactions flagged by the LLaMA model. | *(None)* | **List[Pydantic Model]:** `transaction_id`, `amount`, `reason_from_llama`, `timestamp` |
| `POST` | `/api/admin/loan/{loan_id}/review` | Manually approve or reject a pending loan request. | `loan_id: uuid` (Path Parameter), **Pydantic Model:** `decision: str` ('Approved'/'Rejected') | `loan_id: uuid`, `status: str` (Updated Status) |
| `POST` | `/api/admin/kyc/verify/{user_id}` | Manually update a customer's KYC status. | `user_id: uuid` (Path Parameter), **Pydantic Model:** `is_verified: bool` | `user_id: uuid`, `kyc_status: bool` |

### 6.4. Audit Endpoint (Future Scope)

This structure is reserved for the future read-only Auditor role.

| Method | Endpoint | Description | Input Parameters | Output Parameters |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/api/audit/logs` | Retrieve all system logs (requires 'auditor' role). | `start_date: date` (Optional), `action: str` (Optional) | **List[Pydantic Model]:** `log_id`, `user_id`, `timestamp`, `action`, `ip_address` |
