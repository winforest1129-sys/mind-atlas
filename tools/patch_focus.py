# -*- coding: utf-8 -*-
r"""mind-atlas（MIND）に⭐フォーカス機能を足す（2026-09-09・燻太さんの指定）。

    python tools/patch_focus.py            当てる（⭐何度流しても1回ぶん）
    python tools/patch_focus.py --見るだけ  当てずに、当たるかどうかだけ見る

⭐**燻太さんの言葉**＝「MINDの方にも、LANDで実装した改良版フォーカス機能を実装してほしい。
  ただし、ネットワークの初期状態に関しては現状いまのMINDのままでいいよ。」

⭐**移した元**＝`研究室関連\Plant-gene-atlas\index.html`（LAND）の
  `enterFocus` / `enterFocusPair` / `exitFocus` / `placeFocusRing` 一式。

⚠⚠**そのままでは移せなかったところ（2つ）と、その当てかた**

1. ⭐**輪の並べかた** ── LAND は「上半分＝論文を年代順／下半分＝それ以外を種類ごと」。
   ⚠**MIND には『論文』型も『年』も無い。**
   ⭐**燻太さんの指定（2026-09-09）＝一周ぜんぶを種類ごとに固める。**
   ⭐種類の順は `ORDER`（予感→書物→人物→理論→症例→実験→用語）を使い回す。
   ⏳入れ替えたいときは `ORDER` の1か所だけ触る（一覧パネルの並びと連動する）。

2. ⭐**半径** ── LAND は「証拠の強さ（強い証拠／弱い証拠／言及）」。
   ⚠MIND に証拠の段は無いが、⭐**線に `強さ`（強／標準／弱）がある。**
   ⭐**半径をそれに当てた**（強が内・弱が外）。⭐既定は入り。
   ⚠**輪にすると、力学レイアウトのばね（`PULL`）で見えていた強さが消える。**
     ⭐半径に移すことで、そこを拾い直している。

⚠**当てなかったもの（＝MIND では意味を持たないもの）**
- ⭐LAND の 2026-09-08「フォーカスに入ったら『言及』以外の線を自動で出す」は、
  ⚠**MIND に線の種類のフィルタが無いので、当てるところが無い**（＝何もしない）。
  ⭐**初期状態が「線あり」のままでよい**という燻太さんの指定とも、そろっている。
- ⭐LAND の「年の目盛り」→ ⭐**MIND では『種類の札』に置きかえた**（種類名＋件数）。
- ⭐LAND の「証拠の段＝論文ノードの色の濃さ」→ ⚠**当てない。**
  ⭐MIND でいちばん大事な色は🔴**赤線（対立・批判）**で、それは輪の中でも赤いまま出る。
  ⚠色をかぶせると、型の色（用語・人物・理論…）を潰してしまう。

⚠**LAND で踏んだ罠は、ぜんぶ持ちこんである**（コメントに残した）:
  ①見えている線ぞいにしか辿らない ②数える前にフィルタだけの見えかたに戻す
  ③出たあとに発火する処理は世代番号で捨てる ④コレクションのままsortしない
  ⑤大きくした字のまま fit しない（堂々巡り）
"""
import io, os, sys

# ⚠Windowsの既定は cp932 なので、⭐星や矢印を print すると落ちる（build_positions.py と同じ手当て）。
if not (getattr(sys.stdout, 'encoding', '') or '').lower().startswith('utf'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'index.html')

# ⭐この道具しか書かない目印で「もう当たっている」を見る。
#   ⚠LAND で、共通の行を目印にして⭐**誤って「当たっている」と言った**ことがある。
MARK = 'MIND-FOCUS-RING'

HEADER_HTML = """      <!-- ⭐⭐フォーカス（2026-09-09・LAND から移した）。
           1つ選んで、つながっている相手だけの輪にする -->
      <input type="search" id="focus" placeholder="フォーカス（2つ書くと共通の相手）"
             title="用語を1つ選ぶと、つながっている相手だけの輪にする（ノードのダブルクリックでも同じ）。カンマで2つ書くと、両方につながっているものだけを出す（例: 島皮質, 共感）">
      <button class="btn" id="focusWider" hidden
              title="もう1手先までひろげる">もう1手</button>
      <button class="btn" id="focusBack" hidden
              title="ひとつ前にフォーカスしていた用語に戻る">&#8592; 一歩</button>
      <button class="btn" id="focusOut" hidden
              title="元のネットワークに戻る（Esc キー・背景のダブルクリックでも同じ）">もどる</button>
      <button class="btn" id="focusPng" hidden
              title="いま見えている図をPNGで保存する">画像</button>
      <label id="focusStrWrap" hidden class="qhit"
             title="輪の半径を、線の強さにする（強いほど内側）"><input
             type="checkbox" id="focusStr" checked> 強さを半径に</label>
      <span id="focusTrail" class="qhit"></span>
"""

