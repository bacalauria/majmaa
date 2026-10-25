/**
 * inventory — writes majmaa_inventory.json to My Drive: every file under My Drive
 * as [path, name, id, size, mimeType]. Used to map the site to existing Drive files.
 * Resumable: if it runs out of time it saves progress and continues on the next run.
 */
function inventory() {
  const t0 = Date.now(), props = PropertiesService.getScriptProperties();
  let st = props.getProperty('inv') ? JSON.parse(readText_('majmaa_inventory_state.json') || '{"queue":[],"out":[]}') : null;
  if (!st) st = { queue: [[DriveApp.getRootFolder().getId(), '']], out: [] };
  while (st.queue.length && Date.now() - t0 < 4.5 * 60 * 1000) {
    const [fid, path] = st.queue.shift();
    const f = DriveApp.getFolderById(fid);
    const subs = f.getFolders();
    while (subs.hasNext()) { const s = subs.next(); st.queue.push([s.getId(), path + '/' + s.getName()]); st.out.push([path + '/' + s.getName(), '', s.getId(), 0, 'folder']); }
    const files = f.getFiles();
    while (files.hasNext()) { const x = files.next(); st.out.push([path, x.getName(), x.getId(), x.getSize(), x.getMimeType()]); }
  }
  if (st.queue.length) {
    writeText_('majmaa_inventory_state.json', JSON.stringify(st)); props.setProperty('inv', '1');
    ScriptApp.getProjectTriggers().filter(t => t.getHandlerFunction() === 'inventory').forEach(t => ScriptApp.deleteTrigger(t));
    ScriptApp.newTrigger('inventory').timeBased().after(60 * 1000).create();
    Logger.log('INVENTORY PARTIAL ' + st.out.length + ' entries, ' + st.queue.length + ' folders left');
  } else {
    props.deleteProperty('inv');
    const id = writeText_('majmaa_inventory.json', JSON.stringify(st.out));
    Logger.log('INVENTORY DONE ' + st.out.length + ' entries, file id ' + id);
  }
}
function readText_(name) { const it = DriveApp.getRootFolder().getFilesByName(name); return it.hasNext() ? it.next().getBlob().getDataAsString('UTF-8') : null; }
function writeText_(name, text) {
  const it = DriveApp.getRootFolder().getFilesByName(name);
  if (it.hasNext()) { const f = it.next(); f.setContent(text); return f.getId(); }
  return DriveApp.getRootFolder().createFile(name, text, 'application/json').getId();
}
