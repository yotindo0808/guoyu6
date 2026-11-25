# 課文加密後處理

正式 index.html 由原始檔組合後，再用這裡的程式加工：
- 課文全文與彩色生字圖用老師密碼加密（密碼不寫在任何檔案裡）
- 著作權說明、站內信、課文解鎖畫面

用法（未加密的 index 不可提交到本儲存庫）：

    python3 build_lock.py 未加密的index.html 芫荽體.ttf index.html 老師密碼 prod

msg_inject.js、tts_inject.js 必須和 build_lock.py 放在同一個資料夾。

tts_inject.js：語音報讀改用 Google 雲端國語語音（預設 1.4 倍速，改 RATE 即可），連不上時退回平板內建語音；網址加 ?tts=local 強制用平板語音。build_lock.py 會自動加進去，並加上 no-referrer。

stu_chars_patch.py：學生練習「生字練習」分步驟（① 國字＋注音／② 部首，畫面太矮或直式時改成三步），寫字格與注音鍵依可用高度計算。build_lock.py 會自動套用；原始檔若已改寫成同樣做法，找不到舊程式時只會提醒、不會中斷。
