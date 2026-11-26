// 字音字形學習單產生器（B5 直式，芫荽／ㄅ注音芫荽）
// 用法：bash run.sh <課次資料.json>
//   或：python3 make_comp.py X.json && python3 make_zy.py X.json && node build_worksheet.js X.json [輸出資料夾]
// 換課時修改 DATA 即可。
// 注音字型文字中，若某字要用第 n 個讀音，請在字後加 {n}（例如 含情脈{2}脈{2}）。
// 字型缺字的部件，會由 make_comp.py 先轉成圖片（comp_img/*.png）。
const fs = require('fs');
const path = require('path');
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, ImageRun,
  WidthType, BorderStyle, ShadingType, AlignmentType, VerticalAlign,
  HeightRule, PageBreak, TableLayoutType,
} = require('docx');

const DATA_PATH = process.argv[2];
if (!DATA_PATH) { console.error('用法：node build_worksheet.js <課次資料.json> [輸出資料夾]'); process.exit(1); }
const DATA = JSON.parse(fs.readFileSync(DATA_PATH, 'utf8'));
const OUT_DIR = process.argv[3] || path.join(__dirname, 'output');
const COMP_IMG = JSON.parse(fs.readFileSync(path.join(__dirname, 'comp_img', 'index.json'), 'utf8'));
const ZY_IMG = JSON.parse(fs.readFileSync(path.join(__dirname, 'zy_img', 'index.json'), 'utf8'));

// ---------- 版面常數 ----------
const mm = (v) => Math.round(v * 56.7);
const px = (v) => Math.round(v * 3.7795); // 公釐 → 圖片像素
const PAGE_W = mm(182), PAGE_H = mm(257);
const MARGIN = mm(12);
const CONTENT_W = PAGE_W - MARGIN * 2;

const FONT = '芫荽';
const BPMF = 'ㄅ注音芫荽';
const PT = (p) => p * 2;          // 半點
const BODY = PT(16);
const RED = 'C00000';
const LINE = '595959';
const DASH = 'A6A6A6';
const GREEN_LINE = '8FA77F';
const SHADE_COMP = 'E2EADB';
const SHADE_RAD = 'F2F2F2';
const SHADE_MODEL = 'EDEDED';

const GRID_MM = 15, ZY_MM = 8.7;
const GRID = mm(GRID_MM);         // 國字區 1.5 × 1.5 公分
const HALF = Math.round(GRID / 2);
const ZY_W = mm(ZY_MM);           // 注音欄
const UNIT = mm(38);              // 每個字所佔欄寬
const GAP = mm(2);
const PAD_L = Math.round((UNIT - GRID - ZY_W) / 2);
const PAD_R = UNIT - GRID - ZY_W - PAD_L;
const WBOX_MM = 11;               // 造詞書寫格（四字詞自動縮小）
const WBOX = mm(WBOX_MM);

const NONE = { style: BorderStyle.NONE, size: 0, color: 'FFFFFF' };
const SOLID = (sz = 8, color = LINE) => ({ style: BorderStyle.SINGLE, size: sz, color });
const DASHED = { style: BorderStyle.DASHED, size: 4, color: DASH };
const BOX = (sz = 8, color = LINE) => ({ top: SOLID(sz, color), bottom: SOLID(sz, color), left: SOLID(sz, color), right: SOLID(sz, color) });
const noBorders = { top: NONE, bottom: NONE, left: NONE, right: NONE };
const tableNoBorders = { top: NONE, bottom: NONE, left: NONE, right: NONE, insideHorizontal: NONE, insideVertical: NONE };

// {n} → 異體字選擇子
const ivs = (s) => s.replace(/\{(\d+)\}/g, (_, n) => (n === '1' ? '' : String.fromCodePoint(0xE01E0 + Number(n) - 1)));

