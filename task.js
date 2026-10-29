// WORD FILES: upload history-geography Words next to the SE PDFs; move Islamic-sciences Words next to their PDFs and refresh their content.
const B = 'https://raw.githubusercontent.com/bacalauria/majmaa/ef58c37a2a8ad84570129849035df170322de3a9/';
const man = JSON.parse(UrlFetchApp.fetch(B + 'manifest.json').getContentText());
const props = PropertiesService.getScriptProperties();
const done = JSON.parse(props.getProperty('w2_done') || '{}');
Logger.log('ADV ' + (typeof Drive) + ' items ' + man.length + ' done ' + Object.keys(done).length);
const t0 = Date.now(); const DOCX = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document';
const folderOf = near => { const fs = near.filter(Boolean).map(i => DriveApp.getFileById(i)); const f = fs.find(x => x.getName().indexOf('_se_') >= 0) || fs[0]; return f.getParents().next(); };
for (const it of man) {
  if (done[it.path]) continue;
  if (Date.now() - t0 > 300000) { Logger.log('TIME - run again'); break; }
  const folder = folderOf(it.near);
  const blob = UrlFetchApp.fetch(B + it.path).getBlob().setContentType(DOCX);
  if (it.kind === 'hg') {
    const f = folder.createFile(blob.setName(it.name)); f.setSharing(DriveApp.Access.ANYONE_WITH_LINK, DriveApp.Permission.VIEW);
    done[it.path] = f.getId(); Logger.log('R hg ' + it.key + ' ' + it.part + ' ' + f.getId() + ' in ' + folder.getName());
  } else {
    const f = DriveApp.getFileById(it.id); f.moveTo(folder);
    let how = 'moved';
    if (typeof Drive !== 'undefined') { Drive.Files.update({}, it.id, blob.setName(f.getName())); how += '+content'; }
    done[it.path] = it.id + ' ' + how; Logger.log('R isl ' + it.key + ' ' + it.part + ' ' + it.id + ' ' + how + ' in ' + folder.getName());
  }
  props.setProperty('w2_done', JSON.stringify(done));
}
Logger.log('DONE ' + Object.keys(done).length + '/' + man.length);
