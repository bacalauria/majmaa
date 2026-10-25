/* مجمع البكالوريا — front-end behaviour (no framework, ~6 KB).
   1. theme toggle + mobile menu
   2. instant search over every exam row (assets/search.json, loaded on first use)
   3. in-page viewer for Google Drive files (Drive /preview embed)
   4. home: year → stream picker      5. stream page: subject filter + year rail spy */
(() => {
  'use strict';
  const $ = (s, el = document) => el.querySelector(s);
  const $$ = (s, el = document) => [...el.querySelectorAll(s)];
  const ROOT = document.body.dataset.root || './';
  const store = { get(k) { try { return localStorage.getItem(k); } catch (e) { return null; } },
                  set(k, v) { try { localStorage.setItem(k, v); } catch (e) {} } };

  /* ---------------------------------------------------------------- theme */
  const themeBtn = $('#theme');
  themeBtn && themeBtn.addEventListener('click', () => {
    const cur = document.documentElement.dataset.theme ||
      (matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
    const next = cur === 'dark' ? 'light' : 'dark';
    document.documentElement.dataset.theme = next; store.set('theme', next);
  });
  const menuBtn = $('.menubtn'), nav = $('#nav');
  menuBtn && menuBtn.addEventListener('click', () => {
    const open = nav.classList.toggle('is-open'); menuBtn.setAttribute('aria-expanded', open);
  });

  /* -------------------------------------------------------- drive helpers */
  const driveId = (u) => { const m = /\/d\/([\w-]{10,})|[?&]id=([\w-]{10,})/.exec(u || ''); return m ? (m[1] || m[2]) : null; };
  const isDrive = (u) => /(?:drive|docs)\.google\.com/.test(u || '');

  /* --------------------------------------------------------------- viewer */
  const viewer = $('#viewer'), vframe = $('#vframe');
  function openViewer(url, title) {
    const id = driveId(url);
    if (!id || !viewer || typeof viewer.showModal !== 'function') { window.open(url, '_blank', 'noopener'); return; }
    const isDoc = /docs\.google\.com\/document/.test(url);
    vframe.src = isDoc ? `https://docs.google.com/document/d/${id}/preview` : `https://drive.google.com/file/d/${id}/preview`;
    $('#vtitle').textContent = title || '';
    $('#vopen').href = url;
    $('#vdl').href = isDoc ? `https://docs.google.com/document/d/${id}/export?format=docx` : `https://drive.google.com/uc?export=download&id=${id}`;
    viewer.showModal();
  }
  function closeViewer() { viewer.close(); }
  viewer && viewer.addEventListener('close', () => { vframe.src = 'about:blank'; });
  $('#vclose') && $('#vclose').addEventListener('click', closeViewer);
  viewer && viewer.addEventListener('click', (e) => { if (e.target === viewer) closeViewer(); });

  // Any Drive link on the page opens in the viewer (ctrl/cmd-click still opens a tab).
  document.addEventListener('click', (e) => {
    const a = e.target.closest('a[href]');
    if (!a || e.ctrlKey || e.metaKey || e.shiftKey || e.button !== 0) return;
    if (document.documentElement.dataset.preview) return;   // artifact preview host blocks the Drive iframe
    if (!isDrive(a.href) || !driveId(a.href)) return;
    if (!(a.matches('.fc, [data-drive-url]'))) return;
    e.preventDefault();
    openViewer(a.href, a.dataset.title || a.textContent.trim());
  });

  /* --------------------------------------------------------------- search */
  const dlg = $('#search'), q = $('#q'), res = $('#qres'), hint = $('#qhint');
  let IDX = null, loading = null, active = -1;
  const norm = (s) => (s || '').toString()
    .replace(/[ً-ٰٟـ]/g, '')            // tashkeel, tatweel
    .replace(/[أإآٱ]/g, 'ا').replace(/ة/g, 'ه').replace(/ى/g, 'ي').replace(/ؤ/g, 'و').replace(/ئ/g, 'ي')
    .replace(/[٠-٩]/g, (d) => String(d.charCodeAt(0) - 0x0660))  // Eastern digits -> 0-9
    .toLowerCase();
  const stripAl = (w) => (w.length > 3 && w.startsWith('ال')) ? w.slice(2) : w;
  const tokens = (s) => norm(s).split(/[\s،,.\-–/]+/).filter(Boolean).filter((w) => w !== 'و' && w !== 'شعبه' && w !== 'بكالوريا' && w !== 'باك').map(stripAl);

  // Extra words people type for each stream / subject.
  const ALIAS = {
    math: 'رياضيات رياضي math m', se: 'علوم تجريبيه تجريبي sciences se', mt: 'تقني رياضي تقنى tm mt',
    ge: 'تسيير اقتصاد gestion ge', lph: 'اداب فلسفه ادبي lettres lph', lang: 'لغات اجنبيه langues lang',
    arts: 'فنون arts', sx: 'علوم دقيقه قديم', snv: 'علوم طبيعه حياه قديم', oge: 'تسيير اقتصاد قديم',
    lsi: 'اداب علوم شرعيه اسلاميه قديم', lsh: 'اداب علوم انسانيه قديم',
    // subjects
    ar: 'عربيه عربي ادب', phys: 'فيزياء فيزيائيه physique', svt: 'علوم طبيعه حياه svt', isl: 'اسلاميه اسلاميات شريعه',
    hg: 'تاريخ جغرافيا اجتماعيات', en: 'انجليزيه انجليزي english', fr: 'فرنسيه فرنسي francais', philo: 'فلسفه philo',
    tz: 'امازيغيه tamazight', compta: 'محاسبه تسيير محاسبي مالي', eco: 'اقتصاد مناجمنت', ecolaw: 'اقتصاد قانون',
    law: 'قانون', ge_el: 'كهربائيه كهرباء هندسه', ge_mec: 'ميكانيكيه ميكانيك هندسه', ge_civ: 'مدنيه هندسه',
    ge_proc: 'طرائق كيمياء هندسه', de: 'المانيه', es: 'اسبانيه', it: 'ايطاليه', shar: 'شريعه', 'arts_s': 'فنون'
  };

  function load() {
    if (IDX) return Promise.resolve(IDX);
    if (!loading) loading = fetch(ROOT + 'assets/search.json').then((r) => r.json()).then((d) => {
      d.rows.forEach((r) => {
        const st = d.streams[r[0]], sub = d.subjects[r[3]];
        r.hay = tokens([st[0], st[1], sub, ALIAS[r[0]] || '', ALIAS[r[3]] || '', d.sessions[r[2]] || ''].join(' '));
        r.year = String(r[1]);
      });
      IDX = d; return d;
    });
    return loading;
  }
  function match(r, toks) {
    let score = 0;
    for (const t of toks) {
      if (/^\d{4}$/.test(t)) { if (r.year !== t) return -1; score += 3; continue; }
      if (/^\d{2}$/.test(t)) { if (!r.year.endsWith(t)) return -1; score += 1; continue; }
      let hit = 0;
      for (const h of r.hay) { if (h === t) { hit = 3; break; } if (h.startsWith(t)) hit = Math.max(hit, t.length >= 3 ? 2 : 1); }
      if (!hit) return -1; score += hit;
    }
    return score + r[1] / 10000;   // newer first on ties
  }
  const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  const ICON = { PDF: '<svg viewBox="0 0 24 24"><use href="#i-pdf"/></svg>', Word: 'W', FR: 'FR' };
  const LBL = { PDF: 'PDF', Word: 'Word', FR: 'ع/ف' };
  function fileLinks(list, title) {
    return list.map(([kind, url]) => `<a class="fc fc--${kind === 'Word' ? 'word' : kind === 'FR' ? 'fr' : 'pdf'}" href="${esc(url)}" target="_blank" rel="noopener" data-title="${esc(title)}"><i aria-hidden="true">${ICON[kind] || ICON.PDF}</i><span>${LBL[kind] || esc(kind)}</span></a>`).join('');
  }
  function run() {
    const toks = tokens(q.value);
    if (!toks.length) { res.innerHTML = ''; hint.hidden = false; hint.textContent = 'اكتب المادة أو السنة أو الشعبة، أو كلها معا.'; return; }
    load().then((d) => {
      const out = [];
      for (const r of d.rows) { const s = match(r, toks); if (s >= 0) out.push([s, r]); }
      out.sort((a, b) => b[0] - a[0]);
      const top = out.slice(0, 40);
      hint.hidden = top.length > 0;
      if (!top.length) hint.textContent = 'لا توجد نتائج. جرب كلمة أقصر، مثل «فيزياء 2015».';
      res.innerHTML = top.map(([, r]) => {
        const st = d.streams[r[0]], sub = d.subjects[r[3]], sess = d.sessions[r[2]];
        const ctx = `بكالوريا ${r[1]}${sess ? ' ' + sess : ''} — ${st[0]}`;
        const anchor = `y${r[1]}${r[2] === 'main' ? '' : '-' + r[2]}`;
        const t = sub + ' — ' + ctx;
        return `<li><span class="sr__main" style="--h:${d.hues[r[3]] || 235}"><b class="dot" aria-hidden="true"></b><span class="sr__txt"><span class="sr__subject">${esc(sub)}</span><span class="sr__ctx"><a href="${ROOT}bac/${r[0]}/#${anchor}">${esc(ctx)}</a></span></span></span>` +
          `<span class="sr__files">${r[4].length ? '<span class="sr__lbl">الموضوع</span>' + fileLinks(r[4], t + ' — الموضوع') : ''}` +
          `<span class="sr__files sr__sol">${r[5].length ? '<span class="sr__lbl">الحل</span>' + fileLinks(r[5], t + ' — الحل') : ''}</span>` +
          `${r[6] ? `<a class="vb" href="${esc(r[6])}" target="_blank" rel="noopener"><svg viewBox="0 0 24 24" aria-hidden="true"><use href="#i-play"/></svg><span>فيديو</span></a>` : ''}</span></li>`;
      }).join('');
      active = -1;
    });
  }
  function openSearch() {
    if (!dlg || typeof dlg.showModal !== 'function') return;
    dlg.showModal(); q.focus(); q.select(); load();
  }
  $$('[data-open-search]').forEach((b) => b.addEventListener('click', openSearch));
  q && q.addEventListener('input', run);
  dlg && dlg.addEventListener('click', (e) => { if (e.target === dlg) dlg.close(); });
  q && q.addEventListener('keydown', (e) => {
    const items = $$('li', res); if (!items.length) return;
    if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
      e.preventDefault(); active = (active + (e.key === 'ArrowDown' ? 1 : -1) + items.length) % items.length;
      items.forEach((li, i) => li.classList.toggle('is-active', i === active)); items[active].scrollIntoView({ block: 'nearest' });
    } else if (e.key === 'Enter' && active >= 0) {
      e.preventDefault(); const a = $('.fc', items[active]) || $('a', items[active]); a && a.click();
    }
  });
  document.addEventListener('keydown', (e) => {
    if (e.key === '/' && !/input|textarea|select/i.test(document.activeElement.tagName) && !(dlg && dlg.open)) { e.preventDefault(); openSearch(); }
    if ((e.key === 'k' || e.key === 'K') && (e.metaKey || e.ctrlKey)) { e.preventDefault(); openSearch(); }
  });
  const urlQ = new URLSearchParams(location.search).get('q');
  if (urlQ && q) { openSearch(); q.value = urlQ; run(); }

  /* --------------------------------------------- home: year -> stream picker */
  const yp = $('#yearpick');
  if (yp) {
    const label = $('#pick-year-label');
    const apply = (btn) => {
      $$('.year', yp).forEach((b) => { const on = b === btn; b.classList.toggle('is-on', on); b.setAttribute('aria-checked', on); });
      const y = btn.dataset.year, avail = new Set(btn.dataset.streams.split(' '));
      label.textContent = 'بكالوريا ' + y;
      $$('.picker .tile').forEach((t) => {
        const ok = avail.has(t.dataset.stream);
        t.classList.toggle('is-off', !ok); t.setAttribute('aria-disabled', !ok);
        const base = t.getAttribute('href').split('#')[0];
        t.setAttribute('href', ok ? base + '#y' + y : base);
        if (!ok) t.setAttribute('tabindex', '-1'); else t.removeAttribute('tabindex');
      });
      $$('.picker .system').forEach((sys) => {
        const none = !$$('.tile', sys).some((t) => !t.classList.contains('is-off'));
        sys.classList.toggle('is-off', none); $('.system__off', sys).hidden = !none;
      });
    };
    yp.addEventListener('click', (e) => { const b = e.target.closest('.year'); if (b) apply(b); });
    yp.addEventListener('keydown', (e) => {
      if (!['ArrowLeft', 'ArrowRight'].includes(e.key)) return;
      const bs = $$('.year', yp), i = bs.indexOf(document.activeElement); if (i < 0) return;
      const n = bs[(i + (e.key === 'ArrowLeft' ? 1 : -1) + bs.length) % bs.length]; n.focus(); apply(n); e.preventDefault();
    });
    apply($('.year.is-on', yp));
  }

  /* ----------------------------------------- stream page: subject filter */
  const filter = $('.filter');
  if (filter) {
    const sheets = $$('.sheet'), railLinks = $$('.rail a');
    const set = (subj) => {
      $$('.chip', filter).forEach((c) => { const on = c.dataset.subject === subj; c.classList.toggle('is-on', on); c.setAttribute('aria-pressed', on); });
      sheets.forEach((sh) => {
        let n = 0;
        let last = null;
        $$('.xr', sh).forEach((r) => { const show = subj === '*' || r.dataset.subject === subj; r.hidden = !show; n += show; r.classList.remove('is-last'); if (show) last = r; });
        if (last) last.classList.add('is-last');
        $('.sheet__empty', sh).hidden = n > 0;
        sh.classList.toggle('is-empty', n === 0);
      });
      store.set('subj:' + location.pathname, subj);
    };
    filter.addEventListener('click', (e) => { const c = e.target.closest('.chip'); if (c) set(c.dataset.subject); });
    const saved = store.get('subj:' + location.pathname);
    if (saved && $(`.chip[data-subject="${saved}"]`, filter)) set(saved);

    // Rail scroll-spy
    if ('IntersectionObserver' in window && railLinks.length) {
      const byId = Object.fromEntries(railLinks.map((a) => [a.dataset.anchor, a]));
      const vis = new Map();
      const io = new IntersectionObserver((ents) => {
        ents.forEach((en) => vis.set(en.target.id, en.isIntersecting ? en.boundingClientRect.top : null));
        let best = null, bestTop = Infinity;
        for (const [id, top] of vis) if (top !== null && Math.abs(top) < bestTop) { best = id; bestTop = Math.abs(top); }
        if (!best) return;
        railLinks.forEach((a) => a.classList.remove('is-current'));
        const a = byId[best]; if (a) { a.classList.add('is-current'); a.scrollIntoView({ block: 'nearest', inline: 'nearest' }); }
      }, { rootMargin: '-90px 0px -55% 0px' });
      sheets.forEach((s) => io.observe(s));
    }
  }
})();
