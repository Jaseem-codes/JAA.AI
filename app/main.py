from pathlib import Path
from typing import Optional
import os
import uuid

from fastapi import (
    FastAPI,
    HTTPException,
    UploadFile,
    File
)

from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from document_ingest import ingest_pdf
from agent.agent import ask_ai

from database import (
    delete_chat,
    get_chat_history
)


# =========================
# APP
# =========================

app = FastAPI(
    title="JAA.AI",
    version="1.0.0"
)


# =========================
# DIRECTORIES
# =========================

BASE_DIR = Path(__file__).resolve().parent.parent

UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(
    exist_ok=True
)

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
#
# Local development:
# frontend and API both run
# on 127.0.0.1:8000.
#
# Keep localhost origins only.
#

ALLOWED_ORIGINS = [
    "http://127.0.0.1:8000",
    "http://localhost:8000"
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
def health():

    return {
        "status": "healthy",
        "service": "JAA.AI",
        "version": "1.0.0"
    }


# =========================
# ASK AI
# =========================

@app.get("/ask")
def ask(
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


    # Validate session ID

    if not session_id:

        session_id = "default"

    session_id = session_id.strip()

    if len(session_id) > MAX_SESSION_ID_LENGTH:

        raise HTTPException(
            status_code=400,
            detail="Invalid session ID."
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
def get_history(
    session_id: str
):

    if not session_id:

        raise HTTPException(
            status_code=400,
            detail="Invalid session ID."
        )

    if len(session_id) > MAX_SESSION_ID_LENGTH:

        raise HTTPException(
            status_code=400,
            detail="Invalid session ID."
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
def delete_history(
    session_id: str
):

    if not session_id:

        raise HTTPException(
            status_code=400,
            detail="Invalid session ID."
        )

    if len(session_id) > MAX_SESSION_ID_LENGTH:

        raise HTTPException(
            status_code=400,
            detail="Invalid session ID."
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
async def upload_document(
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
        #
        # Real PDF files normally
        # start with %PDF-

        if not content.startswith(
            b"%PDF-"
        ):

            raise HTTPException(
                status_code=400,
                detail=(
                    "Invalid PDF file."
                )
            )


        # Generate safe server-side filename
        #
        # Never trust the user's filename
        # for the actual storage path.

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


        # Index PDF in ChromaDB

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


        # Remove partially saved file
        # if indexing fails.

        try:

            if file_path.exists():

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