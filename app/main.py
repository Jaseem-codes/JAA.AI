from pathlib import Path
from typing import Optional
import os
import uuid
import re
import base64

import httpx

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
MAX_IMAGE_SIZE = 10 * 1024 * 1024

MAX_QUESTION_LENGTH = 1000
MAX_SESSION_ID_LENGTH = 100

# Ollama models
TEXT_MODEL = "llama3.2"
VISION_MODEL = "gemma3:4b"

OLLAMA_URL = "http://localhost:11434"


# =========================
# CORS
# =========================

ALLOWED_ORIGINS = [
    "https://jaa-ai.onrender.com",
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
# TRUSTED HOST
# =========================

ALLOWED_HOSTS = [
    "jaa-ai.onrender.com",
    "127.0.0.1",
    "localhost"
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

    if not file.filename:

        raise HTTPException(
            status_code=400,
            detail="No file selected."
        )

    original_filename = file.filename

    if not original_filename.lower().endswith(
        ".pdf"
    ):

        raise HTTPException(
            status_code=400,
            detail="Only PDF files are allowed."
        )

    file_path = None

    try:

        content = await file.read()

        if not content:

            raise HTTPException(
                status_code=400,
                detail="The PDF file is empty."
            )

        if len(content) > MAX_PDF_SIZE:

            raise HTTPException(
                status_code=413,
                detail=(
                    "PDF file is too large. "
                    "Maximum size is 10 MB."
                )
            )

        if not content.startswith(
            b"%PDF-"
        ):

            raise HTTPException(
                status_code=400,
                detail="Invalid PDF file."
            )

        safe_filename = (
            f"{uuid.uuid4().hex}.pdf"
        )

        file_path = (
            UPLOAD_DIR /
            safe_filename
        )

        with open(
            file_path,
            "wb"
        ) as f:

            f.write(content)

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


# =========================
# IMAGE UPLOAD
# =========================

@app.post("/upload-image")
@limiter.limit("5/minute")
async def upload_image(
    request: Request,
    file: UploadFile = File(...)
):

    if not file.filename:

        raise HTTPException(
            status_code=400,
            detail="No image selected."
        )

    original_filename = file.filename

    allowed_extensions = (
        ".jpg",
        ".jpeg",
        ".png",
        ".webp"
    )

    if not original_filename.lower().endswith(
        allowed_extensions
    ):

        raise HTTPException(
            status_code=400,
            detail=(
                "Only JPG, JPEG, PNG "
                "and WEBP images are allowed."
            )
        )

    file_path = None

    try:

        content = await file.read()

        if not content:

            raise HTTPException(
                status_code=400,
                detail="The image file is empty."
            )

        if len(content) > MAX_IMAGE_SIZE:

            raise HTTPException(
                status_code=413,
                detail=(
                    "Image file is too large. "
                    "Maximum size is 10 MB."
                )
            )

        # =========================
        # IMAGE SIGNATURE CHECK
        # =========================

        valid_image = False

        # JPG / JPEG
        if content.startswith(b"\xff\xd8\xff"):
            valid_image = True

        # PNG
        elif content.startswith(
            b"\x89PNG\r\n\x1a\n"
        ):
            valid_image = True

        # WEBP
        elif (
            content.startswith(b"RIFF")
            and len(content) >= 12
            and content[8:12] == b"WEBP"
        ):
            valid_image = True

        if not valid_image:

            raise HTTPException(
                status_code=400,
                detail="Invalid image file."
            )

        extension = Path(
            original_filename
        ).suffix.lower()

        safe_filename = (
            f"{uuid.uuid4().hex}{extension}"
        )

        file_path = (
            UPLOAD_DIR /
            safe_filename
        )

        with open(
            file_path,
            "wb"
        ) as f:

            f.write(content)

        return {
            "message":
                "Image uploaded successfully",

            "filename":
                original_filename,

            "image_id":
                safe_filename
        }

    except HTTPException:

        raise

    except Exception as e:

        print(
            "IMAGE UPLOAD ERROR:",
            repr(e)
        )

        try:

            if file_path and file_path.exists():

                file_path.unlink()

        except Exception:

            pass

        raise HTTPException(
            status_code=500,
            detail="Image could not be uploaded."
        )


# =========================
# ASK AI ABOUT IMAGE
# =========================

@app.post("/ask-image")
@limiter.limit("10/minute")
async def ask_image(
    request: Request
):

    try:

        data = await request.json()

    except Exception:

        raise HTTPException(
            status_code=400,
            detail="Invalid JSON request."
        )

    image_id = data.get(
        "image_id"
    )

    question = data.get(
        "question",
        "Describe this image and answer what is asked in it."
    )

    if not image_id:

        raise HTTPException(
            status_code=400,
            detail="Image ID is required."
        )

    if not isinstance(
        image_id,
        str
    ):

        raise HTTPException(
            status_code=400,
            detail="Invalid image ID."
        )

    if not re.fullmatch(
        r"[A-Za-z0-9_-]+\.(jpg|jpeg|png|webp)",
        image_id,
        re.IGNORECASE
    ):

        raise HTTPException(
            status_code=400,
            detail="Invalid image ID."
        )

    if not isinstance(
        question,
        str
    ):

        raise HTTPException(
            status_code=400,
            detail="Invalid question."
        )

    question = question.strip()

    if not question:

        question = (
            "Read this image carefully. "
            "Identify the questions or text "
            "shown in the image and provide "
            "their answers."
        )

    if len(question) > MAX_QUESTION_LENGTH:

        raise HTTPException(
            status_code=400,
            detail=(
                "Question is too long. "
                "Maximum 1000 characters allowed."
            )
        )

    image_path = (
        UPLOAD_DIR /
        image_id
    )

    if not image_path.exists():

        raise HTTPException(
            status_code=404,
            detail="Image not found."
        )

    try:

        # =========================
        # READ IMAGE
        # =========================

        with open(
            image_path,
            "rb"
        ) as image_file:

            image_bytes = image_file.read()

        image_base64 = base64.b64encode(
            image_bytes
        ).decode("utf-8")


        # =========================
        # SEND IMAGE TO OLLAMA
        # =========================

        payload = {
            "model": VISION_MODEL,

            "messages": [
                {
                    "role": "user",

                    "content": question,

                    "images": [
                        image_base64
                    ]
                }
            ],

            "stream": False
        }

        async with httpx.AsyncClient(timeout=600.0) as client:

            response = await client.post(
                f"{OLLAMA_URL}/api/chat",
                json=payload
            )


        # =========================
        # OLLAMA ERROR
        # =========================

        if response.status_code != 200:

            print(
                "OLLAMA IMAGE ERROR:",
                response.text
            )

            raise HTTPException(
                status_code=500,
                detail=(
                    "Vision AI could not "
                    "process the image."
                )
            )


        result = response.json()


        # =========================
        # GET ANSWER
        # =========================

        message = result.get(
            "message",
            {}
        )

        answer = message.get(
            "content"
        )


        if not answer:

            raise HTTPException(
                status_code=500,
                detail=(
                    "Vision AI returned "
                    "an empty answer."
                )
            )


        return {
            "question": question,
            "answer": answer,
            "image_id": image_id,
            "model": VISION_MODEL
        }


    except HTTPException:

        raise

    except httpx.ConnectError:

        raise HTTPException(
            status_code=503,
            detail=(
                "Ollama is not running. "
                "Please start Ollama first."
            )
        )

    except Exception as e:

        print(
            "ASK IMAGE ERROR:",
            repr(e)
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "JAA.AI could not "
                "analyze the image."
            )
        )