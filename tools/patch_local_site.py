# -*- coding: utf-8 -*-
"""⭐ MIND をローカル専用サイトにする（2026-09-18・燻太さんの指定）。目印 LOCAL-2026-09-18。

    python tools/patch_local_site.py        index.html と build_map.py に当てる（二度当てしない）

燻太さんの言葉＝「そろそろMINDも大きくなってきたから、ローカル版サイトに移行したいな。ALGAにあるような
論文の表示機能やCONNECTED PAPERSへのリンク、書庫にある本の対応ページの参照や画像の表示などの機能性を
持たせたい。（…）実装したい機能を持つサイトは公開すると著作権等に抵触する恐れがあるから、MINDの公開は
今後しないようにしたい」。

何が変わるか
  ① file:// で開ける＝CDN の cytoscape/fcose を lib/ に（ALGA と同じ4本）・data.json を fetch せず
     build_map.py が焼く data.js（window.DATA）を読む・brain.svg も brain.js（window.BRAIN_SVG）で読む
  ② 論文＝Connected Papers へ出るボタン（ALGA から移植。DOI があれば /api/redirect/doi/ に直行・無ければ検索欄まで）。
     手元PDFの「手元だけ」札は外す（もう公開しないので）
  ③ 書庫との連携＝../../Taiga_PJ/書庫/catalog.js を読み・ノードの出典（12_ゴールドバーグ 等）と
     台帳の `atlas` 欄を突き合わせて「書庫」の箱を出す。引用元・本文に出てくる頁（p.44・pp.44-45・画像17）を
     押すと・その頁の画像がその場に出る（←→で前後・「書庫で開く」でその頁へ）
  ④ 公開向けの文言（「手元だけ」「公開サイトでは…」）を外す

⚠退避＝_backup/index.html.bak_20260918_ローカル化まえ・_backup/build_map.py.bak_20260918
"""
import io, os, sys, shutil, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'index.html')
BM = os.path.join(ROOT, 'tools', 'build_map.py')
MARK = 'LOCAL-2026-09-18'

s = io.open(SRC, encoding='utf-8').read()
if MARK in s:
    print('もう当ててある（' + MARK + '）'); sys.exit(0)
d = datetime.date.today().strftime('%Y%m%d')
os.makedirs(os.path.join(ROOT, '_backup'), exist_ok=True)
for src, name in ((SRC, 'index.html.bak_' + d + '_ローカル化まえ'), (BM, 'build_map.py.bak_' + d)):
    dst = os.path.join(ROOT, '_backup', name)
    if not os.path.exists(dst):
        shutil.copyfile(src, dst); print('退避: ' + dst)

def rep(old, new, count=1):
    global s
    assert s.count(old) == count, ('当て先が %d 個（%d 個のはず）: ' % (s.count(old), count)) + old[:70]
    s = s.replace(old, new)

# ① ライブラリを手元に
rep('''<script src="https://cdnjs.cloudflare.com/ajax/libs/cytoscape/3.34.2/cytoscape.min.js"></script>''',
    '''<!-- ''' + MARK + ''' ⭐ローカル専用＝ライブラリは lib/（ALGA と同じ4本）。CDN には出ない -->
<script src="lib/cytoscape.min.js"></script>''')
rep('''<script src="https://cdn.jsdelivr.net/npm/layout-base@2.0.1/layout-base.js"></script>
<script src="https://cdn.jsdelivr.net/npm/cose-base@2.2.0/cose-base.js"></script>
<script src="https://cdn.jsdelivr.net/npm/cytoscape-fcose@2.2.0/cytoscape-fcose.js"></script>''',
    '''<script src="lib/layout-base.js"></script>
<script src="lib/cose-base.js"></script>
<script src="lib/cytoscape-fcose.js"></script>''')
rep('''<script src="positions.js"></script>''',
    '''<script src="positions.js"></script>
<!-- ''' + MARK + ''' ⭐file:// では fetch() が使えないので、中身は JS に焼いて読む（書庫と同じ理屈）。
     data.js・brain.js は tools/build_map.py が data.json と同時に書く。
     catalog.js は書庫の台帳（別フォルダ・無ければ書庫の機能だけ出ない） -->
<script src="data.js"></script>
<script src="brain.js"></script>
<script src="../../Taiga_PJ/書庫/catalog.js"></script>''')