const run = (text, o = {}) => {
  const f = o.bpmf ? BPMF : FONT;
  return new TextRun({
    text: o.bpmf ? ivs(text) : text,
    size: o.size || BODY, bold: o.bold, color: o.color,
    underline: o.underline ? { type: 'single', color: o.ulColor || '000000' } : undefined,
    font: { eastAsia: f, ascii: f, hAnsi: f, cs: f, hint: 'eastAsia' },
  });
};
const para = (children, o = {}) => new Paragraph({
  children: Array.isArray(children) ? children : [children],
  alignment: o.align || AlignmentType.LEFT,
  spacing: { before: o.before || 0, after: o.after || 0, line: o.line, lineRule: o.line ? 'exact' : undefined },
  keepNext: o.keepNext, indent: o.indent,
});
const cell = (children, o = {}) => new TableCell({
  children: Array.isArray(children) ? children : [children],
  width: { size: o.w, type: WidthType.DXA },
  columnSpan: o.span, rowSpan: o.rowSpan,
  borders: o.borders || noBorders,
  shading: o.shade ? { type: ShadingType.CLEAR, color: 'auto', fill: o.shade } : undefined,
  verticalAlign: o.valign || VerticalAlign.CENTER,
  margins: o.margins || { top: 0, bottom: 0, left: 60, right: 60 },
});
const emptyP = (size = 8) => para(run('', { size }), { line: 160 });

// 部件：字型有字就用文字，缺字就放圖片
function compRuns(comp, sizePt, red = true) {
  const out = [];
  for (const ch of comp) {
    if (COMP_IMG[ch]) {
      const hmm = sizePt * 0.3528;
      const pxs = Math.round(hmm * 3.78);
      out.push(new ImageRun({ type: 'png', data: fs.readFileSync(path.join(__dirname, 'comp_img', COMP_IMG[ch][red ? 'r' : 'k'])), transformation: { width: pxs, height: pxs } }));
    } else out.push(run(ch, { size: PT(sizePt), color: red ? RED : undefined, bold: red }));
  }
  return out;
}

// 字旁注音：取自「ㄅ注音芫荽」字型本身的排版（聲調位置正確）
function zhuyinImg(ch, zy, red) {
  const name = ZY_IMG[`${ch}|${zy}|${red ? 'r' : 'k'}`];
  if (!name) throw new Error('缺少注音圖片：' + ch + zy);
  return para(new ImageRun({ type: 'png', data: fs.readFileSync(path.join(__dirname, 'zy_img', name)), transformation: { width: px(ZY_MM), height: px(GRID_MM) } }), { align: AlignmentType.CENTER });
}

// 田字格（2 列）＋注音欄。回傳 [上列 cells, 下列 cells]
function gridCells(ch, zy, filled, color) {
  const top = [], bot = [];
  if (filled) {
    top.push(cell(para(run(ch, { size: PT(32), color: color === 'model' ? '000000' : RED }), { align: AlignmentType.CENTER }), {
      w: GRID, span: 2, rowSpan: 2, shade: color === 'model' ? SHADE_MODEL : undefined, borders: BOX(), margins: { top: 0, bottom: 0, left: 0, right: 0 },
    }));
  } else {
    top.push(cell(emptyP(), { w: HALF, borders: { top: SOLID(), left: SOLID(), right: DASHED, bottom: DASHED } }));
    top.push(cell(emptyP(), { w: GRID - HALF, borders: { top: SOLID(), right: SOLID(), left: DASHED, bottom: DASHED } }));
    bot.push(cell(emptyP(), { w: HALF, borders: { bottom: SOLID(), left: SOLID(), right: DASHED, top: DASHED } }));
    bot.push(cell(emptyP(), { w: GRID - HALF, borders: { bottom: SOLID(), right: SOLID(), left: DASHED, top: DASHED } }));
  }
  top.push(cell(filled ? zhuyinImg(ch, zy, color !== 'model') : emptyP(), { w: ZY_W, rowSpan: 2, borders: BOX(), margins: { top: 0, bottom: 0, left: 0, right: 0 } }));
  return [top, bot];
}

