#!/usr/bin/env python3
"""
2026 世界杯 12 小组出线 + 淘汰赛预测（v3 - 真实赛制）

赛制（FIFA 48 队扩军版）：
1. 12 小组，每组 4 队 → 每组前 2 + 8 个最佳第 3 → 32 强
2. 32 强 → 16 强（16 场）→ 8 强（8 场）→ 4 强（4 场）→ 决赛（1 场）
3. 决赛胜者 = 冠军

本脚本：
- 模拟小组赛（每组前 2 + 8 个最佳第 3）
- 蒙特卡洛 1000 次模拟给冠军/4 强/决赛概率
- 输出报告
"""

import json
import random
from pathlib import Path

DATA_DIR = Path('/Work/world-cup-2026/data')
REPORTS_DIR = Path('/Work/world-cup-2026/reports')

data = json.loads((DATA_DIR / 'teams.json').read_text())

# 各队实力分（满分 100）
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


def score(team):
    return TEAM_SCORE.get(team, 40)


def group_standings(teams, noise=0):
    """返回 4 队排序后的列表"""
    scored = [(t, score(t) + random.gauss(0, noise)) for t in teams]
    scored.sort(key=lambda x: -x[1])
    return [t for t, _ in scored]


def match_winner(t1, t2, noise=0):
    s1 = score(t1) + random.gauss(0, noise)
    s2 = score(t2) + random.gauss(0, noise)
    return t1 if s1 >= s2 else t2


def simulate_group_to_r32(noise=0):
    """模拟 12 小组 → 32 强（每组前 2 + 8 个最佳第 3）"""
    # 1. 各小组排名
    group_results = {}
    for letter in 'ABCDEFGHIJKL':
        info = data['groups'][letter]
        group_results[letter] = group_standings(info['teams'], noise)
    
    # 2. 12 组前 2 = 24 队
    top2 = []
    for letter in 'ABCDEFGHIJKL':
        top2.extend(group_results[letter][:2])
    
    # 3. 12 个第 3 名，按实力分排序取前 8
    third_place = [(letter, group_results[letter][2]) for letter in 'ABCDEFGHIJKL']
    third_place.sort(key=lambda x: -score(x[1]))
    best_8_third = [t for _, t in third_place[:8]]
    
    # 4. 32 强
    r32 = top2 + best_8_third
    return r32, group_results


def r32_bracket(r32):
    """
    32 强对阵（FIFA 标准）：
    - 12 组头名 + 4 个最强第 3 = 种子 (16 队)
    - 12 组次名 + 4 个最弱第 3 = 非种子 (16 队)
    简化：按我们的 r32 列表按 0v16, 1v17, ... 配对
    """
    # 简化：按 r32 顺序两两配对（实际 FIFA 有更复杂规则）
    matchups = []
    for i in range(0, 32, 2):
        matchups.append((r32[i], r32[i+1]))
    return matchups


def simulate_tournament(noise=0, return_bracket=False):
    """完整模拟：小组 → 32 强 → 16 强 → 8 强 → 4 强 → 决赛 → 冠军"""
    r32, group_results = simulate_group_to_r32(noise)
    r32_matchups = r32_bracket(r32)
    
    # 32 强 → 16 强
    r16 = [match_winner(m[0], m[1], noise) for m in r32_matchups]
    # 16 强 → 8 强
    r8 = [match_winner(r16[i], r16[i+1], noise) for i in range(0, 16, 2)]
    # 8 强 → 4 强
    r4 = [match_winner(r8[i], r8[i+1], noise) for i in range(0, 8, 2)]
    # 4 强 → 决赛
    r2 = [match_winner(r4[i], r4[i+1], noise) for i in range(0, 4, 2)]
    # 决赛 → 冠军
    champion = match_winner(r2[0], r2[1], noise)
    
    if return_bracket:
        return champion, r4, r2, r32
    return champion, r4, r2


