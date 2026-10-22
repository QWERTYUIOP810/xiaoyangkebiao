# -*- coding: utf-8 -*-
"""郑州航空工业管理学院 作息时间（教务处 2024-09-13 公布）。

来源: https://jwc.zua.edu.cn/info/1185/5689.htm
"""

PERIODS = {
    1: ("08:00", "08:45"),
    2: ("08:55", "09:40"),
    3: ("10:00", "10:45"),
    4: ("10:55", "11:40"),
    5: ("14:30", "15:15"),
    6: ("15:25", "16:10"),
    7: ("16:30", "17:15"),
    8: ("17:25", "18:10"),
    9: ("19:30", "20:15"),
    10: ("20:25", "21:10"),
}

WEEKDAY_CN = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]


def slot_range(slots):
    """把节次集合合并成连续区间 [(start, end), ...]。"""
    out = []
    for s in sorted(slots):
        if out and s == out[-1][1] + 1:
            out[-1] = (out[-1][0], s)
        else:
            out.append((s, s))
    return out


def start_time(slot):
    return PERIODS[slot][0]


def end_time(slot):
    return PERIODS[slot][1]
