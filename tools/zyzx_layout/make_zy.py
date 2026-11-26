# 從「ㄅ注音芫荽」擷取字旁注音（含正確聲調位置），輸出成圖片
import json, sys, os
import glob
HERE = os.path.dirname(os.path.abspath(__file__))
def find_font(name):
    for d in [os.path.join(HERE, 'fonts'), os.path.expanduser('~/.fonts'), '/usr/share/fonts', '/usr/local/share/fonts', '/mnt/user-data/uploads']:
        hit = glob.glob(os.path.join(d, '**', name), recursive=True)
        if hit: return hit[0]
    if name.startswith(('Iansui', 'Bpmf')): sys.exit(f'找不到字型 {name}，請放到 fonts/ 資料夾')
    return None
PHONIC = os.path.join(HERE, 'data', 'phonic_table_A.txt')
from PIL import Image, ImageDraw, ImageFont
BP = find_font('BpmfIansui-Regular.ttf')
D_PATH = os.path.abspath(sys.argv[1])
os.chdir(HERE)
D = json.load(open(D_PATH, encoding='utf-8'))
tbl = {}
for line in open(PHONIC, encoding='utf-8'):
    p = line.rstrip('\n').split('\t')
    if len(p) > 3: tbl[p[0]] = p[3:]
S = 600
font = ImageFont.truetype(BP, S, layout_engine=ImageFont.Layout.RAQM)
asc, desc = font.getmetrics()
import shutil
shutil.rmtree('zy_img', ignore_errors=True)
os.makedirs('zy_img', exist_ok=True)
idx = {}
def make(ch, zy, color, tag):
    reads = tbl.get(ch, [zy])
    if zy is None: n = 0
    elif zy not in reads: print('!! 讀音不在字型中', ch, zy, reads); n = 0
    else: n = reads.index(zy)
    s = ch + (chr(0xE01E0 + n) if n else '')
    img = Image.new('RGBA', (int(S * 1.6), asc + desc), (0, 0, 0, 0))
    ImageDraw.Draw(img).text((0, 0), s, font=font, fill=color)
    base = asc  # 基線
    top = base - int(S * 0.88)
    crop = img.crop((S - int(S*0.02), top, S + int(S*0.56), top + S))
    name = f'{ord(ch):X}_{reads.index(zy) if zy in reads else 0}_{tag}.png'; crop.save('zy_img/' + name)
    idx[f'{ch}|{zy or "*"}|{tag}'] = name
for row in D['shapeRows']:
    if row == 'PAGEBREAK': continue
    for g in row:
        for c in g['chars']:
            make(c['ch'], c['zy'], (0, 0, 0, 255), 'k')
            make(c['ch'], c['zy'], (192, 0, 0, 255), 'r')
for e in D['expand']:
    for ch, zy in e['ans']:
        make(ch, zy, (192, 0, 0, 255), 'r')
import re
for p in D['poly']:
    for w, ans in p['words']:
        for seg in re.split(r'(\[[^\]]+\])', w):
            if not seg: continue
            if seg.startswith('['):
                for ch in seg[1:-1]: make(ch, ans, (192, 0, 0, 255), 'r')
            else:
                for ch in seg: make(ch, None, (0, 0, 0, 255), 'k')
# 綜合練習：句子逐字產生注音（{n} 指定第 n 個讀音）
PUNCT = '，。、！？「」：；'
def tokens(t):
    out = []; tgt = False; i = 0
    while i < len(t):
        c = t[i]
        if c == '[': tgt = True; i += 1; continue
        if c == ']': tgt = False; i += 1; continue
        if t.startswith('__', i): out.append(('__', 1, False)); i += 2; continue
        m = re.match(r'\{(\d+)\}', t[i:])
        if m: ch, _, tg = out[-1]; out[-1] = (ch, int(m.group(1)), tg); i += len(m.group(0)); continue
        out.append((c, 1, tgt)); i += 1
    return out
def make_n(ch, n, color, tag):
    reads = tbl.get(ch, [None])
    make_key = f'{ch}|#{n}|{tag}'
    s = ch + (chr(0xE01E0 + n - 1) if n > 1 else '')
    img = Image.new('RGBA', (int(S * 1.6), asc + desc), (0, 0, 0, 0))
    ImageDraw.Draw(img).text((0, 0), s, font=font, fill=color)
    top = asc - int(S * 0.88)
    crop = img.crop((S - int(S*0.02), top, S + int(S*0.56), top + S))
    name = f'{ord(ch):X}_n{n}_{tag}.png'; crop.save('zy_img/' + name); idx[make_key] = name
for q in D['polyQ']:
    for ch, n, tg in tokens(q['text']):
        if ch in PUNCT: continue
        if tg: make(ch, q['ans'], (192, 0, 0, 255), 'r')
        else: make_n(ch, n, (0, 0, 0, 255), 'k')
for g in D['pick']:
    for q in g['qs']:
        for ch, n, tg in tokens(q['text']):
            if ch in PUNCT or ch == '__': continue
            make_n(ch, n, (0, 0, 0, 255), 'k')
json.dump(idx, open('zy_img/index.json', 'w', encoding='utf-8'), ensure_ascii=False)
print(len(idx), 'images')
