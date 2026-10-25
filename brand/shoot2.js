const { chromium } = require('playwright'); const path = require('path');
const sizes = { 'logo-icon': [1024,1024], avatar: [800,800], 'logo-wordmark': [1400,900,true], 'logo-wordmark-dark': [1400,900], 'youtube-banner': [2560,1440], 'facebook-cover': [1640,624], 'og-image': [1200,630] };
(async () => { const b = await chromium.launch();
  for (const [n, [w, h, transp]] of Object.entries(sizes)) {
    const p = await b.newPage({ viewport: { width: w, height: h } });
    await p.goto('file://' + path.resolve(n + '.html')); await p.evaluate(() => document.fonts.ready); await p.waitForTimeout(300);
    await p.screenshot({ path: `out2/${n}.png`, omitBackground: !!transp }); await p.close(); }
  await b.close(); })();
