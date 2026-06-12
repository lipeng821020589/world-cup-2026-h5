#!/usr/bin/env python3
"""
2026 世界杯 单场赔率监控 + 真实赔率抓取 (v2)

数据源优先级：
  1. The Odds API (需 ODDS_API_KEY 环境变量，免费 500 req/月)
  2. Chrome headless 抓 oddsportal / flashscore 公开页
  3. 实力分估算（兜底，source: strength_estimate）

输出：
  - data/match_odds.jsonl        (历史快照，追加)
  - data/match_odds_latest.json  (最新一份，供 match_predict.py 读)
  - reports/match-odds-*.txt     (人类可读报告)
"""

import json
import os
import re
import time
import urllib.request
import urllib.error
from datetime import datetime
from pathlib import Path
import math

# 加载 .env (from ~/.openclaw/workspace/.env)
ENV_PATH = Path('/home/peng/.openclaw/workspace/.env')
if ENV_PATH.exists():
    for line in ENV_PATH.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        if '=' in line:
            k, v = line.split('=', 1)
            os.environ.setdefault(k.strip(), v.strip())

DATA_DIR = Path('/Work/world-cup-2026/data')
REPORTS_DIR = Path('/Work/world-cup-2026/reports')
MATCH_ODDS_PATH = DATA_DIR / 'match_odds.jsonl'
MATCH_ODDS_LATEST = DATA_DIR / 'match_odds_latest.json'

# 16 场重点比赛（与 v1 一致，扩展到 70 场可选）
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

# 实力分表（与 match_predict.py / group_predict.py 同步）
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
    "DR Congo": 50, "South Africa": 48, "Bosnia and Herzegovina": 54,
    "Bosnia-Herzegovina": 54, "Qatar": 50, "Paraguay": 53, "Turkey": 60,
    "Finland": 48, "Curaçao": 38, "Haiti": 36, "Cape Verde": 45,
    "Jordan": 42, "Uzbekistan": 44, "Austria": 58, "Iraq": 48,
    "Panama": 42, "New Zealand": 40, "Australia": 56, "Scotland": 40,
}

# 冠军赔率基线（用于无真实赔率时反推单场赔率）
CHAMPIONSHIP_ODDS = {
    "Argentina": 6.5, "France": 7.0, "Spain": 8.0, "Brazil": 9.0, "England": 7.5,
    "Germany": 12.0, "Portugal": 16.0, "Netherlands": 18.0, "Belgium": 26.0,
    "USA": 36.0, "Mexico": 41.0, "Morocco": 41.0, "Norway": 41.0, "Uruguay": 31.0,
    "Japan": 51.0, "Colombia": 51.0, "South Korea": 101.0, "Switzerland": 67.0,
    "Turkey": 67.0, "Sweden": 81.0, "Croatia": 67.0, "Denmark": 81.0,
    "Senegal": 81.0, "Egypt": 126.0, "Poland": 126.0, "Saudi Arabia": 251.0,
    "Iran": 251.0, "Ivory Coast": 126.0, "Tunisia": 251.0, "Algeria": 201.0,
    "Ghana": 201.0, "DR Congo": 251.0, "South Africa": 501.0,
    "Bosnia and Herzegovina": 201.0, "Bosnia-Herzegovina": 201.0, "Qatar": 251.0,
    "Paraguay": 201.0, "Finland": 501.0, "Curaçao": 1001.0, "Haiti": 1001.0,
    "Cape Verde": 501.0, "Jordan": 501.0, "Uzbekistan": 501.0, "Austria": 101.0,
    "Iraq": 501.0, "Panama": 501.0, "New Zealand": 1001.0, "Scotland": 126.0,
    "Australia": 81.0, "Ecuador": 126.0, "Nigeria": 151.0, "Serbia": 101.0,
    "Czech Republic": 201.0,
}


# ============ 数据源 1: The Odds API ============

