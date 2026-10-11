import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.user import User


def create_user(
    db: Session,
    email: str,
    role: str,
    password: str = "TestPassword123!",
) -> User:
    user = User(
        email=email,
        hashed_password=hash_password(password),
        role=role,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def login(client: TestClient, email: str) -> dict:
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": email,
            "password": "TestPassword123!",
        },
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_registration_and_login(client: TestClient):
    registration = client.post(
        "/api/v1/auth/register",
        json={
            "email": "newuser@example.com",
            "password": "TestPassword123!",
        },
    )

    assert registration.status_code == 201
    assert registration.json()["role"] == "Viewer"

    headers = login(client, "newuser@example.com")
    response = client.get("/api/v1/documents", headers=headers)

    assert response.status_code == 200
    assert response.json() == []


def test_duplicate_registration_is_rejected(client: TestClient):
    payload = {
        "email": "duplicate@example.com",
        "password": "TestPassword123!",
    }

    assert client.post("/api/v1/auth/register", json=payload).status_code == 201
    assert client.post("/api/v1/auth/register", json=payload).status_code == 409


def test_invalid_login_is_rejected(client: TestClient):
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "missing@example.com",
            "password": "WrongPassword123!",
        },
    )

    assert response.status_code == 401


def test_editor_document_crud_and_audit_logs(
    client: TestClient,
    db_session: Session,
):
    create_user(db_session, "editor@example.com", "Editor")
    headers = login(client, "editor@example.com")

    created = client.post(
        "/api/v1/documents",
        headers=headers,
        json={"title": "Initial document", "content": "Original content"},
    )

    assert created.status_code == 201
    document_id = created.json()["id"]

    retrieved = client.get(
        f"/api/v1/documents/{document_id}",
        headers=headers,
    )
    assert retrieved.status_code == 200

    updated = client.patch(
        f"/api/v1/documents/{document_id}",
        headers=headers,
        json={"title": "Updated document"},
    )
    assert updated.status_code == 200
    assert updated.json()["title"] == "Updated document"

    logs = client.get("/api/v1/audit-logs", headers=headers)
    assert logs.status_code == 403

    deleted = client.delete(
        f"/api/v1/documents/{document_id}",
        headers=headers,
    )
    assert deleted.status_code == 204

    # Verify audit events as an Admin.
    create_user(db_session, "admin@example.com", "Admin")
    admin_headers = login(client, "admin@example.com")

    logs = client.get("/api/v1/audit-logs", headers=admin_headers)
    assert logs.status_code == 200

    actions = [entry["action"] for entry in logs.json()]
    assert actions.count("document.created") == 1
    assert actions.count("document.updated") == 1
    assert actions.count("document.deleted") == 1


def test_viewer_cannot_create_documents(
    client: TestClient,
    db_session: Session,
):
    create_user(db_session, "viewer@example.com", "Viewer")
    headers = login(client, "viewer@example.com")

    response = client.post(
        "/api/v1/documents",
        headers=headers,
        json={"title": "Not allowed", "content": "Viewer content"},
    )

    assert response.status_code == 403


def test_editor_cannot_access_another_users_document(
    client: TestClient,
    db_session: Session,
):
    create_user(db_session, "owner@example.com", "Editor")
    create_user(db_session, "other@example.com", "Editor")

    owner_headers = login(client, "owner@example.com")
    other_headers = login(client, "other@example.com")

    created = client.post(
        "/api/v1/documents",
        headers=owner_headers,
        json={"title": "Private document", "content": "Private content"},
    )
    assert created.status_code == 201

    document_id = created.json()["id"]

    response = client.get(
        f"/api/v1/documents/{document_id}",
        headers=other_headers,
    )
    assert response.status_code == 403


def test_auditor_can_read_but_cannot_create_documents(
    client: TestClient,
    db_session: Session,
):
    create_user(db_session, "auditor@example.com", "Auditor")
    headers = login(client, "auditor@example.com")

    response = client.post(
        "/api/v1/documents",
        headers=headers,
        json={"title": "Not allowed", "content": "Auditor content"},
    )
    assert response.status_code == 403

    logs = client.get("/api/v1/audit-logs", headers=headers)
    assert logs.status_code == 200