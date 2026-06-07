#!/usr/bin/env python3
"""
2026 世界杯 12 小组深度分析生成器
为每个小组生成独立的 .md 分析文件 (analysis/group-A.md ~ group-L.md)
内容包含：
- 4 队实力对比
- 关键球员对决
- 出线预测
- 关键比赛时间
- 关注点 / 黑天鹅
"""

import json
from pathlib import Path
from datetime import datetime, timedelta

DATA_DIR = Path('/Work/world-cup-2026/data')
ANALYSIS_DIR = Path('/Work/world-cup-2026/analysis')
ANALYSIS_DIR.mkdir(exist_ok=True)

# 加载数据
data = json.loads((DATA_DIR / 'teams.json').read_text())
squads = json.loads((DATA_DIR / 'squads.json').read_text())
venues = json.loads((DATA_DIR / 'venues.json').read_text())

# 实力分（与 group_predict.py 同步）
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

# 球衣配色 + 旗
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
    "England": "🏴󠁧󠁢󠁥󠁮󠁧󠁿", "Croatia": "🇭🇷", "Ghana": "🇬🇭", "Panama": "🇵🇦",
}

# 简短组描述
GROUP_DESC = {
    "A": "东道主揭幕战组 — 墨西哥主场首秀，传统亚洲劲旅韩国 vs 回归的捷克",
    "B": "东道主二号加拿大组 — 波黑首次 vs 亚洲杯冠军卡塔尔 + 瑞士稳定输出",
    "C": "卫冕亚军 + 黑马组 — 巴西 + 摩洛哥，Haiti 神秘，苏格兰浪漫主义",
    "D": "东道主三号美国组 — 巴拉圭 + 土耳其搅局，芬兰北境崛起",
    "E": "传统豪门德国组 — 库拉索奇迹首次参赛，科特迪瓦 + 厄瓜多尔高原杀手",
    "F": "隐形死亡之组 — 荷兰 + 日本 + 瑞典，突尼斯打辅助",
    "G": "黄金一代告别组 — 比利时 + 埃及 + 伊朗，新西兰体验之旅",
    "H": "地中海死亡之组 — 西班牙 + 乌拉圭，沙特爆冷基因 + 佛得角首秀",
    "I": "公认死亡之组 — 法国 + 挪威 + 塞内加尔，伊拉克陪跑",
    "J": "卫冕冠军舒适组 — 阿根廷 + 奥地利 + 阿尔及利亚 + 约旦",
    "K": "C 罗告别组 — 葡萄牙 + 哥伦比亚，乌兹别克首秀 + 刚果神秘",
    "L": "三狮军团组 — 英格兰 + 克罗地亚，加纳 + 巴拿马凑数",
}

# 组特殊标签
GROUP_TAGS = {
    "A": "🏆 揭幕战",
    "B": "🍁 东道主",
    "C": "🌟 巴西",
    "D": "🇺🇸 东道主",
    "E": "🆕 库拉索首秀",
    "F": "⚠️ 隐形死亡",
    "G": "👋 比利时告别",
    "H": "⚠️ 地中海死亡",
    "I": "💀 公认死亡",
    "J": "⭐ 卫冕冠军",
    "K": "👋 C 罗告别",
    "L": "🌟 三狮军团",
}

# 死亡之组
DEATH_GROUPS = data.get('death_groups', [])


def score(team):
    return TEAM_SCORE.get(team, 40)


def get_top_players(team, n=3):
    """取一支球队 top n 关键球员"""
    plist = squads.get('teams', {}).get(team, [])
    # 优先 ⭐ 标记
    starred = [p for p in plist if '⭐' in p.get('key', '')]
    return starred[:n] if starred else plist[:n]


def predict_standings(teams):
    """实力排名（4 队）"""
    scored = [(t, score(t)) for t in teams]
    scored.sort(key=lambda x: -x[1])
    return scored


def predict_qualifiers(teams):
    """预测 2 个出线队（实力前 2）"""
    return predict_standings(teams)[:2]


def key_matchups(teams):
    """生成 6 场对决的简化时间（6/12 - 6/27）"""
    if len(teams) != 4:
        return []
    # 标准顺序：A1vA2, A3vA4, A1vA3, A2vA4, A1vA4, A2vA3
    return [
        (teams[0], teams[1]),
        (teams[2], teams[3]),
        (teams[0], teams[2]),
        (teams[1], teams[3]),
        (teams[0], teams[3]),
        (teams[1], teams[2]),
    ]


