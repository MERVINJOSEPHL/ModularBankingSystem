# main.py
from fastapi import FastAPI,HTTPException
from controller import signup_login_controller
from utility.logging import setup_logger
from utility.database import create_tables, engine

logger = setup_logger(__name__)

try:
    create_tables() 
    logger.info("Database tables created successfully or already exist.")
except Exception as e:
    logger.error(f"Failed to create database tables: {e}")

app = FastAPI(
    title="Smart Bank Modular Banking System POC",
    description="API for multi-user authentication and core banking features."
)

# Include the authentication router
app.include_router(signup_login_controller.router, prefix="/api/auth")

@app.get("/")
def read_root():
    """Returns a basic status message for the root endpoint."""
    logger.info("Root endpoint accessed.")
    return {"message": "Smart Bank API is running."}

# Add a simple endpoint to test table creation/connection if needed
@app.get("/health")
def health_check(db_engine=engine):
    """Checks the database connection status."""
    try:
        with db_engine.connect():
            return {"status": "ok", "database": "connected"}
    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Database connection failed."
        )

if __name__ == "__main__":
    # This block is for local development using Uvicorn
    import uvicorn
    logger.info("Starting Uvicorn server...")
    uvicorn.run(app, host="0.0.0.0", port=8000)