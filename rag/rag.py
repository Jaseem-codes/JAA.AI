from pathlib import Path

from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_chroma import Chroma

BASE_DIR = Path(__file__).resolve().parent.parent
DOCUMENT_PATH = BASE_DIR / "data" / "documents.txt"
CHROMA_DIR = BASE_DIR / "chroma_db"


def create_vector_store():
    loader = TextLoader(str(DOCUMENT_PATH), encoding="utf-8")
    documents = loader.load()

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50
    )

    chunks = splitter.split_documents(documents)

    embeddings = HuggingFaceEmbeddings(
        model_name="all-MiniLM-L6-v2"
    )

    vector_store = Chroma(
        collection_name="jaa_ai_documents",
        embedding_function=embeddings,
        persist_directory=str(CHROMA_DIR)
    )

    vector_store.add_documents(chunks)

    return vector_store


if __name__ == "__main__":
    create_vector_store()
    print("JAA.AI RAG vector store created successfully.")