#!/usr/bin/env python3
"""
2026 世界杯 单场胜负预测（v1）

对 72 场赛程逐场预测 1X2（主胜/平/客胜），输出：
  - 实力模型概率（基于 TEAM_SCORE 的 logistic）
  - 市场隐含概率（来自单场赔率，没有则用 baseline 推算）
  - 混合概率（0.5 实力 + 0.5 市场）
  - 凯利公式价值（under/over valued）
  - 置信度（高/中/低）

输出：
  - data/match_predictions.json  （小程序/H5 直接读）
  - reports/match-predictions.txt （人类可读报告）
"""

import json
import math
from datetime import datetime
from pathlib import Path

DATA_DIR = Path('/Work/world-cup-2026/data')
REPORTS_DIR = Path('/Work/world-cup-2026/reports')

# 复用 group_predict.py 的实力分表
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

# 中文名映射（来自 fixtures_2026.json）
TEAM_CN = {
    "Argentina": "阿根廷", "France": "法国", "Spain": "西班牙", "Brazil": "巴西",
    "England": "英格兰", "Germany": "德国", "Portugal": "葡萄牙",
    "Netherlands": "荷兰", "Belgium": "比利时", "USA": "美国", "Mexico": "墨西哥",
    "Canada": "加拿大", "Uruguay": "乌拉圭", "Morocco": "摩洛哥", "Japan": "日本",
    "Norway": "挪威", "Croatia": "克罗地亚", "Denmark": "丹麦", "Switzerland": "瑞士",
    "Serbia": "塞尔维亚", "Senegal": "塞内加尔", "Egypt": "埃及",
    "South Korea": "韩国", "Nigeria": "尼日利亚", "Poland": "波兰", "Sweden": "瑞典",
    "Czech Republic": "捷克", "Ecuador": "厄瓜多尔", "Colombia": "哥伦比亚",
    "Saudi Arabia": "沙特", "Iran": "伊朗", "Ivory Coast": "科特迪瓦",
    "Tunisia": "突尼斯", "Algeria": "阿尔及利亚", "Ghana": "加纳",
    "DR Congo": "民主刚果", "South Africa": "南非",
    "Bosnia and Herzegovina": "波黑", "Qatar": "卡塔尔", "Paraguay": "巴拉圭",
    "Turkey": "土耳其", "Finland": "芬兰", "Curaçao": "库拉索", "Haiti": "海地",
    "Cape Verde": "佛得角", "Jordan": "约旦", "Uzbekistan": "乌兹别克斯坦",
    "Austria": "奥地利", "Iraq": "伊拉克", "Panama": "巴拿马",
    "New Zealand": "新西兰", "Scotland": "苏格兰",
    "Australia": "澳大利亚",
    "Bosnia-Herzegovina": "波黑",
}

# 冠军赔率（用于"无单场赔率"时按实力反推 1X2）
CHAMPIONSHIP_ODDS = {
    "Argentina": 6.5, "France": 7.0, "Spain": 8.0, "Brazil": 9.0, "England": 7.5,
    "Germany": 12.0, "Portugal": 16.0, "Netherlands": 18.0, "Belgium": 26.0,
    "USA": 36.0, "Mexico": 41.0, "Morocco": 41.0, "Norway": 41.0, "Uruguay": 31.0,
    "Japan": 51.0, "Colombia": 51.0, "South Korea": 101.0, "Switzerland": 67.0,
    "Turkey": 67.0, "Sweden": 81.0, "Croatia": 67.0, "Denmark": 81.0,
    "Senegal": 81.0, "Egypt": 126.0, "Poland": 126.0, "Saudi Arabia": 251.0,
    "Iran": 251.0, "Ivory Coast": 126.0, "Tunisia": 251.0, "Algeria": 201.0,
    "Ghana": 201.0, "DR Congo": 251.0, "South Africa": 501.0,
    "Bosnia and Herzegovina": 201.0, "Qatar": 251.0, "Paraguay": 201.0,
    "Finland": 501.0, "Curaçao": 1001.0, "Haiti": 1001.0, "Cape Verde": 501.0,
    "Jordan": 501.0, "Uzbekistan": 501.0, "Austria": 101.0, "Iraq": 501.0,
    "Panama": 501.0, "New Zealand": 1001.0, "Scotland": 126.0,
    "Ecuador": 126.0, "Nigeria": 151.0, "Serbia": 101.0, "Czech Republic": 201.0,
}


