/**
 * مجمع البكالوريا — WordPress → Google Drive migration (runs inside bacalauria@gmail.com).
 *
 * MANIFEST (constant at the end of the project) is a compact list:
 *   D <TAB> <folder path under "بكالوريا الجزائر">|<file code>|<year>
 *   <token> <TAB> <url or path under baccalauria.wordpress.com/wp-content/uploads/>
 *   =<raw file name> <TAB> <url>            (files kept under their original name)
 * Each token becomes  bac_<year>_<code>_<token>.pdf  — the naming already used in Drive
 * (e.g. bac_2012_m_Math_s.pdf), inside  بكالوريا الجزائر/<النظام>/<الشعبة>/<السنة>.
 *
 * migrate_run(): downloads in parallel batches (UrlFetchApp.fetchAll), tries alternative
 * WordPress hosts when a URL fails, saves each file, shares it "anyone with the link can
 * view" (like the existing 2018+ files), records progress in majmaa_migration_state.json,
 * and re-schedules itself every minute until done. Idempotent: a file already present
 * under the target name — or under the old local name (Math.pdf) — is reused, not re-uploaded.
 * At the end it writes majmaa_drive_map.json  { url: driveFileId }  in My Drive.
 */
const MIG = { ROOT: 'بكالوريا الجزائر', STATE: 'majmaa_migration_state.json', MAP: 'majmaa_drive_map.json',
              BATCH: 15, MAX_TRIES: 3, BUDGET_MS: 4.4 * 60 * 1000,
              WP: 'https://baccalauria.wordpress.com/wp-content/uploads/' };

function migrate_jobs_() {
  const jobs = []; let cur = null;
  MANIFEST.split('\n').forEach(line => {
    if (!line.trim()) return;
    const [a, b] = line.split('\t');
    if (a === 'D') { const [path, code, year, pre] = b.split('|'); cur = { path: path.split('/'), code, year, pre: pre || '' }; return; }
    const tail = cur.pre + b;                                   // each folder group shares a URL prefix
    const url = /^https?:/.test(tail) ? tail : MIG.WP + tail;
    const name = a[0] === '=' ? a.slice(1) : 'bac_' + cur.year + '_' + cur.code + '_' + a + '.pdf';
    const legacy = a[0] === '=' ? null : a + '.pdf';
    jobs.push({ url, name, legacy, folder: cur.path });
  });
  return jobs;
}

function migrate_alts_(u) {
  const out = [];
  let m = u.match(/^https:\/\/([\w-]+)\.wordpress\.com\/wp-content\/uploads\/(.+)$/);
  if (m) out.push('https://' + m[1] + '.files.wordpress.com/' + m[2]);
  m = u.match(/^https?:\/\/([\w-]+)\.files\.wordpress\.com\/(.+)$/);
  if (m) {
    out.push('https://' + m[1] + '.wordpress.com/wp-content/uploads/' + m[2]);
    if (m[1] !== 'baccalauria') out.push(MIG.WP + m[2], 'https://baccalauria.files.wordpress.com/' + m[2]);
  }
  return out.filter(x => x !== u);
}

function migrate_run() {
  const lock = LockService.getScriptLock();
  if (!lock.tryLock(1000)) return;
  const t0 = Date.now();
  try {
    const jobs = migrate_jobs_();
    const root = DriveApp.getRootFolder().getFoldersByName(MIG.ROOT).next();
    const st = JSON.parse(readText_(MIG.STATE) || '{"done":{},"failed":{},"folders":{}}');
    const pendingOf = () => jobs.filter(j => !st.done[j.url] && (st.failed[j.url] || { tries: 0 }).tries < MIG.MAX_TRIES);
    let pending = pendingOf();
    while (pending.length && Date.now() - t0 < MIG.BUDGET_MS) {
      migrate_batch_(pending.splice(0, MIG.BATCH), root, st);
      writeText_(MIG.STATE, JSON.stringify(st));
    }
    pending = pendingOf();
    ScriptApp.getProjectTriggers().filter(t => t.getHandlerFunction() === 'migrate_run').forEach(t => ScriptApp.deleteTrigger(t));
    if (pending.length) {
      ScriptApp.newTrigger('migrate_run').timeBased().after(60 * 1000).create();
      Logger.log('MIGRATE progress ' + Object.keys(st.done).length + '/' + jobs.length + ', left ' + pending.length);
    } else {
      const files = {}, missing = {};
      jobs.forEach(j => { if (st.done[j.url]) files[j.url] = st.done[j.url]; else missing[j.url] = (st.failed[j.url] || {}).why || '?'; });
      writeText_(MIG.MAP, JSON.stringify({ files, missing }));
      Logger.log('MIGRATE DONE moved ' + Object.keys(files).length + ', missing ' + Object.keys(missing).length);
      try { MailApp.sendEmail(Session.getEffectiveUser().getEmail(), 'مجمع البكالوريا — انتهى نقل الملفات إلى Drive',
            'Moved: ' + Object.keys(files).length + '\nNot found on WordPress: ' + Object.keys(missing).length); } catch (e) {}
    }
  } finally { lock.releaseLock(); }
}

