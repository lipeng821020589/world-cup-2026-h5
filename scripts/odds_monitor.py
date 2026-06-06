#!/usr/bin/env python3
"""
2026 世界杯 赔率监控 (Odds Monitor)

工作流:
1. 抓取当前赔率（多个博彩公司）— 优先 the-odds-api，回退静态
2. 与上次基线对比，计算变化 % 和方向
3. 写入历史 JSONL
4. 输出 + 报警 (变化 > 5%)

调用方式:
  python3 odds_monitor.py             # 正常抓 + 比较
  python3 odds_monitor.py --update    # 强制更新基线 (手动填入新赔率)
  python3 odds_monitor.py --api-key xxx  # 用真实 API key
"""

import json
import time
import argparse
import urllib.request
from datetime import datetime
from pathlib import Path
import math

DATA_DIR = Path('/Work/world-cup-2026/data')
HISTORY_PATH = DATA_DIR / 'odds_history.jsonl'
BASELINE_PATH = DATA_DIR / 'odds_baseline.json'
REPORTS_DIR = Path('/Work/world-cup-2026/reports')

# ============== 抓取 ==============

def fetch_via_odds_api(api_key, proxy_url='http://127.0.0.1:7890'):
    """通过 the-odds-api.com 抓取 (需 key)"""
    if not api_key:
        return None
    
    proxy = urllib.request.ProxyHandler({
        'http': proxy_url, 'https': proxy_url
    })
    opener = urllib.request.build_opener(proxy)
    opener.addheaders = [('User-Agent', 'Mozilla/5.0')]
    
    url = (
        f'https://api.the-odds-api.com/v4/sports/soccer_fifa_world_cup/odds/'
        f'?apiKey={api_key}&regions=uk&markets=outrights&oddsFormat=decimal'
    )
    try:
        body = opener.open(url, timeout=15).read().decode('utf-8')
        return json.loads(body)
    except Exception as e:
        print(f"❌ the-odds-api: {e}")
        return None


def fetch_manual_baseline():
    """从基线文件读取（手动维护的赔率）"""
    if not BASELINE_PATH.exists():
        return None
    data = json.loads(BASELINE_PATH.read_text())
    # 过滤掉元数据字段（以 _ 开头的）
    return {k: v for k, v in data.items() if not k.startswith('_') and isinstance(v, (int, float))}


# ============== 计算 ==============

def compute_changes(current, previous):
    """
    计算赔率变化
    current: {team: decimal_odds}
    previous: {team: decimal_odds}
    returns: [(team, current, previous, change_pct, direction)]
    """
    changes = []
    for team, dec_now in current.items():
        if team not in previous:
            continue
        dec_prev = previous[team]
        if dec_prev <= 1.0:
            continue
        change_pct = (dec_now - dec_prev) / dec_prev * 100
        direction = "↑" if change_pct > 0.5 else ("↓" if change_pct < -0.5 else "→")
        changes.append({
            'team': team,
            'current': dec_now,
            'previous': dec_prev,
            'change_pct': change_pct,
            'direction': direction,
        })
    changes.sort(key=lambda x: abs(x['change_pct']), reverse=True)
    return changes


def detect_significant_moves(changes, threshold=5.0):
    """检测 > 5% 变化"""
    return [c for c in changes if abs(c['change_pct']) >= threshold]


