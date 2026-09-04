# -*- coding: utf-8 -*-
"""ノードの位置を1回だけ計算して `positions.js` に固める。

    python tools/build_positions.py
    python tools/build_positions.py --待つ 120     （秒。既定は90）
    python tools/build_positions.py --見るだけ     （書かずに数字だけ見る）

⭐ なぜ要るのか
⚠**力学レイアウト（fcose・randomize:true）を開くたびに回していた。**
   そのせいで**開くたびに配置が変わっていた**（2026-09-04の実測＝
   2回のあいだで最大 618px のずれ）。
⭐地図は「どこに何があるか」を覚えて使うものなので、これがいちばん効く。
   ついでに、開くときの計算がまるごと要らなくなる。
⭐この道具は、その計算を「手元で1回だけ」やる。ヘッドレスのChromeで
   index.html を開き、動きが止まるまで待って positions.js に書き出す。

⚠ 決めごと（どれも理由がある）
⭐**フィルタは全部入りで計算する。**本や型で絞っても配置が動かないように。
⭐**落ち着いたかは「動きが止まったか」で見る**（時間で切らない）。
⚠⚠**力学レイアウトを明示的に走らせる。**これをしないと positions.js が
   あるとき preset のまま止まり、**前回の座標をそのまま書き戻すだけ**になる
   （Plant-gene-atlas で実際に踏んだ罠）。
   ⭐歯止め＝「はじめの配置からの最大移動」を出す。50px 未満なら警告。
⚠⚠**file:// では動かない。**index.html は fetch('data.json') で読むので
   file:// だと CORS で弾かれて地図が起動しない。
   ⭐だから**その場に小さな http サーバを立てて**開く（公開時と同じ形）。

⚠ 流す順番
    python tools/build_map.py         ← ノードを足したら、まずこちら
    python tools/build_positions.py   ← ⭐そのあとに、これ
⚠**ノードを足しただけなら流し直さなくても地図は開ける。**座標の無いノードは
   線でつながっている相手のそばに置かれる（画面側でやる）。
   ⭐たくさん足したときや、配置が窮屈になってきたときに流し直す。
"""
import io, os, re, sys, json, time, glob, subprocess, argparse
import http.server, socketserver, threading, functools

if not (getattr(sys.stdout, 'encoding', '') or '').lower().startswith('utf'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'index.html')
OUT = os.path.join(ROOT, 'positions.js')
TMP = os.path.join(ROOT, '_位置計算用.html')

CHROME = [
    r'C:\Program Files\Google\Chrome\Application\chrome.exe',
    r'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe',
    os.path.expandvars(r'%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe'),
]

# ⭐計算用に差しこむスクリプト。
#   ⚠印は 'POSJ'+'SON::' と割って書く。まるごと書くと、この <script> の中身自身が
#     DOM に出てきて、取り出しの正規表現が先にそちらを拾ってしまう。
INJECT = """
<div id="__pos">まだ</div>
<script>
(function(){
  const T = Date.now();
  let prev = null, quiet = 0, done = false, before = null;
  const snap = () => cy.nodes().map(n => { const p = n.position(); return [p.x, p.y]; });
  const moved = (a, b) => {
    if (!a || !b || a.length !== b.length) return 1e9;
    let m = 0;
    for (let i = 0; i < a.length; i++){
      const dx = a[i][0] - b[i][0], dy = a[i][1] - b[i][1];
      const d = Math.sqrt(dx*dx + dy*dy);
      if (d > m) m = d;
    }
    return m;
  };
  const dump = (why) => {
    if (done) return; done = true;
    const o = {};
    cy.nodes().forEach(n => { const p = n.position();
      o[n.id()] = [Math.round(p.x*10)/10, Math.round(p.y*10)/10]; });
    document.getElementById('__pos').textContent =
      'POSJ'+'SON::' + JSON.stringify({ why:why, ms:Date.now()-T,
                                        n:cy.nodes().length,
                                        moved:Math.round(moved(before, snap())),
                                        pos:o }) + ':'+':END';
  };
  const iv0 = setInterval(() => {
    // ⚠index.html は `let cy` なので window.cy では取れない
    if (typeof cy === 'undefined' || !cy || !cy.nodes || !cy.nodes().length) return;
    clearInterval(iv0);
    // フィルタは全部入りにしてから計算する（絞っても配置が動かないように）
    document.querySelectorAll('#filters input, #books input')
            .forEach(i => { i.checked = true; });
    if (window.applyFilters) applyFilters();
    before = snap();
    // 力学レイアウトを明示的に走らせる（preset のまま止まると書き戻しになる）
    const sel = document.getElementById('layout');
    if (sel) sel.value = 'cose';
    cy.layout(layoutOpts('cose')).run();
    const iv = setInterval(() => {
      const now = snap();
      const d = moved(prev, now);
      prev = now;
      if (d < 0.5) quiet++; else quiet = 0;
      // 止まって見えるだけの瞬間があるので、3回続けて動かなければ落ち着いたとみなす
      if (quiet >= 3 && Date.now() - T > 3000){
        clearInterval(iv);
        setTimeout(() => dump('動きが止まった'), 800);
      }
    }, 300);
  }, 20);
  setTimeout(() => dump('時間ぎれ（打ち切り）'), __CAP__);
})();
</script>
</body>"""


