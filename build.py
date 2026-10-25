#!/usr/bin/env python3
"""
build.py — static-site generator for مجمع البكالوريا (Baccalauria).

    python3 build.py            # writes the whole site into ./_site
    python3 build.py --serve    # same, then serves it on http://localhost:8000

Sources
  data/exams.csv     one row per (stream, year, session, subject) with its links.
                     Edit it in any spreadsheet program; it is the single source of
                     truth for the exam archive.
  data/meta.json     streams, subject names, session labels.
  data/content.json  lessons, other countries, olympiads, articles, laureates.
  data/site.json     site URL, title, contact (used for SEO tags and sitemap).
  src/templates/     Jinja2 templates.   src/assets/  CSS, JS, icons.

Every link is written relative to the page, so the output works unchanged at a
custom domain, at <user>.github.io, or at <user>.github.io/<repo>/.
"""
import csv, json, os, re, shutil, sys, collections
from jinja2 import Environment, FileSystemLoader, select_autoescape

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, '_site')
D = lambda *p: os.path.join(ROOT, 'data', *p)

site = json.load(open(D('site.json'), encoding='utf-8'))
meta = json.load(open(D('meta.json'), encoding='utf-8'))
content = json.load(open(D('content.json'), encoding='utf-8'))
rows = list(csv.DictReader(open(D('exams.csv'), encoding='utf-8')))

STREAMS = {s['id']: s for s in meta['streams']}
SUBJECTS = meta['subjects']
SESSIONS = meta['sessions']
SYSTEMS = {'new': 'النظام الجديد', 'old': 'النظام القديم'}
SHORT = {  # short names used in search results and tiles
    'math': 'رياضيات', 'se': 'علوم تجريبية', 'mt': 'تقني رياضي', 'ge': 'تسيير و اقتصاد',
    'lph': 'آداب و فلسفة', 'lang': 'لغات أجنبية', 'arts': 'فنون', 'sx': 'علوم دقيقة',
    'snv': 'علوم الطبيعة و الحياة', 'oge': 'تسيير و اقتصاد', 'lsi': 'آداب و علوم شرعية',
    'lsh': 'آداب و علوم إنسانية'}
for k, v in SHORT.items(): STREAMS[k]['short'] = v

# Colour (HSL hue) of every subject and stream: used for dots, chips and card accents.
HUES = {'ar': 350, 'math': 235, 'phys': 200, 'svt': 145, 'isl': 170, 'shar': 170, 'hg': 30, 'en': 265,
        'fr': 215, 'philo': 290, 'tz': 48, 'compta': 22, 'eco': 12, 'ecolaw': 5, 'law': 330, 'ge_el': 190,
        'ge_mec': 205, 'ge_civ': 25, 'ge_proc': 160, 'de': 275, 'es': 15, 'it': 130, 'arts': 315}
STREAM_STYLE = {  # hue + icon id (see the <symbol>s in base.html)
    'math': (235, 'sigma'), 'se': (155, 'flask'), 'mt': (200, 'compass'), 'ge': (28, 'chart'),
    'lph': (290, 'book'), 'lang': (265, 'globe'), 'arts': (330, 'brush'), 'sx': (235, 'pi'),
    'snv': (145, 'leaf'), 'oge': (28, 'chart'), 'lsi': (175, 'scroll'), 'lsh': (300, 'people')}
for k, (h, ic) in STREAM_STYLE.items(): STREAMS[k].update(hue=h, icon=ic)

# ------------------------------------------------------------ link helpers ---
def drive_id(url):
    m = re.search(r'/d/([\w-]{10,})|[?&]id=([\w-]{10,})', url or '')
    return (m.group(1) or m.group(2)) if m else None

def link(url, kind):
    """Describe one file link for the templates and the JS preview."""
    if not url: return None
    did = drive_id(url) if ('google.com' in url) else None
    return dict(url=url, kind=kind, drive=did,
                host='drive' if did else 'youtube' if 'youtu' in url else 'web')

# --------------------------------------------------------- group the exams ---
by_stream = collections.OrderedDict((s['id'], collections.OrderedDict()) for s in meta['streams'])
for r in rows:
    key = (int(r['year']), r['session'])
    c = dict(sp=link(r['sujet_pdf'], 'PDF'), sw=link(r['sujet_docx'], 'Word'), sf=link(r['sujet_pdf_fr'], 'FR'),
             cp=link(r['solution_pdf'], 'PDF'), cw=link(r['solution_docx'], 'Word'), cf=link(r['solution_pdf_fr'], 'FR'),
             v=link(r['video'], 'Video'))
    by_stream[r['stream']].setdefault(key, []).append(dict(
        subject=r['subject'], name=SUBJECTS.get(r['subject'], r['subject']), hue=HUES.get(r['subject'], 230), c=c,
        sujet=[x for x in (c['sp'], c['sw'], c['sf']) if x],
        solution=[x for x in (c['cp'], c['cw'], c['cf']) if x],
        video=c['v']))

