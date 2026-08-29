from fastapi.testclient import TestClient

import app.main as main


client = TestClient(main.app)


# =========================
# HEALTH TEST
# =========================

def test_health():

    response = client.get("/health")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "healthy"
    assert data["service"] == "JAA.AI"


# =========================
# EMPTY QUESTION TEST
# =========================

def test_empty_question():

    response = client.get(
        "/ask",
        params={
            "question": ""
        }
    )

    assert response.status_code == 400


# =========================
# LONG QUESTION TEST
# =========================

def test_question_too_long():

    long_question = "a" * 1001

    response = client.get(
        "/ask",
        params={
            "question": long_question
        }
    )

    assert response.status_code == 400


# =========================
# ASK AI TEST
# =========================

def test_ask_ai(monkeypatch):

    def fake_ask_ai(
        question,
        session_id
    ):

        return {
            "answer": "Test answer",
            "sources": [
                "test.pdf"
            ]
        }

    monkeypatch.setattr(
        main,
        "ask_ai",
        fake_ask_ai
    )

    response = client.get(
        "/ask",
        params={
            "question": "What is DBMS?",
            "session_id": "test-session"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["answer"] == "Test answer"

    assert data["session_id"] == "test-session"

    assert "test.pdf" in data["sources"]


# =========================
# HISTORY TEST
# =========================

def test_history(monkeypatch):

    monkeypatch.setattr(
        main,
        "get_chat_history",
        lambda session_id: []
    )

    response = client.get(
        "/history/test-session"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["session_id"] == "test-session"

    assert data["messages"] == []


# =========================
# DELETE CHAT TEST
# =========================

def test_delete_chat(monkeypatch):

    deleted = {
        "value": False
    }

    def fake_delete_chat(session_id):

        deleted["value"] = True

    monkeypatch.setattr(
        main,
        "delete_chat",
        fake_delete_chat
    )

    response = client.delete(
        "/history/test-session"
    )

    assert response.status_code == 200

    assert deleted["value"] is True

    data = response.json()

    assert (
        data["message"]
        == "Chat deleted successfully"
    )


# =========================
# INVALID FILE TEST
# =========================

def test_upload_non_pdf():

    response = client.post(
        "/upload",
        files={
            "file": (
                "test.txt",
                b"Hello JAA.AI",
                "text/plain"
            )
        }
    )

    assert response.status_code == 400