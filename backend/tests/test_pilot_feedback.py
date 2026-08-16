from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


def test_pilot_feedback_requires_authentication():
    response = client.post('/pilot-feedback', json={
        'provider': 'openai-grounded-v1',
        'recommendation': 'CONSIDER',
        'application_type': 'statement_of_suitability',
        'word_count': 320,
        'usefulness': 8,
        'would_submit': True,
        'recommendation_trust': True,
        'material_time_saving': True,
        'would_use_again': True,
        'payment_signal': 'maybe',
    })
    assert response.status_code == 401


def test_pilot_feedback_validates_score_and_payment_signal():
    response = client.post('/pilot-feedback', headers={'Authorization': 'Bearer valid_token'}, json={
        'usefulness': 11,
        'would_submit': True,
        'recommendation_trust': True,
        'material_time_saving': True,
        'would_use_again': True,
        'payment_signal': 'unknown',
    })
    assert response.status_code == 422