# ⭐種類の札（LAND の「年の目盛り」に当たるもの）。
#   ⚠**薄い灰色の小さな字では、まったく気づけなかった**（LAND・燻太さんの報告）ので、
#     ⭐色をつけ、⭐字も大きくする。⭐`events:'no'` で背景クリックを邪魔しない。
RING_STYLE = """      { selector:'.ringtick', style:{
          'label':'data(label)', 'shape':'rectangle', 'width':1, 'height':1,
          'background-opacity':0, 'border-width':0, 'events':'no',
          'color':'#c08a3e', 'font-size':16, 'font-weight':'bold',
          'min-zoomed-font-size':0, 'text-wrap':'wrap', 'text-max-width':120,
          'text-valign':'center', 'text-halign':'center',
          'text-background-color':BG, 'text-background-opacity':0.86,
          'text-background-padding':3, 'text-background-shape':'roundrectangle' } },
"""

JS = """
/* ============================================================================
   MIND-FOCUS-RING ── ⭐⭐⭐フォーカス（周りだけ見る）
   2026-09-09・燻太さんの指定で LAND（Plant-gene-atlas）から移した。

   ⚠**なぜ要るか**＝引きで見れば米粒、拡大すれば相手が画面の外。
   ⭐1つ選んで、つながる相手だけにすれば両方いっぺんに解ける。

   ⭐**入る**＝ノードのダブルクリック／フォーカス欄に名前＋Enter／`もう1手`
   ⭐**出る**＝背景の**ダブル**クリック／`Esc`／`もどる`
     ⚠1回押しで出るようにすると、⭐**見ているだけのつもりで抜けてしまう**
       （LAND・2026-09-05 の燻太さんの報告で変えた）。

   ⚠⚠**ノードを消さない。伏せる。**⭐帰りは控えた座標を置き直すだけ（計算ゼロ）。
   ⭐控えるのは**座標・ズーム・視点**の3つ。
   ⚠**表示/非表示は控えない** ── 出るときに `applyFilters()` で
     **いまのチェックから計算し直す**（フォーカス中に触られた変更が活きる）。
   ============================================================================ */
let FOCUS = null;          // いまフォーカスしているノードのid
let FOCUS_SNAP = null;     // 入る前の座標・ズーム・視点
let FOCUS_DEPTH = 1;       // 何手先まで見るか（1〜3）
let FOCUS_TRAIL = [];      // パンくず
let FOCUS_BUSY = false;    // 張り直しの再入を止める
let FOCUS_GEN = 0;         // ⚠あとから発火する処理を捨てるための世代番号
let _bgTap = 0;            // 背景のダブルクリックを数える

/* ⭐**いまの姿を控える。**⚠**2度目からは控え直さない** ──
   フォーカス中に別の用語へ渡り歩いても、⭐背景のダブルクリック一発で
   「最初に入る前」に戻れるようにするため。 */
function snapNow(){
  if (FOCUS_SNAP) return;
  const pos = {};
  cy.nodes().forEach(n => { const p = n.position(); pos[n.id()] = [p.x, p.y]; });
  FOCUS_SNAP = { pos:pos, zoom:cy.zoom(), pan:Object.assign({}, cy.pan()) };
}

/* ⭐**フィルタだけの見えかたに戻す**（フォーカスで伏せたぶんを解く）。
   ⚠⚠**これをせずに隣を数えると「もう1手」が効かない**（LAND で踏んだ罠）。
     1手目で周りを伏せてしまうので、⭐**その先が `visible()` に引っかからない。**
     実測：1手 29件 → もう1手 29件のまま増えなかった。 */
function restoreFilterVisibility(){
  cy.elements().style('display', 'element');
  applyFilters();          // ⚠FOCUS_BUSY 中なので、この中の張り直しは走らない
}

/* ⭐⭐⭐**フォーカスの並べかた ── 中心＋輪**（2026-09-09・燻太さんの指定）

   ⭐**まん中**＝フォーカスした用語。
   ⭐**輪**＝つながっている相手。⭐**一周ぜんぶを種類ごとに固める。**
     ⭐種類の並びは `ORDER`（予感→書物→人物→理論→症例→実験→用語）。
     ⏳**種類の占める角度＝その数の割合**になるので、⭐**円グラフのように読める。**

   ⚠**LAND とここが違う。**LAND は上半分＝論文（年代順）／下半分＝それ以外だった。
     ⭐MIND には『論文』型も『年』も無く、⭐**書物は1ノードにつき1〜2冊しか付かない**ので、
     上半分を出どころに割り当てると⭐**180°に1〜2個だけ**という、すかすかの絵になる。
     ⭐だから一周を使う。

   ⭐**「もう1手」でひろげたぶんは外側の輪**（近い相手ほど内側）。
   ⚠画面の座標は**下がプラス**なので、上向きは `y` が負。 */
const FRING = { rMin:250, ringGap:120, arcGap:96, hopGap:120, strGap:120, maxRings:1 };

/* ⚠**半径は数に合わせて決める**（LAND・2026-09-05・描いて分かった）。
   ⭐固定の半径だと、⭐**多いときに輪が何重にも割れて「輪」に見えない。**
   ⭐一周（2πr）に n 個を arcGap 間隔で並べたい。 */
function ringRadius(n){
  return Math.max(FRING.rMin, (Math.max(n, 1) * FRING.arcGap) / (2 * Math.PI * FRING.maxRings));
}

/* ⭐一周にそって等間隔に置く。⭐12時から時計回り。 */
function placeRing(list, r){
  const n = list.length;
  if (!n) return;
  for (let k = 0; k < n; k++){
    const phi = (Math.PI / 2) - (2 * Math.PI * k) / n;   // 12時 → 3時 → 6時 → 9時
    list[k].position({ x:Math.cos(phi) * r, y:-Math.sin(phi) * r });
  }
}

/* ⭐⭐**半径＝線の強さ**（強いほど内側）。⭐LAND の「強さを半径に」を移したもの。
   ⚠**輪にすると、力学レイアウトのばね（`PULL`）で見えていた強さが消える。**
     ⭐そこを半径で拾い直す。⭐段は 強=0／標準=1／弱=2。 */
function strTier(n, center){
  let best = 9;
  center.edgesWith(n).forEach(e => {
    const w = e.data('w');
    const r = (w === '強') ? 0 : (w === '弱') ? 2 : 1;
    if (r < best) best = r;
  });
  return best === 9 ? 1 : best;
}
function strStep(n, center){
  const box = document.getElementById('focusStr');
  if (!box || !box.checked) return 0;
  return strTier(n, center);
}

/* ⭐⭐**種類の札**（LAND の「年の目盛り」に当たるもの）。
   ⭐その種類の弧のまん中の角度に、⭐**種類名と件数**を輪の外へ立てる。
   ⚠**半径が変わっているだけでは、効いているか分からない**（LAND での燻太さんの報告）。
     ⭐円グラフとして読ませたいのだから、⭐**どの扇が何なのか**は書いてある必要がある。 */
function addTypeTicks(sorted, r, outer){
  if (sorted.length < 5) return;
  const n = sorted.length;
  const runs = [];
  sorted.forEach((node, k) => {
    const t = node.data('type') || '不明';
    const last = runs[runs.length - 1];
    if (last && last.t === t) last.to = k; else runs.push({ t:t, from:k, to:k });
  });
  const add = [];
  runs.forEach((g, i) => {
    if (g.to - g.from + 1 < 2 && runs.length > 4) return;   // ⭐1個だけの種類は札を出さない
    const mid = (g.from + g.to) / 2;
    const phi = (Math.PI / 2) - (2 * Math.PI * mid) / n;
    /* ⚠**輪の外へ出しすぎると、`fit` がそこまで入れようとして縮尺が落ちる**
       （2026-09-09に絵で見て気づいた。zoom 0.53 まで引かれて線の名前が読めなかった）。
       ⭐**実際に使ったいちばん外の半径のすぐ外**に立てる。 */
    const rr = outer + 110;
    add.push({ group:'nodes', classes:'ringtick',
               data:{ id:'__tick_' + i + '_' + g.t,
                      label:g.t + ' ' + (g.to - g.from + 1) },
               position:{ x:Math.cos(phi) * rr, y:-Math.sin(phi) * rr },
               grabbable:false, selectable:false });
  });
  if (add.length) cy.add(add);
}

/* ⭐種類ごとに固めて並べ替える。⚠⚠**素の配列に直してから並べ替える。**
   ⭐cytoscape のコレクションのまま `sort`／`concat` すると、
     ⚠**位置を入れても全部が同じ場所に重なる**（LAND で踏んだ。⭐エラーは出ない）。 */
function sortByType(arr){
  return arr.slice().sort((a, b) => {
    const ia = ORDER.indexOf(a.data('type')), ib = ORDER.indexOf(b.data('type'));
    return ((ia < 0 ? 99 : ia) - (ib < 0 ? 99 : ib)) ||
           a.data('label').localeCompare(b.data('label'), 'ja');
  });
}

function placeFocusRing(center, keepN, lvl){
  center.position({ x:0, y:0 });
  const byHop = {};
  keepN.forEach(n => {
    const h = lvl[n.id()] || 0;
    if (!h) return;                       // まん中は置いた
    (byHop[h] = byHop[h] || []).push(n);
  });
  let r = FRING.rMin;
  Object.keys(byHop).map(Number).sort((a, b) => a - b).forEach(h => {
    const all = sortByType(byHop[h]);
    r = Math.max(r, ringRadius(all.length));
    let i = 0;
    while (i < all.length){
      const cap = Math.max(4, Math.floor(2 * Math.PI * r / FRING.arcGap));
      const slice = all.slice(i, i + cap);
      placeRing(slice, r);
      // ⭐強さを半径に（内側ほど強い）。⚠角度は種類の順のままなので、扇は崩れない
      let outer = r;
      slice.forEach(n => {
        const s = strStep(n, center);
        if (!s) return;
        const p = n.position(), d = Math.hypot(p.x, p.y) || 1;
        const rr = r + s * FRING.strGap;
        if (rr > outer) outer = rr;
        n.position({ x:p.x / d * rr, y:p.y / d * rr });
      });
      if (h === 1 && i === 0) addTypeTicks(slice, r, outer);
      i += slice.length;
      r += FRING.ringGap;
    }
    r += FRING.hopGap;                    // 手数の切れ目をすこし空ける
  });
}
"""

