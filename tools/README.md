# 課文加密後處理

正式 index.html 由原始檔組合後，再用這裡的程式加工：
- 課文全文與彩色生字圖用老師密碼加密（密碼不寫在任何檔案裡）
- 著作權說明、站內信、課文解鎖畫面

用法（未加密的 index 不可提交到本儲存庫）：

    python3 build_lock.py 未加密的index.html 芫荽體.ttf index.html 老師密碼 prod

msg_inject.js 必須和 build_lock.py 放在同一個資料夾。
