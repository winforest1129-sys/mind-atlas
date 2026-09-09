# -*- coding: utf-8 -*-
"""論文ノードの DOI を集め、Europe PMC で OA かどうかを調べて _papers/oa.json に書く。

⚠ Unpaywall は使わない（メールアドレスの送信が要るため）。Europe PMC と arXiv だけで判定する。
"""
import os, re, json, glob, time, urllib.request, urllib.parse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NODES = os.path.join(ROOT, "nodes")
OUT = os.path.join(ROOT, "_papers")
UA = "mind-atlas/1.0 (academic literature map; contact via github winforest1129-sys)"


def get(url, tries=3):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=45) as r:
                return r.read().decode("utf-8", "replace")
        except Exception as e:
            if i == tries - 1:
                return None
            time.sleep(2 * (i + 1))
    return None


def front(path):
    t = open(path, encoding="utf-8").read()
    if not t.startswith("---"):
        return {}, t
    end = t.find("\n---", 3)
    if end < 0:
        return {}, t
    head = t[3:end]
    meta = {}
    for line in head.split("\n"):
        m = re.match(r"^([^\s:][^:]*):\s*(.*)$", line)
        if m:
            meta[m.group(1).strip()] = m.group(2).strip()
    return meta, t


def main():
    os.makedirs(OUT, exist_ok=True)
    cache_path = os.path.join(OUT, "oa.json")
    cache = {}
    if os.path.exists(cache_path):
        cache = json.load(open(cache_path, encoding="utf-8"))

    papers = []
    for f in sorted(glob.glob(os.path.join(NODES, "*.md"))):
        meta, _ = front(f)
        if meta.get("type") != "論文":
            continue
        name = os.path.splitext(os.path.basename(f))[0]
        papers.append({"name": name, "doi": meta.get("DOI", ""), "file": f})

    print("論文ノード %d 件（DOIあり %d）" % (
        len(papers), sum(1 for p in papers if p["doi"])))

    todo = [p for p in papers if p["doi"] and p["name"] not in cache]
    print("これから問い合わせる: %d 件（控えから %d 件）" % (len(todo), len(papers) - len(todo)))

    for i, p in enumerate(todo, 1):
        q = 'DOI:"%s"' % p["doi"]
        url = ("https://www.ebi.ac.uk/europepmc/webservices/rest/search?query="
               + urllib.parse.quote(q) + "&resultType=core&format=json&pageSize=1")
        raw = get(url)
        rec = {"doi": p["doi"], "oa": False, "pmcid": "", "pdf": "", "src": "", "title": ""}
        if raw:
            try:
                j = json.loads(raw)
                hits = j.get("resultList", {}).get("result", [])
                if hits:
                    h = hits[0]
                    rec["title"] = h.get("title", "")
                    rec["pmcid"] = h.get("pmcid", "") or ""
                    rec["oa"] = (h.get("isOpenAccess") == "Y")
                    rec["inepmc"] = (h.get("inEPMC") == "Y")
                    if rec["oa"] and rec["pmcid"]:
                        rec["pdf"] = "https://europepmc.org/articles/%s?pdf=render" % rec["pmcid"]
                        rec["src"] = "EuropePMC"
                    for u in (h.get("fullTextUrlList", {}) or {}).get("fullTextUrl", []):
                        if not rec["pdf"] and u.get("documentStyle") == "pdf" \
                           and u.get("availability") in ("Open access", "Free"):
                            rec["pdf"] = u.get("url", "")
                            rec["src"] = u.get("site", "other")
            except Exception as e:
                rec["err"] = str(e)
        cache[p["name"]] = rec
        mark = "OA " if rec["oa"] else ("free" if rec["pdf"] else "  - ")
        print("%3d/%d %-28s %s %s" % (i, len(todo), p["name"][:28], mark, rec["pmcid"]))
        time.sleep(0.34)
        if i % 20 == 0:
            json.dump(cache, open(cache_path, "w", encoding="utf-8"),
                      ensure_ascii=False, indent=1)

    json.dump(cache, open(cache_path, "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)

    oa = [k for k, v in cache.items() if v.get("pdf")]
    print("\n=== まとめ ===")
    print("DOIを持つ論文 %d / 全論文 %d" % (
        sum(1 for p in papers if p["doi"]), len(papers)))
    print("⭐ PDFのあてがあるもの: %d" % len(oa))
    print("控え: %s" % cache_path)


if __name__ == "__main__":
    main()
