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
3. Edit `data/site.json` → `"url"` to the address GitHub shows you, e.g.
   `https://<your-user>.github.io/baccalauria/` (this only affects SEO tags, the
   sitemap and the 404 page; every other link is relative and works anywhere).
4. Push. The *Build and deploy site* action publishes the site in ~1 minute.

Custom domain (e.g. `baccalauria.dz`): put it in `data/site.json` → `"cname"` and
`"url"`, and add the DNS records GitHub lists under Settings → Pages.

Preview locally: `pip install jinja2 && python3 build.py --serve` → http://localhost:8000

## 3. Move the old files from WordPress to Google Drive

Years **2018 → 2026** are already on Drive. Everything older — new system
2008 → 2017 and the whole old system 1995 → 2007, **2,247 files**, plus 53 BAC
papers that sit in the WordPress media library without being linked — is still
on WordPress. The migration runs inside the Drive account itself:

1. Sign in to Google as **bacalauria@gmail.com**.
2. Upload `migration/bac_migration_manifest.json` to Google Drive (anywhere).
3. Open <https://script.google.com> → **New project**. Replace the code with the
   content of `migration/Code.gs`. Save.
4. Choose the function **`start`** → **Run** → accept the permissions.
5. Close the tab. The script works in 4½-minute slices and re-schedules itself;
   ~2,300 files take roughly 30–45 minutes. You get an e-mail when it is done.
   Run **`status`** at any time to see progress.

Result in Drive:

```
مجمع البكالوريا - أرشيف/
  النظام الجديد/  شعبة الرياضيات/  2012/  BAC2012_math_math_sujet.pdf, …_corrige.pdf …
  النظام القديم/  شعبة العلوم الدقيقة/  1999/ …
  ملفات غير مرتبطة بالموقع/   (unlinked BAC papers found in the media library)
  bac_drive_map.json           (old URL → Drive id)
```

Every file is shared *anyone with the link can view*, like the recent years.
The script is idempotent: re-running never duplicates a file.

6. Download `bac_drive_map.json` from that folder, then:

```bash
python3 migration/apply_drive_map.py ~/Downloads/bac_drive_map.json
git commit -am "Files moved to Google Drive" && git push
```

`apply_drive_map.py` swaps every WordPress link for its Drive link, removes
links whose file no longer exists on WordPress (the site then shows
"غير متوفر حاليا"), and writes `migration/missing_files.csv`: the papers to find
and upload by hand.

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

The visual idea is the Algerian school copybook (cahier Seyès): ruled paper and a
red margin line, exam papers in **blue ink**, solutions in **red pen**. Titles use
*Aref Ruqaa* (handwritten Ruqʿa), everything else *IBM Plex Sans Arabic*; both are
self-hosted under the SIL Open Font License. Light and dark themes follow the
device, with a toggle. Google Drive files open in an in-page viewer with
download and "open in Drive" buttons. Press `/` anywhere to search.
