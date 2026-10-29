"""Pull visit / download statistics from GoatCounter and write data/stats.json.

Run by the deploy workflow (daily + on every push) before build.py. Needs the secret
GOATCOUNTER_TOKEN (a GoatCounter API key with read permission). Without it, or if the API
fails, it leaves any existing data/stats.json untouched and exits 0 so the build still runs.

Event names are set by assets/app.js:
  open/<stream>/<year[-session]>/<subject>/<paper|solution>/<pdf|word|fr>   file opened in the viewer
  dl/...                                                                      download button in the viewer
  video/<stream>/<year>/<subject>[/exN]                                       solution video
  out/<host>                                                                  any other external link
"""
import json, os, sys, datetime, urllib.request, urllib.parse, collections

SITE = 'https://majmaabac.goatcounter.com/api/v0'
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'data', 'stats.json')
TOKEN = os.environ.get('GOATCOUNTER_TOKEN', '').strip()
START = '2026-10-29'          # GoatCounter went live on the new site this day


def api(path, **params):
    params = {k: v for k, v in params.items() if v not in (None, [], '')}
    url = f'{SITE}{path}?' + urllib.parse.urlencode(params, doseq=True)
    req = urllib.request.Request(url, headers={'Authorization': f'Bearer {TOKEN}', 'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def all_hits(start, end):
    """Every path (pages and events) with its count in [start, end]; paginates with exclude_paths."""
    out, seen = [], []
    while True:
        d = api('/stats/hits', start=start, end=end, limit=100, exclude_paths=seen or None)
        hits = d.get('hits') or []
        out += hits
        seen += [h['path_id'] for h in hits if 'path_id' in h]
        if not d.get('more') or not hits:
            return out


def status(msg):
    """One-line status for debugging the daily run (the Actions log is not always reachable); no secrets in it."""
    open(os.path.join(ROOT, 'data', 'stats-status.txt'), 'w').write(f'{datetime.datetime.utcnow():%Y-%m-%d %H:%M} UTC  {msg}\n')


def summarise(hits):
    files, streams, subjects, parts, pages, videos, outs = (collections.Counter() for _ in range(7))
    titles = {}
    for h in hits:
        p, n = h.get('path', ''), int(h.get('count') or 0)
        if not n: continue
        if not h.get('event'):
            pages[p] += n; titles[p] = h.get('title') or p; continue
        seg = p.split('/')
        kind = seg[0]
        if kind in ('open', 'dl') and len(seg) >= 6:
            _, st, yr, sub, part, fmt = seg[:6]
            key = f'{st}/{yr}/{sub}/{part}'
            files[key] += n; streams[st] += n; subjects[sub] += n; parts[f'{part}/{fmt}'] += n
        elif kind == 'video' and len(seg) >= 4:
            videos['/'.join(seg[1:4])] += n; streams[seg[1]] += 0
        elif kind == 'out' and len(seg) >= 2:
            outs[seg[1]] += n
    top = lambda c, k=20: [[key, v] for key, v in c.most_common(k)]
    return dict(downloads=sum(files.values()), videos=sum(videos.values()),
                files=top(files, 30), streams=top(streams, 20), subjects=top(subjects, 30), parts=top(parts, 10),
                pages=[[p, titles.get(p, p), v] for p, v in pages.most_common(15)], video_top=top(videos, 15), outbound=top(outs, 15))


def main():
    if not TOKEN:
        status('no GOATCOUNTER_TOKEN secret'); print('stats: no GOATCOUNTER_TOKEN, skipping'); return
    today = datetime.date.today()
    now = datetime.datetime.utcnow().replace(microsecond=0)
    iso = lambda d: d.strftime('%Y-%m-%dT%H:%M:%SZ')
    t0 = datetime.datetime.fromisoformat(START)
    try:
        tot = api('/stats/total', start=iso(t0), end=iso(now))
        month = summarise(all_hits(iso(max(t0, now - datetime.timedelta(days=30))), iso(now)))
        ever = summarise(all_hits(iso(t0), iso(now)))
    except Exception as e:                       # never break the build because of stats
        body = ''
        if hasattr(e, 'read'):
            try: body = e.read().decode()[:400]
            except Exception: pass
        status(f'API error: {e} {body}')
        print('stats: API error, keeping previous stats.json:', e, body); return
    status(f"ok: {tot.get('total', 0)} pageviews, {ever['downloads']} file opens")
    data = dict(updated=today.isoformat(), since=START, visitors=tot.get('total', 0), month=month, all=ever)
    json.dump(data, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(f"stats: {data['visitors']} pageviews, {ever['downloads']} file opens since {START}")


if __name__ == '__main__':
    main()
