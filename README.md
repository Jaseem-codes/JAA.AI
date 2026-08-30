JAA.AI 🤖

Production-Grade AI Assistant with RAG, Web Search & Conversational Memory

JAA.AI is a production-oriented AI assistant built with Python, FastAPI, Retrieval-Augmented Generation (RAG), ChromaDB, Groq LLM, Tavily Web Search, HuggingFace Embeddings, and PDF document processing.

It can answer general questions, retrieve information from uploaded PDF documents, use web search for external information, and maintain persistent conversational history.

🌐 Live Demo: https://jaa-ai.onrender.com

---

🚀 Features

- 🤖 AI-powered conversational assistant
- 🧠 Retrieval-Augmented Generation (RAG)
- 📄 PDF upload and document processing
- 🔎 Semantic document search using embeddings
- 🗃️ ChromaDB vector database
- 🌐 Tavily web search integration
- 💬 Conversational memory
- 🕘 Persistent chat history
- 🗑️ Chat deletion
- ➕ Multiple chat sessions
- 🔐 Environment-based secret configuration
- ⚡ FastAPI REST API
- 🌍 Render cloud deployment
- 📱 Responsive web interface

---

🏗️ System Architecture

                    ┌─────────────────────┐
                    │    User / Browser   │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │   JAA.AI Frontend   │
                    │     HTML/CSS/JS     │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │       FastAPI       │
                    │      REST API       │
                    └──────────┬──────────┘
                               │
              ┌────────────────┼────────────────┐
              │                │                │
              ▼                ▼                ▼
        ┌───────────┐    ┌────────────┐   ┌────────────┐
        │  ChromaDB │    │    Groq    │   │   Tavily   │
        │    RAG    │    │    LLM     │   │ Web Search │
        └─────▲─────┘    └────────────┘   └────────────┘
              │
              │
        ┌─────┴─────────┐
        │ PDF Processing│
        │ + Embeddings  │
        └───────────────┘

---

🧠 RAG Pipeline

When a user uploads a PDF, JAA.AI processes it through the following pipeline:

PDF Upload
    ↓
Text Extraction
    ↓
Text Chunking
    ↓
HuggingFace Embeddings
    ↓
ChromaDB
    ↓
Semantic Similarity Search
    ↓
Relevant Context
    ↓
Groq LLM
    ↓
AI Response

This enables the assistant to answer questions using information retrieved from uploaded documents rather than relying only on the LLM's general knowledge.

---

🔄 AI Response Pipeline

JAA.AI combines multiple sources of information:

                 ┌─────────────────────┐
                 │ Conversation History│
                 └──────────┬──────────┘
                            │
                 ┌──────────▼──────────┐
                 │ Document Information│
                 └──────────┬──────────┘
                            │
                 ┌──────────▼──────────┐
                 │   Web Information   │
                 └──────────┬──────────┘
                            │
                            ▼
                     ┌────────────┐
                     │  Groq LLM  │
                     └─────┬──────┘
                           │
                           ▼
                     Final Answer

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

- GitHub
- Render

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

Method| Endpoint| Description
GET| "/health"| Check API health
GET| "/ask"| Ask JAA.AI a question
POST| "/upload"| Upload and index a PDF
GET| "/history/{session_id}"| Retrieve chat history
DELETE| "/history/{session_id}"| Delete a conversation

Example

GET /ask?question=What%20is%20DBMS?

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

2. Create a virtual environment

python -m venv venv

3. Activate the environment

Windows:

venv\Scripts\activate

4. Install dependencies

pip install -r requirements.txt

5. Configure environment variables

Create ".env" and add:

GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=llama-3.3-70b-versatile
TAVILY_API_KEY=your_tavily_api_key

6. Run the application

python -m uvicorn app.main:app --reload

Open:

http://127.0.0.1:8000

---

📄 PDF Processing Workflow

1. Open JAA.AI.
2. Click Upload PDF.
3. Select a PDF document.
4. PyMuPDF extracts the text.
5. Text is divided into smaller chunks.
6. HuggingFace generates embeddings.
7. Embeddings and document chunks are stored in ChromaDB.
8. User asks a question.
9. Relevant document chunks are retrieved.
10. Retrieved context is provided to the Groq LLM.
11. JAA.AI generates the final answer.

---

🌐 Web Search

JAA.AI can use Tavily Web Search when external information is required.

The assistant can combine:

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

This allows JAA.AI to:

- Create new conversations
- Continue previous conversations
- Store conversation history
- Load previous messages
- Delete conversations

Chat history is persisted using SQLite and SQLAlchemy.

---

🔒 Security

The application includes basic security and validation mechanisms:

- PDF-only upload validation
- Maximum PDF upload size
- PDF signature validation
- Question length validation
- Session ID validation
- Server-side generated filenames
- Environment variables for secrets
- CORS configuration
- API error handling
- Protection against exposing internal configuration

---

🧪 Testing

The application has been tested for:

- FastAPI startup
- Health endpoint
- AI question answering
- PDF upload
- PDF indexing
- RAG-based question answering
- Chat history
- New chat sessions
- Chat deletion
- Frontend/backend communication
- Render deployment
- Production health endpoint

---

🚀 Deployment

JAA.AI is deployed as a FastAPI Web Service on Render.

Production URL:

https://jaa-ai.onrender.com

The project uses GitHub-based deployment. Code changes pushed to the configured branch can trigger a new Render deployment.

---

🎯 Future Improvements

Planned or possible improvements include:

- Streaming AI responses
- Better source citations
- Multi-PDF management
- User authentication
- PostgreSQL production database
- Advanced document metadata filtering
- Automated RAG evaluation
- Docker containerization
- CI/CD pipeline
- Rate limiting
- Observability and structured logging
- Role-based access control

---

👨‍💻 Author

Jaseem Ahmad

B.Tech — Computer Science & Engineering

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

The goal is to provide a strong foundation for a scalable, production-oriented AI assistant while demonstrating practical skills in Generative AI, RAG systems, backend development, vector databases, API integration, and cloud deployment.