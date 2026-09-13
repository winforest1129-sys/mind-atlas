# -*- coding: utf-8 -*-
"""⭐ フォーカス中の「つながりを光らせる」（PEEK-LIGHT）を index.html に当てる。

    python tools/patch_peek.py                 … この地図（MIND）の index.html に当てる
    python tools/patch_peek.py <index.html>    … ほかの地図（ALGA / LAND）に当てる
    python tools/patch_peek.py <index.html> --戻す [出力先]  … 外した中身を書く（出力先を省くと本体を戻す）

⭐ 何が変わるか（2026-09-13・燻太さんの依頼）
  「ノードのフォーカス時に、クリックしたノードとリンク、そのノードとリンクしている
   ノードを一緒に光らせる。もう1手先を表示させたときに特に生きる」
  - フォーカス中に、見えているノードを**1回押す** → そのノード・その線・線の先の隣が光り、
    輪の残りは薄くなる（消さない）。説明欄は今までどおり出る。
  - 同じノードをもう1回押す／背景を1回押す → 元の輪に戻る。別のノードを押せば移る。
  - ダブルクリック（そこにフォーカスし直す）・Esc・もう1手・一歩・出る は今までどおり。
  - ⚠**初期表示と、検索の「光らせる（spotlight）」は触らない。**フォーカス中だけ。

⚠ 作り
  - 見た目は class で当てる（`.peekdim` 薄く／`.peek` 光る／`.peek0` 押したノード）。
    ⭐ノードは underlay（下に敷く光）。⚠overlay は「フォーカスの中心の点滅」が使っているので触らない。
    ⭐線は太さだけ上げて**色は変えない**（MIND の赤線＝対立・批判を潰さないため）。
  - `clearDim()`・`exitFocus()`・背景の1回押しで必ず消す。enterFocus は clearDim を通るので消える。
  - 何度流しても1回ぶん（PEEK-LIGHT の印で判定）。控えは index.html.bak_YYYYMMDD_HHMM_peekの前。
"""
import io, os, re, sys, time

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
HERE = os.path.dirname(os.path.abspath(__file__))
target = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, '..', 'index.html')
target = os.path.abspath(target)
s = io.open(target, encoding='utf-8').read()

STYLE = """      /* PEEK-LIGHT ── フォーカス中に1回押したノードのつながりを光らせる */
      { selector:'.peekdim', style:{ 'opacity':0.2 } },
      { selector:'node.peek', style:{ 'underlay-color':'#f0a828', 'underlay-opacity':0.42, 'underlay-padding':9 } },
      { selector:'node.peek0', style:{ 'underlay-opacity':0.7, 'underlay-padding':15 } },
      { selector:'edge.peek', style:{ 'width':3.6, 'text-opacity':1, 'z-index':9 } },
"""
FUNCS = """/* PEEK-LIGHT ── ⭐フォーカス中に1回押したノードの「つながり」を光らせる（2026-09-13・燻太さんの依頼）
   「もう1手」で輪が40〜60ノードになると、どれとどれがつながっているか目で追えない。
   押したノード・その線・線の先の隣を光らせ、残りを薄くする（消さない）。
   ⭐同じノードをもう1回押す／背景を1回押す／clearDim／exitFocus で消える。
   ⚠初期表示と検索の spotlight（.dim）には触らない。 */
let PEEK = null;
function clearPeek(){
  if (typeof cy === 'undefined' || !cy) return;
  if (!PEEK && !cy.elements('.peekdim').length) return;
  cy.batch(() => { cy.elements().removeClass('peekdim peek peek0'); });
  PEEK = null;
}
function peekNode(el){
  if (!el || !el.length || el.hasClass('ringtick')) return;
  if (PEEK === el.id()){ clearPeek(); hitCount(''); return; }
  clearPeek();
  const vis = cy.elements(':visible').not('.ringtick');
  const eg  = el.connectedEdges().filter(':visible');
  const nb  = eg.connectedNodes().not(el);
  const lit = el.union(eg).union(nb);
  cy.batch(() => {
    vis.not(lit).addClass('peekdim');
    lit.addClass('peek');
    el.addClass('peek0');
  });
  PEEK = el.id();
  const name = String(el.data('label') || el.id());
  hitCount(name + ' のつながり ' + nb.length + '件（線 ' + eg.length + '本）／もう1回押すと戻る');
}
"""

