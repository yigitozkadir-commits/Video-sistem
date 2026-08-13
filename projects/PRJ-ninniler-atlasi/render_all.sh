#!/bin/bash
# One-off batch render for PRJ-ninniler-atlasi's 10 placeholder-timed silent
# videos (no music yet - see src/lullabies.ts header in remotion_ninniler_atlasi).
set -e
cd "$(dirname "$0")/../../remotion_ninniler_atlasi"
OUT="../projects/PRJ-ninniler-atlasi/render"
mkdir -p "$OUT"

for id in ninni-kazak ninni-kirgiz ninni-turkmen ninni-azerbaycan ninni-tuva \
          ninni-tatar ninni-cuvas ninni-ozbek ninni-karakalpak ninni-kirim-tatari; do
  if [ -f "$OUT/$id.mp4" ]; then
    echo "skip (exists): $id"
    continue
  fi
  echo "rendering $id ..."
  npx remotion render src/index.ts "$id" "$OUT/$id.mp4" --concurrency=4
done
echo "done."
