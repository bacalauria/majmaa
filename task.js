// AUDIT 4: unknown WordPress leftovers -> any same-size file of the same year anywhere in My Drive.
const L = { 'bac_2008_m_phisiq.pdf': 2008, 'bac_2004_snv_anglais10578.pdf': 2004, 'bac_2002_se_francais10562.pdf': 2002, 'bac_2002_se_anglais10558.pdf': 2002,
  'bac_2003_se_physiq_s1.pdf': 2003, 'bac_2003_se_physiq_s2.pdf': 2003, 'bac_2010_se_science2.pdf': 2010, 'bac_2010_se_science2_s.pdf': 2010,
  'bac_2010_se_phisiq2.pdf': 2010, 'bac_2010_se_phisiq2_s.pdf': 2010, 'bac_2009_mt_gmeth_s1.pdf': 2009, 'bac_2010_mt_gmeth_s1.pdf': 2010, 'bac_physiq_ser1.pdf': 0 };
const LEFT = '1L0ODN92kuQp9liGCrdyNydOgY1Ka3S6o';
const lf = DriveApp.getFolderById(LEFT);
const sizes = {}; const it0 = lf.getFiles(); while (it0.hasNext()) { const f = it0.next(); if (L[f.getName()] !== undefined) sizes[f.getName()] = f.getSize(); }
const years = [...new Set(Object.values(L))].filter(Boolean);
const byYear = {};
years.forEach(y => { const out = []; const it = DriveApp.searchFiles("title contains 'bac_" + y + "_' and trashed = false");
  while (it.hasNext()) { const f = it.next(); const p = f.getParents(); const par = p.hasNext() ? p.next() : null; if (par && par.getId() === LEFT) continue;
    out.push([f.getName(), f.getSize(), par ? par.getName() : '']); } byYear[y] = out; Logger.log('YEAR ' + y + ' files ' + out.length); });
Object.keys(L).forEach(n => { const y = L[n], s = sizes[n]; const pool = y ? byYear[y] : [].concat(...Object.values(byYear));
  const same = pool.filter(x => x[1] === s).map(x => x[0] + '@' + x[2]);
  const near = pool.filter(x => Math.abs(x[1] - s) < s * 0.02 && x[1] !== s).map(x => x[0] + '@' + x[2] + ':' + x[1]);
  Logger.log('U ' + n + ' ' + s + ' SAME[' + same.join(', ') + '] NEAR[' + near.slice(0, 6).join(', ') + ']'); });
