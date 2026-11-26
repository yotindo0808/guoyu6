# 字音字形綜合練習（B5 直書、由右到左、上下兩欄）
# 題型：一、圈出正確的國字（形近字）　二、寫出注音，並在（　）中填入正確的國字（形近字）　三、寫出粗體字的注音（多音字）
# 用法：python3 build_practice.py 課次.json 輸出資料夾
import json, sys, os, re, copy
from docx import Document
from docx.shared import Pt, Mm, RGBColor
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

D = json.load(open(sys.argv[1], encoding='utf-8'))
OUT = sys.argv[2]
P = D['practice']
FONT = '芫荽'
ZHUYIN = False   # 注音字型在直書 Word 會轉向跑版，綜合練習一律不加注音
if D.get('zhuyin'): print('注意：綜合練習（直書）目前不支援 zhuyin，題目文字不會加注音')
BPMF = 'ㄅ注音芫荽'
RED = RGBColor(0xC0, 0x00, 0x00)
GRAY = RGBColor(0x40, 0x40, 0x40)
ZY = {c['ch']: c['zy'] for row in D['shapeRows'] if row != 'PAGEBREAK' for g in row for c in g['chars']}
NUMS = '１２３４５６７８９'
SUB = '⑴⑵⑶⑷'

def setfont(r, size, bold=False, color=None):
    r.font.size = Pt(size); r.font.bold = bold
    r.font.name = FONT
    rpr = r._r.get_or_add_rPr(); rf = rpr.find(qn('w:rFonts'))
    if rf is None: rf = OxmlElement('w:rFonts'); rpr.insert(0, rf)
    for k in ('w:ascii', 'w:hAnsi', 'w:eastAsia', 'w:cs'): rf.set(qn(k), FONT)
    if color is not None: r.font.color.rgb = color

def para(doc, before=0, after=0, line=None, indent=0, keep=False):
    p = doc.add_paragraph(); pf = p.paragraph_format
    pf.space_before = Pt(before); pf.space_after = Pt(after)
    if line: pf.line_spacing = Pt(line)
    if indent: pf.left_indent = Pt(indent)
    pf.keep_with_next = keep
    return p

def border(p, color='8FA77F', sz=8):
    ppr = p._p.get_or_add_pPr(); b = OxmlElement('w:pBdr')
    for side in ('top', 'left', 'bottom', 'right'):
        e = OxmlElement('w:' + side); e.set(qn('w:val'), 'single'); e.set(qn('w:sz'), str(sz)); e.set(qn('w:space'), '4'); e.set(qn('w:color'), color); b.append(e)
    ppr.append(b)

def ivs(t): return re.sub(r'\{(\d+)\}', lambda m: '' if m.group(1) == '1' else chr(0xE01E0 + int(m.group(1)) - 1), t)

def add(p, text, size=16, bold=False, color=None, plain=False):
    r = p.add_run(ivs(text)); setfont(r, size, bold, color)
    if ZHUYIN and not plain and color is None and re.search(r'[\u4e00-\u9fff]', text):
        rf = r._r.get_or_add_rPr().find(qn('w:rFonts'))
        for k in ('w:ascii', 'w:hAnsi', 'w:eastAsia', 'w:cs'): rf.set(qn(k), BPMF)
    return r

BLANK_Z = '\u2060　\u2060　\u2060'   # 注音空格
BLANK_C = '\u2060　\u2060　\u2060'     # 國字空格

WIDTH = 12 if ZHUYIN else 17   # 直書一欄大約放得下的字數（注音字型較寬）

def toks(text):
    """切成不可拆開的單位：[字] 粗體目標字；〔答案〕國字空格；〈注音〉注音空格"""
    out = []
    for tok in re.split(r'(\[[^\]]+\]|〔[^〕]*〕|〈[^〉]*〉|«[^»]+»)', text):
        if not tok: continue
        if tok[0] in '[〔〈«': out.append(tok)
        else:
            for piece in re.findall(r'.\{\d+\}|.', tok): out.append(piece)
    return out

def tlen(t):
    if t[0] in '[«': return len(t) - 2
    if t[0] == '〈': return 5
    if t[0] == '〔': return 4
    return 1

def emit(p, t, key, size):
    if t[0] == '[': add(p, t[1:-1], size, True, plain=True)   # 要判斷的字不給注音
    elif t[0] == '«': add(p, t[1:-1], size, plain=True)
    elif t[0] in '〔〈':
        z = t[0] == '〈'
        add(p, '（', size)
        if key: add(p, t[1:-1], 10 if z else size, True, RED)
        else: add(p, '　　　' if z else '　　', size)
        add(p, '）', size)
    else: add(p, t, size)

