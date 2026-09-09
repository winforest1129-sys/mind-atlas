# -*- coding: utf-8 -*-
"""papers/ にあるPDFを、同じ名前の論文ノードに `pdf:` として結ぶ。

⭐ノード名とファイル名は同じ（`2022 Bruineberg` ↔ `papers/2022 Bruineberg.pdf`）。
⭐`本文:` が無いノードには「要旨のみ」を入れる（読んだら手で書き換える）。
⚠ 既に書いてある `pdf:` `本文:` は上書きしない。
使い方: python tools/link_papers.py [--見るだけ]
"""
import os, io, sys, glob, re

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NODES = os.path.join(ROOT, 'nodes')
PAPERS = os.path.join(ROOT, 'papers')
DRY = '--見るだけ' in sys.argv


def main():
    have = {}
    for f in glob.glob(os.path.join(PAPERS, '*.pdf')):
        have[os.path.splitext(os.path.basename(f))[0]] = os.path.basename(f)
    print('papers/ にあるPDF: %d 本' % len(have))

    added = body_added = miss = 0
    for name, fname in sorted(have.items()):
        path = os.path.join(NODES, name + '.md')
        if not os.path.exists(path):
            print('  ⚠ ノードが無い: %s' % name)
            miss += 1
            continue
        t = open(path, encoding='utf-8').read()
        if not t.startswith('---'):
            print('  ⚠ frontmatter が無い: %s' % name)
            continue
        end = t.find('\n---', 3)
        head, rest = t[3:end], t[end:]

        ins = []
        if not re.search(r'^pdf:', head, re.M):
            ins.append('pdf: papers/%s' % fname)
            added += 1
        if not re.search(r'^本文:', head, re.M):
            ins.append('本文: 要旨のみ')
            body_added += 1
        if not ins:
            continue

        # ⭐links: か refs: の直前に入れる。どちらも無ければ末尾に足す
        m = re.search(r'^(links:|refs:)', head, re.M)
        if m:
            head = head[:m.start()] + '\n'.join(ins) + '\n' + head[m.start():]
        else:
            head = head.rstrip('\n') + '\n' + '\n'.join(ins) + '\n'

        if not DRY:
            open(path, 'w', encoding='utf-8').write('---' + head + rest)
        print('  %s %s' % ('(見るだけ)' if DRY else 'OK      ', name))

    print('\npdf: を足した %d ／ 本文: を足した %d ／ ノードが無い %d'
          % (added, body_added, miss))
    if DRY:
        print('⚠ --見るだけ なので書いていない')


if __name__ == '__main__':
    main()
