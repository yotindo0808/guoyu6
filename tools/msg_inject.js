/* ── 站內信（測試版） ── */
function msgErr(j) {
  const e = j && j.error;
  const M = { email: "請填寫正確的電子信箱。", limit: "留言太頻繁，請過幾個小時再試。", busy: "現在留言的人比較多，請稍後再試。",
    input: "請先寫留言內容。", msg: "找不到這則留言，可能已經刪除。",
    mail: "回覆信寄不出去：請先在 Apps Script 執行一次 authorizeMail，同意寄信權限後重新部署。",
    action: "後端還是舊版：請貼上新版 Code.gs，並在「管理部署作業」用「新版本」重新部署。" };
  return M[e] || errMsg(j);
}
function msgReady() { return API && !API.startsWith("__"); }
function openMsgDlg() {
  const ld = document.getElementById("lockdlg"); if (ld) ld.classList.remove("show");
  let d = document.getElementById("msgdlg");
  if (!d) { d = el("div", { id: "msgdlg", role: "dialog", "aria-modal": "true", "aria-labelledby": "msgt" }); document.body.append(d); }
  const asT = TD.me && !TD.me.owner;
  d.innerHTML = '<div class="bx"><h3 id="msgt">✉️ 聯絡網站管理者</h3>' +
    (asT ? `<p class="mh">你目前以「${esc(TD.me.acct)}」登入，管理者的回覆會出現在教師管理的「站內信」，不用留信箱。</p>`
         : '<p class="mh">沒有登入也可以留言，請留下電子信箱，管理者會寄信回覆。已註冊的老師可以先到「教師管理」登入再留言，回覆會出現在後台，不用留信箱。</p>') +
    '<label class="mf">稱呼（選填）<input class="mname" maxlength="30" autocomplete="off"></label>' +
    (asT ? "" : '<label class="mf">電子信箱（必填）<input class="mmail" type="email" maxlength="100" autocomplete="email"></label>') +
    '<label class="mf">留言內容<textarea class="mbody" maxlength="500" rows="3"></textarea><span class="mcnt">0 / 500</span></label>' +
    '<div class="mhp" aria-hidden="true"><input class="mweb" tabindex="-1" autocomplete="off"></div>' +
    '<p class="mpriv">留言只有網站管理者看得到' + (asT ? "。" : "；信箱只用來回覆這則留言。") + '</p>' +
    '<div class="merr" role="status"></div><div class="acts"><button type="button" class="btn mcancel">取消</button><button type="button" class="btn solid msend">送出</button></div></div>';
  d.classList.add("show");
  const q = s => d.querySelector(s);
  q(".mbody").oninput = () => { q(".mcnt").textContent = `${q(".mbody").value.length} / 500`; };
  q(".mcancel").onclick = () => d.classList.remove("show");
  q(".msend").onclick = async () => {
    const err = q(".merr"), btn = q(".msend");
    const body = q(".mbody").value.trim();
    if (!body) { err.textContent = "請先寫留言內容。"; return; }
    const o = { action: "sendmsg", name: q(".mname").value.trim(), body, hp: q(".mweb").value };
    if (asT) Object.assign(o, { acct: TD.me.acct, auth: TD.me.auth });
    else { o.email = q(".mmail").value.trim(); if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(o.email)) { err.textContent = "請填寫正確的電子信箱。"; return; } }
    if (!msgReady()) { err.textContent = "網站還沒有設定後端，暫時無法留言。"; return; }
    btn.disabled = true; err.textContent = "送出中……";
    try {
      const j = await apiCall(o);
      if (!j.ok) { err.textContent = msgErr(j); btn.disabled = false; return; }
      q(".bx").innerHTML = '<h3>✉️ 已送出</h3><p class="mh">謝謝你的留言！' + (asT ? "管理者回覆後，會出現在教師管理的「站內信」。" : "管理者回覆後，會寄到你留下的信箱。") + '</p><div class="acts"><button type="button" class="btn solid mok">好</button></div>';
      q(".mok").onclick = () => { d.classList.remove("show"); if (asT && page() === "teacher" && TD.tab === "msg") renderTeacher(); };
    } catch (e) { err.textContent = apiErr(e); btn.disabled = false; }
  };
  setTimeout(() => q(".mbody").focus(), 50);
}
document.addEventListener("click", e => { if (e.target.closest(".openmsg")) { e.preventDefault(); e.stopPropagation(); openMsgDlg(); } }, true);

