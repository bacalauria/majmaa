// RESTORE: the foreign-languages 2016 second-session history-geography paper + solution are needed; put them next to that stream's 2016 PDFs.
const ref = DriveApp.getFileById('1pfyBUA4b09SVJYjDTAbZRJxrChjG6r9x'); const folder = ref.getParents().next();
[['1JjXppEomZjZ6W2ACfusRJ5-3JJtWWMUp', 'bac_2016_le_HGeo-2.pdf'], ['1tWAn49Zz8z33tiuEyg_oYX8z7ePnV-_G', 'bac_2016_le_HGeo-2_s.pdf']].forEach(([id, name]) => {
  const f = DriveApp.getFileById(id); f.setTrashed(false); f.moveTo(folder); f.setName(name);
  f.setSharing(DriveApp.Access.ANYONE_WITH_LINK, DriveApp.Permission.VIEW);
  Logger.log('RESTORED ' + name + ' ' + id + ' in ' + folder.getName() + ' (ref ' + ref.getName() + ')');
});
