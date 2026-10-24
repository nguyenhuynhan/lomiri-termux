#!/usr/bin/env bash
source "$(dirname -- "$0")/common.sh"
python "$PROJECT_ROOT/scripts/session-state.py" status >/dev/null || { echo 'Start Lomiri first.' >&2; exit 2; }
python - "$PROJECT_ROOT/runtime/work-apps.sock" "$@" <<'PY'
import json, socket, sys
if len(sys.argv) < 3 or sys.argv[2] not in ('code', 'chatgpt'):
    sys.exit('Usage: bash scripts/work-app.sh code [--no-sandbox] | chatgpt')
options = sys.argv[3:]
if options not in ([], ['--no-sandbox']) or (options and sys.argv[2] != 'code'):
    sys.exit('Unsupported application option.')
request = {'app': sys.argv[2], 'no_sandbox': bool(options)}
try:
    with socket.socket(socket.AF_UNIX) as client:
        client.settimeout(10)
        client.connect(sys.argv[1])
        client.sendall(json.dumps(request).encode() + b'\n')
        result = json.loads(client.recv(4096))
    print(result['message'])
    if not result['ok']: sys.exit(2)
except OSError as error:
    sys.exit(f'Application launcher unavailable ({error}). Restart Lomiri after updating the project.')
PY