// 造詞：直書、由右到左；每個詞一條底色，要寫的字留白色方格
const WORD_SHADES = ['E3ECDC', 'F6EEDB'];   // 第一個詞（右）、第二個詞（左）
function wordsVertical(words, target, show, key) {
  const maxLen = Math.max(...words.map((w) => [...w].length));
  const BW = maxLen >= 4 ? mm(10) : WBOX;
  const SG = mm(4);
  const order = words.map((w, i) => i).reverse();   // 右到左
  const cols = [];
  order.forEach((_, k) => { cols.push(BW); if (k < order.length - 1) cols.push(SG); });
  const rows = [];
  for (let r = 0; r < maxLen; r++) {
    const kids = [];
    order.forEach((wi, k) => {
      const chs = [...words[wi]];
      const c = chs[r];
      const shade = WORD_SHADES[wi % WORD_SHADES.length];
      if (c === undefined) kids.push(cell(emptyP(), { w: BW }));
      else {
        const blank = c === target && !show;
        kids.push(cell(para(run(blank ? (key ? c : '') : c, { size: PT(17), color: blank ? RED : undefined }), { align: AlignmentType.CENTER }), {
          w: BW, shade: blank ? 'FFFFFF' : shade,
          borders: blank ? BOX(8, '7F7F7F') : { top: r === 0 ? SOLID(4, 'B5C4A8') : NONE, bottom: r === chs.length - 1 ? SOLID(4, 'B5C4A8') : NONE, left: SOLID(4, 'B5C4A8'), right: SOLID(4, 'B5C4A8') },
          margins: { top: 0, bottom: 0, left: 0, right: 0 },
        }));
      }
      if (k < order.length - 1) kids.push(cell(emptyP(), { w: SG }));
    });
    rows.push(new TableRow({ height: { value: BW, rule: HeightRule.EXACT }, children: kids }));
  }
  return new Table({
    width: { size: cols.reduce((x, y) => x + y, 0), type: WidthType.DXA }, columnWidths: cols, layout: TableLayoutType.FIXED,
    borders: tableNoBorders, alignment: AlignmentType.CENTER, rows,
  });
}

// ---------- 一、部件帶字 ----------
const groupWidth = (g) => g.chars.length * UNIT + (g.chars.length - 1) * GAP;

function shapeGroupTable(g, key) {
  const n = g.chars.length;
  const cols = [];
  g.chars.forEach((_, i) => { cols.push(PAD_L, HALF, GRID - HALF, ZY_W, PAD_R); if (i < n - 1) cols.push(GAP); });
  const totalW = cols.reduce((a, b) => a + b, 0);
  const rows = [];
  const pad = (w, o = {}) => cell(emptyP(), { w, ...o });

  rows.push(new TableRow({
    height: { value: mm(10), rule: HeightRule.EXACT },
    children: [cell(para([run('共同部件　', { size: PT(12), color: '404040' }), ...compRuns(g.comp, 22)], { align: AlignmentType.CENTER }), {
      w: totalW, span: cols.length, shade: SHADE_COMP, borders: BOX(6, GREEN_LINE),
    })],
  }));
  rows.push(new TableRow({ height: { value: mm(2), rule: HeightRule.EXACT }, children: [pad(totalW, { span: cols.length })] }));
  const radCells = [];
  g.chars.forEach((c, i) => {
    radCells.push(pad(PAD_L));
    radCells.push(cell(para(c.rad ? [run('＋', { size: PT(11), color: '7F7F7F' }), run(c.rad, { size: PT(18) })] : [run('部件本身', { size: PT(12), color: '595959' })], { align: AlignmentType.CENTER }), { w: GRID + ZY_W, span: 3, shade: SHADE_RAD, borders: BOX(6) }));
    radCells.push(pad(PAD_R));
    if (i < n - 1) radCells.push(pad(GAP));
  });
  rows.push(new TableRow({ height: { value: mm(9), rule: HeightRule.EXACT }, children: radCells }));
  const arrowCells = [];
  g.chars.forEach((c, i) => {
    arrowCells.push(pad(PAD_L));
    arrowCells.push(cell(para(run('↓', { size: PT(11), color: '7F7F7F' }), { align: AlignmentType.CENTER, line: 240 }), { w: GRID + ZY_W, span: 3 }));
    arrowCells.push(pad(PAD_R));
    if (i < n - 1) arrowCells.push(pad(GAP));
  });
  rows.push(new TableRow({ height: { value: mm(4.5), rule: HeightRule.EXACT }, children: arrowCells }));

  const top = [], bot = [];
  g.chars.forEach((c, i) => {
    const filled = c.model || key;
    const [t, b] = gridCells(c.ch, c.zy, filled, c.model ? 'model' : 'red');
    top.push(pad(PAD_L, { rowSpan: 2 }), ...t, pad(PAD_R, { rowSpan: 2 }));
    bot.push(...b);
    if (i < n - 1) top.push(pad(GAP, { rowSpan: 2 }));
  });
  rows.push(new TableRow({ height: { value: HALF, rule: HeightRule.EXACT }, children: top }));
  rows.push(new TableRow({ height: { value: GRID - HALF, rule: HeightRule.EXACT }, children: bot }));

  const wordCells = [];
  g.chars.forEach((c, i) => {
    const kids = [emptyP(4), wordsVertical(c.words, c.ch, c.model, key), emptyP(4)];
    wordCells.push(cell(kids, { w: UNIT, span: 5, valign: VerticalAlign.TOP, margins: { top: 0, bottom: 0, left: 0, right: 0 } }));
    if (i < n - 1) wordCells.push(pad(GAP));
  });
  rows.push(new TableRow({ children: wordCells }));

  return new Table({ width: { size: totalW, type: WidthType.DXA }, columnWidths: cols, layout: TableLayoutType.FIXED, borders: tableNoBorders, rows });
}

