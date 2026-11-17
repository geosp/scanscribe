#!/usr/bin/env bash
# Usage: ctrlc.sh <extra> <input folder> <work dir>
# Interrupts a run during page 2 like a terminal Ctrl-C: SIGINT to the run's whole process group.
set -um
extra=$1 in=$2 w=$3
cd "$(git -C "$(dirname "$0")" rev-parse --show-toplevel)"
uv sync --locked --extra "$extra" -q
for how in uv-run direct; do
  out=$w/ctrlc-$extra-$how.txt err=$w/ctrlc-$extra-$how.err
  printf 'existing output from an earlier run\n' > "$out"
  before=$(sha256sum < "$out")
  if [ "$how" = uv-run ]; then cmd=(uv run scanscribe); else cmd=(.venv/bin/scanscribe); fi
  "${cmd[@]}" "$in" -o "$out" > "$w/ctrlc-$extra-$how.stdout" 2> "$err" &
  pid=$!
  until grep -q "Processing page 2" "$err" 2>/dev/null; do sleep 0.2; done
  start=$(date +%s.%N)
  kill -INT -- "-$pid"
  wait "$pid"; rc=$?
  secs=$(echo "$(date +%s.%N) - $start" | bc)
  after=$(sha256sum < "$out")
  temps=$(find "$w" -maxdepth 1 -name ".ctrlc-$extra-$how.txt.*.tmp" | wc -l)
  printf '%s %s: exit=%s stopped-after=%.1fs output-unchanged=%s temp-files-left=%s stdout-bytes=%s last-stderr-line="%s" tracebacks=%s\n' \
    "$extra" "$how" "$rc" "$secs" "$([ "$before" = "$after" ] && echo yes || echo NO)" "$temps" \
    "$(wc -c < "$w/ctrlc-$extra-$how.stdout")" "$(tail -1 "$err")" "$(grep -c Traceback "$err")"
done
