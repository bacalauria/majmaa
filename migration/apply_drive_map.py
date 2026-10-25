#!/usr/bin/env python3
"""
apply_drive_map.py — after Code.gs has finished, point the website at Google Drive.

    python3 migration/apply_drive_map.py path/to/bac_drive_map.json
    python3 build.py                       # rebuild (GitHub Actions does this on push)

What it does
  • data/exams.csv and data/content.json: every WordPress URL found in the map is
    replaced by  https://drive.google.com/file/d/<id>/view?usp=drive_link
  • WordPress URLs the migration could not download (the file no longer exists on
    WordPress) are removed from exams.csv, so the site shows "غير متوفر حاليا"
    instead of a dead link. Use --keep-missing to leave them in place.
  • writes migration/missing_files.csv — stream, year, subject, which file, old URL —
    the list of papers to find and upload by hand (then paste the Drive link into
    exams.csv).
  • prints a summary; nothing else is touched. Run it as often as you like.
"""
import argparse, csv, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
CSV_PATH = os.path.join(REPO, 'data', 'exams.csv')
CONTENT_PATH = os.path.join(REPO, 'data', 'content.json')
LINK_COLS = ['sujet_pdf', 'sujet_docx', 'solution_pdf', 'solution_docx', 'video', 'sujet_pdf_fr', 'solution_pdf_fr']

def drive_url(fid):
    return f'https://drive.google.com/file/d/{fid}/view?usp=drive_link'

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('map', help='bac_drive_map.json downloaded from the Drive archive folder')
    ap.add_argument('--keep-missing', action='store_true', help='leave dead WordPress links in place')
    a = ap.parse_args()

    m = json.load(open(a.map, encoding='utf-8'))
    files, missing = m.get('files', {}), m.get('missing', {})
    # WordPress serves the same file over http/https; match on the https form.
    norm = lambda u: re.sub(r'^http://', 'https://', (u or '').strip())

    rows = list(csv.DictReader(open(CSV_PATH, encoding='utf-8')))
    fields = list(rows[0].keys())
    replaced = dropped = left = 0
    missing_rows = []
    for r in rows:
        for c in LINK_COLS:
            u = norm(r.get(c))
            if 'wordpress.com' not in u: continue
            if u in files:
                r[c] = drive_url(files[u]); replaced += 1
            else:
                missing_rows.append(dict(stream=r['stream'], year=r['year'], session=r['session'],
                                         subject=r['subject'], file=c, old_url=u,
                                         reason=missing.get(u, 'not in map')))
                if a.keep_missing: left += 1
                else: r[c] = ''; dropped += 1

    with open(CSV_PATH, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fields); w.writeheader(); w.writerows(rows)

    # content.json (lesson summaries etc.): plain string replacement of known URLs
    text = open(CONTENT_PATH, encoding='utf-8').read()
    n_content = 0
    for u, fid in files.items():
        for variant in (u, u.replace('https://', 'http://')):
            if variant in text:
                text = text.replace(variant, drive_url(fid)); n_content += 1
    open(CONTENT_PATH, 'w', encoding='utf-8').write(text)

    out = os.path.join(HERE, 'missing_files.csv')
    with open(out, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, ['stream', 'year', 'session', 'subject', 'file', 'old_url', 'reason'])
        w.writeheader(); w.writerows(missing_rows)

    still_wp = sum(1 for r in rows for c in LINK_COLS if 'wordpress.com' in (r.get(c) or ''))
    print(f'exams.csv: {replaced} links now on Google Drive, {dropped} dead links removed, {left} kept')
    print(f'content.json: {n_content} links replaced')
    print(f'missing papers listed in {out}: {len(missing_rows)}')
    print(f'WordPress links remaining in exams.csv: {still_wp}')
    return 0

if __name__ == '__main__':
    sys.exit(main())