JS2A = """
/* ⭐⭐⭐フォーカス中のまん中を、**そのノード自身の色**で点滅させる（LAND から）。
   ⚠⚠**canvas なので CSS のアニメーションは効かない。**cytoscape の animate を繰り返す。
   ⭐塗りではなく **overlay（上にかぶせる光）**を呼吸させるので、
     ⚠ノード本来の色（型の色）を潰さない。 */
let FOCUS_BLINK = null;
function stopFocusBlink(){
  if (!FOCUS_BLINK) return;
  clearInterval(FOCUS_BLINK.timer);
  const ns = FOCUS_BLINK.nodes;
  try {
    ns.stop();
    ns.removeStyle('overlay-color').removeStyle('overlay-opacity')
      .removeStyle('overlay-padding');
  } catch(e){}
  FOCUS_BLINK = null;
}
function startFocusBlink(ns){
  stopFocusBlink();
  if (!ns || !ns.length) return;
  ns.forEach(n => n.style({ 'overlay-color': n.style('background-color') || '#888',
                            'overlay-opacity':0.34, 'overlay-padding':10 }));
  let up = false;
  const timer = setInterval(() => {
    if (!FOCUS || !ns.length){ stopFocusBlink(); return; }
    up = !up;
    ns.animate({ style:{ 'overlay-opacity': up ? 0.48 : 0.10,
                         'overlay-padding': up ? 18 : 7 } },
               { duration:560, queue:false });
  }, 600);
  FOCUS_BLINK = { timer:timer, nodes:ns };
}

/* ⭐⭐**光らせたもの・フォーカス中は、画面の上で字の大きさを保つ**（LAND から）。
   ⚠輪は数が多いほど大きくなるので、⭐**引きで名前が消えてしまう**
     （`min-zoomed-font-size:7` を割る）。⭐ズームで割った字の大きさを当てる。 */
function fitLitLabels(){
  if (!cy) return;
  const spot = cy.elements('.dim').length > 0;
  if (!FOCUS && !spot) return;
  const z = cy.zoom() || 1;
  const f = Math.max(11, Math.min(28, 11.5 / z));
  const tgt = (FOCUS ? cy.nodes(':visible') : cy.nodes().not('.dim')).not('.ringtick');
  tgt.style({ 'font-size': f, 'min-zoomed-font-size': 0 });
  cy.nodes('.ringtick').style(
    { 'font-size': Math.max(15, Math.min(38, 17 / z)), 'min-zoomed-font-size': 0 });
  /* ⭐⭐**線の名前（rel）も読める大きさにする**（2026-09-09・絵で見て足した）。
     ⚠⚠**輪の中でいちばん読みたいのは、線に書いてある関係のほう**
       （`対立` `批判` `土台` …）。⭐全体の見た目は触らない ── ここで当てるのは
       **フォーカス中か、光らせているときの、見えている線だけ**。 */
  const eg = FOCUS ? cy.edges(':visible') : cy.edges().not('.dim');
  eg.style({ 'font-size': Math.max(9, Math.min(20, 9.5 / z)), 'min-zoomed-font-size': 0 });
}
function clearLitLabels(){
  if (!cy) return;
  cy.nodes().removeStyle('font-size');
  cy.nodes().removeStyle('min-zoomed-font-size');
  cy.edges().removeStyle('font-size');       // ⚠線のほうも必ず戻す
  cy.edges().removeStyle('min-zoomed-font-size');
}

function focusUI(on){
  ['focusWider','focusOut','focusPng','focusStrWrap'].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.hidden = !on;
  });
  const b = document.getElementById('focusBack');
  if (b) b.hidden = !(on && FOCUS_TRAIL.length > 1);
  if (!on) drawTrail();
}
"""

