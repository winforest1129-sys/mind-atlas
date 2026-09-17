# -*- coding: utf-8 -*-
"""⭐ MIND の初期表示を「型ごとの六角形の島」にする（2026-09-17・燻太さんの指定）。

    python tools/patch_hex_islands.py          index.html に当てる（目印 HEXISLE-MIND-2026-09-17 で二度当てしない）

燻太さんの言葉＝「MINDのノードも多くなってきたから、LANDやALGAのように、ノードの種類ごとに
整列させて、力学の反映をやめることにしようか」。

何が変わるか
  ・初期表示＝種類ごとに六角格子で詰めた島（LAND/ALGA の HEXISLE-2026-09-14 と同じ作り）。
    上の段＝大きな島（最大の 1/4 以上）・下の段＝残り。島の上に種類名＋数の札（.isletick）。
    中の順＝論文は年代順（id が年で始まる）・ほかは ABC→五十音。「これから調べる」（stub）は別の島。
  ・全体では線を出さない（LAND/ALGA と同じ＝全体は一覧・フォーカスはつながりを読むところ）。
    検索で光らせたときだけ、そのノードの線を出す。
  ・レイアウト欄の既定を「型ごとの島」に。「保存した位置」（positions.js）と「ネットワーク（毎回計算）」は残す。
  ・build_positions.py はもう流さない（positions.js は「保存した位置」を選んだときだけ使う）。

⚠退避＝_backup/index.html.bak_20260917_六角島まえ
"""
import io, os, re, sys, shutil, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'index.html')
MARK = 'HEXISLE-MIND-2026-09-17'

s = io.open(SRC, encoding='utf-8').read()
if MARK in s:
    print('もう当ててある（' + MARK + '）'); sys.exit(0)

bak = os.path.join(ROOT, '_backup', 'index.html.bak_' + datetime.date.today().strftime('%Y%m%d') + '_六角島まえ')
os.makedirs(os.path.dirname(bak), exist_ok=True)
if not os.path.exists(bak):
    shutil.copyfile(SRC, bak)
    print('退避: ' + bak)

def rep(old, new, count=1):
    global s
    assert s.count(old) == count, ('当て先が %d 個（%d 個のはず）: ' % (s.count(old), count)) + old[:60]
    s = s.replace(old, new)

# ① レイアウト欄＝既定を「型ごとの島」に
rep('''      <select id="layout">
        <option value="saved">保存した位置</option>
        <option value="cose">ネットワーク</option>''',
'''      <select id="layout" title="全体の並べかた。⭐型ごとの島＝種類ごとに六角形に詰めて置く（線は出さない・計算しない）">
        <option value="isles">型ごとの島</option>   <!-- ''' + MARK + ''' -->
        <option value="saved">保存した位置</option>
        <option value="cose">ネットワーク（毎回計算）</option>''')

# ② 札のスタイル（.ringtick の直後）
rep('''          'text-background-padding':3, 'text-background-shape':'roundrectangle' } },
      /* PEEK-LIGHT''',
'''          'text-background-padding':3, 'text-background-shape':'roundrectangle' } },
      /* ⭐ ''' + MARK + ''' ── 六角形の島の札（種類名＋数）。輪の札と同じ作りで一回り大きい。
         ⚠札は自分で改行して 2 行にする（全角スペースで折らせると半字ぶん左に寄る＝LAND で踏んだ） */
      { selector:'.isletick', style:{
          'label':'data(label)', 'shape':'rectangle', 'width':1, 'height':1,
          'background-opacity':0, 'border-width':0, 'events':'no',
          'color':'data(color)', 'font-size':44, 'font-weight':'bold',
          'min-zoomed-font-size':0, 'text-wrap':'wrap', 'text-max-width':9999,
          'text-justification':'center', 'line-height':1.15,
          'text-valign':'center', 'text-halign':'center',
          'text-background-color':BG, 'text-background-opacity':0.86,
          'text-background-padding':6, 'text-background-shape':'roundrectangle' } },
      /* PEEK-LIGHT''')

# ③ 最初の並べかた
rep('''  const _sel0 = document.getElementById('layout');
  if (SAVED && _sel0 && _sel0.value === 'saved'){''',
'''  const _sel0 = document.getElementById('layout');
  if (_sel0 && _sel0.value === 'isles'){          // ''' + MARK + ''' ⭐既定＝型ごとの島（計算しない・線なし）
    applyIsleLayout();
  } else if (SAVED && _sel0 && _sel0.value === 'saved'){''')

