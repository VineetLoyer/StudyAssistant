import re, hashlib
from typing import Tuple

RANGE_RE = re.compile(r"(slides|pages)\s+(\d+)\s*-\s*(\d+)", re.I)

def parse_range(s: str) -> Tuple[str,int,int]:
    m = RANGE_RE.search(s or "")
    if not m: raise ValueError("Use 'slides 1-35' or 'pages 3-20'")
    kind, a, b = m.group(1).lower(), int(m.group(2)), int(m.group(3))
    if a < 1 or b < a: raise ValueError("Invalid range numbers")
    return kind, a, b

def md5_hex(s: str) -> str:
    return hashlib.md5(s.encode("utf-8")).hexdigest()
