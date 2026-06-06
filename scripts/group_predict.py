#!/usr/bin/env python3
"""
2026 世界杯 12 小组出线预测

按 power_score 给每组 4 队打分，前 2 直接出线，
预测 8 强 + 4 强 + 决赛。
"""

import json
from pathlib import Path

# 加载分组数据
data = json.loads(Path('/Work/world-cup-2026/data/teams.json').read_text())

# 各队简化的"实力分"（基于先前分析 + 当前分组）
TEAM_SCORE = {
    # T1 争冠热门
    "Argentina": 93, "France": 90, "Spain": 91, "Brazil": 82, "England": 91,
    # T2 半决赛级
    "Germany": 79, "Portugal": 80, "Netherlands": 78, "Belgium": 69,
    "USA": 72, "Mexico": 68, "Canada": 67, "Uruguay": 75,
    # T3 16 强级
    "Morocco": 76, "Japan": 70, "Norway": 69,
    "Croatia": 67, "Denmark": 64, "Switzerland": 64, "Serbia": 62,
    "Senegal": 65, "Egypt": 60, "South Korea": 62, "Nigeria": 58,
    "Poland": 58, "Sweden": 62, "Czech Republic": 56,
    "Ecuador": 62, "Colombia": 60, "Saudi Arabia": 56, "Iran": 55,
    "Ivory Coast": 58, "Tunisia": 52, "Algeria": 54, "Ghana": 52,
    "DR Congo": 50,
    # T4
    "South Africa": 48, "Bosnia and Herzegovina": 54, "Qatar": 50,
    "Paraguay": 53, "Turkey": 60, "Finland": 48,
    "Curaçao": 38, "Haiti": 36, "Cape Verde": 45, "Jordan": 42,
    "Uzbekistan": 44, "Austria": 58, "Iraq": 48, "Panama": 42,
    "New Zealand": 40,
}


def group_standings(group_letter, teams):
    """按实力分给一队排名"""
    scored = [(t, TEAM_SCORE.get(t, 40)) for t in teams]
    scored.sort(key=lambda x: -x[1])
    return scored


def main():
    print("=" * 70)
    print("  2026 世界杯 12 小组出线预测")
    print("=" * 70)
    print()
    
    qualified = {}  # 16 强候选
    for letter in 'ABCDEFGHIJKL':
        info = data['groups'][letter]
        teams = info['teams']
        seed = info['seed']
        standings = group_standings(letter, teams)
        
        print(f"📋 Group {letter}  (种子: {seed})")
        print("-" * 50)
        for i, (team, score) in enumerate(standings, 1):
            mark = "✅" if i <= 2 else "❌"
            star = " ⭐" if team in data.get('tier_1_contenders', []) else ""
            print(f"  {mark} {i}. {team:<25} 实力分: {score}{star}")
        print()
        
        qualified[letter] = [t for t, _ in standings[:2]]
    
    # 16 强对阵预测
    print("=" * 70)
    print("  预测 16 强（按 FIFA 16 强对阵规则：A1 vs B2, C1 vs D2, ...）")
    print("=" * 70)
    print()
    
    pairings = [
        ('A', 'B'), ('C', 'D'), ('E', 'F'), ('G', 'H'),
        ('I', 'J'), ('K', 'L'),
    ]
    
    for g1, g2 in pairings:
        a1 = qualified[g1][0]  # 头名
        b2 = qualified[g2][1]  # 次名
        b1 = qualified[g2][0]
        a2 = qualified[g1][1]
        print(f"  {g1}1 {a1} vs {g2}2 {b2}     |     {g1}2 {a2} vs {g2}1 {b1}")
    
    # 4 强预测
    print()
    print("=" * 70)
    print("  4 强预测（基于实力对比）")
    print("=" * 70)
    top8 = sorted([(t, TEAM_SCORE.get(t, 40)) for teams in qualified.values() for t in teams],
                  key=lambda x: -x[1])[:8]
    print()
    for i, (t, s) in enumerate(top8, 1):
        print(f"  {i}. {t} ({s})")
    
    semis = sorted([(t, TEAM_SCORE.get(t, 40)) for t, _ in top8], key=lambda x: -TEAM_SCORE.get(x, 40))[:4]
    print()
    print("  🏆 4 强：", "  /  ".join(semés := sorted(semés if 'semés' in dir() else semis, key=lambda x: -TEAM_SCORE.get(x, 40))))
    
    # 决赛 + 冠军
    print()
    final2 = sorted(semis, key=lambda x: -TEAM_SCORE.get(x, 40))[:2]
    print("  🏆 决赛：", "  vs  ".join(final2))
    print(f"  🏆 冠军预测：{final2[0]}（实力最高）")
    
    print()
    print("=" * 70)
    print("  死亡之组 / 关注点")
    print("=" * 70)
    for dg in data['death_groups']:
        g = dg['letter']
        print(f"  Group {g}: {dg['reason']}")
        print(f"           出线: {qualified[g][0]} + {qualified[g][1]}")


if __name__ == "__main__":
    main()
