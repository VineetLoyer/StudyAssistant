from pydantic import BaseModel, Field
from typing import List, Optional, Dict

class LoadMaterialRequest(BaseModel):
    file_id: str = Field(..., description="Arbitrary ID for the uploaded file")
    type: str = Field(..., description='One of: "pdf","pptx","docx"')
    range: str = Field(..., description='e.g., "slides 1-35" or "pages 3-20"')
    local_path: Optional[str] = None  # dev-only: local file path

class LoadMaterialResponse(BaseModel):
    corpus_id: str
    chunks_indexed: int
    sources: List[str]

class AnswerQuestionRequest(BaseModel):
    corpus_id: str
    query: str
    top_k: int = 6

class AnswerQuestionResponse(BaseModel):
    answer: str
    citations: List[Dict[str, str]]  # [{source_id, excerpt}]


class MakeNotesRequest(BaseModel):
    corpus_id: str
    style: str = "concise"     # "concise" | "exam" | "lecture"
    export_pdf: bool = True

class MakeNotesResponse(BaseModel):
    notes_md: str
    pdf_url: Optional[str] = None

class QuizItem(BaseModel):
    qtype: str                 # "mcq" | "short" | "cloze"
    question: str
    options: Optional[List[str]] = None
    answer: str
    source_id: str             # slide/page/timecode id
    rationale: Optional[str] = None

class GenerateQuizRequest(BaseModel):
    corpus_id: str
    duration: int = 10
    items: int = 10
    focus: List[str] = ["definitions","concepts","derivations"]

class GenerateQuizResponse(BaseModel):
    quiz_id: str
    items: List[QuizItem]

# ---------- Day 4: Scheduling ----------
class SchedulePlan(BaseModel):
    mode: str                  # "once" | "spaced"
    end_date: Optional[str] = None   # YYYY-MM-DD (required if mode="spaced")
    days: Optional[List[str]] = None # ["Mon","Thu"] (for spaced mode)
    window: Optional[str] = None     # "19:00-21:00" local time

class ScheduleQuizRequest(BaseModel):
    quiz_id: str
    plan: SchedulePlan
    title: str = "Pop Quiz"
    tz: Optional[str] = None         # e.g., "America/Los_Angeles"
    confirm: bool = True             # if False, return a summary preview only

class ScheduledEvent(BaseModel):
    start: str       # ISO
    end: str         # ISO
    title: str
    description: str

class ScheduleQuizResponse(BaseModel):
    events: List[ScheduledEvent]
    ics_url: Optional[str] = None
    preview_only: bool = False

