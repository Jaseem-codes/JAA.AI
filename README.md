JAA.AI 🤖

Production-Grade AI Assistant with RAG, Web Search & Conversational Memory

JAA.AI is an AI-powered assistant built with Python, FastAPI, RAG, ChromaDB, Groq LLM, Tavily Web Search and PDF document processing.

It can answer general questions, search uploaded PDF documents using Retrieval-Augmented Generation (RAG), perform web searches for external information, and maintain conversational history.

🌐 Live Demo: https://jaa-ai.onrender.com

---

🚀 Features

- 🤖 AI-powered conversational assistant
- 🧠 Retrieval-Augmented Generation (RAG)
- 📄 PDF document upload
- 🔎 Semantic document search using embeddings
- 🗃️ ChromaDB vector database
- 🌐 Tavily web search integration
- 💬 Conversational memory
- 🕘 Persistent chat history
- 🗑️ Delete chat functionality
- ➕ New chat sessions
- 🔐 Environment-based API key configuration
- ⚡ FastAPI REST API
- 🌍 Cloud deployment with Render
- 📱 Responsive web interface

---

🏗️ Architecture

                    ┌─────────────────────┐
                    │     User / Browser  │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │   JAA.AI Frontend   │
                    │      HTML/CSS/JS     │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │       FastAPI       │
                    │      Backend API    │
                    └──────────┬──────────┘
                               │
              ┌────────────────┼────────────────┐
              │                │                │
              ▼                ▼                ▼
        ┌───────────┐    ┌────────────┐   ┌────────────┐
        │  ChromaDB │    │    Groq    │   │   Tavily   │
        │    RAG    │    │    LLM     │   │ Web Search │
        └───────────┘    └────────────┘   └────────────┘
              ▲
              │
        ┌─────────────┐
        │ PDF Upload  │
        │ + Embeddings│
        └─────────────┘

---

🧠 How RAG Works

When a user uploads a PDF:

PDF
 │
 ▼
Text Extraction
 │
 ▼
Text Chunking
 │
 ▼
HuggingFace Embeddings
 │
 ▼
ChromaDB
 │
 ▼
Semantic Search
 │
 ▼
Relevant Context
 │
 ▼
Groq LLM
 │
 ▼
AI Answer

This allows JAA.AI to answer questions using information contained inside uploaded documents.

---

🛠️ Tech Stack

Backend

- Python
- FastAPI
- Uvicorn

AI / LLM

- Groq
- LangChain
- HuggingFace Embeddings

RAG / Vector Database

- ChromaDB
- LangChain Chroma
- Recursive Character Text Splitter

Document Processing

- PyMuPDF

Web Search

- Tavily API

Database

- SQLAlchemy
- SQLite

Frontend

- HTML
- CSS
- JavaScript

Deployment

- Render
- GitHub

---

📁 Project Structure

JAA.AI/
│
├── app/
│   ├── main.py
│   └── frontend/
│       └── index.html
│
├── agent/
│   └── agent.py
│
├── rag/
│   └── rag.py
│
├── tests/
│
├── uploads/
│
├── chroma_db/
│
├── database.py
├── document_ingest.py
├── requirements.txt
├── .env
├── .gitignore
└── README.md

---

⚙️ API Endpoints

Health Check

GET /health

Checks whether the JAA.AI backend is running.

Ask AI

GET /ask

Example:

/ask?question=What%20is%20DBMS?

Upload PDF

POST /upload

Uploads and indexes a PDF document.

Chat History

GET /history/{session_id}

Returns conversation history.

Delete Chat

DELETE /history/{session_id}

Deletes a conversation.

---

🔐 Environment Variables

Create a ".env" file locally:

GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=llama-3.3-70b-versatile
TAVILY_API_KEY=your_tavily_api_key

Never commit real API keys or secrets to GitHub.

---

💻 Local Setup

1. Clone the repository

git clone https://github.com/Jaseem-codes/JAA.AI.git
cd JAA.AI

2. Create virtual environment

Windows:

python -m venv venv

Activate:

venv\Scripts\activate

3. Install dependencies

pip install -r requirements.txt

4. Configure environment variables

Create ".env" and add:

GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=llama-3.3-70b-versatile
TAVILY_API_KEY=your_tavily_api_key

5. Run the application

python -m uvicorn app.main:app --reload

Open:

http://127.0.0.1:8000

---

📄 PDF Workflow

1. Open JAA.AI.
2. Click Upload PDF.
3. Select a PDF file.
4. JAA.AI extracts the text.
5. The text is divided into chunks.
6. Embeddings are generated.
7. Chunks are stored in ChromaDB.
8. Ask questions about the uploaded PDF.
9. Relevant document information is retrieved before generating the answer.

---

🌐 Web Search

JAA.AI can also use Tavily to retrieve external web information.

This allows the assistant to combine:

Conversation History
        +
Document Information
        +
Web Information
        ↓
      Groq LLM
        ↓
     Final Answer

---

💬 Conversational Memory

Each chat session receives a unique session ID.

JAA.AI uses this ID to maintain conversation history and allows users to:

- Create new chats
- Continue previous chats
- View chat history
- Delete conversations

---

🚀 Deployment

JAA.AI is deployed as a FastAPI Web Service on Render.

Production URL:

https://jaa-ai.onrender.com

The project uses GitHub-based automatic deployment.

Whenever changes are pushed to the configured branch, Render can automatically build and deploy the latest version.

---

🔒 Security Considerations

The application includes several basic security measures:

- PDF-only upload validation
- Maximum PDF upload size
- PDF signature validation
- Question length validation
- Session ID validation
- Environment variables for secrets
- CORS configuration
- Server-side generated filenames
- Error handling for API operations

---

🧪 Testing

The project has been tested for:

- FastAPI server startup
- Health endpoint
- AI question answering
- PDF upload
- PDF indexing
- RAG-based question answering
- Chat history
- New chat
- Chat deletion
- Render deployment
- Production frontend/backend communication

---

🎯 Future Improvements

Possible future improvements include:

- Streaming AI responses
- Better source citations
- Multi-PDF management
- User authentication
- PostgreSQL production database
- Advanced document metadata filtering
- Improved UI/UX
- Automated evaluation of RAG responses
- Docker containerization
- CI/CD pipeline
- Rate limiting
- Observability and logging
- Role-based access control

---

👨‍💻 Author

Jaseem Ahmad

B.Tech Computer Science & Engineering

---

⭐ Project Goal

JAA.AI was developed as a practical AI engineering project demonstrating the integration of:

LLM
+
RAG
+
Vector Database
+
Embeddings
+
Web Search
+
Conversational Memory
+
REST API
+
Cloud Deployment

The goal is to build a scalable foundation for a production-oriented AI assistant.