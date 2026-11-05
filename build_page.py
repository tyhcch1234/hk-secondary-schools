import json, csv, re, html
from theme_rules import school_tags, ORDER as THEME_ORDER

rows = json.load(open('data/schools.json'))
fin = json.load(open('data/final_concerns.json'))
try:
    rep = json.load(open('data/reports/parsed2.json'))
except Exception:
    rep = {}
try:
    summ = json.load(open('data/reports/summaries.json'))
except Exception:
    summ = {}
try:
    manual = json.load(open('data/reports/manual_merged.json'))
except Exception:
    manual = {}

ORDER = ['中西區','灣仔區','香港東區','香港南區','離島區','油尖旺區','深水埗區','九龍城區',
         '黃大仙區','觀塘區','荃灣區','屯門區','元朗區','北區','沙田區','大埔區','西貢區','葵青區']
dorder = {d:i for i,d in enumerate(ORDER)}

LABEL = re.compile(r'(關注事項|關注項目|發展計劃|周年計劃|工作計劃|教育主題|學校主題|願景|計劃書)')
YEAR  = re.compile(r'20\d{2}\s*[-–~至]\s*20?\d{2,4}')

def is_label(it):
    if len(it) > 46: return False
    if YEAR.search(it) and LABEL.search(it): return True
    if re.search(r'(關注事項|關注項目)\s*[：:（(]?\s*$', it): return True
    if re.search(r'(關注事項|關注項目|計劃重點|發展重點)\s*$', it): return True
    if re.fullmatch(r'20\d{2}\s*[-–~]\s*20?\d{2,4}\s*', it): return True
    return False

OVERRIDES = {
 '聖類斯中學': ('三年發展計劃（2025-28）', ['以「全校參與模式」，營造濃厚閱讀氣氛。','透過有系統的價值觀教育課程，以實踐校訓「學問與虔敬」。']),
 '英華女學校': ('', ['發展計劃方向（2021-2026）：環繞「啟發」、「給力」、「擁抱」、「參與」四個主題，在新校舍完善硬件基礎上，給予學生最優化的全人培育。']),
 '瑪利諾神父教會學校': ('重點關注事項（2024-2027）', ['照顧學生學習多樣性。','訂定具天主教特色的校本全人發展框架，裝備學生迎接廿一世紀的社會技能及態度。','營造正向的學校文化。']),
 '迦密中學': ('學校重點關注項目（2025-2028）', ['成為善學者','關愛自我，共建社群','發展可持續教學團隊']),
 '中華基督教會扶輪中學': ('', ['建構學生迎向未來的學習能力','培養學生健康素養']),
 '中華基督教會基智中學': ('校園主題（2025/26）：編織夢想 突破自我', ['發展學習型校園','建構學生正向的生活','優化跨課程語文（LaC）學習，提升學生英語水平']),
 '路德會呂祥光中學': ('學校主題（2025-2028）：燃亮 同行', ['培育學生自信，促進學生主動積極學習。','建立學生自尊，培養健康的身心靈。']),
 '潮州會館中學': ('關注事項（2024-2027）', ['鞏固學生語文基礎，培養自主學習能力，達致終身學習的目標','推展正向教育，建立健康的生活方式，促進全人發展。']),
 '恩主教書院': ('', ['學與教：塑造學生成爲自主學習者。','學生支援與校風：促進學生全人發展。']),
 '拔萃男書院': ('', ['透過科技與適性學習，豐富學生個人化學習經歷。','豐富正向態度與心理健康，促進個人成長。','深化道德價值觀，加強校園凝聚力，發揮學生全人潛能。']),
}

def refine(f):
    items, note = [], ''
    for it in f['items']:
        if '請參閱' in it or '請參考' in it:
            note = it; continue
        if is_label(it): continue
        items.append(it)
    if not items and not note:
        note = '概覽未列明（見學校發展計劃）'
    return items, note

