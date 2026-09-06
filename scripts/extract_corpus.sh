#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
mkdir -p "$ROOT/corpus/standards" "$ROOT/corpus/reports"

pdftotext -layout "$ROOT/assets/raw/规范指南/食源性疾病判定及处置技术指南(试行)-终版.pdf" "$ROOT/corpus/standards/判定及处置技术指南.txt"
pdftotext -layout "$ROOT/assets/raw/规范指南/食源性疾病监测报告工作规范（试行）.pdf" "$ROOT/corpus/standards/监测报告工作规范.txt"
pdftotext -layout "$ROOT/assets/raw/规范指南/2026年食源性疾病监测工作手册-20260109.pdf" "$ROOT/corpus/standards/2026监测工作手册附录.txt"
textutil -convert txt -output "$ROOT/corpus/standards/2012技术指南.txt" "$ROOT/assets/raw/规范指南/6.食品安全事故流行病学调查技术指南(2012年版).doc"

for f in "$ROOT"/assets/raw/结案报告/*; do
  [ -f "$f" ] || continue
  base="$(basename "$f")"; name="${base%.*}"
  case "${base##*.}" in
    pdf) pdftotext -layout "$f" "$ROOT/corpus/reports/${name}.txt" ;;
    doc|docx) textutil -convert txt -output "$ROOT/corpus/reports/${name}.txt" "$f" ;;
  esac
done
echo "done: standards=$(ls "$ROOT/corpus/standards" | wc -l | tr -d ' ') reports=$(ls "$ROOT/corpus/reports" | wc -l | tr -d ' ')"
