# -*- coding: utf-8 -*-
"""深圳样板18L燃热交付看板：新增「沉淀资产·工具包」标签页"""
import io, sys

PATH = '深圳样板_18L燃热交付看板.html'
html = io.open(PATH, encoding='utf-8').read()

# ---------- 1. CSS：标签页导航样式 ----------
css_anchor = '.page{padding:20px;max-width:1400px;margin:0 auto}'
assert html.count(css_anchor) == 1, 'css anchor not unique/found'
css_add = css_anchor + '''
.tabnav{max-width:1400px;margin:16px auto 0;padding:0 20px;display:flex;gap:10px;flex-wrap:wrap}
.tabbtn{cursor:pointer;border:1px solid #334155;background:#1e293b;color:#94a3b8;padding:10px 24px;border-radius:12px;font-size:14px;font-weight:700;font-family:inherit;transition:all .2s}
.tabbtn:hover{color:#f1f5f9;border-color:#f97316}
.tabbtn.active{background:linear-gradient(135deg,#ea580c,#f97316);border-color:#f97316;color:#fff;box-shadow:0 2px 10px #f9731655}'''
html = html.replace(css_anchor, css_add)

# ---------- 2. 主内容包为 tab-main，并在其前插入 tab 导航 ----------
page_anchor = '<div class="page">'
assert html.count(page_anchor) == 1, 'page anchor not unique/found'
tabs_html = '''<div class="tabnav">
  <button class="tabbtn active" id="tbMain" onclick="showTab('main')">📊 交付总览</button>
  <button class="tabbtn" id="tbAssets" onclick="showTab('assets')">📦 沉淀资产 · 工具包</button>
</div>
'''
html = html.replace(page_anchor, tabs_html + '<div class="page" id="view-main">')