data = []
for r in rows:
    f = fin.get(r['id'], {'items':[], 'theme':''})
    f['items'], fnote = refine(f)
    if r['zh'] in OVERRIDES:
        th, its = OVERRIDES[r['zh']]
        f = dict(items=its, theme=th)
    data.append({
        'n': r['zh'], 'e': r['en'], 'd': r['district'], 't': r['type'],
        'g': r['gender'], 'rel': r['religion'], 'w': r['webpage'], 's': r['source'],
        'i': f['items'], 'th': f.get('theme',''), 'note': fnote, 'id': r['id'],
        'tg': school_tags(f['items']),
        'rp': ([{'y': y['y'], 'u': y['u'], 'en': bool(y.get('en')),
                 's': next((x['s'] for x in summ.get(r['id'], []) if x['y'] == y['y']), ''),
                 'b': [{'t': b['title'], 'c': b['content'], 'o': b['outcome']} for b in y['b'][:3]]}
                for y in rep.get(r['id'], [])]
               + [{'y': m['y'], 'u': m['u'], 'en': False, 's': m['s'], 'q': m.get('q',''), 'm': True, 'b': []}
                  for m in manual.get(r['id'], []) if not any(y['y'] == m['y'] for y in rep.get(r['id'], []))])
    })
data.sort(key=lambda x: (dorder.get(x['d'], 99), x['n']))

# CSV
with open('全港中學一覽_2025-26.csv','w',newline='',encoding='utf-8-sig') as fh:
    w = csv.writer(fh)
    w.writerow(['學校名稱','英文名稱','區域','學校類別','學生性別','宗教','主題（自動歸類）','關注事項（2025/26）','近三年學校報告摘要','學校網頁','資料來源（中學概覽）'])
    for x in data:
        w.writerow([x['n'], x['e'], x['d'], x['t'], x['g'], x['rel'], '、'.join(x['tg']),
                    ' / '.join(x['i']) if x['i'] else (x['note'] or '概覽未列明'),
                    ' | '.join(f"{y['y']}：{'；'.join((b['t']+'｜'+' '.join(b['o'] or b['c'])) for b in y['b'][:3])}" for y in x['rp']),
                    x['w'], x['s']])

payload = json.dumps(data, ensure_ascii=False, separators=(',',':'))