# ① fetch → 焼いた JS
rep('''let BRAIN_BASE = null;   // brain.svg（Lynch の解剖図）の中身
fetch('brain.svg').then(r => r.ok ? r.text() : null).then(t => {
  if (!t) return;
  const m = t.match(/<svg[^>]*>([\\s\\S]*)<\\/svg>/i);
  if (m) BRAIN_BASE = m[1];
}).catch(() => { BRAIN_BASE = null; });''',
'''let BRAIN_BASE = null;   // brain.svg（Lynch の解剖図）の中身。''' + MARK + ''' ＝ brain.js（window.BRAIN_SVG）から
try {
  const t = window.BRAIN_SVG || '';
  const m = t.match(/<svg[^>]*>([\\s\\S]*)<\\/svg>/i);
  if (m) BRAIN_BASE = m[1];
} catch (e) { BRAIN_BASE = null; }''')
rep('''fetch('data.json?' + Date.now()).then(r => r.json()).then(d => {
  DATA = d; NODE_IDS = new Set(d.nodes.map(n => n.id)); boot(d);
})
  .catch(e => { document.getElementById('cy').innerHTML =
    '<p style="padding:20px">data.json が読めなかった: ' + e + '</p>'; });''',
'''// ''' + MARK + ''' ⭐data.js（window.DATA）を読む。⚠古い配置が出たら Ctrl+F5（素の src なのでキャッシュが残る）
//   ⚠⚠**同期で boot() を呼ばない**＝この下で定義される const（ORDER など）がまだ初期化されていない（TDZ）。
//     fetch のときと同じく、スクリプト全体を評価し終えてから boot する（Promise で1拍おく）
Promise.resolve().then(() => {
  const d = window.DATA;
  if (!d || !d.nodes) throw new Error('window.DATA が無い（tools/build_map.py で data.js を焼く）');
  DATA = d; NODE_IDS = new Set(d.nodes.map(n => n.id)); boot(d);
}).catch(e => {
  document.getElementById('cy').innerHTML =
    '<p style="padding:20px">data.js が読めなかった: ' + e + '</p>';
});''')

# ② CSS＝Connected Papers の箱・書庫の箱
rep('''  .norefs{''',
'''  /* ''' + MARK + ''' ⭐Connected Papers へ出るボタン（ALGA から）。⚠外へ出る唯一のボタン＝控えめに */
  .cpbox{margin:8px 0 4px}
  .cpbox a{display:inline-block;border:1px dashed var(--sub);color:var(--sub);border-radius:4px;
    padding:3px 9px;font-size:11.5px;text-decoration:none}
  .cpbox a:hover{color:var(--ink);border-color:var(--ink)}
  .cpbox .ext{font-size:10px;margin-left:3px}
  /* ''' + MARK + ''' ⭐書庫の箱＝出典の本がスキャンしてあれば、頁の札と画像 */
  .shoko{margin:10px 0 6px;padding:8px 10px;border:1px solid var(--line);border-radius:6px;background:rgba(127,127,127,.06)}
  .shoko .ttl{font-size:11px;color:var(--sub);margin-bottom:4px}
  .shoko .ttl b{color:var(--ink)}
  .shoko a.open{font-size:11.5px;margin-left:6px}
  .shoko .pgs{display:flex;flex-wrap:wrap;gap:4px;margin:4px 0}
  .shoko .pg,.pg{display:inline-block;cursor:pointer;border:1px solid var(--line);border-radius:10px;
    padding:0 7px;font-size:11px;line-height:18px;color:var(--ink);text-decoration:none;background:rgba(127,127,127,.08)}
  .shoko .pg:hover,.pg:hover{border-color:var(--ink)}
  .shoko .pg.on{background:var(--ink);color:var(--bg)}
  .shoko .view{margin-top:6px;display:none}
  .shoko .view.on{display:block}
  .shoko .view .bar{display:flex;align-items:center;gap:8px;font-size:11.5px;color:var(--sub);margin-bottom:4px}
  .shoko .view .bar button{font-size:12px;padding:1px 8px;cursor:pointer}
  .shoko .view img{width:100%;height:auto;display:block;border:1px solid var(--line);border-radius:4px;background:#fff}
  .shoko .view .txt{font-size:11.5px;line-height:1.7;max-height:220px;overflow:auto;white-space:pre-wrap;
    margin-top:6px;padding:6px 8px;border-left:2px solid var(--line);color:var(--ink)}
  .shoko .nopage{font-size:11px;color:var(--sub)}
  .norefs{''')