# ============== 主流程 ==============

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--api-key', default=None, help='the-odds-api.com key')
    parser.add_argument('--threshold', type=float, default=5.0, help='报警阈值 %')
    parser.add_argument('--update', action='store_true', help='强制更新基线')
    args = parser.parse_args()
    
    print("=" * 70)
    print(f"  2026 世界杯 赔率监控  ({datetime.now().strftime('%Y-%m-%d %H:%M')})")
    print("=" * 70)
    print()
    
    # 1. 抓当前赔率
    current_odds = None
    source = None
    
    if args.api_key:
        print("🔍 尝试 the-odds-api...")
        api_data = fetch_via_odds_api(args.api_key)
        if api_data:
            # 解析 API 返回
            current_odds = parse_api_data(api_data)
            source = 'the-odds-api'
    
    if current_odds is None:
        print("📋 使用基线赔率 (静态)")
        baseline = fetch_manual_baseline()
        if baseline is None:
            print("❌ 没有基线数据，请先创建 data/odds_baseline.json")
            return
        current_odds = baseline
        source = 'baseline'
    
    print(f"✅ 获取 {len(current_odds)} 队赔率 (源: {source})")
    print()
    
    # 2. 读取历史最后一条
    previous_odds = None
    if HISTORY_PATH.exists():
        lines = HISTORY_PATH.read_text().strip().split('\n')
        if lines:
            try:
                last = json.loads(lines[-1])
                previous_odds = last.get('odds', {})
            except: pass
    
    # 3. 计算变化
    if previous_odds:
        changes = compute_changes(current_odds, previous_odds)
        significant = detect_significant_moves(changes, args.threshold)
        
        print(f"📊 赔率变化 (vs 上次, 阈值 {args.threshold}%)")
        print("-" * 70)
        for c in changes[:10]:
            emoji = "🔴" if c['change_pct'] < -args.threshold else ("🟢" if c['change_pct'] > args.threshold else "⚪")
            print(f"  {emoji} {c['team']:<15} {c['previous']:>6.2f} → {c['current']:>6.2f}  "
                  f"{c['direction']} {c['change_pct']:+6.1f}%")
        print()
        
        if significant:
            print(f"🚨 重大变化 (>{args.threshold}%): {len(significant)} 队")
            for c in significant:
                print(f"   {c['team']}: {c['change_pct']:+.1f}%")
        else:
            print(f"✅ 无重大变化（阈值 {args.threshold}%）")
    else:
        print("📝 首次运行，无历史基线对比")
        changes = []
        significant = []
    
    print()
    
    # 4. 保存到历史
    record = {
        'timestamp': datetime.now().isoformat(),
        'source': source,
        'odds': current_odds,
        'changes_from_prev': [c for c in changes if abs(c['change_pct']) > 0.1],
    }
    with open(HISTORY_PATH, 'a') as f:
        f.write(json.dumps(record, ensure_ascii=False) + '\n')
    print(f"💾 历史已保存到 {HISTORY_PATH}")
    
    # 5. 保存基线
    if args.update or not BASELINE_PATH.exists():
        BASELINE_PATH.write_text(json.dumps(current_odds, indent=2, ensure_ascii=False))
        print(f"💾 基线已保存到 {BASELINE_PATH}")
    
    # 6. 生成报告
    report = generate_report(current_odds, changes, significant, source)
    report_path = REPORTS_DIR / f'odds-monitor-{datetime.now().strftime("%Y%m%d-%H%M")}.txt'
    report_path.parent.mkdir(exist_ok=True)
    report_path.write_text(report)
    print(f"📄 报告已保存到 {report_path}")
    print()
    print(report)


def parse_api_data(data):
    """解析 the-odds-api 返回的 JSON 格式"""
    # data 是 list of events
    # 每个 event 包含 bookmakers -> markets -> outcomes
    team_odds = {}
    
    if not data or not isinstance(data, list):
        return team_odds
    
    # 取第一个 event (World Cup winner)
    for event in data:
        if 'fifa' in event.get('sport_key', '').lower() or 'world cup' in event.get('sport_title', '').lower():
            for book in event.get('bookmakers', []):
                for market in book.get('markets', []):
                    if market.get('key') == 'outrights':
                        for outcome in market.get('outcomes', []):
                            team = outcome.get('name', '')
                            price = outcome.get('price', 0)
                            # 取最低水位（最好的赔率）
                            if team not in team_odds or price > team_odds[team]:
                                team_odds[team] = price
            break
    
    return team_odds


def generate_report(current, changes, significant, source):
    """生成可读报告"""
    lines = []
    lines.append("=" * 70)
    lines.append(f"  2026 世界杯 赔率监控报告")
    lines.append(f"  时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"  源: {source}")
    lines.append(f"  球队: {len(current)}")
    lines.append("=" * 70)
    lines.append("")
    
    if significant:
        lines.append(f"🚨 重大赔率变化 ({len(significant)} 队):")
        lines.append("")
        for c in significant:
            arrow = "📉" if c['change_pct'] < 0 else "📈"
            lines.append(f"  {arrow} {c['team']:<15} {c['previous']:.2f} → {c['current']:.2f}  "
                        f"({c['change_pct']:+.1f}%)")
        lines.append("")
        lines.append("💡 解读:")
        lines.append("  📈 赔率上升 = 博彩公司认为该队夺冠可能性下降 (市场上钱流出去)")
        lines.append("  📉 赔率下降 = 博彩公司认为该队夺冠可能性上升 (市场更看好)")
    else:
        lines.append("✅ 无重大变化")
    
    lines.append("")
    lines.append("📊 当前赔率 TOP 20:")
    lines.append("-" * 70)
    sorted_odds = sorted(current.items(), key=lambda x: x[1])
    for i, (team, dec) in enumerate(sorted_odds[:20], 1):
        lines.append(f"  {i:>3}. {team:<15} 小数 {dec:>6.2f}  美式 {decimal_to_american_str(dec):>8}")
    
    return '\n'.join(lines)


def decimal_to_american_str(dec):
    if dec < 2.0:
        return f"{int(-100 / (dec - 1))}"
    else:
        return f"+{int(100 * (dec - 1))}"


if __name__ == "__main__":
    main()
