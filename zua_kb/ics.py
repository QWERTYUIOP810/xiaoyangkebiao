# -*- coding: utf-8 -*-
"""把课程列表写成 iCalendar (.ics)，手机日历订阅后即可按周查看。"""

import hashlib
from datetime import date, datetime, time, timedelta, timezone

from .periods import end_time, start_time

TZID = "Asia/Shanghai"
VTIMEZONE = """BEGIN:VTIMEZONE
TZID:Asia/Shanghai
X-LIC-LOCATION:Asia/Shanghai
BEGIN:STANDARD
DTSTART:19700101T000000
TZOFFSETFROM:+0800
TZOFFSETTO:+0800
TZNAME:CST
END:STANDARD
END:VTIMEZONE"""


def _esc(s):
    return (
        str(s)
        .replace("\\", "\\\\")
        .replace(";", "\\;")
        .replace(",", "\\,")
        .replace("\n", "\\n")
    )


def _fold(line):
    """按 RFC5545 每行不超过 75 字节折行。"""
    raw = line.encode("utf-8")
    if len(raw) <= 75:
        return [line]
    out, cur, size = [], "", 0
    for ch in line:
        b = len(ch.encode("utf-8"))
        if size + b > 74:
            out.append(cur)
            cur, size = " " + ch, 1 + b
        else:
            cur += ch
            size += b
    if cur:
        out.append(cur)
    return out


def build_ics(courses, term_start, cal_name="郑航课表", max_week=20):
    """term_start: 第 1 周周一的 date。"""
    if isinstance(term_start, str):
        term_start = datetime.strptime(term_start, "%Y-%m-%d").date()

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//zua-kb//ZUA Schedule//CN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        "X-WR-CALNAME:" + _esc(cal_name),
        "X-WR-TIMEZONE:" + TZID,
        "X-PUBLISHED-TTL:PT1H",
        "REFRESH-INTERVAL;VALUE=DURATION:PT1H",
    ]
    lines += VTIMEZONE.splitlines()

    seen = set()
    for c in courses:
        weeks = sorted(w for w in (c.weeks or range(1, max_week + 1)) if 1 <= w <= max_week)
        s_slot, e_slot = c.slots
        for w in weeks:
            day = term_start + timedelta(weeks=w - 1, days=c.weekday - 1)
            key = (c.name, c.weekday, c.slots, w, c.room)
            if key in seen:
                continue
            seen.add(key)

            dt_start = datetime.combine(day, time.fromisoformat(start_time(s_slot)))
            dt_end = datetime.combine(day, time.fromisoformat(end_time(e_slot)))

            desc = []
            if c.teacher:
                desc.append("教师：" + c.teacher)
            if c.weeks:
                desc.append("周次：" + ",".join(str(x) for x in sorted(c.weeks)))
            desc.append("第%d-%d节" % (s_slot, e_slot))

            uid_src = "%s|%s|%s|%s|%s" % (c.name, c.weekday, c.slots, w, c.room)
            uid = hashlib.md5(uid_src.encode("utf-8")).hexdigest() + "@zua-kb"

            lines += [
                "BEGIN:VEVENT",
                "UID:" + uid,
                "DTSTAMP:" + stamp,
                "DTSTART;TZID=%s:%s" % (TZID, dt_start.strftime("%Y%m%dT%H%M%S")),
                "DTEND;TZID=%s:%s" % (TZID, dt_end.strftime("%Y%m%dT%H%M%S")),
                "SUMMARY:" + _esc(c.name),
                "LOCATION:" + _esc(c.room),
                "DESCRIPTION:" + _esc("\n".join(desc)),
                "END:VEVENT",
            ]

    lines.append("END:VCALENDAR")

    folded = []
    for line in lines:
        folded.extend(_fold(line))
    return "\r\n".join(folded) + "\r\n"


def merge_windows(courses):
    """辅助：把同一门课连续节次合并（当前 parser 已按区间给出，保留备用）。"""
    return courses