function shapeRowTable(groups, key) {
  const widths = groups.map(groupWidth);
  const sum = widths.reduce((a, b) => a + b, 0);
  const GG = groups.length > 1 ? Math.floor((CONTENT_W - sum) / (groups.length - 1)) : 0;
  const used = sum + GG * (groups.length - 1);
  const side = Math.floor((CONTENT_W - used) / 2);
  const z = { top: 0, bottom: 0, left: 0, right: 0 };
  const cols = [], cells = [];
  if (side > 0) { cols.push(side); cells.push(cell(emptyP(), { w: side, margins: z })); }
  groups.forEach((g, i) => {
    cols.push(widths[i]);
    cells.push(cell([shapeGroupTable(g, key), emptyP(10)], { w: widths[i], valign: VerticalAlign.TOP, margins: z }));
    if (i < groups.length - 1 && GG > 0) { cols.push(GG); cells.push(cell(emptyP(), { w: GG, margins: z })); }
  });
  const rest = CONTENT_W - cols.reduce((a, b) => a + b, 0);
  if (rest > 0) { cols.push(rest); cells.push(cell(emptyP(), { w: rest, margins: z })); }
  return new Table({ width: { size: CONTENT_W, type: WidthType.DXA }, columnWidths: cols, layout: TableLayoutType.FIXED, borders: tableNoBorders, rows: [new TableRow({ cantSplit: true, children: cells })] });
}

// ---------- 標題 ----------
function sectionTitle(text, note) {
  const kids = [run(text, { size: PT(18), bold: true })];
  if (note) kids.push(run('　' + note, { size: PT(13), color: '404040' }));
  return new Paragraph({ children: kids, spacing: { before: 100, after: 120 }, keepNext: true, border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: GREEN_LINE, space: 2 } } });
}
function header(title, key) {
  return [
    para([run(title + (key ? '（教師解答版）' : ''), { size: PT(22), bold: true })], { align: AlignmentType.CENTER, after: 40 }),
    para([run((DATA.bookLabel ? DATA.bookLabel + '　' : '') + DATA.lessonTitle, { size: PT(14), color: '404040' })], { align: AlignmentType.CENTER, after: 60 }),
    para([run('班級＿＿＿＿　座號＿＿＿　姓名＿＿＿＿＿＿＿', { size: PT(14) })], { align: AlignmentType.RIGHT, after: 40 }),
  ];
}

// ---------- 二、多音字：直書（由右到左），目標字右側填讀音 ----------
const P_CW = mm(13), P_ZW = mm(9), P_SG = mm(4);   // 字格、注音格、詞與詞的間距
const P_CHAR_PT = 24;
function zyImgAny(ch, zy, red, emMM) {
  const name = ZY_IMG[`${ch}|${zy || '*'}|${red ? 'r' : 'k'}`];
  if (!name) throw new Error('缺少注音圖片：' + ch + (zy || ''));
  const h = emMM, w = emMM * 0.58;
  return para(new ImageRun({ type: 'png', data: fs.readFileSync(path.join(__dirname, 'zy_img', name)), transformation: { width: px(w), height: px(h) } }), { align: AlignmentType.CENTER });
}
function parseWord(w) {
  const out = [];
  w.split(/(\[[^\]]+\])/).forEach((seg) => {
    if (!seg) return;
    if (seg.startsWith('[')) [...seg.slice(1, -1)].forEach((c) => out.push({ c, t: true }));
    else [...seg].forEach((c) => out.push({ c, t: false }));
  });
  return out;
}
const polyBlockWidth = (p) => p.words.length * (P_CW + P_ZW) + (p.words.length - 1) * P_SG;

