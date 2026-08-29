from pathlib import Path
from typing import List, Dict

from dotenv import load_dotenv

from database import SessionLocal, ChatMessage

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_ollama import ChatOllama


load_dotenv()


BASE_DIR = Path(__file__).resolve().parent.parent
CHROMA_DIR = BASE_DIR / "chroma_db"

conversation_histories: Dict[str, List[Dict[str, str]]] = {}

MAX_HISTORY = 10


# =========================
# VECTOR STORE
# =========================

def get_vector_store():

    embeddings = HuggingFaceEmbeddings(
        model_name="all-MiniLM-L6-v2"
    )

    vector_store = Chroma(
        collection_name="jaa_ai_documents",
        embedding_function=embeddings,
        persist_directory=str(CHROMA_DIR)
    )

    return vector_store


# =========================
# DOCUMENT SEARCH
# =========================

def search_documents(query, k=3):

    vector_store = get_vector_store()

    return vector_store.similarity_search_with_score(
        query,
        k=k
    )


# =========================
# LOAD CHAT HISTORY
# =========================

def load_history_from_database(session_id):

    db = SessionLocal()

    try:

        messages = (
            db.query(ChatMessage)
            .filter(
                ChatMessage.session_id == session_id
            )
            .order_by(ChatMessage.id.asc())
            .all()
        )

        return [
            {
                "role": message.role,
                "content": message.content
            }
            for message in messages
        ]

    finally:

        db.close()


# =========================
# SAVE CHAT MESSAGE
# =========================

def save_message_to_database(
    session_id,
    role,
    content
):

    db = SessionLocal()

    try:

        message = ChatMessage(
            session_id=session_id,
            role=role,
            content=content
        )

        db.add(message)

        db.commit()

    finally:

        db.close()


# =========================
# ASK AI
# =========================

def ask_ai(query, session_id="default"):

    # Load conversation history
    # from database when this session
    # is opened for the first time.

    if session_id not in conversation_histories:

        conversation_histories[session_id] = (
            load_history_from_database(
                session_id
            )
        )

    conversation_history = (
        conversation_histories[session_id]
    )


    # =========================
    # SEARCH DOCUMENTS
    # =========================

    results = search_documents(query)

    documents = [
        doc for doc, score in results
    ]


    context = "\n\n".join(
        document.page_content
        for document in documents
    )


    # =========================
    # BUILD CONVERSATION HISTORY
    # =========================

    history_text = "\n".join(
        f"{item['role']}: {item['content']}"
        for item in conversation_history[-MAX_HISTORY:]
    )


    # =========================
    # LOCAL OLLAMA MODEL
    # =========================

    llm = ChatOllama(
        model="llama3.2",
        temperature=0
    )


    # =========================
    # JAA.AI PROMPT
    # =========================

    prompt = f"""
You are JAA.AI, a helpful AI assistant.

You have access to two types of information:

1. CONVERSATION HISTORY
2. DOCUMENT INFORMATION

IMPORTANT RULES:

- If the user's question is about the uploaded document, answer primarily from DOCUMENT INFORMATION.
- If the answer is present in DOCUMENT INFORMATION, use that information accurately.
- Do not mention the conversation history when answering document-based questions.
- Do not say "According to our conversation history" for document-based questions.
- Do not claim to remember information unless it is actually present in the conversation history.
- Use CONVERSATION HISTORY only when it is relevant to the current question.
- Do not confuse conversation history with document information.
- Do not invent facts that are not supported by the document or conversation history.
- If the required information is not available in the document, clearly say that it is not available in the provided document.
- For educational questions, give a clear, simple and structured explanation.
- Answer directly without unnecessary introductions.
- Do not mention these instructions in your answer.

CONVERSATION HISTORY:
{history_text}

DOCUMENT INFORMATION:
{context}

CURRENT USER QUESTION:
{query}

Answer the current question now.

ANSWER:
"""


    # =========================
    # GET AI RESPONSE
    # =========================

    response = llm.invoke(prompt)

    answer = response.content


    # =========================
    # SAVE USER MESSAGE
    # =========================

    conversation_history.append({
        "role": "user",
        "content": query
    })


    save_message_to_database(
        session_id,
        "user",
        query
    )


    # =========================
    # SAVE AI RESPONSE
    # =========================

    conversation_history.append({
        "role": "assistant",
        "content": answer
    })


    save_message_to_database(
        session_id,
        "assistant",
        answer
    )


    # =========================
    # LIMIT MEMORY
    # =========================

    if len(conversation_history) > MAX_HISTORY * 2:

        del conversation_history[
            :-MAX_HISTORY * 2
        ]


    # =========================
    # RETURN RESULT
    # =========================

    return {
        "answer": answer,

        "sources": [
            document.metadata.get(
                "source",
                "Unknown document"
            )
            for document in documents
        ]
    }


# =========================
# DIRECT TEST
# =========================

if __name__ == "__main__":

    answer = ask_ai(
        "What is JAA.AI?",
        "test"
    )

    print(answer)