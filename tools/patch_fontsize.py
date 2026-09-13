# -*- coding: utf-8 -*-
"""⭐ 説明欄（右パネル）の文字サイズを変えるボタンを index.html に当てる（2026-09-13・燻太さんの依頼）。

    python tools/patch_fontsize.py                 … この地図（MIND）の index.html に当てる
    python tools/patch_fontsize.py <index.html>    … ほかの地図（ALGA / LAND）に当てる
    python tools/patch_fontsize.py <index.html> --戻す   … 当てる前に戻す（印で囲んだ3か所を外す）

⭐ 何が変わるか
  説明欄の上端に小さな帯 ── 「A−」「100%」「A＋」 ── が付く。
  - A− / A＋ … 説明欄の文字を一段小さく／大きく（85%〜160%・8段）
  - まん中の「100%」… いまの倍率。押すと元（100%）に戻る
  - 倍率はこのブラウザに覚える（localStorage の <地図>.sideZoom）。地図そのものは触らない。

⚠ 作り
  - `#sidebody{zoom:var(--sz)}` で中身をまるごと拡縮する（文字だけでなく脳の図・バッジも同じ比で）。
    ⭐ zoom を使うのは、説明欄の中の font-size が px でばらばらに書いてあり、
      ひとつずつ em に直すより壊しにくいから。幅も同じ比で詰まるので、拡大すると行が折れる（本のページを拡大するのと同じ）。
  - 帯は `position:sticky` で説明欄の上に留まる。スマホ（下からのシート）では sheetbar の下に普通に置く。
  - 何度流しても1回ぶん（`FONTBAR` の印で判定）。控えは index.html.bak_YYYYMMDD_HHMM_文字サイズの前。
"""
import io, os, re, sys, time

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
HERE = os.path.dirname(os.path.abspath(__file__))
args = [a for a in sys.argv[1:] if not a.startswith('--')]
target = os.path.abspath(args[0]) if args else os.path.abspath(os.path.join(HERE, '..', 'index.html'))
undo = '--戻す' in sys.argv
s = io.open(target, encoding='utf-8').read()

MARK = 'FONTBAR'
CSS = """  /* FONTBAR ── 説明欄の文字サイズ（A− / 100% / A＋）。2026-09-13・燻太さんの依頼 */
  #side{--sz:1}
  #sidebody{zoom:var(--sz)}
  #fontbar{position:sticky;top:0;display:flex;gap:4px;align-items:center;justify-content:flex-end;
    background:var(--panel);margin:-16px -16px 8px;padding:6px 10px 5px;z-index:3;
    border-bottom:1px solid var(--line)}
  #fontbar .fz{padding:1px 7px;font-size:11px;line-height:1.5;min-width:30px}
  #fontbar .fzv{min-width:44px;text-align:center;font-variant-numeric:tabular-nums;color:var(--sub)}
  #fontbar .fzl{font-size:10.5px;color:var(--sub);margin-right:2px}
  @media (max-width:1024px){
    #fontbar{position:static;margin:0 0 6px;padding:0 0 6px}
  }
  /* /FONTBAR */
"""
HTML = """    <!-- FONTBAR -->
    <div id="fontbar"><span class="fzl">文字</span>
      <button class="btn fz" data-fz="-" title="小さく">A−</button>
      <button class="btn fz fzv" data-fz="0" title="元の大きさ（100%）に戻す">100%</button>
      <button class="btn fz" data-fz="+" title="大きく">A＋</button></div>
    <!-- /FONTBAR -->
"""
JS = """
/* FONTBAR ── ⭐説明欄の文字サイズを変える（2026-09-13・燻太さんの依頼）
   A− / A＋ で一段ずつ。まん中の倍率を押すと 100% に戻る。倍率はこのブラウザに覚える。
   ⚠ #sidebody を zoom で拡縮するだけ。地図（cytoscape）と一覧は触らない。 */
(function(){
  const side = document.getElementById('side');
  const bar  = document.getElementById('fontbar');
  if (!side || !bar) return;
  const KEY = '__PREFIX__.sideZoom';
  const STEPS = [0.85, 0.92, 1, 1.1, 1.2, 1.32, 1.45, 1.6];
  const label = bar.querySelector('.fzv');
  let cur = 1;
  function apply(v, save){
    cur = v;
    side.style.setProperty('--sz', String(v));
    if (label) label.textContent = Math.round(v * 100) + '%';
    if (save){ try { localStorage.setItem(KEY, String(v)); } catch(e){} }
  }
  function step(dir){
    let i = STEPS.indexOf(cur);
    if (i < 0){ i = 0; for (let k = 0; k < STEPS.length; k++){ if (Math.abs(STEPS[k]-cur) < Math.abs(STEPS[i]-cur)) i = k; } }
    i = Math.max(0, Math.min(STEPS.length - 1, i + dir));
    apply(STEPS[i], true);
  }
  bar.addEventListener('click', e => {
    const b = e.target.closest('[data-fz]');
    if (!b) return;
    e.preventDefault();
    const d = b.dataset.fz;
    if (d === '+') step(1); else if (d === '-') step(-1); else apply(1, true);
  });
  try {
    const saved = parseFloat(localStorage.getItem(KEY));
    if (saved > 0.5 && saved < 3) apply(saved, false); else apply(1, false);
  } catch(e){ apply(1, false); }
})();
/* /FONTBAR */
"""

