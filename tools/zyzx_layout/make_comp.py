# 為芫荽缺字的部件產生圖片；並列出注音字型文字中的多音字供確認
import json, sys, os, re
import glob
HERE = os.path.dirname(os.path.abspath(__file__))
def find_font(name):
    for d in [os.path.join(HERE, 'fonts'), os.path.expanduser('~/.fonts'), '/usr/share/fonts', '/usr/local/share/fonts', '/mnt/user-data/uploads']:
        hit = glob.glob(os.path.join(d, '**', name), recursive=True)
        if hit: return hit[0]
    if name.startswith(('Iansui', 'Bpmf')): sys.exit(f'找不到字型 {name}，請放到 fonts/ 資料夾')
    return None
PHONIC = os.path.join(HERE, 'data', 'phonic_table_A.txt')
from fontTools.ttLib import TTFont
from PIL import Image, ImageDraw, ImageFont
D = json.load(open(sys.argv[1], encoding='utf-8'))
IANSUI = find_font('Iansui-Regular.ttf')
FALLBACK = [f for f in [find_font('LXGWWenKaiTC-Medium.ttf'), find_font('NotoSerifCJK-Regular.ttc'), find_font('NotoSansCJK-Regular.ttc')] if f]
os.chdir(HERE)
cm = TTFont(IANSUI).getBestCmap()
comps = set()
for row in D['shapeRows']:
    if row == 'PAGEBREAK': continue
    for g in row: comps.update(g['comp'])
for e in D['expand']: comps.update(e['comp'])
import shutil
shutil.rmtree('comp_img', ignore_errors=True)
os.makedirs('comp_img', exist_ok=True)
idx = {}
for c in sorted(comps):
    if ord(c) in cm: continue
    for fp in FALLBACK:
        f = TTFont(fp, fontNumber=2) if fp.endswith('.ttc') else TTFont(fp)
        if ord(c) in f.getBestCmap():
            font = ImageFont.truetype(fp, 400, index=2 if fp.endswith('.ttc') else 0)
            idx[c] = {}
            for tag, col, sw in [('k', (0, 0, 0, 255), 0), ('r', (192, 0, 0, 255), 10)]:
                img = Image.new('RGBA', (440, 440), (0, 0, 0, 0))
                d = ImageDraw.Draw(img)
                d.text((220, 220), c, font=font, fill=col, anchor='mm', stroke_width=sw, stroke_fill=col)
                name = f'U{ord(c):X}_{tag}.png'; img.save('comp_img/' + name); idx[c][tag] = name
            print('image', c, os.path.basename(fp)); break
json.dump(idx, open('comp_img/index.json', 'w', encoding='utf-8'), ensure_ascii=False)

# 多音字檢查（ㄅ注音芫荽預設讀音＝讀音表第一個）
print('\n=== 以下句子含多音字，「=」後面是會印出的讀音；讀錯的字請在 JSON 該字後面加 {n} 指定第 n 個讀音 ===')
tbl = {}
for line in open(PHONIC, encoding='utf-8'):
    p = line.rstrip('\n').split('\t')
    if len(p) > 4: tbl[p[0]] = p[3:]
texts = [re.sub(r'\[[^\]]*\]', '', w) for p in D['poly'] for w, _ in p['words']]
texts += [re.sub(r'\[[^\]]*\]', '＿', q['text']) for q in D['polyQ']]  # 作答字不檢查
texts += [q['text'] for g in D['pick'] for q in g['qs']]
for t in texts:
    chs = re.findall(r'(.)(\{\d\})?', t)
    flags = [f'{c}{v or ""}={tbl[c][int(v[1])-1] if v else tbl[c][0]}({"/".join(tbl[c])})' for c, v in chs if c in tbl]
    if flags: print(t, ' -> ', '  '.join(flags))
