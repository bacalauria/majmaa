// DELETE: the 2010 SE blind-candidate papers (Kamel: not needed).
['1Y_hkVKcbP9e7fzX7cTBzTxBjqLQg19xX', '1j15Ywe0YhmOIdbW3juRwqAYr3cNOs4qs', '1rLqEnSFiO8badC3Gikt-CTVs2mnjo3mK', '1w9wjejWQfuPL3Ye-gMXZGOX5N4_VebyE'].forEach(id => {
  const f = DriveApp.getFileById(id); f.setTrashed(true); Logger.log('TRASHED ' + f.getName()); });
