# JAA.AI 🤖

### Production-Grade AI Research Assistant

JAA.AI is an AI-powered research assistant that combines **Retrieval-Augmented Generation (RAG)**, **vector search**, **local LLM inference**, and **chat memory** to provide context-aware answers from uploaded PDF documents.

---

## ✨ Features

- 📄 Upload PDF documents
- 🔎 Semantic document search using vector embeddings
- 🧠 Retrieval-Augmented Generation (RAG)
- 🤖 Local AI inference using Ollama + Llama 3.2
- 💬 Context-aware conversational memory
- 🗂️ Chat history management
- 🗑️ Delete individual conversations
- 📚 Display document sources with answers
- ⚡ FastAPI backend
- 🌐 Web-based chat interface
- 🔐 Secure PDF upload validation
- 🧪 Automated API tests
- 💾 Persistent chat storage using SQLite

---

## 🏗️ Architecture

```text
User
  │
  ▼
Web Interface
  │
  ▼
FastAPI Backend
  │
  ├── PDF Upload
  │       │
  │       ▼
  │   PyMuPDF
  │       │
  │       ▼
  │   Text Chunking
  │       │
  │       ▼
  │   HuggingFace Embeddings
  │       │
  │       ▼
  │   ChromaDB
  │
  └── User Question
          │
          ▼
      Vector Search
          │
          ▼
      Relevant Context
          │
          ▼
      Ollama
      Llama 3.2
          │
          ▼
      AI Response