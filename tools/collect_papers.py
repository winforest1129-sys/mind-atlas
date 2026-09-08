# -*- coding: utf-8 -*-
"""⭐`refs:` に書かれている引用元から、⭐**論文らしいもの**を選り分けて一覧にする（2026-09-09）。

    python tools/collect_papers.py              一覧を _papers/refs一覧.tsv に書く
    python tools/collect_papers.py --わけかた     どう振り分けたかの数だけ見る

⭐**燻太さんの狙い**（2026-09-09）＝
  「書物で読んだ内容が、どのような時期の研究で裏付けられているのか追いやすくする」。

⚠**この道具は振り分けるだけ。**外部に問い合わせるのは `resolve_papers.py`、
  ノードを作るのは `write_papers.py`。⭐**分けてあるのは、途中で目視できるようにするため。**
"""
import io, os, re, sys, json, csv
from collections import Counter

if not (getattr(sys.stdout, 'encoding', '') or '').lower().startswith('utf'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTDIR = os.path.join(ROOT, '_papers')

# ⭐**論文が載る場所**。⚠ここに無くても、題に年と巻号があれば拾う（下の `looks_like_paper`）
PAPER_HOST = (
    'pubmed.ncbi.nlm.nih.gov', 'pmc.ncbi.nlm.nih.gov', 'www.ncbi.nlm.nih.gov',
    'doi.org', 'dx.doi.org', 'onlinelibrary.wiley.com', 'compass.onlinelibrary.wiley.com',
    'journals.sagepub.com', 'www.nature.com', 'www.pnas.org', 'www.sciencedirect.com',
    'www.science.org', 'www.cell.com', 'link.springer.com', 'academic.oup.com',
    'www.frontiersin.org', 'www.jneurosci.org', 'elifesciences.org',
    'journals.plos.org', 'royalsocietypublishing.org', 'ajph.aphapublications.org',
    'www.semanticscholar.org', 'oa.mg', 'psycnet.apa.org', 'www.jstor.org',
    'www.tandfonline.com', 'www.biorxiv.org', 'www.medrxiv.org', 'journals.physiology.org',
    'www.mdpi.com', 'bmcpsychology.biomedcentral.com', 'www.cambridge.org',
    'www.researchgate.net', 'www2.psych.ubc.ca', 'psycnet.apa.org',
)
# ⚠**論文ではないもの**（版元・辞書・団体・書店・報道）。⭐ここは題を見ずに落とす
NOT_PAPER_HOST = (
    'en.wikipedia.org', 'ja.wikipedia.org', 'www.iwanami.co.jp', 'www.kawade.co.jp',
    'hexaco.org', 'www.penguinrandomhouse.com', 'www.myersbriggs.org', 'www.hanmoto.com',
    'www.amazon.com', 'www.amazon.co.jp', 'needpress.com',
    'www.deutsche-digitale-bibliothek.de', 'interdevelopmentals.org',
    'retractionwatch.com', 'psu.pb.unizin.org', 'www.bps.org.uk',
    'www.gutenberg.org', 'openlibrary.org', 'www.worldcat.org',
)

YEAR_RE = re.compile(r'(?<!\d)(1[89]\d{2}|20[0-2]\d)(?!\d)')
# ⭐巻号ページの形（`27(9):2349-2356` / `8, 171` / `54(7):480-492`）
VOLPAGE_RE = re.compile(r'\d+\s*(\(\d+\))?\s*[:,]\s*\d+')


def host_of(u):
    m = re.match(r'https?://([^/]+)', u or '')
    return m.group(1).lower() if m else ''


def year_of(s):
    ys = [int(y) for y in YEAR_RE.findall(s or '')]
    return max(ys) if ys else None


def looks_like_paper(title, url):
    """⭐宿主で決まらないときの手がかり＝**年があり、巻号ページの形がある**。"""
    return bool(year_of(title)) and bool(VOLPAGE_RE.search(title or ''))


def classify(title, url):
    h = host_of(url)
    if h in NOT_PAPER_HOST:
        return 'ちがう'
    if h in PAPER_HOST:
        return '論文'
    if h == 'archive.org':
        # ⚠archive.org は論文の写しも本の写しもある。⭐題で見分ける
        return '論文' if looks_like_paper(title, url) else '要確認'
    if not h:
        return '要確認'                       # URL の無い ref（＝記憶で書いたもの）
    return '論文' if looks_like_paper(title, url) else '要確認'


def collect():
    d = json.load(io.open(os.path.join(ROOT, 'data.json'), encoding='utf-8'))
    rows = []
    for n in d['nodes']:
        # ⚠⚠**論文ノード自身の refs は数えない**（2026-09-09に踏んだ）。
        #   ⭐これはこの道具の**出力**であって、入力ではない。
        #   ⚠外さないと、流すたびに refs が膨らむ（345→493件になった）。
        if n.get('type') == '論文':
            continue
        for r in (n.get('refs') or []):
            t, u = r.get('title', ''), r.get('url', '')
            rows.append({'node': n['id'], 'type': n.get('type', ''),
                         'sources': ','.join(n.get('sources') or []),
                         'kind': classify(t, u), 'year': year_of(t) or '',
                         'title': t, 'url': u, 'note': r.get('note', '')})
    return rows


def main():
    rows = collect()
    c = Counter(r['kind'] for r in rows)
    print('refs 総数 %d' % len(rows))
    for k in ('論文', '要確認', 'ちがう'):
        print('  %-6s %4d' % (k, c[k]))
    # ⭐同じ url が何度も出てくる（＝複数のノードが同じ論文を引いている）
    urls = Counter(r['url'] for r in rows if r['kind'] == '論文' and r['url'])
    print('  ⭐論文のうち、別々の url は %d 本（うち2つ以上のノードから引かれているもの %d 本）'
          % (len(urls), sum(1 for v in urls.values() if v > 1)))
    ys = [r['year'] for r in rows if r['kind'] == '論文' and r['year']]
    if ys:
        print('  ⭐年が取れたもの %d 本（%d〜%d）' % (len(ys), min(ys), max(ys)))
    if '--わけかた' in sys.argv:
        return
    os.makedirs(OUTDIR, exist_ok=True)
    p = os.path.join(OUTDIR, 'refs一覧.tsv')
    with io.open(p, 'w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, delimiter='\t',
                           fieldnames=['kind', 'year', 'node', 'type', 'sources',
                                       'title', 'url', 'note'])
        w.writeheader()
        for r in sorted(rows, key=lambda r: (r['kind'], str(r['year']), r['node'])):
            w.writerow(r)
    print('書いた: ' + p)


if __name__ == '__main__':
    main()