def render_player(p):
    flags = p.get('key', '')
    notes = p.get('notes', '')
    line = f"  - **{p['name']}** ({p['pos']}, {p['club']}, {p['age']}岁) {flags}"
    if notes:
        line += f" — {notes}"
    return line


def render_group(letter):
    info = data['groups'][letter]
    teams = info['teams']
    seed = info.get('seed', '?')
    host = info.get('host')
    debut = info.get('debut', [])
    death_flag = any(dg['letter'] == letter for dg in DEATH_GROUPS)
    
    standings = predict_standings(teams)
    qualifiers = predict_qualifiers(teams)
    
    lines = []
    lines.append(f"# Group {letter} 深度分析")
    lines.append("")
    lines.append(f"> **{GROUP_TAGS.get(letter, '')}** — {GROUP_DESC.get(letter, '')}")
    lines.append("")
    lines.append(f"**种子**: {FLAGS.get(seed, '')} {seed}  |  **4 队**: " + " / ".join(f"{FLAGS.get(t, '')} {t}" for t in teams))
    if host:
        lines.append(f"**东道主**: {FLAGS.get(host, '')} {host}")
    if debut:
        lines.append(f"**首次参赛**: {', '.join(debut)}")
    if death_flag:
        lines.append(f"**死亡之组**: 💀 是 (公认)")
    lines.append("")
    
    # 实力对比表
    lines.append("## 📊 实力分档")
    lines.append("")
    lines.append("| 排名 | 球队 | 实力分 | 档位 | 关键标签 |")
    lines.append("|------|------|--------|------|---------|")
    for i, (t, s) in enumerate(standings, 1):
        tier = "🏆 T1" if s >= 88 else ("🥈 T2" if s >= 78 else ("🥉 T3" if s >= 65 else "🐎 T4"))
        qual = "✅" if i <= 2 else "❌"
        # 看是否有 T1 标签
        is_t1 = t in data.get('tier_1_contenders', [])
        label = "⭐ 争冠热门" if is_t1 else tier
        lines.append(f"| {i} | {FLAGS.get(t, '')} {t} | {s} | {label} | {qual} |")
    lines.append("")
    
    # 出线预测
    lines.append("## 🎯 出线预测")
    lines.append("")
    q1, q2 = qualifiers
    lines.append(f"- **头名**: {FLAGS.get(q1[0], '')} **{q1[0]}** ({q1[1]})")
    lines.append(f"- **次名**: {FLAGS.get(q2[0], '')} **{q2[0]}** ({q2[1]})")
    lines.append(f"- **淘汰**: {FLAGS.get(standings[2][0], '')} {standings[2][0]} + {FLAGS.get(standings[3][0], '')} {standings[3][0]}")
    lines.append("")
    
    # 关键球员
    lines.append("## ⭐ 关键球员对决")
    lines.append("")
    for t, _ in standings:
        lines.append(f"### {FLAGS.get(t, '')} {t}")
        for p in get_top_players(t, 3):
            lines.append(render_player(p))
        lines.append("")
    
    # 6 场对决分析
    lines.append("## ⚔️ 6 场小组赛对决")
    lines.append("")
    matchups = key_matchups(teams)
    for i, (t1, t2) in enumerate(matchups, 1):
        s1, s2 = score(t1), score(t2)
        gap = abs(s1 - s2)
        if gap >= 15:
            verdict = f"**{t1} 大胜在望**" if s1 > s2 else f"**{t2} 大胜在望**"
        elif gap >= 5:
            verdict = f"**{t1} 略胜一筹**" if s1 > s2 else f"**{t2} 略胜一筹**"
        else:
            verdict = "🔥 **势均力敌 / 死亡对决**"
        lines.append(f"**{i}. {FLAGS.get(t1, '')} {t1}  vs  {FLAGS.get(t2, '')} {t2}**")
        lines.append(f"   实力分: {s1} vs {s2}  |  差距: {gap}")
        lines.append(f"   预测: {verdict}")
        lines.append("")
    
    # 关注点
    lines.append("## 🎯 关注点 / 黑天鹅")
    lines.append("")
    notes = generate_notes(letter, teams, standings)
    for note in notes:
        lines.append(f"- {note}")
    lines.append("")
    
    # 时间表（占位，6/11 - 6/27）
    lines.append("## 📅 大致时间（具体日期待 FIFA 公布）")
    lines.append("")
    lines.append("| 轮次 | 日期范围 | 北京时间 |")
    lines.append("|------|---------|---------|")
    lines.append("| 第 1 轮 | 6/12 - 6/16 | 次日 03:00 - 09:00 |")
    lines.append("| 第 2 轮 | 6/17 - 6/21 | 次日 03:00 - 09:00 |")
    lines.append("| 第 3 轮 | 6/22 - 6/27 | 次日 03:00 - 09:00 |")
    lines.append("")
    
    return '\n'.join(lines)


