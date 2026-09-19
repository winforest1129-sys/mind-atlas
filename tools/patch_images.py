# -*- coding: utf-8 -*-
"""⭐ 説明欄に絵を出せるようにする（IMG-MIND-2026-09-19・陽介）。

    python tools/patch_images.py            当てる（二度当てしない）
    python tools/patch_images.py --戻す      退避から戻す

ノード本文に  ![説明](img/ファイル名.jpg)  と書くと、説明欄に絵と説明文が出る。
絵は mind-atlas/img/ に置く（file:// で開くので相対パス）。⚠MIND は手元専用（公開しない）なので絵を置ける。
⚠説明文に p.N / 画像N を書かない（頁の札に化ける）── 絵は先に取り出して札の処理から守ってあるが、念のため。

当て先＝index.html の md()（先頭で絵を取り出し、最後に戻す）と、CSS（.fig）。
退避＝_backup/index.html.bak_20260919_画像まえ
"""
import io, os, re, sys, shutil

if not (getattr(sys.stdout, 'encoding', '') or '').lower().startswith('utf'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'index.html')
BAK = os.path.join(ROOT, '_backup', 'index.html.bak_20260919_画像まえ')
MARK = 'IMG-MIND-2026-09-19'

if '--戻す' in sys.argv:
    shutil.copyfile(BAK, SRC); print('戻した:', BAK); sys.exit(0)

s = open(SRC, encoding='utf-8').read()
if MARK in s:
    print('もう当たっている（目印あり）'); sys.exit(0)

os.makedirs(os.path.dirname(BAK), exist_ok=True)
shutil.copyfile(SRC, BAK); print('退避:', BAK)

# --- 1) md()：先頭で ![説明](src) を取り出して置き札にし、最後に <figure> で戻す ------------------
old_head = "function md(s){\n  return esc(s)\n"
new_head = (
    "function md(s){\n"
    "  /* " + MARK + " 説明欄の絵： ![説明](img/…jpg) → <figure>。他の記法や頁の札に触られないよう先に取り出す（陽介） */\n"
    "  const figs = [];\n"
    "  s = s.replace(/!\\[([^\\]\\n]*)\\]\\(([^)\\s]+)\\)/g, (m, alt, src) => {\n"
    "    figs.push('<figure class=\"fig\"><img src=\"' + esc(src) + '\" alt=\"' + esc(alt) + '\" loading=\"lazy\">' +\n"
    "              (alt ? '<figcaption>' + esc(alt) + '</figcaption>' : '') + '</figure>');\n"
    "    return '\\u0000FIG' + (figs.length - 1) + '\\u0000';\n"
    "  });\n"
    "  return esc(s)\n"
)
assert s.count(old_head) == 1, 'md() の頭が見つからない'
s = s.replace(old_head, new_head, 1)

old_tail = "    .replace(/\\n\\n/g, '<br><br>').replace(/\\n/g, '<br>');\n}\n"
new_tail = (
    "    .replace(/\\n\\n/g, '<br><br>').replace(/\\n/g, '<br>')\n"
    "    .replace(/\\u0000FIG(\\d+)\\u0000(?:<br>)?/g, (m, i) => figs[+i]);   // " + MARK + " 絵を戻す\n"
    "}\n"
)
assert s.count(old_tail) == 1, 'md() の尻が見つからない'
s = s.replace(old_tail, new_tail, 1)

# --- 2) CSS：.key の次の行に .fig を足す（暗い配色でも変えない） -----------------------------------
old_css = "  .key{color:#1f3d6b;font-weight:600}\n"
new_css = (
    old_css +
    "  /* " + MARK + " 説明欄の絵 */\n"
    "  .fig{margin:10px 0}\n"
    "  .fig img{display:block;max-width:100%;height:auto;border:1px solid rgba(0,0,0,.12)}\n"
    "  .fig figcaption{font-size:.84em;opacity:.72;margin-top:4px;line-height:1.4}\n"
)
assert s.count(old_css) == 1, 'CSS の .key が見つからない'
s = s.replace(old_css, new_css, 1)

open(SRC, 'w', encoding='utf-8').write(s)
print('当てた:', SRC)

# --- 括弧の数（作業の型 1） ---------------------------------------------------------------------
js = '\n'.join(re.findall(r'<script(?![^>]*src=)[^>]*>(.*?)</script>', s, flags=re.S))
for a, b in ('{}', '()', '[]'):
    print(f'  {a}{b}: {js.count(a)} / {js.count(b)}')
print('  <script>:', len(re.findall(r'<script\b', s)), '/ </script>:', s.count('</script>'))
