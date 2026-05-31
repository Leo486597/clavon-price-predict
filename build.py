#!/usr/bin/env python3
"""Parse propertynoob Clavon raw.html -> self-contained CMA report (index.html)."""
import re, json
from datetime import datetime

html = open('data/raw.html').read()
rows = re.findall(r'<tr>(.*?)</tr>', html, re.S)
clean = lambda x: re.sub(r'<[^>]+>', '', x).strip()

# layout -> (bedrooms label, group) for the whole project
LAYOUT_META = {
    'A1':  ('1BR',            527),
    'B1':  ('2BR Compact',    678),
    'BP1': ('2BR Premium',    764),
    'BP2': ('2BR Premium',    764),
    'BP3': ('2BR Premium',    764),
    'C1':  ('3BR Compact',    958),
    'CP1': ('3BR Premium',   1130),
    'CP2': ('3BR Premium',   1130),
    'D1':  ('3BR',           1281),
    'D2':  ('3BR',           1356),
    'DP1': ('3BR Premium',   1582),
    'E1':  ('4BR',           1690),
}

base = datetime(2020, 12, 1)
months = lambda d: (d.year - base.year) * 12 + (d.month - base.month)

txns = []
for r in rows:
    tds = re.findall(r'<td[^>]*>(.*?)</td>', r, re.S)
    if len(tds) != 8 or not clean(tds[0]).isdigit():
        continue
    m = re.search(r'floorPlanImg/([^"./]+)\.jpg', tds[3])
    layout = m.group(1) if m else None
    plan_url = re.search(r'href="([^"]+)"', tds[3])
    fm = re.match(r'#(\d+)-(\d+)', clean(tds[3]))
    if not fm:
        continue
    dt = datetime.strptime(clean(tds[1]), '%d %b %Y')
    bedrooms = LAYOUT_META.get(layout, ('?', 0))[0]
    txns.append(dict(
        id=int(clean(tds[0])),
        date=clean(tds[1]),
        iso=dt.strftime('%Y-%m-%d'),
        mo=months(dt),
        price=int(clean(tds[2]).replace('$', '').replace(',', '')),
        unit=clean(tds[3]),
        floor=int(fm.group(1)),
        stack=fm.group(2),
        layout=layout,
        bedrooms=bedrooms,
        area=int(clean(tds[4]).replace(',', '')),
        psf=int(clean(tds[5]).replace('$', '').replace(',', '')),
        sale=clean(tds[7]),
        plan=plan_url.group(1) if plan_url else '',
    ))

txns.sort(key=lambda t: t['iso'])
data_json = json.dumps(txns, separators=(',', ':'))

# ---- Target unit (from basic.info.md) ----
TARGET = dict(unit='#19-16', floor=19, stack='16', layout='BP3', area=764,
              bedrooms='2BR Premium', facing='South · sea & cruise view · no west sun',
              block='Block 8')

print(f"Parsed {len(txns)} transactions, {sum(1 for t in txns if t['area']==764)} @764sqft")

TEMPLATE = r'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Clavon #19-16 · Comparative Market Analysis</title>
<style>
:root{
  --navy:#0f2a43; --navy2:#16395c; --teal:#1f9c8f; --gold:#c79a3a; --gold2:#e8c97a;
  --ink:#11212f; --muted:#5f7283; --line:#e2e8ee; --bg:#f4f7fa; --card:#ffffff;
  --good:#1f9c8f; --warn:#c0653a; --hi:#fff6e0;
  --shadow:0 1px 2px rgba(16,33,47,.06),0 8px 24px rgba(16,33,47,.06);
}
*{box-sizing:border-box}
body{margin:0;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
  color:var(--ink);background:var(--bg);line-height:1.5;-webkit-font-smoothing:antialiased}
.wrap{max-width:1080px;margin:0 auto;padding:0 20px}
a{color:var(--teal)}
h1,h2,h3{line-height:1.25;margin:0}
.tag{display:inline-block;font-size:11px;letter-spacing:.14em;text-transform:uppercase;color:var(--gold);font-weight:700}

