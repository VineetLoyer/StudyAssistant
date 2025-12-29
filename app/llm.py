import os
from openai import OpenAI
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
MODEL = os.getenv("LLM_MODEL","gpt-4o-mini")

QA_SYS = (
 "Answer using ONLY the provided snippets. "
 "Keep it ≤ 120 words. After each claim, cite (slide X) or (page X). "
 "If info isn’t present, say 'not found in range'."
)

def answer_with_llm(question: str, snippets: list[dict]) -> str:
    ctx = "\n\n".join(
        f"(source {s['source_id']}) {s['text']}" for s in snippets
    )
    msgs = [
        {"role":"system","content": QA_SYS},
        {"role":"user","content": f"QUESTION: {question}\nSNIPPETS:\n{ctx}"}
    ]
    r = client.chat.completions.create(model=MODEL, messages=msgs, temperature=0.1)
    return r.choices[0].message.content.strip()

NOTES_SYSTEM = (
    "You are a study-notes writer. Use ONLY the provided CHUNKS. "
    "If info is missing, write 'not found in range'. Keep bullets concise (≤12 words), "
    "max 6 bullets/section. Always cite sources as (slide X) or (page X) at the end.\n"
    "Return Markdown with these sections:\n"
    "## Outline\n## Key Terms\n## Formulas\n## Examples\n## Self-Checks"
)
def make_notes_with_llm(style: str, snippets: list[dict]) -> str:
    # snippets: [{source_id, text}]
    # pack up to ~25 snippets to stay cheap
    packed = snippets[:25]
    ctx = "\n\n".join(f"[{i+1}] (src {s['source_id']}) {s['text']}" for i, s in enumerate(packed))
    user = (
        f"STYLE: {style}\n\n"
        f"CHUNKS (with source ids):\n{ctx}\n\n"
        f"Write the Markdown now. Keep it concise and cite each bullet."
    )
    r = client.chat.completions.create(
        model=MODEL,
        temperature=0.2,
        messages=[{"role":"system","content":NOTES_SYSTEM},
                  {"role":"user","content":user}]
    )
    return r.choices[0].message.content.strip()

QUIZ_SYSTEM = (
  "You are a careful quiz writer. Use ONLY the provided snippets from slides/pages. "
  "Write a balanced 10-minute quiz with MCQ, short answer, and cloze items. "
  "Each item MUST include a 'source_id' that points to the slide/page number you used. "
  "Never use outside knowledge."
)

def make_quiz_with_llm(focus: list[str], snippets: list[dict], n_items: int = 10):
    ctx = "\n\n".join(f"(src {s['source_id']}) {s['text']}" for s in snippets[:28])
    user = (
      f"FOCUS: {', '.join(focus)}\n\n"
      f"SNIPPETS:\n{ctx}\n\n"
      "Return strict JSON with this shape:\n"
      "{ \"items\": ["
      "{ \"qtype\": \"mcq|short|cloze\", "
      "\"question\": \"...\", "
      "\"options\": [\"A\",\"B\",\"C\",\"D\"] | null, "
      "\"answer\": \"...\", "
      "\"source_id\": \"<slide-or-page-number>\", "
      "\"rationale\": \"(optional)\" }"
      "] }\n"
      f"Create {n_items} items. Keep questions terse and unambiguous."
    )
    r = client.chat.completions.create(
        model=MODEL, temperature=0.2,
        messages=[{"role":"system","content":QUIZ_SYSTEM},
                  {"role":"user","content":user}]
    )
    return r.choices[0].message.content