def stream_view(sid):
    s = STREAMS[sid]; years = []
    for (y, sess), items in by_stream[sid].items():
        years.append(dict(year=y, session=sess, session_label=SESSIONS.get(sess, ''),
                          anchor=f'y{y}' + ('' if sess == 'main' else f'-{sess}'), rows=items))
    subj_order = []
    for y in years:
        for it in y['rows']:
            if it['subject'] not in subj_order: subj_order.append(it['subject'])
    files = sum(len(it['sujet']) + len(it['solution']) for y in years for it in y['rows'])
    words = sum(bool(it['c']['sw']) + bool(it['c']['cw']) for y in years for it in y['rows'])
    videos = sum(bool(it['c']['v']) for y in years for it in y['rows'])
    ys = [y['year'] for y in years]
    return dict(s, system_name=SYSTEMS[s['system']], years=years,
                subjects=[(k, SUBJECTS[k]) for k in subj_order],
                first=min(ys), last=max(ys), files=files, words=words, videos=videos,
                decades=sorted({y // 10 * 10 for y in ys}, reverse=True))

views = {sid: stream_view(sid) for sid in by_stream}
total_files = sum(v['files'] for v in views.values())
total_words = sum(v['words'] for v in views.values())
total_videos = sum(v['videos'] for v in views.values())
all_years = sorted({y['year'] for v in views.values() for y in v['years']}, reverse=True)
year_streams = {y: [sid for sid, v in views.items() if any(x['year'] == y for x in v['years'])]
                for y in all_years}

# ------------------------------------------------------------ search index ---
def search_index():
    """Compact array consumed by assets/app.js: one entry per exam row."""
    idx = []
    for sid, v in views.items():
        for y in v['years']:
            for it in y['rows']:
                idx.append([sid, y['year'], y['session'], it['subject'],
                            [[l['kind'], l['url']] for l in it['sujet']],
                            [[l['kind'], l['url']] for l in it['solution']],
                            it['video']['url'] if it['video'] else ''])
    return dict(streams={k: [v['short'], v['name'], v['system']] for k, v in STREAMS.items()},
                subjects=SUBJECTS, sessions=SESSIONS, hues=HUES, rows=idx)

# ------------------------------------------------------------------ render ---
env = Environment(loader=FileSystemLoader(os.path.join(ROOT, 'src', 'templates')),
                  autoescape=select_autoescape(['html']), trim_blocks=True, lstrip_blocks=True)
import hashlib
ASSET_VER = hashlib.md5(b''.join(open(os.path.join(ROOT, 'src', 'assets', f), 'rb').read()
                                 for f in ('style.css', 'app.js'))).hexdigest()[:8]   # cache-buster
env.globals.update(ver=ASSET_VER, drive_id=drive_id, site=site, streams=STREAMS, views=views, SYSTEMS=SYSTEMS,
                   total_files=total_files, total_words=total_words, total_videos=total_videos, HUES=HUES, all_years=all_years, content=content)
pages = []

def render(tpl, path, **ctx):
    """path is the output path relative to _site, e.g. 'bac/math/index.html'."""
    depth = path.count('/')
    ctx['root'] = '../' * depth or './'
    if path == '404.html':   # served from any URL depth -> needs the absolute base path
        from urllib.parse import urlparse
        ctx['root'] = urlparse(site['url']).path or '/'
        if not ctx['root'].endswith('/'): ctx['root'] += '/'
    ctx['path'] = path
    html = env.get_template(tpl).render(**ctx)
    dst = os.path.join(OUT, path)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    open(dst, 'w', encoding='utf-8').write(html)
    if not path.startswith('404'): pages.append(path)

def build():
    if os.path.isdir(OUT): shutil.rmtree(OUT)
    shutil.copytree(os.path.join(ROOT, 'src', 'assets'), os.path.join(OUT, 'assets'))
    json.dump(search_index(), open(os.path.join(OUT, 'assets', 'search.json'), 'w', encoding='utf-8'),
              ensure_ascii=False, separators=(',', ':'))
    open(os.path.join(OUT, '.nojekyll'), 'w').close()
    if site.get('cname'): open(os.path.join(OUT, 'CNAME'), 'w').write(site['cname'] + '\n')

    render('home.html', 'index.html', page='home', year_streams=year_streams)
    render('bac_index.html', 'bac/index.html', page='bac')
    for sid, v in views.items():
        render('stream.html', f'bac/{sid}/index.html', page='bac', v=v)
    render('teachers.html', 'teachers/index.html', page='teachers')
    render('lessons.html', 'lessons/index.html', page='lessons')
    render('world.html', 'world/index.html', page='world')
    render('olympiads.html', 'olympiads/index.html', page='olympiads')
    render('article.html', 'platforms/index.html', page='platforms', a=content['platforms'])
    render('articles.html', 'articles/index.html', page='articles')
    for a in content['articles']:
        render('article.html', f'articles/{a["slug"]}/index.html', page='articles', a=a)
    render('toppers.html', 'articles/laureates/index.html', page='articles')
    render('404.html', '404.html', page='404')

    base = site['url'].rstrip('/') + '/'
    sm = ['<?xml version="1.0" encoding="UTF-8"?>',
          '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for p in pages:
        sm.append(f'<url><loc>{base}{p.replace("index.html", "")}</loc></url>')
    sm.append('</urlset>')
    open(os.path.join(OUT, 'sitemap.xml'), 'w').write('\n'.join(sm))
    open(os.path.join(OUT, 'robots.txt'), 'w').write(f'User-agent: *\nAllow: /\nSitemap: {base}sitemap.xml\n')
    print(f'built {len(pages)} pages, {len(rows)} exam rows, {total_files} files -> {OUT}')

if __name__ == '__main__':
    build()
    if '--serve' in sys.argv:
        import http.server, functools
        h = functools.partial(http.server.SimpleHTTPRequestHandler, directory=OUT)
        print('serving on http://localhost:8000'); http.server.ThreadingHTTPServer(('', 8000), h).serve_forever()
