# -*- coding: utf-8 -*-
"""金智 EAMS（郑航教务系统）登录与课表抓取。

登录页关键点（已在真实系统验证）：
1. GET /eams/loginExt.action 拿到 _csrf 和一个「每次刷新都变」的盐值；
2. 密码发送的是 sha1(盐值 + 明文密码)；
3. 页面渲染后立刻提交会返回「请不要过快点击」，需要等几秒；
4. 验证码输入框不存在（未启用）。
"""

import hashlib
import re
import time

import requests

BASE = "http://jwglxt.zua.edu.cn"

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)


class LoginError(RuntimeError):
    pass


def new_session():
    s = requests.Session()
    s.headers.update(
        {
            "User-Agent": UA,
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }
    )
    return s


def _snippet(text, n=200):
    text = re.sub(r"<script[\s\S]*?</script>", " ", text)
    text = re.sub(r"<style[\s\S]*?</style>", " ", text)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:n]


def login(session, username, password, base=BASE, delay=6.0):
    """登录并返回同一个 session（cookie 已带上）。"""
    url = base + "/eams/loginExt.action"
    r = session.get(url, timeout=30)
    r.raise_for_status()

    html = r.text
    m = re.search(r'name="_csrf"[^>]*value="([^"]+)"', html)
    if not m:
        raise LoginError("登录页里找不到 _csrf，系统可能改版了")
    csrf = m.group(1)

    m = re.search(r"CryptoJS\.SHA1\('([^']+)'\s*\+", html)
    if not m:
        raise LoginError("登录页里找不到密码盐值，系统可能改版了")
    salt = m.group(1)

    # 东财/金智的防刷：页面渲染后太快提交会被拒绝
    time.sleep(delay)

    hashed = hashlib.sha1((salt + password).encode("utf-8")).hexdigest()
    r = session.post(
        url,
        data={
            "needModify": "0",
            "_csrf": csrf,
            "username": username,
            "password": hashed,
            "session_locale": "zh_CN",
            "login_from": "login_from",
            "submitBtn": "登录",
        },
        timeout=30,
    )
    text = r.text

    if "请不要过快点击" in text:
        raise LoginError("提交太快被拦了，把 delay 调大一点")
    if "账号或密码异常" in text or "账号或密码错误" in text:
        raise LoginError("账号或密码不对")
    if "loginExt" in r.url:
        raise LoginError("登录没有成功：" + _snippet(text))

    return session


def fetch_course_table(session, base=BASE, semester_id=None):
    """抓学生课表。

    入口页只是个壳：真正的表格由 JS 用 POST 请求
    courseTableForStd!courseTable.action 填进 #contentDiv，
    需要带上「学生 id」和「学期 id」，这两个值从入口页里取。
    """
    r = session.get(base + "/eams/courseTableForStd.action", timeout=30)
    r.raise_for_status()
    if "loginExt" in r.url:
        raise LoginError("会话失效，被踢回登录页")
    html = r.text

    ids = re.search(r'addInput\(form,"ids","(\d+)"\)', html)
    sem = re.search(r'semesterCalendar\(\{[^}]*value:"(\d+)"', html)

    data = {
        "ignoreHead": "1",
        "setting.kind": "std",
        "startWeek": "",
        "semester.id": str(semester_id or (sem.group(1) if sem else "")),
        "ids": ids.group(1) if ids else "",
    }
    r2 = session.post(base + "/eams/courseTableForStd!courseTable.action", data=data, timeout=30)
    r2.raise_for_status()
    if "loginExt" in r2.url:
        raise LoginError("会话失效，被踢回登录页")
    return r2.text
