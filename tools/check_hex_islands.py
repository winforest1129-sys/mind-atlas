# -*- coding: utf-8 -*-
"""⭐ 初期表示「型ごとの六角形の島」（HEXISLE-MIND-2026-09-17）が効いているかをヘッドレスChromeで測る。

    python tools/check_hex_islands.py                 数字だけ
    python tools/check_hex_islands.py --絵 out.png    初期表示の絵も撮る（1500×850）

測るもの＝①Uncaught ②島の数・札の数・島ごとの数と幅高さ ③島どうしの重なり・最近接の距離
  ④全体で見えている線＝0 か ⑤検索で光らせると線が出て・clearDim で伏せ直るか
  ⑥フォーカスに入ると線が出て・出ると伏せ直り・座標が元どおりか ⑦zoom
"""
import io, os, re, sys, json, glob, subprocess, functools, threading
import http.server, socketserver

if not (getattr(sys.stdout, 'encoding', '') or '').lower().startswith('utf'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

args = sys.argv[1:]
PNG = None
if '--絵' in args:
    PNG = os.path.abspath(args[args.index('--絵') + 1])
SRC = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'index.html')
ROOT = os.path.dirname(SRC)
TMP = os.path.join(ROOT, '_島検査用.html')
NAME = '島皮質'

INJECT = r"""
<div id="__chk">まだ</div>
<script>
window.__ERR = [];
window.addEventListener('error', e => window.__ERR.push(String(e.message)));
window.addEventListener('unhandledrejection', e => window.__ERR.push('rejection: ' + e.reason));
(function(){
  const NAME = __NAME__;
  const out = { err:[], steps:[] };
  const done = () => { out.err = window.__ERR.slice();
    document.getElementById('__chk').textContent = 'CHKJ'+'SON::' + JSON.stringify(out) + '::END'; };
  const t0 = setInterval(() => {
    if (typeof cy === 'undefined' || !cy || !cy.nodes().length) return;
    clearInterval(t0);
    setTimeout(() => {
      try {
        const real = cy.nodes().not('.isletick').not('.ringtick');
        out.mode = ISLE_MODE; out.layoutSel = document.getElementById('layout').value;
        out.nodes = real.length; out.labels = cy.nodes('.isletick').length;
        out.visibleEdges0 = cy.edges(':visible').length;
        out.zoom0 = cy.zoom();
        // 島ごと
        out.isles = ISLES.map(c => {
          const bb = real.filter(n => (n.data('stub') ? 'これから調べる' : n.data('type')) === c.type).boundingBox({ includeLabels:false });
          return { type:c.type, n:c.n, x:Math.round(c.x), y:Math.round(c.y), w:Math.round(bb.w), h:Math.round(bb.h),
                   x1:Math.round(bb.x1), x2:Math.round(bb.x2), y1:Math.round(bb.y1), y2:Math.round(bb.y2) };
        });
        // 重なり
        const ov = [];
        for (let i = 0; i < out.isles.length; i++) for (let j = i + 1; j < out.isles.length; j++){
          const a = out.isles[i], b = out.isles[j];
          if (a.x1 < b.x2 && b.x1 < a.x2 && a.y1 < b.y2 && b.y1 < a.y2) ov.push(a.type + '×' + b.type);
        }
        out.overlaps = ov;
        const all = real.boundingBox({ includeLabels:false });
        out.extent = { w:Math.round(all.w), h:Math.round(all.h) };
        // 最近接
        const ps = real.map(n => n.position()); let mn = 1e9;
        for (let i = 0; i < ps.length; i++){ const p = ps[i];
          for (let j = i + 1; j < ps.length; j++){ const q = ps[j];
            const d = Math.hypot(p.x - q.x, p.y - q.y); if (d < mn) mn = d; } }
        out.nearest = Math.round(mn);
        out.labelFont = cy.nodes('.isletick').length ? cy.nodes('.isletick')[0].style('font-size') : null;
        // ⑤ 検索
        const pos0 = {}; real.forEach(n => { const p = n.position(); pos0[n.id()] = [p.x, p.y]; });
        search(NAME);
        out.searchEdges = cy.edges(':visible').length;
        out.searchDimLabels = cy.nodes('.isletick.dim').length;
        clearDim();
        out.afterClearEdges = cy.edges(':visible').length;
        // ⑥ フォーカス
        const node = cy.nodes().filter(n => n.data('label') === NAME);
        enterFocus(node, 1);
        out.focusVisibleNodes = cy.nodes(':visible').not('.ringtick').not('.isletick').length;
        out.focusVisibleEdges = cy.edges(':visible').length;
        out.focusLabelsVisible = cy.nodes('.isletick:visible').length;
        exitFocus();
        out.exitEdges = cy.edges(':visible').length;
        out.exitLabels = cy.nodes('.isletick:visible').length;
        let moved = 0; real.forEach(n => { const p = n.position(), q = pos0[n.id()];
          if (Math.hypot(p.x - q[0], p.y - q[1]) > 0.5) moved++; });
        out.movedAfterExit = moved;
        out.modeAfter = ISLE_MODE;
      } catch (e){ window.__ERR.push('inject: ' + e.message + ' @ ' + (e.stack || '').split('\n')[1]); }
      done();
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
    def log_message(self, *a):
        pass


class Server(socketserver.TCPServer):
    allow_reuse_address = True


def main():
    chrome = find_chrome()
    if not chrome:
        print('⚠Chrome が見つからない'); return 1
    s = io.open(SRC, encoding='utf-8').read()
    io.open(TMP, 'w', encoding='utf-8', newline='\n').write(
        s.replace('</body>', INJECT.replace('__NAME__', json.dumps(NAME, ensure_ascii=False)), 1))
    httpd = Server(('127.0.0.1', 0), functools.partial(Quiet, directory=ROOT))
    port = httpd.server_address[1]
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    url = 'http://127.0.0.1:%d/%s' % (port, os.path.basename(TMP))
    try:
        if PNG:
            subprocess.run([chrome, '--headless', '--disable-gpu', '--no-sandbox', '--hide-scrollbars',
                            '--window-size=1500,850', '--virtual-time-budget=8000',
                            '--screenshot=' + PNG, 'http://127.0.0.1:%d/index.html' % port],
                           capture_output=True, timeout=180)
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
        print('⚠結果が取れなかった（地図が起動していない可能性）'); return 1
    o = json.loads(m.group(1))
    print('対象: %s' % SRC)
    print('⚠Uncaught エラー: %d 件' % len(o['err']))
    for e in o['err']: print('   ' + e)
    for k, v in o.items():
        if k in ('err', 'isles', 'steps'): continue
        print('  %s = %s' % (k, json.dumps(v, ensure_ascii=False)))
    for c in o.get('isles', []):
        print('  島 %-10s %4d  中心(%6d,%6d)  %5d×%-5d' % (c['type'], c['n'], c['x'], c['y'], c['w'], c['h']))
    if PNG: print('絵: ' + PNG)
    return 0


if __name__ == '__main__':
    sys.exit(main())