def fetch_from_odds_api():
    """
    The Odds API (the-odds-api.com)
    免费层 500 req/月，需要 ODDS_API_KEY 环境变量
    """
    api_key = os.environ.get('ODDS_API_KEY')
    if not api_key:
        return None, "ODDS_API_KEY 未设置"

    # 2026 世界杯 sport key: soccer_fifa_world_cup
    url = (
        "https://api.the-odds-api.com/v4/sports/soccer_fifa_world_cup/odds/"
        "?apiKey={key}&regions=uk,eu&markets=h2h&oddsFormat=decimal&dateFormat=iso"
    ).format(key=api_key)

    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'world-cup-2026-bot/1.0'})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode('utf-8'))
        return data, None
    except (urllib.error.HTTPError, urllib.error.URLError) as e:
        return None, f"HTTP 错误: {e}"
    except Exception as e:
        return None, f"异常: {e}"


def normalize_odds_api(events, focus_matches):
    """
    把 The Odds API 返回的 events 转成我们的格式
    匹配规则：主客队名双向包含
    返回: {(home, away): {odds, source, ...}} 供 match_predict.py 用

    Bookmaker 优先级: pinnacle > bet365 > williamhill > 平均
    """
    PRIORITY = ['pinnacle', 'bet365', 'williamhill', 'betfair', 'ladbrokes', 'unibet']

    def pick_bookmaker(bookmakers):
        """按优先级选一家"""
        for key in PRIORITY:
            for bk in bookmakers:
                if bk.get('key') == key:
                    markets = bk.get('markets', [])
                    if any(m.get('key') == 'h2h' for m in markets):
                        return bk
        # fallback: 第一家
        for bk in bookmakers:
            markets = bk.get('markets', [])
            if any(m.get('key') == 'h2h' for m in markets):
                return bk
        return None

    out = {}
    for ev in events or []:
        home = ev.get('home_team', '')
        away = ev.get('away_team', '')
        if not home or not away:
            continue

        bookmakers = ev.get('bookmakers', [])
        if not bookmakers:
            continue
        chosen_bk = pick_bookmaker(bookmakers)
        if not chosen_bk:
            continue
        h2h = next(m for m in chosen_bk['markets'] if m.get('key') == 'h2h')
        outcomes = h2h.get('outcomes', [])

        odds = {}
        for o in outcomes:
            n = o.get('name', '')
            p = o.get('price', 0)
            if n == 'Draw':
                odds['X'] = p
            elif n == home:
                odds['1'] = p
            elif n == away:
                odds['2'] = p
        if '1' not in odds or '2' not in odds or 'X' not in odds:
            continue
        # 过滤异常：X 赔率超过 12.0 或 主队 < 1.01 都不取
        if odds['X'] > 12.0 or odds['1'] < 1.01 or odds['2'] < 1.01:
            continue

        out[(home, away)] = {
            'team1': home, 'team2': away,
            'odds': odds, 'source': f'the_odds_api:{chosen_bk.get("key", "?")}',
            'commence': ev.get('commence_time'),
        }
    return out


# ============ 数据源 2: Chrome headless 抓公开页 ============

def fetch_via_chrome():
    """
    用 Chrome headless 打开赔率聚合站，提取赔率
    注意：聚合站频繁改路径/反爬，本函数作为占位实现
    """
    # 实际抓取时使用：
    # google-chrome --headless --disable-gpu --no-sandbox \
    #   --dump-dom 'https://www.oddsportal.com/football/world/world-cup-2026/' \
    #   > /tmp/odds.html
    # 然后 HTML 解析出 match_id -> {1, X, 2} 赔率
    return None, "Chrome 抓取需要目标 URL 配置（见 SKILL.md）"


# ============ 数据源 3: 实力分估算（兜底）============

def estimate_odds(team1, team2):
    """
    用冠军赔率反推 + 实力分调整 → 估算合理 1X2
    """
    s1 = TEAM_SCORE.get(team1, 50)
    s2 = TEAM_SCORE.get(team2, 50)
    # 主场 +3
    diff = s1 - s2 + 3
    # logistic 系数 20：差距 30 → p1≈80%, 差距 60 → p1≈95%
    p1_raw = 1 / (1 + math.exp(-diff / 20))
    p2_raw = 1 - p1_raw
    # 平局：实力越接近平局越多，差距大时少（最低 0.20）
    closeness = 1 - abs(p1_raw - p2_raw)
    p_x = 0.20 + 0.10 * closeness  # 0.20 ~ 0.30
    # 抽完平局归一化
    p1 = p1_raw * (1 - p_x)
    p2 = p2_raw * (1 - p_x)
    total = p1 + p_x + p2
    p1, p_x, p2 = p1/total, p_x/total, p2/total
    # 反推赔率（含 8% 博彩利润）+ 赔率上限 15.0（避免过山车）
    vig = 0.92
    def safe_odds(p):
        if p < 0.01:
            return 15.0
        return round(min(15.0, 1 / (p * vig)), 2)
    odds = {
        '1': safe_odds(p1),
        'X': safe_odds(p_x),
        '2': safe_odds(p2),
    }
    return odds


