# -*- coding: utf-8 -*-
"""⭐ 公開版（docs/・PUBLIC-2026-09-21）をヘッドレスChromeで開いて測る。

    python tools/check_public.py                 数字だけ
    python tools/check_public.py --絵 out.png    論文ノードを出した絵も撮る

測るもの＝①Uncaught ②window.DATA / BRAIN_SVG が読めて・CATALOG は無い ③島の初期表示
  ④論文ノードに Connected Papers の箱が【無く】・DOI リンクは【ある】・手元PDFのリンクが【無い】
  ⑤書庫の本のノードに書庫の箱が【無く】・本文の頁が札に【なっていない】
  ⑥絵のあるノードで figure が出て・img が読めている
⚠file:// で開く（Pages は https だが・fetch を使わない作りなので同じ）。手元版の検査は check_local.py。
"""
import io, os, re, sys, json, glob, subprocess

if not (getattr(sys.stdout, 'encoding', '') or '').lower().startswith('utf'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

args = sys.argv[1:]
PNG = os.path.abspath(args[args.index('--絵') + 1]) if '--絵' in args else None
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS = os.path.join(ROOT, 'docs')
SRC = os.path.join(DOCS, 'index.html')
TMP = os.path.join(DOCS, '_公開検査用.html')
PAPER = '2020 Peltopuro'
BOOKNODE = '小4のC君'
PICNODE = '追う人と逃げる人'

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
        out.hasDATA = !!(window.DATA && window.DATA.nodes); out.nodes = cy.nodes().not('.isletick').length;
        out.hasBRAIN = !!(window.BRAIN_SVG && window.BRAIN_SVG.length > 1000);
        out.hasCATALOG = !!(window.CATALOG && window.CATALOG.books);
        out.isles = (typeof ISLE_MODE !== 'undefined') ? ISLE_MODE : null; out.labels = cy.nodes('.isletick').length;
        const body = document.getElementById('sidebody') || document.getElementById('side');
        // ⑤ 書庫の本のノード
        const bn = cy.nodes().filter(n => n.data('label') === __BOOKNODE__);
        show(bn[0].data('node'));
        out.shoko = { box: !!body.querySelector('.shoko'), chips: body.querySelectorAll('.pg[data-p]').length };
        // ④ 論文
        const pn = cy.nodes().filter(n => n.data('label') === __PAPER__);
        show(pn[0].data('node'));
        out.paper = { cp: !!body.querySelector('.cpbox'), doi: !!body.querySelector('a[href^="https://doi.org/"]'),
                      pdflink: !!body.querySelector('a.pdflink') };
        // ⑥ 絵（最後に出して・img の load を待ってから書き出す）
        const xn = cy.nodes().filter(n => n.data('label') === __PICNODE__);
        show(xn[0].data('node'));
        const fig = body.querySelector('figure.fig'); const im = fig ? fig.querySelector('img') : null;
        const fin = () => { out.pic = { fig: !!fig, imgLoaded: !!(im && im.naturalWidth > 0), imgW: im ? im.naturalWidth : 0,
                                        caption: fig ? (fig.querySelector('figcaption')||{}).textContent : null }; done(); };
        if (im && !im.complete){ im.addEventListener('load', fin); im.addEventListener('error', fin); setTimeout(fin, 8000); return; }
        fin(); return;
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


def main():
    chrome = find_chrome()
    if not chrome:
        print('⚠Chrome が見つからない'); return 1
    if not os.path.exists(SRC):
        print('⚠docs/index.html が無い（先に tools/build_public.py）'); return 1
    s = io.open(SRC, encoding='utf-8').read()
    inj = (INJECT.replace('__PAPER__', json.dumps(PAPER, ensure_ascii=False))
                 .replace('__BOOKNODE__', json.dumps(BOOKNODE, ensure_ascii=False))
                 .replace('__PICNODE__', json.dumps(PICNODE, ensure_ascii=False)))
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
        print('⚠結果が取れなかった（地図が起動していない可能性）'); return 1
    o = json.loads(m.group(1))
    print('対象: %s（file://）' % SRC)
    print('⚠Uncaught エラー: %d 件' % len(o['err']))
    for e in o['err']: print('   ' + e)
    for k, v in o.items():
        if k == 'err': continue
        print('  %s = %s' % (k, json.dumps(v, ensure_ascii=False)))
    # 期待どおりかを一言で
    ok = (not o['err'] and o.get('hasDATA') and o.get('hasBRAIN') and not o.get('hasCATALOG')
          and o.get('paper', {}).get('cp') is False and o.get('paper', {}).get('doi') is True
          and o.get('paper', {}).get('pdflink') is False
          and o.get('shoko', {}).get('box') is False and o.get('shoko', {}).get('chips') == 0
          and o.get('pic', {}).get('imgLoaded') is True)
    print('判定: ' + ('公開版として期待どおり' if ok else '⚠期待と違うところがある'))
    if PNG: print('絵: ' + PNG)
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
