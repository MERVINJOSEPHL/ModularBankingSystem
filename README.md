# 🏦 Smart Bank Modular Banking System (Final PoC Scope)

## 1. Project Goal and Core Flow

This Proof of Concept (PoC) establishes a secure, modular banking system focused on the essential Customer and Admin workflows, driven by robust **JWT authentication** and cutting-edge **LLaMA-powered fraud detection**.

### Key System Flow
1.  **Customer Onboarding:** Sign up $\rightarrow$ KYC Verification $\rightarrow$ Account Creation (Saving/Deposit Type).
2.  **Customer Actions:** Login via JWT $\rightarrow$ Request Loan OR $\rightarrow$ Make Transaction.
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
