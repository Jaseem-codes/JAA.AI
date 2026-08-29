from pathlib import Path

import pymupdf

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter


BASE_DIR = Path(__file__).resolve().parent

CHROMA_DIR = BASE_DIR / "chroma_db"


def ingest_pdf(pdf_path):

    pdf_path = Path(pdf_path)

    if not pdf_path.exists():
        raise FileNotFoundError(
            f"PDF not found: {pdf_path}"
        )

    documents = []

    # Open PDF
    with pymupdf.open(str(pdf_path)) as pdf:

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

    # Split text into chunks
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50
    )

    chunks = splitter.split_documents(
        documents
    )

    # Create embeddings
    embeddings = HuggingFaceEmbeddings(
        model_name="all-MiniLM-L6-v2"
    )

    # Connect to ChromaDB
    vector_store = Chroma(
        collection_name="jaa_ai_documents",
        embedding_function=embeddings,
        persist_directory=str(CHROMA_DIR)
    )

    # Remove old chunks of the same PDF
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

    # Add new chunks
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