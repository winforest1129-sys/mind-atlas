# -*- coding: utf-8 -*-
"""nodes/*.md を読んで data.json を作る。

使い方:  python tools/build_map.py     （cwd はどこでもよい）

frontmatter の書式（自前パース。PyYAML は不要）:
---
type: 用語            # 用語 / 人物 / 実験 / 症例 / 書物 / 理論
label: 中核意識        # 省略可。省略時はファイル名を使う
出典: 01_ダマシオ      # 蔵書リストの番号。カンマ区切りで複数可
確度: 推測            # 確認済 / 推測 / 未調査
links:
  - {to: 原自己, rel: 土台}
  - {to: 構成主義的情動理論, rel: 対立}
refs:
  - {title: 論文や記事の題, url: https://..., note: 何を確かめたか}
脳部位: vmpfc, ofc      # 脳の模式図で光らせる領域。BRAIN_AREAS のIDをカンマ区切りで
---
本文は "## 見出し" ごとに切って JSON に入れる。

refs = そのノードを書くときに実際に当たった外部の情報源。
右パネルのいちばん下に、リンクとして出る。
**当たっていないなら書かない。** 空であることが「これは記憶で書いた」という印になる。

links の to が nodes/ にまだ無いときは、
「これから調べる用語」として stub ノードを自動で作る（地図上に破線で出る）。
消さずに残すことで、次に何を調べるかが地図の上に見える。
"""
import io, json, os, re, sys, datetime

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NODES_DIR = os.path.join(ROOT, 'nodes')
OUT = os.path.join(ROOT, 'data.json')

VALID_TYPES = ['用語', '人物', '実験', '症例', '書物', '理論']
VALID_CONF = ['確認済', '推測', '未調査']

# 脳の模式図に載せられる領域。index.html の BRAIN_AREAS と必ず揃えること
BRAIN_AREAS = [
    'pfc', 'vmpfc', 'ofc', 'dlpfc', 'vlpfc', 'motor', 'somatosensory',
    'parietal', 'occipital', 'temporal', 'insula',
    'acc', 'pcc', 'corpus_callosum',
    'amygdala', 'hippocampus', 'thalamus', 'hypothalamus',
    'brainstem', 'cerebellum',
]

# 強さ は省略可。省略すると 標準。⚠ rel に半角カンマは書けない（2026-08-31時点で1件も無い）
LINK_RE = re.compile(
    r'^\s*-\s*\{\s*to\s*:\s*(?P<to>[^,}]+?)\s*,\s*rel\s*:\s*(?P<rel>[^,}]+?)\s*'
    r'(?:,\s*強さ\s*:\s*(?P<w>[^,}]+?)\s*)?\}\s*$')

VALID_WEIGHT = ['強', '標準', '弱']
REF_RE = re.compile(
    r'^\s*-\s*\{\s*title\s*:\s*(?P<title>.+?)\s*,\s*url\s*:\s*(?P<url>\S+?)\s*'
    r'(?:,\s*note\s*:\s*(?P<note>[^}]*?)\s*)?\}\s*$')
# 入手: 買える場所。refs（出典）とは別物なので、店名キーで書き分ける
SHOP_RE = re.compile(
    r'^\s*-\s*\{\s*店\s*:\s*(?P<shop>[^,}]+?)\s*,\s*url\s*:\s*(?P<url>\S+?)\s*'
    r'(?:,\s*note\s*:\s*(?P<note>[^}]*?)\s*)?\}\s*$')

VALID_OWNED = ['有', '無', '不明']


def parse_front_matter(text):
    """先頭の --- ... --- を dict に。本文も返す。"""
    if not text.startswith('---'):
        return {}, text
    end = text.find('\n---', 3)
    if end == -1:
        return {}, text
    raw = text[3:end].strip('\n')
    body = text[end + 4:].lstrip('\n')

    meta, links, refs, shops, bad = {}, [], [], [], []
    for line in raw.split('\n'):
        if not line.strip() or line.strip().startswith('#'):
            continue
        m = LINK_RE.match(line)
        if m:
            links.append({'to': m.group('to').strip(),
                          'rel': m.group('rel').strip(),
                          'weight': (m.group('w') or '標準').strip()})
            continue
        m = REF_RE.match(line)
        if m:
            refs.append({'title': m.group('title').strip(),
                         'url': m.group('url').strip(),
                         'note': (m.group('note') or '').strip()})
            continue
        m = SHOP_RE.match(line)
        if m:
            shops.append({'shop': m.group('shop').strip(),
                          'url': m.group('url').strip(),
                          'note': (m.group('note') or '').strip()})
            continue
        if line.lstrip().startswith('- {'):
            bad.append(line.strip())      # どちらの書式にも合わない行は警告に回す
            continue
        if line.startswith((' ', '\t')):
            continue                      # links/refs 以外のインデント行は無視
        if ':' not in line:
            continue
        key, _, val = line.partition(':')
        key, val = key.strip(), val.strip()
        if key in ('links', 'refs', '入手'):
            continue
        val = val.strip('[]')             # 出典: [a, b] も許す
        meta[key] = val
    meta['links'] = links
    meta['refs'] = refs
    meta['shops'] = shops
    meta['_bad'] = bad
    return meta, body


def split_sections(body):
    """本文を "## 見出し" ごとの dict に。"""
    out, cur, buf = {}, None, []
    for line in body.split('\n'):
        if line.startswith('## '):
            if cur is not None:
                out[cur] = '\n'.join(buf).strip()
            cur, buf = line[3:].strip(), []
        else:
            buf.append(line)
    if cur is not None:
        out[cur] = '\n'.join(buf).strip()
    return out