JS2B = """
/* ⭐パンくずを出す。⚠長くなるので後ろの4つだけ。 */
function drawTrail(){
  const el = document.getElementById('focusTrail');
  if (!el) return;
  if (!FOCUS || FOCUS_TRAIL.length < 2){ el.textContent = ''; return; }
  const t = FOCUS_TRAIL.slice(-4);
  el.textContent = (FOCUS_TRAIL.length > 4 ? '… → ' : '') + t.join(' → ');
}
function focusStepBack(){
  if (FOCUS_TRAIL.length < 2) return;
  FOCUS_TRAIL.pop();
  const id = FOCUS_TRAIL.pop();
  const n = id && cy.getElementById(id);
  if (n && n.length) enterFocus(n, 1); else exitFocus();
}
/* ⭐名前からノードを探す。⚠MIND には別名（`namesOf`）が無いのでラベルだけ見る。 */
function findByName(s){
  const k = String(s || '').trim().toLowerCase();
  if (!k) return null;
  const hit = cy.nodes().filter(n => n.data('label').toLowerCase() === k);
  if (hit.length) return hit[0];
  const part = cy.nodes().filter(n => n.data('label').toLowerCase().indexOf(k) >= 0);
  return part.length ? part[0] : null;
}

/* ⭐⭐⭐**2つの用語の「共通の隣」だけを見る**（LAND のアイデア②を移した）。
   ⭐フォーカス欄に `島皮質, 共感` のようにカンマで2つ入れると、
   ⭐**両方につながっているものだけ**を出す。
   ⭐**置きかた**＝左に A、右に B、⭐**まん中の縦の列に共通の相手**（種類ごと）。 */
function enterFocusPair(a, b){
  if (!cy || !a || !b || FOCUS_BUSY) return;
  FOCUS_BUSY = true;
  const gen = ++FOCUS_GEN;
  try {
    snapNow();
    clearDim();
    cy.remove('.ringtick');
    restoreFilterVisibility();
    // ⚠⚠**見えている線ぞいにしか辿らない**（`neighborhood()` は線が隠れていても隣を返す）
    const nbrs = x => x.connectedEdges().filter(e => e.visible())
                       .connectedNodes().filter(n => n.visible() && n.id() !== x.id());
    const na = nbrs(a), nb = nbrs(b);
    const both = na.filter(n => nb.contains(n) && n.id() !== a.id() && n.id() !== b.id());
    FOCUS = a.id();
    const keepN = both.union(a).union(b);
    const keepE = cy.edges().filter(e => e.visible() &&
                    keepN.contains(e.source()) && keepN.contains(e.target()));
    const keep = keepN.union(keepE);
    cy.batch(() => {
      cy.elements().not(keep).style('display', 'none');
      keep.style('display', 'element');
    });
    const col = sortByType(both.toArray());   // ⚠素の配列に直してから並べる
    const gap = 110;
    const h = Math.max(1, col.length - 1) * gap;
    col.forEach((n, i) => n.position({ x:0, y:-h / 2 + i * gap }));
    const D = Math.max(400, h * 0.42);
    a.position({ x:-D, y:0 });
    b.position({ x: D, y:0 });
    cy.layout({ name:'preset', fit:true, padding:80 }).run();
    setTimeout(() => {
      if (gen !== FOCUS_GEN || !FOCUS) return;
      clearLitLabels();                     // ⚠大きくした字のまま fit しない（堂々巡り）
      cy.fit(cy.elements(':visible'), 80);
      fitLitLabels();
    }, 60);
    const box = document.getElementById('focus');
    if (box) box.value = a.data('label') + ', ' + b.data('label');
    FOCUS_TRAIL = [a.id() + ' × ' + b.id()];
    drawTrail();
    focusUI(true);
    startFocusBlink(a.union(b));
    hitCount(both.length
      ? '「' + a.data('label') + '」と「' + b.data('label') + '」に共通するもの ' +
        both.length + '件'
      : '⚠共通するものは無い ── 背景のダブルクリック／Esc でもどる');
  } finally { FOCUS_BUSY = false; }
}
"""