def get_score(team):
    return TEAM_SCORE.get(team, 40)


def get_team_cn(team):
    return TEAM_CN.get(team, team)


def strength_1x2(home, away):
    """
    实力模型 → 1X2 概率
    用 logistic 把实力差映射成主胜概率，客胜对称，平局按 base 0.27 调整
    """
    s_h = get_score(home)
    s_a = get_score(away)
    diff = s_h - s_a
    # 主队 +3 分主场优势
    diff += 3
    # logistic: P(home win) = 1 / (1 + exp(-diff/15))
    p_home_raw = 1 / (1 + math.exp(-diff / 15))
    p_away_raw = 1 - p_home_raw
    # 引入平局：从两端各抽 0.27 的概率（实力越接近平局越多）
    closeness = 1 - abs(p_home_raw - p_away_raw)  # 越接近 1 → 越平
    p_draw_base = 0.18 + 0.15 * closeness  # 0.18 ~ 0.33
    # 抽完平局后归一化
    p_home = p_home_raw * (1 - p_draw_base)
    p_away = p_away_raw * (1 - p_draw_base)
    p_draw = p_draw_base
    # 归一化
    total = p_home + p_draw + p_away
    return p_home / total, p_draw / total, p_away / total


def market_1x2_from_odds(odds_1, odds_x, odds_2):
    """赔率 → 隐含概率（去除 8% 博彩公司利润后归一化）"""
    raw = [1 / odds_1, 1 / odds_x, 1 / odds_2]
    # 去 vig：除以总和再乘以 0.92
    s = sum(raw)
    norm = [r / s * 0.92 for r in raw]
    return norm[0], norm[1], norm[2]


def estimate_1x2_from_strength_odds(home, away):
    """
    没单场赔率时，用"冠军赔率隐含实力"反推 1X2（独立于 TEAM_SCORE，避免自引用）
    平局概率按隐含实力差算
    """
    o_h = CHAMPIONSHIP_ODDS.get(home, 250.0)
    o_a = CHAMPIONSHIP_ODDS.get(away, 250.0)
    # 隐含"夺冠实力比" = 1/o_h : 1/o_a
    s_h = 1 / o_h
    s_a = 1 / o_a
    # 主场加成 8%
    s_h *= 1.08
    # 归一化后取 log 差
    total = s_h + s_a
    p_h_raw = s_h / total
    p_a_raw = s_a / total
    # 平局：差距越大平局越少
    gap = abs(p_h_raw - p_a_raw)
    p_draw = 0.30 - gap * 0.20  # 0.10 ~ 0.30
    p_draw = max(0.12, p_draw)
    p_h = p_h_raw * (1 - p_draw)
    p_a = p_a_raw * (1 - p_draw)
    total = p_h + p_draw + p_a
    # 模拟对应赔率给凯利用
    odds_h = round(1 / (p_h / total * 0.92), 2)
    odds_a = round(1 / (p_a / total * 0.92), 2)
    odds_x = round(1 / (p_draw / total * 0.92), 2)
    # 不返回 odds（无意义），只返回概率；调用方会跳过凯利
    return p_h, p_draw, p_a


def kelly(prob, odds):
    """凯利公式：f* = (bp - q) / b，b=odds-1，p=prob, q=1-prob"""
    b = odds - 1
    q = 1 - prob
    f = (b * prob - q) / b
    return max(0, f)  # 负值不投注


def confidence_level(p_max):
    """最大概率 → 置信度"""
    if p_max >= 0.65:
        return "高"
    if p_max >= 0.50:
        return "中"
    return "低"


