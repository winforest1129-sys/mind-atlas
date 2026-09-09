# -*- coding: utf-8 -*-
"""Europe PMC で見つからなかったぶんを OpenAlex で調べ直して _papers/oa.json を厚くする。

⭐なぜ要るか＝心理学の文献は生物医学系（PMC）に載らないものが多い。
  OpenAlex は Unpaywall のデータを取りこんでいるので、大学リポジトリや PsyArXiv の写しも拾える。
⚠ Unpaywall を直に叩かないのは、必須パラメータでメールアドレスを送ることになるため。
"""
import os, io, sys, json, time, re, glob, urllib.request, urllib.parse

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(ROOT, '_papers', 'oa.json')
UA = 'mind-atlas/1.0 (academic literature map; github winforest1129-sys)'


def get(url, tries=2):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': UA})
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.read().decode('utf-8', 'replace')
        except Exception:
            if i == tries - 1:
                return None
            time.sleep(1.5)
    return None


def main():
    cache = json.load(open(CACHE, encoding='utf-8'))
    # ⚠ Europe PMC の ?pdf=render が 404 を返したぶんも、探し直しの対象に入れる
    #   （記録はあるのに実体が無い、ということが 20 件あった）
    log_path = os.path.join(ROOT, '_papers', 'fetch_log.json')
    failed = set()
    if os.path.exists(log_path):
        lg = json.load(open(log_path, encoding='utf-8'))
        failed = {k for k, v in lg.items() if not v.get('ok')}
    for k in failed:
        if k in cache:
            cache[k]['pdf_epmc_ng'] = cache[k].get('pdf', '')
            cache[k]['pdf'] = ''
    todo = [(k, v) for k, v in sorted(cache.items())
            if not v.get('pdf') and v.get('doi')]
    print('OpenAlex で調べ直す: %d 件（うち EPMC で 404 だったもの %d）'
          % (len(todo), len(failed)))

    found = 0
    for i, (name, rec) in enumerate(todo, 1):
        url = 'https://api.openalex.org/works/doi:' + urllib.parse.quote(rec['doi'])
        raw = get(url)
        rec['oa2'] = True
        if raw:
            try:
                j = json.loads(raw)
                oa = j.get('open_access', {}) or {}
                # ⚠⚠2026-09-09の教訓：oa_url はランディングページのことが多く、
                #   落とすと 3038 バイトの HTML が返ってくる。⭐直の pdf_url を先に集める。
                cands, seen = [], set()

                def push(u):
                    if u and u not in seen:
                        seen.add(u)
                        cands.append(u)

                best = j.get('best_oa_location') or {}
                push(best.get('pdf_url'))
                for loc in (j.get('locations') or []):
                    if loc.get('is_oa'):
                        push(loc.get('pdf_url'))
                for loc in (j.get('locations') or []):
                    if loc.get('is_oa'):
                        push(loc.get('landing_page_url'))
                push(best.get('landing_page_url'))
                push(oa.get('oa_url'))

                if cands:
                    rec['pdf'] = cands[0]
                    rec['pdf_alts'] = cands[1:6]
                    rec['src'] = 'OpenAlex/' + (oa.get('oa_status') or '?')
                    found += 1
                    print('%3d/%d ⭐ %-26s %-8s 候補%d' %
                          (i, len(todo), name[:26], oa.get('oa_status'), len(cands)))
            except Exception as e:
                rec['err2'] = str(e)[:60]
        time.sleep(0.15)
        if i % 25 == 0:
            json.dump(cache, open(CACHE, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
            print('   … %d 件まで（新たに %d 件みつかった）' % (i, found))

    json.dump(cache, open(CACHE, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    total = sum(1 for v in cache.values() if v.get('pdf'))
    print('\n=== まとめ ===')
    print('OpenAlex で新たに見つかった: %d 件' % found)
    print('⭐ PDFのあてがあるもの（合計）: %d 件' % total)


if __name__ == '__main__':
    main()