JS2C = """
function enterFocus(node, depth){
  if (!cy || !node || !node.length || FOCUS_BUSY) return;
  FOCUS_BUSY = true;
  const gen = ++FOCUS_GEN;
  try {
    snapNow();
    clearDim();
    cy.remove('.ringtick');              // ⭐前の札を片づける
    FOCUS = node.id();
    if (depth != null) FOCUS_DEPTH = Math.max(1, Math.min(3, depth));
    restoreFilterVisibility();
    // ⭐**フィルタで見えているものの中で**隣を数える（消したものは辿らない）。
    //   ⭐**何手先か**も控える（輪で、近い相手を内側に置くため）
    const lvl = {};
    lvl[node.id()] = 0;
    let keepN = node, front = node;
    for (let d = 1; d <= FOCUS_DEPTH; d++){
      /* ⚠⚠**見えている線ぞいにしか辿らない。**
         ⭐`neighborhood()` は**線が隠れていても隣を返す**ので、そのまま使うと
           ⚠**線の無いまま輪に並ぶ相手**が出る（LAND で踏んだ）。 */
      const next = front.connectedEdges().filter(e => e.visible())
                        .connectedNodes()
                        .filter(n => n.visible() && lvl[n.id()] == null);
      next.forEach(n => { lvl[n.id()] = d; });
      keepN = keepN.union(next);
      front = next;
      if (!next.length) break;
    }
    // ⭐残ったノードどうしの線は全部見せる（相手どうしの繋がりも読めるように）
    const keepE = cy.edges().filter(e => e.visible() &&
                    keepN.contains(e.source()) && keepN.contains(e.target()));
    const keep = keepN.union(keepE);
    cy.batch(() => {
      cy.elements().not(keep).style('display', 'none');
      keep.style('display', 'element');
    });
    placeFocusRing(node, keepN, lvl);
    cy.layout({ name:'preset', fit:true, padding:80 }).run();
    setTimeout(() => {
      if (gen !== FOCUS_GEN || !FOCUS) return;
      /* ⚠⚠⚠**大きくした字のまま `fit` を掛けると、堂々巡りになる**（LAND で実測）。
         ⭐字を大きくする → 囲みが広がる → `fit` がもっと引く → 字がもっと大きく…
         ⭐**直しかた＝いったん字を戻して `fit` し、そのあとで大きくする。** */
      clearLitLabels();
      cy.fit(cy.elements(':visible'), 80);
      fitLitLabels();
    }, 60);
    const box = document.getElementById('focus');
    if (box) box.value = node.data('label');
    if (FOCUS_TRAIL[FOCUS_TRAIL.length - 1] !== FOCUS) FOCUS_TRAIL.push(FOCUS);
    drawTrail();
    focusUI(true);
    show(node.data('node'));
    startFocusBlink(node);
    hitCount('フォーカス「' + node.data('label') + '」 ／ ' +
             (keepN.length - 1) + '件とつながっている' +
             (FOCUS_DEPTH > 1 ? '（' + FOCUS_DEPTH + '手先まで）' : '') +
             ' ── 背景のダブルクリック／Esc でもどる');
  } finally { FOCUS_BUSY = false; }
}
/* ⭐フォーカスを張り直す（ひろげたとき・フィルタを触られたとき）。 */
function refocus(){
  if (!FOCUS) return;
  const n = cy.getElementById(FOCUS);
  if (n && n.length) enterFocus(n, FOCUS_DEPTH);
  else exitFocus();
}
/* ⭐**出る。**⚠計算はしない ── 控えた座標を置き直すだけ。 */
function exitFocus(){
  stopFocusBlink();
  FOCUS_GEN++;                         // ⚠あとから来る処理を全部むこうにする
  if (!FOCUS_SNAP){ FOCUS = null; focusUI(false); return; }
  const snap = FOCUS_SNAP;
  cy.remove('.ringtick');              // ⭐飾りを片づけてから戻す
  FOCUS = null; FOCUS_SNAP = null; FOCUS_DEPTH = 1;
  cy.batch(() => {
    cy.elements().style('display', 'element');
    cy.nodes().forEach(n => {
      const p = snap.pos[n.id()];
      if (p) n.position({ x:p[0], y:p[1] });
    });
  });
  applyFilters();                      // ⭐**いまのチェックから**計算し直す
  clearLitLabels();
  cy.zoom(snap.zoom);
  cy.pan(snap.pan);
  const box = document.getElementById('focus');
  if (box) box.value = '';
  FOCUS_TRAIL = [];
  focusUI(false);
  hitCount('元のネットワークに戻した');
  setTimeout(() => hitCount(''), 1600);
}
"""

