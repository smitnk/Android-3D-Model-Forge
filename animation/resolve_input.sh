#!/usr/bin/env bash
# Validates workflow inputs and fetches the model. Reads MODEL MODEL_PATH MODEL_URL DURATION FPS RES SAMPLES MSG REPO;
# appends src/duration/fps/w/h/samples to $GITHUB_OUTPUT.
set -euo pipefail
# a push whose message contains [quick] renders a short low-res test
if [[ "${MSG:-}" == *"[quick]"* ]]; then DURATION=2; RES=360x640; SAMPLES=8; fi
[[ "$DURATION" =~ ^[0-9]+(\.[0-9]+)?$ ]] || { echo "::error::bad duration"; exit 1; }
[[ "$FPS" =~ ^[0-9]+$ && "$FPS" -ge 1 && "$FPS" -le 60 ]] || { echo "::error::bad fps"; exit 1; }
[[ "$RES" =~ ^([0-9]+)x([0-9]+)$ ]] || { echo "::error::resolution must be WIDTHxHEIGHT"; exit 1; }
W=${BASH_REMATCH[1]}; H=${BASH_REMATCH[2]}
(( W % 2 == 0 && H % 2 == 0 && W <= 2160 && H <= 3840 )) || { echo "::error::resolution must be even and <= 2160x3840"; exit 1; }
[[ "$SAMPLES" =~ ^[0-9]+$ && "$SAMPLES" -ge 1 && "$SAMPLES" -le 512 ]] || { echo "::error::bad samples"; exit 1; }
mkdir -p in
if [ -n "$MODEL_PATH" ]; then
  [[ "$MODEL_PATH" != *..* && -f "$MODEL_PATH" ]] || { echo "::error::model_path not found: $MODEL_PATH"; exit 1; }
  src="$MODEL_PATH"
else
  url="${MODEL_URL:-https://github.com/$REPO/releases/download/model-latest/${MODEL}.glb}"
  [[ "$url" == https://* && "$url" == *.glb* ]] || { echo "::error::model_url must be an https .glb URL"; exit 1; }
  curl -fsSL --retry 3 --max-filesize 200000000 -o in/model.glb "$url"
  src=in/model.glb
fi
head -c 4 "$src" | grep -q glTF || [[ "$src" == *.blend ]] || { echo "::error::input is not a GLB"; exit 1; }
echo "Model: $src  ${DURATION}s ${FPS}fps ${W}x${H} samples=$SAMPLES"
{ echo "src=$src"; echo "duration=$DURATION"; echo "fps=$FPS"; echo "w=$W"; echo "h=$H"; echo "samples=$SAMPLES"; } >> "$GITHUB_OUTPUT"
