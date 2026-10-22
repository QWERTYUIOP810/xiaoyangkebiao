# -*- coding: utf-8 -*-
"""解析郑航金智 EAMS 的课表页。

真实结构（2026-10 抓取确认）：

    var unitCount = 10;
    activity = new TaskActivity(教师id, 教师名, 课程代码, 课程名(代码), 房间id,
                                教室, 周次位串, null, null, 助教, 备注, "");
    index = 周几*unitCount + 第几节;   // 都是 0 基
    table0.activities[index][...] = activity;

周次位串是 53 个字符，第 i 位是 '1' 表示第 i+1 周上课。
"""

import re
from dataclasses import dataclass, field

WEEKDAY_TOKENS = {
    "星期一": 1, "周一": 1, "星期二": 2, "周二": 2, "星期三": 3, "周三": 3,
    "星期四": 4, "周四": 4, "星期五": 5, "周五": 5, "星期六": 6, "周六": 6,
    "星期日": 7, "星期天": 7, "周日": 7, "周天": 7,
}

CODE_SUFFIX = re.compile(r"\s*\([0-9A-Za-z][0-9A-Za-z.\-]*\)\s*$")
ROOM_PAREN = re.compile(r"^([^(（]+)[(（](.+)[)）]\s*$")


@dataclass
class Course:
    name: str
    weekday: int
    slots: tuple          # (start, end)，1 基，闭区间
    weeks: frozenset = field(default_factory=frozenset)
    teacher: str = ""
    room: str = ""
    note: str = ""
    raw: str = ""


def _unquote(tok):
    tok = tok.strip()
    if len(tok) >= 2 and tok[0] == tok[-1] and tok[0] in "\"'":
        body = tok[1:-1]
        return body.replace("\\'", "'").replace('\\"', '"').replace("\\\\", "\\")
    if tok in ("null", "undefined"):
        return ""
    return tok


def _scan_call(s, i):
    """s[i] 是 '('；返回 (参数列表, 结束位置)，正确处理引号和嵌套括号。"""
    assert s[i] == "("
    depth = 0
    args, cur = [], []
    quote = None
    while i < len(s):
        ch = s[i]
        if quote:
            if ch == "\\" and i + 1 < len(s):
                cur.append(ch)
                cur.append(s[i + 1])
                i += 2
                continue
            if ch == quote:
                quote = None
            cur.append(ch)
        else:
            if ch in "\"'":
                quote = ch
                cur.append(ch)
            elif ch == "(":
                depth += 1
                if depth > 1:
                    cur.append(ch)
            elif ch == ")":
                depth -= 1
                if depth == 0:
                    args.append("".join(cur))
                    return args, i + 1
                cur.append(ch)
            elif ch == "," and depth == 1:
                args.append("".join(cur))
                cur = []
            else:
                cur.append(ch)
        i += 1
    return None, i


def _weeks_from_bits(bits):
    """位串下标就是教学周（第 0 位不用），见 TaskActivity.js 的 marshal()。"""
    return frozenset(
        i for i, ch in enumerate(bits) if ch == "1" and 1 <= i <= 30
    )


def _teacher_before(html, pos):
    """教师名不在参数里，是前面 actTeachers 数组拼出来的。"""
    chunk = html[max(0, pos - 3000):pos]
    last = None
    for last in re.finditer(r"actTeachers\s*=\s*\[(.*?)\]\s*;", chunk, re.S):
        pass
    if not last:
        return ""
    names = re.findall(r'name\s*:\s*"([^"]*)"', last.group(1))
    return "、".join(n for n in names if n)