def main():
    if not os.path.isdir(NODES_DIR):
        print('nodes/ が無い: ' + NODES_DIR)
        return 1

    nodes, edges, warnings = {}, [], []

    for fn in sorted(os.listdir(NODES_DIR)):
        if not fn.endswith('.md') or fn.startswith('_'):
            continue
        path = os.path.join(NODES_DIR, fn)
        text = io.open(path, encoding='utf-8').read()
        meta, body = parse_front_matter(text)
        nid = meta.get('label') or os.path.splitext(fn)[0]

        if nid in nodes:
            warnings.append('id が重複: ' + nid + '（' + fn + '）')
        for b in meta.get('_bad', []):
            warnings.append(fn + ': 書式が読めない行 → ' + b)

        ntype = meta.get('type', '用語')
        if ntype not in VALID_TYPES:
            warnings.append(fn + ': type が不正 "' + ntype + '" → 用語 に倒した')
            ntype = '用語'
        conf = meta.get('確度', '未調査')
        if conf not in VALID_CONF:
            warnings.append(fn + ': 確度 が不正 "' + conf + '" → 未調査 に倒した')
            conf = '未調査'

        refs = meta.get('refs', [])
        if conf == '確認済' and not refs and ntype not in ('書物', '人物'):
            warnings.append(fn + ': 確度が「確認済」なのに refs が無い（出典を書くか、推測に落とす）')

        owned = meta.get('所持', '不明')
        if owned not in VALID_OWNED:
            warnings.append(fn + ': 所持 が不正 "' + owned + '" → 不明 に倒した')
            owned = '不明'
        shops = meta.get('shops', [])
        if owned == '無' and not shops:
            warnings.append(fn + ': 所持が「無」なのに 入手 のリンクが無い'
                            '（読みたくなったときに買えるようにする）')
        if owned != '無' and shops:
            warnings.append(fn + ': 入手 のリンクがあるのに 所持 が「無」でない')

        sources = [s.strip() for s in meta.get('出典', '').split(',') if s.strip()]

        brain = [b.strip() for b in meta.get('脳部位', '').split(',') if b.strip()]
        for b in brain:
            if b not in BRAIN_AREAS:
                warnings.append(fn + ': 脳部位 "' + b + '" は図に無い（使えるのは ' +
                                ', '.join(BRAIN_AREAS) + '）')
        brain = [b for b in brain if b in BRAIN_AREAS]

        nodes[nid] = {
            'id': nid, 'type': ntype, 'confidence': conf,
            'sources': sources, 'refs': refs, 'brain': brain, 'file': 'nodes/' + fn,
            'owned': owned, 'shops': shops,
            'sections': split_sections(body), 'stub': False,
        }
        for lk in meta['links']:
            w = lk.get('weight', '標準')
            if w not in VALID_WEIGHT:
                warnings.append(fn + ': 強さ が不正 "' + w + '" → 標準 に倒した'
                                '（使えるのは ' + ' / '.join(VALID_WEIGHT) + '）')
                w = '標準'
            edges.append({'source': nid, 'target': lk['to'],
                          'rel': lk['rel'], 'weight': w})

    # まだ書いていない用語を stub として起こす
    for e in edges:
        if e['target'] not in nodes:
            nodes[e['target']] = {
                'id': e['target'], 'type': '用語', 'confidence': '未調査',
                'sources': [], 'refs': [], 'brain': [], 'file': None,
                'owned': '不明', 'shops': [],
                'sections': {}, 'stub': True,
            }

    # 線が1本も無いノードを警告
    linked = set()
    for e in edges:
        linked.add(e['source']); linked.add(e['target'])
    for nid in nodes:
        if nid not in linked:
            warnings.append('線が1本も無い: ' + nid)

    data = {
        'generated': datetime.datetime.now().strftime('%Y-%m-%d %H:%M'),
        'nodes': sorted(nodes.values(), key=lambda n: n['id']),
        'edges': edges,
    }
    io.open(OUT, 'w', encoding='utf-8').write(
        json.dumps(data, ensure_ascii=False, indent=1))

    written = [n for n in nodes.values() if not n['stub']]
    stubs = [n for n in nodes.values() if n['stub']]
    with_refs = [n for n in written if n['refs']]
    print('data.json を書いた: ' + OUT)
    print('  ノード ' + str(len(nodes)) + '（書いた ' + str(len(written)) +
          ' ／ これから調べる ' + str(len(stubs)) + '）  線 ' + str(len(edges)))
    by_type = {}
    for n in written:
        by_type[n['type']] = by_type.get(n['type'], 0) + 1
    print('  内訳: ' + ' / '.join(k + ' ' + str(v) for k, v in sorted(by_type.items())))
    strong = [e for e in edges if e.get('weight') == '強']
    weak = [e for e in edges if e.get('weight') == '弱']
    if strong or weak:
        print('  線の強さ: 強 ' + str(len(strong)) + ' 本 ／ 弱 ' + str(len(weak)) + ' 本'
              '（残り ' + str(len(edges) - len(strong) - len(weak)) + ' 本は標準）')
    print('  引用元つき: ' + str(len(with_refs)) + ' / ' + str(len(written)) +
          '（残り ' + str(len(written) - len(with_refs)) + ' は記憶だけで書かれている）')
    if stubs:
        print('  これから調べる: ' + ', '.join(sorted(n['id'] for n in stubs)))
    if warnings:
        print('  --- 気になるところ ---')
        for w in warnings:
            print('  ⚠ ' + w)
    return 0


if __name__ == '__main__':
    sys.exit(main())