function polyBlock(p, key) {
  const words = p.words.map(([w, ans]) => ({ chs: parseWord(w), ans }));
  const order = words.map((_, i) => i).reverse();       // 由右到左
  const maxLen = Math.max(...words.map((w) => w.chs.length));
  const cols = [];
  order.forEach((_, k) => { cols.push(P_CW, P_ZW); if (k < order.length - 1) cols.push(P_SG); });
  const W = cols.reduce((x, y) => x + y, 0);
  const emMM = P_CHAR_PT * 0.3528;
  const rows = [];
  rows.push(new TableRow({
    height: { value: mm(19), rule: HeightRule.EXACT },
    children: [cell([
      para(run(p.ch, { size: PT(26), bold: true }), { align: AlignmentType.CENTER }),
      para([run('讀音：', { size: PT(13), color: '404040' }), run(p.reads.join('　'), { size: PT(17) })], { align: AlignmentType.CENTER }),
    ], {
      w: W, span: cols.length, shade: SHADE_COMP, borders: BOX(6, GREEN_LINE),
    })],
  }));
  rows.push(new TableRow({ height: { value: mm(3), rule: HeightRule.EXACT }, children: [cell(emptyP(), { w: W, span: cols.length })] }));
  const EDGE = 'B5C4A8';
  for (let r = 0; r < maxLen; r++) {
    const kids = [];
    order.forEach((wi, k) => {
      const wd = words[wi];
      const it = wd.chs[r];
      const shade = WORD_SHADES[wi % WORD_SHADES.length];
      if (!it) { kids.push(cell(emptyP(), { w: P_CW }), cell(emptyP(), { w: P_ZW })); }
      else {
        const first = r === 0, last = r === wd.chs.length - 1;
        const vb = { top: first ? SOLID(4, EDGE) : NONE, bottom: last ? SOLID(4, EDGE) : NONE };
        kids.push(cell(para(run(it.c, { size: PT(P_CHAR_PT), bold: it.t }), { align: AlignmentType.CENTER }), {
          w: P_CW, shade, borders: { ...vb, left: SOLID(4, EDGE), right: NONE }, margins: { top: 0, bottom: 0, left: 0, right: 0 },
        }));
        if (it.t) {
          kids.push(cell(key ? zyImgAny(it.c, wd.ans, true, emMM) : emptyP(), {
            w: P_ZW, shade: 'FFFFFF', borders: BOX(8, '7F7F7F'), margins: { top: 0, bottom: 0, left: 0, right: 0 },
          }));
        } else {
          kids.push(cell(DATA.zhuyin ? zyImgAny(it.c, null, false, emMM) : emptyP(), {  // zhuyin: true（低、中年級）才在非目標字旁放注音
            w: P_ZW, shade, borders: { ...vb, right: SOLID(4, EDGE), left: NONE }, margins: { top: 0, bottom: 0, left: 0, right: 0 },
          }));
        }
      }
      if (k < order.length - 1) kids.push(cell(emptyP(), { w: P_SG }));
    });
    rows.push(new TableRow({ height: { value: P_CW, rule: HeightRule.EXACT }, children: kids }));
  }
  return new Table({ width: { size: W, type: WidthType.DXA }, columnWidths: cols, layout: TableLayoutType.FIXED, borders: tableNoBorders, rows });
}

// 依寬度把多音字題組排成數列
function polyRows(key) {
  const out = [];
  const GAPW = mm(8);
  let row = [], used = 0;
  const flush = () => {
    if (!row.length) return;
    const widths = row.map(polyBlockWidth);
    const sum = widths.reduce((a, b) => a + b, 0) + GAPW * (row.length - 1);
    const side = Math.floor((CONTENT_W - sum) / 2);
    const z = { top: 0, bottom: 0, left: 0, right: 0 };
    const cols = [], cells = [];
    if (side > 0) { cols.push(side); cells.push(cell(emptyP(), { w: side, margins: z })); }
    // 由右到左排列題組：第一組放最右邊
    [...row].reverse().forEach((p, i, arr) => {
      const w = polyBlockWidth(p);
      cols.push(w); cells.push(cell([polyBlock(p, key)], { w, valign: VerticalAlign.TOP, margins: z }));
      if (i < arr.length - 1) { cols.push(GAPW); cells.push(cell(emptyP(), { w: GAPW, margins: z })); }
    });
    const rest = CONTENT_W - cols.reduce((a, b) => a + b, 0);
    if (rest > 0) { cols.push(rest); cells.push(cell(emptyP(), { w: rest, margins: z })); }
    out.push(new Table({ width: { size: CONTENT_W, type: WidthType.DXA }, columnWidths: cols, layout: TableLayoutType.FIXED, borders: tableNoBorders, rows: [new TableRow({ cantSplit: true, children: cells })] }));
    out.push(para(run(''), { after: 160 }));
    row = []; used = 0;
  };
  DATA.poly.forEach((p) => {
    const w = polyBlockWidth(p);
    if (row.length && used + GAPW + w > CONTENT_W) flush();
    used += (row.length ? GAPW : 0) + w; row.push(p);
  });
  flush();
  return out;
}

