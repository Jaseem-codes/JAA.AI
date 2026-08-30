from pathlib import Path
import hashlib
import re
import numpy as np
import pymupdf

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter


BASE_DIR = Path(__file__).resolve().parent

CHROMA_DIR = BASE_DIR / "chroma_db"

# New collection because old collection used HuggingFace embeddings
COLLECTION_NAME = "jaa_ai_documents_v2"

# Lightweight embedding size
EMBEDDING_DIM = 384


# =========================
# LIGHTWEIGHT EMBEDDINGS
# =========================

class LightweightEmbeddings:
    """
    Small memory-friendly embedding system.

    It uses a deterministic hashing technique instead of
    loading a large HuggingFace/Sentence-Transformer model.
    """

    def _embed(self, text: str):

        vector = np.zeros(
            EMBEDDING_DIM,
            dtype=np.float32
        )

        # Basic tokenization
        words = re.findall(
            r"\b\w+\b",
            text.lower()
        )

        if not words:
            return vector.tolist()

        for word in words:

            hash_bytes = hashlib.md5(
                word.encode("utf-8")
            ).digest()

            index = int.from_bytes(
                hash_bytes[:4],
                byteorder="little"
            ) % EMBEDDING_DIM

            vector[index] += 1.0

        # Normalize vector
        norm = np.linalg.norm(vector)

        if norm > 0:
            vector = vector / norm

        return vector.tolist()

    def embed_documents(self, texts):

        return [
            self._embed(text)
            for text in texts
        ]

    def embed_query(self, text):

        return self._embed(text)


# =========================
# EMBEDDING INSTANCE
# =========================

embeddings = LightweightEmbeddings()


# =========================
# PDF INGESTION
# =========================

def ingest_pdf(pdf_path):

    pdf_path = Path(pdf_path)

    if not pdf_path.exists():

        raise FileNotFoundError(
            f"PDF not found: {pdf_path}"
        )

    documents = []

    # =========================
    # OPEN PDF
    # =========================

    with pymupdf.open(
        str(pdf_path)
    ) as pdf:

        for page_number, page in enumerate(pdf):

            text = page.get_text().strip()

            if text:

                documents.append(
                    Document(
                        page_content=text,
                        metadata={
                            "source": pdf_path.name,
                            "page": page_number + 1
                        }
                    )
                )

    if not documents:

        raise ValueError(
            "No readable text found in PDF."
        )

    # =========================
    # SPLIT TEXT
    # =========================

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50
    )

    chunks = splitter.split_documents(
        documents
    )

    # =========================
    # CONNECT CHROMA
    # =========================

    vector_store = Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings,
        persist_directory=str(CHROMA_DIR)
    )

    # =========================
    # REMOVE OLD CHUNKS
    # =========================

    try:

        vector_store.delete(
            where={
                "source": pdf_path.name
            }
        )

    except Exception as e:

        print(
            "Old document cleanup skipped:",
            repr(e)
        )

    # =========================
    # ADD NEW CHUNKS
    # =========================

    vector_store.add_documents(
        chunks
    )

    return {
        "pages": len(documents),
        "chunks": len(chunks),
        "source": pdf_path.name
    }


# =========================
# DIRECT TEST
# =========================

if __name__ == "__main__":

    pdf_path = (
        BASE_DIR /
        "DBMS_Unit_1_Complete_Notes_Hinglish.pdf"
    )

    result = ingest_pdf(
        pdf_path
    )

    print(
        "PDF successfully added to ChromaDB."
    )

    print(
        "Pages:",
        result["pages"]
    )

    print(
        "Chunks:",
        result["chunks"]
    )

    print(
        "Source:",
        result["source"]
    )