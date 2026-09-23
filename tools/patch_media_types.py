# -*- coding: utf-8 -*-
"""⭐ 書物から「映像（動画）」と「遊戯（ゲーム）」を分ける（MEDIA-2026-09-23・燻太さんの指定）。

    python tools/patch_media_types.py          index.html と build_map.py に当てる（二度当てしない）

燻太さんの言葉（2026-09-23）＝「MINDの書物と動画を分けることは可能かい？」→ 動画とゲームをそれぞれの型に。

なぜ要るか＝動画3本（映01〜03）とゲーム2本（遊01・遊02）は、型が無かったので **書物で代用** していた
（[[mind-atlas-video-sources]]）。本と同じ形・同じ色・同じ島に混ざり、左パネルの「本でしぼる」にも本として並ぶ。

何が変わるか
  ① 型を2つ足す＝`映像`（角を落とした四角・マゼンタ）／`遊戯`（平行四辺形・オリーブ）。
     どちらも書物のとなり（ORDER で「どこから来たか」の並び）。凡例・島・型ごとの一覧は ORDER と
     TYPE_COLOR から自動で増える
  ② 左パネルの「本でしぼる」→「出典でしぼる」。本／動画／ゲームの3群に分けて並べる。
     ⚠⚠**しぼる仕組みそのものは変えない**（キーは出典の1つめ・複数の出典を持つノードはどれか1つ
     見えていれば残る＝本と本をつなぐ橋を切らない）。⚠型を分けただけで群に入れ忘れると、
     その出典しか持たないノードが**永久に消える**（on に入らないため）
  ③ 説明欄の「形は種類で分けてある」の一文に2つ足す
  ④ build_map.py の VALID_TYPES に2つ足す

⚠ノードの `type:` の書き換えは別（この道具はやらない）＝5ファイル。
⚠退避＝_backup/index.html.bak_YYYYMMDD_映像と遊戯のまえ
"""
import io, os, sys, shutil, datetime

if not (getattr(sys.stdout, 'encoding', '') or '').lower().startswith('utf'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'index.html')
BM = os.path.join(ROOT, 'tools', 'build_map.py')
MARK = 'MEDIA-2026-09-23'

s = io.open(SRC, encoding='utf-8', newline='').read()
NL = '\r\n' if '\r\n' in s else '\n'
if MARK in s:
    print('もう当ててある（' + MARK + '）'); sys.exit(0)

d = datetime.date.today().strftime('%Y%m%d')
os.makedirs(os.path.join(ROOT, '_backup'), exist_ok=True)
dst = os.path.join(ROOT, '_backup', 'index.html.bak_' + d + '_映像と遊戯のまえ')
if not os.path.exists(dst):
    shutil.copyfile(SRC, dst); print('退避: ' + dst)


def rep(text, old, new, what):
    old = old.replace('\n', NL); new = new.replace('\n', NL)
    if text.count(old) != 1:
        print('⚠ %s が %d 回見つかった（1回のはず）' % (what, text.count(old))); sys.exit(1)
    print('  ' + what)
    return text.replace(old, new)


# ① 形と色
s = rep(s, """  '予感':'star', '論文':'rectangle',
  '生物':'pentagon'   // 本に登場した動物・植物（2026-09-12）
};""",
        """  '予感':'star', '論文':'rectangle',
  '生物':'pentagon',   // 本に登場した動物・植物（2026-09-12）
  // """ + MARK + """ ⭐動画とゲーム（それまで書物で代用していた）。どちらも四角の仲間＝
  //   「どこから来たか」の側であることは書物と同じ・形で見分ける
  '映像':'cut-rectangle', '遊戯':'rhomboid'
};""", '形（TYPE_SHAPE）に 映像・遊戯')

s = rep(s, """  // 生物（2026-09-12）。からし色。どの型とも重ならない色にした
  '生物':'#b8962e'
};""",
        """  // 生物（2026-09-12）。からし色。どの型とも重ならない色にした
  '生物':'#b8962e',
  // """ + MARK + """ 映像（動画）と遊戯（ゲーム）。⭐空いていた色相に入れた＝
  //   映像＝赤紫（用語の紫 #7a6da8 と予感の桃 #a8577a のあいだ）／遊戯＝オリーブ（生物の
  //   からし #b8962e と人物の緑 #4f8a6b のあいだ）。⚠赤（対立の線 #b4483f）は使わない
  '映像':'#9c4a94', '遊戯':'#6f8f3c'
};""", '色（TYPE_COLOR）に 映像・遊戯')

# ② 並び
s = rep(s, """const ORDER = ['予感','書物','論文','人物','理論','症例','生物','実験','用語'];""",
        """// """ + MARK + """ 映像・遊戯は書物のとなり（本・動画・ゲーム＝「どこから来たか」の三つ）
const ORDER = ['予感','書物','映像','遊戯','論文','人物','理論','症例','生物','実験','用語'];""",
        '並び（ORDER）に 映像・遊戯')

# ③ 左パネル＝出典でしぼる（本／動画／ゲームの3群）
s = rep(s, """    <h3>本でしぼる</h3>""",
        """    <h3>出典でしぼる</h3>""", '見出しを「出典でしぼる」に')

