# -*- coding: utf-8 -*-
"""⭐確定した書誌から、⭐**論文ノードの一覧**を作る（2026-09-09）。

    python tools/make_paper_list.py

⭐出すもの＝`_papers/論文一覧.json`（ノードを書く道具が読む）。
⭐名前は **`年 筆頭著者`**（⭐LAND `Plant-gene-atlas` と同じ形）。
⚠**ぶつかったら**、⭐雑誌の頭文字や第2著者を足して分ける（⭐**何で分けたかを記録する**）。
"""
import io, os, re, sys, json

if not (getattr(sys.stdout, 'encoding', '') or '').lower().startswith('utf'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import resolve_papers as R
import paper_rules as P

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, '_papers', '論文一覧.json')
CACHE = os.path.join(ROOT, '_papers', 'shoshi_cache.json')


def surname(a):
    """⭐姓だけ。⚠`van Tol` のような前置きは残す。⚠記号はならす。"""
    s = re.sub(r'\s+', ' ', (a or '').strip())
    for ch in '\u2010\u2011\u2012\u2013\u2014\u2212':
        s = s.replace(ch, '-')
    # ⚠⚠**姓が全部大文字で返ってくることがある**（PubMed の COCROFT ／ Crossref の KUPER）。
    #   ⭐そのままだと `2005 COCROFT` と `2005 Cocroft` が別の名前になり、
    #   ⚠⚠**Windows は大小を区別しないので、別々の論文が1つのファイルに潰れる**
    #   （2026-09-09に実際に踏んだ。⭐146本のうち 1 本が消えていた）。
    if s and s == s.upper() and len(s) > 1:
        s = '-'.join(w[:1] + w[1:].lower() for w in s.split('-'))
    return s


def main():
    cache = json.load(io.open(CACHE, encoding='utf-8'))
    rows = [r for r in R.load_rows() if r['kind'] == '論文']
    byurl = {}
    for r in rows:
        byurl.setdefault(r['url'], []).append(r)

    papers, skipped = {}, []
    for u, refs in byurl.items():
        if u in P.MISMATCH or u in P.LATE_DROP or any(u.startswith(k) for k in P.LATE_DROP):
            skipped.append((u, P.MISMATCH.get(u, '論文ではないと決め直した')))
            continue
        rec = None
        hkey = next((k for k in P.HAND if u.startswith(k)), None)   # ⭐前方一致でも当てる
        if hkey:
            h = P.HAND[hkey]
            rec = {'doi': h.get('doi', ''), 'title': h['title'], 'year': h['year'],
                   'journal': h['journal'], 'authors': h['authors'],
                   'kind': '', 'how': h['how']}
        else:
            c = cache.get(u) or {}
            if c.get('ok'):
                rec = dict(c['rec'])
            elif u in P.FIX and P.FIX[u].get('doi'):
                rec = R.by_doi(P.FIX[u]['doi'])
                if rec:
                    rec['how'] = 'Crossref(DOI・手当て)'
            elif u in P.FIX and P.FIX[u].get('year') and (c.get('rec') or {}).get('authors'):
                # ⭐年だけ食い違って弾かれたもの＝**書誌そのものは正しく取れている**
                rec = dict(c['rec'])
                rec['how'] = (rec.get('how') or '') + '・年は手当て'
        if not rec:
            skipped.append((u, '外部で書誌を確定できなかった'))
            continue
        fx = P.FIX.get(u) or {}
        if fx.get('year'):
            rec['year'] = fx['year']
        if fx.get('why'):
            rec['fix'] = fx['why']
        if not rec.get('year') or not rec.get('authors'):
            skipped.append((u, '年か著者が取れない'))
            continue
        rec['urls'] = [u]
        rec['refs'] = refs
        # ⭐同じ論文が別の url で2度出てくることがある（DOI で畳む）
        key = (rec.get('doi') or '').lower() or ('%s|%s' % (rec['year'], surname(rec['authors'][0])))
        if key in papers:
            papers[key]['urls'].append(u)
            papers[key]['refs'].extend(refs)
        else:
            papers[key] = rec

    # ⭐名前をつける
    base = {}
    for k, p in papers.items():
        base.setdefault('%s %s' % (p['year'], surname(p['authors'][0])), []).append(k)
    named = {}
    for nm, ks in base.items():
        if len(ks) == 1:
            papers[ks[0]]['name'] = nm
            papers[ks[0]]['namewhy'] = ''
            named[nm.lower()] = ks[0]
            continue
        # ⚠ぶつかった。⭐第2著者 → それでもだめなら雑誌の頭文字
        for k in ks:
            p = papers[k]
            second = surname(p['authors'][1]) if len(p['authors']) > 1 else ''
            cand = ('%s %s & %s' % (p['year'], surname(p['authors'][0]), second)
                    if second else nm)
            if cand.lower() in named or cand == nm:
                jw = re.sub(r'[^A-Za-z ]', '', p.get('journal') or '')
                ini = ''.join(w[0] for w in jw.split() if w)[:4].upper()
                cand = '%s（%s）' % (nm, ini or 'x')
            i = 2
            c0 = cand
            while cand.lower() in named:
                cand = '%s(%d)' % (c0, i)
                i += 1
            p['name'] = cand
            p['namewhy'] = '⚠同じ「%s」が %d 本あったので分けた' % (nm, len(ks))
            named[cand.lower()] = k

    out = {'papers': list(papers.values()), 'skipped': skipped}
    json.dump(out, io.open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('⭐論文ノードになるもの %d 本' % len(papers))
    print('⚠作らないもの %d 本' % len(skipped))
    for u, why in skipped:
        print('   %s' % why)
        print('     %s' % u[:96])
    coll = [p for p in papers.values() if p.get('namewhy')]
    print('⚠名前がぶつかって分けたもの %d 本' % len(coll))
    for p in coll:
        print('   %s  ← %s' % (p['name'], p['namewhy']))
    ys = sorted(p['year'] for p in papers.values())
    print('⭐年の幅 %d〜%d' % (ys[0], ys[-1]))
    print('書いた: ' + OUT)


if __name__ == '__main__':
    main()
