# -*- coding: utf-8 -*-
"""MIND の初期配置（六角の島）で、名前の札どうしの重なりを数え、島を拡大した絵を撮る（2026-11-03・大河・検討用）。
index.html は書きかえない。一時ファイル _札検査用.html を作って、終わったら消す。

  python probe.py <変種> [--絵 out.png] [--島 書物,映像,遊戯]
  変種: base / wrap（日本語を任意の位置で折る） / JS の式を ; で並べたもの（style を足す実験用）
"""
import io, os, re, sys, json, glob, subprocess, functools, threading
import http.server, socketserver

ROOT = r'C:\Users\s65vu\OneDrive\デスクトップ\私用\心理学\mind-atlas'
SRC = os.path.join(ROOT, 'index.html')
TMP = os.path.join(ROOT, '_札検査用.html')

args = sys.argv[1:]
VAR = args[0] if args else 'base'
PNG = os.path.abspath(args[args.index('--絵') + 1]) if '--絵' in args else None
FOCUS_ISLES = (args[args.index('--島') + 1] if '--島' in args else '書物,映像,遊戯').split(',')

VARIANTS = {
    'base': '',
    'wrap': "cy.style().selector('node').style({'text-overflow-wrap':'anywhere'}).update();",
}
VAR_JS = VARIANTS.get(VAR, VAR)

INJECT = r"""
<div id="__chk">まだ</div>
<script>
window.__ERR = [];
window.addEventListener('error', e => window.__ERR.push(String(e.message)));
(function(){
  const FOCUS_ISLES = __ISLES__;
  const out = { err:[] };
  const done = () => { out.err = window.__ERR.slice();
    document.getElementById('__chk').textContent = 'CHKJ'+'SON::' + JSON.stringify(out) + '::END'; };
  const t0 = setInterval(() => {
    if (typeof cy === 'undefined' || !cy || !cy.nodes().length || !ISLE_MODE) return;
    clearInterval(t0);
    setTimeout(() => {
      try {
        __VARJS__
        if (window.__AFTER) window.__AFTER();
        cy.zoom(1);
      } catch (e){ window.__ERR.push('var: ' + e.message); }
      setTimeout(() => { try {
        const real = cy.nodes().not('.isletick').not('.ringtick');
        const typeOf = n => n.data('stub') ? 'これから調べる' : n.data('type');
        cy.zoom(1);
        const per = {}; let total = 0;
        const groups = {};
        real.forEach(n => { (groups[typeOf(n)] = groups[typeOf(n)] || []).push(n); });
        Object.keys(groups).forEach(t => {
          const arr = groups[t].map(n => ({ n:n, b:n.boundingBox({ includeNodes:true, includeLabels:true, includeOverlays:false }) }));
          let c = 0; const ex = [];
          for (let i = 0; i < arr.length; i++) for (let j = i + 1; j < arr.length; j++){
            const a = arr[i].b, b = arr[j].b;
            const ox = Math.min(a.x2, b.x2) - Math.max(a.x1, b.x1), oy = Math.min(a.y2, b.y2) - Math.max(a.y1, b.y1);
            if (ox > 2 && oy > 2){ c++; if (ex.length < 3) ex.push(arr[i].n.data('label') + ' × ' + arr[j].n.data('label')); }
          }
          const hit = new Set();
          per[t] = { n:arr.length, pairs:c, ex:ex,
                     maxW:Math.round(Math.max.apply(null, arr.map(x => x.b.w))),
                     maxH:Math.round(Math.max.apply(null, arr.map(x => x.b.h))) };
          total += c;
        });
        out.per = per; out.total = total;
        const bb = real.boundingBox({ includeLabels:false }); out.extent = [Math.round(bb.w), Math.round(bb.h)];
        // 絵のために島を拡大
        const sel = real.filter(n => FOCUS_ISLES.indexOf(typeOf(n)) >= 0);
        if (sel.length){ cy.zoom(__Z__); cy.center(sel); }
        if (window.__POST) window.__POST();
        out.zoomShot = cy.zoom();
      } catch (e){ window.__ERR.push('inject: ' + e.message); }
      done();
      }, 800);
    }, 1500);
  }, 60);
  setTimeout(done, 30000);
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
    def log_message(self, *a): pass


class Server(socketserver.TCPServer):
    allow_reuse_address = True


def main():
    chrome = find_chrome()
    s = io.open(SRC, encoding='utf-8').read()
    Z = args[args.index('--zoom') + 1] if '--zoom' in args else '1.1'
    inj = INJECT.replace('__Z__', Z).replace('__ISLES__', json.dumps(FOCUS_ISLES, ensure_ascii=False)).replace('__VARJS__', VAR_JS)
    io.open(TMP, 'w', encoding='utf-8', newline='\n').write(s.replace('</body>', inj, 1))
    httpd = Server(('127.0.0.1', 0), functools.partial(Quiet, directory=ROOT))
    port = httpd.server_address[1]
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    url = 'http://127.0.0.1:%d/%s' % (port, os.path.basename(TMP))
    try:
        if PNG:
            subprocess.run([chrome, '--headless', '--disable-gpu', '--no-sandbox', '--hide-scrollbars',
                            '--window-size=1500,850', '--virtual-time-budget=12000',
                            '--screenshot=' + PNG, url], capture_output=True, timeout=180)
        r = subprocess.run([chrome, '--headless', '--disable-gpu', '--no-sandbox',
                            '--window-size=1500,850', '--virtual-time-budget=40000',
                            '--dump-dom', url], capture_output=True, timeout=180)
        dom = r.stdout.decode('utf-8', 'replace')
    finally:
        try: httpd.shutdown()
        except Exception: pass
        if os.path.exists(TMP): os.remove(TMP)
    m = re.search(r'CHKJSON::(.*?)::END', dom, re.S)
    if not m:
        print('結果が取れなかった'); return 1
    o = json.loads(m.group(1))
    print('変種', VAR, ' Uncaught', len(o['err']), o['err'][:3])
    print('札の重なり（同じ島の中の組）合計', o.get('total'), ' 広がり', o.get('extent'))
    for t, v in sorted(o.get('per', {}).items(), key=lambda kv: -kv[1]['pairs']):
        print('  %-8s %4d個  重なり%4d組  札の最大 %d×%d  例 %s' % (t, v['n'], v['pairs'], v['maxW'], v['maxH'], ' / '.join(v['ex'][:2])))
    if PNG: print('絵', PNG)
    return 0


if __name__ == '__main__':
    sys.exit(main())
