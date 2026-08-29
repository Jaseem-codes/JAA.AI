from pathlib import Path
from typing import Optional

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


app = FastAPI(title="JAA.AI")


# =========================
# DIRECTORIES
# =========================

BASE_DIR = Path(__file__).resolve().parent.parent

UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

FRONTEND_DIR = BASE_DIR / "app" / "frontend"
INDEX_FILE = FRONTEND_DIR / "index.html"


# =========================
# CORS
# =========================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================
# HOME - FRONTEND
# =========================

@app.get("/")
def home():

    if not INDEX_FILE.exists():

        raise HTTPException(
            status_code=404,
            detail="Frontend index.html not found."
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
        "service": "JAA.AI"
    }


# =========================
# ASK AI
# =========================

@app.get("/ask")
def ask(
    question: str,
    session_id: Optional[str] = "default"
):

    if not question or not question.strip():

        raise HTTPException(
            status_code=400,
            detail="Question cannot be empty"
        )

    if len(question) > 1000:

        raise HTTPException(
            status_code=400,
            detail=(
                "Question is too long. "
                "Maximum 1000 characters allowed."
            )
        )

    try:

        result = ask_ai(
            question.strip(),
            session_id
        )

        return {
            "question": question.strip(),
            "answer": result["answer"],
            "sources": result["sources"],
            "session_id": session_id
        }

    except Exception as e:

        print(
            "ERROR:",
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

    if not file.filename:

        raise HTTPException(
            status_code=400,
            detail="No file selected."
        )

    filename = file.filename

    if not filename.lower().endswith(".pdf"):

        raise HTTPException(
            status_code=400,
            detail="Only PDF files are allowed."
        )

    # Safe filename
    safe_filename = Path(
        filename
    ).name

    file_path = (
        UPLOAD_DIR /
        safe_filename
    )

    try:

        # Read uploaded PDF
        content = await file.read()

        if not content:

            raise HTTPException(
                status_code=400,
                detail="The PDF file is empty."
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
                safe_filename,

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

        raise HTTPException(
            status_code=500,
            detail=(
                "PDF was uploaded but "
                "could not be indexed."
            )
        )