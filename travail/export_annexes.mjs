import { writeFile, mkdir } from 'node:fs/promises';
import { spawnSync } from 'node:child_process';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { SpreadsheetFile, Workbook } from '@oai/artifact-tool';

const here = dirname(fileURLToPath(import.meta.url));
const root = resolve(here, '..');
const python = process.env.RETAIL_PYTHON;
if (!python) throw new Error('Définir RETAIL_PYTHON avec le chemin de Python.');
const out = spawnSync(python, [resolve(root,'preuves/scripts/donnees_annexes.py')], {
  encoding: 'utf8', maxBuffer: 4_000_000, env: { ...process.env, PYTHONIOENCODING: 'utf-8' },
});
if (out.status !== 0) throw new Error(out.stderr);
const annexes = JSON.parse(out.stdout);
const requested = new Set(process.argv.slice(2));
for (const name of requested) {
  if (!(name in annexes)) throw new Error('Annexe inconnue : '+name);
}
const previews = resolve(here,'verification_visuelle','classeurs');
await mkdir(previews,{recursive:true});

function letter(index) {
  return String.fromCharCode(65+index);
}

function addSheet(workbook, spec, index) {
  const sheet = workbook.worksheets.add(spec.name);
  const last = letter(spec.headers.length-1);
  const end = spec.rows.length+4;
  const body = sheet.getRange('A5:'+last+end);
  const header = sheet.getRange('A4:'+last+'4');
  const used = sheet.getRange('A1:'+last+end);
  sheet.showGridLines = false;
  sheet.tabColor = index===0 ? '#086F69' : '#40627E';
  used.format.font.name = 'Arial';
  used.format.font.size = 10;
  used.format.font.color = '#21394D';
  used.format.verticalAlignment = 'center';
  sheet.getRange('A1').values = [[spec.name]];
  sheet.getRange('A1').format.font.size = 15;
  sheet.getRange('A1').format.font.bold = true;
  sheet.getRange('A1').format.font.color = '#102A43';
  sheet.getRange('A1:'+last+'1').format.rowHeightPx = 33;
  sheet.getRange('A2').values = [[spec.source]];
  sheet.getRange('A2').format.font.italic = true;
  sheet.getRange('A2').format.font.color = '#49627A';
  sheet.getRange('A2:'+last+'2').format.rowHeightPx = 23;
  header.values = [spec.headers];
  body.values = spec.rows;
  const table = sheet.tables.add('A4:'+last+end, true, 'Donnees'+(index+1));
  table.style = 'TableStyleMedium2';
  header.format.fill = '#102A43';
  header.format.font.color = '#FFFFFF';
  header.format.font.bold = true;
  header.format.wrapText = true;
  header.format.horizontalAlignment = 'center';
  header.format.rowHeightPx = 34;
  body.format.wrapText = true;
  for (const [col,width] of spec.widths.entries()) {
    const l = letter(col);
    sheet.getRange(l+'1:'+l+end).format.columnWidthPx = width;
    if (spec.rows.some(row => typeof row[col] === 'number')) {
      sheet.getRange(l+'5:'+l+end).setNumberFormat(spec.decimals[col] ?? '#,##0');
    }
  }
  for (const [row,cells] of spec.rows.entries()) {
    const lines = Math.max(1, ...cells.map((v,col) => (
      typeof v === 'string' ? Math.ceil(v.length/Math.max(8,Math.floor((spec.widths[col]-20)/6.8))) : 1
    )));
    sheet.getRange('A'+(row+5)+':'+last+(row+5)).format.rowHeightPx = Math.max(24,lines*17+7);
  }
  for (const [row,formats] of (spec.rowFormats ?? []).entries()) {
    for (const [col,format] of Object.entries(formats)) {
      sheet.getCell(row+4,Number(col)).setNumberFormat(format);
    }
  }
  sheet.freezePanes.freezeRows(4);
  return { name: spec.name, last, end };
}

for (const [filename,specs] of Object.entries(annexes)) {
  if (requested.size && !requested.has(filename)) continue;
  const wb = Workbook.create();
  const sheets = specs.map((spec,index) => addSheet(wb,spec,index));
  wb.recalculate();
  for (const sheet of sheets) {
    const range = 'A1:'+sheet.last+Math.min(7,sheet.end);
    const check = await wb.inspect({kind:'region',sheetId:sheet.name,range,tableMaxRows:6,tableMaxCols:7,maxChars:600});
    if (!check.ndjson) throw new Error('Aperçu vide : '+sheet.name);
    const preview = await wb.render({sheetName:sheet.name,range,scale:1,format:'png'});
    await writeFile(resolve(previews,filename+'_'+sheet.name+'.png'),new Uint8Array(await preview.arrayBuffer()));
  }
  const xlsx = await SpreadsheetFile.exportXlsx(wb);
  await xlsx.save(resolve(root,'annexes',filename+'.xlsx'));
  console.log(filename+' : '+sheets.map(s => s.name+' ('+(s.end-4)+')').join(', '));
}
