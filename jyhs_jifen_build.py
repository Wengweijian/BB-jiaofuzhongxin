#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""金九银十·贵阳门店动作积分看板 生成
用法: python3 jyhs_jifen_build.py jyhs_jifen.json jyhs-jifen.html
"""
import json, sys

def build(data_path, out_path):
    d = json.load(open(data_path))
    labels = d['labels']; daily = d['daily_total']
    stores = d['stores']; groups = d['groups']
    nz = [i for i, v in enumerate(daily) if v > 0]
    active_days = len(nz)
    maxday = max(daily) if daily else 1
    total = d['total_score']

    H = [f'''<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>金九银十 · 贵阳门店动作积分看板</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:-apple-system,"PingFang SC","Microsoft YaHei",sans-serif;background:#0b1220;color:#e8eefc;padding:18px 14px 60px}}
.wrap{{max-width:1180px;margin:0 auto}}
h1{{font-size:22px;margin-bottom:4px}}
.sub{{color:#8fa3c8;font-size:13px;margin-bottom:18px}}
.kpis{{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:12px;margin-bottom:20px}}
.kpi{{background:linear-gradient(160deg,#15203a,#0f1830);border:1px solid #24324f;border-radius:14px;padding:14px 16px}}
.kpi .lb{{font-size:12px;color:#8fa3c8;margin-bottom:6px}}
.kpi .vl{{font-size:26px;font-weight:800}}
.kpi .vl small{{font-size:13px;font-weight:600;color:#9fb2d4}}
.section{{background:#101a30;border:1px solid #24324f;border-radius:14px;padding:16px;margin-bottom:16px}}
.section-title{{font-size:15px;font-weight:700;margin-bottom:12px;color:#f1f5f9}}
.table-wrap{{max-height:430px;overflow:auto;border-radius:8px}}
table{{width:100%;border-collapse:collapse;font-size:13px}}
th{{position:sticky;top:0;background:#182642;color:#b7c7e6;text-align:left;padding:9px 10px;white-space:nowrap}}
td{{padding:8px 10px;border-top:1px solid #1c2942;white-space:nowrap}}
td.nm{{font-weight:600;color:#dbe6fb;white-space:normal}}
.bars{{display:flex;align-items:flex-end;gap:4px;height:150px;margin-top:8px}}
.bar{{flex:1;background:#1c2942;border-radius:4px 4px 0 0;position:relative;min-width:8px}}
.bar i{{position:absolute;bottom:0;left:0;right:0;background:linear-gradient(180deg,#60a5fa,#3b82f6);border-radius:4px 4px 0 0}}
.bar .cap{{position:absolute;top:-18px;left:0;right:0;text-align:center;font-size:10px;color:#9fb2d4}}
.bar .lb2{{position:absolute;bottom:-18px;left:-2px;right:-2px;text-align:center;font-size:9px;color:#6b7ea0}}
.chart{{height:190px;padding-bottom:20px;overflow-x:auto}}
.g3{{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:12px}}
.card{{background:#0e1830;border:1px solid #24324f;border-radius:12px;padding:14px}}
.card .t{{font-size:13px;color:#8fa3c8;margin-bottom:6px}}
.card .v{{font-size:24px;font-weight:800;color:#60a5fa}}
.card .d{{font-size:12px;color:#8fa3c8;margin-top:4px}}
.heat{{font-size:11px}}
.heat td,.heat th{{padding:4px 6px;border-top:1px solid #1c2942}}
.heat .cell{{display:inline-block;width:16px;height:16px;border-radius:3px;background:#1c2942}}
.good{{color:#34d399}} .mid{{color:#fbbf24}} .bad{{color:#f87171}}
.foot{{color:#6b7ea0;font-size:12px;margin-top:22px;line-height:1.8}}
</style></head><body><div class="wrap">''']

    H.append('<h1>🏆 金九银十 · 贵阳门店动作积分看板</h1>')
    H.append(f'<div class="sub">统计口径：门店每日动作积分（9月）· 数据更新 {d["updated"]}</div>')

    H.append('<div class="kpis">')
    H.append(f'<div class="kpi"><div class="lb">累计总积分</div><div class="vl">{total}<small>分</small></div></div>')
    H.append(f'<div class="kpi"><div class="lb">参与门店</div><div class="vl">{d["total_stores"]}<small>家</small></div></div>')
    H.append(f'<div class="kpi"><div class="lb">有效天数</div><div class="vl">{active_days}<small>天</small></div></div>')
    H.append(f'<div class="kpi"><div class="lb">日均积分</div><div class="vl">{round(total/active_days) if active_days else 0}<small>分/天</small></div></div>')
    H.append(f'<div class="kpi"><div class="lb">今日上报门店</div><div class="vl">{len(d["today"])}<small>家</small></div></div>')
    H.append('</div>')

    # 每日走势
    H.append('<div class="section"><div class="section-title">📈 每日总积分走势</div><div class="chart"><div class="bars">')
    for i, v in enumerate(daily):
        h = (v / maxday * 100) if maxday else 0
        cap = f'<span class="cap">{v}</span>' if v > 0 else ''
        gray = '' if v > 0 else 'opacity:.35'
        H.append(f'<div class="bar {gray}">{cap}<i style="height:{h:.1f}%"></i><span class="lb2">{labels[i]}</span></div>')
    H.append('</div></div></div>')

    # 组别
    H.append('<div class="section"><div class="section-title">🎖️ S / A / B 组表现</div><div class="g3">')
    for g in ['S', 'A', 'B']:
        if g in groups:
            v = groups[g]
            H.append(f'<div class="card"><div class="t">{g}组（{v["count"]}家）</div><div class="v">{v["total"]}<small style="font-size:13px;color:#9fb2d4"> 分</small></div><div class="d">人均 {round(v["avg"])} 分</div></div>')
    H.append('</div></div>')

    # 区域
    H.append('<div class="section"><div class="section-title">🗺️ 区域积分分布</div><div class="table-wrap"><table>')
    H.append('<tr><th>#</th><th>区域</th><th>门店数</th><th>总积分</th><th>人均积分</th></tr>')
    rt = sorted(d['reg_total'].items(), key=lambda x: -x[1])
    for i, (k, v) in enumerate(rt, 1):
        c = d['reg_cnt'].get(k, 0)
        H.append(f'<tr><td>{i}</td><td class="nm">{k}</td><td>{c}</td><td>{v}</td><td>{round(v/c) if c else 0}</td></tr>')
    H.append('</table></div></div>')

    # 今日动作完成率
    H.append('<div class="section"><div class="section-title">✅ 今日各动作完成门店数</div><div class="table-wrap"><table>')
    H.append('<tr><th>动作</th><th>完成门店数</th><th>覆盖率</th></tr>')
    n = len(d['today']) or 1
    for a in d['act_names']:
        c = d['act_done'].get(a, 0)
        H.append(f'<tr><td class="nm">{a}</td><td>{c}</td><td>{round(c/n*100)}%</td></tr>')
    H.append('</table></div></div>')

    # 门店排行 全部（按总分）
    H.append('<div class="section"><div class="section-title">🥇 门店积分排行（全量·按累计积分）</div><div class="table-wrap"><table>')
    H.append('<tr><th>#</th><th>门店</th><th>组别</th><th>区域</th><th>累计积分</th><th>日均</th></tr>')
    for i, s in enumerate(sorted(stores, key=lambda x: -x['total']), 1):
        avg = round(s['total'] / active_days) if active_days else 0
        H.append(f'<tr><td>{i}</td><td class="nm">{s["store"]}</td><td>{s["group"] or ""}</td><td>{s["region"] or ""}</td><td>{s["total"]}</td><td>{avg}</td></tr>')
    H.append('</table></div></div>')

    H.append(f'<div class="foot">数据来源：贵阳数据积分表（9月）· 每日存根/每日公示<br>'
             f'口径：门店每日动作积分；有效天数 {active_days} 天（{labels[nz[0]] if nz else "-"}–{labels[nz[-1]] if nz else "-"}）<br>'
             f'自动生成：AI交付总监 · {d["updated"]}</div>')
    H.append('</div></body></html>')
    open(out_path, 'w').write(''.join(H))
    print(f'✅ 积分看板已生成: {out_path}')

if __name__ == '__main__':
    build(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else 'jyhs-jifen.html')
