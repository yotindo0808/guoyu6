#!/usr/bin/env bash
# 用法：bash run.sh <課次資料.json> [輸出資料夾]
# 字型：芫荽（Iansui-Regular.ttf）與ㄅ注音芫荽（BpmfIansui-Regular.ttf）放在 fonts/ 或已安裝於系統即可。
set -e
HERE="$(cd "$(dirname "$0")" && pwd)"
DATA="$(cd "$(dirname "$1")" && pwd)/$(basename "$1")"
OUT="${2:-$HERE/output}"
mkdir -p "$OUT" ~/.fonts
[ -d "$HERE/fonts" ] && cp "$HERE"/fonts/*.tt[fc] ~/.fonts/ 2>/dev/null && fc-cache -f >/dev/null 2>&1 || true
python3 "$HERE/make_comp.py" "$DATA"
python3 "$HERE/make_zy.py" "$DATA"
NODE_PATH="$(npm root -g):$HERE/node_modules" node "$HERE/build_worksheet.js" "$DATA" "$OUT"
python3 "$HERE/build_practice.py" "$DATA" "$OUT"
cd "$OUT"
for f in *.docx; do zip -d "$f" '*/' >/dev/null 2>&1 || true; done
command -v soffice >/dev/null && soffice --headless --convert-to pdf *.docx >/dev/null 2>&1 || true
ls -1 "$OUT"
