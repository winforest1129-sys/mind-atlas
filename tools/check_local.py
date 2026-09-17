# -*- coding: utf-8 -*-
"""⭐ ローカル専用サイト（LOCAL-2026-09-18）が file:// で動くかをヘッドレスChromeで測る。

    python tools/check_local.py                 数字だけ
    python tools/check_local.py --絵 out.png    論文ノードと書庫の箱を出した絵も撮る

測るもの＝①Uncaught ②window.DATA / BRAIN_SVG / CATALOG が読めたか ③島の初期表示
  ④論文ノードに Connected Papers の箱・DOI リンク ⑤書庫の本のノードに書庫の箱・頁の札・押すと画像の src が入るか
  ⑥本文の中の頁が札になっているか
⚠http サーバを立てず file:// で開く（catalog.js は別フォルダの相対パスなので）
"""
import io, os, re, sys, json, glob, subprocess

if not (getattr(sys.stdout, 'encoding', '') or '').lower().startswith('utf'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

args = sys.argv[1:]
PNG = os.path.abspath(args[args.index('--絵') + 1]) if '--絵' in args else None
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'index.html')
TMP = os.path.join(ROOT, '_ローカル検査用.html')
PAPER = '2020 Peltopuro'
BOOKNODE = '小4のC君'

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
        out.hasCATALOG = !!(window.CATALOG && window.CATALOG.books); out.catalogBooks = window.CATALOG ? window.CATALOG.books.length : 0;
        out.isles = (typeof ISLE_MODE !== 'undefined') ? ISLE_MODE : null; out.labels = cy.nodes('.isletick').length;
        const body = document.getElementById('sidebody') || document.getElementById('side');
        // ④ 論文
        const pn = cy.nodes().filter(n => n.data('label') === __PAPER__);
        show(pn[0].data('node'));
        out.paper = { cp: !!body.querySelector('.cpbox a'), cpHref: (body.querySelector('.cpbox a')||{}).href || '',
                      doi: !!body.querySelector('a[href^="https://doi.org/"]') };
        // ⑤ 書庫の本のノード
        const bn = cy.nodes().filter(n => n.data('label') === __BOOKNODE__);
        show(bn[0].data('node'));
        const box = body.querySelector('.shoko');
        out.shoko = { box: !!box, book: box ? box.dataset.book : null, chips: body.querySelectorAll('.shoko .pgs .pg').length,
                      bodyChips: body.querySelectorAll('div .pg[data-p]').length - body.querySelectorAll('.shoko .pgs .pg').length };
        const chip = body.querySelector('.shoko .pgs .pg');
        if (chip){ chip.click();
          const v = box.querySelector('.view'); const img = v.querySelector('img');
          out.shoko.viewOn = v.classList.contains('on'); out.shoko.imgSrc = (img.src || '').slice(0, 90);
          out.shoko.cur = v.querySelector('.cur').textContent; out.shoko.openHref = v.querySelector('a.open').href.split('/').pop();
          v.querySelector('.next').click(); out.shoko.afterNext = v.querySelector('.cur').textContent;
        }
      } catch (e){ window.__ERR.push('inject: ' + e.message + ' @ ' + (e.stack || '').split('\n')[1]); }
      done();
    }, 1200);
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
    s = io.open(SRC, encoding='utf-8').read()
    inj = INJECT.replace('__PAPER__', json.dumps(PAPER, ensure_ascii=False)).replace('__BOOKNODE__', json.dumps(BOOKNODE, ensure_ascii=False))
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
    if PNG: print('絵: ' + PNG)
    return 0


if __name__ == '__main__':
    sys.exit(main())
