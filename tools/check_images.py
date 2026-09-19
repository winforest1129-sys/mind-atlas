# -*- coding: utf-8 -*-
"""⭐ 説明欄の絵（IMG-MIND-2026-09-19）が出るかをヘッドレスChromeで測る＋絵を撮る。

    python tools/check_images.py [ノード名] [--絵 out.png]      省略時は「追う人と逃げる人」

測るもの＝①Uncaught ②そのノードに <figure class="fig"> があるか ③img が読めたか（naturalWidth>0）
  ④figcaption の文字 ⑤本文の中の他の記法（太字・==・[[）が壊れていないか
⚠file:// で開く（check_local.py と同じ）。
"""
import io, os, re, sys, json, glob, subprocess

if not (getattr(sys.stdout, 'encoding', '') or '').lower().startswith('utf'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

args = sys.argv[1:]
PNG = os.path.abspath(args[args.index('--絵') + 1]) if '--絵' in args else None
names = [a for i, a in enumerate(args) if a != '--絵' and (i == 0 or args[i-1] != '--絵')]
NODE = names[0] if names else '追う人と逃げる人'
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'index.html')
TMP = os.path.join(ROOT, '_絵の検査用.html')

INJECT = r"""
<div id="__chk">まだ</div>
<script>
window.__ERR = [];
window.addEventListener('error', e => window.__ERR.push(String(e.message) + ' @' + (e.filename||'').split('/').pop() + ':' + e.lineno));
(function(){
  const out = { err:[] };
  const done = () => { out.err = window.__ERR.slice();
    document.getElementById('__chk').textContent = 'CHKJ'+'SON::' + JSON.stringify(out) + '::END'; };
  const t0 = setInterval(() => {
    if (typeof cy === 'undefined' || !cy || !cy.nodes().length) return;
    clearInterval(t0);
    setTimeout(() => {
      try {
        const n = cy.nodes().filter(x => x.data('label') === __NODE__);
        out.found = n.length > 0;
        if (n.length){ show(n[0].data('node')); }
        const body = document.getElementById('sidebody') || document.getElementById('side');
        const fig = body.querySelector('figure.fig');
        out.fig = !!fig;
        const img = fig ? fig.querySelector('img') : null;
        out.imgSrc = img ? img.getAttribute('src') : null;
        out.caption = fig && fig.querySelector('figcaption') ? fig.querySelector('figcaption').textContent : null;
        out.bold = body.querySelectorAll('b').length; out.key = body.querySelectorAll('.key').length;
        out.wiki = body.querySelectorAll('a.wiki').length;
        out.leftover = /FIG\d+/.test(body.innerHTML) || body.innerHTML.indexOf('\u0000') >= 0;
        const fin = () => { out.imgLoaded = img ? (img.naturalWidth > 0) : null; out.imgW = img ? img.naturalWidth : 0;
                            if (fig) fig.scrollIntoView(); done(); };
        if (img && !img.complete){ img.addEventListener('load', fin); img.addEventListener('error', fin); setTimeout(fin, 8000); }
        else fin();
      } catch (e){ out.exc = String(e); done(); }
    }, 1500);
  }, 100);
})();
</script>
</body>"""

def find_chrome():
    for p in [r'C:\Program Files\Google\Chrome\Application\chrome.exe',
              r'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe',
              os.path.expandvars(r'%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe')]:
        if os.path.exists(p): return p
    hit = glob.glob(r'C:\Program Files*\Google\Chrome\Application\chrome.exe')
    return hit[0] if hit else None

def main():
    chrome = find_chrome()
    if not chrome:
        print('⚠Chrome が見つからない'); return 1
    s = io.open(SRC, encoding='utf-8').read()
    inj = INJECT.replace('__NODE__', json.dumps(NODE, ensure_ascii=False))
    io.open(TMP, 'w', encoding='utf-8', newline='\n').write(s.replace('</body>', inj, 1))
    url = 'file:///' + TMP.replace('\\', '/')
    try:
        base = [chrome, '--headless', '--disable-gpu', '--no-sandbox', '--allow-file-access-from-files',
                '--window-size=1500,850', '--virtual-time-budget=30000']
        if PNG:
            subprocess.run(base + ['--hide-scrollbars', '--screenshot=' + PNG, url], capture_output=True, timeout=180)
        r = subprocess.run(base + ['--dump-dom', url], capture_output=True, timeout=180)
        dom = r.stdout.decode('utf-8', 'replace')
    finally:
        if os.path.exists(TMP): os.remove(TMP)
    m = re.search(r'CHKJSON::(.*?)::END', dom, re.S)
    if not m:
        print('⚠検査の結果が取れなかった'); return 1
    out = json.loads(m.group(1).replace('&quot;', '"').replace('&amp;', '&'))
    print('対象:', NODE)
    print('⚠Uncaught エラー:', len(out.get('err', [])), '件', out.get('err') or '')
    for k in ('found', 'fig', 'imgSrc', 'imgLoaded', 'imgW', 'caption', 'bold', 'key', 'wiki', 'leftover', 'exc'):
        if k in out: print(f'  {k} = {out[k]}')
    if PNG: print('絵:', PNG)
    return 0

if __name__ == '__main__':
    sys.exit(main())
