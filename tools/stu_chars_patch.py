"""學生練習「生字練習」分步驟版面（10 吋 ChromeOS 平板，可視範圍約 1280×690）
參考四年級網站 yotindo0808/guoyu4 的 commit ac79800。
第一步「國字＋注音」同一頁、第二步「部首」另一頁；畫面太矮時改成國字／注音／部首三步。
寫字格與注音鍵依實際可用高度計算。投影上課不受影響（charPractice 只用在學生練習）。
build_lock.py 會呼叫 apply(s)；也可單獨執行：python3 stu_chars_patch.py 輸入.html 輸出.html
"""
import sys

PATCHES = [
    # 寫字格大小可由外部指定
    ('function writeTask(c, onDone) {\n  const q = qid(`寫國字：${c.c}`); const box = el("div", { class: "ptask" });\n  const size = Math.max(160, Math.min(240, Math.floor(innerHeight * .27)));',
     'function writeTask(c, onDone, o = {}) {\n  const q = qid(`寫國字：${c.c}`); const box = el("div", { class: "ptask" });\n  const size = o.size || Math.max(160, Math.min(240, Math.floor(innerHeight * .27)));'),
    # 生字練習分步驟
    ('  const tasks = el("div", { class: "cptasks" }); tasks.append(writeTask(c, fin), zhuyinTask(c, fin), radicalTask(c, fin));\n  wrap.append(head, tasks);\n  return slide("cps", wrap);',
     r'''  /* 學生練習分步驟：寫國字＋拼注音一頁、選部首一頁；作答區太矮時國字、注音再分開，一次做一件。
     寫字格與注音鍵依實際可用高度計算（10 吋平板約 1280×690） */
  wrap.classList.add("cp2"); let tight = null, cur = 0, groups = [];
  const zt = zhuyinTask(c, () => mark()); let wt = null;
  zt.querySelectorAll(".zkt").forEach(b => { const tn = b.firstChild; if (tn && tn.nodeType === 3) b.replaceChild(el("span", { class: "tm" }, tn.data), tn); });   /* 聲調符號單獨放大 */
  const rt = radicalTask(c, () => mark());
  const p1 = el("div", { class: "cpp1" }), p2 = el("div", { class: "cpp2" }); p2.append(rt);
  const steps = el("span", { class: "cpsteps" }); head.append(steps);
  const done = t => t && t.classList.contains("pdone");
  const limit = () => { const sl = wrap.closest(".slide"); const r = sl.getBoundingClientRect(); return r.bottom - parseFloat(getComputedStyle(sl).paddingBottom || 0) - 9; };
  function mark() { fin(); paintSteps(); const g = groups[cur]; if (g && g.every(done) && cur < groups.length - 1) setTimeout(() => go(cur + 1), 900); }
  function paintSteps() { [...steps.children].forEach((b, k) => { b.classList.toggle("on", k === cur); b.classList.toggle("ok", !!groups[k] && groups[k].every(done)); }); }
  function go(k) { cur = k; const g = groups[k]; [wt, zt].forEach(t => { if (t) t.hidden = !g.includes(t); }); p1.hidden = !g.some(t => t === wt || t === zt); p2.hidden = !g.includes(rt); p1.classList.toggle("one", g.length === 1); paintSteps(); const st = wrap.closest(".dstage"); if (st) requestAnimationFrame(() => fine(st)); }
  const lay = () => {
    const st = wrap.closest(".dstage"); if (!st || !wrap.offsetParent) return;
    const was = [p1.hidden, p2.hidden]; p1.hidden = false; p2.hidden = true;
    const top = p1.getBoundingClientRect().top; p1.hidden = was[0]; p2.hidden = was[1];
    const av = Math.max(200, limit() - top);
    const t = av < 360 || innerHeight > innerWidth;   /* 太矮或直式：國字、注音分開 */
    wrap.classList.toggle("tight", t);
    if (t !== tight) { tight = t; groups = t ? [[null], [zt], [rt]] : [[null, zt], [rt]]; steps.innerHTML = "";
      (t ? ["① 國字", "② 注音", "③ 部首"] : ["① 國字＋注音", "② 部首"]).forEach((n, k) => { const b = el("button", { type: "button", class: "cpstep" }, n); b.onclick = e => { e.stopPropagation(); go(k); }; steps.append(b); }); }
    const sz = Math.max(160, Math.min(440, Math.floor(Math.min(av - 92, innerWidth * (t ? .6 : .36)))));
    if (!wt || (wt._sz !== sz && !done(wt))) { const nw = writeTask(c, () => mark(), { size: sz }); nw._sz = sz; if (wt) wt.replaceWith(nw); else p1.prepend(nw); wt = nw; }
    groups[0][0] = wt;
    const rows = t ? 7.4 : 6.5, extra = t ? 40 : 110;
    wrap.style.setProperty("--kh", Math.max(22, Math.min(70, Math.floor((av - extra) / rows - 6))) + "px");
    go(Math.min(cur, groups.length - 1));
  };
  /* 排好後實際量測剩下的高度，把注音鍵與寫字格放大填滿（不超過作答區） */
  const lastBottom = t => t.lastElementChild ? t.lastElementChild.getBoundingClientRect().bottom : t.getBoundingClientRect().bottom;
  const fine = st => {
    if (!wrap.offsetParent) return; const sb = limit();
    if (!zt.hidden) { const kh = parseFloat(wrap.style.getPropertyValue("--kh")) || 40; const nk = Math.max(22, Math.min(76, Math.floor(kh + (sb - lastBottom(zt)) / 6.8))); if (nk !== kh) wrap.style.setProperty("--kh", nk + "px"); }
    if (wt && !wt.hidden && !done(wt)) { const cap = Math.min(440, Math.floor(innerWidth * (tight ? .6 : .36))); const nsz = Math.max(160, Math.min(cap, wt._sz + Math.floor(sb - lastBottom(wt)))); if (Math.abs(nsz - wt._sz) >= 6) { const nw = writeTask(c, () => mark(), { size: nsz }); nw._sz = nsz; wt.replaceWith(nw); groups[0][0] = wt = nw; } }
  };
  p1.append(zt); wrap.append(head, p1, p2);
  const sl = slide("cps", wrap); sl.dataset.nofit = "1"; sl.onshow = () => requestAnimationFrame(lay);
  let rzT = 0; addEventListener("resize", () => { if (!wrap.isConnected) return; clearTimeout(rzT); rzT = setTimeout(() => { tight = null; lay(); }, 120); });
  return sl;'''),
]

