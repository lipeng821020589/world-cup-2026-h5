#!/usr/bin/env python3
"""
生成小程序 tabBar 图标 (PNG)
简化：用 PIL 画几何图形
"""

from PIL import Image, ImageDraw
from pathlib import Path

OUT = Path('/Work/world-cup-2026/miniapp/images')
OUT.mkdir(parents=True, exist_ok=True)

SIZE = 81  # 小程序 tabBar 标准尺寸

def make_icon(name, draw_fn, color=(150, 150, 150)):
    """画 81x81 图标"""
    img = Image.new('RGBA', (SIZE, SIZE), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    draw_fn(d, color)
    img.save(OUT / f'{name}.png')
    print(f"  ✅ {name}.png")

def make_active(name, draw_fn):
    make_icon(name, draw_fn, color=(26, 71, 42))  # #1a472a


# ============ 首页 (房子) ============
def home_icon(d, color):
    # 房子
    d.polygon([(40, 15), (15, 35), (15, 65), (65, 65), (65, 35)], fill=color)
    d.rectangle([(35, 45), (45, 65)], fill='white')

make_icon('home', home_icon)
make_active('home_active', home_icon)


# ============ 小组 (4 圆点) ============
def groups_icon(d, color):
    for x, y in [(25, 25), (55, 25), (25, 55), (55, 55)]:
        d.ellipse([x-10, y-10, x+10, y+10], fill=color)

make_icon('groups', groups_icon)
make_active('groups_active', groups_icon)


# ============ 球队 (人形) ============
def teams_icon(d, color):
    # 头
    d.ellipse([(30, 15), (50, 35)], fill=color)
    # 身
    d.polygon([(20, 70), (40, 35), (60, 70)], fill=color)

make_icon('teams', teams_icon)
make_active('teams_active', teams_icon)


# ============ 赔率 (¥ 符号) ============
def odds_icon(d, color):
    # Y 形
    d.line([(25, 20), (40, 45), (55, 20)], fill=color, width=6)
    d.line([(40, 45), (40, 70)], fill=color, width=6)
    # 双横线
    d.line([(28, 35), (52, 35)], fill=color, width=4)
    d.line([(28, 48), (52, 48)], fill=color, width=4)

make_icon('odds', odds_icon)
make_active('odds_active', odds_icon)


print()
print(f"✅ 已生成 8 个图标到 {OUT}")
