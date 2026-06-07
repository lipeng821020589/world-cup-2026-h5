#!/usr/bin/env python3
"""
小程序数据构建器
把 world-cup-2026/data/*.json 转成 miniapp/data/*.js 模块
JSON 不能直接被小程序 import，需要 module.exports 包装
"""

import json
from pathlib import Path

ROOT = Path('/Work/world-cup-2026')
OUT = ROOT / 'miniapp' / 'data'
OUT.mkdir(parents=True, exist_ok=True)

# 各源数据 → 小程序数据
SOURCES = {
    'teams':    ROOT / 'data' / 'teams.json',
    'squads':   ROOT / 'data' / 'squads.json',
    'venues':   ROOT / 'data' / 'venues.json',
    'matches':  ROOT / 'data' / 'matches.json',
    'odds_baseline': ROOT / 'data' / 'odds_baseline.json',
}

# 实力分 (与 group_predict.py 同步)
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

# 旗 (与 group_analysis_gen.py 同步)
FLAGS = {
    "Mexico": "🇲🇽", "South Africa": "🇿🇦", "South Korea": "🇰🇷", "Czech Republic": "🇨🇿",
    "Canada": "🇨🇦", "Bosnia and Herzegovina": "🇧🇦", "Qatar": "🇶🇦", "Switzerland": "🇨🇭",
    "Brazil": "🇧🇷", "Morocco": "🇲🇦", "Haiti": "🇭🇹", "Scotland": "🏴",
    "USA": "🇺🇸", "Paraguay": "🇵🇾", "Turkey": "🇹🇷", "Finland": "🇫🇮",
    "Germany": "🇩🇪", "Curaçao": "🇨🇼", "Ivory Coast": "🇨🇮", "Ecuador": "🇪🇨",
    "Netherlands": "🇳🇱", "Japan": "🇯🇵", "Sweden": "🇸🇪", "Tunisia": "🇹🇳",
    "Belgium": "🇧🇪", "Egypt": "🇪🇬", "Iran": "🇮🇷", "New Zealand": "🇳🇿",
    "Spain": "🇪🇸", "Cape Verde": "🇨🇻", "Saudi Arabia": "🇸🇦", "Uruguay": "🇺🇾",
    "France": "🇫🇷", "Senegal": "🇸🇳", "Iraq": "🇮🇶", "Norway": "🇳🇴",
    "Argentina": "🇦🇷", "Algeria": "🇩🇿", "Austria": "🇦🇹", "Jordan": "🇯🇴",
    "Portugal": "🇵🇹", "DR Congo": "🇨🇩", "Uzbekistan": "🇺🇿", "Colombia": "🇨🇴",
    "England": "🏴", "Croatia": "🇭🇷", "Ghana": "🇬🇭", "Panama": "🇵🇦",
}


def write_module(name, data):
    """写一个 .js 模块，module.exports = ..."""
    out = OUT / f'{name}.js'
    body = json.dumps(data, ensure_ascii=False, indent=2)
    out.write_text(f"// 自动生成 from build_miniapp_data.py\nmodule.exports = {body};\n")
    print(f"  ✅ {out.name}  ({len(body)} 字符)")


