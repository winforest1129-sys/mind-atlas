# -*- coding: utf-8 -*-
"""⭐地図に `論文` 型を通す手当て（2026-09-09・燻太さんの指定）。

    python tools/patch_papers.py            当てる（何度流しても1回ぶん）
    python tools/patch_papers.py --見るだけ

⭐燻太さんの狙い＝「書物で読んだ内容が、どのような時期の研究で裏付けられているのか追いやすくする」。

⭐当てるところ
  `tools/build_map.py` … ① `論文` を型に足す ② `年 / 著者 / 雑誌 / DOI` を data.json へ通す
  `index.html`        … ③ 形と色 ④ 一覧の並び ⑤ 説明欄に書誌を出す
                        ⑥ ⭐**輪の中では、論文だけ年代順に並べる**

⚠**輪の作りそのもの（一周を種類ごと）は変えていない。**
  ⭐変えたのは「論文の扇の中の並び」だけ＝ラベル順 → **年代順**。
  ⏳LAND のように「上半分を丸ごと論文の年表にする」かどうかは、燻太さんと相談してから。
"""
import io, os, sys

if not (getattr(sys.stdout, 'encoding', '') or '').lower().startswith('utf'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BM = os.path.join(ROOT, 'tools', 'build_map.py')
IH = os.path.join(ROOT, 'index.html')
MARK = 'MIND-PAPER-TYPE'

A_TYPES = "VALID_TYPES = ['用語', '人物', '実験', '症例', '書物', '理論', '予感']"
B_TYPES = ("VALID_TYPES = ['用語', '人物', '実験', '症例', '書物', '理論', '予感', '論文']\n"
           "# ⭐MIND-PAPER-TYPE：論文ノードが持てる欄（2026-09-09）。\n"
           "#   ⚠ここに無い欄は data.json に通らない（型ごとの決まった欄だけを通す作り）。\n"
           "PAPER_FIELDS = ['年', '著者', '雑誌', 'DOI', '書誌の出どころ']")

A_NODE = """        nodes[nid] = {
            'id': nid, 'type': ntype, 'confidence': conf,
            'sources': sources, 'refs': refs, 'brain': brain, 'file': 'nodes/' + fn,
            'owned': owned, 'shops': shops,
            'sections': split_sections(body), 'stub': False,
        }"""
B_NODE = """        # ⭐論文の書誌（年・著者・雑誌・DOI）を通す。⚠他の型では空のまま
        fields = {}
        for k in PAPER_FIELDS:
            if meta.get(k):
                fields[k] = meta[k]
        if ntype == '論文' and not fields.get('年'):
            warnings.append(fn + ': 論文なのに 年 が無い（輪で年代順に並べられない）')

        nodes[nid] = {
            'id': nid, 'type': ntype, 'confidence': conf,
            'sources': sources, 'refs': refs, 'brain': brain, 'file': 'nodes/' + fn,
            'owned': owned, 'shops': shops, 'fields': fields,
            'sections': split_sections(body), 'stub': False,
        }"""
A_STUB = """                'owned': '不明', 'shops': [],
                'sections': {}, 'stub': True,"""
B_STUB = """                'owned': '不明', 'shops': [], 'fields': {},
                'sections': {}, 'stub': True,"""

A_SHAPE = """  '予感':'star'
};"""
B_SHAPE = """  '予感':'star', '論文':'rectangle'
};"""
A_COLOR = """  '予感':'#a8577a'
};"""
B_COLOR = """  '予感':'#a8577a',
  // ⭐論文（2026-09-09）。⚠いちばん数が多くなる型なので、⭐落ち着いた灰青にして
  //   書物（濃い青 #3d5a80）とも用語（紫 #7a6da8）とも見分けがつくようにした
  '論文':'#7d8794'
};"""
A_ORDER = "const ORDER = ['予感','書物','人物','理論','症例','実験','用語'];"
B_ORDER = ("// ⭐論文は書物のとなり（どちらも「どこから来たか」の側）。⭐輪の並びもこの順を使う\n"
           "const ORDER = ['予感','書物','論文','人物','理論','症例','実験','用語'];")

# ⭐輪の中の並び。⚠論文だけ年代順にする（MIND-PAPER-TYPE）
A_SORT = """function sortByType(arr){
  return arr.slice().sort((a, b) => {
    const ia = ORDER.indexOf(a.data('type')), ib = ORDER.indexOf(b.data('type'));
    return ((ia < 0 ? 99 : ia) - (ib < 0 ? 99 : ib)) ||
           a.data('label').localeCompare(b.data('label'), 'ja');
  });
}"""
B_SORT = r"""function paperYear(n){
  const d = n.data('node');
  const y = d && d.fields && d.fields['年'];
  if (y && /^\d{4}$/.test(String(y).trim())) return parseInt(y, 10);
  const m = /(\d{4})/.exec(String(n.data('label') || ''));
  return m ? parseInt(m[1], 10) : 9999;      // 年が分からないものは最後に回す
}
function sortByType(arr){
  return arr.slice().sort((a, b) => {
    const ia = ORDER.indexOf(a.data('type')), ib = ORDER.indexOf(b.data('type'));
    const d = (ia < 0 ? 99 : ia) - (ib < 0 ? 99 : ib);
    if (d) return d;
    /* ⭐⭐MIND-PAPER-TYPE（2026-09-09）：**論文どうしは年代順**に並べる。
       ⭐燻太さんの狙い＝「どのような時期の研究で裏付けられているのか追いやすく」。
       ⚠輪の作り（一周を種類ごと）は変えていない。⭐変えたのは論文の扇の中だけ。 */
    if (a.data('type') === '論文' && b.data('type') === '論文'){
      const ya = paperYear(a), yb = paperYear(b);
      if (ya !== yb) return ya - yb;
    }
    return a.data('label').localeCompare(b.data('label'), 'ja');
  });
}"""

# ⭐説明欄に書誌を出す
A_SHOW = """  if (n.sources.length) h += '<br>出典: ' + n.sources.map(esc).join(' / ');"""
B_SHOW = """  if (n.sources.length) h += '<br>出典: ' + n.sources.map(esc).join(' / ');
  /* ⭐⭐MIND-PAPER-TYPE：論文の書誌を、いちばん上に出す（2026-09-09）。
     ⚠**どこから取った書誌かも必ず出す** ── Crossref／PubMed で確かめたのか、
       引用元の記述をそのまま写したのかで、寄りかかれる度合いが違う。 */
  if (n.fields && Object.keys(n.fields).length){
    const F = n.fields;
    const line = [];
    if (F['著者']) line.push(esc(F['著者']));
    if (F['年'])   line.push(esc(F['年']));
    if (F['雑誌']) line.push('<i>' + esc(F['雑誌']) + '</i>');
    if (line.length) h += '<br>' + line.join(' ・ ');
    if (F['DOI']) h += '<br>DOI: <a href="https://doi.org/' + esc(F['DOI']) +
                       '" target="_blank" rel="noopener noreferrer">' + esc(F['DOI']) + '</a>';
    if (F['書誌の出どころ'])
      h += '<br><span style="opacity:.75">書誌の出どころ: ' + esc(F['書誌の出どころ']) + '</span>';
  }"""


def patch(path, pairs, look):
    s = io.open(path, encoding='utf-8').read()
    if MARK in s:
        print('  ⭐もう当たっている: ' + os.path.basename(path))
        return None
    for a, b in pairs:
        if s.count(a) != 1:
            print('  ⚠当てる先が見つからない／複数ある（%d件）: %s'
                  % (s.count(a), a.split('\n')[0][:60]))
            return False
    if look:
        return True
    for a, b in pairs:
        s = s.replace(a, b, 1)
    io.open(path, 'w', encoding='utf-8', newline='\n').write(s)
    return True


def main():
    look = '--見るだけ' in sys.argv
    ok1 = patch(BM, [(A_TYPES, B_TYPES), (A_NODE, B_NODE), (A_STUB, B_STUB)], look)
    ok2 = patch(IH, [(A_SHAPE, B_SHAPE), (A_COLOR, B_COLOR), (A_ORDER, B_ORDER),
                     (A_SORT, B_SORT), (A_SHOW, B_SHOW)], look)
    if ok1 is False or ok2 is False:
        return 1
    print('⭐' + ('当てる先はぜんぶ見つかった（書いていない）' if look else '当てた'))
    return 0


if __name__ == '__main__':
    sys.exit(main())