# ④ レイアウト欄を変えたとき
rep('''  document.getElementById('layout').onchange = e => cy.layout(layoutOpts(e.target.value)).run();''',
'''  document.getElementById('layout').onchange = e => {          // ''' + MARK + '''
    if (FOCUS) exitFocus();
    if (e.target.value === 'isles'){ applyIsleLayout(); return; }
    leaveIsleMode();
    cy.layout(layoutOpts(e.target.value)).run();
  };''')

# ⑤ ズームで島の札の字を当て直す（全体表示でも）
rep('''  cy.on('zoom', () => {
    if (!FOCUS && !cy.elements('.dim').length) return;''',
'''  cy.on('zoom', () => {                          // ''' + MARK + ''' ⭐島の札は zoom に合わせて画面で 20px ほどに
    clearTimeout(_isleTimer);
    _isleTimer = setTimeout(fitIsleLabels, 80);
    if (!FOCUS && !cy.elements('.dim').length) return;''')

# ⑥ 検索で光らせたとき＝島では線が無いので、光らせたノードの線だけ出す
rep('''  cy.elements().addClass('dim');
  hit.removeClass('dim');
  hit.neighborhood().removeClass('dim');       // 直接つながっているノード
  hit.connectedEdges().removeClass('dim');     // その線''',
'''  cy.elements().addClass('dim');
  cy.nodes('.isletick').removeClass('dim');    // ''' + MARK + ''' 島の札は薄くしない
  hit.removeClass('dim');
  hit.neighborhood().removeClass('dim');       // 直接つながっているノード
  hit.connectedEdges().removeClass('dim');     // その線
  if (ISLE_MODE && !FOCUS) hit.connectedEdges().style('display', 'element');   // ''' + MARK + ''' 島では線を伏せているので、光らせた線だけ出す''')
rep('''  cy.elements().not('.dim').selectify();
  cy.nodes().not('.dim').grabify();''',
'''  cy.elements().not('.dim').selectify();
  cy.nodes().not('.dim').not('.isletick').grabify();   // ''' + MARK)

# ⑦ PEEK-LIGHT の受け口＝島の札は押しても何もしない・数えない
rep('''  if (!el || !el.length || el.hasClass('ringtick')) return;''',
    '''  if (!el || !el.length || el.hasClass('ringtick') || el.hasClass('isletick')) return;   // ''' + MARK)
rep('''  const vis = cy.elements(':visible').not('.ringtick');
  const eg  = el.connectedEdges().filter(':visible');''',
'''  const vis = cy.elements(':visible').not('.ringtick').not('.isletick');   // ''' + MARK + '''
  const eg  = el.connectedEdges().filter(':visible');''')

# ⑧ clearDim＝島の札は掴ませない・光らせたときに出した線をまた伏せる
rep('''  cy.elements().removeClass('dim').selectify();
  // ⚠薄くしたときに外した「掴める」を必ず戻す。⚠輪の札（.ringtick）は掴ませない
  cy.nodes().not('.ringtick').grabify();''',
'''  cy.elements().removeClass('dim').selectify();
  // ⚠薄くしたときに外した「掴める」を必ず戻す。⚠輪の札（.ringtick）・島の札（.isletick）は掴ませない
  cy.nodes().not('.ringtick').not('.isletick').grabify();   // ''' + MARK + '''
  hideIsleEdges();                                          // ''' + MARK + ''' 光らせたときに出した線を伏せ直す''')

# ⑨ 字の大きさ＝島の札は別に扱う
rep('''  const tgt = (FOCUS ? cy.nodes(':visible') : cy.nodes().not('.dim')).not('.ringtick');''',
    '''  const tgt = (FOCUS ? cy.nodes(':visible') : cy.nodes().not('.dim')).not('.ringtick').not('.isletick');   // ''' + MARK)
rep('''  cy.nodes().removeStyle('font-size');
  cy.nodes().removeStyle('min-zoomed-font-size');''',
'''  cy.nodes().not('.isletick').removeStyle('font-size');            // ''' + MARK + ''' 島の札の字は zoom で当てるので触らない
  cy.nodes().not('.isletick').removeStyle('min-zoomed-font-size');''')

# ⑩ フォーカスから出たとき＝線を伏せ直す（applyFilters の中で効く）
rep('''  applyFilters();                      // ⭐**いまのチェックから**計算し直す
  clearLitLabels();
  cy.zoom(snap.zoom);''',
'''  applyFilters();                      // ⭐**いまのチェックから**計算し直す（島なら線も伏せ直る）
  clearLitLabels();
  fitIsleLabels();                     // ''' + MARK + '''
  cy.zoom(snap.zoom);''')