def generate_notes(letter, teams, standings):
    notes = []
    q1, q2 = standings[0], standings[1]
    q3, q4 = standings[2], standings[3]
    gap12 = abs(q1[1] - q2[1])
    gap23 = abs(q2[1] - q3[1])
    
    # 头两名差距
    if gap12 <= 5:
        notes.append(f"⚠️ **{q1[0]} vs {q2[0]} 头名之争白热化**（差距仅 {gap12} 分）")
    else:
        notes.append(f"✅ **{q1[0]} 头名较稳**，{q2[0]} 需力拼次名防翻车")
    
    # 2/3 名差距
    if gap23 <= 5:
        notes.append(f"🔥 **{q2[0]} / {q3[0]} 次名争夺激烈**（差距仅 {gap23} 分），有冷门可能")
    
    # 黑马提醒
    dark_horses_in_group = [t for t in teams if t in ['Norway', 'Morocco', 'Senegal', 'Egypt', 'Japan', 'South Korea', 'Ecuador', 'Ivory Coast']]
    if dark_horses_in_group:
        notes.append(f"🐎 黑马提醒: **{', '.join(dark_horses_in_group)}** 有望搅局")
    
    # 死亡之组特别说明
    if letter == 'I':
        notes.append("💀 **公认死亡之组**：3 队都有 16 强实力，1 队会悲剧")
        notes.append("📌 关注：**法国 vs 挪威 6/20** = 小组冠军争夺战")
    elif letter == 'F':
        notes.append("⚠️ **隐形死亡之组**：荷/日/瑞 3 强，突尼斯打辅助")
        notes.append("📌 预测：荷兰 + 日本出线，瑞典 30 年首次小组出局？")
    elif letter == 'H':
        notes.append("⚠️ **地中海死亡之组**：西班牙 2024 欧洲杯冠军 + 乌拉圭贝尔萨体系")
        notes.append("📌 沙特有 2022 胜阿根廷基因，需防冷")
    elif letter == 'C':
        notes.append("🌟 **T1 巴西 + 黑马摩洛哥**，苏格兰浪漫主义或搅局")
    elif letter == 'J':
        notes.append("⭐ **阿根廷舒适组** — 头名稳，次名 3 抢 1")
    elif letter == 'L':
        notes.append("🌟 **英格兰头名稳**，克罗地亚告别莫德里奇")
    
    # 东道主
    hosts = [t for t in teams if t in ['Mexico', 'USA', 'Canada']]
    if hosts:
        notes.append(f"🏠 东道主 **{hosts[0]}** 主场加成 +0.5 实力分")
    
    # 首次参赛
    if info := data['groups'][letter].get('debut'):
        notes.append(f"🆕 **{info[0]} 首次参赛** — 加勒比 / 非洲 / 亚洲新军")
    
    return notes


def main():
    print("=" * 70)
    print("  2026 世界杯 12 小组深度分析生成器")
    print("=" * 70)
    print()
    
    for letter in 'ABCDEFGHIJKL':
        md = render_group(letter)
        out = ANALYSIS_DIR / f'group-{letter}.md'
        out.write_text(md)
        print(f"  ✅ {out.name}  ({len(md)} 字符)")
    
    print()
    print("=" * 70)
    print(f"  ✅ 12 份小组分析已生成到 {ANALYSIS_DIR}")
    print("=" * 70)


if __name__ == "__main__":
    main()
