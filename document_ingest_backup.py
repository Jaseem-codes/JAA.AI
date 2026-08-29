from pathlib import Path

import fitz
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma


BASE_DIR = Path(__file__).resolve().parent

PDF_PATH = BASE_DIR / "DBMS_Unit_1_Complete_Notes_Hinglish.pdf"
CHROMA_DIR = BASE_DIR / "chroma_db"


def ingest_pdf():

    if not PDF_PATH.exists():
        print("PDF not found:", PDF_PATH)
        return

    pdf = fitz.open(str(PDF_PATH))

    documents = []

    for page_number, page in enumerate(pdf):

        text = page.get_text().strip()

        if text:
            documents.append(
                Document(
                    page_content=text,
                    metadata={
                        "source": PDF_PATH.name,
                        "page": page_number + 1
                    }
                )
            )

    pdf.close()

    if not documents:
        print("No text found in PDF.")
        return

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50
    )

    chunks = splitter.split_documents(documents)

    embeddings = HuggingFaceEmbeddings(
        model_name="all-MiniLM-L6-v2"
    )

    Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        collection_name="jaa_ai_documents",
        persist_directory=str(CHROMA_DIR)
    )

    print("PDF successfully added to ChromaDB.")
    print("Pages:", len(documents))
    print("Chunks:", len(chunks))


if __name__ == "__main__":
    ingest_pdf()