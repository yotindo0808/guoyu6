"""產生「課文加密」測試版：不改動原網站，只輸出另一個 HTML。
用法：python3 build_locktest.py 原始index.html 芫荽體.ttf 輸出.html 密碼
"""
import base64, io, json, os, re, sys, html
from PIL import Image, ImageDraw, ImageFont
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes

src, font_path, out, pw = sys.argv[1:5]
TEST = (sys.argv[5] if len(sys.argv) > 5 else "test") == "test"
ITER = 150000
NUMS = "一二三四五六七八九十"

s = open(src, encoding="utf-8").read()
key0 = "const LESSONS = "
i = s.index(key0) + len(key0)
obj, end = json.JSONDecoder().raw_decode(s, i)

font = ImageFont.truetype(font_path, 120)

def glyph_png(ch, size):
    w, h = size
    im = Image.new("RGB", (w, h), "white")
    d = ImageDraw.Draw(im)
    pink = (246, 196, 206)
    for x in range(0, w, 8):  # 田字格虛線
        d.line([(x, h // 2), (x + 4, h // 2)], fill=pink, width=1)
    for y in range(0, h, 8):
        d.line([(w // 2, y), (w // 2, y + 4)], fill=pink, width=1)
    bb = d.textbbox((0, 0), ch, font=font)
    tw, th = bb[2] - bb[0], bb[3] - bb[1]
    d.text(((w - tw) / 2 - bb[0], (h - th) / 2 - bb[1]), ch, font=font, fill=(60, 60, 60))
    buf = io.BytesIO(); im.save(buf, "PNG", optimize=True)
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()

sealed_plain = {}
for lid, L in obj.items():
    real_text = L.get("text") or []
    real_img = [c.get("img", "") for c in L.get("cards", [])]
    sealed_plain[lid] = {"text": real_text, "img": real_img}
    ph = []
    for n, p in enumerate(real_text):
        words, seen = [], set()
        for w in re.findall(r'data-w="([^"]+)"', p):
            if w not in seen:
                seen.add(w); words.append(w)
        hidden = "".join(f'<button type="button" class="w" data-w="{html.escape(w)}">{html.escape(w)}</button>' for w in words)
        no = NUMS[n] if n < len(NUMS) else str(n + 1)
        tl = (L.get("tlabel") or [])
        where = f"「{tl[n]}」" if n < len(tl) else f"第{no}段課文"
        ph.append(
            f'<span class="lockp">🔒 {where}請翻開課本閱讀。'
            f'<button type="button" class="btn unlockbtn">🔑 老師解鎖</button></span>'
            f'<span class="lockw" hidden>{hidden}</span>')
    L["text"] = ph
    for c in L.get("cards", []):
        b = base64.b64decode(c["img"].split(",", 1)[1])
        c["img"] = glyph_png(c["c"], Image.open(io.BytesIO(b)).size)

# 加密（PBKDF2-SHA256 → AES-GCM），網頁裡只留下密文
salt, iv = os.urandom(16), os.urandom(12)
k = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=ITER).derive(pw.encode())
ct = AESGCM(k).encrypt(iv, json.dumps(sealed_plain, ensure_ascii=False).encode(), None)
b64 = lambda x: base64.b64encode(x).decode()
sealed = {"s": b64(salt), "i": b64(iv), "n": ITER, "c": b64(ct)}

s = s[:i] + json.dumps(obj, ensure_ascii=False) + s[end:]

lock_css = """
<style id="lockcss">
.lockp{display:block;padding:14px 18px;border:2px dashed #c9b28a;border-radius:12px;background:#fffaf0;color:#6b5a3a;line-height:1.8}
.lockp .unlockbtn{margin-left:.6em;font-size:.85em}
html:not(.proj) .unlockbtn{display:none}
#lockbtn{font-family:var(--ui);font-size:13px;border:1px solid rgba(255,255,255,.6);background:transparent;color:#fff;border-radius:8px;padding:4px 10px;cursor:pointer;flex:none;white-space:nowrap}
#lockbtn.on{background:#e8f5ee;color:#1d4a3a}
html:not(.proj) #lockbtn,html.tmode #lockbtn{display:none}
#lockdlg h3{color:#1d4a3a}
#testtag{font-family:var(--ui);background:#b3432f;color:#fff;font-size:12px;padding:3px 9px;border-radius:999px;flex:none;white-space:nowrap}
#lockdlg{position:fixed;inset:0;background:rgba(0,0,0,.45);display:none;align-items:center;justify-content:center;z-index:10000}
#lockdlg.show{display:flex}
#lockdlg .bx{font-family:var(--ui);color:#333;background:#fff;border-radius:14px;padding:22px 24px;width:min(420px,90vw);box-shadow:0 8px 30px rgba(0,0,0,.25)}
#lockdlg h3{margin:0 0 .4em}
#lockdlg p{margin:.3em 0 .8em;font-size:.92em;color:#555;line-height:1.6}
#lockdlg input{width:100%;box-sizing:border-box;font-size:1.1em;padding:8px 10px;border:2px solid #bbb;border-radius:8px}
#lockdlg .err{color:#b3261e;min-height:1.4em;font-size:.9em;margin-top:.4em}
#lockdlg .acts{display:flex;gap:10px;justify-content:flex-end;margin-top:10px}
#lockdlg .bx{width:min(520px,92vw)!important;max-height:92vh;overflow:auto}
@media (max-height:620px){#lockdlg .lkbub{font-size:.85em;line-height:1.6;padding:9px 12px}#lockdlg .bx{padding:14px 18px}}
#lockdlg .lkbub{position:relative;background:#fff8e1;border:2.5px solid #f0a33a;border-radius:14px;padding:12px 15px;margin:.2em 0 1em;font-size:.95em;line-height:1.75;color:#4a3a1a}
#lockdlg .lkbub:after{content:"";position:absolute;left:28px;bottom:-11px;width:18px;height:18px;background:#fff8e1;border-right:2.5px solid #f0a33a;border-bottom:2.5px solid #f0a33a;transform:rotate(45deg)}
#lockdlg .lkbub b{color:#a35a00}
#lockdlg .lkhint{font-size:.95em;color:#1d4a3a;font-weight:bold;margin:.2em 0 .5em}
#lockdlg .lknote{color:#b3261e;font-weight:bold;margin:.2em 0 .6em}
.crline{font-family:var(--ui);font-size:12.5px;line-height:1.7;opacity:.75;text-align:center;margin:1.2em auto 0;max-width:46em}
.crcard ol{padding-left:1.4em;line-height:1.85;margin:.4em 0 0}
.crcard li{margin:.25em 0}
.crcard{margin-top:16px}
.crcard h3{margin:0 0 .4em}
.gl{margin:0;padding-left:1.3em;line-height:1.85}
.gl li{margin:.15em 0}
.gmore summary{cursor:pointer;font-weight:bold}
.crcard a{color:var(--accent);word-break:break-all}
.hmsg{text-align:center;margin:1em 0 0}
.shb{display:inline-block;margin:2px 4px 2px 0;padding:4px 12px;font-size:.92em;text-decoration:none}
.linkbtn{font:inherit;color:inherit;background:none;border:none;border-bottom:2px solid currentColor;padding:0 .1em;margin:0 .15em;cursor:pointer;font-weight:bold}
#msgdlg{position:fixed;inset:0;background:rgba(0,0,0,.45);display:none;align-items:center;justify-content:center;z-index:10001}
#msgdlg.show{display:flex}
#msgdlg .bx{font-family:var(--ui);color:#333;background:#fff;border-radius:14px;padding:20px 24px;width:min(540px,92vw);max-height:92vh;overflow:auto;box-shadow:0 8px 30px rgba(0,0,0,.25)}
#msgdlg h3{margin:0 0 .4em;color:#1d4a3a}
#msgdlg .mh{font-size:.93em;line-height:1.7;color:#4a3a1a;background:#fff8e1;border:2px solid #f0a33a;border-radius:12px;padding:9px 13px;margin:.2em 0 .8em}
#msgdlg .mf{display:block;font-size:.92em;margin:.35em 0;color:#444}
#msgdlg input,#msgdlg textarea{display:block;width:100%;box-sizing:border-box;font:inherit;font-size:1.05em;padding:7px 10px;border:2px solid #bbb;border-radius:8px;margin-top:4px}
#msgdlg .mcnt{display:block;text-align:right;font-size:.8em;color:#888}
#msgdlg .mhp{position:absolute;left:-9999px;width:1px;height:1px;overflow:hidden}
#msgdlg .mpriv{font-size:.82em;color:#777;margin:.3em 0}
#msgdlg .merr{color:#b3261e;min-height:1.3em;font-size:.9em}
#msgdlg .acts{display:flex;gap:10px;justify-content:flex-end;margin-top:8px}
.mlist{display:flex;flex-direction:column;gap:12px;margin-top:10px}
.mitem{border:1.5px solid rgba(127,127,127,.4);border-radius:12px;padding:10px 14px}
.mitem.unread{border-color:#f0a33a;box-shadow:inset 4px 0 0 #f0a33a}
.mhead{display:flex;gap:12px;align-items:center;flex-wrap:wrap;font-size:.92em}
.mtime{opacity:.7}
.mst{margin-left:auto;font-size:.82em;padding:1px 9px;border-radius:999px;border:1px solid currentColor;opacity:.85}
.mst.u{color:#f0a33a}.mst.r{color:#5bbf8f}
.mtext{white-space:pre-wrap;line-height:1.75;margin:.4em 0}
.mreply{white-space:pre-wrap;line-height:1.7;border-left:3px solid #5bbf8f;padding:4px 10px;margin:.4em 0;opacity:.9}
.mrl{display:block;font-size:.82em;opacity:.75}
.mrbox textarea{width:100%;box-sizing:border-box;font:inherit;padding:7px 10px;border-radius:8px}
</style>
"""

lock_js = """
<script id="lockjs">
const SEALED = __SEALED__;
const PLACEHOLDER = {}; Object.keys(LESSONS).forEach(id => { const L0 = LESSONS[id]; PLACEHOLDER[id] = { text: (L0.text || []).slice(), img: (L0.cards || []).map(c => c.img) }; });
let UNLOCKED = false;
const ub = s => Uint8Array.from(atob(s), ch => ch.charCodeAt(0));
async function deriveKey(pw) {
  const base = await crypto.subtle.importKey("raw", new TextEncoder().encode(pw), "PBKDF2", false, ["deriveKey"]);
  return crypto.subtle.deriveKey({ name: "PBKDF2", salt: ub(SEALED.s), iterations: SEALED.n, hash: "SHA-256" }, base, { name: "AES-GCM", length: 256 }, true, ["decrypt"]);
}
function applyData(data) {
  Object.keys(data).forEach(id => { const L0 = LESSONS[id]; if (!L0) return; L0.text = data[id].text; (L0.cards || []).forEach((c, k) => { if (data[id].img[k]) c.img = data[id].img[k]; }); });
}
async function openWithKey(key) {
  const pt = await crypto.subtle.decrypt({ name: "AES-GCM", iv: ub(SEALED.i) }, key, ub(SEALED.c));
  applyData(JSON.parse(new TextDecoder().decode(pt))); UNLOCKED = true; paintLockBtn();
  if (page() === "lesson") render();
}
function relock() {
  Object.keys(PLACEHOLDER).forEach(id => { const L0 = LESSONS[id]; L0.text = PLACEHOLDER[id].text.slice(); (L0.cards || []).forEach((c, k) => c.img = PLACEHOLDER[id].img[k]); });
  UNLOCKED = false; try { sessionStorage.removeItem("kwkey"); } catch (e) {}
  paintLockBtn(); if (page() === "lesson") render();
}
function paintLockBtn() { const b = document.getElementById("lockbtn"); if (b) { b.textContent = UNLOCKED ? "🔓 課文已解鎖" : "🔒 課文已上鎖"; b.classList.toggle("on", UNLOCKED); b.title = UNLOCKED ? "按一下重新上鎖" : "按一下輸入密碼解鎖"; } }
let AFTER_UNLOCK = null;
function askPw(note, then) {
  const d = document.getElementById("lockdlg"); d.classList.add("show"); AFTER_UNLOCK = then || null;
  const n = d.querySelector(".lknote"); n.textContent = typeof note === "string" ? note : ""; n.hidden = !n.textContent;
  const inp = d.querySelector("input"); inp.value = ""; d.querySelector(".err").textContent = ""; setTimeout(() => inp.focus(), 50);
}
async function tryPw() {
  const d = document.getElementById("lockdlg"); const inp = d.querySelector("input"); const err = d.querySelector(".err"); const go = d.querySelector(".go");
  if (!inp.value) { err.textContent = "請輸入密碼。"; return; }
  go.disabled = true; err.textContent = "解鎖中……";
  try {
    const key = await deriveKey(inp.value); await openWithKey(key);
    try { const raw = await crypto.subtle.exportKey("raw", key); sessionStorage.setItem("kwkey", btoa(String.fromCharCode(...new Uint8Array(raw)))); } catch (e) {}
    d.classList.remove("show");
    if (AFTER_UNLOCK) { const f = AFTER_UNLOCK; AFTER_UNLOCK = null; f(); }
  } catch (e) { err.textContent = "密碼不正確，請再試一次。"; }
  go.disabled = false;
}

/*__MSGJS__*/
/* 紙本學習單：生字講義需課文密碼，其他學習單直接下載 */
const SHEETS = __SHEETS__;
tabB5 = function (body) {
  const c = card("紙本學習單", "", "");
  c.append(el("p", { class: "hint" }, "🔒 生字講義有彩色生字圖，需要課文密碼。其他學習單不需要密碼：PDF 可以直接列印，Word／PowerPoint 可以自己修改。"));
  const sel = el("select", { class: "tsel" }); LIST.filter(([id]) => LESSONS[id]).forEach(([id, n]) => sel.append(el("option", { value: id }, n)));
  sel.value = LESSONS[cur.lesson] ? cur.lesson : sel.value;
  const wrap = el("div", { class: "tscroll" });
  const link = (f, label, name) => f ? `<a class="btn shb" href="${f}" download="${name}">${label}</a>` : "";
  const draw = () => {
    const id = sel.value, no = plainText(LESSONS[id].no), S = SHEETS[id] || {};
    const row = (n, paper, stu, tch, edit) => `<tr><td>${n}</td><td>${paper}</td><td>${stu}</td><td>${tch}</td><td>${edit}</td></tr>`;
    const wip = '<span class="hint">製作中</span>';
    const one = (k, n, paper) => { const x = S[k]; if (!x) return row(n, paper, wip, "—", "—");
      return row(n, paper, link(x.pdf, "PDF", `${no}_${n}.pdf`),
        x.tpdf ? link(x.tpdf, "PDF", `${no}_${n}_教師版.pdf`) : (x.tWip ? wip : "—"),
        [link(x.doc, x.doc && x.doc.endsWith(".pptx") ? "PowerPoint" : "Word", `${no}_${n}${x.doc ? x.doc.slice(x.doc.lastIndexOf(".")) : ""}`),
         link(x.tdoc, x.tdoc && x.tdoc.endsWith(".pptx") ? "教師版 PowerPoint" : "教師版 Word", `${no}_${n}_教師版${x.tdoc ? x.tdoc.slice(x.tdoc.lastIndexOf(".")) : ""}`)].filter(Boolean).join(" ") || "—"); };
    wrap.innerHTML = `<table class="ttable"><thead><tr><th>學習單</th><th>紙張</th><th>學生版</th><th>教師版</th><th>可編輯檔</th></tr></thead><tbody>
      <tr><td>🔒 生字講義</td><td>B5</td><td><button type="button" class="btn solid shb" id="b5go">下載</button></td><td>—</td><td>—</td></tr>
      ${one("words", "詞語選詞填寫", "A4")}${one("zx", S.zxp ? "字音字形學習單（上課用）" : "字音字形講義", "B5")}${S.zxp ? one("zxp", "字音字形綜合練習", "B5") : ""}${one("jx", "句型練習單（直書）", "B5")}</tbody></table>`;
    wrap.querySelector("#b5go").onclick = () => { L = LESSONS[sel.value]; openPrint(); };
  };
  sel.onchange = draw; draw();
  c.append(tools(sel), wrap); body.append(c);
};
if (page() === "teacher") renderTeacher();
{ const _rc = readChallenge; readChallenge = function (para, label) { return UNLOCKED ? _rc(para, label) : el("span", { class: "lockread" }); }; }
/* 著作權說明（測試版） */
const CR_LINE = "本站部分內容引用或改寫自康軒版《國語》六上、雄::gsyan 筆順練習及教育部辭典資料，著作權屬原權利人，僅供課堂教學使用。詳見「使用說明」。";
function copyrightCard() {
  const c = el("section", { class: "card crcard" });
  c.innerHTML = '<h3>著作權說明</h3><ol>' +
    '<li>課文引用自康軒文教事業《國小國語》第十一冊（六年級上學期），作者依各課標示；課文大意、段落大意、課文結構及部分題目、例句，依康軒備課資料整理或改寫。著作權屬康軒文教事業及原作者所有。</li>' +
    '<li>彩色生字圖取自「雄::gsyan」網站（顏國雄）的 HTML5 FUN 筆順練習，著作權屬原作者所有。網址：<a href="https://gsyan888.blogspot.com/p/stroke.html" target="_blank" rel="noopener">gsyan888.blogspot.com/p/stroke.html</a></li>' +
    '<li>詞語解釋、字音、部首參考教育部《國語辭典簡編本》《國語小字典》等辭典資料。</li>' +
    '<li>情境圖、簡單說及部分例句由 LDG 製作。</li>' +
    '<li>以上內容僅在學校課堂教學必要範圍內使用。課文全文與彩色生字圖已加密，只開放給網站管理者認識的老師解鎖。權利人如認為本站有不當使用，請透過<button type="button" class="linkbtn openmsg">✉️ 站內信</button>與網站管理者聯絡，將立即處理。</li></ol>';
  return c;
}
{ const _th = tabHelp; tabHelp = function (body) {
  const q = el("section", { class: "card crcard" });
  q.innerHTML = '<h3>使用說明</h3><ul class="gl">' +
    '<li><b>只想上課</b>：首頁按「投影上課」，不用註冊。下方有全螢幕、畫筆、遮住選項、抽籤、計時；題目卡按「公布答案」。</li>' +
    '<li><b>要收學生作答</b>：到「教師管理」註冊 → 建組別 → 把「學生連結」或 QR code 給學生。</li>' +
    '<li><b>控制練習範圍</b>：後台「今日任務」勾選小節和題數；投影時也可以按「開放給學生」。</li>' +
    '<li><b>看結果</b>：後台「作答紀錄」。標示「待老師確認」的，請看明細判斷。</li>' +
    '<li><b>學生平板</b>會一直停在學生練習；老師要用時，按左下角「老師」輸入帳號密碼。</li></ul>';
  const k = el("section", { class: "card crcard" });
  k.innerHTML = '<h3>課文密碼與註冊</h3><ul class="gl">' +
    '<li>課文全文、彩色生字圖和生字講義下載需要<b>課文密碼</b>，只提供給網站管理者認識的老師。密碼提示：管理者 IG 頭像的英文。</li>' +
    '<li>註冊帳號只用來收學生作答紀錄，<b>不能代替課文密碼</b>。</li>' +
    '<li>其他教材、練習和紙本學習單（詞語、字音字形、句型）都不需要密碼。</li></ul>';
  const pv = el("section", { class: "card crcard" });
  pv.innerHTML = '<h3>隱私重點</h3><ul class="gl">' +
    '<li>學生作答在平板上先加密才送出，只有該組老師登入後看得到；網站管理者只看得到帳號名稱、組別名稱和筆數。</li>' +
    '<li>註冊時會拿到<b>救援碼</b>，請存好。密碼和救援碼都弄丟，紀錄就找不回來。</li>' +
    '<li>帳號、組別名稱不要用學生全名或學校全名。口說、手寫作答會用到 Google／Apple 的辨識服務；語音報讀使用 Google 雲端語音（只傳送要唸的文字）。</li></ul>';
  const more = el("details", { class: "card crcard gmore" }, '<summary>看完整說明</summary>'); const tmp = el("div"); _th(tmp); tmp.querySelectorAll("details").forEach(x => x.open = true); more.append(...tmp.childNodes);
  body.append(q, k, pv, copyrightCard()); const mc = card("聯絡網站管理者", "", "對網站有問題、建議，或有特殊需求，可以用站內信留言。留言只有網站管理者看得到。"); mc.append(tools(el("button", { type: "button", class: "btn solid openmsg" }, "✉️ 寫站內信"))); mc.classList.add("crcard"); body.append(mc, more); }; }
{ const _rh = renderHome; renderHome = function () { _rh(); const w = document.querySelector("#main .homewrap"); if (w) { w.append(el("p", { class: "hmsg" }, '<button type="button" class="btn openmsg">✉️ 聯絡網站管理者</button>')); w.append(el("p", { class: "crline" }, CR_LINE)); } }; }
if (page() === "home") renderHome(); if (page() === "guide") renderGuide();

(function initLock() {
  document.head.insertAdjacentHTML("beforeend", "");
  const b = document.createElement("button"); b.type = "button"; b.id = "lockbtn"; b.className = "mset";
  b.onclick = () => UNLOCKED ? relock() : askPw();
  const bar = document.querySelector("#bar .row"); bar.insertBefore(b, document.getElementById("mset"));
  paintLockBtn();
  if (__TEST__) document.querySelector("#bar .ver").insertAdjacentHTML("afterend", '<span id="testtag" title="測試版：課文加密，請勿給學生使用">測試版</span>');
  document.body.insertAdjacentHTML("beforeend", "" +
    '<div id="lockdlg" role="dialog" aria-modal="true" aria-labelledby="lockt"><div class="bx"><h3 id="lockt">🔑 課文解鎖</h3>' +
    '<p class="lknote" hidden></p>' +
    '<div class="lkbub"><b>為什麼需要密碼？</b><br>課文全文和彩色生字圖受著作權保護，只開放給網站管理者認識的老師使用。有沒有註冊帳號，都需要這組密碼。<br><b>沒有密碼也能照常上課：</b>課文請學生翻開課本，生字改用一般字體顯示，其他練習都不受影響。<br>想要密碼，請用<button type="button" class="linkbtn openmsg">✉️ 站內信</button>聯絡管理者。</div>' +
    '<p class="lkhint">🔑 密碼提示：管理者 IG 頭像的英文</p>' +
    '<input type="password" autocomplete="off" aria-label="密碼"><div class="err"></div>' +
    '<div class="acts"><button type="button" class="btn cancel">取消</button><button type="button" class="btn solid go">解鎖</button></div></div></div>');
  const d = document.getElementById("lockdlg");
  d.querySelector(".cancel").onclick = () => d.classList.remove("show");
  d.querySelector(".go").onclick = tryPw;
  d.querySelector("input").addEventListener("keydown", e => { if (e.key === "Enter") tryPw(); if (e.key === "Escape") d.classList.remove("show"); });
  document.addEventListener("click", e => { if (e.target.closest(".unlockbtn")) { e.preventDefault(); e.stopPropagation(); askPw(); } }, true);
  { const _op = openPrint; openPrint = function () { if (UNLOCKED) return _op(); const keep = L; askPw("下載生字講義需要課文密碼。", () => { L = keep; _op(); }); }; }
  let saved = null; try { saved = sessionStorage.getItem("kwkey"); } catch (e) {}
  if (saved) crypto.subtle.importKey("raw", ub(saved), "AES-GCM", true, ["decrypt"]).then(openWithKey).catch(() => {});
})();
</script>
""".replace("__SEALED__", json.dumps(sealed)).replace("__TEST__", "true" if TEST else "false").replace("__SHEETS__", open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "sheets.json"), encoding="utf-8").read()).replace("/*__MSGJS__*/", open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "msg_inject.js"), encoding="utf-8").read())
lock_js += "<script id=\"ttsjs\">\n" + open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "tts_inject.js"), encoding="utf-8").read() + "\n</script>\n"