# ② 論文＝Connected Papers・「手元だけ」札を外す
rep('''    if (F['pdf'])
      h += '<br><a class="pdflink" href="' + esc(encodeURI(F['pdf'])) +
           '" target="_blank" rel="noopener noreferrer">本文PDFを開く</a>' +
           '<span class="localonly" title="papers/ は公開していない。手元でだけ開ける。' +
           '公開サイトからは上のDOIで原典へ">手元だけ</span>';''',
'''    if (F['pdf'])   // ''' + MARK + ''' ローカル専用になったので「手元だけ」の札は要らない
      h += '<br><a class="pdflink" href="' + esc(encodeURI(F['pdf'])) +
           '" target="_blank" rel="noopener noreferrer">本文PDFを開く</a>';''')
rep('''  if (n.file) h += '<br><span style="opacity:.7">' + esc(n.file) + '</span>';
  h += '</div>';
''',
'''  if (n.file) h += '<br><span style="opacity:.7">' + esc(n.file) + '</span>';
  h += '</div>';
  if (n.type === '論文') h += cpBox(n);                    // ''' + MARK + ''' Connected Papers
  CUR_SHOKO = shokoBooksOf(n);                              // ''' + MARK + ''' 本文の頁を札にするため先に決める
  h += shokoBox(n);                                         // ''' + MARK + ''' 書庫の箱（出典の本がスキャンしてあれば）
''')

# ③ 本文の頁（p.44・pp.44-45・画像17）を札にする＝md() の最後で
rep('''    .replace(/^#{3,} +(.+)$/gm, '<b class="h3">$1</b>')''',
'''    .replace(/^#{3,} +(.+)$/gm, '<b class="h3">$1</b>')
    .replace(PAGE_RE, (m0) => pageChip(m0))                 // ''' + MARK + ''' 書庫の頁の札''')

# ③ 引用元の note・title の頁も札に
rep('''      h += safe ? '<a href="' + esc(safe) + '" target="_blank" rel="noopener noreferrer">' +
                  esc(r.title) + '</a>'
                : esc(r.title);
      if (r.note) h += '<div class="note">' + esc(r.note) + '</div>';''',
'''      h += safe ? '<a href="' + esc(safe) + '" target="_blank" rel="noopener noreferrer">' +
                  esc(r.title) + '</a>'
                : esc(r.title).replace(PAGE_RE, (m0) => pageChip(m0));   // ''' + MARK + '''
      if (r.note) h += '<div class="note">' + esc(r.note).replace(PAGE_RE, (m0) => pageChip(m0)) + '</div>';''')

# ③ 札の押しかた＝show() の末尾で結び付ける
rep('''  body.querySelectorAll('a[data-go]').forEach(a => a.onclick = () => goLink(a.dataset.go));
}''',
'''  body.querySelectorAll('a[data-go]').forEach(a => a.onclick = () => goLink(a.dataset.go));
  wireShoko(body);                                          // ''' + MARK + '''
}''')

