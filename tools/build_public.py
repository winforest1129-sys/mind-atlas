# -*- coding: utf-8 -*-
"""⭐ 公開版を docs/ に焼く（PUBLIC-2026-09-21・燻太さんの指定）。

    python tools/build_public.py        手元版（index.html ほか）から docs/ を作り直す
    ※ tools/build_map.py の最後から自動で呼ばれる＝「MIND作成時に手元版と公開版の両方ができる」

燻太さんの言葉（2026-09-21）＝「MINDの論文と文献表示機能だけなくした以前の公開バージョンを有効にして
ほしい。MIND作成時は、公開版とローカル版の両方を作成して、公開版は以前の仕様でpushする運用にしたい」。

何をするか
  ① index.html から「手元専用の機能」の呼び出しを外して docs/index.html にする（関数の定義は残る・呼ばないだけ）
       a. 書庫の台帳 ../../Taiga_PJ/書庫/catalog.js を読む <script>   → 書庫の箱・頁の札は台帳が無ければ出ない設計
       b. 論文ノードの Connected Papers の箱（cpBox）の呼び出し
       c. 書庫の箱（shokoBox）の呼び出し
       d. 手元PDF（papers/）へのリンク                               → papers/ は公開しない（.gitignore）
     ⚠どれも exact match。1つでも見つからなければ止まる（index.html を直したときに黙ってずれないため）
  ② 画面が読むものを丸ごと写す＝data.js・data.json・brain.js・brain.svg・positions.js・lib/・img/・.nojekyll
     ⚠nodes/・tools/・papers/・_backup/ は写さない（公開版は焼いたサイトだけ）
  ③ 焼いた docs/index.html に手元専用の呼び出しが残っていないか確かめる

配信＝GitHub Pages・main の /docs（https://winforest1129-sys.github.io/mind-atlas/）。
検査＝tools/check_public.py（ヘッドレスで開いて・Connected Papers と書庫の箱が無く・絵は出ることを測る）。
⚠docs/ は生成物。直接編集しない（次のビルドで消える）。
"""
import io, os, sys, shutil

if not (getattr(sys.stdout, 'encoding', '') or '').lower().startswith('utf'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS = os.path.join(ROOT, 'docs')
MARK = 'PUBLIC-2026-09-21'

# ① 外す呼び出し（old → new）。⚠1つずつ exact match・ちょうど1回ずつ
STRIP = [
    ('<script src="../../Taiga_PJ/書庫/catalog.js"></script>\n',
     '<!-- ' + MARK + ' 公開版＝書庫の台帳は読まない（書庫の箱・頁の札は出ない） -->\n'),
    ("  if (n.type === '論文') h += cpBox(n);                    // LOCAL-2026-09-18 Connected Papers\n",
     '  // ' + MARK + ' 公開版＝Connected Papers の箱は出さない\n'),
    ('  h += shokoBox(n);                                         // LOCAL-2026-09-18 書庫の箱（出典の本がスキャンしてあれば）\n',
     '  // ' + MARK + ' 公開版＝書庫の箱は出さない\n'),
    ("    if (F['pdf'])   // LOCAL-2026-09-18 ローカル専用になったので「手元だけ」の札は要らない\n"
     "      h += '<br><a class=\"pdflink\" href=\"' + esc(encodeURI(F['pdf'])) +\n"
     "           '\" target=\"_blank\" rel=\"noopener noreferrer\">本文PDFを開く</a>';\n",
     '    // ' + MARK + ' 公開版＝手元PDF（papers/）へのリンクは出さない（公開しないので開けない）\n'),
]
# ③ 残っていてはいけない文字列
FORBID = ['<script src="../../Taiga_PJ/書庫/catalog.js"', 'h += cpBox(', 'h += shokoBox(', 'pdflink\\" href']
# ② 写すもの
FILES = ['data.js', 'data.json', 'brain.js', 'brain.svg', 'positions.js']
DIRS = ['lib', 'img']


def main():
    src = os.path.join(ROOT, 'index.html')
    s = io.open(src, encoding='utf-8').read()
    for old, new in STRIP:
        n = s.count(old)
        if n != 1:
            print('⚠ build_public: 外す場所が %d 回見つかった（1回のはず）:\n   %s' % (n, old.strip().splitlines()[0]))
            return 1
        s = s.replace(old, new)
    head = ('<!-- ' + MARK + ' ⭐公開版。tools/build_public.py が手元版 index.html から焼いた生成物＝直接編集しない。'
            '手元専用の機能（Connected Papers・書庫の箱・手元PDF）を外してある -->\n')
    first, rest = s.split('\n', 1)          # 1行目（<!doctype html>）の直後に目印を入れる
    s = first + '\n' + head + rest
    bad = [f for f in FORBID if f in s]
    if bad:
        print('⚠ build_public: 公開版に残ってはいけないものがある: ' + ', '.join(bad)); return 1

    # docs/ を写す。⚠フォルダごと消して作り直すと OneDrive がフォルダの削除を弾く（WinError 5）ので・
    #   ファイル単位で上書きし・要らなくなったファイルだけ消す（フォルダは残す）
    want = {}                                   # docs/ からの相対パス → 元のパス（None は自前で書く）
    want['index.html'] = None
    want['.nojekyll'] = None
    for f in FILES:
        p = os.path.join(ROOT, f)
        if not os.path.exists(p):
            print('⚠ build_public: %s が無い' % f); return 1
        want[f] = p
    for d in DIRS:
        p = os.path.join(ROOT, d)
        if os.path.isdir(p):
            for r, _, fs in os.walk(p):
                for f in fs:
                    full = os.path.join(r, f)
                    want[os.path.relpath(full, ROOT).replace(os.sep, '/')] = full
    os.makedirs(DOCS, exist_ok=True)
    removed = 0
    for r, _, fs in os.walk(DOCS):
        for f in fs:
            full = os.path.join(r, f)
            if os.path.relpath(full, DOCS).replace(os.sep, '/') not in want:
                os.remove(full); removed += 1
    for rel, src_path in want.items():
        dst = os.path.join(DOCS, rel.replace('/', os.sep))
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        if rel == 'index.html':
            io.open(dst, 'w', encoding='utf-8', newline='\n').write(s)
        elif rel == '.nojekyll':
            io.open(dst, 'w').write('')
        else:
            shutil.copyfile(src_path, dst)
    copied = len(want) - 1
    if removed:
        print('  docs/ の古いファイルを %d 個消した' % removed)
    size = sum(os.path.getsize(os.path.join(r, f)) for r, _, fs in os.walk(DOCS) for f in fs)
    print('docs/ に公開版を焼いた: %d ファイル・%.1f MB（Connected Papers・書庫の箱・手元PDF は外した）'
          % (copied + 1, size / 1e6))
    return 0


if __name__ == '__main__':
    sys.exit(main())
