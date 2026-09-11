#!/usr/bin/env bash
# run-dirplayer.sh — play the ORIGINAL mizube (RE227368) in the browser
# via dirplayer-rs (Kartatz fork with the mizube fixes).
#
# Prereqs (one-time):
#   - Rust (rustup) + wasm32-unknown-unknown target
#   - wasm-pack 0.13.x  (https://rustwasm.github.io/wasm-pack/installer.html)
#   - Node.js 18+ and a Chromium/Chrome browser
#
# Usage:
#   ./tools/run-dirplayer.sh <path-to-RE227368-dir> [work-dir]
#
# What it does:
#   1. clones Kartatz/dirplayer-rs (if absent) and builds the WASM VM
#   2. extracts the embedded movie from mizube.exe -> movie.dcr
#   3. lays out the cast files (symlinks; system.cxt/cgoto.cxt as .cct)
#   4. serves the game dir on :8000 (CORS) and the app on :3000
#   5. prints the URL to load in the browser
set -euo pipefail

GAME_DIR="${1:?usage: run-dirplayer.sh <RE227368 dir> [work-dir]}"
WORK="${2:-$PWD/.dirplayer}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"

mkdir -p "$WORK"
[ -d "$GAME_DIR/mizube.exe" ] || [ -f "$GAME_DIR/mizube.exe" ] || {
    echo "!! $GAME_DIR/mizube.exe not found" >&2; exit 1; }

# 1. dirplayer-rs (fork with the fixes)
DPR="$WORK/dirplayer-rs"
if [ ! -d "$DPR" ]; then
    echo '>> cloning Kartatz/dirplayer-rs (fork of igorlira/dirplayer-rs + mizube fixes)'
    git clone https://github.com/Kartatz/dirplayer-rs "$DPR"
fi
if [ ! -f "$DPR/vm-rust/pkg/vm_rust_bg.wasm" ]; then
    echo '>> building the WASM VM (first build: ~3-5 min)'
    (cd "$DPR" && npm install --no-audit --no-fund && npm run build-vm)
fi

# 2. extract the embedded movie (Director score) from the projector exe
echo '>> extracting the embedded movie from mizube.exe'
GAMEDATA="$WORK/game"
mkdir -p "$GAMEDATA"
python3 "$REPO_ROOT/tools/extract_movie.py" "$GAME_DIR/mizube.exe" "$GAMEDATA/movie.dcr" >/dev/null

# 3. cast libraries next to the movie (names normalized to .cct)
for f in "$GAME_DIR"/*.cct; do ln -sf "$(cd "$(dirname "$f")" && pwd)/$(basename "$f")" "$GAMEDATA/"; done
ln -sf "$(cd "$(dirname "$GAME_DIR/system.cxt")" && pwd)/system.cxt" "$GAMEDATA/system.cct"
ln -sf "$(cd "$(dirname "$GAME_DIR/cgoto.cxt")" && pwd)/cgoto.cxt" "$GAMEDATA/cgoto.cct"
ls "$GAMEDATA"

# 4. serve the game with CORS + start the app
echo '>> serving game data on http://127.0.0.1:8000 (CORS)'
cat > "$GAMEDATA/cors_server.py" <<'EOF'
import http.server, socketserver, os
class CORS(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Cross-Origin-Resource-Policy', 'cross-origin')
        super().end_headers()
os.chdir(os.path.dirname(os.path.abspath(__file__)))
socketserver.TCPServer.allow_reuse_address = True
with socketserver.ThreadingTCPServer(('127.0.0.1', 8000), CORS) as httpd:
    httpd.serve_forever()
EOF
( setsid python3 "$GAMEDATA/cors_server.py" </dev/null >"$WORK/game-server.log" 2>&1 & )

echo '>> starting the dirplayer app on http://localhost:3000'
( cd "$DPR" && setsid env BROWSER=none PORT=3000 npm start </dev/null >"$WORK/app.log" 2>&1 & )

sleep 5
until curl -sI http://localhost:3000 2>/dev/null | head -1 | grep -q 200; do sleep 2; done

cat <<EOF

=======================================================================
 READY.

 1. Open  http://localhost:3000
 2. In "MOVIE URL" enter:  http://127.0.0.1:8000/movie.dcr
 3. CHECK THE "Auto-play" BOX (bottom left)  <-- the movie will not
    start otherwise (dirplayer's default; see docs/dirplayer-exploration.md)
 4. Click "Load Movie".  First load takes ~20s (11 castLibs,
    ~450MB on disk). Watch the console for "[heap] ... 1159 MB".
 5. The game boots to the original title cards; the menu appears
    after ~60s. Click the menu to play.

 Heads-up (known gaps, see docs/dirplayer-exploration.md):
   - 17 audio Xtras are not implemented yet (game may be silent)
   - stop/restart the servers with:  pkill -f cors_server; pkill -f react-scripts
=======================================================================
EOF
