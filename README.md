# 郑航课表 · 手机一键看

**全程只用你自己的电脑连教务系统**，没有任何第三方服务器接触学校系统或你的密码。

流程：

```
你的电脑  →  登录教务系统抓课表  →  生成网页 + ICS  →  推送到 GitHub Pages  →  手机打开
```

GitHub 只保存「课表长什么样」，不参与抓取，也拿不到你的账号。

---

## 现在是怎么自动跑的

- 开机自启：`%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\ZUA-KB-Update.vbs`
- 启动后立刻跑一次，之后**每 4 小时**跑一次
- 实际执行：`run_update.bat` → `zua_kb.main`（抓取+生成）→ `publish.py`（推送）
- 日志：`logs/update.log`

只有课表内容真的变了才会产生提交，平时跑完是安静的。

## 手动跑一次

双击 `run_update.bat`，或者：

```bash
python -m zua_kb.main --out docs/schedule.ics
python publish.py
```

## 手机

打开 https://qwertyuiop810.github.io/zua-kb/

菜单 → **添加到主屏幕**，以后点图标就是本周课表。

日历订阅（可选）：https://qwertyuiop810.github.io/zua-kb/schedule.ics

---

## 需要注意

**令牌会过期**：`.token` 里的 GitHub 令牌 2026-10-29 到期。到期后推送会失败
（日志里会写 HTTP 401），换一个新令牌存进 `.token` 即可。

**电脑关机就不更新**：页面会停留在最后一次抓到的内容，不会变成空白。

**学期变了**：改 `.env` 里的 `ZUA_TERM_START`（第 1 周周一的日期）。
2026-2027 学年第一学期是 `2026-09-07`。

**上课时间变了**：改 `zua_kb/periods.py`。

---

## 实现备忘

- 登录：`/eams/loginExt.action`，密码 = `sha1(页面盐值 + 明文)`，提交太快会被
  「请不要过快点击」拦截，脚本固定等 6 秒。
- 课表：入口页是空壳，真正数据要 POST 到 `courseTableForStd!courseTable.action`，
  带 `ids`（学生 id）和 `semester.id`，两个值从入口页 HTML 里抠。
- 数据：`new TaskActivity(教师, 课程, 教室, 周次位串, ...)` +
  `index = 周几*10 + 第几节`（0 基）。周次位串 55 位，**下标即教学周**（第 0 位不用）。
- 教务系统会拦境外 IP（GitHub Actions 的 Azure 机房直接连超时），所以只能本机抓。
