/**
 * مجمع البكالوريا — move every file still hosted on WordPress into Google Drive.
 * ===========================================================================
 *
 * WHERE IT RUNS
 *   Google Apps Script, inside the bacalauria@gmail.com account
 *   (script.google.com → New project → paste this file). It downloads each file
 *   from WordPress with UrlFetchApp and saves it with DriveApp, so no API key,
 *   OAuth client or local install is needed.
 *
 * WHAT IT DOES
 *   1. Reads bac_migration_manifest.json (upload it to your Drive first, any
 *      folder). Each job = { url, alt[], folder[], name, optional? }.
 *   2. Creates  "مجمع البكالوريا - أرشيف / <النظام> / <الشعبة> / <السنة>"
 *      and saves each file there under a clean name, e.g. BAC2012_mt_math_sujet.pdf.
 *   3. Shares every file "anyone with the link can view" (same as the recent years).
 *   4. Downloads in parallel batches (UrlFetchApp.fetchAll); when a URL fails it
 *      tries the alternative addresses listed in the manifest.
 *   5. Works in ~4.5-minute slices (the Apps Script limit is 6 min) and schedules
 *      itself to continue one minute later until everything is done. Progress is
 *      saved after every batch in bac_migration_state.json, so it is safe to stop
 *      and re-run at any time: finished files are never downloaded twice.
 *   6. At the end writes bac_drive_map.json (old URL → Drive file id) next to the
 *      archive and emails you a summary. Give that file to apply_drive_map.py
 *      to rewrite the website's links.
 *
 * HOW TO RUN
 *   ▸ Select the function  start  in the toolbar and press Run. Accept the
 *     permissions (Drive, external requests, triggers, send email to yourself).
 *   ▸ Close the tab. It continues by itself. Run  status  any time to see progress.
 *   ▸ To restart from zero: run  resetEverything  (does NOT delete Drive files).
 */

const CONFIG = {
  MANIFEST_NAME: 'bac_migration_manifest.json',
  MANIFEST_URL: '',                   // optional: raw URL of the manifest instead of a Drive file
  STATE_NAME: 'bac_migration_state.json',
  MAP_NAME: 'bac_drive_map.json',
  INCLUDE_OPTIONAL: true,             // also move BAC papers in the media library that no page links to
  BATCH: 12,                          // parallel downloads per round
  MAX_TRIES: 3,                       // runs a failing file is retried before it is reported missing
  TIME_BUDGET_MS: 4.5 * 60 * 1000,
  SHARE_PUBLIC: true,
  EMAIL_SUMMARY: true,
};

/* ------------------------------------------------------------ entry points */

function start() {
  deleteRunTriggers_();
  run();
}

function run() {
  const lock = LockService.getScriptLock();
  if (!lock.tryLock(1000)) { Logger.log('Another run is in progress.'); return; }
  const t0 = Date.now();
  try {
    const manifest = loadManifest_();
    const root = getOrCreateRoot_(manifest.root_folder);
    const st = loadState_(root);
    const jobs = manifest.jobs.filter(j => CONFIG.INCLUDE_OPTIONAL || !j.optional);
    let pending = jobs.filter(j => !st.done[j.url] && (st.failed[j.url] || { tries: 0 }).tries < CONFIG.MAX_TRIES);
    Logger.log(`${jobs.length} jobs, ${Object.keys(st.done).length} done, ${pending.length} pending`);

    while (pending.length && Date.now() - t0 < CONFIG.TIME_BUDGET_MS) {
      const batch = pending.splice(0, CONFIG.BATCH);
      processBatch_(batch, root, st);
      saveState_(root, st);
    }

    pending = jobs.filter(j => !st.done[j.url] && (st.failed[j.url] || { tries: 0 }).tries < CONFIG.MAX_TRIES);
    deleteRunTriggers_();
    if (pending.length) {
      ScriptApp.newTrigger('run').timeBased().after(60 * 1000).create();
      Logger.log(`Paused with ${pending.length} left — continuing automatically in 1 minute.`);
    } else {
      finish_(root, st, jobs);
    }
  } finally {
    lock.releaseLock();
  }
}

function status() {
  const manifest = loadManifest_();
  const root = getOrCreateRoot_(manifest.root_folder);
  const st = loadState_(root);
  const total = manifest.jobs.filter(j => CONFIG.INCLUDE_OPTIONAL || !j.optional).length;
  const done = Object.keys(st.done).length;
  const failed = Object.values(st.failed).filter(f => f.tries >= CONFIG.MAX_TRIES).length;
  Logger.log(`Done ${done} / ${total}  (${Math.round(100 * done / total)}%) — missing after ${CONFIG.MAX_TRIES} tries: ${failed}`);
  Logger.log(`Scheduled continuation: ${ScriptApp.getProjectTriggers().some(t => t.getHandlerFunction() === 'run') ? 'yes' : 'no'}`);
}

/** Forget progress (Drive files stay). Use only to start over. */
function resetEverything() {
  deleteRunTriggers_();
  const manifest = loadManifest_();
  const root = getOrCreateRoot_(manifest.root_folder);
  const it = root.getFilesByName(CONFIG.STATE_NAME);
  while (it.hasNext()) it.next().setTrashed(true);
  Logger.log('State cleared.');
}

/* --------------------------------------------------------------- the work */

