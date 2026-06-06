#!/usr/bin/env python3
"""
2026 世界杯 赔率追踪工具

功能:
1. 从多个博彩公司抓取夺冠赔率（占位 — 需付费 API key）
2. 美式/小数赔率转换
3. 凯利公式价值计算
4. 价值排序 → 找 undervalued 球队
5. 历史赔率存档
"""

import json
import time
import urllib.request
from datetime import datetime
from pathlib import Path

# ============== 赔率数据 ==============

# 基础赔率（2026-06-06 估算，从公开博彩公司平均报价）
# 字段: team, decimal_odds (欧赔), american_odds (美式)
BASE_ODDS = {
    "Argentina":     {"decimal": 6.50, "american": "+550"},
    "France":        {"decimal": 7.00, "american": "+600"},
    "Spain":         {"decimal": 8.00, "american": "+700"},
    "Brazil":        {"decimal": 9.00, "american": "+800"},
    "England":       {"decimal": 7.50, "american": "+650"},
    "Germany":       {"decimal": 12.00, "american": "+1100"},
    "Portugal":      {"decimal": 16.00, "american": "+1500"},
    "Netherlands":   {"decimal": 18.00, "american": "+1700"},
    "Belgium":       {"decimal": 26.00, "american": "+2500"},
    "USA":           {"decimal": 36.00, "american": "+3500"},
    "Mexico":        {"decimal": 41.00, "american": "+4000"},
    "Morocco":       {"decimal": 41.00, "american": "+4000"},
    "Norway":        {"decimal": 41.00, "american": "+4000"},
    "Uruguay":       {"decimal": 31.00, "american": "+3000"},
    "Japan":         {"decimal": 51.00, "american": "+5000"},
    "Colombia":      {"decimal": 51.00, "american": "+5000"},
    "South Korea":   {"decimal": 101.00, "american": "+10000"},
    "Switzerland":   {"decimal": 67.00, "american": "+6600"},
    "Turkey":        {"decimal": 67.00, "american": "+6600"},
    "Sweden":        {"decimal": 81.00, "american": "+8000"},
}

# 实力概率（来自 group_predict.py 的 TEAM_SCORE，归一化到 0-1）
TEAM_STRENGTH = {
    "Argentina": 0.93, "France": 0.90, "Spain": 0.91, "Brazil": 0.82, "England": 0.91,
    "Germany": 0.79, "Portugal": 0.80, "Netherlands": 0.78, "Belgium": 0.69,
    "USA": 0.72, "Mexico": 0.68, "Morocco": 0.76, "Norway": 0.69, "Uruguay": 0.75,
    "Japan": 0.70, "Colombia": 0.60, "South Korea": 0.62, "Switzerland": 0.64,
    "Turkey": 0.60, "Sweden": 0.62,
}


# ============== 赔率工具函数 ==============

def decimal_to_american(decimal):
    """小数赔率 → 美式赔率"""
    if decimal < 2.0:
        return int(-100 / (decimal - 1))
    else:
        return int(100 * (decimal - 1))


def american_to_decimal(american):
    """美式赔率 → 小数赔率"""
    if american > 0:
        return 1 + american / 100
    else:
        return 1 - 100 / american


def implied_probability(decimal):
    """小数赔率 → 隐含概率（含博彩公司水分）"""
    return 1 / decimal


def kelly_fraction(prob_win, decimal_odds):
    """凯利公式: f* = (bp - q) / b, b=赔率-1, p=胜率, q=1-p"""
    b = decimal_odds - 1
    q = 1 - prob_win
    f = (b * prob_win - q) / b
    return max(0, f)  # 永远不投负数


def expected_value(prob_win, decimal_odds, stake=1):
    """期望值 EV = p * (odds-1) * stake - (1-p) * stake"""
    return prob_win * (decimal_odds - 1) - (1 - prob_win)


def value_ratio(my_prob, decimal_odds):
    """价值比 = 我的概率 / 隐含概率 (>1 = 价值低估, <1 = 价值高估)"""
    implied = implied_probability(decimal_odds)
    return my_prob / implied


# ============== 抓取函数（占位） ==============

def fetch_odds_pinnacle():
    """
    从 Pinnacle 抓取赔率
    实际需要 Pinnacle API key
    占位返回 None
    """
    print("⚠️ Pinnacle API 需要 key，跳过")
    return None


