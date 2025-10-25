# 🏦 Smart Bank Modular Banking System

## 1. Project Overview & Problem Statement

The **Smart Bank Modular Banking System** is a full-stack application designed to create a secure, role-based digital banking environment. It modernizes core functionalities—Customer transactions, Loan processing, and Administrative oversight—by integrating advanced security and logging features.

### Problem Solved: LLaMA-Powered Fraud Detection

Traditional banking fraud detection often relies on rigid rules or external, internet-dependent ML services. This project implements an innovative, **offline LLaMA (Large Language Model) model** for real-time, contextual fraud scoring. By keeping the LLaMA model and sensitive transaction data local, we achieve **maximum security and data privacy** while enabling a flexible, expert-system approach to anomaly detection.

---

## 2. Architecture & Tech Stack

This project uses a modern, modular architecture with a powerful, performant backend and a fast, interactive frontend.

| Component | Technology | Rationale & Use |
| :--- | :--- | :--- |
| **Backend API** | **FastAPI** | High-performance API framework for rapid development and asynchronous operations. |
| **Database** | **PostgreSQL** | Robust, open-source relational database for structured storage of financial data and audit logs. |
| **Data Validation**| **Pydantic** | Ensures strict **input validation** and data integrity across all API endpoints (e.g., transaction amounts, loan terms). |
| **Frontend UI** | **Streamlit** | Used for building a simple, interactive, multi-role user interface (Customer, Admin, Auditor) quickly. |
| **Authentication**| **JWT (JSON Web Tokens)** & **`passlib/bcrypt`** | Secure, stateless authentication with **password hashing** for all three user roles and role-based access control (RBAC). |
| **Fraud Model** | **LLaMA Model (Offline/Local)** | Processes structured transaction data (via prompting) to provide a **FRAUD/NOT\_FRAUD** decision and justification, ensuring high security and data residency. |
| **Testing** | **Pytest** | Framework for developing a comprehensive suite of unit and integration tests for the API logic. |

---

## 3. Key System Features

The system supports three distinct user roles, each with specific access controls.

### 3.1. 👨‍💻 Customer Operations

Customers interact with the core banking features after secure JWT login.

| Feature | Description | API Endpoints |
| :--- | :--- | :--- |
| **Account Management** | View account details and summaries for **Saving, Current, and FD** accounts. | `GET /api/accounts/summary` |
| **Transaction** | Perform fund transfers after **balance validation** and limit checks. | `POST /api/transactions/transfer` |
| **Loan Application** | Submit new loan requests (Loan Type, Amount, Tenure). | `POST /api/loans/apply` |
| **Status Check** | View transaction history and the repayment status of active/past loans. | `GET /api/loans/{loan_id}/status` |

### 3.2. 🚨 Fraud Detection & Flagging

This process runs immediately after a customer attempts a large or unusual transaction.

1.  **Data Transformation:** Transaction data is structured into a text prompt, including historical context and anti-fraud rules.
2.  **LLaMA Execution:** The **offline LLaMA model** is queried with the prompt.
3.  **Decision & Logging:** If the LLaMA model classifies the transaction as **FRAUD**, an immutable record is created in the **`Fraud_Flag`** table.
4.  **Issue Raised:** An immediate notification/flag appears on the Admin dashboard.

### 3.3. 💼 Bank Admin Operations

Admins are responsible for high-level oversight and resolving flagged issues.

| Feature | Description |
| :--- | :--- |
| **Review Flagged Transactions** | View transactions marked as **FRAUD** by the LLaMA model, review the model's reason, and manually decide to **Approve/Reject** the transaction. |
| **Loan Approval** | Review and approve or reject pending loan applications. |
| **Account/Log Review** | See customer requests and review system-level flags. |

### 3.4. 📝 Auditor Operations (Multi-Logging System)

The Auditor has read-only access to system activity for compliance and review.

| Feature | Description |
| :--- | :--- |
| **Audit Log Viewing** | Access the complete, time-stamped log of all significant activities across the system. |
| **Activity Review** | Review log entries, which include the **`user_id`**, **`timestamp`**, **`action`** (e.g., 'LOGIN', 'TRANSFER', 'LOAN\_APPROVED'), and **`ip_address`**. |
| **Log Storage** | Every system action is noted in the central `Audit_Log` database table (replacing the file system log mentioned previously for better security and querying). |

---

## 4. Installation and Setup

### Prerequisites

* Python 3.10+
* PostgreSQL Database
* A local LLaMA instance accessible via a private API (e.g., using Ollama or a dedicated server)

### Steps

1.  **Clone the Repository:**
    ```bash
    git clone [repository_url]
    cd smart-bank-modular
    ```

2.  **Setup Environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    ```

3.  **Configure Environment Variables:**
    Create a `.env` file with your PostgreSQL connection details, JWT secret key, and LLaMA endpoint configuration.

4.  **Database Migration (PostgreSQL):**
    Run the initial migration script to create all necessary tables (`User`, `Account`, `Transaction`, `Audit_Log`, etc.).

5.  **Run the API (FastAPI):**
    ```bash
    uvicorn app.main:app --reload
    ```

6.  **Run the Frontend (Streamlit):**
    In a separate terminal, start the UI:
    ```bash
    streamlit run ui/app.py
    ```

---

## 5. Testing

All core application logic is covered by **Pytest**.

To run tests:

```bash
pytest