def main():
    print("=" * 70)
    print("  2026 世界杯 小组赛 + 淘汰赛预测 (v3)")
    print("=" * 70)
    print()
    
    # ============ 1. 小组赛展示 ============
    r32, group_results = simulate_group_to_r32()
    print("📋 12 小组排名（按实力分）")
    print("=" * 70)
    for letter in 'ABCDEFGHIJKL':
        ranks = group_results[letter]
        seed = data['groups'][letter].get('seed', '?')
        print(f"  Group {letter} (种子: {seed})")
        for i, t in enumerate(ranks, 1):
            mark = "✅" if i <= 2 else ("⭐" if i == 3 else "❌")
            star = " ⭐" if t in data.get('tier_1_contenders', []) else ""
            print(f"    {mark} {i}. {t:<25} ({score(t)}){star}")
        print()
    
    print("=" * 70)
    print(f"  32 强: {len(r32)} 队（24 组前 2 + 8 最佳第 3）")
    print("=" * 70)
    
    # ============ 2. 32 强 → 冠军 (无噪) ============
    print()
    print("=" * 70)
    print("  🏆 淘汰赛逐轮（无噪 = 最可能结果）")
    print("=" * 70)
    champion, r4, r2 = simulate_tournament()
    r16_w, r8_w = simulate_tournament()[:0], None  # 重新跑只拿中间也行
    
    # 重跑一次拿完整
    r32_matchups = r32_bracket(r32)
    r16 = [match_winner(m[0], m[1]) for m in r32_matchups]
    r8 = [match_winner(r16[i], r16[i+1]) for i in range(0, 16, 2)]
    r4_disp = [match_winner(r8[i], r8[i+1]) for i in range(0, 8, 2)]
    r2_disp = [match_winner(r4_disp[i], r4_disp[i+1]) for i in range(0, 4, 2)]
    
    print(f"  16 强 ({len(r16)} 队): {'  /  '.join(r16[:8])}")
    print(f"  16 强 ({len(r16)} 队, 后 8): {'  /  '.join(r16[8:])}")
    print(f"  8 强 ({len(r8)} 队): {'  /  '.join(r8)}")
    print(f"  4 强 ({len(r4_disp)} 队): {'  /  '.join(r4_disp)}")
    print(f"  决赛: {r2_disp[0]}  vs  {r2_disp[1]}")
    print(f"  🏆 冠军: {champion}（实力 {score(champion)}）")
    print()
    
    # ============ 3. 蒙特卡洛 1000 次模拟 ============
    print("=" * 70)
    print("  🎲 蒙特卡洛 1000 次模拟（±3 实力分扰动）")
    print("=" * 70)
    N = 1000
    champ_count = {}
    final4_count = {}
    final2_count = {}
    r16_count = {}
    
    for _ in range(N):
        ch, r4_m, r2_m, r32_m = simulate_tournament(noise=3, return_bracket=True)
        # r16 推导：32 强出 16 强不易直接拿到（要再跑一次），跳过
        champ_count[ch] = champ_count.get(ch, 0) + 1
        for t in r4_m:
            final4_count[t] = final4_count.get(t, 0) + 1
        for t in r2_m:
            final2_count[t] = final2_count.get(t, 0) + 1
    
    print()
    print(f"  冠军概率 Top 8（{N} 次模拟）:")
    for t, c in sorted(champ_count.items(), key=lambda x: -x[1])[:8]:
        bar = "█" * int(c * 30 / N)
        print(f"    {t:<14} {c*100/N:5.1f}%  {bar}")
    
    print()
    print(f"  4 强概率 Top 8:")
    for t, c in sorted(final4_count.items(), key=lambda x: -x[1])[:8]:
        bar = "█" * int(c * 30 / N)
        print(f"    {t:<14} {c*100/N:5.1f}%  {bar}")
    
    print()
    print(f"  决赛概率 Top 6:")
    for t, c in sorted(final2_count.items(), key=lambda x: -x[1])[:6]:
        bar = "█" * int(c * 30 / N)
        print(f"    {t:<14} {c*100/N:5.1f}%  {bar}")
    print()
    
    # ============ 4. 死亡之组提醒 ============
    print("=" * 70)
    print("  💀 死亡之组出线预测")
    print("=" * 70)
    for dg in data['death_groups']:
        g = dg['letter']
        ranks = group_results[g]
        print(f"  Group {g}: {dg['reason']}")
        print(f"           出线: {ranks[0]} + {ranks[1]}")
    print()
    
    # ============ 5. 持久化 ============
    report_lines = [
        "=" * 70,
        f"  2026 世界杯 终极预测报告",
        f"  生成时间: 2026-06-07",
        f"  基于: 实力分 + 蒙特卡洛 {N} 次模拟（±3 实力分扰动）",
        f"  赛制: 48 队 → 32 强 → 16 → 8 → 4 → 决赛",
        "=" * 70,
        "",
        f"🏆 冠军 (最可能): {champion}",
        f"   决赛: {r2_disp[0]} vs {r2_disp[1]}",
        f"   4 强: {', '.join(r4_disp)}",
        f"   8 强: {', '.join(r8)}",
        "",
        "📊 冠军概率 Top 8:",
    ]
    for t, c in sorted(champ_count.items(), key=lambda x: -x[1])[:8]:
        report_lines.append(f"   {t}: {c*100/N:.1f}%")
    
    report_lines.append("")
    report_lines.append("📊 4 强概率 Top 8:")
    for t, c in sorted(final4_count.items(), key=lambda x: -x[1])[:8]:
        report_lines.append(f"   {t}: {c*100/N:.1f}%")
    
    out = REPORTS_DIR / 'final-prediction.txt'
    out.write_text('\n'.join(report_lines))
    print(f"💾 已保存到 {out}")


if __name__ == "__main__":
    main()