# ⑪ applyFilters の末尾＝島では線を伏せる（⚠フォーカス中・張り直し中は触らない）
rep('''  if (typeof FOCUS !== 'undefined' && FOCUS && !FOCUS_BUSY) refocus();
}''',
'''  if (typeof FOCUS !== 'undefined' && FOCUS && !FOCUS_BUSY) refocus();
  hideIsleEdges();                     // ''' + MARK + '''
}''')

# ⑫ layoutOpts＝'isles' が渡ってきても計算しない
rep('''function layoutOpts(name){
  // ⭐保存した位置＝座標を置くだけ。計算しない
  if (name === 'saved'){''',
'''function layoutOpts(name){
  // ⭐型ごとの島＝applyIsleLayout が preset で置く。まちがって渡ってきたら座標をそのまま使う
  if (name === 'isles') return { name:'preset', fit:true, padding:80 };   // ''' + MARK + '''
  // ⭐保存した位置＝座標を置くだけ。計算しない
  if (name === 'saved'){''')

# ⑬ 本体＝島のレイアウト（layoutOpts の前に置く）
BODY = r'''
/* ============================================================================
   ⭐⭐⭐ ''' + MARK + r''' ── 初期表示＝型ごとの六角形の島（燻太さんの指定・LAND/ALGA と同じ作り）

   ⭐燻太さんの言葉（2026-09-17）＝「MINDのノードも多くなってきたから、LANDやALGAのように、
     ノードの種類ごとに整列させて、力学の反映をやめることにしようか」。
   ⭐役目を分ける ── **全体＝何が登録されているかの一覧**（線なし・計算しない）／
     **フォーカス＝つながりを読むところ**（線あり・輪）。検索で光らせたときは、そのノードの線だけ出す。
   ⭐島＝六角格子（行を半分ずらす・colGap 112・行間 112×0.866）で詰めた六角形。
     席は 1+3R(R+1) ≥ N の最小の R、余る席は上下の行を交互に丸ごと外す。
     中の順＝論文は年代順（id が年で始まる）・ほかは ABC→五十音（左→右・上→下）。
   ⭐島どうし＝2 段。上の段＝大きな島（最大の 1/4 以上）を ORDER の順に横へ、下の段＝残り。
     中心の間隔の下限＝112×16（札が引きでも重ならない幅）。
   ⭐「これから調べる」（stub）は別の島（フィルタの区分と同じ）。
   ⭐島の上に種類名＋数の札（.isletick）。字は zoom に合わせて 22/z（44〜640px）＝引いても画面で 20px ほど。
   ⚠positions.js は「保存した位置」を選んだときだけ使う。build_positions.py はもう流さない。
   ============================================================================ */
let ISLE_MODE = false;          // いま全体を「型ごとの島」で置いているか
let ISLES = null;               // 島ごとの中心と大きさ（札を置き直すため）
let _isleTimer = null;
const ISLE_COLGAP = 112;
const isleTypes = () => ORDER.concat(['これから調べる']);   // ⚠ORDER はこの下で定義されるので、使うときに引く

function isleTypeOf(n){ return n.data('stub') ? 'これから調べる' : n.data('type'); }

/* 種類ごとの並び＝論文は年代順（id が「2022 Templeton」の形）・ほかは ABC→五十音 */
function isleSort(type, list){
  const key = n => String(n.data('label') || n.id());
  return list.slice().sort((a, b) => key(a).localeCompare(key(b), 'ja', { numeric:true }));
}

function applyIsleLayout(){
  if (!cy) return;
  if (FOCUS) exitFocus();
  clearDim();
  cy.remove('.isletick');
  const hexW = ISLE_COLGAP, hexH = ISLE_COLGAP * 0.866;
  const all = cy.nodes().not('.ringtick').not('.isletick');
  const groups = isleTypes().map(t => ({ type:t, list: isleSort(t, all.filter(n => isleTypeOf(n) === t).toArray()) }))
                           .filter(g => g.list.length);
  // ① 島ごとに六角格子の席を作る
  const isles = groups.map(g => {
    const list = g.list, N = list.length;
    let R = 0; while (1 + 3 * R * (R + 1) < N) R++;
    let rows = []; for (let k = -R; k <= R; k++) rows.push(2 * R + 1 - Math.abs(k));
    let top = 0, bot = 0;
    const sum = a => a.reduce((x, v) => x + v, 0);
    while (rows.length > 1){
      const first = rows[0], last = rows[rows.length - 1];
      if (top <= bot && sum(rows) - first >= N){ rows.shift(); top++; }
      else if (sum(rows) - last >= N){ rows.pop(); bot++; }
      else break;
    }
    const cells = []; let i = 0;
    for (let r = 0; r < rows.length && i < N; r++){
      const len = Math.min(rows[r], N - i);
      for (let c = 0; c < len; c++) cells.push({ r:r, c:c, len:len });
      i += len;
    }
    const used = cells.length ? cells[cells.length - 1].r + 1 : 1;
    const wide = Math.max.apply(null, rows.slice(0, used));
    const w = wide * hexW, h = used * hexH;
    const rel = list.map((n, j) => { const cl = cells[j];
      return { x:(cl.c - (cl.len - 1) / 2) * hexW, y:(cl.r - (used - 1) / 2) * hexH }; });
    return { type:g.type, list:list, rel:rel, w:w, h:h, x:0, y:0 };
  });
  // ② 島を 2 段に並べる（円詰めは小島が寄り合って札が重なるのでしない＝LAND で踏んだ）
  const maxN = Math.max.apply(null, isles.map(c => c.list.length));
  const bigs = isles.filter(c => c.list.length >= maxN / 4), smalls = isles.filter(c => c.list.length < maxN / 4);
  const gap = hexW * 1.2, minPitch = hexW * 16;
  const rowPlace = (arr, y, pitchMin) => {
    let x = 0; const xs = [];
    arr.forEach((c, k) => {
      if (k) x += Math.max(pitchMin, arr[k - 1].w / 2 + c.w / 2 + gap);
      xs.push(x);
    });
    const mid = xs.length ? (xs[0] + xs[xs.length - 1]) / 2 : 0;
    arr.forEach((c, k) => { c.x = xs[k] - mid; c.y = y; });
  };
  const hBig = bigs.length ? Math.max.apply(null, bigs.map(c => c.h)) : 0;
  const hSml = smalls.length ? Math.max.apply(null, smalls.map(c => c.h)) : 0;
  rowPlace(bigs, 0, 0);
  if (smalls.length) rowPlace(smalls, hBig / 2 + hexH * 2.2 + hSml / 2, minPitch);
  // ③ 置く
  cy.batch(() => {
    isles.forEach(c => c.list.forEach((n, j) => n.position({ x:c.x + c.rel[j].x, y:c.y + c.rel[j].y })));
  });
  ISLES = isles.map(c => ({ type:c.type, n:c.list.length, x:c.x, y:c.y, w:c.w, h:c.h }));
  ISLE_MODE = true;
  addIsleLabels();
  hideIsleEdges();
  cy.layout({ name:'preset', fit:true, padding:80 }).run();
  setTimeout(() => { cy.fit(cy.elements(':visible'), 80); fitIsleLabels(); }, 60);
}

/* 島の札（種類名＋数）を置く。⚠掴めない・選べない・押せない（events:no） */
function addIsleLabels(){
  if (!ISLES) return;
  cy.remove('.isletick');
  const hexH = ISLE_COLGAP * 0.866;
  cy.add(ISLES.map(c => ({ group:'nodes', classes:'isletick',
    data:{ id:'__isle_' + c.type, label:c.type + '\n' + c.n,
           color:(c.type === 'これから調べる' ? SUB : (TYPE_COLOR[c.type] || '#c08a3e')) },
    position:{ x:c.x, y:c.y - c.h / 2 - hexH * 0.75 },
    grabbable:false, selectable:false })));
  fitIsleLabels();
}

/* 島の札の字＝どの zoom でも画面で 20px ほど */
function fitIsleLabels(){
  if (!cy || !ISLE_MODE) return;
  const z = cy.zoom() || 1;
  cy.nodes('.isletick').style({ 'font-size': Math.max(44, Math.min(640, 22 / z)), 'min-zoomed-font-size': 0 });
}

/* 全体（島）では線を出さない。⚠フォーカス中・張り直し中は触らない（隣は見えている線ぞいに数えるため） */
function hideIsleEdges(){
  if (!cy || !ISLE_MODE) return;
  if (typeof FOCUS !== 'undefined' && (FOCUS || FOCUS_BUSY)) return;
  cy.edges().style('display', 'none');
}

/* 島をやめて別の並べかたへ（保存した位置・毎回計算）＝札を片づけ・線を戻す */
function leaveIsleMode(){
  if (!cy) return;
  ISLE_MODE = false; ISLES = null;
  cy.remove('.isletick');
  cy.edges().style('display', 'element');
  applyFilters();
}
'''
rep('''function layoutOpts(name){''', BODY + '''
function layoutOpts(name){''')

io.open(SRC, 'w', encoding='utf-8', newline='\n').write(s)
print('当てた: ' + SRC)
