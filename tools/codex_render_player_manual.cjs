const path = require('path');
const {pathToFileURL} = require('url');
const {chromium} = require(path.join(process.env.USERPROFILE, '.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright-core'));
(async () => {
  const browser = await chromium.launch({channel: 'msedge', headless: true});
  try {
    const page = await browser.newPage();
    for (const lang of ['EN', 'ES']) {
      const base = path.join(__dirname, 'installer/payload/manual', `BT3-TagTeam-Manual-${lang}`);
      await page.goto(pathToFileURL(base + '.html').href);
      await page.pdf({path: base + '.pdf', format: 'A4', printBackground: true,
        preferCSSPageSize: true, displayHeaderFooter: true,
        headerTemplate: '<div></div>',
        footerTemplate: '<div style="font-family:Arial;font-size:8px;width:100%;text-align:center;color:#556070">BT3 Tag Team · Real Power Scale &nbsp; <span class="pageNumber"></span> / <span class="totalPages"></span></div>'});
    }
  } finally { await browser.close(); }
})().catch(e => {console.error(e); process.exitCode = 1;});