CSS = r'''
<style id="cp2css">
/* ── 學生練習「生字練習」分步驟、依螢幕高度放大（10 吋平板） ── */
.cp2 .cphead { gap: 10px; flex-wrap: nowrap; }
.cp2 .cphead .hint { flex: 1 1 auto; min-width: 0; }
.cpsteps { display: flex; gap: 8px; margin-left: auto; flex: none; }
.cpstep { font-family: var(--ui); font-size: 17px; padding: .3em .9em; border-radius: 999px; border: 2px solid var(--line); background: var(--paper); color: var(--ink); cursor: pointer; white-space: nowrap; }
.cpstep.on { background: var(--accent); border-color: var(--accent); color: #fff; }
.cpstep.ok::after { content: " √"; }
.cp2.tight .cpstep { font-size: 15px; padding: .15em .7em; }
.cp2.tight .cphead > .hint { display: none; }
.cpp1 { display: grid; grid-template-columns: auto minmax(0, 1fr); gap: 14px; align-items: stretch; }
.cpp1 .ptask { justify-content: flex-start; }
.cpp1 .ptask .btn { font-size: 18px; padding: .35em .9em; }
.cp2 .zkb { width: 100%; gap: 6px; }
.cp2 .zrow { display: flex; flex-wrap: nowrap; gap: 6px; justify-content: center; width: 100%; }
.cp2 .zk { flex: 0 0 calc((100% - 42px) / 8); min-width: 0; border-width: 2px; border-radius: 10px; height: var(--kh, 56px); font-size: calc(var(--kh, 56px) * .58); }
.cp2 .ztones .zk { flex: 1 1 0; height: calc(var(--kh, 56px) * 1.25); }
.cp2 .zkt { display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 2px; line-height: 1; overflow: hidden; padding: 0; }
.cp2 .zkt .tm { display: block; font-size: calc(var(--kh, 56px) * 1.05); line-height: 1; height: .5em; overflow: visible; transform: translateY(.08em); }
.cp2 .zkt small { font-size: max(14px, calc(var(--kh, 56px) * .32)); line-height: 1.1; color: var(--muted); }
.cp2 .zans { font-size: calc(var(--kh, 56px) * .62); min-width: 4em; }
.cp2 .zansrow .btn { font-size: 18px; padding: .35em .9em; }
.cp2 .phead { display: none; }   /* 右上角步驟按鈕已標示，省下高度 */
.cp2 .ptask { padding: 6px 10px; gap: 6px; }
.cp2 .pres { font-size: 17px; min-height: 1.3em; }
.cp2 .cphead { min-height: 0; }
.cp2 .cphead .bigsay { transform: none; }
.cpp2 { display: flex; justify-content: center; }
.cpp2 .ptask { min-width: min(720px, 90%); padding: 18px; }
.cpp2 .ropt { min-width: 6em; padding: 14px 18px; }
.cpp2 .ropt .rg { font-size: 64px; }
.cpp2 .ropt small { font-size: 17px; }
.cp2 .cpp1[hidden], .cp2 .cpp2[hidden], .cp2 .ptask[hidden] { display: none; }
.cpp1.one { grid-template-columns: 1fr; justify-items: center; }
.cpp1.one .ptask { width: min(100%, 900px); }
/* 只在「生字練習」這一頁、畫面不夠高時收窄外框（其他頁面不變） */
@media (max-height: 760px) {
  html:not(.proj) .deck:has(.slide.cps.in) .dhint { display: none; }
  html:not(.proj) .deck:has(.slide.cps.in) .dtop { min-height: 0; }
  html:not(.proj) .deck:has(.slide.cps.in) .dbot { flex-wrap: nowrap; gap: 8px; }
  html:not(.proj) .deck:has(.slide.cps.in) .dbot .dots { order: 0; flex: 1 1 auto; flex-basis: auto; min-width: 0; flex-wrap: nowrap; overflow-x: auto; justify-content: flex-start; }
  html:not(.proj) .deck:has(.slide.cps.in) .dbot .dot { width: 28px; height: 28px; min-width: 28px; font-size: 13px; padding: 0; flex: none; }
  html:not(.proj) .deck:has(.slide.cps.in) .dbot .nav { padding: 6px 14px; flex: none; }
  html:not(.proj) .deck:has(.slide.cps.in) .dbot .dtools { flex: none; }
}
</style>
'''

def apply(s):
    if 'id="cp2css"' in s:
        return s
    for old, new in PATCHES:
        if s.count(old) != 1:
            print("⚠️ 生字練習分步驟：找不到要修改的程式（原始檔可能已更動），這次沒有套用：\n" + old[:80], file=sys.stderr)
            return s
        s = s.replace(old, new, 1)
    i = s.index("</head>")
    return s[:i] + CSS + s[i:]

if __name__ == "__main__":
    src, out = sys.argv[1:3]
    open(out, "w", encoding="utf-8").write(apply(open(src, encoding="utf-8").read()))