def main():
    print("=" * 60)
    print("  小程序数据构建器")
    print("=" * 60)
    print()
    
    # 1. 直接复制 JSON 数据
    for name, src in SOURCES.items():
        if not src.exists():
            print(f"  ⚠️ 跳过 {name}（{src} 不存在）")
            continue
        data = json.loads(src.read_text())
        write_module(name, data)
    
    # 2. 生成综合 team 列表（48 队 + 实力分 + 旗 + 所属组）
    teams_data = json.loads((ROOT / 'data' / 'teams.json').read_text())
    teams_list = []
    for letter in 'ABCDEFGHIJKL':
        info = teams_data['groups'][letter]
        for team in info['teams']:
            teams_list.append({
                'name': team,
                'flag': FLAGS.get(team, '🏳'),
                'score': TEAM_SCORE.get(team, 40),
                'tier': (
                    'T1' if TEAM_SCORE.get(team, 40) >= 88 else
                    'T2' if TEAM_SCORE.get(team, 40) >= 78 else
                    'T3' if TEAM_SCORE.get(team, 40) >= 65 else 'T4'
                ),
                'group': letter,
                'seed_of_group': team == info.get('seed'),
            })
    write_module('teams_list', teams_list)
    
    # 3. 生成 12 小组预测 (从 group_predict 算法移植)
    # 不在这里跑模拟，直接硬编码预测（基于 group_analysis_gen.py 的输出）
    predictions = {
        'A': [('Mexico', 68), ('South Korea', 62), ('Czech Republic', 56), ('South Africa', 48)],
        'B': [('Canada', 67), ('Switzerland', 64), ('Bosnia and Herzegovina', 54), ('Qatar', 50)],
        'C': [('Brazil', 82), ('Morocco', 76), ('Scotland', 40), ('Haiti', 36)],
        'D': [('USA', 72), ('Turkey', 60), ('Paraguay', 53), ('Finland', 48)],
        'E': [('Germany', 79), ('Ecuador', 62), ('Ivory Coast', 58), ('Curaçao', 38)],
        'F': [('Netherlands', 78), ('Japan', 70), ('Sweden', 62), ('Tunisia', 52)],
        'G': [('Belgium', 69), ('Egypt', 60), ('Iran', 55), ('New Zealand', 40)],
        'H': [('Spain', 91), ('Uruguay', 75), ('Saudi Arabia', 56), ('Cape Verde', 45)],
        'I': [('France', 90), ('Norway', 69), ('Senegal', 65), ('Iraq', 48)],
        'J': [('Argentina', 93), ('Austria', 58), ('Algeria', 54), ('Jordan', 42)],
        'K': [('Portugal', 80), ('Colombia', 60), ('DR Congo', 50), ('Uzbekistan', 44)],
        'L': [('England', 91), ('Croatia', 67), ('Ghana', 52), ('Panama', 42)],
    }
    write_module('predictions', predictions)
    
    # 4. 死亡之组
    death_groups = [
        {'letter': 'I', 'reason': 'France + Norway (Haaland) + Senegal (2022 16 强)'},
        {'letter': 'F', 'reason': 'Netherlands + Japan + Sweden 三强'},
        {'letter': 'H', 'reason': 'Spain (欧洲杯冠军) + Uruguay (贝尔萨体系)'},
    ]
    write_module('death_groups', death_groups)
    
    # 5. 蒙特卡洛结果（从最新 final-prediction.txt 提取，硬编码）
    monte_carlo = {
        'champion_prob': {
            'Spain': 39.2, 'Argentina': 37.2, 'England': 20.3, 'France': 3.2, 'Brazil': 0.1,
        },
        'final4_prob': {
            'Spain': 99.7, 'Brazil': 91.2, 'Senegal': 55.4, 'Argentina': 53.3,
            'England': 38.0, 'Sweden': 17.7, 'Norway': 15.7, 'France': 8.7,
        },
        'final_matchup': 'Spain vs Argentina',
        'most_likely_champion': 'Argentina',
    }
    write_module('monte_carlo', monte_carlo)
    
    # 6. 关键事件 (首页用)
    events = [
        {'id': 'opener', 'name': '🏆 揭幕战 墨西哥 vs 南非', 'date': '2026-06-11', 'time_local': '14:00', 'venue': 'Estadio Azteca', 'stage': 'Group A'},
        {'id': 'final',  'name': '🏆 决赛', 'date': '2026-07-19', 'time_local': '15:00', 'venue': 'MetLife Stadium', 'stage': 'Final'},
        {'id': 'fra_nor', 'name': '💀 死亡之组：法国 vs 挪威', 'date': '2026-06-20', 'time_local': '20:00', 'venue': 'AT&T Stadium', 'stage': 'Group I'},
    ]
    write_module('events', events)
    
    # 7. 倒计时目标
    countdown_targets = [
        {'id': 'opener', 'name': '揭幕战', 'date': '2026-06-11T14:00:00-06:00'},
        {'id': 'final',  'name': '决赛',   'date': '2026-07-19T15:00:00-04:00'},
    ]
    write_module('countdown_targets', countdown_targets)
    
    print()
    print("=" * 60)
    print(f"  ✅ 已生成 {len(list(OUT.glob('*.js')))} 个数据模块到 {OUT}")
    print("=" * 60)


if __name__ == "__main__":
    main()
