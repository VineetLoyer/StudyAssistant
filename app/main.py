# app/main.py
import os
from typing import Optional 
from fastapi import FastAPI, HTTPException, Header
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from dotenv import load_dotenv
import jwt
import uuid
from .models import LoadMaterialRequest, LoadMaterialResponse, MakeNotesRequest, MakeNotesResponse, GenerateQuizRequest, GenerateQuizResponse, QuizItem,ScheduleQuizRequest, ScheduleQuizResponse, ScheduledEvent
from .utils import parse_range, md5_hex
from .ingestion import extract_pdf_pages, extract_pptx_slides, extract_docx_pages, make_chunks
from .models import AnswerQuestionRequest, AnswerQuestionResponse
from .store import VectorStore
from .llm import answer_with_llm, make_notes_with_llm, make_quiz_with_llm
from .schedule import gen_events_once, gen_events_spaced, write_ics, DOWNLOAD_DIR
from .pdf import markdown_to_html, html_to_pdf, DOWNLOAD_DIR
from .auth import require_user


load_dotenv()
app = FastAPI(title="Study MCP — Day1")
app.mount("/downloads", StaticFiles(directory=DOWNLOAD_DIR), name="downloads")

# --------- auth helper ----------
def _decode_bearer(authorization: str):
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    token = authorization.split(" ", 1)[1]
    issuer = os.getenv("JWT_ISSUER", "cequence")
    audience = os.getenv("JWT_AUDIENCE", "study-mcp")
    alg = os.getenv("JWT_ALG", "HS256")
    secret = os.getenv("JWT_SECRET", "dev-demo-secret-change-me")
    try:
        return jwt.decode(
            token, secret, algorithms=[alg], audience=audience, issuer=issuer,
            options={"require": ["exp", "iat"]}
        )
    except jwt.InvalidTokenError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {e}")

# --------- baseline routes ----------
@app.get("/health")
def health():
    return {"ok": True}

# @app.get("/whoami")
# def whoami(authorization: str = Header(default=None), x_user_id: str = Header(default=None)):
#     claims = _decode_bearer(authorization)
#     scopes = claims.get("scopes") or []
#     if isinstance(scopes, str): scopes = [scopes]
#     return {"sub": claims.get("sub"), "scopes": scopes, "user_id": x_user_id}
# @app.get("/whoami")
# def whoami(authorization: str = Header(default=None)):
#     session = require_user(authorization)
#     sub = session.get("subject") or session.get("claims", {}).get("sub")
#     return {"sub": sub, "aud": session.get("claims", {}).get("aud")}

@app.get("/whoami")
def whoami(authorization: str = Header(default=None)):
    s = require_user(authorization)
    aud = s["claims"].get("aud")
    if not aud:
        return {"sub": s["subject"], "aud": None, "note": "aud claim missing in token"}
    return {"sub": s["subject"], "aud": aud}

# --------- TEMP: inline models + stub load_material ----------
class LoadMaterialRequest(BaseModel):
    file_id: str = Field(..., description="Arbitrary ID")
    type: str = Field(..., description='One of: "pdf","pptx","docx"')
    range: str = Field(..., description='e.g., "slides 1-5" or "pages 3-10"')
    local_path: Optional[str] = None

class LoadMaterialResponse(BaseModel):
    corpus_id: str
    chunks_indexed: int
    sources: list[str]

def _md5_hex(s: str) -> str:
    import hashlib
    return hashlib.md5(s.encode("utf-8")).hexdigest()

def _parse_range(s: str):
    import re
    m = re.search(r"(slides|pages)\s+(\d+)\s*-\s*(\d+)", s or "", re.I)
    if not m: raise HTTPException(status_code=400, detail="Use 'slides a-b' or 'pages a-b'")
    kind, a, b = m.group(1).lower(), int(m.group(2)), int(m.group(3))
    if a < 1 or b < a: raise HTTPException(status_code=400, detail="Invalid range numbers")
    return kind, a, b

store = VectorStore()

@app.post("/mcp/tools/load_material", response_model=LoadMaterialResponse)
def load_material(req: LoadMaterialRequest, authorization: str = Header(default=None)):
    # _ = _decode_bearer(authorization)  # verifies token
    session = require_user(authorization)
    user_id = session["subject"]  # use this if you need per-user storage later

    kind, start, end = parse_range(req.range)
    if not req.local_path or not os.path.exists(req.local_path):
        raise HTTPException(status_code=400, detail="Provide existing local_path for dev")

    if req.type.lower() == "pdf" and kind == "pages":
        items = extract_pdf_pages(req.local_path, start, end)
    elif req.type.lower() == "pptx" and kind == "slides":
        items = extract_pptx_slides(req.local_path, start, end)
    elif req.type.lower() == "docx":
        items = extract_docx_pages(req.local_path, start, end)
    else:
        raise HTTPException(status_code=400, detail="Type/range mismatch. Use 'pages' for pdf/docx and 'slides' for pptx.")

    corpus_id = md5_hex(f"{req.file_id}:{req.type}:{req.range}")[:12]
    chunks = make_chunks(kind, items, corpus_id)
    if not chunks:
        raise HTTPException(status_code=422, detail="No text extracted in the specified range")

    store.add_corpus(corpus_id, chunks)
    sources = sorted({c.source_id for c in chunks}, key=lambda x: int(x))
    return LoadMaterialResponse(corpus_id=corpus_id, chunks_indexed=len(chunks), sources=sources)


