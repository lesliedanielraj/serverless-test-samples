"""
Unit tests for the JWT Handler module.
"""

from datetime import datetime, timedelta

import jwt
import pytest

from handlers.shared.jwt_handler import JWTDecoder


@pytest.fixture
def secret_key():
    return "test-secret-key"


@pytest.fixture
def jwt_decoder(secret_key):
    return JWTDecoder(secret_key)


@pytest.fixture
def sample_payload():
    return {
        "sub": "1234567890",
        "name": "John Doe",
        "iat": int(datetime.now().timestamp()),
        "exp": int((datetime.now() + timedelta(hours=1)).timestamp()),
    }


@pytest.fixture
def expired_payload():
    return {
        "sub": "1234567890",
        "name": "John Doe",
        "iat": int((datetime.now() - timedelta(hours=2)).timestamp()),
        "exp": int((datetime.now() - timedelta(hours=1)).timestamp()),
    }


def test_decode_valid_token(jwt_decoder, sample_payload, secret_key):
    token = jwt.encode(sample_payload, secret_key, algorithm="HS256")
    decoded = jwt_decoder.decode_token(token)
    assert decoded["sub"] == sample_payload["sub"]
    assert decoded["name"] == sample_payload["name"]


def test_decode_token_without_verification(jwt_decoder, sample_payload, secret_key):
    token = jwt.encode(sample_payload, secret_key, algorithm="HS256")
    decoded = jwt_decoder.decode_token(token, verify=False)
    assert decoded["sub"] == sample_payload["sub"]
    assert decoded["name"] == sample_payload["name"]


def test_decode_expired_token(jwt_decoder, expired_payload, secret_key):
    token = jwt.encode(expired_payload, secret_key, algorithm="HS256")
    with pytest.raises(jwt.ExpiredSignatureError):
        jwt_decoder.decode_token(token)


def test_decode_invalid_token(jwt_decoder):
    with pytest.raises(jwt.InvalidTokenError):
        jwt_decoder.decode_token("invalid.token.here")


def test_decode_token_without_secret_key():
    decoder = JWTDecoder()
    with pytest.raises(ValueError):
        decoder.decode_token("some.token.here", verify=True)


def test_get_token_expiry(jwt_decoder, sample_payload, secret_key):
    token = jwt.encode(sample_payload, secret_key, algorithm="HS256")
    expiry = jwt_decoder.get_token_expiry(token)
    assert isinstance(expiry, datetime)
    assert abs((expiry - datetime.fromtimestamp(sample_payload["exp"])).total_seconds()) < 1


def test_is_token_expired_with_expired_token(jwt_decoder, expired_payload, secret_key):
    token = jwt.encode(expired_payload, secret_key, algorithm="HS256")
    assert jwt_decoder.is_token_expired(token) is True


def test_is_token_expired_with_valid_token(jwt_decoder, sample_payload, secret_key):
    token = jwt.encode(sample_payload, secret_key, algorithm="HS256")
    assert jwt_decoder.is_token_expired(token) is False


def test_get_token_claims(jwt_decoder, sample_payload, secret_key):
    token = jwt.encode(sample_payload, secret_key, algorithm="HS256")
    claims = jwt_decoder.get_token_claims(token)
    assert claims == sample_payload


def test_generate_sample_token(jwt_decoder):
    token = jwt_decoder.generate_sample_token()
    # Decode without verification since it uses a different secret
    decoded = jwt_decoder.decode_token(token, verify=False)

    # Verify standard claims
    assert decoded["sub"] == "1234567890"
    assert decoded["iss"] == "https://api.example.com"
    assert decoded["aud"] == "example_client_id"
    assert "iat" in decoded
    assert "exp" in decoded
    assert "nbf" in decoded
    assert decoded["jti"] == "unique-jwt-id-123"

    # Verify custom claims
    assert decoded["name"] == "John Doe"
    assert decoded["email"] == "john.doe@example.com"
    assert set(decoded["roles"]) == {"user", "admin"}
    assert set(decoded["permissions"]) == {"read", "write", "delete"}
    assert decoded["org_id"] == "org_123456"

    # Verify nested metadata
    assert decoded["user_metadata"]["first_name"] == "John"
    assert decoded["user_metadata"]["last_name"] == "Doe"
    assert decoded["user_metadata"]["country"] == "US"
    assert decoded["user_metadata"]["verified"] is True

    # Verify token is not expired
    assert not jwt_decoder.is_token_expired(token)
