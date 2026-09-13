# -*- coding: utf-8 -*-
"""⭐ スマホ幅（400px）で、フォーカス中の1回押しが2段階になっているかをヘッドレスChromeで測る（2026-09-13 夜）。

    python tools/check_peek_phone.py                      MIND の index.html を、既定の用語で
    python tools/check_peek_phone.py <index.html> 用語     ほかの地図の index.html を、その地図の用語で
    CHK_W=900 python tools/check_peek_phone.py           幅を変えて（タブレット縦＝900）
    CHK_W=900 CHK_SIDEW=420 python tools/check_peek_phone.py   前回の説明欄の幅を覚えている状態で（全幅になるか）

測るもの＝①Uncaught ②1回目の tap＝光る・シートは開かない ③2回目（450ms後）＝シートが開く・光はそのまま
  ④シートを閉じて、速い2回押し（ダブル）でもフォーカスの中心が変わらない（説明が開くだけ）
  ⑤背景1回で光が消える ⑥フォーカス外の1回押しは今までどおりシートが開く ⑦もう1手・一歩ではシートが開かない（開いていれば閉じる）
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
TMP = os.path.join(ROOT, '_peek検査用_phone.html')
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
  const sideOpen = () => document.getElementById('side').classList.contains('open');
  const cnt = (what) => ({ what, peekN: cy.nodes('.peek').length, peekE: cy.edges('.peek').length,
                           dim: cy.elements('.peekdim').length, PEEK: (typeof PEEK !== 'undefined' ? PEEK : '?'),
                           sideOpen: sideOpen(), focus: FOCUS });
  const done = () => { out.err = window.__ERR.slice();
    document.getElementById('__chk').textContent = 'CHKJ'+'SON::' + JSON.stringify(out) + '::END'; };
  const wait = ms => new Promise(r => setTimeout(r, ms));
  const t0 = setInterval(() => {
    if (typeof cy === 'undefined' || !cy || !cy.nodes().length) return;
    clearInterval(t0);
    setTimeout(async () => {
      try {
        const sd = document.getElementById('side');
        out.steps.push({ what:'幅', isPhone: isPhone(), w: window.innerWidth,
          sideW: Math.round(sd.getBoundingClientRect().width), sideInline: sd.style.width || '(なし)',
          savedW: localStorage.getItem('mindatlas.sideW') });
        // ⑥ フォーカス外の1回押し＝シートが開く（今までどおり）
        const any = cy.nodes().not('.ringtick')[0];
        any.emit('tap'); out.steps.push(cnt('⑥フォーカス外で tap'));
        closeSheets(); clearDim();
        const node = cy.nodes().filter(n => n.data('label') === NAME);
        if (!node.length){ out.steps.push({ what:'⚠見つからない: ' + NAME }); done(); return; }
        enterFocus(node, 2); closeSheets();
        const ring = cy.nodes(':visible').not('.ringtick').filter(n => n.id() !== node.id());
        let pick = null, best = -1;
        ring.forEach(n => { const k = n.connectedEdges().filter(':visible').length; if (k > best){ best = k; pick = n; } });
        out.steps.push({ what:'もう1手 ' + NAME, ring: ring.length, pick: pick.data('label'), pickEdges: best, sideOpen: sideOpen() });
        const focusBefore = cy.nodes(':visible').not('.ringtick').length;
        // ② 1回目＝光る・シートは開かない
        pick.emit('tap');
        const s = cnt('②1回目の tap'); s.expectN = pick.connectedEdges().filter(':visible').connectedNodes().length; out.steps.push(s);
        // ③ 2回目（450ms あける）＝シートが開く・光はそのまま
        await wait(450);
        pick.emit('tap'); out.steps.push(cnt('③2回目の tap（450ms後）'));
        // ④ シートを閉じ、速い2回押しでもフォーカスの中心が変わらない
        closeSheets(); await wait(450);
        pick.emit('tap'); pick.emit('tap');
        const s4 = cnt('④速い2回押し'); s4.visibleSame = (cy.nodes(':visible').not('.ringtick').length === focusBefore); out.steps.push(s4);
        // ⑤ 背景1回で消える
        closeSheets(); await wait(450);
        cy.emit('tap'); out.steps.push(cnt('⑤背景を1回'));
        // ⑦ もう1手・一歩・フォーカス欄＝シートが開かない（開いていたら閉じる）
        openSheet('side');
        document.getElementById('focusWider').click(); out.steps.push(cnt('⑦もう1手（開いていたシートから）'));
        enterFocus(pick, 1);   // 履歴を2つにする（一歩が効くように）
        openSheet('side');
        document.getElementById('focusBack').click();
        const s7 = cnt('⑦一歩（' + pick.data('label') + ' から）'); s7.backTo = FOCUS === node.id(); out.steps.push(s7);
        exitFocus();
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
    s = s.replace('</body>', INJECT.replace('__NAME__', json.dumps(NAME, ensure_ascii=False)), 1)
    # CHK_SIDEW=420 で「前回の幅」を覚えている状態を仕込む（タブレット縦で半分幅になった件の検査）
    if os.environ.get('CHK_SIDEW'):
        s = s.replace('<head>', '<head><script>try{localStorage.setItem("mindatlas.sideW",%s)}catch(e){}</script>'
                      % json.dumps(os.environ['CHK_SIDEW']), 1)
    io.open(TMP, 'w', encoding='utf-8', newline='\n').write(s)
    httpd = Server(('127.0.0.1', 0), functools.partial(Quiet, directory=ROOT))
    port = httpd.server_address[1]
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    url = 'http://127.0.0.1:%d/%s' % (port, os.path.basename(TMP))
    try:
        r = subprocess.run([chrome, '--headless', '--disable-gpu', '--no-sandbox',
                            '--window-size=%s,900' % os.environ.get('CHK_W', '400'), '--virtual-time-budget=40000',
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
