#!/bin/bash
# H5 部署后自动化截图（Chrome headless）
# 用法: ./h5_screenshot.sh [URL] [OUT_DIR]
# 默认: https://lipeng821020589.github.io/world-cup-2026-h5/ -> /tmp/wc2026-screenshots/

set -e
URL="${1:-https://lipeng821020589.github.io/world-cup-2026-h5/}"
OUT_DIR="${2:-/home/peng/.openclaw/workspace/.cache/wc2026-shots}"
TS=$(date +%Y%m%d-%H%M%S)

mkdir -p "$OUT_DIR"

echo "📸 截图: $URL"
echo "📁 输出: $OUT_DIR"
echo ""

# 1) 首页 (mobile 420x1800)
google-chrome --headless --disable-gpu --no-sandbox --hide-scrollbars \
  --window-size=420,1800 --screenshot="$OUT_DIR/home-mobile-$TS.png" \
  --virtual-time-budget=8000 \
  "${URL}" 2>/dev/null
echo "✅ home-mobile"

# 2) 预测 tab (mobile)
google-chrome --headless --disable-gpu --no-sandbox --hide-scrollbars \
  --window-size=420,7000 --screenshot="$OUT_DIR/predict-mobile-$TS.png" \
  --virtual-time-budget=8000 \
  "${URL}#predict" 2>/dev/null
echo "✅ predict-mobile"

# 3) 桌面版首页 (1280x1800)
google-chrome --headless --disable-gpu --no-sandbox --hide-scrollbars \
  --window-size=1280,1800 --screenshot="$OUT_DIR/home-desktop-$TS.png" \
  --virtual-time-budget=8000 \
  "${URL}" 2>/dev/null
echo "✅ home-desktop"

# 4) 桌面版预测 (1280x5000)
google-chrome --headless --disable-gpu --no-sandbox --hide-scrollbars \
  --window-size=1280,5000 --screenshot="$OUT_DIR/predict-desktop-$TS.png" \
  --virtual-time-budget=8000 \
  "${URL}#predict" 2>/dev/null
echo "✅ predict-desktop"

# 5) 赔率 tab
google-chrome --headless --disable-gpu --no-sandbox --hide-scrollbars \
  --window-size=420,3000 --screenshot="$OUT_DIR/odds-mobile-$TS.png" \
  --virtual-time-budget=8000 \
  "${URL}#odds" 2>/dev/null
echo "✅ odds-mobile"

ls -la "$OUT_DIR" | tail -10
echo ""
echo "📁 全部截图: $OUT_DIR"
