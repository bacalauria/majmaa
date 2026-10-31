#!/usr/bin/env python3
"""
build.py — static-site generator for مَجْمَعُ البكالوريا (Baccalauria).

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

# Scheduled videos: data/video_schedule.json maps a YouTube id to the moment it goes public
# ("2026-11-02T18:00:00+01:00").  Until then the video is left out everywhere (exam tables,
# series pages, article links), so the site never links to a video that is still private.
# The workflow rebuilds the site daily and shortly after each publishing slot.
from datetime import datetime, timezone
SCHED = json.load(open(D('video_schedule.json'))) if os.path.exists(D('video_schedule.json')) else {}
NOW = datetime.fromisoformat(os.environ['BUILD_NOW']) if os.environ.get('BUILD_NOW') else datetime.now(timezone.utc)  # BUILD_NOW: preview a later date
AR_MONTHS = ['', 'جانفي', 'فيفري', 'مارس', 'أفريل', 'ماي', 'جوان', 'جويلية', 'أوت', 'سبتمبر', 'أكتوبر', 'نوفمبر', 'ديسمبر']
def yt_id(u):
    m = re.search(r'(?:youtu\.be/|[?&]v=|shorts/|embed/)([\w-]{11})', u or '')
    return m.group(1) if m else (u if re.fullmatch(r'[\w-]{11}', u or '') else None)
def is_live(u):
    t = SCHED.get(yt_id(u))
    return not t or datetime.fromisoformat(t) <= NOW
def publish_day(u):
    d = datetime.fromisoformat(SCHED[yt_id(u)]); return f'{d.day} {AR_MONTHS[d.month]}'
for r in rows:
    if r['video'] and SCHED:
        us = [u.strip() for u in r['video'].split('|') if u.strip()]
        r['_multi'] = len(us) > 1
        r['video'] = '|'.join(u for u in us if is_live(u))
for s in content['video_series']:
    if s.get('episodes'): s['episodes'] = [e for e in s['episodes'] if is_live(e['id'])]
content['video_series'] = [s for s in content['video_series'] if not s.get('hide_until_live') or s.get('episodes')]

# Articles: the body of each article lives in data/articles/<slug>.html (plain HTML).
# Headings <h2> get ids and feed the table of contents; reading time ≈ 180 words/min.
def load_article(a):
    f = D('articles', a['slug'] + '.html')
    if os.path.exists(f): a['html'] = open(f, encoding='utf-8').read()
    toc, n = [], [0]
    def h2(m):
        n[0] += 1; toc.append((f's{n[0]}', re.sub(r'<[^>]+>', '', m.group(1))))
        return f'<h2 id="s{n[0]}">{m.group(1)}</h2>'
    a['html'] = re.sub(r'<h2>(.*?)</h2>', h2, a['html'])
    # links to videos that are not public yet become plain text with their publishing day
    a['html'] = re.sub(r'<a href="(https://www\.youtube\.com/watch\?v=[\w-]{11}[^"]*)"[^>]*>(.*?)</a>',
                       lambda m: m.group(0) if is_live(m.group(1)) else f'{m.group(2)} <small class="soon">(يُنشر في {publish_day(m.group(1))})</small>',
                       a['html'])
    a['toc'] = toc
    words = len(re.sub(r'<[^>]+>', ' ', a['html']).split())
    a['minutes'] = max(1, round(words / 180))
    return a
for a in content['articles']: load_article(a)
content['platforms'].update(slug='platforms', title='المنصات التعليمية', kind='دليل',
    desc='أفضل المنصات التعليمية المجانية لتلميذ البكالوريا و أستاذه: الرسمية الجزائرية، العربية، العالمية، و الأدوات.')
load_article(content['platforms'])
# ------------------------------------------------ topic pages (world, olympiads)
# Each topic page body is plain HTML in data/<section>/<id>.html: an optional
# <p class="lead">, an optional <div class="facts">, then <h2> sections.  The body
# is cut into those parts so the template can lay them out as a hero + section cards.
def load_body(path):
    html = open(path, encoding='utf-8').read() if os.path.exists(path) else ''
    lead = facts = ''
    m = re.search(r'<p class="lead">(.*?)</p>', html, re.S)
    if m: lead, html = m.group(1), html.replace(m.group(0), '', 1)
    m = re.search(r'<div class="facts">(.*?)\n</div>', html, re.S)
    if m: facts, html = m.group(1), html.replace(m.group(0), '', 1)
    parts = re.split(r'<h2>(.*?)</h2>', html)
    pre, secs = parts[0].strip(), []
    for i in range(1, len(parts), 2):
        secs.append(dict(id=f's{len(secs)+1}', title=parts[i], html=parts[i+1].strip()))
    return dict(lead=lead, facts=facts, pre=pre, sections=secs)

world = json.load(open(D('world.json'), encoding='utf-8'))
for x in world['systems']: x.update(load_body(D('world', x['id'] + '.html')))
olymp = json.load(open(D('olympiads.json'), encoding='utf-8'))
for x in olymp['subjects']: x.update(load_body(D('olympiads', x['id'] + '.html')))
lessons = json.load(open(D('lessons.json'), encoding='utf-8'))
# per-stream module lists: the stream's key modules first, then the common ones
LESSON_ORDER = {
    'math': ['math', 'phys', 'svt'], 'mt': ['math', 'phys', 'ge_civ', 'ge_el', 'ge_mec', 'ge_proc'],
    'se': ['svt', 'phys', 'math'], 'ge': ['compta', 'eco', 'law', 'math'],
    'lph': ['philo', 'ar', 'hg'], 'lang': ['fr', 'en', 'de', 'es', 'it', 'ar', 'philo'], 'arts': ['arts', 'ar', 'philo']}
lessons['by_stream'], lessons['mod_count'] = {}, {}
for sid in lessons['streams']:
    mine = []
    for m in lessons['modules']:
        for grp in m['variants']:
            if sid in grp:
                items = {g: [it for it in its if sid in it.get('for', [sid])] for g, its in m['items'].items()}
                mine.append(dict(subject=m['subject'], items=items, shared=[x for x in grp if x != sid]))
    pri = LESSON_ORDER.get(sid, [])
    mine.sort(key=lambda m: pri.index(m['subject']) if m['subject'] in pri else len(pri))
    lessons['by_stream'][sid], lessons['mod_count'][sid] = mine, len(mine)

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
             v=link(r['video'].split('|')[0], 'Video'),
             # several videos (one per exercise) are stored as url1|url2|...
             vs=[link(u.strip(), 'Video') for u in r['video'].split('|') if u.strip()] if ('|' in r['video'] or r.get('_multi')) else [])
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
import hashlib, re, html as html_lib
ASSET_VER = hashlib.md5(b''.join(open(os.path.join(ROOT, 'src', 'assets', f), 'rb').read()
                                 for f in ('style.css', 'app.js'))).hexdigest()[:8]   # cache-buster
MONTHS = ['جانفي', 'فيفري', 'مارس', 'أفريل', 'ماي', 'جوان', 'جويلية', 'أوت', 'سبتمبر', 'أكتوبر', 'نوفمبر', 'ديسمبر']
env.filters['ardate'] = lambda d: f"{MONTHS[int(d[5:7]) - 1]} {d[:4]}" if d and len(d) >= 7 else (d or '')
env.globals.update(ver=ASSET_VER, drive_id=drive_id, site=site, streams=STREAMS, views=views, SYSTEMS=SYSTEMS,
                   total_files=total_files, total_words=total_words, total_videos=total_videos, HUES=HUES, all_years=all_years, content=content,
                   world=world, olymp=olymp, lessons=lessons, SUBJ=SUBJECTS)
pages = []
og_cards = []
# Visit / download statistics pulled from GoatCounter by scripts/stats.py (absent until the API key is set).
_sp = os.path.join(ROOT, 'data', 'stats.json')
stats = json.load(open(_sp, encoding='utf-8')) if os.path.exists(_sp) else None
_lp = os.path.join(ROOT, 'data', 'legacy_stats.json')
legacy = json.load(open(_lp, encoding='utf-8')) if os.path.exists(_lp) else None   # old WordPress (Jetpack) totals
env.globals.update(stats=stats, stats_public=site.get('stats_public', False), legacy=legacy)

def render(tpl, path, **ctx):
    """path is the output path relative to _site, e.g. 'bac/math/index.html'."""
    depth = path.count('/')
    ctx['root'] = '../' * depth or './'
    if path == '404.html':   # served from any URL depth -> needs the absolute base path
        from urllib.parse import urlparse
        ctx['root'] = urlparse(site['url']).path or '/'
        if not ctx['root'].endswith('/'): ctx['root'] += '/'
    ctx['path'] = path
    # Per-page link-preview card (assets/og/<key>.jpg, made by brand/og_cards.py); falls back to the site-wide one.
    key = path[:-len('index.html')].strip('/').replace('/', '-') or 'home'
    og = os.path.join(ROOT, 'src', 'assets', 'og', key + '.jpg')
    if os.path.exists(og):
        ctx['og_image'] = f"assets/og/{key}.jpg?v={hashlib.md5(open(og, 'rb').read()).hexdigest()[:6]}"
    html = env.get_template(tpl).render(**ctx)
    if not path.startswith('404'):   # manifest the card generator reads: key, section, title, description
        m = lambda prop: (re.search(f'<meta property="og:{prop}" content="([^"]*)"', html) or [None, ''])[1]
        og_cards.append({'key': key, 'section': path.split('/')[0] if '/' in path else '',
                         'title': html_lib.unescape(m('title')).split(' | ')[0], 'desc': html_lib.unescape(m('description'))})
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
    render('videos.html', 'videos/index.html', page='videos')
    for s in content['video_series']:
        if s.get('episodes'): render('video_series.html', f'videos/{s["slug"]}/index.html', page='videos', s=s)
    render('productions.html', 'productions/index.html', page='productions')
    render('lessons_hub.html', 'lessons/index.html', page='lessons')
    for sid in lessons['streams']:
        render('lessons_stream.html', f'lessons/{sid}/index.html', page='lessons', v=views[sid])
    render('world_hub.html', 'world/index.html', page='world')
    for x in world['systems']:
        render('topic.html', f'world/{x["id"]}/index.html', page='world', t=x, kind='world')
    render('olymp_hub.html', 'olympiads/index.html', page='olympiads')
    for x in olymp['subjects']:
        render('topic.html', f'olympiads/{x["id"]}/index.html', page='olympiads', t=x, kind='olympiads')
    if stats or legacy: render('popular.html', 'popular/index.html', page='popular')
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
    if os.environ.get('OG_MANIFEST'):   # only when regenerating cards: python brand/og_cards.py
        json.dump(og_cards, open(os.environ['OG_MANIFEST'], 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    _ss = os.path.join(ROOT, 'data', 'stats-status.txt')
    if os.path.exists(_ss): shutil.copy(_ss, os.path.join(OUT, 'stats-status.txt'))
    open(os.path.join(OUT, 'robots.txt'), 'w').write(f'User-agent: *\nAllow: /\nSitemap: {base}sitemap.xml\n')
    print(f'built {len(pages)} pages, {len(rows)} exam rows, {total_files} files -> {OUT}')

if __name__ == '__main__':
    build()
    if '--serve' in sys.argv:
        import http.server, functools
        h = functools.partial(http.server.SimpleHTTPRequestHandler, directory=OUT)
        print('serving on http://localhost:8000'); http.server.ThreadingHTTPServer(('', 8000), h).serve_forever()
