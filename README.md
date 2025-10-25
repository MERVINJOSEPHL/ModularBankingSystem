# 🏦 Smart Bank Modular Banking System (5-Hour POC)

## 1. Project Goal and Scope

This project delivers a **Proof of Concept (PoC)** within a strict **5-hour limit**. The primary objective is to prove the technical viability of the system's core security and its most complex feature: integrating an **offline LLaMA model** for fraud analysis.

### Focus: LLaMA Fraud Integration Structure

The PoC demonstrates the essential pipeline: how structured transactional data is sent to a dedicated function (simulating the **LLaMA model**) for analysis, and how the resulting `FRAUD` flag is persisted in the PostgreSQL database.

---

## 2. Achieved Architecture & Tech Stack

This PoC uses a focused technology stack to achieve a secure vertical slice.

| Component | Technology | Role (5-Hour Scope) |
| :--- | :--- | :--- |
| **Backend API** | **FastAPI** | High-performance API for handling authentication and the single transaction route. |
| **Database** | **PostgreSQL** | Stores **`User`** records, **`Transaction`**, and **`Fraud_Flag`** records. |
| **Data Validation**| **Pydantic** | Used to validate input for sign-up, login, and transaction data. |
| **Frontend UI** | **Streamlit** | Provides a functional **Login Form** and a basic transaction input interface. |
| **Authentication**| **JWT** & **Password Hashing** | Secure login and token-based access to the protected transaction route. |
| **Fraud Model** | **LLaMA (Mocked Offline)** | A Python function that takes structured transaction data and returns a hardcoded **"FRAUD"** decision, simulating the LLaMA model's secure, local output. |

---

## 3. Core Features Demonstrated

The PoC demonstrates the end-to-end flow of a secured user submitting a transfer that gets immediately flagged for fraud.

### 3.1. Authentication Flow
* **Customer Sign Up:** Register a user with **password hashing**.
* **Customer Login:** Obtain and use a **JWT** for subsequent requests.
* **Protected Access:** The JWT is required to access the transaction endpoint.

### 3.2. Transaction & Fraud Flagging Pipeline

1.  **Submission:** Customer inputs a test transfer via the Streamlit UI.
2.  **API Validation:** FastAPI validates the input using Pydantic.
3.  **LLaMA Call:** The system calls the **mock LLaMA function** with the data.
4.  **Flagging:** The function returns a pre-determined **"FRAUD"** decision.
5.  **Persistence:** The system logs the transaction and creates a corresponding **`Fraud_Flag`** record in PostgreSQL.

---

## 4. Work Items Completed (The 5-Hour Deliverable)

| Work Item | Status |
| :--- | :--- |
| **Project & DB Setup** | FastAPI structure, Pydantic, and basic PostgreSQL connection configured. |
| **Database Schema** | **`User`**, **`Transaction`**, and **`Fraud_Flag`** tables created in PostgreSQL. |
| **Security Core** | Working **Login/Signup** endpoints with JWT generation and password hashing. |
| **Frontend POC** | Streamlit UI with functional **Login Form** and JWT handling. |
| **LLaMA Integration** | **`POST /api/transactions/transfer`** endpoint implemented, successfully calling the function that simulates the **LLaMA model's offline classification**. |
| **Testing** | Basic **Pytest** for the primary login flow. |

---

## 5. Installation and Setup

### Prerequisites

* Python 3.10+
* PostgreSQL running locally.
* The actual LLaMA code/access is assumed to be available locally (or the mock function will be used).

### Instructions

1.  **Clone & Setup:**
    ```bash
    git clone [repository_url]
    cd smart-bank-modular
    pip install -r requirements.txt
    # Configure DB details in a .env file
    ```
2.  **Database Migration:** Run your migration script to create the necessary `User`, `Transaction`, and `Fraud_Flag` tables.
3.  **Start the Backend (FastAPI):**
    ```bash
    uvicorn app.main:app --reload
    ```
4.  **Start the Frontend (Streamlit):**
    In a separate terminal, start the UI:
    ```bash
    streamlit run ui/app.py
    ```

Navigate to the Streamlit app, sign up, log in, and perform a test transfer to demonstrate the LLaMA fraud pipeline working end-to-end.
