#!/usr/bin/env bash
# ============================================================
# 贵阳8月 · 业绩+积分+排行 结合看板 自动更新脚本
# 用法:
#   bash guiyang_auto_update.sh <积分表.xlsx> [数据回传表.xlsx] [业绩排行榜.xlsx]
# 流程: 解析xlsx → 生成看板HTML → 更新index.html → 推送GitHub Pages
# ============================================================
set -e
cd "$(dirname "$0")"

XLSX="${1:?用法: bash guiyang_auto_update.sh <积分表.xlsx> [数据回传表.xlsx] [业绩排行榜.xlsx]}"
PERF_XLSX="${2:-}"
RANK_XLSX="${3:-}"
TS=$(date +%Y%m%d_%H%M%S)
DATA_JSON="guiyang_data.json"
OUT_HTML="贵阳8月_门店动作执行看板.html"

echo "📥 积分表: $XLSX"
echo "① 解析积分数据..."
python3 guiyang_parse.py "$XLSX" "$DATA_JSON"

PERF_ARG=""
if [ -n "$PERF_XLSX" ] && [ -f "$PERF_XLSX" ]; then
  echo "📥 数据回传表: $PERF_XLSX"
  echo "② 解析业绩数据..."
  python3 guiyang_parse.py "$PERF_XLSX" "/tmp/guiyang_perf.json"
  PERF_ARG="/tmp/guiyang_perf.json"
fi

RANK_ARG=""
if [ -n "$RANK_XLSX" ] && [ -f "$RANK_XLSX" ]; then
  echo "📥 业绩排行榜: $RANK_XLSX"
  echo "③ 解析排行榜数据..."
  python3 guiyang_parse.py "$RANK_XLSX" "/tmp/guiyang_rank.json"
  RANK_ARG="/tmp/guiyang_rank.json"
fi

echo "④ 生成看板（业绩+积分+排行结合）..."
python3 guiyang_build.py "$DATA_JSON" "$PERF_ARG" "$RANK_ARG" "$OUT_HTML"

echo "⑤ 更新主入口 index.html..."
cp "$OUT_HTML" index.html

echo "⑥ 推送 GitHub Pages..."
git add -A
git commit -m "每日更新：贵阳业绩+积分+排行看板 ($TS)" --allow-empty
git push origin main

echo "✅ 完成！外部链接: https://wengweijian.github.io/BB-jiaofuzhongxin/"
