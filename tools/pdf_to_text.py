# -*- coding: utf-8 -*-
"""papers/ の本文PDFを _papers/txt/ にテキスト化する。読むための下ごしらえ。

⚠ _papers/txt/ は .gitignore に入れてある（PDFから作り直せるものなので）。
使い方:
  python tools/pdf_to_text.py            … まだ起こしていないものを全部
  python tools/pdf_to_text.py "2017 Soto" … 1本だけ
"""
import os, io, sys, glob
import fitz

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAPERS = os.path.join(ROOT, 'papers')
OUT = os.path.join(ROOT, '_papers', 'txt')


def one(pdf):
    name = os.path.splitext(os.path.basename(pdf))[0]
    dest = os.path.join(OUT, name + '.txt')
    if os.path.exists(dest) and os.path.getsize(dest) > 500:
        return name, os.path.getsize(dest), True
    doc = fitz.open(pdf)
    parts = []
    for i, page in enumerate(doc):
        parts.append('\n===== p.%d =====\n' % (i + 1) + page.get_text())
    doc.close()
    txt = ''.join(parts)
    open(dest, 'w', encoding='utf-8').write(txt)
    return name, len(txt), False


def main():
    os.makedirs(OUT, exist_ok=True)
    want = sys.argv[1] if len(sys.argv) > 1 else None
    files = sorted(glob.glob(os.path.join(PAPERS, '*.pdf')))
    if want:
        files = [f for f in files if want in os.path.basename(f)]
    made = 0
    thin = []
    for f in files:
        try:
            name, size, cached = one(f)
        except Exception as e:
            print('ERR %-28s %s' % (os.path.basename(f)[:28], str(e)[:50]))
            continue
        if not cached:
            made += 1
        # ⚠ 文字が取れないPDF（画像だけの走査版）は、ここで分かる
        if size < 3000:
            thin.append((name, size))
        print('%-30s %8d %s' % (name[:30], size, '(控えから)' if cached else ''))
    print('\n新しく起こした %d 本 ／ 置き場 %s' % (made, OUT))
    if thin:
        print('⚠ 文字がほとんど取れなかったもの（画像だけのPDFかもしれない）:')
        for n, s in thin:
            print('   %-30s %d' % (n, s))


if __name__ == '__main__':
    main()