def strip(s):
    s = re.sub(r"  /\* FONTBAR ──.*?/\* /FONTBAR \*/\n", "", s, flags=re.S)
    s = re.sub(r"    <!-- FONTBAR -->.*?<!-- /FONTBAR -->\n", "", s, flags=re.S)
    s = re.sub(r"\n/\* FONTBAR ── .*?/\* /FONTBAR \*/\n", "", s, flags=re.S)
    return s

stamp = time.strftime('%Y%m%d_%H%M')
if undo:
    if MARK not in s:
        print('当たっていない:', target); sys.exit(0)
    io.open(target + '.bak_' + stamp + '_文字サイズを外す前', 'w', encoding='utf-8').write(s)
    io.open(target, 'w', encoding='utf-8').write(strip(s))
    print('外した:', target); sys.exit(0)

if MARK in s:
    print('もう当たっている（何度流しても1回ぶん）:', target); sys.exit(0)

# localStorage の接頭辞（mindatlas / genatlas …）を既存の使いかたから拾う
m = re.search(r"localStorage\.(?:setItem|getItem)\(\s*['\"]([A-Za-z0-9_]+)\.", s)
prefix = m.group(1) if m else ''   # ALGA/LAND は鍵に接頭辞が無い（sidew など）
m2 = re.search(r"const KEY = '([A-Za-z0-9_]+)\.", s)
if m2: prefix = m2.group(1)

# 1) CSS: 最初の </style> の直前
i = s.find('</style>')
if i < 0: print('⚠ </style> が無い'); sys.exit(1)
s = s[:i] + CSS + s[i:]
# 2) HTML: <aside id="side"> の中の <div id="sidebody"> の直前
j = s.find('<aside id="side">')
k = s.find('<div id="sidebody">', j)
if j < 0 or k < 0: print('⚠ <aside id="side"> / <div id="sidebody"> が無い'); sys.exit(1)
ls = s.rfind('\n', 0, k) + 1     # その行の頭
s = s[:ls] + HTML + s[ls:]
# 3) JS: 最後の </script> の直前
e = s.rfind('</script>')
s = s[:e] + JS.replace('__PREFIX__.', (prefix + '.') if prefix else '') + s[e:]

io.open(target + '.bak_' + stamp + '_文字サイズの前', 'w', encoding='utf-8').write(io.open(target, encoding='utf-8').read())
io.open(target, 'w', encoding='utf-8').write(s)
print('当てた:', target, '／ localStorage の鍵 =', ((prefix + '.') if prefix else '') + 'sideZoom')
