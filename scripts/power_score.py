#!/usr/bin/env python3
"""
2026 世界杯球队实力评分脚本

评分维度（0-100）：
- FIFA 排名 (30%)
- 阵容深度 (25%)
- 教练团队 (15%)
- 近 2 年大赛表现 (20%)
- 赛程/分组 (10%)
"""

TEAMS = {
    "阿根廷": {
        "fifa_rank_score": 95,  # FIFA 排名分（1=100, 50=50, 100+=0）
        "squad_depth": 92,
        "coach": 90,  # 斯卡洛尼
        "recent_form": 100,  # 2022 冠军 + 2024 美洲杯
        "schedule": 80,  # 假设分组中等
        "notes": "卫冕冠军",
    },
    "法国": {
        "fifa_rank_score": 92,
        "squad_depth": 100,  # 史上最深
        "coach": 85,
        "recent_form": 85,  # 2022 亚军
        "schedule": 80,
        "notes": "阵容深度无敌",
    },
    "西班牙": {
        "fifa_rank_score": 93,
        "squad_depth": 88,
        "coach": 92,  # 德拉富恩特
        "recent_form": 95,  # 2024 欧洲杯冠军
        "schedule": 82,
        "notes": "2024 欧洲杯冠军",
    },
    "巴西": {
        "fifa_rank_score": 88,
        "squad_depth": 90,
        "coach": 78,  # 多里瓦尔
        "recent_form": 70,  # 2022 8 强
        "schedule": 78,
        "notes": "前场豪华，9 号位缺人",
    },
    "英格兰": {
        "fifa_rank_score": 90,
        "squad_depth": 95,
        "coach": 95,  # 图赫尔
        "recent_form": 88,  # 2024 欧洲杯亚军
        "schedule": 80,
        "notes": "史上最豪华阵容",
    },
    "德国": {
        "fifa_rank_score": 78,
        "squad_depth": 85,
        "coach": 80,
        "recent_form": 75,
        "schedule": 75,
        "notes": "重建中",
    },
    "葡萄牙": {
        "fifa_rank_score": 80,
        "squad_depth": 82,
        "coach": 82,
        "recent_form": 78,
        "schedule": 78,
        "notes": "C 罗最后一届？",
    },
    "荷兰": {
        "fifa_rank_score": 75,
        "squad_depth": 78,
        "coach": 85,  # 科曼
        "recent_form": 78,
        "schedule": 78,
        "notes": "科曼二进宫",
    },
    "美国": {
        "fifa_rank_score": 65,
        "squad_depth": 70,
        "coach": 80,  # 贝尔哈特
        "recent_form": 70,
        "schedule": 90,  # 东道主红利
        "notes": "东道主",
    },
    "墨西哥": {
        "fifa_rank_score": 60,
        "squad_depth": 65,
        "coach": 75,
        "recent_form": 68,
        "schedule": 88,
        "notes": "东道主",
    },
    "加拿大": {
        "fifa_rank_score": 55,
        "squad_depth": 62,
        "coach": 78,
        "recent_form": 70,
        "schedule": 88,
        "notes": "东道主 + 戴维斯",
    },
    "乌拉圭": {
        "fifa_rank_score": 70,
        "squad_depth": 72,
        "coach": 88,  # 贝尔萨
        "recent_form": 75,
        "schedule": 75,
        "notes": "贝尔萨体系",
    },
    "摩洛哥": {
        "fifa_rank_score": 68,
        "squad_depth": 70,
        "coach": 82,
        "recent_form": 90,  # 2022 4 强
        "schedule": 75,
        "notes": "2022 4 强",
    },
    "日本": {
        "fifa_rank_score": 60,
        "squad_depth": 65,
        "coach": 85,  # 森保一
        "recent_form": 75,
        "schedule": 75,
        "notes": "稳定输出",
    },
    "挪威": {
        "fifa_rank_score": 58,
        "squad_depth": 65,
        "coach": 78,
        "recent_form": 80,  # 预选赛屠弱旅
        "schedule": 75,
        "notes": "哈兰德 + 厄德高",
    },
    "比利时": {
        "fifa_rank_score": 65,
        "squad_depth": 70,
        "coach": 75,
        "recent_form": 65,
        "schedule": 75,
        "notes": "黄金一代末班",
    },
}

WEIGHTS = {
    "fifa_rank_score": 0.30,
    "squad_depth": 0.25,
    "coach": 0.15,
    "recent_form": 0.20,
    "schedule": 0.10,
}


def score_team(data: dict) -> float:
    """计算单队综合实力分"""
    return sum(data[k] * WEIGHTS[k] for k in WEIGHTS)


def rank_teams(teams: dict) -> list:
    """按实力分排序"""
    scored = [(name, score_team(data), data["notes"]) for name, data in teams.items()]
    return sorted(scored, key=lambda x: -x[1])


def tier_from_score(score: float) -> str:
    """分档"""
    if score >= 88:
        return "🏆 T1 争冠热门"
    if score >= 78:
        return "🥈 T2 半决赛级"
    if score >= 68:
        return "🥉 T3 16 强级"
    return "🐎 T4 搅局者"


def main():
    print("=" * 60)
    print("  2026 世界杯 球队实力评分")
    print("=" * 60)
    print()

    ranked = rank_teams(TEAMS)
    print(f"{'排名':<5}{'球队':<10}{'实力分':<10}{'分档':<18}{'备注'}")
    print("-" * 60)
    for i, (name, score, notes) in enumerate(ranked, 1):
        tier = tier_from_score(score)
        print(f"{i:<5}{name:<10}{score:<10.1f}{tier:<18}{notes}")

    print()
    print("=" * 60)
    print("前 5 名为争冠热门（T1）")
    print("=" * 60)


if __name__ == "__main__":
    main()