// ---------- 三、部件擴充（開放式，每格可寫國字＋注音） ----------
function expandBlocks(key) {
  const N = 6;
  const SLOT_GAP = mm(4.5);
  const out = [];
  DATA.expand.forEach((e) => {
    const cols = [];
    for (let i = 0; i < N; i++) { cols.push(HALF, GRID - HALF, ZY_W); if (i < N - 1) cols.push(SLOT_GAP); }
    const W = cols.reduce((a, b) => a + b, 0);
    const headRow = new TableRow({
      height: { value: mm(11), rule: HeightRule.EXACT },
      children: [cell(para([run('部件　', { size: PT(13), color: '404040' }), ...compRuns(e.comp, 24), run('　　提示部首：', { size: PT(14), color: '404040' }), run(e.hints.join('、') + '……', { size: PT(17), color: '404040' })]), {
        w: W, span: cols.length, shade: SHADE_COMP, borders: BOX(6, GREEN_LINE), margins: { top: 0, bottom: 0, left: mm(3), right: 0 },
      })],
    });
    const spacer = new TableRow({ height: { value: mm(3), rule: HeightRule.EXACT }, children: [cell(emptyP(), { w: W, span: cols.length })] });
    const top = [], bot = [];
    for (let i = 0; i < N; i++) {
      const a = key ? e.ans[i] : null;
      const [t, b] = gridCells(a ? a[0] : '', a ? a[1] : '', !!a, 'red');
      top.push(...t); bot.push(...b);
      if (i < N - 1) top.push(cell(emptyP(), { w: SLOT_GAP, rowSpan: 2 }));
    }
    out.push(new Table({
      width: { size: W, type: WidthType.DXA }, columnWidths: cols, layout: TableLayoutType.FIXED, borders: tableNoBorders, alignment: AlignmentType.CENTER,
      rows: [headRow, spacer, new TableRow({ height: { value: HALF, rule: HeightRule.EXACT }, children: top }), new TableRow({ height: { value: GRID - HALF, rule: HeightRule.EXACT }, children: bot })],
    }));
    out.push(para(run(''), { after: 600 }));
  });
  return out;
}

// ---------- 綜合練習（直書，由右到左） ----------
const PUNCT = '，。、！？「」：；';
const VERT = { '，': '︐', '。': '︒', '、': '︑' };
function tokens(t) {
  const out = []; let tgt = false; let i = 0;
  while (i < t.length) {
    const c = t[i];
    if (c === '[') { tgt = true; i++; continue; }
    if (c === ']') { tgt = false; i++; continue; }
    if (t.startsWith('__', i)) { out.push({ c: '__', n: 1, t: false }); i += 2; continue; }
    const m = t.slice(i).match(/^\{(\d+)\}/);
    if (m) { out[out.length - 1].n = Number(m[1]); i += m[0].length; continue; }
    out.push({ c, n: 1, t: tgt }); i++;
  }
  return out;
}
function zyByIndex(ch, n, emMM) {
  const name = ZY_IMG[`${ch}|#${n}|k`];
  if (!name) throw new Error('缺少注音圖片：' + ch + '#' + n);
  return para(new ImageRun({ type: 'png', data: fs.readFileSync(path.join(__dirname, 'zy_img', name)), transformation: { width: px(emMM * 0.58), height: px(emMM) } }), { align: AlignmentType.CENTER });
}

