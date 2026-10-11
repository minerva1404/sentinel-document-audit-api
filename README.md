# Sentinel — Secure Document Management & Audit API

A secure, RESTful document management API built with FastAPI, PostgreSQL, SQLAlchemy, JWT authentication, Role-Based Access Control (RBAC), and audit logging.

Sentinel demonstrates backend engineering practices for applications that manage sensitive business documents, including authenticated access, permission enforcement, document ownership, and traceable operations.

## Overview

Organizations need to ensure that documents are accessible only to authorized users and that important actions can be traced.

Sentinel addresses these requirements through a REST API that provides:

- Secure user registration and login
- Password hashing and JWT-based authentication
- Role-Based Access Control (RBAC)
- Document creation, retrieval, updating, and deletion
- Document ownership enforcement
- Audit logging for document mutations
- Restricted access to audit records
- Automated unit and integration tests
- Continuous integration with GitHub Actions
- Cloud deployment with Render and Supabase PostgreSQL

## Live Deployment

- **API Base URL:** https://sentinel-document-audit-api.onrender.com
- **Interactive API Documentation:** https://sentinel-document-audit-api.onrender.com/docs
- **Health Check:** https://sentinel-document-audit-api.onrender.com/health
- **Database Health Check:** https://sentinel-document-audit-api.onrender.com/health/database

## Technology Stack

| Technology | Purpose |
|---|---|
| Python 3.12 | Backend programming language |
| FastAPI | REST API framework |
| PostgreSQL | Production relational database |
| Supabase | Managed PostgreSQL hosting |
| SQLAlchemy | ORM and database interaction |
| Alembic | Database schema migrations |
| Pydantic | Request validation and data schemas |
| JWT | Stateless authentication |
| pwdlib with Argon2 | Password hashing |
| Pytest | Automated testing |
| HTTPX | API integration testing |
| GitHub Actions | Continuous integration |
| Render | API deployment |

## Architecture

```text
Client
  |
  v
FastAPI Application
  |
  +--> Authentication & JWT
  |
  +--> Role-Based Access Control
  |
  +--> Document Management
  |       |
  |       +--> Ownership & Permission Checks
  |
  +--> Audit Logging
  |
  v
SQLAlchemy ORM
  |
  v
PostgreSQL (Supabase)
```

GitHub Actions runs the automated test suite when changes are pushed to the repository or a pull request targets the main branch.

## Authentication and Authorization

Sentinel uses JWT bearer tokens to authenticate API requests.

### Authentication Flow

1. A user registers with an email address and password.
2. The password is hashed before storage.
3. The user logs in with valid credentials.
4. The API returns an access token.
5. The client sends the token in the `Authorization` header for protected endpoints.
6. The API validates the token and checks the user's permissions before allowing access.

Example authorization header:

```http
Authorization: Bearer YOUR_ACCESS_TOKEN
```

Newly registered users receive the Viewer role by default. Registration does not allow users to assign themselves privileged roles.

## Role-Based Access Control

Sentinel implements four application roles.

| Role | Permissions |
|---|---|
| Viewer | View documents they are authorized to access |
| Editor | Create, view, update, and delete their own documents |
| Auditor | Read documents and audit records according to the application's authorization rules |
| Admin | Administrative access to documents and audit records |

Document ownership and role checks are enforced by the API. A user cannot access another user's private document merely by changing the document ID in a request.

Privileged roles should be assigned only through an authorized administrative process.

## API Endpoints

The versioned API prefix is `/api/v1`.

### Authentication

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/api/v1/auth/register` | Register a user |
| POST | `/api/v1/auth/login` | Authenticate and obtain a JWT |

### Documents

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/v1/documents` | List documents available to the authenticated user |
| POST | `/api/v1/documents` | Create a document when permitted |
| GET | `/api/v1/documents/{document_id}` | Retrieve a document when permitted |
| PATCH | `/api/v1/documents/{document_id}` | Update a document when permitted |
| DELETE | `/api/v1/documents/{document_id}` | Delete a document when permitted |

### Audit Logs

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/v1/audit-logs` | Retrieve audit records for authorized roles |

### Health

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/health` | Check application health |
| GET | `/health/database` | Check database connectivity |

