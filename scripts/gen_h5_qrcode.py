#!/usr/bin/env python3
"""生成 H5 入口二维码 (PNG + ASCII)"""
import qrcode
from pathlib import Path

URL = "https://lipeng821020589.github.io/world-cup-2026-h5/"
OUT = Path("/Work/world-cup-2026/analysis/h5-qrcode.png")

# 高质量二维码
qr = qrcode.QRCode(
    version=None,  # 自动选最小
    error_correction=qrcode.constants.ERROR_CORRECT_H,  # 30% 容错
    box_size=12,
    border=3,
)
qr.add_data(URL)
qr.make(fit=True)

# 主题色 (绿色 + 绿底)
img = qr.make_image(fill_color="#1a472a", back_color="white")
img.save(OUT)
print(f"✅ PNG: {OUT}  ({OUT.stat().st_size} bytes)")

# 打印 URL
print(f"\n📱 扫码打开: {URL}")
print(f"   或访问:   {URL}")

# 写到 README 引用
README_REF = Path("/Work/world-cup-2026/analysis/H5-README.md")
README_REF.write_text(f"""# 📱 手机预览入口

![H5 入口](h5-qrcode.png)

**链接**: {URL}

打开手机相机扫码即可（无需下载）
""", encoding="utf-8")
print(f"✅ 引用文档: {README_REF}")
