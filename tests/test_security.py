import pytest
import jwt

from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from app.schemas.auth import RegisterRequest


def test_password_hashing():
    password = "ExamplePassword123!"
    hashed = hash_password(password)

    assert hashed != password
    assert verify_password(password, hashed)
    assert not verify_password("WrongPassword123!", hashed)


def test_access_token():
    token = create_access_token(subject="123")
    payload = decode_access_token(token)

    assert payload["sub"] == "123"
    assert "exp" in payload
    assert "iat" in payload


def test_invalid_token_is_rejected():
    with pytest.raises(jwt.PyJWTError):
        decode_access_token("this-is-not-a-valid-token")


def test_registration_cannot_assign_admin_role():
    request = RegisterRequest(
        email="viewer@example.com",
        password="ExamplePassword123!",
        role="Admin",
    )

    assert not hasattr(request, "role")