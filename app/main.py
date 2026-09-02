from pathlib import Path
from typing import Optional
import os
import uuid
import re

from fastapi import (
    FastAPI,
    HTTPException,
    UploadFile,
    File,
    Request
)

from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

from document_ingest import ingest_pdf
from agent.agent import ask_ai

from database import (
    delete_chat,
    get_chat_history
)


# =========================
# RATE LIMITER
# =========================

limiter = Limiter(
    key_func=get_remote_address
)


# =========================
# APP
# =========================

app = FastAPI(
    title="JAA.AI",
    version="1.0.0"
)

app.state.limiter = limiter

app.add_exception_handler(
    429,
    _rate_limit_exceeded_handler
)


# =========================
# DIRECTORIES
# =========================

BASE_DIR = Path(__file__).resolve().parent.parent

UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

FRONTEND_DIR = BASE_DIR / "app" / "frontend"
INDEX_FILE = FRONTEND_DIR / "index.html"


# =========================
# SECURITY SETTINGS
# =========================

MAX_PDF_SIZE = 10 * 1024 * 1024
MAX_QUESTION_LENGTH = 1000
MAX_SESSION_ID_LENGTH = 100


# =========================
# CORS
# =========================

ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "ALLOWED_ORIGINS",
        "http://127.0.0.1:8000,http://localhost:8000"
    ).split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=[
        "GET",
        "POST",
        "DELETE"
    ],
    allow_headers=[
        "Content-Type"
    ],
)


# =========================
# TRUSTED HOST
# =========================

ALLOWED_HOSTS = [
    host.strip()
    for host in os.getenv(
        "ALLOWED_HOSTS",
        "127.0.0.1,localhost"
    ).split(",")
    if host.strip()
]

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=ALLOWED_HOSTS
)


# =========================
# SECURITY HEADERS
# =========================

@app.middleware("http")
async def security_headers(
    request: Request,
    call_next
):

    response = await call_next(request)

    response.headers[
        "X-Content-Type-Options"
    ] = "nosniff"

    response.headers[
        "X-Frame-Options"
    ] = "DENY"

    response.headers[
        "Referrer-Policy"
    ] = "strict-origin-when-cross-origin"

    response.headers[
        "Permissions-Policy"
    ] = "camera=(), microphone=(), geolocation=()"

    return response


# =========================
# SESSION VALIDATION
# =========================

def validate_session_id(
    session_id: Optional[str]
) -> str:

    if not session_id:
        return "default"

    session_id = session_id.strip()

    if not session_id:
        return "default"

    if len(session_id) > MAX_SESSION_ID_LENGTH:
        raise HTTPException(
            status_code=400,
            detail="Invalid session ID."
        )

    # Allow only safe characters
    if not re.fullmatch(
        r"[A-Za-z0-9_-]+",
        session_id
    ):
        raise HTTPException(
            status_code=400,
            detail="Invalid session ID."
        )

    return session_id


# =========================
# HOME
# =========================

@app.get("/")
def home():

    if not INDEX_FILE.exists():

        raise HTTPException(
            status_code=404,
            detail="Frontend not found."
        )

    return FileResponse(
        INDEX_FILE
    )


# =========================
# HEALTH CHECK
# =========================

@app.get("/health")
@limiter.limit("30/minute")
def health(
    request: Request
):

    return {
        "status": "healthy",
        "service": "JAA.AI",
        "version": "1.0.0"
    }


# =========================
# ASK AI
# =========================

@app.get("/ask")
@limiter.limit("10/minute")
def ask(
    request: Request,
    question: str,
    session_id: Optional[str] = "default"
):

    # Validate question

    if not question or not question.strip():

        raise HTTPException(
            status_code=400,
            detail="Question cannot be empty."
        )

    question = question.strip()

    if len(question) > MAX_QUESTION_LENGTH:

        raise HTTPException(
            status_code=400,
            detail=(
                "Question is too long. "
                "Maximum 1000 characters allowed."
            )
        )


    # Validate session

    session_id = validate_session_id(
        session_id
    )


    try:

        result = ask_ai(
            question,
            session_id
        )

        return {
            "question": question,
            "answer": result["answer"],
            "sources": result["sources"],
            "session_id": session_id
        }

    except Exception as e:

        print(
            "ASK ERROR:",
            repr(e)
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "JAA.AI could not "
                "process your request."
            )
        )


# =========================
# CHAT HISTORY
# =========================

@app.get("/history/{session_id}")
@limiter.limit("20/minute")
def get_history(
    request: Request,
    session_id: str
):

    session_id = validate_session_id(
        session_id
    )

    try:

        messages = get_chat_history(
            session_id
        )

        return {
            "session_id": session_id,
            "messages": [
                {
                    "role": message.role,
                    "content": message.content
                }
                for message in messages
            ]
        }

    except Exception as e:

        print(
            "HISTORY ERROR:",
            repr(e)
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Could not load "
                "chat history."
            )
        )


# =========================
# DELETE CHAT
# =========================

@app.delete("/history/{session_id}")
@limiter.limit("10/minute")
def delete_history(
    request: Request,
    session_id: str
):

    session_id = validate_session_id(
        session_id
    )

    try:

        delete_chat(
            session_id
        )

        return {
            "message":
                "Chat deleted successfully",

            "session_id":
                session_id
        }

    except Exception as e:

        print(
            "DELETE ERROR:",
            repr(e)
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Could not delete chat."
            )
        )


# =========================
# PDF UPLOAD + RAG
# =========================

@app.post("/upload")
@limiter.limit("5/minute")
async def upload_document(
    request: Request,
    file: UploadFile = File(...)
):

    # Check filename

    if not file.filename:

        raise HTTPException(
            status_code=400,
            detail="No file selected."
        )


    original_filename = file.filename


    # Only PDF extension

    if not original_filename.lower().endswith(
        ".pdf"
    ):

        raise HTTPException(
            status_code=400,
            detail="Only PDF files are allowed."
        )


    file_path = None

    try:

        # Read PDF

        content = await file.read()


        # Empty file check

        if not content:

            raise HTTPException(
                status_code=400,
                detail="The PDF file is empty."
            )


        # File size check

        if len(content) > MAX_PDF_SIZE:

            raise HTTPException(
                status_code=413,
                detail=(
                    "PDF file is too large. "
                    "Maximum size is 10 MB."
                )
            )


        # PDF signature check

        if not content.startswith(
            b"%PDF-"
        ):

            raise HTTPException(
                status_code=400,
                detail="Invalid PDF file."
            )


        # Generate safe server filename

        safe_filename = (
            f"{uuid.uuid4().hex}.pdf"
        )

        file_path = (
            UPLOAD_DIR /
            safe_filename
        )


        # Save PDF

        with open(
            file_path,
            "wb"
        ) as f:

            f.write(content)


        # Index PDF

        result = ingest_pdf(
            file_path
        )


        return {
            "message":
                "PDF uploaded and indexed successfully",

            "filename":
                original_filename,

            "pages":
                result["pages"],

            "chunks":
                result["chunks"],

            "source":
                result["source"]
        }


    except HTTPException:

        raise


    except Exception as e:

        print(
            "UPLOAD ERROR:",
            repr(e)
        )


        # Delete failed upload

        try:

            if file_path and file_path.exists():

                file_path.unlink()

        except Exception:

            pass


        raise HTTPException(
            status_code=500,
            detail=(
                "PDF could not be "
                "uploaded or indexed."
            )
        )