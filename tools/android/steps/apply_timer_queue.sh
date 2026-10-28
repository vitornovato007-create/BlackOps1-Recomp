#!/usr/bin/env bash
set -euo pipefail

SOURCE="patches/android/timer_queue.cpp"
TARGET="rexglue-sdk/src/core/timer_queue.cpp"

if [ ! -f "$SOURCE" ]; then
  echo "::error file=$SOURCE::Patch persistente do TimerQueue nao encontrado."
  exit 1
fi
if [ ! -f "$TARGET" ]; then
  echo "::error file=$TARGET::TimerQueue do checkout ReXGlue nao encontrado."
  exit 1
fi

cp "$SOURCE" "$TARGET"

if grep -n -E 'std::jthread|std::stop_token|request_stop\(' "$TARGET"; then
  echo "::error file=$TARGET::O TimerQueue ainda contem APIs jthread/stop_token incompatíveis com o compilador Android usado."
  exit 1
fi

grep -q 'std::thread dispatch_thread_' "$TARGET"
grep -q 'std::atomic<bool> stop_requested_' "$TARGET"
grep -q 'dispatch_thread_.join()' "$TARGET"

echo "Patch TimerQueue aplicado e verificado:"
grep -n -E 'std::thread dispatch_thread_|std::atomic<bool> stop_requested_|dispatch_thread_.join' "$TARGET"