def parse_js_activities(html):
    """从 TaskActivity 脚本里解析课程。"""
    unit_m = re.search(r"var\s+unitCount\s*=\s*(\d+)", html)
    unit = int(unit_m.group(1)) if unit_m else 10

    events = []
    for m in re.finditer(r"TaskActivity\s*\(", html):
        args, _ = _scan_call(html, m.end() - 1)
        if args and len(args) >= 7:
            events.append((m.start(), "act", args))
    for m in re.finditer(r"index\s*=\s*(\d+)\s*\*\s*unitCount\s*\+\s*(\d+)", html):
        events.append((m.start(), "idx", (int(m.group(1)), int(m.group(2)))))
    events.sort(key=lambda x: x[0])

    raw_courses = []
    cur, cur_pos = None, 0
    for pos, kind, payload in events:
        if kind == "act":
            cur, cur_pos = payload, pos
            continue
        if cur is None:
            continue
        wd, slot = payload
        if not (0 <= wd < 7 and 0 <= slot < unit):
            continue
        raw_courses.append((cur, cur_pos, wd + 1, slot + 1))

    courses = []
    for args, pos, wd, slot in raw_courses:
        teacher = _unquote(args[1])
        if not teacher or "join(" in teacher:
            teacher = _teacher_before(html, pos)
        full_name = _unquote(args[3])
        room_raw = _unquote(args[5])
        weeks = _weeks_from_bits(_unquote(args[6]))
        note = _unquote(args[10]) if len(args) > 10 else ""

        if not weeks or room_raw.strip() == "停课":
            continue

        name = CODE_SUFFIX.sub("", full_name).strip() or full_name
        room = room_raw
        m = ROOM_PAREN.match(room_raw)
        if m:
            room = m.group(1).strip()
            if not note:
                note = m.group(2).strip()

        courses.append(
            Course(
                name=name,
                weekday=wd,
                slots=(slot, slot),
                weeks=weeks,
                teacher=teacher,
                room=room,
                note=note,
                raw=full_name,
            )
        )

    return _merge_slots(courses)


def _merge_slots(courses):
    """把同一门课连续的节次合并成区间，顺便去重。"""
    buckets = {}
    for c in courses:
        key = (c.name, c.weekday, c.room, c.weeks, c.teacher, c.note)
        buckets.setdefault(key, set()).add(c.slots[0])

    merged = []
    for key, slots in buckets.items():
        name, wd, room, weeks, teacher, note = key
        ordered = sorted(slots)
        start = prev = ordered[0]
        ranges = []
        for s in ordered[1:]:
            if s == prev + 1:
                prev = s
            else:
                ranges.append((start, prev))
                start = prev = s
        ranges.append((start, prev))
        for a, b in ranges:
            merged.append(
                Course(name, wd, (a, b), weeks, teacher, room, note, name)
            )

    merged.sort(key=lambda c: (c.weekday, c.slots[0], c.name))
    return merged


# ---------------------------------------------------------------- 兜底：网格

def _norm(s):
    return re.sub(r"\s+", " ", s or "").strip()


def parse_grid(html):
    """备用：按「表头星期 / 首列节次」的普通表格解析。"""
    from lxml import html as LH

    doc = LH.fromstring(html)
    rows = doc.xpath("//tr")
    if not rows:
        return []

    header = (-1, {})
    for i, row in enumerate(rows):
        cells = row.xpath("./td|./th")
        mapping = {}
        for idx, cell in enumerate(cells):
            t = _norm(cell.text_content())
            for tok, wd in WEEKDAY_TOKENS.items():
                if tok in t:
                    mapping[idx] = wd
                    break
        if len(mapping) > len(header[1]):
            header = (i, mapping)

    if len(header[1]) < 3:
        return []

    courses, last_slot = [], None
    for row in rows[header[0] + 1:]:
        cells = row.xpath("./td|./th")
        if not cells:
            continue
        m = re.search(r"第?\s*(\d{1,2})\s*节", _norm(cells[0].text_content()))
        if m:
            last_slot = int(m.group(1))
        if not last_slot:
            continue
        for idx, wd in header[1].items():
            if idx >= len(cells):
                continue
            text = _norm(cells[idx].text_content())
            if not text:
                continue
            name = text.split(" ")[0]
            courses.append(
                Course(name=name, weekday=wd, slots=(last_slot, last_slot),
                       weeks=frozenset(range(1, 19)), raw=text)
            )
    return courses


def parse_course_table(html):
    courses = parse_js_activities(html)
    if courses:
        return courses
    return parse_grid(html)
