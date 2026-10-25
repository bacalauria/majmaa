# مَجْمَعُ البكالوريا — Baccalauria

The new home of **baccalauria.wordpress.com**: a fast static site for GitHub Pages,
generated from one spreadsheet-friendly data file. All files (exam papers and
solutions) live in the Google Drive of **bacalauria@gmail.com**.

| | |
|---|---|
| Exam rows | 1,722 (12 streams, 1995 → 2026) |
| Files linked | 3,397 papers and solutions |
| Pages | 23 static pages + instant search over every paper |
| Weight | home page 17 KB of HTML, largest stream page 215 KB (≈ 20 KB gzipped); search data loads only when used; fonts self-hosted; no framework, no tracking |

---

## 1. Folder layout

```
build.py                    the site generator (Python 3 + Jinja2)
data/exams.csv              ★ every exam: stream, year, session, subject + its links
data/meta.json              stream names, subject names, session labels
data/content.json           lessons, other countries, olympiads, articles, laureates
data/site.json              site URL, title, e-mail (used for SEO + sitemap)
src/templates/*.html        page templates
src/assets/                 style.css, app.js, fonts, icon
migration/Code.gs           Google Apps Script: WordPress → Google Drive
migration/bac_migration_manifest.json   the 2,300 files to move, with target folders
migration/apply_drive_map.py            rewrites data/ to the new Drive links
.github/workflows/pages.yml builds and publishes on every push
```

## 2. Put it on GitHub (once)

1. Create a repository (e.g. `baccalauria`) and upload the content of this folder.
2. **Settings → Pages → Build and deployment → Source: GitHub Actions.**
3. `data/site.json` → `"url"` is `https://bacalauria.github.io/majmaa/`; change it if
   you add a custom domain (it only affects SEO tags, the sitemap and the 404 page).
4. Push. The *Build and deploy site* action publishes the site in ~1 minute.

Custom domain (e.g. `baccalauria.dz`): put it in `data/site.json` → `"cname"` and
`"url"`, and add the DNS records GitHub lists under Settings → Pages.

Preview locally: `pip install jinja2 && python3 build.py --serve` → http://localhost:8000

## 3. Files on Google Drive

All papers live in the Drive of **bacalauria@gmail.com** under

```
بكالوريا الجزائر/
  النظام الجديد/<الشعبة>/<السنة>/bac_<year>_<code>_<Subject>[_s].pdf     (2008 → today)
  النظام الجديد/<الشعبة>/2017/دورة-1 | دورة-2                            (two sessions)
  النظام القديم/<الشعبة>/<السنة>/…                                       (1995 → 2007)
  ملفات من ووردبريس غير مرتبطة/                                          (media-library extras)
```

Codes: `m se mt ge lp le art` (new system), `sx snv ge si l` (old system).
Every file is shared *anyone with the link can view*.

**The October 2026 migration.** Years 2018+ were already on Drive. Everything older
was still on WordPress; it was copied by the Apps Script project **“BAClaude”** in
the bacalauria account (`migration/Migrate.gs` + the compact job list
`migration/manifest_compact.tsv`). The script downloads in parallel, renames to the
convention above, re-uses files already in Drive, resumes itself every minute and
writes `majmaa_drive_map.json` (old URL → Drive id) to My Drive when done. Then:

```bash
python3 migration/apply_drive_map.py majmaa_drive_map.json   # rewrites data/ to Drive links
python3 build.py                                             # or just push: Actions rebuilds
```

`migration/missing_files.csv` lists the papers WordPress could no longer serve; they
are restored from the local archive (`D:\Teaching\BAC\BACAlgeria`).

## 4. Adding a new session (e.g. BAC 2027)

Open `data/exams.csv` in Excel / Google Sheets / LibreOffice and add one row per
subject:

| system | stream | year | session | subject | sujet_pdf | sujet_docx | solution_pdf | solution_docx | video |
|---|---|---|---|---|---|---|---|---|---|
| new | math | 2027 | main | math | *Drive link* | | *Drive link* | | |

* `stream`: `math se mt ge lph lang arts` (new system), `sx snv oge lsi lsh` (old).
* `session`: `main`, or `s1` / `s2` / `exc` (first, second, exceptional).
* `subject` codes are listed in `data/meta.json` (`ar math phys svt isl hg en fr philo tz …`).
* Rows appear in file order, so put new years at the top of each stream's block.

Save as CSV (UTF-8), push. Done. New laureates go in `data/content.json` → `toppers`.

## 5. Things found in the WordPress content (and how they were handled)

* **Maths page:** below its 2026 table, the WordPress Maths page contained a full
  copy of the *Sciences expérimentales* page (2025 → 2008, same Drive files,
  `bac_*_se_*` names). The real Maths tables (`bac_*_m_*`) came after it. The
  new site uses the real Maths tables, so visitors to Maths no longer see
  Sciences papers for 2008 → 2025.
* **Arts page:** the first table is headed *2025* while a second 2025 table and
  2024 follow. It is treated as **2026**. Please confirm.
* **228 WordPress links point to files that are not in the media library**
  (mostly old-system GE/SI/L 1995–2007 and some links to the old blog
  `khelifak.files.wordpress.com`). They are probably already broken on the live
  site. The migration tries alternative addresses for each one; whatever still
  fails ends up in `missing_files.csv`.
* Typos fixed in display only: «اللعة الفرنسية» → «اللغة الفرنسية».
* Empty WordPress pages (USA, Canada, UK, pre-1995, old-system lessons) were not
  carried over.
* The media library also holds non-BAC files (university course PDFs and Excel
  sheets, theme images). They are not part of the site and are not moved.

## 6. Design notes

Modern ed-tech look: white surfaces, an indigo → violet brand gradient and a
colour per subject and stream (`HUES` / `STREAM_STYLE` in `build.py`). Titles use
*Readex Pro*, text *IBM Plex Sans Arabic*; both are self-hosted under the SIL Open
Font License. Light and dark themes follow the device, with a toggle.

Every exam row keeps the old site's columns:
**الموضوع (PDF · Word) | الحل (PDF · Word) | فيديو الحل**. A file that is not ready
yet shows as a faint dashed “قريبا” chip; fill the `sujet_docx`, `solution_docx` or
`video` cell in `data/exams.csv` and the chip turns into a live button. The
**للأساتذة** page explains the Word project and counts what is available.
Google Drive files open in an in-page viewer with download and "open in Drive"
buttons. Press `/` anywhere to search.
