# 🏦 Smart Bank Modular Banking System (POC)

This project is a **Proof of Concept (POC)** for a modular banking system built using **FastAPI** for the backend API and **Streamlit** for the frontend dashboard.  

It demonstrates multi-role authentication, secure KYC processing, atomic financial transactions with limits, loan management, and comprehensive audit logging.

---

## 🚀 1. Features Overview

The system is designed with a **service-oriented architecture (SOA)** and supports three primary user roles: **Customer**, **Admin**, and **Auditor**.

| Feature | Endpoint | Roles | Description |
|----------|-----------|--------|-------------|
| **Authentication** | `/api/auth/signup`, `/api/auth/login` | All | Secure registration and JWT-based login for all roles. |
| **KYC Submission** | `/api/kyc/customer/submit` | Customer | Customer submits details; status moves to *In Progress*. |
| **KYC Review** | `/api/kyc/admin/review` | Admin | Review submitted KYC data and set final status to *Approved* or *Reverted*. |
| **Loan Application** | `/api/loan/customer/apply` | Customer | Submit a loan application, gated by KYC Approval. |
| **Transactions** | `/api/transactions/customer/transfer` | Customer | Atomic P2P transfers checked against Global Daily Limit. |
| **Audit Logs** | `/api/auditor/audit-logs` | Auditor | Secure, read-only access to logs for all critical system actions (reviews, transactions). |

---

## 🛠️ 2. Project Structure

The architecture enforces strict **separation of concerns** (MVC-like pattern) to ensure maintainability and scalability.

smart-bank-modular/
├── controller/ # FastAPI endpoint definitions (Routers)
├── models/ # Pydantic (data models) and SQLAlchemy (ORM Schemas)
├── services/ # Core business logic (KYC, Loan, Txn, Audit logic)
├── utility/ # Common functions (DB connection, Auth, Logging)
├── pages/ # Streamlit pages (Customer, Admin, Auditor dashboards)
├── main.py # FastAPI application entry point
├── app.py # Streamlit UI application entry point
└── requirements.txt # Project dependencies


---

## 💻 3. Setup and Installation

### 3.1. Prerequisites
- **Python 3.10+**
- A database (SQLite used for quick development via ORM)

---

### 3.2. Installation Steps

**1️⃣ Clone the repository and navigate to the project directory**
```bash
cd smart-bank-modular
2️⃣ Create and activate a virtual environment
python -m venv venv
source venv/bin/activate       # macOS/Linux/Git Bash
# or
.\venv\Scripts\activate        # Windows PowerShell
3️⃣ Install dependencies
pip install -r requirements.txt
Ensure requirements.txt includes: fastapi, uvicorn, streamlit, requests, and other core libraries.

3.3. Running the Application

You must run the backend API and frontend UI concurrently in two separate terminal sessions.

🖥️ Start the FastAPI Backend (Terminal 1):

uvicorn main:app --reload


API will be available at: http://127.0.0.1:8000

🌐 Start the Streamlit Frontend (Terminal 2):

streamlit run app.py


UI will open in your browser, typically at: http://localhost:8501

🕵️ 4. Development & Testing
4.1. Initial Testing Flow

Signup:
Register at least three users via the Streamlit signup page:

Customer: user: customer1, role: customer, with an initial deposit

Admin: user: admin1, role: admin

Auditor: user: auditor1, role: auditor

Login as Customer1:

Go to the KYC tab → Submit details.

Login as Admin1:

Go to the KYC Review tab → Select Customer1’s ID → Approve the KYC.

Transaction / Loan:

Customer1 can now Apply for Loan and Transfer Funds.

Login as Auditor1:

View the Audit Logs to see all critical actions logged securely.

4.2. Running Unit Tests

The core API logic is covered by a comprehensive Pytest suite that uses mocking to isolate service layers from the database and handle authorization checks.

Run tests from your main directory:

pytest


Executes ~25 granular test cases covering all features and roles.

🧩 5. Future Enhancements (Optional Ideas)

Integration with PostgreSQL for production-grade data handling.

Microservices split for KYC, Loan, and Transaction domains.

Dockerized deployment for full-stack containerization.

Role-based access UI improvements in Streamlit.

📜 License

This project is provided as a Proof of Concept for demonstration and educational purposes.


---

Would you like me to add **badges** (Python version, FastAPI, Streamlit, License, etc.) at the top for a polished GitHub look?
