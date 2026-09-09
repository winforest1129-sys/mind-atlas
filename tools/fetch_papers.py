# -*- coding: utf-8 -*-
"""_papers/oa.json を見て、オープンアクセスの本文PDFを papers/ に落とす。

⚠⚠papers/ は .gitignore に入れてある。この地図は public なので本文そのものは公開しない。
⭐落としたら先頭4バイトが %PDF かを必ず確かめる（HTMLが .pdf の名前で保存される事故が起きる）。
"""
import os, io, sys, json, time, threading, urllib.request
from concurrent.futures import ThreadPoolExecutor

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
# ⭐⭐2026-09-09：1本ずつ順に落としたら 2分/本 になった（?pdf=render が遅く、
#   タイムアウト90秒を2つのURLで待っていた）。⭐並行にして待ち時間を重ねる。
#   ⚠相手に負担をかけないよう 5 本まで。タイムアウトも 30 秒に詰める。
WORKERS = 5
TIMEOUT = 30
_lock = threading.Lock()
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAPERS = os.path.join(ROOT, 'papers')
CACHE = os.path.join(ROOT, '_papers', 'oa.json')
LOG = os.path.join(ROOT, '_papers', 'fetch_log.json')
UA = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/124.0 Safari/537.36')


def safe(name):
    """ファイル名に使えない字を落とす。⭐ノード名はそのまま使いたいので最小限だけ直す。"""
    for ch in '\\/:*?"<>|':
        name = name.replace(ch, '-')
    return name.strip()


def fetch(url):
    req = urllib.request.Request(url, headers={
        'User-Agent': UA, 'Accept': 'application/pdf,*/*'})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        return r.read()


def main():
    os.makedirs(PAPERS, exist_ok=True)
    cache = json.load(open(CACHE, encoding='utf-8'))
    log = {}
    if os.path.exists(LOG):
        log = json.load(open(LOG, encoding='utf-8'))

    todo = [(k, v) for k, v in sorted(cache.items()) if v.get('pdf')]
    print('PDFのあてがあるもの: %d 件' % len(todo))

    counts = {'ok': 0, 'skip': 0, 'ng': 0, 'done': 0}

    def one(item):
        name, rec = item
        dest = os.path.join(PAPERS, safe(name) + '.pdf')
        if os.path.exists(dest) and os.path.getsize(dest) > 20000:
            with _lock:
                counts['skip'] += 1
                counts['done'] += 1
            return
        urls = [rec['pdf']] + list(rec.get('pdf_alts') or [])
        # ⭐?pdf=render が駄目なら、PMC の別の入口も試す
        if rec.get('pmcid'):
            urls.append('https://www.ebi.ac.uk/europepmc/webservices/rest/%s/fullTextPDF'
                        % rec['pmcid'])
        got, why, src = None, '', ''
        for u in urls:
            try:
                b = fetch(u)
                if b[:4] == b'%PDF':
                    got, src = b, u
                    break
                why = 'PDFではない中身が返った(%d bytes)' % len(b)
            except Exception as e:
                why = str(e)[:90]
        with _lock:
            counts['done'] += 1
            n = counts['done']
            if got:
                open(dest, 'wb').write(got)
                log[name] = {'ok': True, 'kb': round(len(got) / 1024, 1),
                             'url': src, 'pmcid': rec.get('pmcid', '')}
                counts['ok'] += 1
                print('%3d/%d OK  %-30s %6.1f KB' % (n, len(todo), name[:30], len(got) / 1024))
            else:
                log[name] = {'ok': False, 'why': why, 'url': rec['pdf']}
                counts['ng'] += 1
                print('%3d/%d NG  %-30s %s' % (n, len(todo), name[:30], why[:50]))
            if n % 10 == 0:
                json.dump(log, open(LOG, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
            sys.stdout.flush()

    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        list(ex.map(one, todo))

    json.dump(log, open(LOG, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('\n=== まとめ ===')
    print('落とせた %d ／ すでにあった %d ／ 落とせなかった %d'
          % (counts['ok'], counts['skip'], counts['ng']))
    have = [f for f in os.listdir(PAPERS) if f.endswith('.pdf')]
    print('papers/ にあるPDF: %d 本' % len(have))


if __name__ == '__main__':
    main()