function msgItem(m, owner, after) {
  const box = el("div", { class: "mitem" + (m.status === "未讀" ? " unread" : "") });
  const who = owner ? (m.kind === "老師" ? `老師：${esc(m.acct)}${m.name ? `（${esc(m.name)}）` : ""}` : `訪客：${esc(m.name || "（未填稱呼）")}〈${esc(m.email)}〉`) : "我的留言";
  box.append(el("div", { class: "mhead" }, `<span class="mtime">${fmtTime(m.time)}</span><b>${who}</b><span class="mst ${m.status === "未讀" ? "u" : m.status === "已回覆" ? "r" : ""}">${esc(m.status)}</span>`));
  box.append(el("div", { class: "mtext" }, esc(m.body)));
  if (m.reply) box.append(el("div", { class: "mreply" }, `<span class="mrl">${owner ? "我的回覆" : "管理者回覆"}${m.rtime ? "（" + fmtTime(m.rtime) + "）" : ""}</span>${esc(m.reply)}`));
  if (owner) {
    const msg = el("p", { class: "hint", role: "status" });
    const bar = el("div", { class: "tools" });
    if (m.status === "未讀") {
      const rd = el("button", { type: "button", class: "btn" }, "標為已讀");
      rd.onclick = async () => { rd.disabled = true; try { const j = await apiCall({ action: "msgread", ...cred(), id: m.id }); if (!j.ok) { msg.textContent = msgErr(j); rd.disabled = false; return; } if (TD.me.info) TD.me.info.unread = Math.max(0, (TD.me.info.unread || 1) - 1); after(); } catch (e) { msg.textContent = apiErr(e); rd.disabled = false; } };
      bar.append(rd);
    }
    const rp = el("button", { type: "button", class: "btn" }, m.reply ? "再回覆一次" : "回覆");
    rp.onclick = () => {
      if (box.querySelector(".mrbox")) return;
      const rb = el("div", { class: "mrbox" });
      rb.append(el("p", { class: "hint" }, m.kind === "老師" ? "回覆會出現在這位老師的教師管理後台。" : "回覆會以不接受回信（noreply）的地址寄到對方信箱，不會顯示你的信箱。"));
      const ta = el("textarea", { rows: "4", maxlength: "1000" }); const go = el("button", { type: "button", class: "btn solid" }, "送出回覆");
      go.onclick = async () => {
        if (!ta.value.trim()) { msg.textContent = "請先寫回覆內容。"; return; }
        go.disabled = true; msg.textContent = "送出中……";
        try { const j = await apiCall({ action: "msgreply", ...cred(), id: m.id, text: ta.value.trim() }); if (!j.ok) { msg.textContent = msgErr(j); go.disabled = false; return; } if (m.status === "未讀" && TD.me.info) TD.me.info.unread = Math.max(0, (TD.me.info.unread || 1) - 1); after(); }
        catch (e) { msg.textContent = apiErr(e); go.disabled = false; }
      };
      rb.append(ta, tools(go)); box.insertBefore(rb, msg); ta.focus();
    };
    const del = el("button", { type: "button", class: "btn" }, "刪除"); let armed = false;
    del.onclick = async () => {
      if (!armed) { armed = true; del.textContent = "確定刪除？再按一次"; setTimeout(() => { armed = false; del.textContent = "刪除"; }, 4000); return; }
      del.disabled = true;
      try { const j = await apiCall({ action: "msgdel", ...cred(), id: m.id }); if (!j.ok) { msg.textContent = msgErr(j); del.disabled = false; return; } if (m.status === "未讀" && TD.me.info) TD.me.info.unread = Math.max(0, (TD.me.info.unread || 1) - 1); after(); }
      catch (e) { msg.textContent = apiErr(e); del.disabled = false; }
    };
    bar.append(rp, del); box.append(bar, msg);
  }
  return box;
}
async function tabMsg(body) {
  const owner = TD.me.owner;
  const c = card("站內信", "", owner ? "老師和訪客留給網站管理者的訊息，只有管理者看得到。未讀的留言以橘色標示。" : "你留給網站管理者的訊息，以及管理者的回覆。");
  if (!owner) { const nb = el("button", { type: "button", class: "btn solid openmsg" }, "✉️ 寫新留言"); c.append(tools(nb)); }
  const list = el("div", { class: "mlist" }, '<p class="hint">讀取中……</p>'); c.append(list); body.append(c);
  try {
    const j = await apiCall({ action: owner ? "msglist" : "mymsgs", ...cred() });
    if (!j.ok) { list.innerHTML = ""; list.append(el("p", { class: "hint" }, msgErr(j))); return; }
    list.innerHTML = "";
    if (!j.msgs.length) { list.append(el("p", { class: "hint" }, "目前沒有站內信。")); return; }
    j.msgs.forEach(m => list.append(msgItem(m, owner, () => renderTeacher())));
  } catch (e) { list.innerHTML = ""; list.append(el("p", { class: "hint" }, apiErr(e))); }
}
