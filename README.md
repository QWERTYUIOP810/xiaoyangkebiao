# 郑航课表 · 手机一键看

自动登录郑州航空工业管理学院教务系统（金智 EAMS），把课表变成：

- **手机网页**：加到桌面，点开就是本周课表，自动算周次、高亮今天、标出冲突；
- **iCalendar 订阅**：想用日历的话，订阅 `schedule.ics`。

后台每 4 小时自动更新一次，不用再登教务系统。

---

## 一、本机手动跑

```bash
python -m zua_kb.main --out docs/schedule.ics
```

需要先在本目录的 `.env` 里填好学号密码（`.env` 已在 `.gitignore`，不会提交）。

生成两个文件：

- `docs/index.html` —— 手机网页版课表
- `docs/schedule.ics` —— 日历订阅源

调试时加 `--dump docs/table.html` 会把教务系统原始课表页存下来。

---

## 二、部署到 GitHub（不用开电脑）

1. 新建仓库，把本目录推上去（见文末命令）。
2. **Settings → Secrets and variables → Actions**：
   - Secret `ZUA_USER` = 学号
   - Secret `ZUA_PASS` = 密码
   - Variables 标签 → Variable `ZUA_TERM_START` = `2026-09-07`
3. **Actions** → 选 `update-schedule` → **Run workflow**，确认变绿。
4. **Settings → Pages**：Source 选 `Deploy from a branch`，Branch `main`，目录 `/docs`，Save。
5. 一两分钟后：

```
https://<用户名>.github.io/<仓库名>/
https://<用户名>.github.io/<仓库名>/schedule.ics
```

---

## 三、手机上怎么用

1. 手机浏览器打开 Pages 地址
2. 菜单 → **添加到主屏幕**
3. 点桌面图标 → 本周课表；左右按钮翻周

一加 / ColorOS 自带日历不支持「网址订阅」，所以网页版是主推方案。
想用日历的话，用 Outlook（日历 → 添加 → 从 Web 订阅）粘贴 `schedule.ics` 地址。

---

## 四、几点说明

**学期起点**：`ZUA_TERM_START=2026-09-07` 是 2026-2027 学年第一学期第 1 周周一，
来自教务处《关于做好2026-2027学年第一学期开学初教学工作的通知》。
每学期换新的时候改这一个值。

**冲突标记**：教务系统里同一格叠两门课是允许的（常见于重修），系统会标红。
页面照原样显示并加「冲突」标签，不会替你隐藏。

**上课时间**：写在 `zua_kb/periods.py`，来源是教务处「上课时间安排」。
学校调整作息时改这里。

---

## 五、实现备忘

- 登录：`/eams/loginExt.action`，密码 = `sha1(页面里的盐 + 明文)`，
  提交太快会被「请不要过快点击」拦，脚本里固定等 6 秒。
- 课表：入口页是空的，真正的数据要 POST 到
  `courseTableForStd!courseTable.action`，带 `ids`（学生 id）和 `semester.id`，
  这两个值从入口页 HTML 里抠。
- 数据格式：`new TaskActivity(教师, 课程, 教室, 周次位串, ...)` +
  `index = 周几*10 + 第几节`（都是 0 基）。
  周次位串是 55 位，**下标即教学周**（第 0 位不用），见 `TaskActivity.js` 的 `marshal()`。

---

## 六、本地模式（GitHub 抓不到时）

Windows 任务计划定时跑 `update.bat`，再把 `docs/` 发布出去。
需要电脑开着。
