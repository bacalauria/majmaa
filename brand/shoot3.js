// Renders brand/build3/*.html (made by make3.py) to brand/out3/*.png with Chromium.
const { chromium } = require('playwright'); const path = require('path'); const fs = require('fs');
const dir = path.join(__dirname, 'build3'), out = path.join(__dirname, 'out3'); fs.mkdirSync(out, { recursive: true });
const sizes = JSON.parse(fs.readFileSync(path.join(dir, 'sizes.json')));
(async () => { const b = await chromium.launch();
  for (const [n, [w, h, transp]] of Object.entries(sizes)) {
    const p = await b.newPage({ viewport: { width: w, height: h } });
    await p.goto('file://' + path.join(dir, n + '.html')); await p.evaluate(() => document.fonts.ready); await p.waitForTimeout(300);
    await p.screenshot({ path: path.join(out, n + '.png'), omitBackground: !!transp }); await p.close(); }
  await b.close(); })();
