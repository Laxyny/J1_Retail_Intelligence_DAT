import { readFile, readdir, writeFile } from 'node:fs/promises';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { createRequire } from 'node:module';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '../..');
const modules = process.env.RETAIL_CODEX_MODULES;
if (!modules) throw new Error('Définir RETAIL_CODEX_MODULES avec le chemin vers node_modules du runtime Codex.');
const require = createRequire(resolve(modules, '../package.json'));
const { chromium } = require('playwright');
const folder = resolve(root, 'preuves/schemas');
const mermaidPath = process.env.RETAIL_MERMAID_JS;
const mermaidUrl = 'https://cdn.jsdelivr.net/npm/mermaid@10.9.5/dist/mermaid.min.js';
const mermaidScript = mermaidPath ? await readFile(mermaidPath,'utf8') : await fetch(mermaidUrl).then(async response => {
  if (!response.ok) throw new Error('Mermaid : HTTP '+response.status);
  return response.text();
});
const browser = await chromium.launch({ channel: 'msedge', headless: true });
try {
  const page = await browser.newPage({ viewport: { width: 1600, height: 1800 }, deviceScaleFactor: 2 });
  await page.setContent('<body style="margin:0;background:white"><main id="chart" style="display:inline-block"></main></body>');
  await page.addScriptTag({ content: mermaidScript });
  await page.evaluate(() => window.mermaid.initialize({
    startOnLoad: false,
    theme: 'base',
    securityLevel: 'loose',
    themeVariables: {
      fontFamily: 'Segoe UI, sans-serif', fontSize: '16px',
      primaryColor: '#E9F4F1', primaryTextColor: '#122840', primaryBorderColor: '#5B8B87',
      secondaryColor: '#EDF2F8', lineColor: '#487087', clusterBkg: '#F5F8FB', clusterBorder: '#9FB6C7',
      edgeLabelBackground: '#FFFFFF',
    },
    flowchart: { htmlLabels: false, nodeSpacing: 28, rankSpacing: 34, curve: 'linear', useMaxWidth: false },
  }));
  for (const file of (await readdir(folder)).filter(name => name.endsWith('.mmd')).sort()) {
    const name = file.slice(0,-4);
    const code = await readFile(resolve(folder,file),'utf8');
    const svg = await page.evaluate(async ({name,code}) => {
      const {svg} = await window.mermaid.render('fig'+name, code);
      document.getElementById('chart').innerHTML = svg;
      return svg;
    }, {name,code});
    await writeFile(resolve(folder,name+'.svg'),svg,'utf8');
    await page.locator('#chart svg').screenshot({ path: resolve(folder,name+'.png') });
    console.log(name + ' · SVG et PNG');
  }
} finally {
  await browser.close();
}