def fetch_with_fallback(focus_matches):
    """
    多源 fallback：API → Chrome → 估算
    返回: {(home, away): {team1, team2, odds, source, ...}}
    """
    # 1. The Odds API
    api_data, api_err = fetch_from_odds_api()
    if api_data:
        result = normalize_odds_api(api_data, focus_matches)
        if result:
            print(f"✅ The Odds API: {len(result)} 场真实赔率")
            return result, "the_odds_api", api_err
    print(f"⚠️  The Odds API: {api_err}")

    # 2. Chrome headless
    ch_data, ch_err = fetch_via_chrome()
    if ch_data:
        print(f"✅ Chrome 抓取: {len(ch_data)} 场")
        return ch_data, "chrome_scrape", ch_err
    print(f"⚠️  Chrome 抓取: {ch_err}")

    # 3. 估算（只覆盖 focus_matches）
    print("📐 使用实力分估算（兜底）")
    result = {}
    for mid, t1, t2, stage, date in focus_matches:
        result[(t1, t2)] = {
            'team1': t1, 'team2': t2, 'stage': stage, 'date': date,
            'odds': estimate_odds(t1, t2),
            'source': 'strength_estimate',
        }
    return result, "strength_estimate", None


# ============ 价值分析（凯利公式）============

def compute_match_value(odds_1, odds_x, odds_2, team1, team2):
    """单场价值 = 实力概率 × 赔率 - 1"""
    s1 = TEAM_SCORE.get(team1, 50)
    s2 = TEAM_SCORE.get(team2, 50)
    diff = s1 - s2 + 3
    p1_raw = 1 / (1 + math.exp(-diff / 12))
    p2_raw = 1 - p1_raw
    p_x = 0.25
    p1 = p1_raw * (1 - p_x)
    p2 = p2_raw * (1 - p_x)
    total = p1 + p_x + p2
    p1, p_x, p2 = p1/total, p_x/total, p2/total

    ev_1 = p1 * odds_1 - 1
    ev_x = p_x * odds_x - 1
    ev_2 = p2 * odds_2 - 1

    # 凯利
    def kelly(p, o):
        b = o - 1
        q = 1 - p
        f = (b * p - q) / b
        return max(0, round(f * 100, 1))

    return {
        'p1': round(p1 * 100, 1), 'px': round(p_x * 100, 1), 'p2': round(p2 * 100, 1),
        'ev_1': round(ev_1, 3), 'ev_x': round(ev_x, 3), 'ev_2': round(ev_2, 3),
        'kelly_1': kelly(p1, odds_1), 'kelly_x': kelly(p_x, odds_x), 'kelly_2': kelly(p2, odds_2),
        'best': max([('1', ev_1), ('X', ev_x), ('2', ev_2)], key=lambda x: x[1]),
    }


# ============ Main ============