# ---------- 3. 沉淀资产页内容 ----------
assets_html = '''
<!-- ================= 沉淀资产·工具包 标签页 ================= -->
<div class="page" id="view-assets" style="display:none">

<div class="banner banner-green">📦 <b>沉淀目标：</b>打样期 9.2-10.7 收官时，交付「可全国复制的样板打法 + 终端工具包」。本页汇总<b>目前已沉淀的工具/内容</b>，随项目推进持续更新（最近盘点：2026-09-07）。</div>

<div class="kpi-row">
  <div class="kpi orange"><div class="lab">📕 话术手册迭代</div><div class="val">V4→V7</div><div class="tip">8/26-9/1 · 含场景总览</div></div>
  <div class="kpi green"><div class="lab">📗 实战案例归档</div><div class="val">3 <small>份</small></div><div class="tip">+1份终端提炼版</div></div>
  <div class="kpi blue"><div class="lab">💼 方法交付件</div><div class="val">4 <small>份</small></div><div class="tip">云文档框架·填写中</div></div>
  <div class="kpi purple"><div class="lab">📊 数据机制</div><div class="val">3 <small>套</small></div><div class="tip">达成表/双排行/积分</div></div>
</div>

<!-- 话术资产 -->
<div class="section">
  <div class="section-title">📕 话术资产（终端话术版本演进线） <span class="tag">核心资产</span></div>
  <table>
    <tr><th>资产</th><th>时间</th><th>要点</th><th>状态</th></tr>
    <tr><td><b>《终端推燃热话术包 V4补充》</b></td><td>8/26</td><td>话术包补充版，走终端接地气方向</td><td><span class="badge bg-orange">已迭代</span></td></tr>
    <tr><td><b>《18L介绍话术 1.0》+《异议应对 1.0》</b></td><td>8/27</td><td>群策群力共创会产出：双卫同洗/出水快/免改表等卖点体系 + 16L升18L价格锚定话术；会议纪要同步归档</td><td><span class="badge bg-green">已沉淀</span></td></tr>
    <tr><td><b>《终端推燃热话术包 V6 接地气版》</b></td><td>8/28</td><td>终端口语化表达迭代（md+docx双格式）</td><td><span class="badge bg-green">已沉淀</span></td></tr>
    <tr><td><b>《燃热750 场景话术总览》+《终端话术与场景手册 V1》</b></td><td>8/28</td><td>按客户场景组织话术（双卫/浴缸/多点用水等）</td><td><span class="badge bg-green">已沉淀</span></td></tr>
    <tr><td><b>《终端推燃热话术手册 V7 定稿版》</b></td><td>9/1</td><td><b>当前主用版本</b>：全员培训/每日晨读/通关考核统一口径</td><td><span class="badge bg-blue">✅ 定稿在用</span></td></tr>
  </table>
</div>

<!-- 启动与培训 -->
<div class="grid-2">
  <div class="section">
    <div class="section-title">🚀 启动与培训材料 <span class="tag green">全员落地</span></div>
    <table>
      <tr><th>材料</th><th>说明</th></tr>
      <tr><td><b>《深圳18L燃热样板-启动会》PPT</b></td><td>9/2 项目启动会 + 产品培训宣贯</td></tr>
      <tr><td><b>启动会手册 V1.0</b></td><td>9/2 定稿，全员培训用（含目标/打法/机制）</td></tr>
      <tr><td><b>终端执行一页纸（积分制）</b></td><td>每日晨读/体验18L/晒单/落地等积分标准（详见总览页）</td></tr>
      <tr><td><b>通关考核 SOP 评分表</b></td><td>老师随机到店听真实讲解打分（9/5-9/10 通关期）</td></tr>
    </table>
  </div>
  <div class="section">
    <div class="section-title">💼 方法论交付件（4份框架） <span class="tag blue">9/5 搭建 · 填写中</span></div>
    <table>
      <tr><th>交付件</th><th>云文档</th><th>用途</th></tr>
      <tr><td><b>① 18L终端推介方案</b></td><td><a href="https://feishu.cn/docx/LkiAdOZw9o65R8xeFgic245rnYc" style="color:#60a5fa">打开 →</a></td><td>推介流程+异议话术库</td></tr>
      <tr><td><b>② 18L终端体验方案</b></td><td><a href="https://feishu.cn/docx/L0mwdGHZdoepXJxPlrWcPEZMnic" style="color:#60a5fa">打开 →</a></td><td>体验区+物料体系</td></tr>
      <tr><td><b>③ 完整版18L销售运营模式</b></td><td><a href="https://feishu.cn/docx/NGkBdvy2yoQmyCx6WzLc0AFVnZe" style="color:#60a5fa">打开 →</a></td><td>全国可复制打法</td></tr>
      <tr><td><b>④ 18L用户调研报告</b></td><td><a href="https://feishu.cn/docx/TsQVdwzQqoSbByxxxV7ctlbDnah" style="color:#60a5fa">打开 →</a></td><td>已购/潜在/竞品用户洞察</td></tr>
    </table>
  </div>
</div>

<!-- 实战案例库 -->
<div class="section">
  <div class="section-title">📗 实战案例库（导购真实成交案例） <span class="tag green">进1份=沉淀1份</span></div>
  <div class="grid-3">
    <div class="ch-card zhuan">
      <h3>宝安华美居 · 彭亮</h3>
      <div class="core">16L升18L异议处理范本（HT750-18）</div>
      <ul>
        <li>老板老客加购；父母家进口林内16L维修3千+放弃</li>
        <li>处理"16L用得好好的干嘛多花几百买18L"异议</li>
        <li>讲解：预混仓±0.1℃恒温/水量伺服/无氧铜水箱对标进口技术</li>
        <li>→ 异议话术库+导购竞赛候选案例</li>
      </ul>
    </div>
    <div class="ch-card ka">
      <h3>宝安华美居 · 宋新英</h3>
      <div class="core">抢林内老客 + 连带全屋套系（U2-i1pro）</div>
      <ul>
        <li>前城滨海花园二手房 3室2厅2卫，原计划买林内</li>
        <li>异议三招：国产技术迭代快（±0.1°vs±3°）→买大不买小→零冷水iPro</li>
        <li>顺带升级烟灶+洗碗机+蒸烤一体全屋套系</li>
        <li>✅ 已出《导购案例提炼》终端学习版（晨读5条话术）</li>
      </ul>
    </div>
    <div class="ch-card jia">
      <h3>龙华万众城 · 刘建生</h3>
      <div class="core">新房婚房双卫 → 16L升级 i1 PRO 18L</div>
      <ul>
        <li>新房婚房客户（父子到店），两卫需求→16L起步</li>
        <li>830-16不满意→转 i1 PRO：装修效果图+半管预热背书</li>
        <li>恒温±0.1°破万和传统3-5°；老客信任+开业价逼单成交</li>
        <li>✅ 与 9/3 捷报开单互证（烟灶消毒柜+18L）</li>
      </ul>
    </div>
  </div>
  <div class="rank-note">📌 案例由项目组收集上传、AI归档提炼（docx→终端学习版），每周优秀案例参评；精华持续注入交付件①话术库。彭亮/宋新英/刘建生 3份已归档，后续进群即沉淀。</div>
</div>

<!-- 数据与机制 -->
<div class="grid-2">
  <div class="section">
    <div class="section-title">📊 数据与机制沉淀</div>
    <table>
      <tr><th>机制</th><th>说明</th><th>状态</th></tr>
      <tr><td><b>数据达成表（日报）</b></td><td>每日捷报口径 xlsx（燃热全量+18L分台）→ 看板自动更新</td><td><span class="badge bg-green">运行中</span></td></tr>
      <tr><td><b>门店销售双排行</b></td><td>燃热排行 + 18L排行（PNG+Excel，9/6起）</td><td><span class="badge bg-green">运行中</span></td></tr>
      <tr><td><b>终端积分周榜</b></td><td>每日积分统计→周度公示→周榜激励（配套一页纸）</td><td><span class="badge bg-yellow">周度公示中</span></td></tr>
      <tr><td><b>里程碑节点验收</b></td><td>9/13 → 45台｜9/20 出样验收｜10/7 收官 100台</td><td><span class="badge bg-blue">按节点</span></td></tr>
    </table>
  </div>
  <div class="section">
    <div class="section-title">🏁 结案沉淀预告 <span class="tag">10/7 收官</span></div>
    <div style="font-size:13px;color:#cbd5e1;line-height:2">
      打样期收官时输出<b>三大结案资产</b>：<br>
      ① <b>样板打法复盘</b> — 四渠道策略效果/里程碑达成/激励复盘；<br>
      ② <b>终端工具包全国复制版</b> — 话术手册+异议手册+执行一页纸+培训课件打包；<br>
      ③ <b>完整版18L销售运营模式</b>（交付件③定稿）— 供全国城市复制落地。<br>
      <span style="color:#64748b">持续进行中：内容官·赖圆章 — 话术/异议手册迭代 ｜ 客户上门采访与案例沉淀 ｜ 交付课件沉淀。</span>
    </div>
  </div>
</div>

</div>
'''

script_anchor = '</div>\n\n<script>'
# 页面结构：...banner-blue的section闭合... </div>(view-main闭合) \n\n <script>
idx = html.rfind('</div>\n\n<script>')
assert idx != -1, 'script anchor not found'
html = html[:idx] + '</div>\n' + assets_html + '\n<script>' + html[idx + len('</div>\n\n<script>'):]

# ---------- 4. 标签页切换 JS ----------
js_anchor = 'var DATA = {'
assert html.count(js_anchor) == 1
show_tab_js = '''function showTab(name){
  var m=document.getElementById('view-main'), a=document.getElementById('view-assets');
  var bm=document.getElementById('tbMain'), ba=document.getElementById('tbAssets');
  if(name==='assets'){ m.style.display='none'; a.style.display=''; bm.classList.remove('active'); ba.classList.add('active'); }
  else { m.style.display=''; a.style.display='none'; ba.classList.remove('active'); bm.classList.add('active'); }
  window.scrollTo(0,0);
}

var DATA = {'''
html = html.replace(js_anchor, show_tab_js)

io.open(PATH, 'w', encoding='utf-8').write(html)
print('OK done. new size =', len(html))
