# -*- coding: utf-8 -*-
"""生成手机端「本周课表」网页（单文件，无依赖，可加到桌面）。"""

import json
from datetime import date

from .periods import PERIODS, WEEKDAY_CN


def _course_dict(c):
    weeks = sorted(c.weeks) if c.weeks else list(range(1, 19))
    return {
        "name": c.name,
        "teacher": c.teacher,
        "room": c.room,
        "weekday": c.weekday,
        "start": c.slots[0],
        "end": c.slots[1],
        "weeks": weeks,
    }


def render_html(courses, term_start, title="郑航课表"):
    if isinstance(term_start, str):
        term_start = date.fromisoformat(term_start)

    data = {
        "termStart": term_start.isoformat(),
        "title": title,
        "periods": {str(k): list(v) for k, v in PERIODS.items()},
        "courses": [_course_dict(c) for c in courses],
    }
    payload = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    return TEMPLATE.replace("/*__DATA__*/", payload)


TEMPLATE = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="theme-color" content="#0d6efd">
<title>本周课表</title>
<style>
  :root{
    --bg:#f5f6f8; --card:#fff; --text:#1c1f23; --muted:#8a9099;
    --line:#e8eaed; --accent:#0d6efd; --today:#e8f0ff;
  }
  @media (prefers-color-scheme: dark){
    :root{ --bg:#16181c; --card:#1f2227; --text:#e9ecef; --muted:#8b929c;
           --line:#2b2f36; --accent:#4c8dff; --today:#1d2a44; }
  }
  *{box-sizing:border-box;-webkit-tap-highlight-color:transparent}
  body{margin:0;background:var(--bg);color:var(--text);width:100%;overflow-x:hidden;
       font:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif;
       padding:0 0 40px;}
  header{position:sticky;top:0;z-index:9;background:var(--bg);padding:14px 16px 10px;
         border-bottom:1px solid var(--line);backdrop-filter:blur(8px)}
  .row{display:flex;align-items:center;justify-content:space-between;gap:8px}
  h1{font-size:19px;margin:0;font-weight:650}
  .sub{color:var(--muted);font-size:12px;margin-top:3px}
  .nav{display:flex;align-items:center;gap:6px}
  button{background:var(--card);border:1px solid var(--line);color:var(--text);
         border-radius:10px;padding:7px 11px;font-size:14px;cursor:pointer}
  button:active{transform:scale(.96)}
  .today-btn{color:var(--accent);border-color:var(--accent)}
  main{padding:12px 12px 0}
  .day{background:var(--card);border:1px solid var(--line);border-radius:14px;
       margin-bottom:10px;overflow:hidden}
  .day.today{border-color:var(--accent);background:var(--today)}
  .day-h{display:flex;justify-content:space-between;align-items:baseline;
         padding:10px 14px;border-bottom:1px solid var(--line);font-size:14px}
  .day-h b{font-weight:600}
  .day-h span{color:var(--muted);font-size:12px}
  .empty{padding:14px;color:var(--muted);font-size:13px;text-align:center}
  .item{display:flex;gap:12px;padding:11px 14px;border-top:1px solid var(--line)}
  .item:first-of-type{border-top:none}
  .item.clash{background:rgba(220,53,69,.06)}
  .tag.clash-tag{background:rgba(220,53,69,.12);color:#dc3545}
  .time{flex:0 0 78px;color:var(--muted);font-size:12px;line-height:1.5;padding-top:2px}
  .time b{display:block;color:var(--text);font-size:13px;font-weight:600}
  .body{min-width:0;flex:1}
  .name{font-size:15px;font-weight:600;line-height:1.35;word-break:break-word}
  .meta{color:var(--muted);font-size:12px;margin-top:3px;line-height:1.5;word-break:break-word}
  .tag{display:inline-block;border-radius:6px;padding:1px 6px;font-size:11px;
       background:rgba(13,110,253,.1);color:var(--accent);margin-left:6px;vertical-align:2px}
  .legend{text-align:center;color:var(--muted);font-size:11px;padding:6px 0 0}
</style>
</head>
<body>
<header>
  <div class="row">
    <div>
      <h1 id="title">本周课表</h1>
      <div class="sub" id="sub"></div>
    </div>
    <div class="nav">
      <button id="prev" aria-label="上一周">‹</button>
      <button id="next" aria-label="下一周">›</button>
    </div>
  </div>
</header>
<main id="main"></main>
<div class="legend">左右按钮切换周次 · 数据每次打开自动是最新的</div>

<script>
const D = /*__DATA__*/;
const DAY = 86400000;
const WEEKDAYS = ["周一","周二","周三","周四","周五","周六","周日"];

function parseDate(s){ const [y,m,d]=s.split("-").map(Number); return new Date(y,m-1,d); }
function startOfDay(d){ return new Date(d.getFullYear(),d.getMonth(),d.getDate()); }
function fmt(d){ return (d.getMonth()+1)+"月"+d.getDate()+"日"; }

const termStart = parseDate(D.termStart);
const today = startOfDay(new Date());
const baseWeek = Math.floor((today - termStart)/ (7*DAY)) + 1;
let week = Math.max(1, baseWeek);

function dateOf(w, wd){ return new Date(termStart.getTime() + ((w-1)*7 + (wd-1))*DAY); }
function sameDay(a,b){ return a.getFullYear()===b.getFullYear() && a.getMonth()===b.getMonth() && a.getDate()===b.getDate(); }

function hhmm(t){ return t; }

function render(){
  const main = document.getElementById("main");
  document.getElementById("title").textContent = "第 " + week + " 周";
  const mon = dateOf(week,1), sun = dateOf(week,7);
  document.getElementById("sub").textContent = fmt(mon)+" – "+fmt(sun) + (week===baseWeek ? " · 本周" : "");

  let html = "";
  for (let wd=1; wd<=7; wd++){
    const d = dateOf(week, wd);
    const isToday = sameDay(d, today);
    const items = D.courses
      .filter(c => c.weekday===wd && c.weeks.includes(week))
      .sort((a,b)=> a.start-b.start || a.end-b.end);

    html += '<section class="day'+(isToday?' today':'')+'"'+(isToday?' id="today"':'')+'>';
    html += '<div class="day-h"><b>'+WEEKDAYS[wd-1]+(isToday?' · 今天':'')+'</b><span>'+fmt(d)+'</span></div>';
    if (!items.length){
      html += '<div class="empty">没课</div>';
    } else {
      const clash = new Set();
      for (let i=0;i<items.length;i++){
        for (let j=i+1;j<items.length;j++){
          if (items[i].start <= items[j].end && items[j].start <= items[i].end){
            clash.add(i); clash.add(j);
          }
        }
      }
      items.forEach(function(c, idx){
        const p1 = D.periods[String(c.start)], p2 = D.periods[String(c.end)];
        const meta = [];
        if (c.room) meta.push(c.room);
        if (c.teacher) meta.push(c.teacher);
        meta.push("第"+c.start+"-"+c.end+"节");
        html += '<div class="item'+(clash.has(idx)?' clash':'')+'">'
             +  '<div class="time"><b>'+p1[0]+'</b>'+p2[1]+'</div>'
             +  '<div class="body"><div class="name">'+esc(c.name)
             +  (clash.has(idx)?'<span class="tag clash-tag">冲突</span>':'')
             +  '</div><div class="meta">'+esc(meta.join(" · "))+'</div></div>'
             +  '</div>';
      });
    }
    html += '</section>';
  }
  main.innerHTML = html;
  const t = document.getElementById("today");
  if (t) t.scrollIntoView({block:"center"});
}

function esc(s){ return String(s).replace(/[&<>"']/g, m=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[m])); }

document.getElementById("prev").onclick = ()=>{ week=Math.max(1,week-1); render(); };
document.getElementById("next").onclick = ()=>{ week=week+1; render(); };
render();
</script>
</body>
</html>
"""
