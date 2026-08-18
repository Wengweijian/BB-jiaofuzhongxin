#!/usr/bin/env bash
# ============================================================
# 贵阳8月 · 门店动作执行看板 自动更新脚本
# 用法: bash guiyang_auto_update.sh <数据表/积分表.xlsx>
# 流程: 解析xlsx → 生成看板HTML → 推送GitHub Pages
# ============================================================
set -e
cd "$(dirname "$0")"

XLSX="${1:?用法: bash guiyang_auto_update.sh <xlsx文件>}"
TS=$(date +%Y%m%d_%H%M%S)
DATA_JSON="guiyang_data.json"
OUT_HTML="贵阳8月_门店动作执行看板.html"

echo "📥 输入文件: $XLSX"
echo "① 解析数据..."
python3 guiyang_parse.py "$XLSX" "$DATA_JSON"

echo "② 生成看板..."
python3 guiyang_build.py "$DATA_JSON" "$OUT_HTML"

echo "③ 更新主入口 index.html..."
cp "$OUT_HTML" index.html

echo "④ 推送 GitHub Pages..."
git add -A
git commit -m "每日更新：贵阳门店动作执行看板 ($TS)" --allow-empty
git push origin main

echo "✅ 完成！外部链接: https://wengweijian.github.io/BB-jiaofuzhongxin/"
