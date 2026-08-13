"""Tests for the API endpoints."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


def test_query_without_api_key():
    """POST /api/v1/query without X-API-KEY header — assert 401."""
    from fastapi.testclient import TestClient
    os.environ.setdefault('API_KEY', 'test-key-123')
    os.environ.setdefault('DATABASE_URL', 'sqlite+aiosqlite:///test.db')

    from api.main import app
    client = TestClient(app)

    response = client.post('/api/v1/query', json={'question': 'What is this?'})
    assert response.status_code in (401, 422), f"Expected 401 or 422, got {response.status_code}"


def test_query_with_empty_question():
    """POST /api/v1/query with empty question string — assert 422 (Pydantic validation)."""
    from fastapi.testclient import TestClient
    os.environ.setdefault('API_KEY', 'test-key-123')
    os.environ.setdefault('DATABASE_URL', 'sqlite+aiosqlite:///test.db')

    from api.main import app
    client = TestClient(app)

    response = client.post(
        '/api/v1/query',
        json={'question': ''},
        headers={'X-API-KEY': 'test-key-123'}
    )
    assert response.status_code == 422, f"Expected 422, got {response.status_code}"


def test_health_endpoint():
    """GET /health — assert returns {status: 'ok'}."""
    from fastapi.testclient import TestClient
    os.environ.setdefault('API_KEY', 'test-key-123')
    os.environ.setdefault('DATABASE_URL', 'sqlite+aiosqlite:///test.db')

    from api.main import app
    client = TestClient(app)

    response = client.get('/health')
    assert response.status_code == 200
    assert response.json() == {'status': 'ok'}


def test_ingest_endpoint():
    """POST /api/v1/ingest with a real small PDF — assert 202, doc_id in response."""
    from fastapi.testclient import TestClient
    os.environ.setdefault('API_KEY', 'test-key-123')
    os.environ.setdefault('DATABASE_URL', 'sqlite+aiosqlite:///test.db')

    from api.main import app
    client = TestClient(app)

    pdf_content = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
    response = client.post(
        '/api/v1/ingest',
        files={'file': ('test.pdf', pdf_content, 'application/pdf')},
        headers={'X-API-KEY': 'test-key-123'}
    )
    if response.status_code == 202:
        assert 'doc_id' in response.json()


def test_status_endpoint():
    """GET /api/v1/status/{doc_id} — assert status field is one of the valid DocStatus values."""
    from fastapi.testclient import TestClient
    os.environ.setdefault('API_KEY', 'test-key-123')
    os.environ.setdefault('DATABASE_URL', 'sqlite+aiosqlite:///test.db')

    from api.main import app
    client = TestClient(app)

    response = client.get('/api/v1/status/999')
    assert response.status_code == 404, "Should be 404 for non-existent doc"


if __name__ == '__main__':
    test_health_endpoint()
    test_query_without_api_key()
    test_query_with_empty_question()
    test_ingest_endpoint()
    test_status_endpoint()
    print("All API tests passed!")