function processBatch_(batch, root, st) {
  // Each job walks through [url, ...alt] until one answer is a real file.
  let todo = batch.map(j => ({ job: j, candidates: [j.url].concat(j.alt || []), lastCode: null }));
  while (todo.length) {
    const reqs = todo.map(t => ({ url: t.candidates[0], muteHttpExceptions: true, followRedirects: true }));
    let resps;
    try { resps = UrlFetchApp.fetchAll(reqs); }
    catch (e) {             // one bad host can throw for the whole batch: fall back to one by one
      resps = reqs.map(r => { try { return UrlFetchApp.fetch(r.url, r); } catch (err) { return null; } });
    }
    const next = [];
    todo.forEach((t, i) => {
      const r = resps[i];
      const code = r ? r.getResponseCode() : 0;
      if (r && code === 200 && looksLikeFile_(r, t.job.name)) {
        try {
          saveFile_(t.job, r.getBlob(), t.candidates[0], root, st);
        } catch (e) {
          markFailed_(st, t.job, 'drive: ' + e.message);
        }
        return;
      }
      t.lastCode = code;
      t.candidates.shift();
      if (t.candidates.length) next.push(t);
      else markFailed_(st, t.job, 'http ' + code);
    });
    todo = next;
  }
}

function looksLikeFile_(resp, name) {
  const type = String(resp.getHeaders()['Content-Type'] || resp.getHeaders()['content-type'] || '');
  if (/text\/html/i.test(type)) return false;                 // WordPress "not found" pages
  const bytes = resp.getContent();
  if (bytes.length < 512) return false;
  if (/\.pdf$/i.test(name)) return bytes[0] === 0x25 && bytes[1] === 0x50;   // "%P" of %PDF
  return true;
}

function saveFile_(job, blob, fromUrl, root, st) {
  const folder = getOrCreatePath_(root, job.folder, st);
  let file;
  const existing = folder.getFilesByName(job.name);   // crash-safe: reuse a copy saved by an interrupted run
  if (existing.hasNext()) file = existing.next();
  else {
    file = folder.createFile(blob.setName(job.name));
    file.setDescription('مجمع البكالوريا — نقل من ' + job.url);
  }
  if (CONFIG.SHARE_PUBLIC) {
    try { file.setSharing(DriveApp.Access.ANYONE_WITH_LINK, DriveApp.Permission.VIEW); } catch (e) { /* inherited from root folder */ }
  }
  st.done[job.url] = { id: file.getId(), from: fromUrl === job.url ? undefined : fromUrl };
  delete st.failed[job.url];
}

function markFailed_(st, job, why) {
  const f = st.failed[job.url] || { tries: 0 };
  f.tries += 1; f.why = why;
  st.failed[job.url] = f;
}

function finish_(root, st, jobs) {
  const files = {}, missing = {};
  jobs.forEach(j => {
    if (st.done[j.url]) files[j.url] = st.done[j.url].id;
    else missing[j.url] = (st.failed[j.url] || {}).why || 'not attempted';
  });
  const out = JSON.stringify({ generated: new Date().toISOString(), root_folder_id: root.getId(),
                               files: files, missing: missing }, null, 1);
  const it = root.getFilesByName(CONFIG.MAP_NAME);
  if (it.hasNext()) it.next().setContent(out); else root.createFile(CONFIG.MAP_NAME, out, 'application/json');
  const msg = `Migration finished.\nMoved: ${Object.keys(files).length}\nNot found on WordPress: ${Object.keys(missing).length}\n` +
              `Archive folder: ${root.getUrl()}\nMap file: ${CONFIG.MAP_NAME} (inside that folder)`;
  Logger.log(msg);
  if (CONFIG.EMAIL_SUMMARY) {
    try { MailApp.sendEmail(Session.getEffectiveUser().getEmail(), 'مجمع البكالوريا — انتهى نقل الملفات إلى Drive', msg); } catch (e) {}
  }
}

/* --------------------------------------------------------------- helpers */

function loadManifest_() {
  let text;
  const it = DriveApp.getFilesByName(CONFIG.MANIFEST_NAME);
  if (it.hasNext()) text = it.next().getBlob().getDataAsString('UTF-8');
  else if (CONFIG.MANIFEST_URL) text = UrlFetchApp.fetch(CONFIG.MANIFEST_URL).getContentText('UTF-8');
  else throw new Error(`Upload ${CONFIG.MANIFEST_NAME} to Google Drive first (or set CONFIG.MANIFEST_URL).`);
  return JSON.parse(text);
}

function getOrCreateRoot_(name) {
  const it = DriveApp.getRootFolder().getFoldersByName(name);
  if (it.hasNext()) return it.next();
  const f = DriveApp.getRootFolder().createFolder(name);
  if (CONFIG.SHARE_PUBLIC) f.setSharing(DriveApp.Access.ANYONE_WITH_LINK, DriveApp.Permission.VIEW);
  return f;
}

function getOrCreatePath_(root, parts, st) {
  const key = parts.join('/');
  if (st.folders[key]) {
    try { return DriveApp.getFolderById(st.folders[key]); } catch (e) { delete st.folders[key]; }
  }
  let f = root;
  parts.forEach(p => {
    const it = f.getFoldersByName(p);
    f = it.hasNext() ? it.next() : f.createFolder(p);
  });
  st.folders[key] = f.getId();
  return f;
}

function loadState_(root) {
  const it = root.getFilesByName(CONFIG.STATE_NAME);
  if (it.hasNext()) {
    const s = JSON.parse(it.next().getBlob().getDataAsString('UTF-8'));
    s.done = s.done || {}; s.failed = s.failed || {}; s.folders = s.folders || {};
    return s;
  }
  return { done: {}, failed: {}, folders: {} };
}

function saveState_(root, st) {
  const text = JSON.stringify(st);
  const it = root.getFilesByName(CONFIG.STATE_NAME);
  if (it.hasNext()) it.next().setContent(text); else root.createFile(CONFIG.STATE_NAME, text, 'application/json');
}

function deleteRunTriggers_() {
  ScriptApp.getProjectTriggers().filter(t => t.getHandlerFunction() === 'run').forEach(t => ScriptApp.deleteTrigger(t));
}
