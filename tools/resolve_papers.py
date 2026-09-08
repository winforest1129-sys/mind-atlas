# -*- coding: utf-8 -*-
"""⭐`refs:` の論文を、⭐外部（Crossref／PubMed）に問い合わせて書誌を確定する（2026-09-09）。

    python tools/resolve_papers.py            取りにいく（⭐控えがあれば使い回す）
    python tools/resolve_papers.py --やり直し   控えを捨てて取り直す

⭐出どころ＝Crossref REST API ／ NCBI E-utilities（どちらも公開・鍵不要）。
⭐控えは `_papers/書誌キャッシュ.json`（⭐同じものを何度も叩かない）。

⚠⚠いちばん怖いのは、別の論文を掴むこと。
  LAND で `2006 Ichimura` の素性が丸ごと誤っていた事故がある。
  ⭐だから照合を必ず通す＝
    ① 引用元の文字列にある年と、取れた年が ±1 年で合うこと
    ② 引用元の文字列に、取れた筆頭著者の姓が入っていること
  ⭐どちらかでも外れたら要確認にして、採らない。推測で埋めない。
"""
import io, os, re, sys, json, time, urllib.request, urllib.parse

if not (getattr(sys.stdout, 'encoding', '') or '').lower().startswith('utf'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import collect_papers as C
from paper_rules import decide

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTDIR = os.path.join(ROOT, '_papers')
CACHE = os.path.join(OUTDIR, 'shoshi_cache.json')
MAIL = 'w.in.forest1129@gmail.com'
UA = 'mind-atlas/1.0 (mailto:%s)' % MAIL

DOI_RE = re.compile(r'\b(10\.\d{4,9}/[^\s"<>?#]+)', re.I)
PMID_RE = re.compile(r'pubmed\.ncbi\.nlm\.nih\.gov/(\d+)')
PMC_RE = re.compile(r'(PMC\d+)')


def get(url, tries=3):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': UA,
                                                       'Accept': 'application/json'})
            with urllib.request.urlopen(req, timeout=25) as r:
                return json.loads(r.read().decode('utf-8', 'replace'))
        except Exception:
            if i == tries - 1:
                return None
            time.sleep(1.2 * (i + 1))
    return None


TAIL_RE = re.compile(r'/(full|abstract|pdf|epdf|meta|html|short|abs|citation)$', re.I)


def clean_doi(d):
    d = re.sub(r'[.,;)\]]+$', '', d)
    # ⚠⚠**これで14本を取り逃していた**（2026-09-09）。
    #   Frontiers は `.../articles/10.3389/fpsyg.2020.01429/full` の形で、
    #   ⭐末尾の `/full` まで DOI に食いこんでいた。
    for _ in range(2):
        d = TAIL_RE.sub('', d)
    return d


def doi_from_url(u):
    """⭐url から DOI を取り出す。⚠**Nature は記事IDがそのまま DOI の後半**。"""
    m = DOI_RE.search(u or '')
    if m:
        return clean_doi(m.group(1))
    m = re.search(r'nature\.com/articles/(s?[0-9a-zA-Z._-]+)', u or '')
    if m:
        return '10.1038/' + m.group(1)
    return None


def from_crossref_msg(m, how):
    if not m:
        return None
    au = [a.get('family') or a.get('name') or '' for a in (m.get('author') or [])]
    dp = ((m.get('issued') or {}).get('date-parts') or [[None]])[0]
    ct = (m.get('container-title') or [''])
    return {'doi': (m.get('DOI') or '').lower(),
            'title': re.sub(r'\s+', ' ', (m.get('title') or [''])[0] or ''),
            'year': dp[0] if dp else None,
            'journal': re.sub(r'&amp;', '&', ct[0] if ct else ''),
            'authors': [a for a in au if a],
            'kind': m.get('type') or '',
            'how': how}


def by_doi(doi):
    d = get('https://api.crossref.org/works/%s?mailto=%s'
            % (urllib.parse.quote(doi), MAIL))
    return from_crossref_msg((d or {}).get('message'), 'Crossref(DOI)')


def pm_surname(name):
    """PubMed の著者名は「姓 イニシャル」の形（`Xu P` / `van Tol MJ`）。

    ⚠⚠**先頭の語を取ると、複合姓で壊れる**（`Al Bahri M` → `Al`）。
      ⭐2026-09-09 に `2025 Al` という意味のないノード名が出て気づいた。
    ⭐**末尾のイニシャルだけを落とす**のが正しい。
    """
    return re.sub(r'\s+[A-Z]{1,4}$', '', (name or '').strip()) or (name or '').strip()


def by_pmid(pmid):
    d = get('https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi'
            '?db=pubmed&retmode=json&id=' + pmid)
    r = ((d or {}).get('result') or {}).get(pmid)
    if not r:
        return None
    doi = ''
    for a in (r.get('articleids') or []):
        if a.get('idtype') == 'doi':
            doi = (a.get('value') or '').lower()
    y = re.match(r'(\d{4})', r.get('pubdate') or '')
    return {'doi': doi, 'title': re.sub(r'\s+', ' ', r.get('title') or '').rstrip('.'),
            'year': int(y.group(1)) if y else None,
            'journal': r.get('fulljournalname') or r.get('source') or '',
            'authors': [pm_surname(a.get('name', '')) for a in (r.get('authors') or [])],
            'kind': 'journal-article', 'how': 'PubMed(PMID)'}