HTML = r'''<!DOCTYPE html>
<html lang="zh-Hant-HK">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>全港中學一覽表（2025/26 關注事項）</title>
<style>
*,*::before,*::after{box-sizing:border-box}
:root{
  --bg:#f6f7f9; --card:#fff; --ink:#16181d; --ink2:#5a616e; --ink3:#8a909c;
  --line:#e4e7ec; --accent:#2f5bea; --accent-soft:#eef2fe;
  --gov:#7c3aed; --gov-bg:#f3edff; --aided:#0f766e; --aided-bg:#e6f7f4;
  --dss:#b45309; --dss-bg:#fdf1e0; --caput:#475569; --caput-bg:#eef1f5;
  --radius:12px;
}
html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--bg);color:var(--ink);
  font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","Noto Sans HK","Noto Sans TC","PingFang HK","Microsoft JhengHei",sans-serif;
  font-size:15px;line-height:1.55}
a{color:var(--accent);text-decoration:none}
a:hover{text-decoration:underline}
.wrap{max-width:1180px;margin:0 auto;padding:0 16px}

/* header */
header{background:linear-gradient(180deg,#1b2a4a 0%,#24365c 100%);color:#fff;padding:30px 0 26px}
header h1{margin:0 0 6px;font-size:24px;letter-spacing:.5px;font-weight:700}
header .sub{color:#c6d0e4;font-size:13.5px}
header .sub b{color:#fff;font-weight:600}
.stats{display:flex;flex-wrap:wrap;gap:8px;margin-top:16px}
.stat{background:rgba(255,255,255,.1);border:1px solid rgba(255,255,255,.16);
  padding:6px 11px;border-radius:999px;font-size:12.5px;color:#e7ecf7}
.stat b{color:#fff}

/* controls */
.controls{position:sticky;top:0;z-index:30;background:rgba(255,255,255,.94);
  backdrop-filter:blur(8px);border-bottom:1px solid var(--line)}
.controls-in{display:flex;flex-wrap:wrap;gap:10px;align-items:center;padding:12px 16px;max-width:1180px;margin:0 auto}
.search{position:relative;flex:1 1 260px;min-width:200px}
.search input{width:100%;padding:10px 12px 10px 34px;border:1px solid var(--line);border-radius:10px;
  font-size:14px;background:#fff;color:var(--ink);outline:none;font-family:inherit}
.search input:focus{border-color:var(--accent);box-shadow:0 0 0 3px rgba(47,91,234,.12)}
.search svg{position:absolute;left:11px;top:50%;transform:translateY(-50%);width:15px;height:15px;stroke:var(--ink3)}
select{padding:10px 30px 10px 11px;border:1px solid var(--line);border-radius:10px;background:#fff;
  font-size:14px;color:var(--ink);font-family:inherit;outline:none;appearance:none;
  background-image:url("data:image/svg+xml;charset=utf8,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 12 12'%3E%3Cpath d='M2 4l4 4 4-4' fill='none' stroke='%238a909c' stroke-width='1.6'/%3E%3C/svg%3E");
  background-repeat:no-repeat;background-position:right 10px center;background-size:11px}
select:focus{border-color:var(--accent);box-shadow:0 0 0 3px rgba(47,91,234,.12)}
.count{font-size:13px;color:var(--ink2);margin-left:auto;white-space:nowrap}
.count b{color:var(--ink)}

/* table */
main{padding:18px 0 40px}
.tablecard{background:var(--card);border:1px solid var(--line);border-radius:var(--radius);overflow:clip;
  box-shadow:0 1px 2px rgba(16,24,40,.04)}
table{width:100%;border-collapse:collapse;font-size:14px}
thead th{position:sticky;top:64px;z-index:20;background:#fbfbfc;border-bottom:1px solid var(--line);
  text-align:left;padding:11px 14px;font-size:12.5px;letter-spacing:.4px;color:var(--ink2);
  font-weight:600;white-space:nowrap;cursor:pointer;user-select:none}
thead th:hover{color:var(--ink)}
thead th .ar{color:var(--ink3);font-size:10px;margin-left:4px}
tbody td{padding:13px 14px;border-bottom:1px solid #f0f2f5;vertical-align:top}
tbody tr:hover{background:#fafbfd}
tbody tr:last-child td{border-bottom:none}
.c-name{min-width:210px}
.c-name .zh{font-weight:600;font-size:14.5px;color:var(--ink);display:inline-block}
.c-name .en{display:block;font-size:11.5px;color:var(--ink3);margin-top:2px;letter-spacing:.2px}
.c-name .links{margin-top:5px;display:flex;gap:8px;flex-wrap:wrap}
.c-name .links a{font-size:11.5px;color:var(--ink2);border:1px solid var(--line);border-radius:6px;
  padding:1px 7px;background:#fff}
.c-name .links a:hover{color:var(--accent);border-color:#cdd8fb;text-decoration:none}
.c-dist{white-space:nowrap;color:var(--ink2);font-size:13.5px}
.badge{display:inline-block;padding:2px 9px;border-radius:999px;font-size:12px;font-weight:600;letter-spacing:.2px}
.b-官立{color:var(--gov);background:var(--gov-bg)}
.b-資助{color:var(--aided);background:var(--aided-bg)}
.b-直資{color:var(--dss);background:var(--dss-bg)}
.b-按位津貼{color:var(--caput);background:var(--caput-bg)}
.meta{display:block;margin-top:4px;font-size:11.5px;color:var(--ink3)}
.c-theme{min-width:120px}
.chip{display:inline-block;margin:0 4px 4px 0;padding:1px 7px;border-radius:999px;font-size:11px;
  background:var(--accent-soft);color:#2f4ea8;border:1px solid #dbe4fd;cursor:pointer;line-height:1.5}
.chip:hover{background:#e2e9fd;text-decoration:none}
.chip.more{background:#f4f6fb;color:var(--ink2);border-color:var(--line)}
@media (prefers-color-scheme:dark){.chip{background:#1e2a4a;color:#b9c8ee;border-color:#2c3a5e}
  .chip:hover{background:#25335a}.chip.more{background:#1a1f2b;color:#9aa3b2;border-color:#2a3140}}
.rpBtn{margin-top:7px;display:inline-block;border:1px solid #cdd8fb;color:#2f4ea8;background:#f5f8ff;
  border-radius:6px;padding:2px 9px;font-size:11.5px;font-family:inherit;cursor:pointer;line-height:1.6}
.rpBtn:hover{background:#eaf0ff}
.rpBtn.on{background:#e7eeff!important}
tr.rpRow>td{background:#fbfcff;padding:0 14px 14px!important}
.rpPanel{border-top:1px dashed var(--line);padding:12px 2px 4px;font-size:13px}
.rpY{margin-bottom:12px}
.rpY:last-child{margin-bottom:0}
.rpYh{display:flex;align-items:center;gap:8px;margin-bottom:6px}
.rpTag{background:#eef2fe;color:#2f4ea8;border-radius:6px;padding:1px 8px;font-size:12px;font-weight:600}
.rpSrc{font-size:11.5px;color:var(--ink3)}
.rpB{margin:0 0 7px;padding-left:10px;border-left:2px solid #e4e9f7}
.rpT{font-weight:600;color:var(--ink);font-size:13px;margin-bottom:2px}
.rpO,.rpC{color:var(--ink2);font-size:12.5px;line-height:1.6;margin:1px 0}
.rpS{margin:0 0 7px;font-size:13px;line-height:1.75;color:var(--ink)}
.rpD{margin-top:4px}
.rpD>summary{cursor:pointer;font-size:11.5px;color:var(--ink3);list-style:none}
.rpD>summary::-webkit-details-marker{display:none}
.rpD>summary:hover{color:var(--accent)}
.rpD[open]>summary{margin-bottom:6px}
.rpLab{color:var(--ink3);font-size:11.5px;margin-right:4px}
.conc{min-width:300px}
.conc ol{margin:0;padding-left:18px}
.conc li{margin:0 0 4px;color:var(--ink);font-size:13.5px;line-height:1.6}
.conc li:last-child{margin-bottom:0}
.conc .none{color:var(--ink3);font-size:13px}
.conc .th{display:inline-block;margin-top:6px;font-size:11.5px;color:var(--ink2);background:#f4f6fb;
  border-radius:6px;padding:2px 8px}
.more{margin-top:4px}
.moreLink{font-size:11.5px;color:var(--accent)}
.empty{padding:40px;text-align:center;color:var(--ink3);font-size:14px}

/* footer */
footer{border-top:1px solid var(--line);background:#fff;padding:24px 0 40px;color:var(--ink2);font-size:12.5px;line-height:1.8}
footer h3{font-size:13px;color:var(--ink);margin:0 0 8px;letter-spacing:.3px}
footer ul{margin:0 0 14px;padding-left:18px}
footer li{margin-bottom:3px}
footer .note{color:var(--ink3)}

/* mobile cards */
@media (max-width:760px){
  header{padding:22px 0 18px}
  header h1{font-size:20px}
  .controls-in{padding:10px 12px;gap:8px}
  .search{flex:1 1 100%}
  .count{width:100%;margin:0;text-align:right}
  thead{display:none}
  tbody tr{display:block;padding:14px 14px 12px;border-bottom:1px solid var(--line)}
  tbody td{display:block;padding:0;border:none}
  .c-name{margin-bottom:8px}
  .c-name .zh{font-size:15.5px}
  .c-dist{margin-bottom:2px}
  .c-dist::before{content:"區域：";color:var(--ink3)}
  .c-type{margin-bottom:8px}
  .c-type::before{content:"類別：";color:var(--ink3)}
  .c-type .meta{display:inline;margin-left:6px}
  .c-theme{margin-bottom:6px}
  .c-theme::before{content:"主題：";color:var(--ink3)}
  .rowmeta .badge{font-size:11px}
  .conc::before{content:"關注項目";display:block;font-size:11.5px;color:var(--ink3);margin:0 0 3px}
  .conc ol{padding-left:16px}
  .conc li{font-size:13px}
  .tablecard{border-radius:10px}
  main{padding:12px 0 30px}
}
@media print{
  header{background:#fff;color:#000;border-bottom:1px solid #ccc}
  header .sub,.stats{color:#333}
  .controls{display:none}
  thead th{position:static}
  body{background:#fff;font-size:11px}
  .c-name .links{display:none}
}
</style>
</head>
<body>
<header>
  <div class="wrap">
    <h1>全港中學一覽表</h1>
    <div class="sub">共 <b>__N__</b> 所中學 · 校名／區域／學校類別／主題／關注項目 · 資料來源：<b>家校會《中學概覽 2025/2026》</b>（教育局．家庭與學校合作事宜委員會）</div>
    <div class="stats">
      <span class="stat">資助 <b>__AIDED__</b></span>
      <span class="stat">直資 <b>__DSS__</b></span>
      <span class="stat">官立 <b>__GOV__</b></span>
      <span class="stat">按位津貼 <b>__CAPUT__</b></span>
      <span class="stat">18 區全收錄</span>
      <span class="stat">概覽未列明 <b>__MISSING__</b> 所</span>
      <span class="stat">報告摘要 <b>__REP__</b> 校</span>
      <span class="stat">2026/27 概覽尚未出版</span>
    </div>
  </div>
</header>

<div class="controls">
  <div class="controls-in">
    <div class="search">
      <svg viewBox="0 0 24 24" fill="none" stroke-width="2"><circle cx="11" cy="11" r="7"/><path d="M20 20l-3.5-3.5"/></svg>
      <input id="q" type="search" placeholder="搜尋校名／地區／主題／關注事項關鍵字…" autocomplete="off">
    </div>
    <select id="fd"><option value="">全部區域</option></select>
    <select id="ft"><option value="">全部類別</option></select>
    <select id="fth"><option value="">全部主題</option></select>
    <span class="count">顯示 <b id="n">0</b> / __N__</span>
  </div>
</div>

<main>
  <div class="wrap">
    <div class="tablecard">
      <table id="tb">
        <colgroup><col style="width:23%"><col style="width:8%"><col style="width:11%"><col style="width:15%"><col style="width:43%"></colgroup>
        <thead>
          <tr>
            <th data-k="n">學校名稱<span class="ar">⇅</span></th>
            <th data-k="d">區域<span class="ar">⇅</span></th>
            <th data-k="t">學校類別<span class="ar">⇅</span></th>
            <th style="cursor:default">主題</th>
            <th style="cursor:default">關注項目（2025/26 學年）</th>
          </tr>
        </thead>
        <tbody id="body"></tbody>
      </table>
      <div class="empty" id="empty" style="display:none">沒有符合條件的學校，請調整篩選。</div>
    </div>
  </div>
</main>

<footer>
  <div class="wrap">
    <h3>資料說明</h3>
    <ul>
      <li><b>校名</b>：點擊校名可開啟該校在《中學概覽 2025/2026》的官方資料頁（資料來源）；每列另附「概覽 PDF」及「學校網頁」連結。</li>
      <li><b>區域</b>：按教育局 18 區分區（學校實際所在區域）。</li>
      <li><b>學校類別</b>：官立／資助／直資／按位津貼，另附學生性別及宗教背景。</li>
      <li><b>主題</b>：按 16 類主題以關鍵詞多標籤自動歸類（每校平均 2.6 個），點主題標籤可即時篩選；分類為整理結果，非官方分類。</li>
      <li><b>報告摘要</b>：由各校官網可讀取的《學校周年報告》PDF 抽取（近三年），列出關注事項及其「成效／成就」段落；中文摘要由 AI 依報告原文改寫，只使用原文內容、不加入外部資料，可展開核對原文摘錄及 PDF。數字與結論以原文為準；約 3 成學校在網上公開可讀報告，其餘未收錄。</li>
      <li><b>關注項目</b>：摘自概覽「學校特色 → 學校關注事項」一欄，由學校自行提供及核實，已按原文整理為條目；部分學校只列年度主題或未填報，該等情況會標示「概覽未列明」。</li>
    </ul>
    <h3>範圍與限制</h3>
    <ul>
      <li>涵蓋《中學概覽》收錄的 441 所本地中學，<span class="note">不包括國際學校及私立獨立學校</span>。</li>
      <li>最新一期官方概覽為 <b>2025/2026</b> 學年版本；<b>2026/2027</b> 學年版通常於每年 12 月出版，屆時需重新抓取更新。多數學校的關注事項屬三年發展計劃（如 2024-2027），跨年沿用。</li>
      <li>如需查核最新年度計劃，可經每列的「學校網頁」前往該校「學校發展計劃／周年計劃」頁面。</li>
      <li>本頁為資料整理，非官方出版物；如有差異，以學校及教育局公布為準。</li>
    </ul>
    <p class="note">整理日期：2026 年 11 月 5 日</p>
  </div>
</footer>

<script>
const DATA = __DATA__;
const $ = s => document.querySelector(s);
const body = $('#body'), q = $('#q'), fd = $('#fd'), ft = $('#ft'), fth = $('#fth'), nEl = $('#n');

// filter options
const dists = [...new Set(DATA.map(d => d.d))];
const types = ['官立','資助','直資','按位津貼'].filter(t => DATA.some(d => d.t === t));
dists.forEach(d => fd.insertAdjacentHTML('beforeend', `<option value="${d}">${d}</option>`));
types.forEach(t => ft.insertAdjacentHTML('beforeend', `<option value="${t}">${t}</option>`));
const themeCount = {};
DATA.forEach(d => (d.tg||[]).forEach(t => themeCount[t] = (themeCount[t]||0)+1));
Object.keys(themeCount).sort((a,b)=>themeCount[b]-themeCount[a])
  .forEach(t => fth.insertAdjacentHTML('beforeend', `<option value="${t}">${t}（${themeCount[t]}）</option>`));

const esc = s => String(s).replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const SHOW = 3;
let sortKey = null, sortDir = 1, view = DATA.slice();

function themeChips(tg){
  tg = tg || [];
  if (!tg.length) return '<span class="none" style="font-size:11.5px;color:var(--ink3)">—</span>';
  const show = tg.slice(0,2).map(t=>`<button class="chip" data-th="${esc(t)}">${esc(t)}</button>`).join('');
  const rest = tg.length > 2 ? `<button class="chip more" data-th-more="1">+${tg.length-2}</button>` : '';
  return show + rest;
}

function rpPanel(rp){
  return '<div class="rpPanel">' + rp.map(function(y){
    const blocks = (y.b||[]).map(function(b){
      const o = (b.o||[]).map(x=>`<p class="rpO">${esc(x)}</p>`).join('');
      const c = (!b.o||!b.o.length) ? (b.c||[]).map(x=>`<p class="rpC"><span class="rpLab">內容</span>${esc(x)}</p>`).join('') : '';
      return `<div class="rpB"><div class="rpT">${esc(b.t)}</div>${o}${c}</div>`;
    }).join('');
    const sumTxt = y.s ? `<p class="rpS">${esc(y.s)}</p>` : '';
    const quote = y.q ? `<details class="rpD"><summary>原文佐證 ▾</summary><p class="rpO">「${esc(y.q)}」</p></details>` : '';
    const detail = blocks ? `<details class="rpD"><summary>原文摘錄 ▾</summary>${blocks}</details>` : '';
    return `<div class="rpY"><div class="rpYh"><span class="rpTag">${esc(y.y)}</span>${y.en ? '<span class=\"rpTag\" style=\"background:#f3f4f6;color:#5a616e\">英文原文</span>' : ''}${y.m ? '<span class=\"rpTag\" style=\"background:#ecfdf3;color:#0f766e\">人工查證</span>' : ''}
      <a class="rpSrc" href="${y.u}" target="_blank" rel="noopener">報告原文 PDF</a></div>${sumTxt}${quote}${detail}</div>`;
  }).join('') + '</div>';
}

function rowHTML(d, idx){
  const items = d.i || [];
  const shown = items.slice(0, SHOW);
  const rest = items.slice(SHOW);
  let list = '';
  if (shown.length){
    list = '<ol>' + shown.map(x => `<li>${esc(x)}</li>`).join('') + '</ol>';
    if (rest.length){
      list += `<div class="more" data-idx="${idx}"><a href="#" class="moreLink">＋ 另 ${rest.length} 項</a>
        <ol class="hiddenList" style="display:none">${rest.map(x=>`<li>${esc(x)}</li>`).join('')}</ol></div>`;
    }
  } else {
    list = `<span class="none">${esc(d.note || '概覽未列明（見學校發展計劃）')}</span>`;
  }
  const theme = (d.th && d.th.length <= 30) ? `<span class="th">年度主題：${esc(d.th)}</span>` : '';
  const meta = [d.g, d.rel && d.rel !== '不適用' ? d.rel : ''].filter(Boolean).join(' · ');
  return `<tr>
    <td class="c-name">
      <a class="zh" href="${d.s}" target="_blank" rel="noopener">${esc(d.n)}</a>
      <span class="en">${esc(d.e)}</span>
      <span class="links">
        <a href="${d.s}" target="_blank" rel="noopener">概覽資料</a>
        <a href="https://preview.chsc.hk/pdf/ssp2025/${d.id}_2.pdf" target="_blank" rel="noopener">概覽 PDF</a>
        ${d.w ? `<a href="${d.w}" target="_blank" rel="noopener">學校網頁</a>` : ''}
      </span>
    </td>
    <td class="c-dist"><span class="dlabel">${esc(d.d)}</span></td>
    <td class="c-type"><span class="badge b-${esc(d.t)}">${esc(d.t)}</span>${meta ? `<span class="meta">${esc(meta)}</span>` : ''}</td>
    <td class="c-theme">${themeChips(d.tg)}</td>
    <td class="conc">${list}${theme}${(d.rp&&d.rp.length) ? `<button class="rpBtn" data-rp="${idx}">近三年報告摘要（${d.rp.length} 年）▾</button>` : ''}</td>
  </tr>` + ((d.rp&&d.rp.length) ? `<tr class="rpRow" id="rp${idx}" style="display:none"><td colspan="5">${rpPanel(d.rp)}</td></tr>` : '');
}

function render(){
  const kw = q.value.trim().toLowerCase();
  const rd = fd.value, rt = ft.value, rth = fth.value;
  view = DATA.filter(d => {
    if (rd && d.d !== rd) return false;
    if (rt && d.t !== rt) return false;
    if (rth && !(d.tg||[]).includes(rth)) return false;
    if (!kw) return true;
    const hay = (d.n + d.e + d.d + d.t + (d.i||[]).join('') + (d.th||'') + (d.tg||[]).join('')).toLowerCase();
    return hay.includes(kw);
  });
  if (sortKey){
    view.sort((a,b) => {
      const x = a[sortKey] || '', y = b[sortKey] || '';
      return (x > y ? 1 : x < y ? -1 : 0) * sortDir;
    });
  }
  body.innerHTML = view.map((d,i) => rowHTML(d,i)).join('');
  nEl.textContent = view.length;
  $('#empty').style.display = view.length ? 'none' : 'block';
}

q.addEventListener('input', render);
fd.addEventListener('change', render);
ft.addEventListener('change', render);
fth.addEventListener('change', render);
document.querySelectorAll('thead th[data-k]').forEach(th => {
  th.addEventListener('click', () => {
    const k = th.dataset.k;
    if (sortKey === k) sortDir *= -1; else { sortKey = k; sortDir = 1; }
    render();
  });
});
body.addEventListener('click', e => {
  const rb = e.target.closest('.rpBtn');
  if (rb){
    const box = document.getElementById('rp'+rb.dataset.rp);
    if (box){
      const open = box.style.display !== 'none';
      box.style.display = open ? 'none' : 'table-row';
      rb.classList.toggle('on', !open);
    }
    return;
  }
  const chip = e.target.closest('.chip');
  if (chip && chip.dataset.th){
    fth.value = chip.dataset.th;
    render();
    window.scrollTo({top:0, behavior:'smooth'});
    return;
  }
  const a = e.target.closest('.moreLink');
  if (!a) return;
  e.preventDefault();
  const box = a.parentElement;
  const ol = box.querySelector('.hiddenList');
  const open = ol.style.display !== 'none';
  ol.style.display = open ? 'none' : 'block';
  a.textContent = open ? `＋ 另 ${ol.children.length} 項` : '− 收起';
});
render();
</script>
</body>
</html>'''

m = {d['t']: 0 for d in data}
for d in data: m[d['t']] = m.get(d['t'],0)+1
out = (HTML.replace('__DATA__', payload)
        .replace('__N__', str(len(data)))
        .replace('__AIDED__', str(m.get('資助',0)))
        .replace('__DSS__', str(m.get('直資',0)))
        .replace('__GOV__', str(m.get('官立',0)))
        .replace('__CAPUT__', str(m.get('按位津貼',0)))
        .replace('__MISSING__', str(sum(1 for d in data if not d['i'])))
        .replace('__REP__', str(sum(1 for d in data if d['rp']))))
open('index.html','w',encoding='utf-8').write(out)
print('written', len(out), 'bytes; schools', len(data))
