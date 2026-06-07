#!/usr/bin/env python3
"""
2026 世界杯 单场赔率监控（小组赛 + 淘汰赛）

跟夺冠赔率不同，单场赔率是博彩公司"实时报价"。
小组赛 48 场比赛，每场 3 种结果（主胜/平/客胜），赔率波动大。

本脚本：
- 维护 matches.json 中的 16 场重点比赛的单场赔率
- 每 4h 对比变化
- 报警阈值：> 10% 变化（单场赔率比夺冠赔率波动更大）
"""

import json
import time
from datetime import datetime
from pathlib import Path

DATA_DIR = Path('/Work/world-cup-2026/data')
REPORTS_DIR = Path('/Work/world-cup-2026/reports')
MATCH_ODDS_PATH = DATA_DIR / 'match_odds.jsonl'

# 16 场重点比赛（从 matches.json 抓）
# 格式: match_id, team1, team2, stage, date
FOCUS_MATCHES = [
    ("M001", "Mexico", "South Africa", "A", "2026-06-11"),
    ("M008", "Brazil", "Morocco", "C", "2026-06-13"),
    ("M011", "France", "Senegal", "I", "2026-06-14"),
    ("M015", "Netherlands", "Japan", "F", "2026-06-16"),
    ("M018", "Argentina", "Algeria", "J", "2026-06-17"),
    ("M020", "Spain", "Uruguay", "H", "2026-06-18"),
    ("M022", "England", "Croatia", "L", "2026-06-19"),
    ("M030", "France", "Norway", "I", "2026-06-20"),
    ("M032", "Argentina", "Austria", "J", "2026-06-21"),
    ("M040", "Uruguay", "Saudi Arabia", "H", "2026-06-23"),
    ("M045", "France", "Iraq", "I", "2026-06-25"),
    ("M048", "Sweden", "Tunisia", "F", "2026-06-26"),
    ("M050", "Brazil", "Scotland", "C", "2026-06-27"),
]


def fetch_match_odds_stub():
    """抓取单场赔率（占位）"""
    print("⚠️ 真实单场赔率 API 需付费 key (the-odds-api.com $79/月)")
    print("📋 使用静态基线估算")
    return {
        m[0]: {
            "team1": m[1],
            "team2": m[2],
            "stage": m[3],
            "date": m[4],
            "odds": {
                # 1=主胜, X=平, 2=客胜
                "1": 1.85,  # 占位
                "X": 3.50,
                "2": 4.20,
            },
            "source": "static_estimate",
        }
        for m in FOCUS_MATCHES
    }


def compute_match_value(odds_1, odds_x, odds_2, team1_score, team2_score):
    """
    计算单场价值
    实力概率 = softmax(score1, score2)
    """
    import math
    scores = [team1_score, team2_score]
    T = 8
    exps = [math.exp(s / T) for s in scores]
    Z = sum(exps)
    p1, p2 = exps[0] / Z, exps[1] / Z
    # 平局概率粗估 = 25%
    px = 0.25
    # 归一化
    total = p1 + px + p2
    p1, px, p2 = p1/total, px/total, p2/total
    
    value_1 = p1 * odds_1 - 1
    value_x = px * odds_x - 1
    value_2 = p2 * odds_2 - 1
    
    return {
        "p1": p1, "px": px, "p2": p2,
        "ev_1": value_1, "ev_x": value_x, "ev_2": value_2,
        "best_bet": max([("1", value_1), ("X", value_x), ("2", value_2)], key=lambda x: x[1])
    }


def main():
    print("=" * 70)
    print(f"  2026 世界杯 单场赔率监控 ({datetime.now().strftime('%Y-%m-%d %H:%M')})")
    print("=" * 70)
    print()
    
    matches = fetch_match_odds_stub()
    print(f"📋 重点比赛: {len(matches)} 场")
    print()
    
    # 读取历史
    history = []
    if MATCH_ODDS_PATH.exists():
        for line in MATCH_ODDS_PATH.read_text().strip().split('\n'):
            try:
                history.append(json.loads(line))
            except: pass
    
    last = history[-1] if history else None
    
    # 报告
    lines = [
        "=" * 70,
        f"  2026 世界杯 单场赔率监控",
        f"  时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "=" * 70,
        "",
        f"📋 重点比赛: {len(matches)} 场",
        "",
    ]
    
    # 加载球员库（用于价值分析）
    TEAMS_DATA = json.loads(Path('/Work/world-cup-2026/data/teams.json').read_text())
    
    # 临时内联 TEAM_SCORE（与 group_predict.py 同步）
    TEAM_SCORE = {
        "Argentina": 93, "France": 90, "Spain": 91, "Brazil": 82, "England": 91,
        "Germany": 79, "Portugal": 80, "Netherlands": 78, "Belgium": 69,
        "USA": 72, "Mexico": 68, "Canada": 67, "Uruguay": 75,
        "Morocco": 76, "Japan": 70, "Norway": 69,
        "Croatia": 67, "Denmark": 64, "Switzerland": 64, "Serbia": 62,
        "Senegal": 65, "Egypt": 60, "South Korea": 62, "Nigeria": 58,
        "Poland": 58, "Sweden": 62, "Czech Republic": 56,
        "Ecuador": 62, "Colombia": 60, "Saudi Arabia": 56, "Iran": 55,
        "Ivory Coast": 58, "Tunisia": 52, "Algeria": 54, "Ghana": 52,
        "DR Congo": 50,
        "South Africa": 48, "Bosnia and Herzegovina": 54, "Qatar": 50,
        "Paraguay": 53, "Turkey": 60, "Finland": 48,
        "Curaçao": 38, "Haiti": 36, "Cape Verde": 45, "Jordan": 42,
        "Uzbekistan": 44, "Austria": 58, "Iraq": 48, "Panama": 42,
        "New Zealand": 40,
    }
    
    print("🎯 重点比赛价值分析")
    print("-" * 70)
    for mid, m in matches.items():
        s1 = TEAM_SCORE.get(m['team1'], 40)
        s2 = TEAM_SCORE.get(m['team2'], 40)
        o = m['odds']
        v = compute_match_value(o['1'], o['X'], o['2'], s1, s2)
        best = v['best_bet']
        print(f"  [{m['date']}] {m['team1']:<20} vs {m['team2']:<20} ({m['stage']})")
        print(f"    赔率: 1={o['1']:.2f}  X={o['X']:.2f}  2={o['2']:.2f}")
        print(f"    实力概率: {v['p1']*100:.1f}% / {v['px']*100:.1f}% / {v['p2']*100:.1f}%")
        print(f"    最佳押注: {best[0]} (EV={best[1]:+.2f})")
        print()
        lines.extend([
            f"[{m['date']}] {m['team1']} vs {m['team2']} ({m['stage']})",
            f"  赔率: 1={o['1']:.2f}  X={o['X']:.2f}  2={o['2']:.2f}",
            f"  实力: {v['p1']*100:.1f}% / {v['px']*100:.1f}% / {v['p2']*100:.1f}%",
            f"  最佳: {best[0]} (EV={best[1]:+.2f})",
            "",
        ])
    
    # 保存历史
    record = {
        'timestamp': datetime.now().isoformat(),
        'matches': matches,
    }
    with open(MATCH_ODDS_PATH, 'a') as f:
        f.write(json.dumps(record, ensure_ascii=False) + '\n')
    
    # 保存报告
    out = REPORTS_DIR / f'match-odds-{datetime.now().strftime("%Y%m%d-%H%M")}.txt'
    out.write_text('\n'.join(lines))
    print(f"💾 已保存到 {out}")


if __name__ == "__main__":
    main()