The interactive Swagger UI is available at [`/docs`](https://sentinel-document-audit-api.onrender.com/docs) on the deployed service.

## Audit Logging

Sentinel records important document operations so authorized users can inspect activity.

Audit entries include information such as:

- The actor associated with an operation
- The action performed
- The affected resource type and identifier
- Relevant structured details
- The timestamp of the event

Document mutations and their corresponding audit records are committed within the same database transaction.

Audit records are exposed through a read-restricted API endpoint. The application is designed to prevent ordinary API users from modifying audit records through the provided endpoints; this is application-level protection, not a claim of database-enforced immutability.

## Database and Migrations

Sentinel uses SQLAlchemy models and Alembic migrations to manage its relational schema.

The database contains entities for:

- Users
- Documents
- Audit logs

The initial Alembic migration creates the core tables and their relationships.

For environments that require schema changes, generate and review migrations rather than manually altering production tables.

Generate a migration:

```bash
alembic revision --autogenerate -m "describe schema change"
```

Apply migrations:

```bash
alembic upgrade head
```

Review autogenerated migration files before applying them.

## Local Development

### Prerequisites

- Python 3.12
- Git
- A PostgreSQL database
- A terminal and code editor

### 1. Clone the Repository

```bash
git clone https://github.com/minerva1404/sentinel-document-audit-api
cd sentinel-document-audit-api
```

Replace `YOUR_GITHUB_USERNAME` with the GitHub account that owns the repository.

### 2. Create a Virtual Environment

```bash
python -m venv .venv
```

Activate it in Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

### 3. Install Dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a local `.env` file using `.env.example` as a reference.

```powershell
Copy-Item .env.example .env
```

Set the following values in `.env`:

```dotenv
DATABASE_URL=postgresql+psycopg://USER:PASSWORD@HOST:5432/DATABASE
SECRET_KEY=replace_with_a_long_random_secret
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

Use your own database credentials and a securely generated secret. The example values are placeholders and are not production credentials.

Never commit `.env` or expose database credentials, passwords, or JWT signing secrets.

### 5. Apply Database Migrations

```bash
alembic upgrade head
```

Run this against a development database configured for your local environment. Do not run migrations against production without reviewing the change and confirming the target database.

### 6. Start the Application

```bash
uvicorn app.main:app --reload
```

Open the following local URLs:

- **API:** http://127.0.0.1:8000
- **Swagger UI:** http://127.0.0.1:8000/docs
- **Health Check:** http://127.0.0.1:8000/health

## Testing

Run the complete automated test suite:

```bash
python -m pytest -q
```

The test suite covers authentication, registration, duplicate-registration rejection, invalid login, document CRUD operations, role restrictions, document ownership, and audit-log access.

The tests use an isolated SQLite database through SQLAlchemy dependency overrides, keeping automated integration tests separate from the production PostgreSQL database.

## Continuous Integration

The GitHub Actions workflow in `.github/workflows/ci.yml`:

1. Checks out the repository.
2. Sets up Python.
3. Installs project dependencies.
4. Runs the automated test suite.

A successful workflow confirms that the configured automated tests pass in the CI environment. It does not replace production smoke tests or a full security review.

## Deployment

Sentinel is deployed as a web service on Render and uses Supabase PostgreSQL for its production database.

### Render Configuration

**Build Command**

```bash
pip install -r requirements.txt
```

**Start Command**

```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

### Required Environment Variables

| Variable | Purpose |
|---|---|
| `DATABASE_URL` | Sentinel production PostgreSQL connection string |
| `SECRET_KEY` | Secret used for JWT signing |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access-token lifetime in minutes |

Configure secrets through Render's environment settings. Keep the production database separate from local development and automated test databases.

After deployment, verify `/health`, `/health/database`, and `/docs`. Do not expose secrets in logs, screenshots, source code, or public documentation.

## Security Considerations

- Passwords are hashed instead of stored in plaintext.
- Protected endpoints require authentication.
- Role and document-ownership checks restrict access.
- Public registration assigns the least-privileged default role.
- Audit records are available only to authorized roles.
- Environment-specific credentials are configured outside the repository.
- Automated tests verify key authentication and authorization behavior.

This project demonstrates security-oriented API design; it is not a claim of independent penetration testing, formal compliance certification, or complete production security assurance.

## Future Improvements

Potential extensions include:

- Refresh-token rotation and revocation
- Rate limiting and brute-force protection
- Pagination and filtering for large document collections
- Document version history
- Stronger database-level audit protections
- Structured application logging and monitoring
- Automated deployment smoke tests
- Expanded authorization and security test coverage

## Project Structure

```text
sentinel-document-audit-api/
├── .github/
│   └── workflows/
│       └── ci.yml
├── alembic/
│   └── versions/
├── app/
│   ├── api/
│   │   ├── routes/
│   │   │   ├── audit.py
│   │   │   ├── auth.py
│   │   │   └── documents.py
│   │   ├── deps.py
│   │   └── __init__.py
│   ├── core/
│   │   ├── config.py
│   │   └── security.py
│   ├── db/
│   │   └── session.py
│   ├── models/
│   ├── schemas/
│   ├── create_admin.py
│   └── main.py
├── tests/
│   ├── conftest.py
│   ├── test_api.py
│   └── test_security.py
├── .env.example
├── .gitignore
├── alembic.ini
├── requirements.txt
└── README.md
```

## Author

**Angel Minerva Unnava**

Backend engineering portfolio project focused on secure REST API development, authentication, authorization, database design, auditability, automated testing, and cloud deployment.
