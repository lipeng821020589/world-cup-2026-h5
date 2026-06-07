#!/usr/bin/env python3
"""
2026 世界杯倒计时
- 揭幕战: 2026-06-11 14:00 (墨西哥城, UTC-6, 北京时间 6/12 04:00)
- 决赛: 2026-07-19 15:00 (新泽西, UTC-4, 北京时间 7/20 03:00)
- 小组赛结束: 2026-06-27
- 16 强开打: 2026-06-30
"""

from datetime import datetime, timezone, timedelta

# 北京时间
BJ = timezone(timedelta(hours=8))

EVENTS = [
    ("🏆 揭幕战 (墨西哥 vs 南非)",          "2026-06-11 14:00",  "America/Mexico_City", "Estadio Azteca"),
    ("⚽ 小组赛首轮结束",                   "2026-06-12 23:59",  "UTC",                 "—"),
    ("🏁 小组赛末轮 (末班车)",              "2026-06-27 23:59",  "UTC",                 "—"),
    ("🎯 16 强开打",                       "2026-06-30 20:00",  "UTC",                 "—"),
    ("🔥 8 强开始 (Quarterfinals)",         "2026-07-04 20:00",  "UTC",                 "—"),
    ("⭐ 半决赛 #1",                       "2026-07-14 20:00",  "America/New_York",    "—"),
    ("⭐ 半决赛 #2",                       "2026-07-15 20:00",  "America/New_York",    "—"),
    ("🥉 三四名决赛",                       "2026-07-18 20:00",  "America/New_York",    "—"),
    ("🏆 决赛",                            "2026-07-19 15:00",  "America/New_York",    "MetLife Stadium"),
]

TZ_OFFSETS = {
    "UTC": 0, "Asia/Shanghai": 8, "America/Mexico_City": -6, "America/New_York": -4,
}

def parse_local(dt_str, tz_name):
    """把 'YYYY-MM-DD HH:MM' + tz_name 解析为 UTC aware datetime"""
    dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M")
    offset = TZ_OFFSETS.get(tz_name, 0)
    return dt.replace(tzinfo=timezone(timedelta(hours=offset)))

def fmt_bj(dt_utc):
    return dt_utc.astimezone(BJ).strftime("%Y-%m-%d %H:%M 北京时间")

def main():
    now = datetime.now(timezone.utc)
    print("=" * 70)
    print(f"  2026 世界杯 关键时间节点 (现在: {fmt_bj(now)})")
    print("=" * 70)
    print()
    
    for name, dt_str, tz_name, venue in EVENTS:
        target = parse_local(dt_str, tz_name)
        delta = target - now
        total_sec = int(delta.total_seconds())
        
        if total_sec < 0:
            status = "✅ 已结束"
            days = hours = mins = 0
        else:
            status = ""
            days = total_sec // 86400
            hours = (total_sec % 86400) // 3600
            mins = (total_sec % 3600) // 60
        
        bj = fmt_bj(target)
        print(f"  {name}")
        print(f"    {bj}")
        if venue != "—":
            print(f"    🏟️  {venue}")
        if status:
            print(f"    {status}")
        else:
            print(f"    ⏳ 距今: {days} 天 {hours} 小时 {mins} 分钟")
        print()


if __name__ == "__main__":
    main()
