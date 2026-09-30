from datetime import date

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_me_requires_authentication() -> None:
    response = client.get('/api/v1/me')
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
