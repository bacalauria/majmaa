"""Per-page link-preview cards (1200x630) -> src/assets/og/<key>.jpg

Each page of the site gets its own Facebook/WhatsApp/X preview image showing the
section and the page title, in the brand style of the site-wide og-image.

Run from the repo root (needs playwright + Pillow, fonts from src/assets/fonts):
    python brand/og_cards.py
It runs build.py with OG_MANIFEST set to collect every page's title/description,
renders one HTML card per page with Chromium, and saves JPEGs. Re-run after adding
pages or changing titles; build.py picks the cards up automatically (and versions
their URLs by content hash so social sites refresh them).
"""
import json, os, re, shutil, subprocess, sys, tempfile, html
sys.path.insert(0, os.path.dirname(__file__))
os.chdir(os.path.dirname(os.path.abspath(__file__)))           # make2 reads mim-path.txt from here
from make2 import HEAD, green_bg, CREAM, GOLD, RED            # noqa: E402  (brand palette and background)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DST = os.path.join(ROOT, 'src', 'assets', 'og')
SECTION = {'bac': 'البكالوريا الجزائرية', 'lessons': 'دروس و ملخصات', 'world': 'البكالوريا في العالم',
           'olympiads': 'الأولمبياد العلمية', 'videos': 'سلاسل الفيديو', 'articles': 'مقالات',
           'teachers': 'للأساتذة', 'productions': 'إصداراتنا', 'platforms': 'مراجع'}


def split(c):
    """-> (kicker, title, accent line) for the card."""
    t, sec = c['title'], c['section']
    m = re.match(r'مواضيع و حلول بكالوريا (شعبة .+?) (\d{4} – \d{4})$', t)
    if m: return 'مواضيع و حلول البكالوريا', m[1], m[2]
    if t.endswith(' — محتوى السلسلة'): return 'سلسلة فيديو', t[:-len(' — محتوى السلسلة')], ''
    if t.startswith('دروس و ملخصات — '): return 'دروس و ملخصات', t.split(' — ', 1)[1], ''
    if t.startswith('للأساتذة: '): return 'للأساتذة', t[len('للأساتذة: '):], ''
    return SECTION.get(sec, 'مَجْمَعُ البكالوريا'), t, ''


def card(c):
    kick, title, accent = (html.escape(x) for x in split(c))
    fs = 76 if len(title) <= 22 else 64 if len(title) <= 34 else 54
    desc = html.escape(c['desc'])
    return green_bg() + f'''<div style="position:absolute;inset:0;padding:58px 76px 54px;display:flex;flex-direction:column">
<div style="display:flex;justify-content:space-between;align-items:center">
  <div style="display:flex;align-items:center;gap:16px"><img src="emblem.png" style="width:92px;height:92px;margin:-14px 0"><div class="wm" style="font-size:44px">مَجْمَعُ البكالوريا</div></div>
  <span style="font:700 26px TJ;color:{GOLD};padding:8px 24px;border-radius:99px;border:2px solid rgba(201,162,74,.65)">{kick}</span></div>
<div style="flex:1;display:flex;flex-direction:column;justify-content:center">
  <div style="font:700 {fs}px/1.28 EM;color:{CREAM}">{title}</div>
  {f'<div style="font:700 40px TJ;color:{GOLD};margin-top:10px;direction:ltr;text-align:right">{accent}</div>' if accent else ''}
  <div class="rule" style="width:300px;margin:26px 0 22px"><i></i><b></b><i></i></div>
  <div style="font:400 29px/1.5 TJ;color:rgba(251,248,241,.82);display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;max-width:1000px">{desc}</div>
</div>
<div style="font:400 24px TJ;color:rgba(251,248,241,.6)">كل ما يحتاجه طالب البكالوريا، في مكان واحد</div></div>'''


def main():
    tmp = tempfile.mkdtemp()
    man = os.path.join(tmp, 'og.json')
    subprocess.run([sys.executable, os.path.join(ROOT, 'build.py')], check=True, cwd=ROOT,
                   env={**os.environ, 'OG_MANIFEST': man}, stdout=subprocess.DEVNULL)
    cards = [c for c in json.load(open(man, encoding='utf-8')) if c['key'] != 'home']   # home keeps og-image.jpg
    for f in os.listdir(os.path.join(ROOT, 'src', 'assets', 'fonts')):
        shutil.copy(os.path.join(ROOT, 'src', 'assets', 'fonts', f), tmp)
    shutil.copy(os.path.join(ROOT, 'brand', 'emblem.png'), tmp)
    for c in cards:
        open(os.path.join(tmp, c['key'] + '.html'), 'w', encoding='utf-8').write(
            HEAD + '<style>html,body{width:1200px;height:630px;overflow:hidden}</style>' + card(c))
    os.makedirs(DST, exist_ok=True)
    js = os.path.join(tmp, 'shoot.js')
    open(js, 'w').write('''const {chromium}=require('playwright');const keys=%s;
(async()=>{const b=await chromium.launch();const p=await b.newPage({viewport:{width:1200,height:630}});
for(const k of keys){await p.goto('file://%s/'+k+'.html');await p.evaluate(()=>document.fonts.ready);await p.waitForTimeout(150);
await p.screenshot({path:'%s/'+k+'.png'});}await b.close();})();''' % (json.dumps([c['key'] for c in cards]), tmp, tmp))
    subprocess.run(['node', js], check=True, cwd=tmp)
    from PIL import Image
    for c in cards:
        Image.open(os.path.join(tmp, c['key'] + '.png')).convert('RGB').save(
            os.path.join(DST, c['key'] + '.jpg'), quality=86, optimize=True, progressive=True)
    print(f'{len(cards)} cards -> {DST}')


if __name__ == '__main__':
    main()
