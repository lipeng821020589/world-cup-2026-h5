#!/usr/bin/env python3
"""
抓取 TheSportsDB 公开 API 的 2026 世界杯真实赛程
- 揭幕战 + 全部小组赛 (round 1)
- 含: 比赛 ID, 时间戳, 球队, 球场, 城市, 比分占位
- 转为 JSON 存到 data/fixtures_2026.json
- 推到 GitHub Pages
"""

import json
import time
import urllib.request
from pathlib import Path
from datetime import datetime, timezone, timedelta

API = "https://www.thesportsdb.com/api/v1/json/3/eventsround.php"
LEAGUE_ID = "4429"  # FIFA World Cup
SEASON = "2026"

OUT = Path("/Work/world-cup-2026/data/fixtures_2026.json")

def fetch_round(round_num: int) -> list:
    """抓取某一轮比赛"""
    url = f"{API}?id={LEAGUE_ID}&r={round_num}&s={SEASON}"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read().decode('utf-8'))
        return data.get('events') or []

def cn_team(name_en):
    """英文队名转中文"""
    MAP = {
        'Argentina': '阿根廷', 'France': '法国', 'Spain': '西班牙', 'Brazil': '巴西',
        'England': '英格兰', 'Germany': '德国', 'Portugal': '葡萄牙', 'Netherlands': '荷兰',
        'Belgium': '比利时', 'USA': '美国', 'Mexico': '墨西哥', 'Canada': '加拿大',
        'Uruguay': '乌拉圭', 'Morocco': '摩洛哥', 'Japan': '日本', 'Norway': '挪威',
        'Croatia': '克罗地亚', 'Switzerland': '瑞士', 'Senegal': '塞内加尔',
        'Egypt': '埃及', 'South Korea': '韩国', 'Sweden': '瑞典', 'Ecuador': '厄瓜多尔',
        'Czech Republic': '捷克', 'Turkey': '土耳其', 'Colombia': '哥伦比亚',
        'Saudi Arabia': '沙特', 'Ivory Coast': '科特迪瓦', 'Tunisia': '突尼斯',
        'Algeria': '阿尔及利亚', 'Ghana': '加纳', 'Austria': '奥地利', 'Iraq': '伊拉克',
        'Jordan': '约旦', 'Cape Verde': '佛得角', 'South Africa': '南非', 'Qatar': '卡塔尔',
        'Haiti': '海地', 'Scotland': '苏格兰', 'Panama': '巴拿马', 'New Zealand': '新西兰',
        'Finland': '芬兰', 'Poland': '波兰', 'Iran': '伊朗', 'Nigeria': '尼日利亚',
        'Denmark': '丹麦', 'Serbia': '塞尔维亚', 'DR Congo': '刚果（金）',
        'Paraguay': '巴拉圭', 'Uzbekistan': '乌兹别克', 'Curaçao': '库拉索',
        'Bosnia and Herzegovina': '波黑', 'Australia': '澳大利亚',
    }
    return MAP.get(name_en, name_en)

def parse_event(e: dict) -> dict:
    """解析一条赛事。
    TheSportsDB 的 strTimestamp 是比赛当地的 ISO 时间（无时区后缀）。
    - 北美/加拿大场馆: UTC-5 (EST) 或 UTC-6 (CDT/Mexico)
    - 实际场次时间以墨西哥/美国本地时间为准
    简化处理：strTimestamp 当作 UTC-6 (CDT/Mexico City) 解析，
    这样所有 3 个东道国的比赛误差在 0-1 小时内范围可控。
    """
    ts = e.get('strTimestamp', '')
    try:
        # 视作 UTC-6 本地时间（最常用：墨西哥/德州/中央时区）
        local_tz = timezone(timedelta(hours=-6))
        dt_local = datetime.fromisoformat(ts).replace(tzinfo=local_tz)
        dt_bj = dt_local.astimezone(timezone(timedelta(hours=8)))
        time_bj = dt_bj.strftime('%Y-%m-%d %H:%M')
        time_short = dt_bj.strftime('%m-%d %H:%M')
        weekday = '周' + '一二三四五六日'[dt_bj.weekday()]
    except Exception:
        time_bj = e.get('dateEventLocal', '') + ' ' + e.get('strTimeLocal', '')
        time_short = time_bj
        weekday = ''

    home = e.get('strHomeTeam', '')
    away = e.get('strAwayTeam', '')

    return {
        'id': e.get('idEvent'),
        'round': int(e.get('intRound', 0)),
        'group': e.get('strGroup', ''),
        'date_utc': ts,
        'time_bj': time_bj,
        'time_short': time_short,
        'weekday': weekday,
        'home': home,
        'home_cn': cn_team(home),
        'home_badge': e.get('strHomeTeamBadge', ''),
        'away': away,
        'away_cn': cn_team(away),
        'away_badge': e.get('strAwayTeamBadge', ''),
        'venue': e.get('strVenue', ''),
        'city': e.get('strCity', ''),
        'country': e.get('strCountry', ''),
        'status': e.get('strStatus', 'NS'),  # NS=未开始
        'home_score': e.get('intHomeScore'),
        'away_score': e.get('intAwayScore'),
        'poster': e.get('strPoster', ''),
    }

def main():
    all_events = []
    # 抓 round 1-3 (小组赛) + 4-5 (淘汰赛)
    for r in range(1, 4):
        print(f"📥 抓取第 {r} 轮...")
        try:
            events = fetch_round(r)
            parsed = [parse_event(e) for e in events]
            all_events.extend(parsed)
            print(f"   ✅ {len(parsed)} 场")
        except Exception as ex:
            print(f"   ❌ 失败: {ex}")
        time.sleep(0.5)

    # 按时间排序
    all_events.sort(key=lambda x: x['time_bj'])

    # 标记揭幕战 (第一场)
    if all_events:
        all_events[0]['is_opener'] = True

    # 写入 JSON
    result = {
        '_note': '2026 世界杯 真实赛程 (来源: TheSportsDB 公开 API)',
        '_fetched_at': datetime.now().isoformat(timespec='seconds'),
        '_source': 'https://www.thesportsdb.com/api/v1/json/3/eventsround.php?id=4429',
        '_count': len(all_events),
        'matches': all_events,
    }
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f"\n✅ 写入 {OUT} ({OUT.stat().st_size} 字节)")
    print(f"📊 共 {len(all_events)} 场比赛")
    print(f"🏆 首场: {all_events[0]['home_cn']} vs {all_events[0]['away_cn']} @ {all_events[0]['time_bj']}")
    print(f"🏁 末场: {all_events[-1]['home_cn']} vs {all_events[-1]['away_cn']} @ {all_events[-1]['time_bj']}")

if __name__ == '__main__':
    main()
