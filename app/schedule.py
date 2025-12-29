import os, uuid, datetime as dt
from typing import List, Optional
from dateutil import tz
from ics import Calendar, Event

DOWNLOAD_DIR = os.path.join(os.getcwd(), "downloads")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

WEEKMAP = {"Mon":0,"Tue":1,"Wed":2,"Thu":3,"Fri":4,"Sat":5,"Sun":6}

def pick_time_in_window(window: str) -> tuple[int,int]:
    # "19:00-21:00" -> pick center minute
    start_s, end_s = window.split("-")
    sh, sm = map(int, start_s.split(":"))
    eh, em = map(int, end_s.split(":"))
    start_minutes = sh*60 + sm
    end_minutes   = eh*60 + em
    mid = (start_minutes + end_minutes)//2
    return divmod(mid, 60)  # hour, minute

def gen_events_once(tzname: Optional[str],window: Optional[str],title: str,minutes: int = 10):
    now = dt.datetime.now(tz=tz.gettz(tzname)) if tzname else dt.datetime.now()
    if window:
        hh, mm = pick_time_in_window(window)
        start = now.replace(hour=hh, minute=mm, second=0, microsecond=0)
        if start < now:
            start = start + dt.timedelta(days=1)
    else:
        start = now + dt.timedelta(minutes=5)
    end = start + dt.timedelta(minutes=minutes)
    return [(start, end, title)]

def gen_events_spaced(end_date: str,days: list[str],tzname: Optional[str],window: str,title: str,minutes: int = 10) -> List[tuple]:
    assert days and window
    localtz = tz.gettz(tzname) if tzname else None
    today = dt.date.today()
    y, m, d = map(int, end_date.split("-"))
    until = dt.date(y, m, d)

    hh, mm = pick_time_in_window(window)
    events = []
    cur = today
    while cur <= until:
        if cur.weekday() in [WEEKMAP[d] for d in days]:
            start = dt.datetime(cur.year, cur.month, cur.day, hh, mm)
            if localtz: start = start.replace(tzinfo=localtz)
            end = start + dt.timedelta(minutes=minutes)
            events.append((start, end, title))
        cur += dt.timedelta(days=1)
    return events

def write_ics(events: List[tuple], name_hint: str, description: str = "") -> str:
    cal = Calendar()
    for (start, end, title) in events:
        ev = Event()
        ev.name = title
        ev.begin = start
        ev.end = end
        ev.description = description
        cal.events.add(ev)
    stem = f"{name_hint}-{uuid.uuid4().hex[:8]}.ics"
    path = os.path.join(DOWNLOAD_DIR, stem)
    with open(path, "w", encoding="utf-8") as f:
        f.writelines(cal)
    return path