# ② ③ 本体＝show() の前に置く
BODY = r'''
/* ============================================================================
   ''' + MARK + r''' ── ローカル専用の機能（2026-09-18・燻太さんの指定）

   ⭐MIND はもう公開しない（GitHub Pages を切り・リポジトリは private）。理由＝書庫の画像や
     論文の本文を地図から引く作りは・公開すると著作権に抵触するおそれがあるから。
   ⭐だから ALGA/LAND と同じく file:// で開く。fetch は使わず・data.js / brain.js / catalog.js を script で読む。
   ============================================================================ */

/* ⭐Connected Papers へ出るボタン（ALGA から移植・2026-09-10 の作り）。
   DOI があれば /api/redirect/doi/<DOI> で網の構築に直行・無ければ検索欄にノード名を入れるところまで。
   ⚠この地図で外へ出る唯一のボタン＝DOI（公開情報）が外部サイトに渡る。押すかどうかは人が決める。 */
const CP = 'https://www.connectedpapers.com/';
function cpUrl(n){
  const doi = ((n.fields || {})['DOI'] || (n.fields || {})['doi'] || '').trim();
  if (doi)
    return { u: CP + 'api/redirect/doi/' + doi.split('/').map(encodeURIComponent).join('/'),
             lab: 'Connected Papers でこの論文の網を開く',
             tip: 'DOI ' + doi + ' を渡して、引用の網（グラフ）を作らせる。⚠外部サイトに DOI が渡ります' };
  return { u: CP + 'search?q=' + encodeURIComponent(n.id),
           lab: 'Connected Papers で探す',
           tip: 'この論文は DOI を持っていないので「' + n.id + '」を検索欄に入れるところまで。⚠外部サイトに渡ります' };
}
function cpBox(n){
  const c = cpUrl(n);
  return '<div class="cpbox"><a href="' + esc(c.u) + '" target="_blank" rel="noopener noreferrer" title="' +
         esc(c.tip) + '">' + esc(c.lab) + '<span class="ext">&#8599;</span></a></div>';
}

/* ⭐書庫との連携。
   書庫の台帳（../../Taiga_PJ/書庫/catalog.js → window.CATALOG）の各本に `atlas` 欄＝この地図の出典の札
   （例 15_宮口）がある。ノードの出典と突き合わせて・スキャンしてある本なら「書庫」の箱を出す。
   頁の札＝引用元・本文の「p.44」「pp.44-45」「画像17」を押すと・その頁の画像がその場に出る。
   ⚠頁の数は本によって意味が違う（紙の頁／Kindle のスクリーンショットの通し番号）＝台帳の頁表（p 列）で引く。 */
const SHOKO_URL = '../../Taiga_PJ/書庫/index.html';
const PAGE_RE = /(?:pp?\.\s*|画像)(\d{1,3})(?:\s*[-‐−–〜~]\s*(\d{1,3}))?/g;
let CUR_SHOKO = [];               // いま説明欄に出しているノードの、書庫にある本

function shokoBooksOf(n){
  const C = window.CATALOG;
  if (!C || !C.books || !n || !n.sources) return [];
  return C.books.filter(b => b.atlas && n.sources.indexOf(b.atlas) >= 0 && b.pages && b.pages.length);
}
function shokoPage(b, p){
  const key = String(p);
  return b.pages.find(x => String(x.p) === key) || null;
}
/* 引用元と本文から、頁の札を集める（本ごとに・小さい順・重複なし） */
function shokoPagesIn(n){
  const found = new Set();
  const grab = (t) => { if (!t) return;
    for (const m of String(t).matchAll(PAGE_RE)){
      const a = parseInt(m[1], 10), z = m[2] ? parseInt(m[2], 10) : a;
      if (z >= a && z - a <= 12) for (let k = a; k <= z; k++) found.add(k); } };
  (n.refs || []).forEach(r => { grab(r.title); grab(r.note); });
  Object.keys(n.sections || {}).forEach(k => grab(n.sections[k]));
  return Array.from(found).sort((x, y) => x - y);
}
function pageChip(m0){
  if (!CUR_SHOKO.length) return m0;
  const m = new RegExp(PAGE_RE.source).exec(m0);
  if (!m) return m0;
  const p = m[1];
  const b = CUR_SHOKO.find(bk => shokoPage(bk, p));
  if (!b) return m0;
  return '<a class="pg" data-book="' + esc(b.id) + '" data-p="' + esc(p) + '" title="書庫の頁を見る（' +
         esc(b.title) + ' p.' + esc(p) + '）">' + m0 + '</a>';
}
function shokoBox(n){
  if (!CUR_SHOKO.length) return '';
  let h = '';
  CUR_SHOKO.forEach(b => {
    const pages = shokoPagesIn(n).filter(p => shokoPage(b, p));
    h += '<div class="shoko" data-book="' + esc(b.id) + '"><div class="ttl">書庫: <b>' + esc(b.title) + '</b>' +
         (b.sub ? ' ' + esc(b.sub) : '') + '（' + b.pages.length + '頁' + (b.text ? '・本文あり' : '') + '）' +
         '<a class="open" href="' + SHOKO_URL + '#b=' + encodeURIComponent(b.id) + '" target="_blank" rel="noopener">書庫で開く</a></div>';
    if (pages.length){
      h += '<div class="pgs">' + pages.map(p => '<span class="pg" data-book="' + esc(b.id) + '" data-p="' + p + '">p.' + p + '</span>').join('') + '</div>';
    } else {
      h += '<div class="nopage">このノードには頁の記載が無い（p.N・pp.N-M・画像N の形で書くと札になる）</div>';
    }
    h += '<div class="view"><div class="bar"><button class="prev" title="前の頁">&#9664;</button>' +
         '<span class="cur"></span><button class="next" title="次の頁">&#9654;</button>' +
         '<a class="open" target="_blank" rel="noopener">この頁を書庫で開く</a>' +
         '<button class="close" title="閉じる" style="margin-left:auto">×</button></div>' +
         '<img alt=""><div class="txt" hidden></div></div></div>';
  });
  return h;
}
/* 書庫の本文（OCR）は text/<id>.js（window.BOOK_TEXT[id][通し番号]）に焼いてある。押した本のぶんだけ1回読む */
const SHOKO_TXT = {};
function shokoText(b, i, cb){
  if (!b.text){ cb(null); return; }
  const done = () => { const T = (window.BOOK_TEXT || {})[b.id]; cb(T ? (T[String(i)] || null) : null); };
  if (SHOKO_TXT[b.id]){ done(); return; }
  const sc = document.createElement('script');
  sc.src = '../../Taiga_PJ/書庫/text/' + encodeURIComponent(b.id) + '.js';
  sc.onload = () => { SHOKO_TXT[b.id] = 'ok'; done(); };
  sc.onerror = () => { SHOKO_TXT[b.id] = 'err'; done(); };
  document.head.appendChild(sc);
}
function showShokoPage(box, b, p){
  const pg = shokoPage(b, p);
  if (!pg) return;
  const view = box.querySelector('.view');
  view.classList.add('on');
  view.querySelector('img').src = pg.src;
  view.querySelector('.cur').textContent = 'p.' + pg.p + '（' + pg.i + '/' + b.pages.length + '枚目）';
  view.querySelector('a.open').href = SHOKO_URL + '#b=' + encodeURIComponent(b.id) + '&i=' + pg.i;
  view.dataset.i = pg.i;
  box.querySelectorAll('.pg').forEach(c => c.classList.toggle('on', String(c.dataset.p) === String(pg.p)));
  const txt = view.querySelector('.txt');
  txt.hidden = true; txt.textContent = '';
  shokoText(b, pg.i, t => { if (t){ txt.textContent = t; txt.hidden = false; } });
}
function wireShoko(body){
  const C = window.CATALOG;
  if (!C) return;
  const byId = {}; (C.books || []).forEach(b => byId[b.id] = b);
  const boxOf = id => body.querySelector('.shoko[data-book="' + CSS.escape(id) + '"]');
  body.querySelectorAll('.pg').forEach(c => c.onclick = (ev) => {
    ev.preventDefault();
    const b = byId[c.dataset.book], box = boxOf(c.dataset.book);
    if (!b || !box) return;
    showShokoPage(box, b, c.dataset.p);
    box.scrollIntoView({ block: 'nearest' });
  });
  body.querySelectorAll('.shoko').forEach(box => {
    const b = byId[box.dataset.book]; if (!b) return;
    const view = box.querySelector('.view');
    const step = (d) => { const i = parseInt(view.dataset.i || '0', 10) + d;
      const pg = b.pages.find(x => x.i === i); if (pg) showShokoPage(box, b, pg.p); };
    // ⚠縦書き（rtl）の本は「次の頁」が左＝ボタンは前後のまま・向きは書庫に合わせない（ここは頁の数で前後）
    view.querySelector('.prev').onclick = () => step(-1);
    view.querySelector('.next').onclick = () => step(+1);
    view.querySelector('.close').onclick = () => { view.classList.remove('on');
      box.querySelectorAll('.pg').forEach(c => c.classList.remove('on')); };
  });
}

'''
rep('''function show(n){
  const side = document.getElementById('side');''', BODY + '''function show(n){
  const side = document.getElementById('side');''')

