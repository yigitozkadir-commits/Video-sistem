#!/bin/bash
set -e
cd "$(dirname "$0")/../../remotion_ninniler_atlasi"
OUT="../projects/PRJ-ninniler-atlasi/render"
mkdir -p "$OUT"

for id in ninni-altay ninni-saha ninni-karacay-malkar ninni-anadolu ninni-hakas \
          ninni-baskurt ninni-nogay ninni-gagauz ninni-kerkuk ninni-sor ninni-uygur ninni-ahiska; do
  if [ -f "$OUT/$id.mp4" ]; then
    echo "skip (exists): $id"
    continue
  fi
  echo "rendering $id ..."
  npx remotion render src/index.ts "$id" "$OUT/$id.mp4" --concurrency=4
done
echo "done."
