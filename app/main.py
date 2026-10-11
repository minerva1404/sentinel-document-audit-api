from fastapi import FastAPI
from sqlalchemy import text

from app.api.routes import audit, auth, documents
from app.db.session import engine

app = FastAPI(
    title="Sentinel",
    description=(
        "Secure Document Management, Role-Based Access Control, "
        "and Audit Logging API"
    ),
    version="1.0.0",
)

app.include_router(auth.router, prefix="/api/v1")
app.include_router(documents.router, prefix="/api/v1")
app.include_router(audit.router, prefix="/api/v1")


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "healthy"}


@app.get("/health/database", tags=["Health"])
def database_health_check():
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
    return {"status": "healthy", "database": "connected"}