# ⭐画面のボタン・キーの結び付け。⚠`boot()` の中（`cy` がある場所）に置く。
WIRE = """
  /* ⭐⭐フォーカスの結び付け（2026-09-09・LAND から移した） */
  document.getElementById('focusOut').onclick   = exitFocus;
  document.getElementById('focusBack').onclick  = focusStepBack;
  document.getElementById('focusWider').onclick = () => {
    if (!FOCUS) return;
    const n = cy.getElementById(FOCUS);
    if (n && n.length) enterFocus(n, Math.min(3, FOCUS_DEPTH + 1));
  };
  document.getElementById('focusStr').onchange = () => { if (FOCUS) refocus(); };
  /* ⭐いま見えている図をPNGで保存する。⚠背景は透けさせない（暗い地図でも読めるように）。 */
  document.getElementById('focusPng').onclick = () => {
    try {
      const url = cy.png({ full:true, scale:2, bg:BG });
      const a = document.createElement('a');
      a.href = url;
      a.download = 'mind-atlas_' + (FOCUS || 'focus') + '.png';
      document.body.appendChild(a); a.click(); a.remove();
    } catch(e){ hitCount('⚠画像にできなかった'); }
  };
  // ⭐⭐Esc でフォーカスから出る
  document.addEventListener('keydown', e => {
    if (e.key !== 'Escape' || !FOCUS) return;
    e.preventDefault();
    exitFocus();
  });
  /* ⭐フォーカス欄（Enter で入る。⚠検索欄とは別もの）。
     ⭐カンマで2つ書くと「共通の隣」（例: 島皮質, 共感）。 */
  (function setupFocusBox(){
    const box = document.getElementById('focus');
    if (!box) return;
    box.addEventListener('keydown', ev => {
      if (ev.key !== 'Enter') return;
      ev.preventDefault();
      const v = box.value.trim();
      if (!v){ if (FOCUS) exitFocus(); return; }
      const parts = v.split(',').map(s => s.trim()).filter(Boolean);
      if (parts.length >= 2){
        const a = findByName(parts[0]), b = findByName(parts[1]);
        if (a && b) enterFocusPair(a, b);
        else hitCount('⚠その名前は見つからない');
        return;
      }
      const n = findByName(v);
      if (n) enterFocus(n, 1); else hitCount('⚠その名前は見つからない');
    });
  })();
"""