s = rep(s, """  // 「本でしぼる」= 書物ノードごとのチェックボックス。キーは その本の 出典 の値
  const books = data.nodes.filter(n => n.type === '書物' && !n.stub)
                          .sort((a,b) => (a.sources[0]||'').localeCompare(b.sources[0]||''));
  const bbox = document.getElementById('books');
  bbox.innerHTML = '';
  books.forEach(b => {
    const key = b.sources[0] || b.id;
    const lab = document.createElement('label');
    lab.innerHTML = '<input type="checkbox" data-book="' + esc(key) + '" checked>' +
      '<span>' + esc(b.id) + '<br><span class="sub">' + esc(key) + '</span></span>';
    bbox.appendChild(lab);
    lab.querySelector('input').onchange = applyFilters;
  });
  if (!books.length) bbox.innerHTML = '<p class="sub">まだ書物のノードが無い。</p>';""",
        """  /* 「出典でしぼる」= 出典ノードごとのチェックボックス。キーは その出典の値（sources[0]）。
     """ + MARK + """ ⭐本・動画・ゲームの3群に分けて並べる。⚠⚠**しぼる仕組みは変えない**＝
       ここに並んだキーだけが applyFilters の `on` に入る。⚠新しい出典の型を足したら
       **必ずこの表にも足す**（足し忘れると、その出典しか持たないノードが永久に消える）。 */
  const SRC_GROUPS = [['書物','本'], ['映像','動画'], ['遊戯','ゲーム']];
  const bbox = document.getElementById('books');
  bbox.innerHTML = '';
  let nSrc = 0;
  SRC_GROUPS.forEach(g => {
    const t = g[0];
    const list = data.nodes.filter(n => n.type === t && !n.stub)
                           .sort((a,b) => (a.sources[0]||'').localeCompare(b.sources[0]||''));
    if (!list.length) return;
    nSrc += list.length;
    const head = document.createElement('p');
    head.className = 'srcgroup';
    head.innerHTML = '<span class="dot" style="background:' + (TYPE_COLOR[t]||'#888') + '"></span>' +
                     esc(g[1]) + ' <span class="sub">' + list.length + '</span>';
    bbox.appendChild(head);
    list.forEach(b => {
      const key = b.sources[0] || b.id;
      const lab = document.createElement('label');
      lab.innerHTML = '<input type="checkbox" data-book="' + esc(key) + '" checked>' +
        '<span>' + esc(b.id) + '<br><span class="sub">' + esc(key) + '</span></span>';
      bbox.appendChild(lab);
      lab.querySelector('input').onchange = applyFilters;
    });
  });
  if (!nSrc) bbox.innerHTML = '<p class="sub">まだ出典のノードが無い。</p>';""",
        '左パネルを3群に')

s = rep(s, """  .books .sub{color:var(--sub);font-size:10.5px}""",
        """  .books .sub{color:var(--sub);font-size:10.5px}
  /* """ + MARK + """ 出典の群の見出し（本／動画／ゲーム） */
  .books .srcgroup{margin:9px 0 3px;font-size:11px;letter-spacing:.04em;color:var(--sub);
    display:flex;align-items:center;gap:5px}
  .books .srcgroup:first-child{margin-top:0}
  .books .srcgroup .dot{width:8px;height:8px;border-radius:2px;display:inline-block}""",
        '群の見出しの見た目')

# ④ 説明欄の一文
s = rep(s, """      形は種類で分けてある。丸＝用語、角丸四角＝書物、六角＝人物、菱形＝理論、三角＝実験、八角＝症例、五角＝生物（本に登場した動物）、""",
        """      形は種類で分けてある。丸＝用語、角丸四角＝書物、<b>角を落とした四角＝映像（動画）</b>、<b>平行四辺形＝遊戯（ゲーム）</b>、六角＝人物、菱形＝理論、三角＝実験、八角＝症例、五角＝生物（本に登場した動物）、""",
        '説明欄の形の一覧')

io.open(SRC, 'w', encoding='utf-8', newline='').write(s)
print('index.html に当てた')

# ⑤ build_map.py
b = io.open(BM, encoding='utf-8', newline='').read()
BNL = '\r\n' if '\r\n' in b else '\n'
if MARK not in b:
    old = "VALID_TYPES = ['用語', '人物', '実験', '症例', '書物', '理論', '予感', '論文', '生物']"
    if b.count(old) != 1:
        print('⚠ build_map.py の VALID_TYPES が見つからない'); sys.exit(1)
    new = ("# " + MARK + " 映像＝動画（映NN）・遊戯＝ゲーム（遊NN）。それまで書物で代用していた。"
           + BNL + "#   ⚠index.html の TYPE_SHAPE・TYPE_COLOR・ORDER・SRC_GROUPS と必ず揃える" + BNL
           + "VALID_TYPES = ['用語', '人物', '実験', '症例', '書物', '理論', '予感', '論文', '生物', '映像', '遊戯']")
    b = b.replace(old, new)
    b = b.replace("type: 用語            # 用語 / 人物 / 実験 / 症例 / 書物 / 理論",
                  "type: 用語            # 用語 / 人物 / 実験 / 症例 / 書物 / 映像 / 遊戯 / 理論", 1)
    io.open(BM, 'w', encoding='utf-8', newline='').write(b)
    print('build_map.py に当てた')
print('⭐次＝ノードの type: を書き換える（5ファイル）→ python tools/build_map.py')
