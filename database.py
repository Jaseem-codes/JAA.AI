from pathlib import Path

from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.orm import declarative_base, sessionmaker


BASE_DIR = Path(__file__).resolve().parent

DATABASE_URL = f"sqlite:///{BASE_DIR / 'jaa_ai.db'}"


engine = create_engine(
    DATABASE_URL,
    connect_args={
        "check_same_thread": False
    }
)


SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


Base = declarative_base()


class ChatMessage(Base):

    __tablename__ = "chat_messages"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    session_id = Column(
        String,
        index=True,
        nullable=False
    )

    role = Column(
        String,
        nullable=False
    )

    content = Column(
        Text,
        nullable=False
    )


Base.metadata.create_all(
    bind=engine
)


def delete_chat(session_id: str):

    db = SessionLocal()

    try:

        db.query(ChatMessage).filter(
            ChatMessage.session_id == session_id
        ).delete(
            synchronize_session=False
        )

        db.commit()

        return True

    except Exception:

        db.rollback()

        raise

    finally:

        db.close()


def get_chat_history(session_id: str):

    db = SessionLocal()

    try:

        messages = (
            db.query(ChatMessage)
            .filter(
                ChatMessage.session_id == session_id
            )
            .order_by(
                ChatMessage.id.asc()
            )
            .all()
        )

        return messages

    finally:

        db.close()