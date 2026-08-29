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


def search_documents(query, k=3):

    vector_store = get_vector_store()

    return vector_store.similarity_search_with_score(
        query,
        k=k
    )


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


    # Search documents

    results = search_documents(query)

    documents = [
        doc for doc, score in results
    ]


    context = "\n\n".join(
        document.page_content
        for document in documents
    )


    # Build conversation history

    history_text = "\n".join(
        f"{item['role']}: {item['content']}"
        for item in conversation_history[-MAX_HISTORY:]
    )


    llm = ChatOllama(
        model="llama3.2",
        temperature=0
    )


    prompt = f"""
You are JAA.AI, a helpful AI assistant.

You have access to TWO types of information:

1. CONVERSATION HISTORY
2. DOCUMENT INFORMATION

IMPORTANT:
- Conversation history is the most important source for personal information.
- If the user told you their name, remember it.
- If the user asks "What is my name?", look at the conversation history first.
- Do NOT say that you don't know the user's name if it appears in the conversation history.
- Answer directly and confidently when the information is present.
- Do not confuse document information with conversation history.
- Use document information only when it is relevant.
- Keep answers clear and concise.

CONVERSATION HISTORY:
{history_text}

DOCUMENT INFORMATION:
{context}

CURRENT USER QUESTION:
{query}

Now answer the current question using the conversation history first.

ANSWER:
"""


    response = llm.invoke(prompt)

    answer = response.content


    # Save user message in memory

    conversation_history.append({
        "role": "user",
        "content": query
    })


    # Save user message in SQLite

    save_message_to_database(
        session_id,
        "user",
        query
    )


    # Save AI response in memory

    conversation_history.append({
        "role": "assistant",
        "content": answer
    })


    # Save AI response in SQLite

    save_message_to_database(
        session_id,
        "assistant",
        answer
    )


    # Keep only recent messages
    # in memory.

    if len(conversation_history) > MAX_HISTORY * 2:

        del conversation_history[
            :-MAX_HISTORY * 2
        ]


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


if __name__ == "__main__":

    answer = ask_ai(
        "What is JAA.AI?",
        "test"
    )

    print(answer)