def pmc_to_pmid(pmc):
    d = get('https://www.ncbi.nlm.nih.gov/pmc/utils/idconv/v1.0/?format=json&ids=' + pmc)
    for r in ((d or {}).get('records') or []):
        if r.get('pmid'):
            return str(r['pmid'])          # ⚠数で返ってくることがある
        if r.get('doi'):
            return 'doi:' + str(r['doi'])
    return None


def by_title(q):
    d = get('https://api.crossref.org/works?rows=3&mailto=%s&query.bibliographic=%s'
            % (MAIL, urllib.parse.quote(q[:300])))
    items = ((d or {}).get('message') or {}).get('items') or []
    return [from_crossref_msg(m, 'Crossref(title)') for m in items]


def norm(s):
    """⚠**ハイフンが何種類もある**（Baron‐Cohen で照合を落とした）。ならして比べる。"""
    s = (s or '').lower()
    for ch in '‐‑‒–—−':
        s = s.replace(ch, '-')
    return s


def agrees(rec, ref_title, exact_id=False):
    """⚠照合。

    ⭐**url に DOI か PMID が入っていたら、それが正**（`exact_id`）。
      その場合、著者の照合は掛けない ── 引用元の文字列が題だけのことがあるため。
    ⚠**年の食い違いだけは、`exact_id` でも残す。**
      ⭐実際にこれで、⭐**引用元の題と url が別の論文を指している箇所**が2つ見つかった。
    """
    if not rec:
        return False, 'torenakatta'
    # ⚠⚠**年が取れないものは通さない**（2026-09-09に穴を塞いだ）。
    #   ⭐`Reynierse 2009` が、年の無い別の章（Type Theory Revisited）に化けていた。
    #   ⭐年が無いと年の照合が飛ぶので、⭐**素通りしてしまう。**
    if not rec.get('year'):
        return False, 'toshi ga torenai'
    ry = C.year_of(ref_title)
    if rec.get('year') and ry and abs(int(rec['year']) - int(ry)) > 1:
        return False, 'nen ga awanai (ref %s / got %s)' % (ry, rec['year'])
    au = (rec.get('authors') or [''])[0]
    if not au:
        return (True, '') if exact_id else (False, 'chosha ga torenai')
    if exact_id:
        return True, ''
    # ⚠⚠**題で探したものは、ここを通さないと化ける**（2026-09-09に2つ踏んだ）。
    #   ① 引用元に年が無いと年の照合が飛ぶ ── ⭐**年が無いなら題での照合は認めない**
    #      （`同メタ分析の全文PDF（ペンシルベニア大学）` が、
    #        ⭐**まったく無関係な中国語の教育論文**に化けた）
    #   ② `len(au) > 2` にしていたので、⭐**漢字2文字の姓が照合をすり抜けた**
    if not ry:
        return False, 'ref ni nen ga nai (title search wa mitomenai)'
    if norm(au) not in norm(ref_title):
        return False, 'hittou chosha [%s] ga ref ni nai' % au
    return True, ''


def resolve_one(url, ref_title):
    """戻り値＝(書誌, 確かなidで取れたか)。"""
    d = doi_from_url(url)
    if d:
        r = by_doi(d)
        if r:
            return r, True
    m = PMID_RE.search(url or '')
    if m:
        r = by_pmid(m.group(1))
        if r:
            return r, True
    m = PMC_RE.search(url or '')
    if m:
        p = pmc_to_pmid(m.group(1))
        if p and p.startswith('doi:'):
            r = by_doi(p[4:])
            if r:
                return r, True
        elif p:
            r = by_pmid(p)
            if r:
                return r, True
    for r in by_title(ref_title or ''):
        ok, _ = agrees(r, ref_title)
        if ok:
            return r, False
    return None, False


def load_rows():
    rows = C.collect()
    for r in rows:
        r['kind'] = decide(r['kind'], r['url'])
    return rows


def main():
    fresh = '--やり直し' in sys.argv
    os.makedirs(OUTDIR, exist_ok=True)
    cache = {} if fresh or not os.path.exists(CACHE) else \
        json.load(io.open(CACHE, encoding='utf-8'))
    papers = [r for r in load_rows() if r['kind'] == '論文']
    byurl = {}
    for r in papers:
        byurl.setdefault(r['url'], []).append(r)
    print('論文の refs %d件 / betsubetsu no url %d hon' % (len(papers), len(byurl)))
    todo = [u for u in byurl if u not in cache]
    print('mada totte inai %d hon' % len(todo))
    for i, u in enumerate(todo, 1):
        t = byurl[u][0]['title']
        rec, exact = resolve_one(u, t)
        ok, why = agrees(rec, t, exact)
        cache[u] = {'rec': rec, 'ok': ok, 'why': why, 'ref_title': t,
                    'exact': exact}
        if i % 10 == 0 or i == len(todo):
            print('  %d/%d' % (i, len(todo)))
            json.dump(cache, io.open(CACHE, 'w', encoding='utf-8'),
                      ensure_ascii=False, indent=1)
        time.sleep(0.12)
    json.dump(cache, io.open(CACHE, 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    good = sum(1 for u in byurl if cache.get(u, {}).get('ok'))
    print('shougou ga tootta %d / %d hon' % (good, len(byurl)))
    print('hikae: ' + CACHE)


if __name__ == '__main__':
    main()
