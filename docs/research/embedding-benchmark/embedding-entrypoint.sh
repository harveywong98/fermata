#!/bin/sh
set -eu
exec /app/llama-server -m "/models/${MODEL_FILE:?}" \
  --embedding --pooling "${POOLING:?}" --no-mmap \
  --host 0.0.0.0 --port 8080 \
  -c "${CONTEXT:-512}" -b 2048 -ub 2048 \
  -t 4 -tb 4 -ngl 0 -np 1
