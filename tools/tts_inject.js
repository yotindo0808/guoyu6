/* ── 雲端語音報讀（ChromeOS 無法安裝中文語音，內建只有機器腔 eSpeak）──
   改用 Google 雲端國語語音播放音檔；連不上時自動退回平板內建語音。
   網址加 ?tts=local 可強制使用平板內建語音（比對用）。 */
(function cloudTTS() {
  const FORCE_LOCAL = /[?&]tts=local\b/.test(location.search);
  const RATE = 1.4;            // 播放速度（1 = 原速；雲端與平板語音都用這個）
  const MAXLEN = 90;           // 每段最多字數（雲端服務單次上限約 200 字）
  const TIMEOUT = 7000;        // 幾毫秒沒開始播放就改用內建語音
  let cloudOK = !FORCE_LOCAL, failAt = 0;
  const cache = new Map();     // 文字 → Audio（同一句重播或預先載入）
  let cur = null, token = 0;

  const url = t => "https://translate.google.com/translate_tts?ie=UTF-8&client=tw-ob&tl=zh-TW&ttsspeed=1&q=" + encodeURIComponent(t);
  const fix = t => TTSFIX.reduce((s, [a, b]) => s.split(a).join(b), String(t).normalize("NFKC").replace(/[\u{E0100}-\u{E01EF}\uFE00-\uFE0F]/gu, ""));
  /* 切成短段：先依句號等切，太長再依逗號切，最後硬切 */
  function chunks(t) {
    t = t.replace(/\s+/g, " ").trim(); if (!t) return [];
    const out = [];
    const push = s => { s = s.trim(); if (!s) return; while (s.length > MAXLEN) { out.push(s.slice(0, MAXLEN)); s = s.slice(MAXLEN); } if (s) out.push(s); };
    const big = t.match(/[^。！？；!?;\n]+[。！？；!?;」』）\n]*/g) || [t];
    let buf = "";
    big.forEach(seg => {
      if (seg.length > MAXLEN) { if (buf) { push(buf); buf = ""; } (seg.match(/[^，、：,:]+[，、：,:]*/g) || [seg]).forEach(p => { if ((buf + p).length > MAXLEN) { push(buf); buf = p; } else buf += p; }); }
      else if ((buf + seg).length > MAXLEN) { push(buf); buf = seg; }
      else buf += seg;
    });
    push(buf);
    return out;
  }
  function audioFor(t) {
    let a = cache.get(t);
    if (!a) {
      a = new Audio(); a.preload = "auto"; a.src = url(t);
      a.addEventListener("error", () => cache.delete(t));
      cache.set(t, a);
      if (cache.size > 60) cache.delete(cache.keys().next().value);
    }
    return a;
  }
  function prefetch(t) { if (cloudOK && t) chunks(fix(t)).slice(0, 2).forEach(audioFor); }
  function localSpeak(text, opt) {
    if (!HAS_TTS) { opt.onend && opt.onend(); return; }
    speechSynthesis.cancel();
    const u = new SpeechSynthesisUtterance(text); u.lang = "zh-TW"; if (VOICE) u.voice = VOICE; u.rate = opt.rate || RATE;
    u.onend = () => opt.onend && opt.onend(); u.onerror = () => opt.onend && opt.onend();
    speechSynthesis.speak(u);
  }
  function halt() {
    token++;
    if (cur) { try { cur.pause(); cur.currentTime = 0; } catch (e) {} cur = null; }
    if (HAS_TTS) speechSynthesis.cancel();
  }
  window.ttsPrefetch = prefetch;

  speak = function (text, opt = {}) {
    if (!text) return;
    halt();
    text = fix(text);
    if (!cloudOK && failAt && Date.now() - failAt > 120000 && !FORCE_LOCAL) cloudOK = true; // 兩分鐘後再試雲端
    if (!cloudOK) { localSpeak(text, opt); return; }
    const parts = chunks(text), my = token;
    let k = 0, done = false;
    const finish = () => { if (done) return; done = true; if (my === token) { cur = null; opt.onend && opt.onend(); } };
    const fallback = from => { if (my !== token) return; cloudOK = false; failAt = Date.now(); if (cur) { try { cur.pause(); } catch (e) {} } cur = null; localSpeak(parts.slice(from).join(""), opt); done = true; };
    const next = () => {
      if (my !== token) return;
      if (k >= parts.length) { finish(); return; }
      const idx = k, a = audioFor(parts[k++]);
      if (k < parts.length) audioFor(parts[k]);         // 預先載入下一段
      cur = a; a.defaultPlaybackRate = RATE; a.playbackRate = RATE; a.preservesPitch = true;
      let started = false;
      const tm = setTimeout(() => { if (!started) fallback(idx); }, TIMEOUT);
      a.onplaying = () => { started = true; clearTimeout(tm); };
      a.onended = () => { clearTimeout(tm); a.onended = a.onerror = a.onplaying = null; try { a.currentTime = 0; } catch (e) {} next(); };
      a.onerror = () => { clearTimeout(tm); fallback(idx); };
      try { a.currentTime = 0; } catch (e) {}
      const p = a.play(); if (p && p.catch) p.catch(err => { clearTimeout(tm); if (err && err.name === "NotAllowedError") { if (my === token) { cur = null; done = true; localSpeak(parts.slice(idx).join(""), opt); } } else fallback(idx); });
    };
    next();
  };

  stopSpeak = function () {
    halt();
    document.querySelectorAll(".say.on").forEach(b => b.classList.remove("on"));
    if (window.CSS && CSS.highlights) CSS.highlights.delete("reading");
  };

  /* 逐句朗讀：唸這一句時先載入下一句，句與句之間不卡頓 */
  let raList = [];
  const _ra = readAloud;
  readAloud = function (container, btn) {
    raList = [];
    if (cloudOK && !btn.classList.contains("on")) {
      const c = container.cloneNode(true); c.querySelectorAll(".say, .zb").forEach(x => x.remove());
      const t = c.textContent.replace(/[\u{E0100}-\u{E01EF}]/gu, "");
      raList = (t.match(/[^。！？；]+[。！？；」』）]*/g) || []).map(s => fix(s).trim()).filter(Boolean);
      raList.slice(0, 2).forEach(prefetch);
    }
    return _ra(container, btn);
  };
  const _sp = speak;
  speak = function (text, opt) {
    _sp(text, opt);
    if (cloudOK && raList.length && text) { const j = raList.indexOf(fix(text).trim()); if (j >= 0 && raList[j + 1]) prefetch(raList[j + 1]); }
  };

  /* 平板沒有中文語音時，報讀按鈕原本會被藏起來；雲端可用時一律顯示 */
  if (!HAS_TTS) {
    const _sb = sayBtn;
    sayBtn = function (getText, label) { const b = _sb(getText, label); b.hidden = false; return b; };
  }
})();