def find_chrome():
    for p in CHROME:
        if os.path.exists(p):
            return p
    hit = glob.glob(r'C:\Program Files*\Google\Chrome\Application\chrome.exe')
    return hit[0] if hit else None


class Quiet(http.server.SimpleHTTPRequestHandler):
    """アクセスログを出さないだけの SimpleHTTPRequestHandler。"""
    def log_message(self, *a):
        pass


class Server(socketserver.TCPServer):
    allow_reuse_address = True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--待つ', dest='cap', type=int, default=90,
                    help='最長で何秒待つか（既定90）')
    ap.add_argument('--見るだけ', dest='dry', action='store_true')
    a = ap.parse_args()

    chrome = find_chrome()
    if not chrome:
        print('⚠Chrome が見つからない。'
              'tools/build_positions.py の CHROME に道を足すこと')
        return 1

    s = io.open(SRC, encoding='utf-8').read()
    if '</body>' not in s:
        print('⚠index.html に </body> が無い')
        return 1
    io.open(TMP, 'w', encoding='utf-8', newline='\n').write(
        s.replace('</body>', INJECT.replace('__CAP__', str(a.cap * 1000)), 1))

    # ⚠file:// だと fetch('data.json') が弾かれるので、小さな http サーバを立てる
    httpd = Server(('127.0.0.1', 0), functools.partial(Quiet, directory=ROOT))
    port = httpd.server_address[1]
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    url = 'http://127.0.0.1:%d/%s' % (port, os.path.basename(TMP))

    print('計算中… 最長 %d 秒待つ（ヘッドレスのChrome）' % a.cap)
    t0 = time.time()
    try:
        r = subprocess.run(
            [chrome, '--headless', '--disable-gpu', '--no-sandbox',
             '--virtual-time-budget=%d' % (a.cap * 1000 + 20000),
             '--dump-dom', url],
            capture_output=True, timeout=a.cap + 120)
        dom = r.stdout.decode('utf-8', 'replace')
    finally:
        try:
            httpd.shutdown()
        except Exception:
            pass
        if os.path.exists(TMP):
            os.remove(TMP)

    m = re.search(r'POSJSON::(.*?)::END', dom, re.S)
    if not m:
        print('⚠座標を取り出せなかった。'
              '--待つ を増やすか、index.html が開けるか確かめること')
        return 1
    d = json.loads(m.group(1))
    pos = d['pos']
    print('  %s ／ ノード %d ／ 画面の中で %.1f 秒'
          % (d['why'], d['n'], d['ms'] / 1000.0))
    print('  手元の待ち時間 %.1f 秒' % (time.time() - t0))
    mv = d.get('moved', -1)
    print('  はじめの配置からの最大移動 %d px' % mv)
    if 0 <= mv < 50:
        print('  ⚠⚠**ほとんど動いていない。力学レイアウトが走っていない疑いがある。**')
        print('    前回の positions.js をそのまま書き戻していないか確かめること')

    xs = [v[0] for v in pos.values()]
    ys = [v[1] for v in pos.values()]
    print('  広がり x %.0f〜%.0f ／ y %.0f〜%.0f'
          % (min(xs), max(xs), min(ys), max(ys)))
    if d['why'].startswith('時間ぎれ'):
        print('  ⚠**時間ぎれで打ち切った。**落ち着く前の配置かもしれない。'
              '--待つ を増やして流し直すとよい')

    if a.dry:
        print('（見るだけ。positions.js は書いていない）')
        return 0

    body = ',\n'.join('  "%s": [%s, %s]' % (k.replace('"', '\\"'), v[0], v[1])
                      for k, v in sorted(pos.items()))
    txt = ('// tools/build_positions.py が作る。手で直さない。\n'
           '// ⭐ノードの位置。これがあると、開くときに力学レイアウトを計算しない\n'
           '//   （⭐毎回まったく同じ配置になる）。無くても地図は動く。\n'
           '// ⚠ノードを足したら build_map.py のあとに流し直すとよい。\n'
           '//   座標の無いノードは、線でつながっている相手のそばに置かれる。\n'
           '// 作った日時: %s ／ ノード %d\n'
           'window.POS = {\n%s\n};\n'
           % (time.strftime('%Y-%m-%d %H:%M'), len(pos), body))
    io.open(OUT, 'w', encoding='utf-8', newline='\n').write(txt)
    print('positions.js を書いた（%.1f KB）' % (len(txt.encode('utf-8')) / 1024.0))
    print('⏳次: index.html を開いて確かめる')
    return 0


if __name__ == '__main__':
    sys.exit(main())