def predict_match(match, match_odds_map):
    """单场预测"""
    home = match['home']
    away = match['away']
    match_id = match['id']

    # 1) 实力模型
    p_h, p_d, p_a = strength_1x2(home, away)

    # 2) 市场赔率（按 (home, away) 查）
    market_odds = None
    key = (home, away)
    if key in match_odds_map:
        odds_obj = match_odds_map[key].get('odds', {})
        if odds_obj and odds_obj.get('1', 1) > 1.01:
            market_odds = (odds_obj['1'], odds_obj.get('X', 3.2), odds_obj['2'])

    if market_odds:
        m_h, m_d, m_a = market_1x2_from_odds(*market_odds)
        market_source = "real"
    else:
        m_h, m_d, m_a = estimate_1x2_from_strength_odds(home, away)
        market_source = "estimate"
        # 估算时给一个伪赔率（用于凯利展示）— 留空不参与凯利
        market_odds = None

    # 3) 混合
    blend_h = 0.5 * p_h + 0.5 * m_h
    blend_d = 0.5 * p_d + 0.5 * m_d
    blend_a = 0.5 * p_a + 0.5 * m_a
    # 归一化
    total = blend_h + blend_d + blend_a
    blend_h, blend_d, blend_a = blend_h/total, blend_d/total, blend_a/total

    # 4) 选最可能结果
    probs = {'1': blend_h, 'X': blend_d, '2': blend_a}
    pick = max(probs, key=probs.get)
    pick_label = {'1': f"{get_team_cn(home)} 胜", 'X': "平局", '2': f"{get_team_cn(away)} 胜"}[pick]
    pick_prob = probs[pick]
    conf = confidence_level(pick_prob)

    # 5) 凯利公式（仅在有真实赔率时计算）
    if market_odds:
        k_1 = kelly(blend_h, market_odds[0])
        k_x = kelly(blend_d, market_odds[1])
        k_2 = kelly(blend_a, market_odds[2])
    else:
        k_1 = k_x = k_2 = 0

    return {
        'match_id': match_id,
        'home': home,
        'home_cn': get_team_cn(home),
        'away': away,
        'away_cn': get_team_cn(away),
        'group': match.get('group'),
        'round': match.get('round'),
        'date_utc': match.get('date_utc'),
        'time_bj': match.get('time_bj'),
        'venue': match.get('venue'),
        'status': match.get('status', 'NS'),
        'home_score': match.get('home_score'),
        'away_score': match.get('away_score'),
        'strength': {
            'home': round(p_h, 4),
            'draw': round(p_d, 4),
            'away': round(p_a, 4),
        },
        'market': {
            'source': market_source,
            'odds_1': market_odds[0] if market_odds else None,
            'odds_x': market_odds[1] if market_odds else None,
            'odds_2': market_odds[2] if market_odds else None,
            'home': round(m_h, 4),
            'draw': round(m_d, 4),
            'away': round(m_a, 4),
        },
        'blend': {
            'home': round(blend_h, 4),
            'draw': round(blend_d, 4),
            'away': round(blend_a, 4),
        },
        'pick': pick,
        'pick_label': pick_label,
        'pick_prob': round(pick_prob, 4),
        'confidence': conf,
        'kelly': {
            'home': round(k_1, 4),
            'draw': round(k_x, 4),
            'away': round(k_2, 4),
        },
    }


