#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
贵阳8月 · 门店动作执行看板 一键构建脚本
用法:
  1) python3 guiyang_parse.py <积分表.xlsx> guiyang_data.json   # 解析数据
  2) python3 guiyang_build.py guiyang_data.json [输出.html]     # 生成看板
  3) bash guiyang_update.sh <积分表.xlsx>                        # 一步到位(解析+生成+推送)
"""
import json, sys, html as htmlmod
from collections import defaultdict

def build(data_path, perf_path=None, rank_path=None, out_path='贵阳8月_门店动作执行看板.html'):
    with open(data_path) as f:
        D = json.load(f)
    PERF = None
    if perf_path:
        try:
            with open(perf_path) as f:
                PERF = json.load(f)
        except Exception:
            PERF = None
    RANK = None
    if rank_path:
        try:
            with open(rank_path) as f:
                RANK = json.load(f)
        except Exception:
            RANK = None
    has_perf = PERF is not None and PERF.get('rows')
    has_rank = RANK is not None and RANK.get('channels')
    off = 1 if has_perf else 0  # 有业绩数据时业绩页占 page0

    dates = D['date_labels']
    daily_total = D['daily_total']
    reg_daily = D['reg_daily']
    reg_cnt = D['reg_cnt']
    stores_daily = D['stores_daily']
    ranks = D['ranks']
    TODAY = D['today']
    act_done = D['act_done']
    reg_today = D['reg_today']

    # ===== 阶段口径（第二阶段 8.17-8.23） =====
    PHASE_START = '08/17'
    phase_idx = next((i for i, d in enumerate(dates) if d >= PHASE_START), None)
    phase_active = phase_idx is not None and phase_idx > 0
    phase_dates = dates[phase_idx:] if phase_active else dates
    phase_n = len(phase_dates)
    for s in stores_daily:
        s['phase_total'] = sum(s['daily'][phase_idx:]) if phase_active else s['total']
        s['phase_avg'] = round(s['phase_total'] / phase_n, 1) if phase_n else 0
    # 重建排名：按阶段积分（S组前5 / A组前5 / B组前8 有奖金 300/200/100/50）
    if phase_active:
        ranks = {}
        group_key = {'S组': 'S', 'A组': 'A', 'B组': 'B'}  # 数据里分组为 S/A/B
        for g in ['S组', 'A组', 'B组']:
            members = [s for s in stores_daily if s.get('group') == group_key.get(g)]
            members.sort(key=lambda x: -x['phase_total'])
            arr = []
            for i, s in enumerate(members):
                rank = i + 1
                reward = None
                if g == 'S组' and rank <= 5:
                    reward = [300, 200, 100, 50, 50][rank - 1]
                elif g == 'A组' and rank <= 5:
                    reward = [300, 200, 100, 50, 50][rank - 1]
                elif g == 'B组' and rank <= 8:
                    reward = [300, 200, 100, 50, 50, 50, 50, 50][rank - 1]
                arr.append({'region': s['region'], 'store': s['store'], 'score': s['phase_total'],
                            'daily_avg': s['phase_avg'], 'rank': rank, 'reward': reward})
            ranks[g] = arr

    N = len(TODAY)
    zero_today = [t for t in TODAY if t['total'] == 0]
    pass_today = [t for t in TODAY if t['total'] >= 30]
    top_today = sorted(TODAY, key=lambda x: -x['total'])[:5]

    # ===== 门店趋势：进步/退步（前后半段日均对比） =====
    def _avg(vals):
        return sum(vals) / len(vals) if vals else 0
    trends = []
    for s in stores_daily:
        daily = s['daily']
        n = len(daily)
        half = n // 2
        f_avg = _avg(daily[:half])
        l_avg = _avg(daily[half:])
        trends.append({'store': s['store'], 'change': round(l_avg - f_avg, 1),
                       'f': round(f_avg, 1), 'l': round(l_avg, 1)})
    trends.sort(key=lambda x: -x['change'])
    progress_stores = [t for t in trends if t['change'] > 5][:8]   # 进步前8
    decline_stores = [t for t in trends[::-1] if t['change'] < -3][:8]  # 退步前8
    phase_score = sum(s['phase_total'] for s in stores_daily)
    phase_end = phase_dates[-1][-2:] if phase_dates else '23'

    ACT_ICONS = [('晨会','🌅'),('夕会','🌆'),('每日一读','📖'),('上门量尺','📏'),
                 ('KDS预约','📅'),('新增客资','👤'),('小红书截流','📕'),('捷报','🎉')]

    reg_colors = {
        '贵阳专卖店': '#16a34a', '贵阳家装': '#16a34a', '黔南': '#ca8a04', '遵义': '#ca8a04',
        '全省KA': '#ca8a04', '黔东南': '#dc2626', '铜仁': '#dc2626'}
    reg_order = ['贵阳专卖店','贵阳家装','黔南','遵义','全省KA','黔东南','铜仁']

    A = []
    A.append('''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>贵阳8月 · 门店动作执行看板</title>
<script src="chart.umd.min.js"></script>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,BlinkMacSystemFont,'PingFang SC','Microsoft YaHei',sans-serif;background:#0f172a;color:#e2e8f0}
.hero{background:linear-gradient(135deg,#1e3a8a 0%,#1d4ed8 60%,#3b82f6 100%);padding:22px 24px;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:12px}
.hero h1{font-size:24px;font-weight:800;letter-spacing:1px;color:#fff}
.hero .sub{font-size:13px;color:#bfdbfe;margin-top:4px}
.hero-right{text-align:right;font-size:12px;color:#dbeafe}
.update-badge{display:inline-flex;align-items:center;gap:6px;background:rgba(255,255,255,0.15);padding:4px 12px;border-radius:20px;font-size:12px;color:#fff}
.pulse{width:8px;height:8px;background:#4ade80;border-radius:50%;animation:pulse 1.5s infinite}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.3}}
.nav{display:flex;background:#1e293b;border-bottom:2px solid #334155;overflow-x:auto}
.nav button{flex:1;min-width:140px;padding:16px 10px;font-size:15px;font-weight:600;color:#94a3b8;background:none;border:none;cursor:pointer;border-bottom:3px solid transparent;white-space:nowrap}
.nav button.active{color:#3b82f6;border-bottom-color:#3b82f6;background:#0f172a}
.nav button:hover{color:#e2e8f0}
.page{display:none;padding:20px;max-width:1400px;margin:0 auto}
.page.active{display:block}
.kpi-row{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:14px;margin-bottom:18px}
.kpi{background:#1e293b;border-radius:14px;padding:18px 16px;border:1px solid #334155;position:relative;overflow:hidden}
.kpi .lab{font-size:12px;color:#94a3b8;margin-bottom:6px}
.kpi .val{font-size:30px;font-weight:800}
.kpi .val small{font-size:13px;color:#64748b;font-weight:600}
.kpi .tip{font-size:11px;color:#64748b;margin-top:6px}
.kpi::before{content:'';position:absolute;left:0;top:0;bottom:0;width:4px}
.kpi.green::before{background:#22c55e}.kpi.yellow::before{background:#eab308}.kpi.red::before{background:#ef4444}.kpi.blue::before{background:#3b82f6}
.section{background:#1e293b;border-radius:14px;padding:20px;margin-bottom:18px;border:1px solid #334155}
.section-title{font-size:16px;font-weight:700;margin-bottom:14px;display:flex;align-items:center;gap:8px;color:#f1f5f9}
.section-title .tag{font-size:11px;background:#3b82f6;color:#fff;padding:2px 10px;border-radius:12px;font-weight:600}
.grid-2{display:grid;grid-template-columns:1fr 1fr;gap:18px}
.grid-3{display:grid;grid-template-columns:1fr 1fr 1fr;gap:18px}
table{width:100%;border-collapse:collapse;font-size:13px}
th{text-align:left;padding:9px 10px;background:#0f172a;color:#94a3b8;font-weight:600;border-bottom:1px solid #334155;font-size:12px;position:sticky;top:0}
td{padding:9px 10px;border-bottom:1px solid #2d3a4e}
tr:hover td{background:#263348}
.badge{display:inline-block;padding:2px 10px;border-radius:12px;font-size:11px;font-weight:700}
.bg-green{background:#16a34a33;color:#4ade80}.bg-red{background:#dc262633;color:#f87171}.bg-yellow{background:#ca8a0433;color:#fbbf24}.bg-blue{background:#3b82f633;color:#60a5fa}
.rank-num{font-size:16px;font-weight:800}
.light{display:inline-block;width:12px;height:12px;border-radius:50%;margin-right:6px;vertical-align:middle}
.lg{background:#22c55e}.ly{background:#eab308}.lr{background:#ef4444}
.pbar{height:10px;background:#334155;border-radius:6px;overflow:hidden}
.pfill{height:100%;border-radius:6px;transition:width .6s}
.act-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px}
.act-card{background:#0f172a;border-radius:12px;padding:14px;text-align:center;border:1px solid #334155}
.act-card .icon{font-size:26px}
.act-card .name{font-size:13px;color:#94a3b8;margin:6px 0 2px}
.act-card .rate{font-size:22px;font-weight:800}
.act-card .done{font-size:11px;color:#64748b}
.store-tag{display:inline-flex;align-items:center;gap:6px;padding:6px 12px;border-radius:10px;font-size:13px;margin:4px;font-weight:600}
.st-red{background:#dc262633;color:#f87171;border:1px solid #dc262666}
.st-green{background:#16a34a33;color:#4ade80;border:1px solid #16a34a66}
.heat-wrap{overflow-x:auto}
.heat-table td,.heat-table th{padding:4px 6px;font-size:11px;text-align:center;white-space:nowrap}
.heat-cell{display:inline-block;width:26px;height:26px;line-height:26px;border-radius:5px;font-size:10px;font-weight:700}
.h0{background:#450a0a;color:#f87171}.h1{background:#7f1d1d;color:#fca5a5}.h2{background:#991b1b;color:#fecaca}
.h3{background:#b45309;color:#fde68a}.h4{background:#a16207;color:#fef3c7}
.h5{background:#166534;color:#bbf7d0}.h6{background:#15803d;color:#dcfce7}.h7{background:#16a34a;color:#f0fdf4}
.todo{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:10px}
.todo-item{display:flex;align-items:center;gap:10px;background:#0f172a;padding:12px 14px;border-radius:10px;border:1px solid #334155}
.todo-item .ck{width:22px;height:22px;border-radius:6px;display:flex;align-items:center;justify-content:center;font-size:14px;font-weight:800;flex-shrink:0}
.ck-ok{background:#16a34a33;color:#4ade80;border:2px solid #22c55e}
.ck-no{background:#dc262633;color:#f87171;border:2px solid #dc2626}
.todo-item .nm{font-size:13px;font-weight:600;flex:1}
.todo-item .rt{font-size:12px;color:#94a3b8}
.reward-card{display:flex;align-items:center;gap:14px;padding:14px;background:#0f172a;border-radius:12px;border:1px solid #334155;margin-bottom:10px}
.reward-card .medal{font-size:30px}
.reward-card .info{flex:1}
.reward-card .info .nm{font-weight:700;font-size:14px}
.reward-card .info .ds{font-size:12px;color:#94a3b8;margin-top:2px}
.reward-card .amt{font-size:20px;font-weight:800;color:#fbbf24}
.search-box{display:flex;gap:10px;margin-bottom:16px}
.search-box input{flex:1;padding:12px 16px;border-radius:10px;border:1px solid #334155;background:#0f172a;color:#e2e8f0;font-size:15px;outline:none}
.search-box input:focus{border-color:#3b82f6}
.search-box button{padding:12px 24px;border-radius:10px;background:#3b82f6;color:#fff;border:none;font-size:14px;font-weight:600;cursor:pointer}
.hl-row{background:#3b82f633 !important;border-left:3px solid #3b82f6}
.banner{border-radius:12px;padding:14px 18px;margin-bottom:18px;font-size:14px;display:flex;align-items:center;gap:10px}
.banner-red{background:#dc262633;border:1px solid #dc262666;color:#fecaca}
.banner-green{background:#16a34a33;border:1px solid #16a34a66;color:#bbf7d0}
@media(max-width:768px){.grid-2,.grid-3{grid-template-columns:1fr}.hero{flex-direction:column;text-align:center}.hero-right{text-align:center}}
</style>
</head>
<body>

<div class="hero">
  <div>
    <h1>🏪 贵阳8月老板电器 · 门店动作执行看板</h1>
    <div class="sub">项目周期 8.06-8.31 ｜ 让每个门店每天都能看到：今天你做了没有？</div>
  </div>
  <div class="hero-right">
    <div class="update-badge"><span class="pulse"></span> 数据更新至 ''' + D['updated'] + '''</div>
    <div style="margin-top:6px">统计周期：''' + ' / '.join(dates) + '''（''' + str(D['n_days']) + '''天）｜ 基础项满分 50分/天</div>
  </div>
</div>
''')

    # ===== 全局业绩横幅（每页可见） =====
    if has_perf:
        perf_total = PERF.get('total') or {}
        g_target = perf_total.get('target', 0)
        g_done = perf_total.get('done', 0)
        g_rate = perf_total.get('rate', 0) * 100
        g_time = PERF.get('time_pct', 0)
        g_diff = perf_total.get('diff', 0)
        g_remain = PERF.get('remain_days', 0)
        g_daily = g_diff / g_remain if g_remain > 0 else 0
        g_color = '#4ade80' if g_rate >= g_time else '#fbbf24'
        A.append(f'''<div style="background:#1e293b;border:2px solid #334155;border-radius:0;padding:10px 24px;display:flex;align-items:center;gap:20px;flex-wrap:wrap;font-size:13px">
  <span style="color:#94a3b8">📈 业绩达成</span>
  <span style="font-weight:800;font-size:16px;color:{g_color}">{g_rate:.1f}%</span>
  <div class="pbar" style="flex:1;min-width:120px"><div class="pfill" style="width:{min(g_rate,100)}%;background:{g_color}"></div></div>
  <span style="color:#94a3b8">时间进度 <b style="color:#fbbf24">{g_time}%</b></span>
  <span style="color:#94a3b8">完成 <b style="color:#4ade80">{g_done/10000:.1f}万</b> / 目标 <b style="color:#e2e8f0">{g_target/10000:.1f}万</b></span>
  <span style="color:#94a3b8">还差 <b style="color:#f87171">{g_diff/10000:.1f}万</b> · 剩{g_remain}天 · 日均需<b style="color:#fbbf24">{g_daily/10000:.1f}万</b></span>
</div>''')

    A.append('<div class="nav">\n')
    if has_perf:
        A.append('  <button class="active" onclick="go(0)">📈 业绩达成</button>')
    tb_cls = 'active' if not has_perf else ''
    A.append(f'  <button class="{tb_cls}" onclick="go({off})">🚦 今日战报</button>')
    A.append(f'  <button onclick="go({off+1})">🏆 门店排行</button>')
    A.append(f'  <button onclick="go({off+2})">🎯 核心策略落地情况</button>')
    A.append(f'  <button onclick="go({off+3})">💰 积分与奖励</button>')
    A.append('</div>')

    # ===== 业绩达成页（可选） =====
    if has_perf:
        perf_total = PERF.get('total') or {}
        target = perf_total.get('target', 0)
        done = perf_total.get('done', 0)
        rate = perf_total.get('rate', 0)
        diff = perf_total.get('diff', 0)
        time_pct = PERF.get('time_pct', 0)
        remain_days = PERF.get('remain_days', 0)
        need_daily = diff / remain_days if remain_days > 0 else 0
        rate_pct = rate * 100
        rate_color = '#4ade80' if rate_pct >= time_pct else '#f87171'
        A.append('<div id="page0" class="page active">')
        A.append(f'''
<div class="kpi-row">
  <div class="kpi blue"><div class="lab">🎯 业绩总目标</div><div class="val">{target/10000:.0f}<small> 万</small></div><div class="tip">项目期 8.06-8.31</div></div>
  <div class="kpi green"><div class="lab">✅ 已完成业绩</div><div class="val" style="color:#4ade80">{done/10000:.1f}<small> 万</small></div><div class="tip">占目标 {rate_pct:.1f}%</div></div>
  <div class="kpi yellow"><div class="lab">⏳ 时间进度</div><div class="val" style="color:#fbbf24">{time_pct}%</div><div class="tip">剩余 {remain_days} 天</div></div>
  <div class="kpi red"><div class="lab">📉 还差</div><div class="val" style="color:#f87171">{diff/10000:.1f}<small> 万</small></div><div class="tip">每天要干 {need_daily/10000:.1f} 万才能达标</div></div>
</div>
<div class="banner banner-red">🚨 <b>达成率 {rate_pct:.1f}% vs 时间进度 {time_pct}%</b> —— 落后 {max(0,time_pct-rate_pct):.1f} 个百分点，剩下 {remain_days} 天，日均要完成 {need_daily/10000:.1f} 万，冲起来！</div>
<div class="section"><div class="section-title">📊 业绩达成进度 <span class="tag">绿色=达标 · 红色=落后</span></div>
  <div style="display:flex;align-items:center;gap:14px;margin-bottom:8px">
    <div style="width:120px;font-size:13px;color:#94a3b8">📈 达成率</div>
    <div class="pbar" style="flex:1"><div class="pfill" style="width:{min(rate_pct,100)}%;background:{rate_color}"></div></div>
    <div style="width:70px;text-align:right;font-weight:800;color:{rate_color}">{rate_pct:.1f}%</div>
  </div>
  <div style="display:flex;align-items:center;gap:14px">
    <div style="width:120px;font-size:13px;color:#94a3b8">⏳ 时间进度</div>
    <div class="pbar" style="flex:1"><div class="pfill" style="width:{min(time_pct,100)}%;background:#fbbf24"></div></div>
    <div style="width:70px;text-align:right;font-weight:800;color:#fbbf24">{time_pct}%</div>
  </div>
</div>
<div class="section"><div class="section-title">🏢 渠道业绩达成 <span class="tag">看谁在扛任务</span></div><table><tr><th>负责老师</th><th>区域/渠道</th><th>目标</th><th>已完成</th><th>达成率</th><th>差额</th></tr>''')
        for r in PERF.get('rows', []):
            rt = r.get('rate', 0) * 100
            rc = '#4ade80' if rt >= 50 else ('#fbbf24' if rt >= 30 else '#f87171')
            A.append(f'<tr><td><b>{r.get("teacher","") or "合计"}</b></td><td>{r.get("region","")}</td><td>{r.get("target",0)/10000:.1f}万</td><td>{r.get("done",0)/10000:.1f}万</td><td><span style="font-weight:800;color:{rc}">{rt:.1f}%</span></td><td style="color:#f87171">{r.get("diff",0)/10000:.1f}万</td></tr>')
        A.append('</table></div>')
        # ===== 区域排名 =====
        if has_rank and RANK.get('regions'):
            A.append('<div class="section"><div class="section-title">🗺️ 区域排名 <span class="tag">按完成率排序</span></div><div class="table-wrap" style="max-height:300px;overflow-y:auto"><table><tr><th>#</th><th>区域</th><th>目标</th><th>已完成</th><th>完成率</th></tr>')
            for i, c in enumerate(RANK['regions'][:10], 1):
                rc = '#4ade80' if c['rate'] >= 0.5 else ('#fbbf24' if c['rate'] >= 0.3 else '#f87171')
                medal = '🥇' if i == 1 else ('🥈' if i == 2 else ('🥉' if i == 3 else str(i)))
                A.append(f'<tr><td>{medal}</td><td><b>{c["name"]}</b></td><td>{c["target"]/10000:.1f}万</td><td>{c["done"]/10000:.1f}万</td><td><span style="font-weight:800;color:{rc}">{c["rate"]*100:.1f}%</span></td></tr>')
            A.append('</table></div></div>')
        # ===== 军长排名 =====
        if has_rank and RANK.get('juns'):
            A.append('<div class="section"><div class="section-title">👑 军长排名 <span class="tag">按完成率排序</span></div><div class="table-wrap" style="max-height:260px;overflow-y:auto"><table><tr><th>#</th><th>军长</th><th>目标</th><th>已完成</th><th>完成率</th></tr>')
            for i, c in enumerate(RANK['juns'][:10], 1):
                rc = '#4ade80' if c['rate'] >= 0.5 else ('#fbbf24' if c['rate'] >= 0.3 else '#f87171')
                medal = '🥇' if i == 1 else ('🥈' if i == 2 else ('🥉' if i == 3 else str(i)))
                A.append(f'<tr><td>{medal}</td><td><b>{c["name"]}</b></td><td>{c["target"]/10000:.1f}万</td><td>{c["done"]/10000:.1f}万</td><td><span style="font-weight:800;color:{rc}">{c["rate"]*100:.1f}%</span></td></tr>')
            A.append('</table></div></div>')
        # ===== 渠道排名 =====
        if has_rank and RANK.get('channels'):
            A.append('<div class="section"><div class="section-title">🥇 渠道排名 <span class="tag">按完成率排序</span></div><div class="table-wrap" style="max-height:320px;overflow-y:auto"><table><tr><th>#</th><th>渠道</th><th>目标</th><th>已完成</th><th>完成率</th></tr>')
            for i, c in enumerate(RANK['channels'][:16], 1):
                rc = '#4ade80' if c['rate'] >= 0.5 else ('#fbbf24' if c['rate'] >= 0.3 else '#f87171')
                medal = '🥇' if i == 1 else ('🥈' if i == 2 else ('🥉' if i == 3 else str(i)))
                A.append(f'<tr><td>{medal}</td><td><b>{c["name"]}</b></td><td>{c["target"]/10000:.1f}万</td><td>{c["done"]/10000:.1f}万</td><td><span style="font-weight:800;color:{rc}">{c["rate"]*100:.1f}%</span></td></tr>')
            A.append('</table></div></div>')
        # ===== 门店A组/B组排名 =====
        if has_rank and (RANK.get('groupA') or RANK.get('groupB')):
            A.append('<div class="grid-2">')
            for gname, gkey in [('🏅 门店A组排名', 'groupA'), ('🌱 门店B组排名', 'groupB')]:
                arr = RANK.get(gkey, [])[:15]
                A.append(f'<div class="section"><div class="section-title">{gname}<span class="tag">TOP{len(arr)}</span></div><div class="table-wrap" style="max-height:340px;overflow-y:auto"><table><tr><th>#</th><th>门店</th><th>区域</th><th>完成率</th><th>完成/目标</th></tr>')
                for i, s in enumerate(arr, 1):
                    rc = '#4ade80' if s['rate'] >= 0.5 else ('#fbbf24' if s['rate'] >= 0.3 else '#f87171')
                    medal = '🥇' if i == 1 else ('🥈' if i == 2 else ('🥉' if i == 3 else str(i)))
                    A.append(f'<tr><td>{medal}</td><td><b>{s["store"]}</b></td><td style="font-size:11px;color:#94a3b8">{s.get("region","")}</td><td><span style="font-weight:800;color:{rc}">{s["rate"]*100:.1f}%</span></td><td style="font-size:11px">{s["done"]/10000:.1f}/{s["target"]/10000:.1f}万</td></tr>')
                A.append('</table></div></div>')
            A.append('</div>')
        # ===== 军师长PK =====
        if has_rank and RANK.get('junshi'):
            A.append('<div class="section"><div class="section-title">👥 军长/师长 PK <span class="tag">比谁带兵能打</span></div><div class="table-wrap" style="max-height:300px;overflow-y:auto"><table><tr><th>#</th><th>军长</th><th>师长</th><th>渠道</th><th>目标</th><th>已完成</th><th>完成率</th></tr>')
            js = sorted(RANK['junshi'], key=lambda x: -x['rate'])
            for i, j in enumerate(js, 1):
                rc = '#4ade80' if j['rate'] >= 0.5 else ('#fbbf24' if j['rate'] >= 0.3 else '#f87171')
                medal = '🥇' if i == 1 else ('🥈' if i == 2 else ('🥉' if i == 3 else str(i)))
                A.append(f'<tr><td>{medal}</td><td><b>{j.get("jun","") or "—"}</b></td><td>{j.get("shi","") or "—"}</td><td>{j.get("ch","")}</td><td>{j["target"]/10000:.1f}万</td><td>{j["done"]/10000:.1f}万</td><td><span style="font-weight:800;color:{rc}">{j["rate"]*100:.1f}%</span></td></tr>')
            A.append('</table></div></div>')
        A.append('</div>')

    # ===== 今日战报 =====
    A.append(f'<div id="page{off}" class="page{" active" if not has_perf else ""}">')
    pass_cnt = len(pass_today)
    rate = round(pass_cnt/N*100) if N else 0
    A.append(f'''
<div class="kpi-row">
  <div class="kpi blue"><div class="lab">参与门店</div><div class="val">{N}<small> 家</small></div><div class="tip">覆盖 7 大区域</div></div>
  <div class="kpi green"><div class="lab">今日达标门店（≥30分）</div><div class="val" style="color:#4ade80">{pass_cnt}<small> 家</small></div><div class="tip">达标率 {rate}%</div></div>
  <div class="kpi red"><div class="lab">今日零分门店</div><div class="val" style="color:#f87171">{len(zero_today)}<small> 家</small></div><div class="tip">一项动作都没做 ⚠️</div></div>
  <div class="kpi yellow"><div class="lab">今日动作完成率</div><div class="val" style="color:#fbbf24">{round(sum(t['total'] for t in TODAY)/N/50*100) if N else 0}%</div><div class="tip">日均{round(sum(t['total'] for t in TODAY)/N,1) if N else 0}分 / 满分50分</div></div>
  <div class="kpi blue"><div class="lab">{phase_n}天阶段累计积分</div><div class="val">{phase_score:,}</div><div class="tip">第二阶段 8.17-8.{phase_end}</div></div>
</div>''')
    if len(zero_today) > 0:
        names = '、'.join([t['store'] for t in zero_today[:8]])
        more = f" 等{len(zero_today)}家" if len(zero_today) > 8 else ''
        A.append(f'<div class="banner banner-red">🚨 <b>今天还没动作的 {len(zero_today)} 家门店：</b>{names}{more} —— 老板电器项目，动作就是分数，分数就是钱！</div>')
    else:
        A.append('<div class="banner banner-green">🎉 今天所有门店都有动作，继续保持！</div>')

    A.append('<div class="section"><div class="section-title">✅ 今天这 8 件事，做了几件？<span class="tag">全门店完成率</span></div><div class="todo">')
    for name, icon in ACT_ICONS:
        done = act_done.get(name, 0)
        pct = round(done/N*100) if N else 0
        cls = 'ck-ok' if pct >= 50 else 'ck-no'
        mark = '✓' if pct >= 50 else '✗'
        A.append(f'<div class="todo-item"><div class="ck {cls}">{mark}</div><div class="nm">{icon} {name}</div><div class="rt">{done}/{N} 家 · <b>{pct}%</b></div></div>')
    A.append('</div></div>')

    A.append('<div class="section"><div class="section-title">🚦 各区域今天做得怎么样？<span class="tag">绿灯=达标过半 · 红灯=要加油</span></div><div class="grid-2">')
    jun_map = {}
    for s in stores_daily:
        jun_map.setdefault(s['region'], s['jun'])
    for reg in reg_order:
        if reg not in reg_today: continue
        d, t = reg_today[reg]
        pct = round(d/t*100) if t else 0
        color = reg_colors.get(reg, '#94a3b8')
        light = 'lg' if pct >= 50 else ('ly' if pct >= 30 else 'lr')
        A.append(f'''<div style="background:#0f172a;border-radius:12px;padding:14px 16px;border-left:4px solid {color}">
      <div style="display:flex;justify-content:space-between;align-items:center">
        <div style="font-size:15px;font-weight:700"><span class="light {light}"></span>{reg}</div>
        <div style="font-size:12px;color:#94a3b8">军长：{jun_map.get(reg,'')}</div>
      </div>
      <div style="display:flex;justify-content:space-between;margin-top:8px;font-size:12px;color:#94a3b8">
        <span>今日达标 {d}/{t} 家</span><span style="font-weight:700;color:{color}">{pct}%</span>
      </div>
      <div class="pbar" style="margin-top:8px"><div class="pfill" style="width:{pct}%;background:{color}"></div></div>
    </div>''')
    A.append('</div></div>')

    A.append('<div class="grid-2"><div class="section"><div class="section-title">🔥 今日动作之星 TOP5</div><table><tr><th>#</th><th>门店</th><th>今日得分</th><th>状态</th></tr>')
    medals = ['🥇','🥈','🥉','4','5']
    for i, t in enumerate(top_today[:5]):
        A.append(f'<tr><td class="rank-num" style="color:#fbbf24">{medals[i]}</td><td><b>{t["store"]}</b><br><span style="font-size:11px;color:#64748b">{t["region"]}</span></td><td style="font-size:16px;font-weight:800;color:#4ade80">{t["total"]} 分</td><td><span class="badge bg-green">达标 ✓</span></td></tr>')
    A.append('</table></div>')
    A.append('<div class="section"><div class="section-title">📢 今天被点名的门店</div>')
    if zero_today:
        for t in zero_today:
            A.append(f'<span class="store-tag st-red">❌ {t["store"]}</span>')
    else:
        A.append('<div style="color:#4ade80;font-size:14px">🎉 无零分门店！</div>')
    A.append('</div></div>')

    # 进步门店 / 退步门店
    A.append('<div class="grid-2">')
    A.append('<div class="section"><div class="section-title">🟢 进步的门店 <span class="tag">越来越好 ↑</span></div>')
    if progress_stores:
        for t in progress_stores:
            A.append(f'<span class="store-tag st-green">↑ {t["store"]} <span style="opacity:.7">+{t["change"]}</span></span>')
        A.append('<div style="font-size:11px;color:#64748b;margin-top:8px">对比：前后半段日均积分上升 &gt;5分</div>')
    else:
        A.append('<div style="color:#4ade80;font-size:14px">暂无显著进步门店</div>')
    A.append('</div>')
    A.append('<div class="section"><div class="section-title">🔴 退步的门店 <span class="tag">越来越差 ↓</span></div>')
    if decline_stores:
        for t in decline_stores:
            A.append(f'<span class="store-tag st-red">↓ {t["store"]} <span style="opacity:.7">{t["change"]}</span></span>')
        A.append('<div style="font-size:11px;color:#64748b;margin-top:8px">对比：前后半段日均积分下降 &gt;3分</div>')
    else:
        A.append('<div style="color:#4ade80;font-size:14px">暂无显著退步门店</div>')
    A.append('</div></div>')
    A.append('</div>')

    # ===== 门店排行 =====
    A.append(f'<div id="page{off+1}" class="page">')
    A.append('<div class="search-box"><input id="searchInput" placeholder="🔍 输入门店名称，看你的排名和分数（例如：红星一店）"><button onclick="searchStore()">查我的门店</button></div>')
    A.append('<div id="searchResult" style="margin-bottom:18px"></div>')
    A.append('<div class="grid-3">')
    for gname, gkey in [('⭐ S组 头部标杆','S组'), ('🏅 A组 中坚力量','A组'), ('🌱 B组 潜力阵营','B组')]:
        arr = ranks.get(gkey, [])
        A.append(f'<div class="section"><div class="section-title">{gname}<span class="tag">{len(arr)}家</span></div><div class="table-wrap" style="max-height:520px;overflow-y:auto"><table><tr><th>#</th><th>门店</th><th>积分</th><th>日均</th><th>奖励</th></tr>')
        for r in arr:
            reward = f'<span class="badge bg-green">¥{r["reward"]}</span>' if r.get('reward') else ''
            medal = '🥇' if r['rank']==1 else ('🥈' if r['rank']==2 else ('🥉' if r['rank']==3 else str(r['rank'])))
            A.append(f'<tr data-store="{htmlmod.escape(str(r["store"]))}"><td>{medal}</td><td><b>{htmlmod.escape(str(r["store"]))}</b></td><td style="font-weight:700">{r["score"]}</td><td>{r["daily_avg"]}</td><td>{reward}</td></tr>')
        A.append('</table></div></div>')
    A.append('</div></div>')

    # ===== 每日打卡 =====
    A.append(f'<div id="page{off+2}" class="page">')
    # 核心策略落地情况（内容推广条数 + 活动落地场次）
    strat = D.get('strategy_daily') or {}
    strat_labels = strat.get('labels', dates)
    strat_content = strat.get('content', [0]*len(dates))
    strat_activity = strat.get('activity', [0]*len(dates))
    A.append('<div class="section"><div class="section-title">🎯 核心策略落地情况 <span class="tag">内容推广条数 + 活动落地场次 · 核心策略＝内容推广＋活动落地</span></div><div style="height:240px"><canvas id="strategyChart"></canvas></div></div>')
    A.append('<div class="section"><div class="section-title">📈 全门店每日总积分走势 <span class="tag">看看大家是不是越干越有劲</span></div><div style="height:260px"><canvas id="trendChart"></canvas></div></div>')
    A.append('<div class="section"><div class="section-title">🗓️ 每日打卡热力图 <span class="tag">绿=做得好 · 红=没做 · 点自己门店那行看</span></div><div class="heat-wrap"><table class="heat-table"><tr><th>门店</th>')
    for d in dates:
        A.append(f'<th>{d}</th>')
    A.append('<th>阶段合计</th></tr>')
    for s in sorted(stores_daily, key=lambda x: -x['total']):
        A.append(f'<tr data-store="{htmlmod.escape(str(s["store"]))}"><td style="text-align:left"><b>{htmlmod.escape(str(s["store"]))}</b> <span style="color:#64748b;font-size:10px">{s["group"]}</span></td>')
        for v in s['daily']:
            if v == 0: cls, disp = 'h0', '0'
            elif v <= 20: cls, disp = 'h1', str(v)
            elif v <= 35: cls, disp = 'h2', str(v)
            elif v <= 50: cls, disp = 'h3', str(v)
            elif v <= 70: cls, disp = 'h4', str(v)
            elif v <= 90: cls, disp = 'h5', str(v)
            elif v <= 110: cls, disp = 'h6', str(v)
            else: cls, disp = 'h7', str(v)
            A.append(f'<td><span class="heat-cell {cls}">{disp}</span></td>')
        tot = s['phase_total'] if phase_active else s['total']
        totcls = 'h7' if tot>=400 else ('h5' if tot>=200 else ('h3' if tot>=100 else 'h0'))
        A.append(f'<td><span class="heat-cell {totcls}">{tot}</span></td></tr>')
    A.append('</table></div></div>')
    A.append('</div>')

    # ===== 积分与奖励 =====
    A.append(f'<div id="page{off+3}" class="page">')
    A.append('<div class="section"><div class="section-title">💡 积分规则 —— 大白话版 <span class="tag">做了就有分，不做就是0</span></div><div class="grid-2">')
    A.append('''<div>
<div style="font-size:14px;font-weight:700;margin-bottom:10px">📌 每天必做 8 件事（每天最多 50 分）</div>
<table><tr><th>动作</th><th>怎么做</th><th>得分</th></tr>
<tr><td>🌅 晨会</td><td>早上开会打卡</td><td><span class="badge bg-blue">5分</span></td></tr>
<tr><td>🌆 夕会</td><td>晚上总结打卡</td><td><span class="badge bg-blue">5分</span></td></tr>
<tr><td>📖 每日一读</td><td>读学习资料</td><td><span class="badge bg-blue">5分</span></td></tr>
<tr><td>📏 上门量尺</td><td>去客户家量尺</td><td><span class="badge bg-blue">10分/组</span></td></tr>
<tr><td>📅 KDS预约</td><td>约客户到店</td><td><span class="badge bg-blue">10分/组</span></td></tr>
<tr><td>👤 新增客资</td><td>收集新客户信息</td><td><span class="badge bg-blue">5分/组</span></td></tr>
<tr><td>📕 小红书截流</td><td>小红书引客户</td><td><span class="badge bg-blue">10分/人</span></td></tr>
<tr><td>🎉 捷报</td><td>成交了报喜</td><td><span class="badge bg-blue">2分/品类</span></td></tr>
</table></div>
<div>
<div style="font-size:14px;font-weight:700;margin-bottom:10px">➕ 每周加餐动作（额外加分）</div>
<table><tr><th>动作</th><th>时间</th><th>得分</th></tr>
<tr><td>🎬 抖音宣发</td><td>周二/周四</td><td><span class="badge bg-green">+10分/条</span></td></tr>
<tr><td>📕 小红书发布</td><td>周二</td><td><span class="badge bg-green">+10分/条</span></td></tr>
<tr><td>📞 老用户回访</td><td>周三/周五</td><td><span class="badge bg-green">+5分/人</span></td></tr>
<tr><td>🎪 周末活动落地</td><td>周末</td><td><span class="badge bg-green">+20分</span></td></tr>
<tr><td>🤝 渠道活动落地</td><td>周中</td><td><span class="badge bg-green">+20分</span></td></tr>
</table>
<div style="margin-top:14px;padding:14px;background:#0f172a;border-radius:12px;border:1px solid #334155">
<div style="font-size:14px;font-weight:700;margin-bottom:8px">💪 怎么当第一名？</div>
<div style="font-size:13px;color:#94a3b8;line-height:1.9">
1️⃣ 每天 8 件必做件件不落（50分/天）<br>
2️⃣ 周二周四发抖音、周二发小红书<br>
3️⃣ 周三周五回访老客户<br>
4️⃣ 周末一定落地活动（+20分）<br>
5️⃣ 成交马上发捷报 🎉
</div>
</div>
</div></div></div>''')

    A.append('<div class="section"><div class="section-title">🏆 分组奖励 —— 每月发钱 <span class="tag">按积分排名</span></div><div class="grid-3">')
    for gname, gkey, emoji in [('S组','S组','⭐'),('A组','A组','🏅'),('B组','B组','🌱')]:
        arr = ranks.get(gkey, [])
        A.append(f'<div><div style="font-size:14px;font-weight:700;margin-bottom:10px">{emoji} {gname}</div>')
        for i, r in enumerate(arr[:5]):
            amt = r['reward'] if r.get('reward') else 0
            medal = '🥇' if i==0 else ('🥈' if i==1 else ('🥉' if i==2 else f'第{i+1}名'))
            A.append(f'<div class="reward-card"><div class="medal">{medal}</div><div class="info"><div class="nm">{htmlmod.escape(str(r["store"]))}</div><div class="ds">{r["score"]}分 · 日均{r["daily_avg"]}</div></div><div class="amt">¥{amt}</div></div>')
        A.append('</div>')
    A.append('</div><div style="margin-top:14px;padding:14px 18px;background:linear-gradient(90deg,#422006,#713f12);border:2px solid #f59e0b;border-radius:12px;font-size:15px;font-weight:800;color:#fbbf24;text-align:center">🏆 S组前5 / A组前5 / B组前8 都有奖金（300/200/100/50元）—— 每天认真做，下个月站上领奖台的就是你！💪</div></div>')
    A.append('</div>')

    # ===== JS =====
    A.append('''
<script>
const pages = ['page0','page1','page2','page3','page4'].slice(0, __NPAGES__);
function go(i){
  pages.forEach((p,idx)=>{document.getElementById(p).classList.toggle('active',idx===i)});
  document.querySelectorAll('.nav button').forEach((b,idx)=>b.classList.toggle('active',idx===i));
}
function searchStore(){
  const q = document.getElementById('searchInput').value.trim();
  const res = document.getElementById('searchResult');
  if(!q){res.innerHTML='';return;}
  document.querySelectorAll('tr[data-store]').forEach(tr=>tr.classList.remove('hl-row'));
  let found = 0;
  document.querySelectorAll('tr[data-store]').forEach(tr=>{
    if(tr.dataset.store.includes(q)){
      tr.classList.add('hl-row'); found++;
      tr.scrollIntoView({behavior:'smooth',block:'center'});
    }
  });
  if(found){
    res.innerHTML = `<div class="banner banner-green">✅ 找到 <b>${found}</b> 个匹配门店，已高亮显示（蓝色底纹）！</div>`;
  }else{
    res.innerHTML = `<div class="banner banner-red">❌ 没找到「${q}」，检查一下名字，或直接看下面排行榜/热力图</div>`;
  }
}
new Chart(document.getElementById('strategyChart'), {
  type:'bar',
  data:{labels:__STRAT_LABELS__, datasets:[
    {label:'内容推广条数', data:__CONTENT__, backgroundColor:'rgba(139,92,246,0.7)', borderRadius:4},
    {label:'活动落地场次', data:__ACTIVITY__, backgroundColor:'rgba(251,191,36,0.7)', borderRadius:4}
  ]},
  options:{
    plugins:{legend:{labels:{color:'#94a3b8'}}},
    scales:{
      y:{beginAtZero:true, grid:{color:'#334155'}, ticks:{color:'#94a3b8'}},
      x:{grid:{color:'#334155'}, ticks:{color:'#94a3b8'}}
    }
  }
});
new Chart(document.getElementById('trendChart'), {
  type:'line',
  data:{labels:__DATES__, datasets:[{
    label:'每日总积分', data:__TOTAL__,
    borderColor:'#3b82f6', backgroundColor:'rgba(59,130,246,0.15)',
    fill:true, tension:0.35, borderWidth:3, pointRadius:5, pointBackgroundColor:'#3b82f6'
  }]},
  options:{
    plugins:{legend:{labels:{color:'#94a3b8'}}},
    scales:{
      y:{beginAtZero:true, grid:{color:'#334155'}, ticks:{color:'#94a3b8'}},
      x:{grid:{color:'#334155'}, ticks:{color:'#94a3b8'}}
    }
  }
});
</script>
</body>
</html>
''')

    html_str = ''.join(A)
    html_str = html_str.replace('__DATES__', json.dumps(dates, ensure_ascii=False))
    html_str = html_str.replace('__TOTAL__', json.dumps(daily_total))
    html_str = html_str.replace('__STRAT_LABELS__', json.dumps(strat_labels, ensure_ascii=False))
    html_str = html_str.replace('__CONTENT__', json.dumps(strat_content))
    html_str = html_str.replace('__ACTIVITY__', json.dumps(strat_activity))
    html_str = html_str.replace('__NPAGES__', str(4 + off))
    with open(out_path, 'w') as f:
        f.write(html_str)
    print(f"✅ 看板已生成: {out_path} ({len(html_str):,} bytes)")
    return out_path

if __name__ == '__main__':
    data_path = sys.argv[1] if len(sys.argv) > 1 else 'guiyang_data.json'
    perf_path = sys.argv[2] if len(sys.argv) > 2 else None
    out_path = sys.argv[3] if len(sys.argv) > 3 else '贵阳8月_门店动作执行看板.html'
    build(data_path, perf_path, out_path)