function migrate_batch_(batch, root, st) {
  let todo = batch.map(j => ({ job: j, cands: [j.url].concat(migrate_alts_(j.url)) }));
  // Files already in Drive (same name or old local name) are reused without downloading.
  todo = todo.filter(t => {
    const folder = migrate_folder_(root, t.job.folder, st);
    const f = migrate_existing_(folder, t.job);
    if (f) { migrate_share_(f); st.done[t.job.url] = f.getId(); return false; }
    return true;
  });
  while (todo.length) {
    const reqs = todo.map(t => ({ url: t.cands[0], muteHttpExceptions: true, followRedirects: true }));
    let resps;
    try { resps = UrlFetchApp.fetchAll(reqs); }
    catch (e) { resps = reqs.map(r => { try { return UrlFetchApp.fetch(r.url, r); } catch (err) { return null; } }); }
    const next = [];
    todo.forEach((t, i) => {
      const r = resps[i], code = r ? r.getResponseCode() : 0;
      if (r && code === 200 && migrate_isfile_(r, t.job.name)) {
        try {
          const folder = migrate_folder_(root, t.job.folder, st);
          const f = folder.createFile(r.getBlob().setName(t.job.name));
          f.setDescription('مجمع البكالوريا — منقول من ' + t.job.url);
          migrate_share_(f);
          st.done[t.job.url] = f.getId(); delete st.failed[t.job.url];
        } catch (e) { migrate_fail_(st, t.job, 'drive ' + e.message); }
        return;
      }
      t.cands.shift();
      if (t.cands.length) next.push(t); else migrate_fail_(st, t.job, 'http ' + code);
    });
    todo = next;
  }
}

function migrate_existing_(folder, job) {
  let it = folder.getFilesByName(job.name);
  if (it.hasNext()) return it.next();
  if (job.legacy) {
    it = folder.getFilesByName(job.legacy);
    if (it.hasNext()) { const f = it.next(); f.setName(job.name); return f; }
  }
  return null;
}
function migrate_isfile_(resp, name) {
  const h = resp.getHeaders(), type = String(h['Content-Type'] || h['content-type'] || '');
  if (/text\/html/i.test(type)) return false;
  const b = resp.getContent();
  if (b.length < 512) return false;
  return /\.pdf$/i.test(name) ? (b[0] === 0x25 && b[1] === 0x50) : true;
}
function migrate_share_(f) { try { f.setSharing(DriveApp.Access.ANYONE_WITH_LINK, DriveApp.Permission.VIEW); } catch (e) {} }
function migrate_fail_(st, job, why) { const f = st.failed[job.url] || { tries: 0 }; f.tries++; f.why = why; st.failed[job.url] = f; }
function migrate_folder_(root, parts, st) {
  const key = parts.join('/');
  if (st.folders[key]) { try { return DriveApp.getFolderById(st.folders[key]); } catch (e) {} }
  let f = root;
  parts.forEach(p => { const it = f.getFoldersByName(p); f = it.hasNext() ? it.next() : f.createFolder(p); });
  st.folders[key] = f.getId();
  return f;
}
function migrate_status() {
  const st = JSON.parse(readText_(MIG.STATE) || '{"done":{},"failed":{}}');
  Logger.log('STATUS done ' + Object.keys(st.done).length + ' failed ' + Object.keys(st.failed).length +
             ' triggers ' + ScriptApp.getProjectTriggers().map(t => t.getHandlerFunction()).join(','));
}