def main():
    # 加载赛程
    fixtures = json.loads((DATA_DIR / 'fixtures_2026.json').read_text())
    matches = fixtures.get('matches', [])

    # 加载最新单场赔率（优先 match_odds_latest.json，否则用 history 末条）
    match_odds_map = {}  # {team_pair_tuple: {odds, source}}
    latest_path = DATA_DIR / 'match_odds_latest.json'
    if latest_path.exists():
        odds_data = json.loads(latest_path.read_text()).get('matches', {})
        for mid, m in odds_data.items():
            # 按 (home, away) 做键，方便 fixtures 查
            key = (m['team1'], m['team2'])
            match_odds_map[key] = m
    else:
        odds_path = DATA_DIR / 'match_odds.jsonl'
        if odds_path.exists():
            lines = odds_path.read_text().strip().split('\n')
            if lines:
                last = json.loads(lines[-1])
                for mid, m in last.get('matches', {}).items():
                    key = (m['team1'], m['team2'])
                    match_odds_map[key] = m

    # 过滤：跳过已完赛 (FT / AET / PEN)
    upcoming = [m for m in matches if m.get('status') not in ('FT', 'AET', 'PEN')]

    predictions = []
    for m in upcoming:
        pred = predict_match(m, match_odds_map)
        predictions.append(pred)

    # 按时间排序
    predictions.sort(key=lambda p: p.get('date_utc', ''))

    # 输出 JSON（小程序 / H5 用）
    out_json = {
        '_meta': {
            'generated_at': datetime.now().isoformat(timespec='seconds'),
            'model_version': 'v1.0',
            'algorithm': 'hybrid: 0.5*strength(TEAM_SCORE logistic) + 0.5*market(odds implied)',
            'total_matches': len(matches),
            'upcoming': len(predictions),
        },
        'matches': predictions,
    }
    out_path = DATA_DIR / 'match_predictions.json'
    out_path.write_text(json.dumps(out_json, ensure_ascii=False, indent=2))
    print(f"[ok] JSON 写入 {out_path} ({len(predictions)} 场)")

    # 输出报告（txt）
    lines = []
    lines.append("=" * 70)
    lines.append("  2026 世界杯 · 单场胜负预测报告 v1")
    lines.append(f"  生成时间: {out_json['_meta']['generated_at']}")
    lines.append(f"  待预测: {len(predictions)} 场 (总 {len(matches)} 场，{len(matches)-len(predictions)} 场已完赛)")
    lines.append("=" * 70)
    lines.append("")

    # 按 group 分组
    by_group = {}
    for p in predictions:
        g = p.get('group') or '?'
        by_group.setdefault(g, []).append(p)

    for g in sorted(by_group.keys()):
        lines.append(f"\n【{g} 组】")
        lines.append("-" * 70)
        for p in by_group[g]:
            mkt = p['market']
            bl = p['blend']
            lines.append(f"  {p['time_bj']:>13}  {p['home_cn']:>6}  vs  {p['away_cn']:<6}  |  {p['venue']}")
            if mkt['source'] == 'real' and mkt['odds_1']:
                lines.append(f"    赔率: 1={mkt['odds_1']:.2f}  X={mkt['odds_x']:.2f}  2={mkt['odds_2']:.2f}  (市场)")
            else:
                lines.append(f"    赔率: 估算 (无真实单场赔率)")
            lines.append(f"    实力: 主={p['strength']['home']*100:.1f}%  平={p['strength']['draw']*100:.1f}%  客={p['strength']['away']*100:.1f}%")
            lines.append(f"    市场: 主={mkt['home']*100:.1f}%  平={mkt['draw']*100:.1f}%  客={mkt['away']*100:.1f}%")
            lines.append(f"    混合: 主={bl['home']*100:.1f}%  平={bl['draw']*100:.1f}%  客={bl['away']*100:.1f}%")
            lines.append(f"    ➜ 推荐: {p['pick_label']}  概率={p['pick_prob']*100:.1f}%  置信={p['confidence']}")
            k = p['kelly']
            if max(k['home'], k['draw'], k['away']) > 0.001:
                lines.append(f"    凯利: 主={k['home']*100:.1f}%  平={k['draw']*100:.1f}%  客={k['away']*100:.1f}%")
            lines.append("")

    # Top 10 高置信
    lines.append("\n" + "=" * 70)
    lines.append("【Top 10 高置信推荐】")
    lines.append("-" * 70)
    top = sorted(predictions, key=lambda p: -p['pick_prob'])[:10]
    for p in top:
        lines.append(f"  {p['pick_prob']*100:5.1f}%  {p['confidence']:>3}  {p['time_bj']:>13}  {p['home_cn']} vs {p['away_cn']}  → {p['pick_label']}")

    out_txt = REPORTS_DIR / 'match-predictions.txt'
    out_txt.write_text('\n'.join(lines))
    print(f"[ok] 报告写入 {out_txt}")


if __name__ == '__main__':
    main()
