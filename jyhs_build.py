#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""金九银十贵阳老板电器 · 业绩达成看板 生成脚本
用法: python3 jyhs_build.py jyhs_perf.json 金九银十_贵阳业绩达成看板.html
"""
import json, sys
from datetime import datetime

def w(v):
    return round(v / 10000, 1)

def pct(v):
    return f"{v*100:.1f}%"

def bar(rate, ref=None):
    p = max(0, min(rate * 100, 100))
    cls = 'good' if rate >= 0.10 else ('mid' if rate >= 0.06 else 'bad')
    return f'<div class="pb"><div class="pb-in {cls}" style="width:{p:.1f}%"></div></div>'

def rcls(rate):
    return 'good' if rate >= 0.10 else ('mid' if rate >= 0.06 else 'bad')

def table(rows, label):
    h = [f'<div class="section"><div class="section-title">{label}</div><div class="table-wrap"><table>',
         '<tr><th>#</th><th>对象</th><th>9月目标</th><th>已完成</th><th>达成率</th><th>一阶段完成率</th><th>进度</th></tr>']
    for i, x in enumerate(rows, 1):
        h.append(f'<tr><td>{i}</td><td class="nm">{x["name"]}</td>'
                 f'<td>{w(x["t9"])}万</td><td>{w(x["d9"])}万</td>'
                 f'<td class="{rcls(x["r9"])}">{pct(x["r9"])}</td>'
                 f'<td>{"--" if x["pt"]==0 else pct(x["pr"])}</td>'
                 f'<td>{bar(x["r9"])}</td></tr>')
    h.append('</table></div></div>')
    return ''.join(h)

def build(data_path, out_path):
    d = json.load(open(data_path))
    o = d['overall']
    # 门店去重（同名保留首个）
    seen, stores = set(), []
    for s in d['stores']:
        if s['store'] in seen:
            continue
        seen.add(s['store'])
        stores.append(s)
    valid = [s for s in stores if s['t9'] > 0]
    top = sorted(valid, key=lambda x: -x['r9'])[:15]
    bottom = sorted([s for s in valid if s['d9'] < s['t9']], key=lambda x: x['r9'])[:15]
    zero = [s for s in stores if s['t9'] > 0 and s['d9'] == 0]

    H = []
    H.append(f'''<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>金九银十 · 贵阳老板电器 业绩达成看板</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:-apple-system,"PingFang SC","Microsoft YaHei",sans-serif;background:#0b1220;color:#e8eefc;padding:18px 14px 60px}}
.wrap{{max-width:1180px;margin:0 auto}}
h1{{font-size:22px;margin-bottom:4px}}
.sub{{color:#8fa3c8;font-size:13px;margin-bottom:18px}}
.kpis{{display:grid;grid-template-columns:repeat(auto-fit,minmax(165px,1fr));gap:12px;margin-bottom:20px}}
.kpi{{background:linear-gradient(160deg,#15203a,#0f1830);border:1px solid #24324f;border-radius:14px;padding:14px 16px}}
.kpi .lb{{font-size:12px;color:#8fa3c8;margin-bottom:6px}}
.kpi .vl{{font-size:26px;font-weight:800;letter-spacing:.5px}}
.kpi .vl small{{font-size:13px;font-weight:600;color:#9fb2d4}}
.good{{color:#34d399}} .mid{{color:#fbbf24}} .bad{{color:#f87171}}
.section{{background:#101a30;border:1px solid #24324f;border-radius:14px;padding:16px;margin-bottom:16px}}
.section-title{{font-size:15px;font-weight:700;margin-bottom:12px;color:#f1f5f9}}
.table-wrap{{max-height:420px;overflow:auto;border-radius:8px}}
table{{width:100%;border-collapse:collapse;font-size:13px}}
th{{position:sticky;top:0;background:#182642;color:#b7c7e6;font-weight:600;text-align:left;padding:9px 10px;white-space:nowrap}}
td{{padding:8px 10px;border-top:1px solid #1c2942;white-space:nowrap}}
td.nm{{font-weight:600;color:#dbe6fb;white-space:normal}}
.pb{{background:#1c2942;border-radius:6px;height:8px;min-width:70px;overflow:hidden}}
.pb-in{{height:100%;border-radius:6px}}
.pb-in.good{{background:#34d399}} .pb-in.mid{{background:#fbbf24}} .pb-in.bad{{background:#f87171}}
.prow{{display:flex;align-items:center;gap:10px;margin:8px 0}}
.prow .t{{width:120px;font-size:13px;color:#b7c7e6}}
.prow .pbb{{flex:1;background:#1c2942;border-radius:8px;height:14px;overflow:hidden}}
.prow .pbb i{{display:block;height:100%}}
.prow .v{{width:64px;text-align:right;font-size:13px;font-weight:700}}
.foot{{color:#6b7ea0;font-size:12px;margin-top:22px;line-height:1.8}}
</style></head><body><div class="wrap">''')
    H.append(f'<h1>🏬 金九银十 · 贵阳老板电器 业绩达成看板</h1>')
    H.append(f'<div class="sub">一阶段 9.1–9.20（目标40%）· 项目周期 {o.get("start","")}–{o.get("end","")} · 剩余 {o.get("remain_days",0)} 天 · 数据更新 {d["updated"]}</div>')

    # KPI
    H.append('<div class="kpis">')
    H.append(f'<div class="kpi"><div class="lb">项目总目标</div><div class="vl">{w(o["target"])}<small>万</small></div></div>')
    H.append(f'<div class="kpi"><div class="lb">累计完成</div><div class="vl">{w(o["done"])}<small>万</small></div></div>')
    H.append(f'<div class="kpi"><div class="lb">整体达成率</div><div class="vl {rcls(o["rate"])}">{pct(o["rate"])}</div></div>')
    H.append(f'<div class="kpi"><div class="lb">时间进度</div><div class="vl mid">{o.get("time_pct",0)}<small>%</small></div></div>')
    H.append(f'<div class="kpi"><div class="lb">差额</div><div class="vl bad">{w(o["diff"])}<small>万</small></div></div>')
    H.append(f'<div class="kpi"><div class="lb">待跟进门店(0出货)</div><div class="vl bad">{len(zero)}<small>家</small></div></div>')
    H.append('</div>')

    # 进度对比
    H.append('<div class="section"><div class="section-title">📈 达成率 vs 时间进度</div>')
    H.append(f'<div class="prow"><div class="t">整体达成率</div><div class="pbb"><i class="{rcls(o["rate"])}" style="width:{min(o["rate"]*100,100):.1f}%;background:currentColor"></i></div><div class="v {rcls(o["rate"])}">{pct(o["rate"])}</div></div>')
    H.append(f'<div class="prow"><div class="t">时间进度</div><div class="pbb"><i style="width:{min(o.get("time_pct",0),100):.1f}%;background:#60a5fa"></i></div><div class="v mid">{o.get("time_pct",0)}%</div></div>')
    gap = o['rate']*100 - o.get('time_pct',0)
    gl = '领先时间进度' if gap >= 0 else '落后时间进度'
    H.append(f'<div class="sub" style="margin:10px 0 0">当前{gl} {abs(gap):.1f} 个百分点（达成率口径含双月目标，仅供参考节奏）</div>')
    H.append('</div>')

    H.append(table(d['by_jun'], '👑 军长业绩排名'))
    H.append(table(d['by_channel'], '🛒 渠道业绩排名'))
    H.append(table(d['by_region'], '🗺️ 区域/板块排名'))

    # 门店 TOP / 待跟进
    def store_table(rows, label, tag):
        h = [f'<div class="section"><div class="section-title">{label}</div><div class="table-wrap"><table>',
             '<tr><th>#</th><th>门店</th><th>区域</th><th>军长</th><th>9月目标</th><th>已完成</th><th>达成率</th></tr>']
        for i, x in enumerate(rows, 1):
            h.append(f'<tr><td>{i}</td><td class="nm">{x["store"]}</td><td>{x["region"] or ""}</td><td>{x["jun"] or ""}</td>'
                     f'<td>{w(x["t9"])}万</td><td>{w(x["d9"])}万</td>'
                     f'<td class="{rcls(x["r9"])}">{pct(x["r9"])}</td></tr>')
        h.append('</table></div></div>')
        return ''.join(h)
    H.append(store_table(top, '🥇 门店达成率 TOP15', 'top'))
    H.append(store_table(bottom, '🔴 门店达成率待跟进（后15）', 'bottom'))

    # 门店明细全量（对齐“门店动销数据看板”列：军长|师长|渠道|门店|目标|完成|达成率|差额）
    allrows = sorted([s for s in stores if s['t9'] > 0], key=lambda x: -x['r9'])
    h = ['<div class="section"><div class="section-title">📋 门店明细（全量·按达成率排序）<span class="tag">' + str(len(allrows)) + '家</span></div><div class="table-wrap"><table>',
         '<tr><th>#</th><th>门店</th><th>军长</th><th>师长</th><th>渠道</th><th>9月目标</th><th>已完成</th><th>达成率</th><th>差额</th></tr>']
    for i, x in enumerate(allrows, 1):
        h.append(f'<tr><td>{i}</td><td class="nm">{x["store"]}</td><td>{x["jun"] or ""}</td><td>{x["shi"] or ""}</td>'
                 f'<td>{x["ch"] or ""}</td><td>{w(x["t9"])}万</td><td>{w(x["d9"])}万</td>'
                 f'<td class="{rcls(x["r9"])}">{pct(x["r9"])}</td><td>{w(x["t9"]-x["d9"])}万</td></tr>')
    h.append('</table></div></div>')
    H.append(''.join(h))

    H.append(f'<div class="foot">数据来源：金九银十贵阳老板电器 · 项目数据回传表（9/12）<br>'
             f'口径：①项目总目标 {w(o["target"])}万 / 累计完成 {w(o["done"])}万（与群内口径一致）；②门店明细口径合计 {w(d["detail_total"])}万 / 完成 {w(d["detail_done"])}万<br>'
             f'自动生成：AI交付总监 · {d["updated"]}</div>')
    H.append('</div></body></html>')

    html = ''.join(H)
    open(out_path, 'w').write(html)
    print(f"✅ 看板已生成: {out_path} ({len(html)} bytes)")

if __name__ == '__main__':
    build(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else '金九银十_贵阳业绩达成看板.html')
