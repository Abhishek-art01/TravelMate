import base64
import time

import jwt
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _b64url(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b'=').decode('ascii')


def _make_signed_token(private_key_pem: str, *, kid: str = 'test-kid-1', user_id: str = 'supabase-user-123') -> str:
    now = int(time.time())
    payload = {
        'sub': user_id,
        'email': 'user@example.com',
        'role': 'user',
        'iss': 'https://example.supabase.co/auth/v1',
        'aud': 'authenticated',
        'exp': now + 300,
        'iat': now,
        'nbf': now,
        'app_metadata': {'provider': 'email'},
    }
    return jwt.encode(payload, private_key_pem, algorithm='RS256', headers={'kid': kid, 'alg': 'RS256'})


def test_me_requires_authentication() -> None:
    response = client.get('/api/v1/users/me')
    assert response.status_code == 401
    assert response.json()['error']['code'] == 'AUTHENTICATION_REQUIRED'


def test_profile_age_validation_rejects_underage_users() -> None:
    payload = {
        'display_name': 'Young Explorer',
        'date_of_birth': '2015-01-01',
        'bio': 'Too young to join TravelMate.',
    }

    response = client.post('/api/v1/profiles', json=payload)
    assert response.status_code == 422
    assert 'at least 18' in response.json()['detail'][0]['msg']


def test_valid_jwt_is_verified_against_jwks(monkeypatch) -> None:
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import rsa

    from app import config

    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_key = private_key.public_key()
    public_numbers = public_key.public_numbers()
    public_jwk = {
        'kty': 'RSA',
        'alg': 'RS256',
        'use': 'sig',
        'kid': 'test-kid-1',
        'n': _b64url(public_numbers.n.to_bytes((public_numbers.n.bit_length() + 7) // 8, 'big')),
        'e': _b64url(public_numbers.e.to_bytes((public_numbers.e.bit_length() + 7) // 8, 'big')),
    }

    private_key_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption(),
    )

    monkeypatch.setattr(config.get_settings(), 'supabase_jwks_url', 'https://example.supabase.co/auth/v1/jwks')
    monkeypatch.setattr(config.get_settings(), 'supabase_jwt_issuer', 'https://example.supabase.co/auth/v1')
    monkeypatch.setattr(config.get_settings(), 'supabase_jwt_audience', 'authenticated')

    from app.core import security

    monkeypatch.setattr(security, '_fetch_jwks_document', lambda _: {'keys': [public_jwk]})

    token = _make_signed_token(private_key_pem.decode(), kid='test-kid-1', user_id='supabase-user-123')
    response = client.get('/api/v1/users/me', headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 200
    assert response.json()['user_id'] == 'supabase-user-123'


def test_admin_route_requires_permission(monkeypatch) -> None:
    from app.core.security import get_current_user

    async def fake_user() -> dict:
        return {'user_id': 'user-1', 'email': 'user@example.com', 'role': 'user', 'permissions': ['profile.read']}

    app.dependency_overrides[get_current_user] = fake_user
    try:
        response = client.get('/api/v1/admin/system')
    finally:
        app.dependency_overrides.clear()
    assert response.status_code == 403


def test_super_admin_can_access_admin_route(monkeypatch) -> None:
    from app.core.security import get_current_user

    async def fake_user() -> dict:
        return {'user_id': 'admin-1', 'email': 'admin@example.com', 'role': 'super_admin', 'permissions': ['system.manage']}

    app.dependency_overrides[get_current_user] = fake_user
    try:
        response = client.get('/api/v1/admin/system')
    finally:
        app.dependency_overrides.clear()
    assert response.status_code == 200
    assert response.json()['ok'] is True