TABS_OLD_O = '[["accts", "老師帳號"], ["legacy", "未加密的舊紀錄"], ["b5", "紙本學習單"]]'
TABS_NEW_O = '[["accts", "老師帳號"], ["msg", (me.info && me.info.unread) ? `站內信（${me.info.unread}）` : "站內信"], ["legacy", "未加密的舊紀錄"], ["b5", "紙本學習單"]]'
TABS_OLD_T = '["group", "組別管理"], ["b5", "紙本學習單"]]'
TABS_NEW_T = '["group", "組別管理"], ["b5", "紙本學習單"], ["msg", "站內信"]]'
MAP_OLD = 'accts: tabAccts, legacy: tabLegacy })[TD.tab](body);'
MAP_NEW = 'accts: tabAccts, legacy: tabLegacy, msg: tabMsg })[TD.tab](body);'
REG_PATCH = [
    ("<tr><td>投影上課、所有課程內容與教學工具（畫筆、遮住選項、抽籤、計時）</td><td>✓</td><td>✓</td></tr>",
     "<tr><td>投影上課、教學工具（畫筆、遮住選項、抽籤、計時）、其他課程內容</td><td>✓</td><td>✓</td></tr>\n<tr><td>課文全文、彩色生字圖</td><td>需課文密碼</td><td>需課文密碼</td></tr>"),
    ("<tr><td>下載生字講義（本頁下方）</td><td>✓</td><td>✓</td></tr>",
     "<tr><td>下載生字講義（本頁下方「紙本學習單」）</td><td>需課文密碼</td><td>需課文密碼</td></tr>\n<tr><td>下載其他紙本學習單（詞語、字音字形、句型）</td><td>✓</td><td>✓</td></tr>"),
    ("註冊免費，只要自訂帳號和密碼。學生的作答會加密，只有你看得到，詳見下方「隱私與安全說明」。",
     "註冊免費，只用來收學生作答紀錄，不能代替課文密碼。課文密碼只提供給網站管理者認識的老師，提示：管理者 IG 頭像的英文。學生的作答會加密，只有你看得到。"),
    ("只用來上課的話，不註冊也能使用全部教學功能。",
     "只用來上課的話不用註冊；課文全文和生字講義需要課文密碼，有沒有註冊都一樣。"),
    ("box.append(lc, rc, diff, b5, privacyCard(false), guideCard(false));",
     "const more = card(\"使用說明與隱私\", \"\", \"完整的使用說明、隱私說明和著作權說明，都在「使用說明」頁。\"); const gm = el(\"button\", { type: \"button\", class: \"btn\" }, \"看使用說明\"); gm.onclick = () => { location.hash = \"guide\"; }; more.append(tools(gm));\n  box.append(lc, rc, diff, b5, more);"),
]
for a, b in REG_PATCH:
    assert s.count(a) == 1, a[:40]
    s = s.replace(a, b)