// 通用直書句子表：cols = [{tokens, ans}]，由右到左；opts 決定尺寸與作答方式
function verticalSentences(items, o, key) {
  const z = { top: 0, bottom: 0, left: 0, right: 0 };
  const EDGE = 'B5C4A8';
  const emMM = o.charPt * 0.3528;
  const order = items.map((_, i) => i).reverse();
  const cols = [];
  order.forEach((wi, k) => { cols.push(o.cw, o.zw); if (k < order.length - 1) cols.push(o.gapAfter ? o.gapAfter(wi) : o.gap); });
  const W = cols.reduce((x, y) => x + y, 0);
  const rows = [];
  // 選項列（選字填空用）
  if (o.groupHeader) rows.push(o.groupHeader(order, cols));
  // 題號列
  const numCells = [];
  order.forEach((wi, k) => {
    numCells.push(cell(para(run(String(items[wi].no), { size: PT(14), bold: true }), { align: AlignmentType.CENTER }), { w: o.cw + o.zw, span: 2, margins: z }));
    if (k < order.length - 1) numCells.push(cell(emptyP(), { w: cols[k * 3 + 2], margins: z }));
  });
  rows.push(new TableRow({ height: { value: mm(8), rule: HeightRule.EXACT }, children: numCells }));
  const maxLen = Math.max(...items.map((it) => it.tokens.length));
  for (let r = 0; r < maxLen; r++) {
    const kids = [];
    order.forEach((wi, k) => {
      const it = items[wi];
      const tk = it.tokens[r];
      const shade = WORD_SHADES[wi % 2];
      if (!tk) kids.push(cell(emptyP(), { w: o.cw, margins: z }), cell(emptyP(), { w: o.zw, margins: z }));
      else {
        const first = r === 0, last = r === it.tokens.length - 1;
        const vb = { top: first ? SOLID(4, EDGE) : NONE, bottom: last ? SOLID(4, EDGE) : NONE };
        if (tk.c === '__') {
          kids.push(cell(para(run(key ? it.ans : '', { size: PT(o.charPt + 4), color: RED }), { align: AlignmentType.CENTER }), {
            w: o.cw + o.zw, span: 2, shade: 'FFFFFF', borders: BOX(8, '7F7F7F'), margins: z,
          }));
        } else if (PUNCT.includes(tk.c)) {
          kids.push(cell(para(run(VERT[tk.c] || tk.c, { size: PT(o.charPt) }), { align: AlignmentType.CENTER }), { w: o.cw, shade, borders: { ...vb, left: SOLID(4, EDGE), right: NONE }, margins: z }));
          kids.push(cell(emptyP(), { w: o.zw, shade, borders: { ...vb, right: SOLID(4, EDGE), left: NONE }, margins: z }));
        } else {
          kids.push(cell(para(run(tk.c, { size: PT(o.charPt), bold: tk.t }), { align: AlignmentType.CENTER }), {
            w: o.cw, shade, borders: { ...vb, left: SOLID(4, EDGE), right: NONE }, margins: z,
          }));
          if (tk.t) {
            kids.push(cell(key ? zyImgAny(tk.c, it.ans, true, emMM) : emptyP(), { w: o.zw, shade: 'FFFFFF', borders: BOX(8, '7F7F7F'), margins: z }));
          } else {
            kids.push(cell(zyByIndex(tk.c, tk.n, emMM), { w: o.zw, shade, borders: { ...vb, right: SOLID(4, EDGE), left: NONE }, margins: z }));
          }
        }
      }
      if (k < order.length - 1) kids.push(cell(emptyP(), { w: cols[k * 3 + 2], margins: z }));
    });
    rows.push(new TableRow({ height: { value: o.ch, rule: HeightRule.EXACT }, children: kids }));
  }
  return new Table({ width: { size: W, type: WidthType.DXA }, columnWidths: cols, layout: TableLayoutType.FIXED, borders: tableNoBorders, alignment: AlignmentType.CENTER, rows });
}

function polyQuestions(key) {
  const items = DATA.polyQ.map((q, i) => ({ no: i + 1, tokens: tokens(q.text), ans: q.ans }));
  return verticalSentences(items, { cw: mm(13), zw: mm(8.5), gap: mm(4.5), ch: mm(14.5), charPt: 24 }, key);
}