# ⭐引きで名前が消えないよう、ズームが変わったら字の大きさを当て直す。
WIRE2 = """
  /* ⭐⭐ズームが変わったら、字の大きさを当て直す（LAND から）。
     ⚠⚠**輪は数が多いほど大きくなる**ので、当て直さないと引きで名前が消える。
     ⭐連打で重くならないよう、落ち着いてから1回だけ走らせる。 */
  cy.on('zoom', () => {
    if (!FOCUS && !cy.elements('.dim').length) return;
    clearTimeout(_litTimer);
    _litTimer = setTimeout(fitLitLabels, 80);
  });
"""

# --- 当てる先（⚠1文字でも違うと当たらない。当たらなければ止まる） --------------
A_HEADER = '      <select id="layout">'
A_STYLE  = "      { selector:'.dim', style:{ 'opacity':0.12 } }"
A_DBL_FROM = """    if (dbl){
      const box = document.getElementById('q');
      if (box) box.value = el.data('label');   // 検索欄と状態をそろえる
      spotlight(el);
    } else {"""
A_DBL_TO = """    if (dbl){
      /* ⭐⭐2026-09-09：ダブルクリックは「光らせる」から**フォーカス**に変えた
         （LAND と同じ約束）。⭐検索欄に名前を打てば、今までどおり光らせられる。 */
      enterFocus(el, 1);
    } else {"""
A_BG_FROM = """  cy.on('tap', ev => { if (ev.target === cy){
    clearDim();"""
A_BG_TO = """  cy.on('tap', ev => { if (ev.target === cy){
    /* ⭐⭐フォーカス中は、⭐**背景のダブルクリック**で元のネットワークに戻す
       （LAND・2026-09-05 に1回押しから変えた。
         ⚠1回押しだと、⭐**見ているだけのつもりで抜けてしまう**）。 */
    if (FOCUS){
      const t = Date.now();
      const dbl = (t - _bgTap < 420);
      _bgTap = dbl ? 0 : t;
      if (dbl) exitFocus();
      return;
    }
    clearDim();"""
A_HOME = """  document.addEventListener('keydown', e => {
    if (e.key !== 'Home') return;
    const a = document.activeElement;
    if (a && /^(INPUT|TEXTAREA|SELECT)$/.test(a.tagName)) return;
    e.preventDefault();
    resetView();
  });"""
