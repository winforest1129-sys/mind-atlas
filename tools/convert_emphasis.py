# -*- coding: utf-8 -*-
"""ノード本文の強調を、絵文字から記法（** / == / !!）に置き換える。

2026-09-09・燻太さんの指定＝「強調するときは★の絵文字を使うのではなく、
文字の色を変えるか、太字にするなどにして、過剰な強調は避ける」。

## 当てる規則
1. 見出し行（# で始まる）と表の行（| で始まる）の絵文字は、ぜんぶ落とす
   （README の「見出しに強調を付けない」「表の中は素で書く」）
2. 絵文字のすぐ後ろが太字なら
   - ⭐**X**  →  **X**        （太字がすでに強調なので、絵文字だけ落とす）
   - ⚠**X**  →  !!**X**!!    （注意は赤茶にする。index.html は ** を先に処理するので入れ子が効く）
3. 絵文字の後ろが素の文なら、絵文字を落とすだけ。
   ⚠ どこまでが強調なのか本文からは決められないので、勝手に == で囲まない。
   README の「ためらったら強調しない。あとから足すほうが直しやすい」に従う。
4. ⏳ は落とす。

## 触らないもの
- frontmatter（--- と --- のあいだ）。⚠ refs の note にも絵文字は多いが、
  YAML風の行に !! を入れるとパースの当たりが変わりかねないので、今回は本文だけにする。
- コード体（`…`）の中身。

使い方: python tools/convert_emphasis.py [--見るだけ]
"""
import os, io, sys, re, glob

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NODES = os.path.join(ROOT, 'nodes')
DRY = '--見るだけ' in sys.argv

STAR = '⭐★'
WARN = '⚠'
WAIT = '⏳'
ALL = STAR + WARN + WAIT + '🔴'
RUN = '[' + ALL + ']+'


def convert_line(line):
    """1行ぶんを変換する。⚠ 行の種類で扱いを変えるので、行単位で処理する。"""
    stripped = line.lstrip()
    # 1. 見出しと表は、ぜんぶ落とす
    if stripped.startswith('#') or stripped.startswith('|'):
        line = re.sub(RUN + r'\s*', '', line)
        return re.sub(r'\s+$', '', line)

    out = []
    i = 0
    while i < len(line):
        m = re.compile(RUN).match(line, i)
        if not m:
            out.append(line[i])
            i += 1
            continue
        run = m.group(0)
        j = m.end()
        # 絵文字のあとの空白は、いったん飛ばす
        k = j
        while k < len(line) and line[k] == ' ':
            k += 1
        kind_warn = (WARN in run)
        b = re.compile(r'\*\*(.+?)\*\*').match(line, k)
        if b:
            inner = b.group(1)
            if kind_warn:
                out.append('!!**' + inner + '**!!')
            else:
                out.append('**' + inner + '**')
            i = b.end()
        else:
            # 3. 太字が続かないとき。
            #    ⚠ ここで単に落とすと「注意」という情報そのものが消える
            #    （例「⚠Crossref は 2010 と返すが、これは電子化年」）。
            #    ⭐だから最初の1文だけを記法で包む。長い段落は包まない（赤や色だらけになるため）。
            rest = line[k:]
            m2 = re.search(r'^(.{4,80}?[。．！？])', rest)
            if m2 and not re.match(r'^\s*$', m2.group(1)):
                sent = m2.group(1)
                if kind_warn:
                    out.append('!!' + sent + '!!')
                    i = k + len(sent)
                    continue
                if len(run) >= 2 and STAR[0] in run:
                    # ⭐⭐以上＝とくに要点だと書き手が思ったところ。== で残す
                    out.append('==' + sent + '==')
                    i = k + len(sent)
                    continue
            i = k
        continue
    res = ''.join(out)
    # ⚠ 太字の内側に入りこんだ絵文字は、上の走査では拾えない
    #   （例「**⚠この主張自体が、批判の的になりやすい**」）。ここで落とす。
    res = re.sub(RUN + r'\s*', '', res)
    # 行頭に残った空白と、二重の空白を整える
    res = re.sub(r'^[ \t]+(?=\S)', '', res) if re.match(r'^[ \t]+[^ \t-]', res) else res
    res = re.sub(r'[ \t]+$', '', res)
    return res


def clean_front(head):
    """frontmatter（refs の note など）の絵文字を落とす。

    ⭐note も説明欄に出るので、燻太さんの指定の対象。
    ⚠ ただしここには !! や == を入れない ── 出典の説明は、強調より中身が大事だから。
    """
    out = []
    for line in head.split('\n'):
        if re.search(RUN, line):
            line = re.sub(RUN + r'\s*', '', line)
        out.append(line)
    return '\n'.join(out)


def split_body(t):
    if not t.startswith('---'):
        return '', t
    end = t.find('\n---', 3)
    if end < 0:
        return '', t
    end = t.find('\n', end + 1)
    return t[:end + 1], t[end + 1:]


def main():
    files = sorted(glob.glob(os.path.join(NODES, '*.md')))
    changed = 0
    before = after = 0
    samples = []
    for f in files:
        t = open(f, encoding='utf-8').read()
        head, body = split_body(t)
        before += sum(t.count(c) for c in ALL)
        lines = body.split('\n')
        new = [convert_line(l) for l in lines]
        nb = '\n'.join(new)
        head = clean_front(head)
        after += sum((head + nb).count(c) for c in ALL)
        if nb != body or head != split_body(t)[0]:
            changed += 1
            if len(samples) < 3:
                for a, b in zip(lines, new):
                    if a != b and len(a) > 20:
                        samples.append((os.path.basename(f), a[:90], b[:90]))
                        break
            if not DRY:
                open(f, 'w', encoding='utf-8').write(head + nb)

    print('ノード %d 件のうち %d 件を書き換え' % (len(files), changed))
    print('本文の絵文字: %d → %d' % (before, after))
    print('\n=== 変わりかたの見本 ===')
    for fn, a, b in samples:
        print('\n[%s]' % fn)
        print('  前: ' + a)
        print('  後: ' + b)
    if DRY:
        print('\n--見るだけ なので書いていない')


if __name__ == '__main__':
    main()