@app.post("/mcp/tools/answer_question", response_model=AnswerQuestionResponse)
def answer_question(req: AnswerQuestionRequest, authorization: str = Header(default=None)):
    _ = _decode_bearer(authorization)
    session = require_user(authorization)
    user_id = session["subject"]  # use this if you need per-user storage later

    hits = store.search(req.query, req.corpus_id, k=req.top_k)
    if not hits:
        return AnswerQuestionResponse(answer="not found in range", citations=[])
    chunks = store.get_chunks([i for i,_ in hits])
    snippets = [
        {"source_id": c.source_id, "text": c.text[:500]}
        for c in chunks
    ]
    ans = answer_with_llm(req.query, snippets[:min(req.top_k, len(snippets))])
    cits = [{"source_id": c.source_id, "excerpt": c.text[:140]} for c in chunks[:req.top_k]]
    return AnswerQuestionResponse(answer=ans, citations=cits)

@app.post("/mcp/tools/make_notes", response_model=MakeNotesResponse)
def make_notes(req: MakeNotesRequest, authorization: str = Header(default=None)):
    
    session = require_user(authorization)
    user_id = session["subject"]  # use this if you need per-user storage later

    # auth check (reuse your existing _decode_bearer)
    _ = _decode_bearer(authorization)

    # collect snippets from corpus
    snippets = store.all_chunks_for_corpus(req.corpus_id, max_per_source=4, max_total=28)
    if not snippets:
        raise HTTPException(status_code=404, detail="No chunks for this corpus_id; load material first.")

    # call LLM
    notes_md = make_notes_with_llm(req.style, snippets)

    # optional export to PDF
    pdf_url = None
    if req.export_pdf:
        html = markdown_to_html(notes_md)
        pdf_path = html_to_pdf(html, filename_hint=f"notes-{req.corpus_id}")
        # turn path into URL under /downloads
        fname = os.path.basename(pdf_path)
        pdf_url = f"/downloads/{fname}"

    return MakeNotesResponse(notes_md=notes_md, pdf_url=pdf_url)


QUIZZES: dict[str, list[dict]] = {}

@app.post("/mcp/tools/generate_quiz", response_model=GenerateQuizResponse)
def generate_quiz(req: GenerateQuizRequest, authorization: str = Header(default=None)):
    session = require_user(authorization)
    user_id = session["subject"]  # use this if you need per-user storage later

    _ = _decode_bearer(authorization)

    # collect snippets from this corpus
    snippets = store.all_chunks_for_corpus(req.corpus_id, max_per_source=4, max_total=28)
    if not snippets:
        raise HTTPException(status_code=404, detail="No chunks for this corpus_id; load material first.")

    # call LLM
    raw = make_quiz_with_llm(req.focus, snippets, n_items=req.items)

    # parse LLM JSON safely
    import json, re
    try:
        js = json.loads(raw)
    except Exception:
        # try to extract JSON block if model added prose
        m = re.search(r'\{[\s\S]*\}', raw)
        js = json.loads(m.group(0)) if m else {"items":[]}

    items = []
    for it in js.get("items", [])[:req.items]:
        items.append(QuizItem(
            qtype=it.get("qtype","mcq"),
            question=it.get("question",""),
            options=it.get("options"),
            answer=it.get("answer",""),
            source_id=str(it.get("source_id","")),
            rationale=it.get("rationale")
        ).model_dump())

    if not items:
        raise HTTPException(status_code=500, detail="Quiz generation failed")

    quiz_id = uuid.uuid4().hex[:12]
    QUIZZES[quiz_id] = items
    return GenerateQuizResponse(quiz_id=quiz_id, items=[QuizItem(**i) for i in items])


@app.post("/mcp/tools/schedule_quiz", response_model=ScheduleQuizResponse)
def schedule_quiz(req: ScheduleQuizRequest, authorization: str = Header(default=None)):
    session = require_user(authorization)
    user_id = session["subject"]  # use this if you need per-user storage later

    _ = _decode_bearer(authorization)

    items = QUIZZES.get(req.quiz_id)
    if not items:
        raise HTTPException(status_code=404, detail="Unknown quiz_id")

    # Build description with quick summary + link back (you can add your UI link here)
    desc = f"Auto-generated 10-min quiz ({len(items)} items).\n"
    # choose events
    if req.plan.mode == "once":
        events = gen_events_once(req.tz, req.plan.window, f"{req.title}")
    elif req.plan.mode == "spaced":
        if not (req.plan.end_date and req.plan.days and req.plan.window):
            raise HTTPException(status_code=400, detail="end_date, days, and window required for spaced mode")
        events = gen_events_spaced(req.plan.end_date, req.plan.days, req.tz, req.plan.window, f"{req.title}")
    else:
        raise HTTPException(status_code=400, detail="mode must be 'once' or 'spaced'")

    # If confirm is False, return a preview only
    evs_out = [ScheduledEvent(start=e[0].isoformat(), end=e[1].isoformat(), title=e[2], description=desc) for e in events]
    if not req.confirm:
        return ScheduleQuizResponse(events=evs_out, preview_only=True)

    # Write ICS and expose via /downloads
    ics_path = write_ics(events, name_hint=f"quiz-{req.quiz_id}", description=desc)
    fname = os.path.basename(ics_path)
    ics_url = f"/downloads/{fname}"
    return ScheduleQuizResponse(events=evs_out, ics_url=ics_url, preview_only=False)