def main():
    print("=" * 70)
    print(f"  2026 世界杯 单场赔率监控 v2 ({datetime.now().strftime('%Y-%m-%d %H:%M')})")
    print("=" * 70)
    print()

    matches, source, err = fetch_with_fallback(FOCUS_MATCHES)
    print(f"\n📋 抓取结果: {len(matches)} 场 (来源: {source})\n")

    # 匹配 fixtures 拿 stage/date 上下文
    fixtures_path = DATA_DIR / 'fixtures_2026.json'
    fixtures_by_pair = {}
    if fixtures_path.exists():
        fx = json.loads(fixtures_path.read_text())
        for m in fx.get('matches', []):
            if m.get('status') in ('FT', 'AET', 'PEN'):
                continue
            fixtures_by_pair[(m['home'], m['away'])] = m
    # 补充 focus meta
    for mid, t1, t2, stage, date in FOCUS_MATCHES:
        if (t1, t2) not in fixtures_by_pair:
            fixtures_by_pair[(t1, t2)] = {'group': stage, 'time_bj': date, 'venue': ''}

    # 加载历史
    history = []
    if MATCH_ODDS_PATH.exists():
        for line in MATCH_ODDS_PATH.read_text().strip().split('\n'):
            try:
                history.append(json.loads(line))
            except Exception:
                pass
    last = history[-1] if history else None

    # 报告
    lines = [
        "=" * 70,
        f"  2026 世界杯 单场赔率监控 v2",
        f"  时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"  来源: {source}" + (f" (err: {err})" if err else ""),
        "=" * 70,
        "",
        f"📋 重点比赛: {len(matches)} 场",
        "",
    ]

    print("🎯 价值分析 (Top 价值优先)")
    print("-" * 70)

    # 全部计算后按 EV 排序，只打 Top
    enriched = []
    for key, m in matches.items():
        odds = m['odds']
        v = compute_match_value(odds['1'], odds['X'], odds['2'], m['team1'], m['team2'])
        meta = fixtures_by_pair.get(key, {})
        prev_odds = None
        if last:
            for prev_key, prev_m in last.get('matches', {}).items():
                if prev_m.get('team1') == m['team1'] and prev_m.get('team2') == m['team2']:
                    prev_odds = prev_m.get('odds')
                    break
        change_str = ""
        if prev_odds:
            d1 = odds['1'] - prev_odds.get('1', odds['1'])
            change_str = f"  Δ1={d1:+.2f}"
        enriched.append({
            'key': key, 'm': m, 'meta': meta,
            'odds': odds, 'v': v, 'change_str': change_str,
        })

    # 按最佳 EV 降序
    enriched.sort(key=lambda x: -x['v']['best'][1])
    for e in enriched[:30]:  # 只列 Top 30
        m, odds, v, meta = e['m'], e['odds'], e['v'], e['meta']
        time_str = meta.get('time_bj', '') or meta.get('date', '')
        group = meta.get('group', '')
        best = v['best']
        print(f"  [{time_str}] {m['team1']:<20} vs {m['team2']:<20} ({group}){e['change_str']}")
        print(f"    赔率: 1={odds['1']:.2f}  X={odds['X']:.2f}  2={odds['2']:.2f}  [{m.get('source', source)}]")
        print(f"    实力: {v['p1']}% / {v['px']}% / {v['p2']}%")
        print(f"    凯利: {v['kelly_1']}% / {v['kelly_x']}% / {v['kelly_2']}%")
        print(f"    最佳: {best[0]} (EV={best[1]:+.3f})")
        print()

        lines.extend([
            f"[{time_str}] {m['team1']} vs {m['team2']} ({group}){e['change_str']}",
            f"  赔率: 1={odds['1']:.2f}  X={odds['X']:.2f}  2={odds['2']:.2f}  [{m.get('source', source)}]",
            f"  实力: {v['p1']}% / {v['px']}% / {v['p2']}%",
            f"  凯利: {v['kelly_1']}% / {v['kelly_x']}% / {v['kelly_2']}%",
            f"  最佳: {best[0]} (EV={best[1]:+.3f})",
            "",
        ])

    # 保存 jsonl 历史（key 转字符串，jsonl 不支持 tuple key）
    matches_serializable = {f"{k[0]}|{k[1]}": v for k, v in matches.items()}
    record = {
        'timestamp': datetime.now().isoformat(timespec='seconds'),
        'source': source,
        'matches': matches_serializable,
    }
    with open(MATCH_ODDS_PATH, 'a') as f:
        f.write(json.dumps(record, ensure_ascii=False) + '\n')
    print(f"💾 历史 → {MATCH_ODDS_PATH}")

    # 保存 latest
    MATCH_ODDS_LATEST.write_text(json.dumps(record, ensure_ascii=False, indent=2))
    print(f"💾 最新 → {MATCH_ODDS_LATEST}")

    # 报告
    out = REPORTS_DIR / f'match-odds-{datetime.now().strftime("%Y%m%d-%H%M")}.txt'
    out.write_text('\n'.join(lines))
    print(f"💾 报告 → {out}")


if __name__ == '__main__':
    main()
