# -*- coding: utf-8 -*-
"""⭐ PEEK-LIGHT（フォーカス中の1回押しで、つながりを光らせる）が効いているかをヘッドレスChromeで測る。

    python tools/check_peek.py                      MIND の index.html を、既定の用語で
    python tools/check_peek.py <index.html> 用語     ほかの地図の index.html を、その地図の用語で

測るもの＝①Uncaught ②「もう1手」の輪の中の1ノードを tap したとき、光ったノード＝そのノード＋見えている隣か
  ③光った線はぜんぶそのノードにつながっているか ④薄くなった数 ⑤同じノードをもう1回で消えるか
  ⑥背景1回で消えるか ⑦exitFocus で消えるか ⑧フォーカス外（初期表示）の tap では何も光らないか
"""
import io, os, re, sys, json, glob, subprocess, functools, threading
import http.server, socketserver

if not (getattr(sys.stdout, 'encoding', '') or '').lower().startswith('utf'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

args = sys.argv[1:]
if args and args[0].lower().endswith('.html'):
    SRC = os.path.abspath(args[0]); args = args[1:]
else:
    SRC = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'index.html')
ROOT = os.path.dirname(SRC)
TMP = os.path.join(ROOT, '_peek検査用.html')
NAME = args[0] if args else '島皮質'

INJECT = r"""
<div id="__chk">まだ</div>
<script>
window.__ERR = [];
window.addEventListener('error', e => window.__ERR.push(String(e.message)));
window.addEventListener('unhandledrejection', e => window.__ERR.push('rejection: ' + e.reason));
(function(){
  const NAME = __NAME__;
  const out = { err:[], steps:[] };
  const cnt = (what) => ({ what, peekN: cy.nodes('.peek').length, peekE: cy.edges('.peek').length,
                           dim: cy.elements('.peekdim').length, PEEK: (typeof PEEK !== 'undefined' ? PEEK : '?') });
  const done = () => { out.err = window.__ERR.slice();
    document.getElementById('__chk').textContent = 'CHKJ'+'SON::' + JSON.stringify(out) + '::END'; };
  const t0 = setInterval(() => {
    if (typeof cy === 'undefined' || !cy || !cy.nodes().length) return;
    clearInterval(t0);
    setTimeout(() => {
      try {
        // ⑧ フォーカス外で tap → 何も光らないこと
        const any = cy.nodes().not('.ringtick')[0];
        any.emit('tap'); out.steps.push(cnt('⑧初期表示で tap'));
        clearDim();
        const node = cy.nodes().filter(n => n.data('label') === NAME);
        if (!node.length){ out.steps.push({ what:'⚠見つからない: ' + NAME }); done(); return; }
        enterFocus(node, 2);
        const ring = cy.nodes(':visible').not('.ringtick').filter(n => n.id() !== node.id());
        // いちばん線の多い隣を選ぶ（光る数が読みやすい）
        let pick = null, best = -1;
        ring.forEach(n => { const k = n.connectedEdges().filter(':visible').length; if (k > best){ best = k; pick = n; } });
        out.steps.push({ what:'もう1手 ' + NAME, ring: ring.length, pick: pick.data('label'), pickEdges: best });
        // ② tap（1回）
        pick.emit('tap');
        const s = cnt('②③ ' + pick.data('label') + ' を tap');
        const eg = pick.connectedEdges().filter(':visible');
        const nb = eg.connectedNodes();
        s.expectN = nb.length; // pick 自身を含む
        s.expectE = eg.length;
        s.edgesOK = cy.edges('.peek').filter(e => e.source().id() !== pick.id() && e.target().id() !== pick.id()).length === 0;
        s.nodesOK = cy.nodes('.peek').filter(n => !nb.contains(n)).length === 0;
        s.visibleTotal = cy.elements(':visible').not('.ringtick').length;
        out.steps.push(s);
        // ⑤ もう1回で消える（400ms 内だとダブル扱いになるので直接呼ぶ）
        peekNode(pick); out.steps.push(cnt('⑤同じノードをもう1回'));
        // ⑥ 背景1回で消える
        peekNode(pick); cy.emit('tap'); out.steps.push(cnt('⑥背景を1回'));
        // ⑦ exitFocus で消える
        peekNode(pick); exitFocus(); out.steps.push(cnt('⑦exitFocus のあと'));
        out.steps.push({ what:'出たあと', visible: cy.nodes(':visible').length, dimLeft: cy.elements('.peekdim').length });
      } catch (e){ window.__ERR.push('inject: ' + e.message); }
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
        r = subprocess.run([chrome, '--headless', '--disable-gpu', '--no-sandbox',
                            '--window-size=1600,1000', '--virtual-time-budget=40000',
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
    for st in o['steps']: print('  ' + json.dumps(st, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    sys.exit(main())
