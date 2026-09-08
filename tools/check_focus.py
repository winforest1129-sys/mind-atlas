# -*- coding: utf-8 -*-
"""⭐フォーカスが本当に効いているかを、ヘッドレスのChromeで測る（2026-09-09）。

    python tools/check_focus.py            既定の3つで測る
    python tools/check_focus.py 島皮質 共感  用語を指定する

⚠**JSを触ったら括弧を数えるだけでは足りない。**⭐実際に走らせて数を見る。
⭐測るもの＝①Uncaughtエラー ②入る前／1手／もう1手／出たあとのノード数と線の数
  ③⭐**線の無いノード**（0でなければ、辿りかたが壊れている）
  ④⭐**もどりのずれ**（0pxでなければ、座標の控えが壊れている）⑤種類の札の数
"""
import io, os, re, sys, json, glob, subprocess, functools, threading
import http.server, socketserver

if not (getattr(sys.stdout, 'encoding', '') or '').lower().startswith('utf'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'index.html')
TMP = os.path.join(ROOT, '_フォーカス検査用.html')

INJECT = r"""
<div id="__chk">まだ</div>
<script>
window.__ERR = [];
window.addEventListener('error', e => window.__ERR.push(String(e.message)));
window.addEventListener('unhandledrejection', e => window.__ERR.push('rejection: ' + e.reason));
(function(){
  const NAMES = __NAMES__;
  const out = { err:[], steps:[] };
  const snap = () => {
    const ns = cy.nodes(':visible').not('.ringtick');
    const es = cy.edges(':visible');
    const lonely = ns.filter(n => n.connectedEdges().filter(e => e.visible()).length === 0);
    return { n:ns.length, e:es.length, lonely:lonely.length,
             tick:cy.nodes('.ringtick').length, zoom:Math.round(cy.zoom()*1000)/1000 };
  };
  const pos0 = {};
  const done = () => {
    out.err = window.__ERR.slice();
    document.getElementById('__chk').textContent = 'CHKJ'+'SON::' + JSON.stringify(out) + '::END';
  };
  const t0 = setInterval(() => {
    // ⚠⚠`let cy` は window に乗らないので `window.cy` で見てはいけない
    //   （LAND の build_positions.py で踏んだ罠。`typeof` で見る）
    if (typeof cy === 'undefined' || !cy || !cy.nodes().length) return;
    clearInterval(t0);
    setTimeout(() => {
      cy.nodes().forEach(n => { const p = n.position(); pos0[n.id()] = [p.x, p.y]; });
      out.steps.push(Object.assign({ what:'入る前' }, snap()));
      NAMES.forEach(nm => {
        const node = cy.nodes().filter(n => n.data('label') === nm);
        if (!node.length){ out.steps.push({ what:'⚠見つからない: ' + nm }); return; }
        enterFocus(node, 1);
        out.steps.push(Object.assign({ what:'1手 ' + nm }, snap()));
        enterFocus(node, 2);
        out.steps.push(Object.assign({ what:'もう1手 ' + nm }, snap()));
        exitFocus();
        let drift = 0;
        cy.nodes().forEach(n => {
          const a = pos0[n.id()]; if (!a) return;
          const p = n.position();
          drift = Math.max(drift, Math.hypot(p.x-a[0], p.y-a[1]));
        });
        const s = Object.assign({ what:'出たあと ' + nm }, snap());
        s.drift = Math.round(drift*10)/10;
        out.steps.push(s);
      });
      // ⭐2つの共通の隣も試す
      if (NAMES.length >= 2){
        const a = cy.nodes().filter(n => n.data('label') === NAMES[0]);
        const b = cy.nodes().filter(n => n.data('label') === NAMES[1]);
        if (a.length && b.length){
          enterFocusPair(a[0], b[0]);
          out.steps.push(Object.assign({ what:'共通 ' + NAMES[0] + '×' + NAMES[1] }, snap()));
          exitFocus();
        }
      }
      done();
    }, 900);
  }, 60);
  setTimeout(done, 25000);
})();
</script>
</body>"""


def find_chrome():
    for p in [r'C:\Program Files\Google\Chrome\Application\chrome.exe',
              r'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe',
              os.path.expandvars(r'%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe')]:
        if os.path.exists(p):
            return p
    hit = glob.glob(r'C:\Program Files*\Google\Chrome\Application\chrome.exe')
    return hit[0] if hit else None


class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass


class Server(socketserver.TCPServer):
    allow_reuse_address = True


def main():
    names = sys.argv[1:] or ['島皮質', '共感', 'サリエンス・ネットワーク']
    chrome = find_chrome()
    if not chrome:
        print('⚠Chrome が見つからない')
        return 1
    s = io.open(SRC, encoding='utf-8').read()
    io.open(TMP, 'w', encoding='utf-8', newline='\n').write(
        s.replace('</body>', INJECT.replace('__NAMES__',
                  json.dumps(names, ensure_ascii=False)), 1))
    httpd = Server(('127.0.0.1', 0), functools.partial(Quiet, directory=ROOT))
    port = httpd.server_address[1]
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    url = 'http://127.0.0.1:%d/%s' % (port, os.path.basename(TMP))
    try:
        r = subprocess.run(
            [chrome, '--headless', '--disable-gpu', '--no-sandbox',
             '--window-size=1600,1000', '--virtual-time-budget=40000',
             '--dump-dom', url], capture_output=True, timeout=180)
        dom = r.stdout.decode('utf-8', 'replace')
    finally:
        try: httpd.shutdown()
        except Exception: pass
        if os.path.exists(TMP): os.remove(TMP)
    m = re.search(r'CHKJSON::(.*?)::END', dom, re.S)
    if not m:
        print('⚠結果が取れなかった（地図が起動していない可能性）')
        return 1
    o = json.loads(m.group(1))
    print('⚠Uncaught エラー: %d 件' % len(o['err']))
    for e in o['err']:
        print('   ' + e)
    print('')
    print('%-30s %7s %7s %10s %6s %7s %7s' %
          ('', 'ノード', '線', '線の無い', '札', 'zoom', 'ずれ'))
    for st in o['steps']:
        if 'n' not in st:
            print(st['what'])
            continue
        print('%-30s %7d %7d %10d %6d %7.3f %7s' %
              (st['what'], st['n'], st['e'], st['lonely'], st['tick'], st['zoom'],
               (str(st['drift']) + 'px') if 'drift' in st else '-'))
    return 0


if __name__ == '__main__':
    sys.exit(main())