for a, b in [(TABS_OLD_O, TABS_NEW_O), (TABS_OLD_T, TABS_NEW_T), (MAP_OLD, MAP_NEW)]:
    assert s.count(a) == 1, a
    s = s.replace(a, b)

s = s.replace("</head>", lock_css + "</head>", 1)
idx = s.rindex("</body>")
# 學生練習「生字練習」分步驟版面（10 吋平板），見 stu_chars_patch.py
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import stu_chars_patch
s = stu_chars_patch.apply(s)
# 平板浮動鍵盤：只改變高度時不重畫有作答框的卡片
_KB_OLD = 'window.addEventListener("resize", () => { clearTimeout(rzT); rzT = setTimeout(refit, 250); });'
_KB_NEW = 'let rzW = innerWidth; window.addEventListener("resize", () => { clearTimeout(rzT); /* 平板浮動鍵盤跳出或收起只改變高度：卡片有作答框時不重畫，避免鍵盤縮回、打好的字被清掉 */ const wChg = Math.abs(innerWidth - rzW) > 40; rzW = innerWidth; const ae = document.activeElement; const typing = ae && (ae.matches("input, textarea, [contenteditable]") && !ae.matches("[type=button],[type=radio],[type=checkbox]")); if (!wChg && (typing || host.querySelector("input:not([type=button]):not([type=radio]):not([type=checkbox]), textarea, [contenteditable=true]"))) return; rzT = setTimeout(refit, 250); });'
if _KB_OLD in s:
    s = s.replace(_KB_OLD, _KB_NEW, 1)
idx = s.rindex("</body>")  # 上面的替換會改變長度，要重新找位置
s = s[:idx] + lock_js + s[idx:]
if 'name="referrer"' not in s:
    s = s.replace('<meta name="robots"', '<meta name="referrer" content="no-referrer">\n<meta name="robots"', 1)
if TEST: s = s.replace("<title>", "<title>【測試版】", 1)
open(out, "w", encoding="utf-8").write(s)
print("ok", len(s), "cipher bytes", len(ct))