def unpatch(s):
    """当てたものを外した中身を返す（--戻す／控えの作り直し用）。当てた塊は決まっているので、そのまま消せば元に戻る。"""
    s = s.replace(STYLE, '', 1)
    s = s.replace("      if (FOCUS) peekNode(el);   // PEEK-LIGHT\n", '', 1)
    s = s.replace("if (dbl) exitFocus(); else clearPeek();   // PEEK-LIGHT", "if (dbl) exitFocus();", 1)
    s = s.replace("  clearPeek();   // PEEK-LIGHT\n", '', 1)   # exitFocus の頭
    s = s.replace(FUNCS, '', 1)
    s = s.replace("function clearDim(){\n  clearPeek();   // PEEK-LIGHT\n", "function clearDim(){\n", 1)
    return s

if '--戻す' in sys.argv:
    if 'PEEK-LIGHT' not in s:
        print('当たっていない:', target); sys.exit(0)
    out = unpatch(s)
    assert 'PEEK-LIGHT' not in out, '外しきれていない'
    i = sys.argv.index('--戻す')
    dst = sys.argv[i + 1] if len(sys.argv) > i + 1 else target
    io.open(dst, 'w', encoding='utf-8', newline='').write(out)
    print('外した中身を書いた:', dst); sys.exit(0)
if 'PEEK-LIGHT' in s:
    print('もう当たっている:', target); sys.exit(0)

n = 0
# 1. スタイル：.dim の行の**手前**に足す
#    ⚠ .dim の行はスタイル配列の最後でカンマが無いことがある（MIND）。直後に足すと構文エラーで
#      `let cy` のスクリプトごと死に、`cy` が DOM 要素を指して「cy.nodes is not a function」が出る（2026-09-13に踏んだ）
m = re.search(r"^ *\{ selector:'\.dim', style:\{[^\n]*\n", s, re.M)
assert m, ".dim のスタイルが見つからない"
s = s[:m.start()] + STYLE + s[m.start():]; n += 1
# 2. ノードの1回押し
old = "      show(el.data('node'));\n"
assert s.count(old) == 1, "show(el.data('node')) が1か所でない: %d" % s.count(old)
s = s.replace(old, old + "      if (FOCUS) peekNode(el);   // PEEK-LIGHT\n"); n += 1
# 3. 背景の1回押し（フォーカス中）
old = "if (dbl) exitFocus();"
assert s.count(old) == 1, "if (dbl) exitFocus() が1か所でない"
s = s.replace(old, "if (dbl) exitFocus(); else clearPeek();   // PEEK-LIGHT"); n += 1
# 4. exitFocus の頭
m = re.search(r"^function exitFocus\(\)\{\n( *stopFocusBlink\(\);[^\n]*\n)", s, re.M)
assert m, "exitFocus の頭が見つからない"
s = s[:m.end()] + "  clearPeek();   // PEEK-LIGHT\n" + s[m.end():]; n += 1
# 5. clearDim の頭に消す処理、関数本体はその手前に
old = "function clearDim(){\n"
assert s.count(old) == 1
s = s.replace(old, FUNCS + old + "  clearPeek();   // PEEK-LIGHT\n"); n += 1

bak = target + '.bak_' + time.strftime('%Y%m%d_%H%M') + '_peekの前'
io.open(bak, 'w', encoding='utf-8', newline='').write(io.open(target, encoding='utf-8').read())
io.open(target, 'w', encoding='utf-8', newline='').write(s)
print('当てた（%d か所）: %s\n控え: %s' % (n, target, bak))