function pickTable(key) {
  const items = []; const groupOf = [];
  let no = 1;
  DATA.pick.forEach((g, gi) => g.qs.forEach((q) => { items.push({ no: no++, tokens: tokens(q.text), ans: q.ans }); groupOf.push(gi); }));
  const CW = mm(7.6), ZW = mm(4.6);
  const IN = mm(0.6), OUT = Math.floor((CONTENT_W - items.length * (CW + ZW) - (items.length - 1 - (DATA.pick.length - 1)) * IN) / (DATA.pick.length - 1));
  const gapAfter = (wi) => (groupOf[wi] === groupOf[wi - 1] ? IN : OUT);   // order 由右到左：wi 的左邊是 wi+1
  const groupHeader = (order, cols) => {
    const cells = [];
    let k = 0;
    while (k < order.length) {
      const g = groupOf[order[k]];
      let span = 0, w = 0, j = k;
      while (j < order.length && groupOf[order[j]] === g) {
        span += 2; w += cols[j * 3] + cols[j * 3 + 1];
        if (j + 1 < order.length && groupOf[order[j + 1]] === g) { span += 1; w += cols[j * 3 + 2]; }
        j++;
      }
      const opts = DATA.pick[g].opts;
      const ps = opts.map((t) => para(run(t, { size: PT(16), bold: true }), { align: AlignmentType.CENTER, line: 400 }));
      cells.push(cell(ps, { w, span, shade: SHADE_RAD, borders: BOX(6), margins: { top: 0, bottom: 0, left: 0, right: 0 } }));
      if (j < order.length) cells.push(cell(emptyP(), { w: cols[(j - 1) * 3 + 2], margins: { top: 0, bottom: 0, left: 0, right: 0 } }));
      k = j;
    }
    return new TableRow({ height: { value: mm(31), rule: HeightRule.EXACT }, children: cells });
  };
  // gapAfter 以 order 的位置計算：第 k 欄與第 k+1 欄之間
  const order = items.map((_, i) => i).reverse();
  const gapFn = (wi) => { const k = order.indexOf(wi); const next = order[k + 1]; return groupOf[wi] === groupOf[next] ? IN : OUT; };
  return verticalSentences(items, { cw: CW, zw: ZW, gap: IN, gapAfter: gapFn, ch: mm(13), charPt: 16, groupHeader }, key);
}

// ---------- 組合 ----------
const newPage = () => new Paragraph({ children: [run('', { size: 2 })], pageBreakBefore: true, spacing: { before: 0, after: 0, line: 20, lineRule: 'exact' } });
const docOf = (children) => new Document({
  styles: { default: { document: { run: { font: { eastAsia: FONT, ascii: FONT, hAnsi: FONT }, size: BODY } } } },
  sections: [{ properties: { page: { size: { width: PAGE_W, height: PAGE_H }, margin: { top: MARGIN, bottom: MARGIN, left: MARGIN, right: MARGIN, header: mm(6), footer: mm(6) } } }, children }],
});

function buildClass(key) {
  const ch = [...header('字音字形學習單', key)];
  ch.push(sectionTitle('一、部件帶字', '部首＋部件，寫出國字和注音，再完成直書語詞。'));
  DATA.shapeRows.forEach((row) => {
    if (row === 'PAGEBREAK') { ch.push(newPage()); return; }
    ch.push(shapeRowTable(row, key));
  });
  ch.push(para(run(''), { after: 120 }));
  ch.push(sectionTitle('二、多音字', '看語詞判斷讀音，在粗體字右邊的方格寫出注音。'));
  polyRows(key).forEach((x) => ch.push(x));
  ch.push(newPage());
  ch.push(sectionTitle('三、部件擴充', '同一個部件換上其他部首，還能組成哪些字？寫出國字和注音。'));
  ch.push(para(run(''), { after: 80 }));
  expandBlocks(key).forEach((x) => ch.push(x));
  if (key) ch.push(para(run('紅字為參考答案，學生寫出其他正確的字也算對。', { size: PT(12), color: RED })));
  return docOf(ch);
}

function buildPractice(key) {
  const ch = [...header('字音字形綜合練習', key)];
  ch.push(sectionTitle('一、讀音判斷', '看句子判斷讀音，在粗體字右邊的方格寫出注音。'));
  ch.push(polyQuestions(key));
  ch.push(newPage());
  ch.push(sectionTitle('二、選字填空', '從上方的字選出正確的字，寫在方格裡。'));
  ch.push(pickTable(key));
  return docOf(ch);
}

(async () => {
  const dir = OUT_DIR;
  fs.mkdirSync(dir, { recursive: true });
  const L = DATA.fileLabel || DATA.lessonShort;
  const files = [
    [`${L}_字音字形學習單（上課用）.docx`, buildClass(false)],
    [`${L}_字音字形學習單（上課用）_教師解答版.docx`, buildClass(true)],
  ];
  for (const [n, d] of files) fs.writeFileSync(path.join(dir, n), await Packer.toBuffer(d));
  console.log('done');
})();