def rich(p, text, key, size=16, first=0, indent='　'):
    """自己斷行：空格不會被拆到兩行；優先在逗號後換行"""
    ts = toks(text); lines = []; cur = []; w = first
    for i, t in enumerate(ts):
        L = tlen(t)
        if cur and w + L > WIDTH:
            # 往回找逗號斷行
            cut = max([k for k, x in enumerate(cur) if x in '，、；　' and k > len(cur) // 3] or [len(cur) - 1])
            if cut < len(cur) - 1 and cut > 0:
                lines.append(cur[:cut + 1]); cur = cur[cut + 1:]
            else:
                lines.append(cur); cur = []
            w = len(indent) + sum(tlen(x) for x in cur)
        if t in '，。、）」！？' and not cur and lines:   # 標點不放行首
            lines[-1].append(t); continue
        cur.append(t); w += L
    if cur: lines.append(cur)
    for k, ln in enumerate(lines):
        if k:
            p.add_run().add_break(); add(p, indent, size)
        for t in ln: emit(p, t, key, size)

def circle(p, text, key, size=16):
    # （寓／[遇]）言：教師版把正確的字標紅、加底線；括號裡的選項不給注音
    inside = False
    for tok in re.split(r'(\[[^\]]+\]|（|）)', text):
        if not tok: continue
        if tok == '（': inside = True
        if tok.startswith('['):
            r = add(p, tok[1:-1], size, key, RED if key else None, plain=True)
            if key: r.font.underline = True
        else: add(p, tok, size, plain=inside)
        if tok == '）': inside = False

def title(doc, text, note):
    p = para(doc, before=6, after=4, keep=True)
    add(p, text, 18, True)
    if note: add(p, '　' + note, 13, False, GRAY)

def build(key):
    doc = Document()
    st = doc.styles['Normal']; st.font.name = FONT; st.font.size = Pt(17)
    st.element.rPr.rFonts.set(qn('w:eastAsia'), FONT)
    sec = doc.sections[0]
    sec.page_width, sec.page_height = Mm(182), Mm(257)
    for k in ('top_margin', 'bottom_margin', 'left_margin', 'right_margin'): setattr(sec, k, Mm(12))
    sp = sec._sectPr
    cols = OxmlElement('w:cols'); cols.set(qn('w:num'), '2'); cols.set(qn('w:space'), '454'); cols.set(qn('w:sep'), '1')
    td = OxmlElement('w:textDirection'); td.set(qn('w:val'), 'tbRl')
    old = sp.find(qn('w:cols'))
    if old is not None: sp.remove(old)
    grid = sp.find(qn('w:docGrid'))
    (grid.addprevious(cols) if grid is not None else sp.append(cols))
    (grid.addprevious(td) if grid is not None else sp.append(td))
    # 頁首
    p = para(doc, after=2); add(p, '字音字形綜合練習', 21, True)
    p = para(doc); add(p, D['bookLabel'] + '　' + D['lessonTitle'], 13, False, GRAY)
    if key: add(p, '　教師解答版', 13, True, RED)
    p = para(doc, after=6); add(p, '班級＿＿＿　座號＿＿　姓名＿＿＿＿＿＿', 13)
    # 一、圈出正確的國字
    title(doc, '一、圈出正確的國字', '')
    for i, grp in enumerate(P['circle']):
        L = lambda w: len(w.replace('[', '').replace(']', ''))
        lines = []
        for w in grp:   # 一行放得下就兩個詞並排（直書一欄約 17 字）
            if lines and len(lines[-1]) == 1 and L(lines[-1][0]) + L(w) + 3 <= 17: lines[-1].append(w)
            else: lines.append([w])
        for k, ws in enumerate(lines):
            p = para(doc, before=4 if k == 0 and i else 0, line=26)
            add(p, (NUMS[i] if k == 0 else '　') + '　', 16, k == 0)
            for j, w in enumerate(ws):
                if j: add(p, '　', 16)
                circle(p, w, key, 16)
    # 二、寫出注音，並在（　）中填入正確的國字
    title(doc, '二、寫出注音，並在（　）中填入正確的國字', '')
    for i, b in enumerate(P['fill']):
        p = para(doc, before=8 if i else 2, line=26)
        border(p)
        add(p, NUMS[i] + '　', 16, True)
        rich(p, '　'.join('«' + c + '»：〈' + ZY[c] + '〉' for c in b['chars']), key, first=2, indent='　　')
        for k, s in enumerate(b['sents']):
            p = para(doc, line=26)
            lead = '　' + (SUB[k] if len(b['sents']) > 1 else '　')
            add(p, lead); rich(p, s, key, first=2, indent='　　')
    # 三、多音字
    title(doc, '三、寫出粗體字的注音', '')
    for i, b in enumerate(P['poly']):
        p = para(doc, before=8 if i else 2, line=26)
        border(p)
        add(p, NUMS[i] + '　', 16, True)
        rich(p, '　'.join(w + '：〈' + z + '〉' for w, z in b['box']), key, first=2, indent='　　')
        for k, (s, z) in enumerate(b['sents']):
            p = para(doc, line=26)
            add(p, '　' + SUB[k]); rich(p, s.replace(']', ']〈' + z + '〉', 1), key, first=2, indent='　　')
    name = f"{D['fileLabel']}_字音字形綜合練習{'_教師解答版' if key else ''}.docx"
    doc.save(os.path.join(OUT, name)); print(name)

os.makedirs(OUT, exist_ok=True)
build(False); build(True)