def fetch_odds_the_odds_api(api_key):
    """从 the-odds-api.com 抓取
    免费层: 500 calls/月
    文档: https://the-odds-api.com/liveapi/guides/v4/
    """
    if not api_key:
        print("⚠️ 缺 API key，跳过 the-odds-api")
        return None
    
    proxy = urllib.request.ProxyHandler({
        'http': 'http://127.0.0.1:7890',
        'https': 'http://127.0.0.1:7890',
    })
    opener = urllib.request.build_opener(proxy)
    opener.addheaders = [('User-Agent', 'Mozilla/5.0')]
    
    url = (
        f'https://api.the-odds-api.com/v4/sports/soccer_fifa_world_cup/odds/'
        f'?apiKey={api_key}&regions=uk&markets=outrights&oddsFormat=decimal'
    )
    try:
        body = opener.open(url, timeout=12).read().decode('utf-8')
        return json.loads(body)
    except Exception as e:
        print(f"❌ the-odds-api: {e}")
        return None


def fetch_odds_smarkets():
    """Smarkets 博彩交易所 (相对开放)"""
    print("⚠️ Smarkets API 需认证，跳过")
    return None


# ============== 主分析 ==============

def main():
    print("=" * 70)
    print("  2026 世界杯 赔率追踪 + 价值分析")
    print("=" * 70)
    print()
    
    # 计算每队的价值
    # 先做 softmax 归一化：将实力分 (60-95) 转成合理概率
    import math
    teams_list = list(BASE_ODDS.keys())
    raw_strengths = [TEAM_STRENGTH.get(t, 60) for t in teams_list]
    # Softmax with temperature
    T = 8  # temperature，适中
    exps = [math.exp(s / T) for s in raw_strengths]
    Z = sum(exps)
    probs = [e / Z for e in exps]
    team_to_prob = dict(zip(teams_list, probs))
    
    results = []
    for team, odds in BASE_ODDS.items():
        dec = odds['decimal']
        impl = implied_probability(dec)
        my_p = team_to_prob.get(team, 0.01)
        my_p_scaled = my_p
        
        vr = value_ratio(my_p_scaled, dec)
        ev = expected_value(my_p_scaled, dec, stake=1)
        kelly = kelly_fraction(my_p_scaled, dec)
        
        results.append({
            'team': team,
            'decimal': dec,
            'american': odds['american'],
            'implied_pct': impl * 100,
            'my_prob_pct': my_p_scaled * 100,
            'value_ratio': vr,
            'ev': ev,
            'kelly': kelly,
        })
    
    # 按价值比降序
    results.sort(key=lambda x: -x['value_ratio'])
    
    print(f"{'排名':<5}{'球队':<12}{'小数赔率':<10}{'美式赔率':<10}{'隐含%':<8}{'我的%':<8}{'价值比':<8}{'EV':<8}{'凯利%':<8}")
    print("-" * 80)
    for i, r in enumerate(results, 1):
        marker = "🟢" if r['value_ratio'] > 1.0 else ("🟡" if r['value_ratio'] > 0.7 else "🔴")
        print(f"{i:<5}{r['team']:<12}{r['decimal']:<10.2f}{r['american']:<10}"
              f"{r['implied_pct']:<8.1f}{r['my_prob_pct']:<8.1f}"
              f"{marker}{r['value_ratio']:<7.2f}{r['ev']:<8.2f}{r['kelly']*100:<8.1f}")
    
    print()
    print("=" * 70)
    print("  🟢 Top 5 价值低估（值得关注的）")
    print("=" * 70)
    print("  ⚠️ 说明：这套评估只用实力分 vs 赔率算价值，")
    print("     实际还要考虑: 主力伤病、赛程、天气、博彩公司水位等")
    print("=" * 70)
    for r in results[:5]:
        print(f"  {r['team']:<12} 价值比 {r['value_ratio']:.2f}  EV={r['ev']:.2f}  凯利%={r['kelly']*100:.1f}%")
    
    print()
    print("=" * 70)
    print("  🔴 价值最差的 5 队（避免投注）")
    print("=" * 70)
    for r in results[-5:]:
        print(f"  {r['team']:<12} 价值比 {r['value_ratio']:.2f}  EV={r['ev']:.2f}")
    
    # 保存
    out = {
        'timestamp': datetime.now().isoformat(),
        'source': 'static_baseline (no real-time fetch)',
        'teams': results
    }
    Path('/Work/world-cup-2026/reports/odds-analysis.json').write_text(
        json.dumps(out, indent=2, ensure_ascii=False)
    )
    print(f"\n📁 已保存到 reports/odds-analysis.json")


if __name__ == "__main__":
    main()
