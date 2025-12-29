# StudyAssistant

An AI-powered study assistant that helps students learn from educational materials. Built for the MCP Hackathon.

## Features

- **Material Ingestion** - Load PDFs, PowerPoints, and Word documents with page/slide range selection
- **Question Answering** - Ask questions about your materials with cited answers
- **Notes Generation** - Auto-generate structured study notes with PDF export
- **Quiz Generation** - Create MCQ, short answer, and cloze questions from your content
- **Quiz Scheduling** - Schedule quizzes with spaced repetition support and calendar export

## Tech Stack

| Component | Technology |
|-----------|------------|
| API | FastAPI + Uvicorn |
| Auth | Descope + PyJWT |
| Vector Search | FAISS (CPU) |
| Embeddings | sentence-transformers (MiniLM-L6-v2) |
| LLM | OpenAI GPT-4o-mini |
| Document Parsing | PyMuPDF, python-pptx, python-docx |
| PDF Export | pdfkit + wkhtmltopdf |

## Setup

### Prerequisites

- Python 3.10+
- wkhtmltopdf (for PDF export)
- OpenAI API key
- Descope project (for auth)

### Installation

```bash
# Clone the repo
git clone https://github.com/your-username/StudyAssistant.git
cd StudyAssistant

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt
```

### Environment Variables

Create a `.env` file:

```env
OPENAI_API_KEY=your-openai-key
DESCOPE_PROJECT_ID=your-descope-project-id
JWT_SECRET=your-jwt-secret
JWT_ISSUER=cequence
JWT_AUDIENCE=study-mcp
```

### Run

```bash
uvicorn app.main:app --reload
```

API available at `http://localhost:8000`

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `POST /mcp/tools/load_material` | Load and index a document |
| `POST /mcp/tools/answer_question` | Ask questions about indexed content |
| `POST /mcp/tools/make_notes` | Generate study notes |
| `POST /mcp/tools/generate_quiz` | Create a quiz |
| `POST /mcp/tools/schedule_quiz` | Schedule quiz sessions |
| `GET /health` | Health check |
| `GET /whoami` | Get current user info |

## License

MIT