/* Header */
header{background:linear-gradient(135deg,var(--navy),var(--navy2));color:#fff;padding:34px 0 30px}
header .wrap{display:flex;flex-wrap:wrap;justify-content:space-between;gap:24px;align-items:flex-end}
header h1{font-size:30px;font-weight:700;margin:6px 0 4px}
header .sub{color:#b9cbdc;font-size:14px}
.subject{background:rgba(255,255,255,.08);border:1px solid rgba(255,255,255,.16);border-radius:12px;
  padding:14px 18px;min-width:280px}
.subject .row{display:flex;justify-content:space-between;gap:18px;font-size:13px;padding:3px 0;color:#dce6ef}
.subject .row b{color:#fff;font-weight:600}

/* Hero recommendation */
.hero{margin-top:-22px}
.hero-card{background:var(--card);border-radius:16px;box-shadow:var(--shadow);padding:26px 28px;border:1px solid var(--line)}
.hero-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin-top:18px}
.metric{border:1px solid var(--line);border-radius:12px;padding:16px;text-align:center;background:#fbfdfe}
.metric.feature{background:linear-gradient(160deg,#fffaf0,#fff);border-color:var(--gold2);position:relative;overflow:hidden}
.metric.feature:before{content:"RECOMMENDED";position:absolute;top:8px;right:-30px;transform:rotate(45deg);
  background:var(--gold);color:#fff;font-size:8px;letter-spacing:.1em;padding:3px 34px;font-weight:700}
.metric .lbl{font-size:11px;text-transform:uppercase;letter-spacing:.08em;color:var(--muted);font-weight:600}
.metric .val{font-size:26px;font-weight:750;margin:6px 0 2px;color:var(--navy)}
.metric .psf{font-size:12px;color:var(--muted)}
.metric.feature .val{color:var(--gold)}
.verdict{margin-top:18px;font-size:15px;color:#28475f;background:var(--hi);border:1px solid var(--gold2);
  border-radius:10px;padding:14px 16px}
.verdict b{color:var(--navy)}

/* Sections */
section{margin:40px 0}
section h2{font-size:21px;color:var(--navy);margin-bottom:4px}
section .lead{color:var(--muted);font-size:14px;margin-bottom:18px;max-width:760px}
.card{background:var(--card);border:1px solid var(--line);border-radius:14px;box-shadow:var(--shadow);padding:22px}
.cols{display:grid;grid-template-columns:1fr 1fr;gap:18px}
@media(max-width:820px){.cols{grid-template-columns:1fr}.hero-grid{grid-template-columns:1fr 1fr}
  header .wrap{align-items:flex-start}}

/* Stat strip */
.stats{display:grid;grid-template-columns:repeat(4,1fr);gap:14px}
.stat{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:16px;box-shadow:var(--shadow)}
.stat .n{font-size:22px;font-weight:750;color:var(--navy)}
.stat .l{font-size:12px;color:var(--muted);margin-top:2px}
@media(max-width:820px){.stats{grid-template-columns:1fr 1fr}}

/* Model breakdown */
.bd{border-collapse:collapse;width:100%;font-size:14px}
.bd td{padding:9px 6px;border-bottom:1px solid var(--line)}
.bd td:last-child{text-align:right;font-variant-numeric:tabular-nums;font-weight:600}
.bd tr.tot td{border-top:2px solid var(--navy);border-bottom:none;font-size:16px;color:var(--navy);font-weight:750;padding-top:12px}
.bd .pos{color:var(--good)} .bd .neg{color:var(--warn)}
.chip{display:inline-block;background:#eef4f3;color:var(--teal);border-radius:20px;padding:2px 9px;font-size:11px;font-weight:600;margin-left:6px}

/* Comparable highlight box */
.comp-hero{display:flex;gap:18px;flex-wrap:wrap;align-items:center;background:#f0f8f7;border:1px solid #bfe2dd;border-radius:12px;padding:16px 18px}
.comp-hero .big{font-size:30px;font-weight:750;color:var(--teal)}
.comp-hero .lbl{font-size:12px;color:var(--muted);text-transform:uppercase;letter-spacing:.06em}

/* Charts */
.chart-wrap{position:relative}
svg{width:100%;height:auto;display:block;font-family:inherit}
.legend{display:flex;gap:16px;flex-wrap:wrap;font-size:12px;color:var(--muted);margin-top:8px}
.legend span{display:inline-flex;align-items:center;gap:5px}
.dot{width:10px;height:10px;border-radius:50%;display:inline-block}

/* Controls / table */
.controls{display:flex;gap:10px;flex-wrap:wrap;align-items:center;margin-bottom:14px}
.controls label{font-size:12px;color:var(--muted);font-weight:600}
select,input[type=number]{border:1px solid var(--line);border-radius:8px;padding:7px 10px;font-size:13px;background:#fff;color:var(--ink)}
.btn{border:1px solid var(--line);background:#fff;border-radius:8px;padding:7px 12px;font-size:12px;cursor:pointer;color:var(--muted);font-weight:600}
.btn.on{background:var(--navy);color:#fff;border-color:var(--navy)}
.tbl-scroll{overflow:auto;max-height:520px;border:1px solid var(--line);border-radius:10px}
table.tx{border-collapse:collapse;width:100%;font-size:13px}
table.tx th{position:sticky;top:0;background:var(--navy);color:#fff;padding:9px 10px;text-align:right;font-weight:600;cursor:pointer;white-space:nowrap;font-size:12px}
table.tx th:first-child,table.tx th.l{text-align:left}
table.tx td{padding:8px 10px;text-align:right;border-bottom:1px solid var(--line);font-variant-numeric:tabular-nums;white-space:nowrap}
table.tx td.l{text-align:left}
table.tx tr:hover td{background:#f6fafb}
table.tx tr.s16{background:#fff6e0}
table.tx tr.s16:hover td{background:#fdeecb}
.badge{font-size:10px;font-weight:700;padding:2px 6px;border-radius:5px;letter-spacing:.03em}
.b-bp1{background:#e7eef6;color:#3f6489}.b-bp2{background:#eaf2ec;color:#3f7d57}.b-bp3{background:#fbeede;color:#b07020}
.b-other{background:#eef0f2;color:#73828f}
.s-Resale{color:#1f9c8f;font-weight:700}.s-Sub{color:#7a6cae;font-weight:600}.s-New{color:#94a3af}

/* Estimator */
.est-grid{display:grid;grid-template-columns:1.1fr .9fr;gap:22px}
@media(max-width:820px){.est-grid{grid-template-columns:1fr}}
.slider{margin:14px 0}
.slider .top{display:flex;justify-content:space-between;font-size:13px;margin-bottom:4px}
.slider .top b{color:var(--navy)}
input[type=range]{width:100%;accent-color:var(--teal)}
.est-out{background:var(--navy);color:#fff;border-radius:14px;padding:22px;text-align:center;display:flex;flex-direction:column;justify-content:center}
.est-out .lbl{font-size:12px;text-transform:uppercase;letter-spacing:.08em;color:#9fb6cb}
.est-out .big{font-size:34px;font-weight:750;margin:6px 0}
.est-out .psf{color:#bcd0e2;font-size:14px}
.est-out .band{margin-top:14px;font-size:13px;color:#cdddec;border-top:1px solid rgba(255,255,255,.15);padding-top:12px}

ul.notes{margin:8px 0 0;padding-left:18px;font-size:14px;color:#33495b}
ul.notes li{margin:7px 0}
.foot{color:var(--muted);font-size:12px;text-align:center;padding:30px 0 50px;line-height:1.7}
.pill{display:inline-block;background:#eef4f3;color:var(--teal);border-radius:6px;padding:1px 7px;font-size:12px;font-weight:600}
.warnbox{background:#fff5f0;border:1px solid #f0c9b6;border-radius:10px;padding:12px 14px;font-size:13px;color:#8a4a2e;margin-top:14px}
</style>
</head>
<body>
<header>
  <div class="wrap">
    <div>
      <span class="tag">Comparative Market Analysis · Seller's Report</span>
      <h1>Clavon &nbsp;__UNIT__</h1>
      <div class="sub">D5 Clementi · 99-yr leasehold · __BR__ · __AREA__ sqft · TOP 2024 &nbsp;|&nbsp; Analysis date: __TODAY__</div>
    </div>
    <div class="subject">
      <div class="row"><span>Subject unit</span><b>__UNIT__</b></div>
      <div class="row"><span>Layout · Stack</span><b>__LAYOUT__ · stack __STACK__</b></div>
      <div class="row"><span>Floor</span><b>__FLOOR__ of 37</b></div>
      <div class="row"><span>Block</span><b>__BLOCK__</b></div>
      <div class="row"><span>Aspect</span><b style="font-size:11px">__FACING__</b></div>
    </div>
  </div>
</header>

<div class="wrap hero">
  <div class="hero-card">
    <span class="tag">Pricing recommendation</span>
    <h2 style="color:var(--navy);font-size:22px;margin-top:4px">What to sell __UNIT__ for</h2>
    <div class="hero-grid">
      <div class="metric"><div class="lbl">Quick-Sale Floor</div><div class="val" id="m-floor"></div><div class="psf" id="m-floor-psf"></div></div>
      <div class="metric"><div class="lbl">Fair Market Value</div><div class="val" id="m-fair"></div><div class="psf" id="m-fair-psf"></div></div>
      <div class="metric feature"><div class="lbl">List / Asking Price</div><div class="val" id="m-ask"></div><div class="psf" id="m-ask-psf"></div></div>
      <div class="metric"><div class="lbl">Stretch / Ceiling</div><div class="val" id="m-ceil"></div><div class="psf" id="m-ceil-psf"></div></div>
    </div>
    <div class="verdict" id="verdict"></div>
  </div>
</div>

<div class="wrap">

<section>
  <h2>Market at a glance</h2>
  <p class="lead">All __N__ recorded transactions at Clavon (Dec 2020 launch &rarr; latest). The model below focuses on the <b>764 sqft 2-Bedroom Premium</b> pool &mdash; the only true peers for your unit.</p>
  <div class="stats" id="stats"></div>
</section>

<section>
  <h2>The benchmark sale</h2>
  <p class="lead">The single most relevant comparable on the entire register &mdash; same stack, same BP3 butterfly layout, just 3 floors above, and the most recent resale.</p>
  <div class="card">
    <div class="comp-hero">
      <div><div class="lbl">Closest comparable</div><div class="big">#22-16</div></div>
      <div><div class="lbl">Transacted</div><div style="font-size:20px;font-weight:700">$1,650,000</div><div class="psf" style="color:var(--muted);font-size:13px">$2,159 psf · Mar 2026 · Resale</div></div>
      <div style="flex:1;min-width:220px;font-size:13px;color:#33495b">
        Identical <b>BP3 butterfly · stack 16 · Block 8</b>. Your <b>__UNIT__</b> sits 3 floors lower, but is a more recent listing in a still-rising market and carries the same south-facing sea/cruise aspect. Floor gap (&minus;3 storeys &asymp; &minus;$19 psf) is roughly offset by 2 months of price growth (&asymp; +$16 psf) &mdash; net: priced essentially in line with #22-16.
      </div>
    </div>
  </div>
</section>

<section>
  <h2>How the price was built</h2>
  <p class="lead">A hedonic regression on all __N764__ &times; 764 sqft sales (R&sup2; = <span id="r2"></span>) isolates the value of floor, layout and market timing. Estimate for __UNIT__ at today's market:</p>
  <div class="cols">
    <div class="card">
      <table class="bd" id="breakdown"></table>
      <div class="warnbox">⚠︎ The raw time-trend slightly over-extrapolates at the tail (it would price #22-16 ~$58 psf above its actual sale). The headline recommendation therefore <b>blends the model with the #22-16 benchmark</b> rather than taking the model number neat.</div>
    </div>
    <div class="card">
      <h3 style="font-size:15px;color:var(--navy);margin-bottom:10px">What moves the number</h3>
      <table class="bd">
        <tr><td>Each additional floor</td><td class="pos" id="c-floor"></td></tr>
        <tr><td>Market growth (per month)</td><td class="pos" id="c-mo"></td></tr>
        <tr><td>BP3 butterfly vs BP2 layout</td><td class="pos" id="c-bp3"></td></tr>
        <tr><td>BP1 vs BP2 layout</td><td class="pos" id="c-bp1"></td></tr>
      </table>
      <p style="font-size:13px;color:#33495b;margin-top:14px">Your BP3 layout is the <b>most valuable</b> of the three 764 sqft variants &mdash; the dual-aspect "butterfly" plan commands a clear premium, and stack 16 adds the south-facing sea &amp; cruise view with no afternoon west sun. These are the attributes that justify pricing at the <b>top of the 2BR Premium band</b>.</p>
    </div>
  </div>
</section>

<section>
  <h2>Price trend &amp; floor premium</h2>
  <p class="lead">764 sqft sales over time, and how PSF climbs with floor height. The star marks where __UNIT__ should price.</p>
  <div class="cols">
    <div class="card chart-wrap">
      <h3 style="font-size:14px;color:var(--navy);margin-bottom:6px">PSF over time — 764 sqft pool</h3>
      <div id="chart-time"></div>
      <div class="legend">
        <span><i class="dot" style="background:#94a3af"></i>New launch</span>
        <span><i class="dot" style="background:#7a6cae"></i>Sub-sale</span>
        <span><i class="dot" style="background:#1f9c8f"></i>Resale</span>
        <span><i class="dot" style="background:var(--gold)"></i>★ #19-16 target</span>
      </div>
    </div>
    <div class="card chart-wrap">
      <h3 style="font-size:14px;color:var(--navy);margin-bottom:6px">PSF vs floor — 2024+ resale/sub-sale</h3>
      <div id="chart-floor"></div>
      <div class="legend">
        <span><i class="dot" style="background:#cbd5dd"></i>Other stacks</span>
        <span><i class="dot" style="background:var(--gold)"></i>Stack 16 (BP3)</span>
        <span><i class="dot" style="background:var(--navy)"></i>★ #19-16 target</span>
      </div>
    </div>
  </div>
</section>

<section>
  <h2>Tune the estimate</h2>
  <p class="lead">Adjust assumptions to stress-test the recommendation. Defaults reflect __UNIT__ in today's market.</p>
  <div class="card est-grid">
    <div>
      <div class="slider"><div class="top"><label>Floor</label><b id="v-floor"></b></div><input type="range" id="s-floor" min="2" max="37" value="19"></div>
      <div class="slider"><div class="top"><label>Months from launch (market timing)</label><b id="v-mo"></b></div><input type="range" id="s-mo" min="38" max="72" value="65"></div>
      <div class="slider"><div class="top"><label>Layout</label><b id="v-lay"></b></div>
        <div class="controls" style="margin:0"><button class="btn" data-lay="BP1">BP1</button><button class="btn" data-lay="BP2">BP2</button><button class="btn on" data-lay="BP3">BP3</button></div>
      </div>
      <div class="slider"><div class="top"><label>View / aspect premium</label><b id="v-view"></b></div><input type="range" id="s-view" min="0" max="60" value="25" step="5"></div>
      <p style="font-size:12px;color:var(--muted)">View premium = extra psf for the south-facing sea/cruise aspect &amp; no west sun (not captured by the base model).</p>
    </div>
    <div class="est-out">
      <div class="lbl">Estimated fair value</div>
      <div class="big" id="e-price"></div>
      <div class="psf" id="e-psf"></div>
      <div class="band" id="e-band"></div>
    </div>
  </div>
</section>

<section>
  <h2>Comparable transactions</h2>
  <p class="lead">Filter & sort the register. Stack 16 (your stack) is highlighted. Click any column header to sort.</p>
  <div class="controls">
    <label>Show:</label>
    <button class="btn on" data-f="prem">764 Premium only</button>
    <button class="btn" data-f="s16">Stack 16 only</button>
    <button class="btn" data-f="all">All units</button>
    <span style="width:14px"></span>
    <label>Sale type:</label>
    <button class="btn on" data-s="Resale">Resale</button>
    <button class="btn on" data-s="Sub">Sub-sale</button>
    <button class="btn" data-s="New">New</button>
    <span style="margin-left:auto;font-size:12px;color:var(--muted)" id="tcount"></span>
  </div>
  <div class="tbl-scroll">
    <table class="tx">
      <thead><tr>
        <th class="l" data-k="iso">Date</th><th class="l" data-k="unit">Unit</th>
        <th data-k="floor">Floor</th><th class="l" data-k="layout">Layout</th>
        <th data-k="area">Area</th><th data-k="price">Price</th>
        <th data-k="psf">PSF</th><th class="l" data-k="sale">Sale</th>
      </tr></thead>
      <tbody id="tbody"></tbody>
    </table>
  </div>
</section>

<section>
  <h2>Seller's playbook</h2>
  <div class="card">
    <ul class="notes">
      <li><b>List at <span class="pill" id="p-ask"></span>.</b> This sits just above the current BP3 ceiling (#26-07 hit $2,264 psf in Jan 2026), giving ~3–5% negotiating room down toward your target while anchoring buyers high.</li>
      <li><b>Expect to transact around <span class="pill" id="p-fair"></span></b> (~$2,185 psf) — the midpoint of the hedonic model ($2,215 psf) and the #22-16 benchmark ($2,159 psf, same stack, 3 floors up, Mar 2026). The lower floor is offset by 2 months of market growth in a rising trend.</li>
      <li><b>Hold your floor at <span class="pill" id="p-floor"></span>.</b> Below this you are leaving money on the table — even mid-floor stack-16 sales (#09-16, #12-16) cleared ~$2,057 psf, and the market has risen ~$95/psf/yr since.</li>
      <li><b>Lead with the layout & view.</b> BP3 "butterfly" is the most sought-after 764 sqft plan and trades ~$90 psf above BP2. Stack 16's south aspect, sea/cruise view and no-west-sun are genuine, defensible premiums — feature them in the listing.</li>
      <li><b>Timing.</b> Resale momentum is positive (3 resales in 2026 at $2,074–$2,159 psf). If holding cost allows, the trend favours patience over a quick discount.</li>
    </ul>
  </div>
</section>

</div>

<div class="foot">
  Prepared from __N__ caveated transactions scraped from propertynoob.com (D5 · Clavon · Sales). PSF model = OLS on the 764 sqft pool; figures are an estimate for negotiation guidance, not a valuation.<br>
  This is a decision-support tool, not formal financial or valuation advice. Verify against the latest URA caveats before listing.
</div>

<script>
const DATA = __DATA__;
const TARGET = __TARGET__;
const TODAY_MO = __TODAYMO__;
const fmt = n => '$' + Math.round(n).toLocaleString('en-US');
const fmtK = n => '$' + (Math.round(n/1000)).toLocaleString('en-US') + 'k';

/* ---------- Hedonic OLS: psf ~ 1 + floor + month + BP1 + BP3 (BP2 base) ---------- */
const P764 = DATA.filter(t => t.area === 764);
function ols(rows){
  const X = rows.map(t => [1, t.floor, t.mo, t.layout==='BP1'?1:0, t.layout==='BP3'?1:0]);
  const y = rows.map(t => t.psf);
  const k = 5, XtX = Array.from({length:k},()=>Array(k).fill(0)), Xty = Array(k).fill(0);
  for(let i=0;i<X.length;i++){for(let a=0;a<k;a++){Xty[a]+=X[i][a]*y[i];for(let b=0;b<k;b++)XtX[a][b]+=X[i][a]*X[i][b];}}
  // solve via Gauss-Jordan
  const M = XtX.map((r,i)=>[...r, Xty[i]]);
  for(let c=0;c<k;c++){
    let p=c; for(let r=c+1;r<k;r++) if(Math.abs(M[r][c])>Math.abs(M[p][c])) p=r;
    [M[c],M[p]]=[M[p],M[c]];
    const pv=M[c][c];
    for(let j=c;j<=k;j++)M[c][j]/=pv;
    for(let r=0;r<k;r++){ if(r===c)continue; const f=M[r][c]; for(let j=c;j<=k;j++)M[r][j]-=f*M[c][j]; }
  }
  const beta = M.map(r=>r[k]);
  const yhat = X.map(x=>x.reduce((s,v,i)=>s+v*beta[i],0));
  const ybar = y.reduce((a,b)=>a+b,0)/y.length;
  const ssr = y.reduce((s,v,i)=>s+(v-yhat[i])**2,0), sst = y.reduce((s,v)=>s+(v-ybar)**2,0);
  return {beta, r2: 1-ssr/sst};
}
const {beta, r2} = ols(P764);
const B0=beta[0], Bfloor=beta[1], Bmo=beta[2], Bbp1=beta[3], Bbp3=beta[4];
const layCoef = l => l==='BP1'?Bbp1 : l==='BP3'?Bbp3 : 0;
const predPsf = (floor, mo, lay) => B0 + Bfloor*floor + Bmo*mo + layCoef(lay);

/* ---------- Headline recommendation (model blended w/ #22-16 benchmark) ---------- */
const modelPsf = predPsf(TARGET.floor, TODAY_MO, TARGET.layout);   // ~2215
const BENCH = 2159;                                                // #22-16 resale Mar-2026 (same stack, +3 floors)
const fairPsf  = Math.round(modelPsf*0.5 + BENCH*0.5);             // midpoint of model & same-stack benchmark
const floorPsf = Math.round(fairPsf - 50);
const askPsf   = Math.round(fairPsf + 95);
const ceilPsf  = Math.round(fairPsf + 145);
const A = TARGET.area;
const toPrice = p => Math.round(p*A/1000)*1000;
function setMetric(id, psf){
  document.getElementById('m-'+id).textContent = fmtK(toPrice(psf));
  document.getElementById('m-'+id+'-psf').textContent = '$'+psf.toLocaleString()+' psf';
}
setMetric('floor', floorPsf); setMetric('fair', fairPsf); setMetric('ask', askPsf); setMetric('ceil', ceilPsf);
document.getElementById('verdict').innerHTML =
  `<b>Bottom line:</b> List ${TARGET.unit} at <b>${fmt(toPrice(askPsf))}</b> (~$${askPsf} psf) and expect to close around `+
  `<b>${fmt(toPrice(fairPsf))}</b> (~$${fairPsf} psf). Don't accept below <b>${fmt(toPrice(floorPsf))}</b>. `+
  `Your BP3 butterfly layout + south sea-view stack put this at the top of Clavon's 2-bedroom band.`;
['ask','fair','floor'].forEach(k=>{const e=document.getElementById('p-'+k);if(e)e.textContent=fmt(toPrice(k==='ask'?askPsf:k==='fair'?fairPsf:floorPsf));});

/* ---------- Stats strip ---------- */
const recent = P764.filter(t=>t.iso>='2025-01-01');
const psfs = recent.map(t=>t.psf).sort((a,b)=>a-b);
const med = psfs[Math.floor(psfs.length/2)];
const lastResale = DATA.filter(t=>t.area===764 && t.sale==='Resale').slice(-1)[0];
const stats = [
  ['n', DATA.length, 'Total transactions'],
  ['p', P764.length, '764 sqft 2BR Premium sales'],
  ['m', '$'+med.toLocaleString(), 'Median PSF (764, since 2025)'],
  ['g', '+$'+Math.round(Bmo*12)+'/yr', 'PSF growth (model)'],
];
document.getElementById('stats').innerHTML = stats.map(s=>`<div class="stat"><div class="n">${s[1]}</div><div class="l">${s[2]}</div></div>`).join('');

/* ---------- Model breakdown table ---------- */
document.getElementById('r2').textContent = r2.toFixed(3);
const rowsBd = [
  ['Base PSF (BP2, ground, launch)', B0, ''],
  [`Floor 19 &nbsp;<span class="chip">19 × $${Bfloor.toFixed(1)}</span>`, Bfloor*19, 'pos'],
  [`Market timing &nbsp;<span class="chip">${TODAY_MO} mo × $${Bmo.toFixed(1)}</span>`, Bmo*TODAY_MO, 'pos'],
  ['BP3 butterfly premium', Bbp3, 'pos'],
];
let bdHtml = rowsBd.map(r=>`<tr><td>${r[0]}</td><td class="${r[2]}">${r[1]>=0&&r[2]?'+':''}$${Math.round(r[1]).toLocaleString()}</td></tr>`).join('');
bdHtml += `<tr class="tot"><td>Model estimate — ${TARGET.unit}</td><td>$${Math.round(modelPsf).toLocaleString()} psf</td></tr>`;
bdHtml += `<tr><td style="color:var(--muted)">→ at ${A} sqft</td><td style="color:var(--navy)">${fmt(modelPsf*A)}</td></tr>`;
document.getElementById('breakdown').innerHTML = bdHtml;
document.getElementById('c-floor').textContent = '+$'+Bfloor.toFixed(1)+' psf';
document.getElementById('c-mo').textContent = '+$'+Bmo.toFixed(1)+' psf';
document.getElementById('c-bp3').textContent = '+$'+Math.round(Bbp3)+' psf';
document.getElementById('c-bp1').textContent = '+$'+Math.round(Bbp1)+' psf';

/* ---------- Charts (hand-rolled SVG) ---------- */
function svgEl(tag, attrs){const e=document.createElementNS('http://www.w3.org/2000/svg',tag);for(const k in attrs)e.setAttribute(k,attrs[k]);return e;}
const SALE_COLOR = {New:'#94a3af', Sub:'#7a6cae', Resale:'#1f9c8f'};

function chartTime(){
  const W=480,H=300,m={l:48,r:12,t:12,b:34};
  const pts = P764;
  const xs = pts.map(p=>p.mo), ys = pts.map(p=>p.psf);
  const x0=Math.min(...xs), x1=Math.max(...xs), y0=Math.min(...ys)-40, y1=Math.max(...ys)+40;
  const sx = v => m.l + (v-x0)/(x1-x0)*(W-m.l-m.r);
  const sy = v => H-m.b - (v-y0)/(y1-y0)*(H-m.t-m.b);
  const svg = svgEl('svg',{viewBox:`0 0 ${W} ${H}`});
  // gridlines + y labels
  for(let g=0;g<=4;g++){const yv=y0+(y1-y0)*g/4;const yy=sy(yv);
    svg.appendChild(svgEl('line',{x1:m.l,y1:yy,x2:W-m.r,y2:yy,stroke:'#eef2f5'}));
    const t=svgEl('text',{x:m.l-6,y:yy+3,'text-anchor':'end',fill:'#9aa7b2','font-size':10});t.textContent='$'+Math.round(yv);svg.appendChild(t);}
  // year x labels
  const yrMo = {'2021':1,'2022':13,'2023':25,'2024':37,'2025':49,'2026':61};
  for(const [yr,mo] of Object.entries(yrMo)){if(mo<x0-2||mo>x1+2)continue;const xx=sx(mo);
    const t=svgEl('text',{x:xx,y:H-12,'text-anchor':'middle',fill:'#9aa7b2','font-size':10});t.textContent=yr;svg.appendChild(t);}
  // trend line (BP3, model)
  const tl=[];for(let mo=x0;mo<=x1;mo+=2)tl.push([sx(mo),sy(predPsf(19,mo,'BP3'))]);
  svg.appendChild(svgEl('polyline',{points:tl.map(p=>p.join(',')).join(' '),fill:'none',stroke:'var(--gold2)','stroke-width':2,'stroke-dasharray':'4 4'}));
  // points
  pts.forEach(p=>{svg.appendChild(svgEl('circle',{cx:sx(p.mo),cy:sy(p.psf),r:p.sale==='New'?2.2:3.4,
    fill:SALE_COLOR[p.sale],opacity:p.sale==='New'?.45:.9}));});
  // target star
  const tx=sx(TODAY_MO), ty=sy(fairPsf);
  svg.appendChild(star(tx,ty,8,'var(--gold)'));
  document.getElementById('chart-time').appendChild(svg);
}
function chartFloor(){
  const W=480,H=300,m={l:48,r:12,t:12,b:34};
  const pts = P764.filter(t=>t.iso>='2024-01-01' && t.sale!=='New');
  const ys=pts.map(p=>p.psf); const y0=Math.min(...ys)-30,y1=Math.max(...ys)+30;
  const sx=v=>m.l+(v-1)/(37-1)*(W-m.l-m.r);
  const sy=v=>H-m.b-(v-y0)/(y1-y0)*(H-m.t-m.b);
  const svg=svgEl('svg',{viewBox:`0 0 ${W} ${H}`});
  for(let g=0;g<=4;g++){const yv=y0+(y1-y0)*g/4;const yy=sy(yv);
    svg.appendChild(svgEl('line',{x1:m.l,y1:yy,x2:W-m.r,y2:yy,stroke:'#eef2f5'}));
    const t=svgEl('text',{x:m.l-6,y:yy+3,'text-anchor':'end',fill:'#9aa7b2','font-size':10});t.textContent='$'+Math.round(yv);svg.appendChild(t);}
  [5,10,15,20,25,30,35].forEach(f=>{const xx=sx(f);
    const t=svgEl('text',{x:xx,y:H-12,'text-anchor':'middle',fill:'#9aa7b2','font-size':10});t.textContent=f;svg.appendChild(t);});
  pts.forEach(p=>{const s16=p.stack==='16';svg.appendChild(svgEl('circle',{cx:sx(p.floor),cy:sy(p.psf),
    r:s16?4.5:3,fill:s16?'var(--gold)':'#cbd5dd',opacity:s16?1:.8,stroke:s16?'#a87f28':'none','stroke-width':s16?1:0}));});
  const tx=sx(TARGET.floor),ty=sy(fairPsf);
  svg.appendChild(star(tx,ty,8,'var(--navy)'));
  document.getElementById('chart-floor').appendChild(svg);
}
function star(cx,cy,r,fill){
  let pts='';for(let i=0;i<10;i++){const ang=-Math.PI/2+i*Math.PI/5;const rr=i%2?r*0.45:r;pts+=(cx+rr*Math.cos(ang))+','+(cy+rr*Math.sin(ang))+' ';}
  return svgEl('polygon',{points:pts.trim(),fill:fill,stroke:'#fff','stroke-width':1.2});
}
chartTime(); chartFloor();

/* ---------- Interactive estimator ---------- */
let estLay='BP3';
function est(){
  const f=+document.getElementById('s-floor').value;
  const mo=+document.getElementById('s-mo').value;
  const view=+document.getElementById('s-view').value;
  document.getElementById('v-floor').textContent=f;
  const yr=2020+Math.floor((mo+11)/12); const mm=((mo+11)%12)+1;
  document.getElementById('v-mo').textContent=`${mo} mo (~${['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'][mm-1]} ${yr})`;
  document.getElementById('v-lay').textContent=estLay+(estLay==='BP3'?' (butterfly)':'');
  document.getElementById('v-view').textContent='+$'+view+' psf';
  const psf=predPsf(f,mo,estLay)+view;
  document.getElementById('e-price').textContent=fmt(toPrice(psf));
  document.getElementById('e-psf').textContent='$'+Math.round(psf).toLocaleString()+' psf';
  document.getElementById('e-band').innerHTML=`Negotiation band<br><b>${fmtK(toPrice(psf-50))} – ${fmtK(toPrice(psf+95))}</b>`;
}
['s-floor','s-mo','s-view'].forEach(id=>document.getElementById(id).addEventListener('input',est));
document.querySelectorAll('[data-lay]').forEach(b=>b.addEventListener('click',()=>{
  document.querySelectorAll('[data-lay]').forEach(x=>x.classList.remove('on'));b.classList.add('on');estLay=b.dataset.lay;est();}));
est();

/* ---------- Comparables table ---------- */
let filt='prem', sales={Resale:true,Sub:true,New:false}, sortK='iso', sortDir=-1;
const tbody=document.getElementById('tbody');
function layClass(l){return l==='BP1'?'b-bp1':l==='BP2'?'b-bp2':l==='BP3'?'b-bp3':'b-other';}
function render(){
  let rows=DATA.filter(t=>sales[t.sale]);
  if(filt==='prem') rows=rows.filter(t=>t.area===764);
  else if(filt==='s16') rows=rows.filter(t=>t.stack==='16');
  rows.sort((a,b)=>{let x=a[sortK],y=b[sortK];if(typeof x==='string'){return sortDir*x.localeCompare(y);}return sortDir*(x-y);});
  tbody.innerHTML=rows.map(t=>`<tr class="${t.stack==='16'?'s16':''}">
    <td class="l">${t.date}</td>
    <td class="l"><a href="${t.plan}" target="_blank" rel="noopener">${t.unit}</a></td>
    <td>${t.floor}</td>
    <td class="l"><span class="badge ${layClass(t.layout)}">${t.layout}</span> <span style="color:#9aa7b2;font-size:11px">${t.bedrooms}</span></td>
    <td>${t.area.toLocaleString()}</td>
    <td>$${t.price.toLocaleString()}</td>
    <td>$${t.psf.toLocaleString()}</td>
    <td class="l s-${t.sale}">${t.sale}</td></tr>`).join('');
  document.getElementById('tcount').textContent=rows.length+' shown';
}
document.querySelectorAll('[data-f]').forEach(b=>b.addEventListener('click',()=>{
  document.querySelectorAll('[data-f]').forEach(x=>x.classList.remove('on'));b.classList.add('on');filt=b.dataset.f;render();}));
document.querySelectorAll('[data-s]').forEach(b=>b.addEventListener('click',()=>{
  b.classList.toggle('on');sales[b.dataset.s]=b.classList.contains('on');render();}));
document.querySelectorAll('table.tx th').forEach(th=>th.addEventListener('click',()=>{
  const k=th.dataset.k;if(sortK===k)sortDir*=-1;else{sortK=k;sortDir=(k==='iso'||k==='psf'||k==='price'||k==='floor')?-1:1;}render();}));
render();
</script>
</body>
</html>'''

out = (TEMPLATE
       .replace('__DATA__', data_json)
       .replace('__TARGET__', json.dumps(TARGET))
       .replace('__TODAYMO__', str(months(datetime(2026, 5, 1))))
       .replace('__TODAY__', '31 May 2026')
       .replace('__UNIT__', TARGET['unit'])
       .replace('__LAYOUT__', TARGET['layout'])
       .replace('__STACK__', TARGET['stack'])
       .replace('__FLOOR__', str(TARGET['floor']))
       .replace('__BLOCK__', TARGET['block'])
       .replace('__FACING__', TARGET['facing'])
       .replace('__BR__', TARGET['bedrooms'])
       .replace('__AREA__', str(TARGET['area']))
       .replace('__N764__', str(sum(1 for t in txns if t['area'] == 764)))
       .replace('__N__', str(len(txns))))

open('index.html', 'w').write(out)
print(f"Wrote index.html ({len(out):,} bytes)")
