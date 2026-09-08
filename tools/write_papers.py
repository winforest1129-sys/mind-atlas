# -*- coding: utf-8 -*-
"""⭐`_papers/論文一覧.json` から、⭐**論文ノードを書き出す**（2026-09-09）。

    python tools/write_papers.py            書く（⭐すでにあるものは上書きしない）
    python tools/write_papers.py --上書き    書き直す
    python tools/write_papers.py --見るだけ

⭐名前＝`年 筆頭著者`（LAND とそろえた）。⭐リンクは **論文 → 用語（rel: 裏づけ）**。

⚠**rel をひとつに揃えた理由**＝
  引用元の `note` には「何を示したか」が1本ずつ書いてあるが、⭐それは**ノードの側の言葉**。
  ⭐線の名前を機械で作ると、⚠**批判なのに「裏づけ」と書く**ような取り違えが起きる。
  ⭐だから線は `裏づけ`（＝この地図がその論文に寄りかかっている、という事実）だけを言い、
    ⭐**中身は論文ノードの本文に、引用元の note をそのまま並べる**。
  ⚠⚠**だから赤線（対立・批判）は、この作業では1本も増えない。**そこは人が書く。

⚠**出典（本）は、引いているノードの出典を集めたもの。**
  ⭐本フィルタで本を消したとき、その本からしか引かれていない論文も一緒に消えるようにするため。
  ⚠出典を持たないノードだけから引かれている論文は、出典なし＝いつも見える（既存の決まりどおり）。
"""
import io, os, re, sys, json

if not (getattr(sys.stdout, 'encoding', '') or '').lower().startswith('utf'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NODES = os.path.join(ROOT, 'nodes')
LIST = os.path.join(ROOT, '_papers', '論文一覧.json')

BAD = re.compile(r'[\/:*?"<>|]')          # ⚠Windows のファイル名に使えない字


def safe(name):
    return BAD.sub('-', name).strip()


def esc_field(s):
    """⚠frontmatter の1行に入れる値。⭐改行とコロンの直後の空白は潰す。"""
    return re.sub(r'\s+', ' ', str(s or '')).strip()


def main():
    look = '--見るだけ' in sys.argv
    over = '--上書き' in sys.argv
    d = json.load(io.open(LIST, encoding='utf-8'))
    made = skipped = 0
    for p in d['papers']:
        fn = safe(p['name']) + '.md'
        path = os.path.join(NODES, fn)
        if os.path.exists(path) and not over:
            skipped += 1
            continue
        # ⭐引いているノードごとに1行。⚠同じノードから2つの ref があれば1本にまとめる
        byn = {}
        for r in p['refs']:
            byn.setdefault(r['node'], []).append(r)
        links = ''.join('  - {to: %s, rel: 裏づけ}\n' % n for n in sorted(byn))
        srcs = sorted({s for r in p['refs'] for s in (r['sources'] or '').split(',') if s})
        au = p['authors']
        aus = (au[0] if len(au) == 1 else
               '%s & %s' % (au[0], au[1]) if len(au) == 2 else
               '%s ら（%d名）' % (au[0], len(au)))
        fields = []
        fields.append('年: %s' % p['year'])
        fields.append('著者: %s' % esc_field(aus))
        if p.get('journal'):
            fields.append('雑誌: %s' % esc_field(p['journal']))
        if p.get('doi'):
            fields.append('DOI: %s' % esc_field(p['doi']))
        fields.append('書誌の出どころ: %s' % esc_field(p['how']))
        url = p['urls'][0]
        ref_note = '書誌は %s で確かめた（2026-09-09）' % esc_field(p['how'])
        head = ['---', 'type: 論文', '確度: 確認済']
        if srcs:
            head.append('出典: %s' % ', '.join(srcs))
        head += fields
        head.append('links:')
        body = '\n'.join(head) + '\n' + links + 'refs:\n'
        body += '  - {title: %s, url: %s, note: %s}\n' % (
            esc_field(p['title'] or p['name']), url, ref_note)
        for u in p['urls'][1:]:
            body += '  - {title: 同じ論文の別の入口, url: %s, note: 引用元にあった url}\n' % u
        body += '---\n\n'
        body += '## これは何か\n'
        body += '**%s**\n\n' % esc_field(p['title'] or '')
        body += '%s（%s）%s\n\n' % (esc_field(aus), p['year'],
                                    '／ *%s*' % esc_field(p['journal']) if p.get('journal') else '')
        if p.get('fix'):
            body += '> %s\n\n' % p['fix']
        if p.get('namewhy'):
            body += '> %s\n\n' % p['namewhy']
        body += '## この地図で、どこに効いているか\n'
        body += '⭐**引いているのは %d か所。**引用元に書かれていた「何を確かめたか」を、そのまま並べる。\n\n' % len(byn)
        for n in sorted(byn):
            for r in byn[n]:
                note = (r['note'] or '').strip() or '（覚え書きなし）'
                body += '- **[[%s]]** ── %s\n' % (n, note)
        body += '\n## 燻太さんの考え\n'
        if look:
            made += 1
            continue
        io.open(path, 'w', encoding='utf-8', newline='\n').write(body)
        made += 1
    print('⭐書いた %d 本 ／ すでにあって触らなかった %d 本' % (made, skipped))
    if look:
        print('（見るだけ。書いていない）')


if __name__ == '__main__':
    main()