A_FILTER_FROM = """    a.style.opacity = hidden ? 0.3 : 1;
  });
}"""
A_FILTER_TO = """    a.style.opacity = hidden ? 0.3 : 1;
  });
  /* ⭐フィルタが変わったら、フォーカスも張り直す（LAND と同じ）。
     ⚠⚠**`FOCUS_BUSY` を見るのが要る** ── `restoreFilterVisibility()` から
       呼ばれたときにも張り直すと、⭐**入れ子になって戻ってこない。** */
  if (typeof FOCUS !== 'undefined' && FOCUS && !FOCUS_BUSY) refocus();
}"""
A_CLEARDIM_FROM = """function clearDim(){
  if (!cy) return;
  cy.elements().removeClass('dim').selectify();
  cy.nodes().grabify();     // ⚠薄くしたときに外した「掴める」を必ず戻す
  hitCount('');
}"""
A_CLEARDIM_TO = """function clearDim(){
  if (!cy) return;
  cy.elements().removeClass('dim').selectify();
  // ⚠薄くしたときに外した「掴める」を必ず戻す。⚠輪の札（.ringtick）は掴ませない
  cy.nodes().not('.ringtick').grabify();
  clearLitLabels();         // ⭐光らせるとき用に大きくした字を戻す
  hitCount('');
}"""
A_HELP_FROM = """      <b>ダブルクリック</b>すると、そのノードと<b>直接つながっているものだけ</b>が光る
      （検索欄に名前を打つのと同じ）。<b>背景をクリックすると戻る。</b><br>"""
A_HELP_TO = """      <b>ダブルクリック</b>すると、そのノードを<b>まん中にした輪</b>になる（＝フォーカス）。
      つながっている相手だけが、<b>種類ごとにまとまって</b>一周に並ぶので、
      <b>どの種類と何件つながっているかが円グラフのように読める</b>。
      輪の<b>半径は線の強さ</b>（強いほど内側）。<br>
      &#9733;<b>出るときは、背景を「ダブルクリック」</b>（または Esc キー・上の「もどる」）。
      1回押しだと、見ているだけのつもりで抜けてしまうので。<br>
      &#9733;上の<b>フォーカス欄</b>に名前を打って Enter でも入れる。
      <b>カンマで2つ書くと、両方につながっているものだけ</b>が出る（例: 島皮質, 共感）。<br>
      &#9733;<b>もう1手</b>で、その先までひろげる。<b>&#8592; 一歩</b>で、ひとつ前に戻る。<br><br>
      <b>検索欄</b>に名前を打つと、こちらは<b>その場で光らせる</b>（地図は動かさない）。
      <b>背景をクリックすると戻る。</b><br>"""
A_JS = "function esc(s){ const d = document.createElement('div'); d.textContent = s; return d.innerHTML; }"


def main():
    look = ('--見るだけ' in sys.argv)
    s = io.open(SRC, encoding='utf-8').read()
    if MARK in s:
        print('⭐もう当たっている（' + MARK + '）。何もしない。')
        return
    for name, a in [('ヘッダ', A_HEADER), ('スタイル', A_STYLE),
                    ('ダブルクリック', A_DBL_FROM), ('背景クリック', A_BG_FROM),
                    ('Homeキー', A_HOME), ('applyFilters', A_FILTER_FROM),
                    ('clearDim', A_CLEARDIM_FROM), ('説明欄', A_HELP_FROM),
                    ('本体の置き場', A_JS)]:
        if s.count(a) != 1:
            print('⚠当てる先が見つからない／複数ある: ' + name + '（' + str(s.count(a)) + '件）')
            return
    s = s.replace(A_HEADER, HEADER_HTML + A_HEADER, 1)
    s = s.replace(A_STYLE, RING_STYLE + A_STYLE, 1)
    s = s.replace(A_DBL_FROM, A_DBL_TO, 1)
    s = s.replace(A_BG_FROM, A_BG_TO, 1)
    s = s.replace(A_HOME, A_HOME + '\n' + WIRE + WIRE2, 1)
    s = s.replace(A_FILTER_FROM, A_FILTER_TO, 1)
    s = s.replace(A_CLEARDIM_FROM, A_CLEARDIM_TO, 1)
    s = s.replace(A_HELP_FROM, A_HELP_TO, 1)      # ⭐案内文も直す（挙動が変わったので）
    body = ('let _litTimer = null;   // ⭐字の大きさを当て直すのを、落ち着いてから1回だけ\n'
            + JS + JS2A + JS2B + JS2C + '\n')
    s = s.replace(A_JS, body + A_JS, 1)
    if look:
        print('⭐ぜんぶの当てる先が1件ずつ見つかった（書いていない）。')
        return
    io.open(SRC, 'w', encoding='utf-8', newline='\n').write(s)
    print('index.html に当てた（%.1f KB）' % (len(s.encode('utf-8')) / 1024.0))


if __name__ == '__main__':
    main()
