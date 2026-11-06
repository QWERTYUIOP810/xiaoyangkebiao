# -*- coding: utf-8 -*-
"""设置/修改课表页面的访问口令。

双击 设置口令.bat 运行；写入 gate.json 后立即重新生成页面。
"""

import getpass
import hashlib
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
GATE_FILE = os.path.join(HERE, "gate.json")

sys.stdout.reconfigure(encoding="utf-8")


def main():
    print("=" * 40)
    print(" 设置课表访问口令")
    print("=" * 40)
    print("提示：这是前端口令，能挡住随手点开的人，")
    print("      但懂技术的人仍可从源码里看到课表内容。")
    print()

    p1 = getpass.getpass("新口令：").strip()
    if not p1:
        print("口令为空，已取消")
        return 1
    p2 = getpass.getpass("再输一次：").strip()
    if p1 != p2:
        print("两次不一致，已取消")
        return 1

    h = hashlib.sha256(p1.encode("utf-8")).hexdigest()
    with open(GATE_FILE, "w", encoding="utf-8") as f:
        json.dump({"hash": h, "hint": "输入口令查看课表"}, f, ensure_ascii=False, indent=2)
    print("\n已写入 gate.json")

    print("正在重新生成页面（要登录教务系统，约 10 秒）...")
    r = subprocess.run([sys.executable, "-m", "zua_kb.main", "--out", "docs/schedule.ics"],
                       cwd=HERE, capture_output=True, text=True, encoding="utf-8")
    if r.returncode != 0:
        print(r.stdout or "")
        print(r.stderr or "")
        print("生成失败，但口令已保存，下次更新会自动生效。")
    else:
        print((r.stdout or "").strip())

    print("\n下一步：双击 run_update.bat 推送上去，或等下一次自动更新。")
    input("\n按回车退出...")


if __name__ == "__main__":
    main()
