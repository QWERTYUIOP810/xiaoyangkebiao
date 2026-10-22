# -*- coding: utf-8 -*-
"""郑航课表 -> iCalendar。

用法:
    python -m zua_kb.main --demo                    # 用假数据生成示例 ics
    python -m zua_kb.main --dump docs/table.html    # 抓课表页并存下来（调试用）
    python -m zua_kb.main --out docs/schedule.ics   # 正常生成

环境变量:
    ZUA_USER / ZUA_PASS       学号、密码
    ZUA_TERM_START            第 1 周周一的日期，如 2026-08-31
    ZUA_BASE                  默认 http://jwglxt.zua.edu.cn
"""

import argparse
import os
import sys
from datetime import date

from . import eams
from .ics import build_ics
from .parser import Course, parse_course_table
from .render import render_html


def load_dotenv(path=".env"):
    """极简 .env 读取：KEY=VALUE，支持 # 注释。"""
    if not os.path.exists(path):
        return
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def demo_courses():
    return [
        Course("高等数学", 1, (1, 2), frozenset(range(1, 17)), "张老师", "05A101"),
        Course("大学英语", 2, (3, 4), frozenset(range(1, 17)), "李老师", "05B203"),
        Course("数据结构", 3, (5, 6), frozenset(range(1, 9)) | frozenset(range(10, 17)), "王老师", "06C305"),
        Course("体育", 4, (7, 8), frozenset(range(1, 17)), "刘老师", "东操场"),
        Course("马克思主义基本原理", 5, (9, 10), frozenset([1, 3, 5, 7, 9, 11, 13, 15]), "陈老师", "07A201"),
    ]


def main(argv=None):
    load_dotenv()
    ap = argparse.ArgumentParser()
    ap.add_argument("--demo", action="store_true")
    ap.add_argument("--dump", metavar="PATH", help="保存课表页 HTML 到指定文件")
    ap.add_argument("--out", default="docs/schedule.ics")
    ap.add_argument("--term-start", default=os.environ.get("ZUA_TERM_START", ""))
    ap.add_argument("--cal-name", default="郑航课表")
    args = ap.parse_args(argv)

    if args.demo:
        courses = demo_courses()
        term = date.fromisoformat(args.term_start) if args.term_start else date(2026, 8, 31)
    else:
        user = os.environ.get("ZUA_USER", "")
        pwd = os.environ.get("ZUA_PASS", "")
        if not user or not pwd:
            print("缺少 ZUA_USER / ZUA_PASS 环境变量", file=sys.stderr)
            return 2
        base = os.environ.get("ZUA_BASE", eams.BASE)
        s = eams.new_session()
        try:
            eams.login(s, user, pwd, base=base)
            html = eams.fetch_course_table(s, base=base)
        except eams.LoginError as e:
            print("登录/抓取失败：%s" % e, file=sys.stderr)
            return 1

        if args.dump:
            os.makedirs(os.path.dirname(args.dump) or ".", exist_ok=True)
            with open(args.dump, "w", encoding="utf-8") as f:
                f.write(html)
            print("已保存课表页：%s（%d 字节）" % (args.dump, len(html)))

        courses = parse_course_table(html)
        if not courses:
            print("没有解析出任何课程，页面结构可能和金智默认布局不同。", file=sys.stderr)
            print("请加 --dump 保存 HTML 后反馈。", file=sys.stderr)
            return 3
        if not args.term_start:
            print("缺少 ZUA_TERM_START（第 1 周周一的日期）", file=sys.stderr)
            return 2
        term = date.fromisoformat(args.term_start)

    text = build_ics(courses, term, cal_name=args.cal_name)
    out = args.out
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    with open(out, "w", encoding="utf-8", newline="") as f:
        f.write(text)

    html_out = os.path.join(os.path.dirname(out) or ".", "index.html")
    with open(html_out, "w", encoding="utf-8") as f:
        f.write(render_html(courses, term, title=args.cal_name))
    print("已生成 %s：%d 门课，%d 字节" % (out, len(courses), len(text.encode("utf-8"))))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
