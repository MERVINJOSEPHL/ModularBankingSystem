# smart-bank-modular/main.py

from fastapi import FastAPI, HTTPException
from controller import signup_login_controller, loan_controller, kyc_controller,transaction_controller,auditor_controller
from utility.logging import setup_logger
from utility.database import create_tables, engine

logger = setup_logger(__name__)

# --- Database Initialization ---
try:
    create_tables() 
    logger.info("Database tables created successfully or already exist.")
except Exception as e:
    logger.error(f"Failed to create database tables: {e}")

# --- FastAPI App Declaration (FIXED) ---
app = FastAPI(
    title="Smart Bank Modular Banking System POC",
    description="API for multi-user authentication and core banking features.",
    
    # FIX: Define the security scheme using 'apiKey' in 'header'
    # This forces Swagger UI to show the simple token input field.
    openapi_extra={
        "securitySchemes": {
            "BearerAuth": {
                "type": "apiKey", 
                "in": "header",    
                "name": "Authorization", 
                "description": "Enter the JWT Bearer token (e.g., 'Bearer <token>')"
            }
        },
    }
)

# --- Router Inclusion ---
app.include_router(signup_login_controller.router, prefix="/api/auth")
app.include_router(loan_controller.router, prefix="/api/loan")
app.include_router(kyc_controller.router, prefix="/api/kyc")
app.include_router(transaction_controller.router, prefix="/api/transactions")
app.include_router(auditor_controller.router, prefix="/api/auditor")

@app.get("/")
def read_root():
    """Returns a basic status message for the root endpoint."""
    logger.info("Root endpoint accessed.")
    return {"message": "Smart Bank API is running."}


@app.get("/health")
def health_check(): 
    """
    Checks the database connection status.
    FIX: Removed 'db_engine=engine' from the signature to eliminate Pydantic warning.
    """
    try:
        with engine.connect(): 
            return {"status": "ok", "database": "connected"}
    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Database connection failed."
        )

# --- Uvicorn Startup ---
if __name__ == "__main__":
    import uvicorn
    logger.info("Starting Uvicorn server...")
    uvicorn.run(app, host="0.0.0.0", port=8000)