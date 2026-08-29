from pathlib import Path
from typing import Optional

from fastapi import (
    FastAPI,
    HTTPException,
    UploadFile,
    File
)

from fastapi.middleware.cors import CORSMiddleware

from agent.agent import ask_ai

from database import (
    delete_chat,
    get_chat_history
)


app = FastAPI(title="JAA.AI")


# =========================
# UPLOAD DIRECTORY
# =========================

BASE_DIR = Path(__file__).resolve().parent.parent

UPLOAD_DIR = BASE_DIR / "uploads"

UPLOAD_DIR.mkdir(
    exist_ok=True
)


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
# HOME
# =========================

@app.get("/")
def home():

    return {
        "message": "JAA.AI is running"
    }


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


        answer = result["answer"]

        sources = result["sources"]


        return {

            "question": question.strip(),

            "answer": answer,

            "sources": sources,

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
# PDF UPLOAD
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
            detail=(
                "Only PDF files are allowed."
            )
        )


    # Prevent unsafe path characters
    safe_filename = Path(
        filename
    ).name


    file_path = (
        UPLOAD_DIR /
        safe_filename
    )


    try:

        content = await file.read()


        if not content:

            raise HTTPException(
                status_code=400,
                detail="The PDF file is empty."
            )


        with open(
            file_path,
            "wb"
        ) as f:

            f.write(content)


        return {

            "message":
                "PDF uploaded successfully",

            "filename":
                safe_filename,

            "path":
                str(file_path)

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
                "Could not upload PDF."
            )
        )