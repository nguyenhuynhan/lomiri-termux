#!/usr/bin/env bash
source "$(dirname -- "$0")/common.sh"
bash "$PROJECT_ROOT/scripts/stop.sh"
guest /bin/bash -lc 'gcc -Wall -Wextra -shared -fPIC -g -o runtime/libcrash-trace.so src/crash-trace.c -ldl'
export LOMIRI_TRACE=1
bash "$PROJECT_ROOT/scripts/start.sh"
echo 'Diagnostic mode: crash handler exits Lomiri after printing its stack to runtime/session.log.'
