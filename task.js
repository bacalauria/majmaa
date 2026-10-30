// WATERMARK: replace the content of the 81 HG + Islamic Word files on Drive in place (same IDs), then verify md5.
const B = 'https://raw.githubusercontent.com/bacalauria/majmaa/4b24e636ed75f67b0560a434c6c34a4aceff3275/w/';
const man = JSON.parse(UrlFetchApp.fetch(B + 'manifest.json').getContentText());
const props = PropertiesService.getScriptProperties();
const done = JSON.parse(props.getProperty('wm_done') || '{}');
const t0 = Date.now(); const DOCX = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document';
Logger.log('ADV ' + (typeof Drive) + ' items ' + man.length + ' done ' + Object.keys(done).length);
for (const it of man) {
  if (done[it.id]) continue;
  if (Date.now() - t0 > 300000) { Logger.log('TIME - run again'); break; }
  const meta = Drive.Files.get(it.id, {fields: 'name,md5Checksum,trashed'});
  if (meta.md5Checksum !== it.md5) {
    const blob = UrlFetchApp.fetch(B + it.id + '.docx').getBlob().setContentType(DOCX).setName(meta.name);
    Drive.Files.update({}, it.id, blob);
  }
  const after = Drive.Files.get(it.id, {fields: 'name,md5Checksum,trashed'});
  done[it.id] = (after.md5Checksum === it.md5 ? 'OK ' : 'MISMATCH ') + after.name + (after.trashed ? ' TRASHED' : '');
  props.setProperty('wm_done', JSON.stringify(done));
}
const vals = Object.values(done);
Logger.log('DONE ' + vals.length + '/' + man.length + ' ok ' + vals.filter(v => v.startsWith('OK')).length);
vals.filter(v => !v.startsWith('OK')).forEach(v => Logger.log('BAD ' + v));
Logger.log('NAMES ' + vals.map(v => v.split(' ')[1]).join(','));