io.open(SRC, 'w', encoding='utf-8', newline='\n').write(s)
print('当てた: ' + SRC)

# ---------- build_map.py＝data.js と brain.js も焼く ----------
b = io.open(BM, encoding='utf-8').read()
if MARK not in b:
    old = '''    io.open(OUT, 'w', encoding='utf-8').write(
        json.dumps(data, ensure_ascii=False, indent=1))'''
    assert b.count(old) == 1
    b = b.replace(old, old + '''
    # ''' + MARK + ''' ⭐file:// で開くために、data.json と同じ中身を data.js（window.DATA）にも焼く。
    #   brain.svg も brain.js（window.BRAIN_SVG）に。書庫の catalog.js と同じ理屈（fetch が使えないため）
    io.open(os.path.join(ROOT, 'data.js'), 'w', encoding='utf-8', newline='\\n').write(
        '/* 生成物（tools/build_map.py）。手で直さない。data.json と同じ中身 */\\nwindow.DATA = ' +
        json.dumps(data, ensure_ascii=False, indent=1) + ';\\n')
    svg_path = os.path.join(ROOT, 'brain.svg')
    if os.path.exists(svg_path):
        io.open(os.path.join(ROOT, 'brain.js'), 'w', encoding='utf-8', newline='\\n').write(
            '/* 生成物（tools/build_map.py）。brain.svg（Patrick J. Lynch・CC BY 2.5）の中身 */\\nwindow.BRAIN_SVG = ' +
            json.dumps(io.open(svg_path, encoding='utf-8').read(), ensure_ascii=False) + ';\\n')
    print('data.js と brain.js も書いた')''')
    io.open(BM, 'w', encoding='utf-8', newline='\n').write(b)
    print('当てた: ' + BM)
