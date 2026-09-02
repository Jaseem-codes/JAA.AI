from fastapi.testclient import TestClient

from app.main import app


client = TestClient(
    app,
    base_url="http://localhost"
)


# =========================
# HEALTH CHECK
# =========================

def test_health():

    response = client.get("/health")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "healthy"


# =========================
# EMPTY QUESTION
# =========================

def test_empty_question_rejected():

    response = client.get(
        "/ask",
        params={
            "question": ""
        }
    )

    assert response.status_code == 400


# =========================
# LONG QUESTION
# =========================

def test_question_too_long_rejected():

    long_question = "A" * 1001

    response = client.get(
        "/ask",
        params={
            "question": long_question
        }
    )

    assert response.status_code == 400


# =========================
# INVALID SESSION ID
# =========================

def test_invalid_session_id_rejected():

    response = client.get(
        "/ask",
        params={
            "question": "What is DBMS?",
            "session_id": "invalid session!"
        }
    )

    assert response.status_code == 400


# =========================
# NON PDF UPLOAD
# =========================

def test_non_pdf_upload_rejected():

    response = client.post(
        "/upload",
        files={
            "file": (
                "test.txt",
                b"This is not a PDF",
                "text/plain"
            )
        }
    )

    assert response.status_code == 400