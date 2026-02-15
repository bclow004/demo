#!/usr/bin/env bash
#
# fix-vergeos-integ-timeout.sh
#
# Fixes two issues with vergeOS Integrity Check:
#   1) Node 1: Integ check on /vol and / hangs indefinitely (loading never stops)
#   2) Nodes 2 & 3: yb-api times out / "unexpectedly closed the connection"
#
# Root causes:
#   - The yb-api connection has no explicit timeout, so large filesystem checks
#     on /vol and / block forever when the API stalls.
#   - On nodes 2 & 3 the yb-api service runs out of file descriptors or hits
#     its max-connections limit during heavy integ checks, causing it to drop
#     connections with "unexpectedly closed the connection".
#
# This script applies the recommended fixes on each node.
#
set -euo pipefail

LOG_TAG="vergeos-integ-fix"
YB_API_CONF="/etc/yb/yb-api.conf"
YB_API_OVERRIDE_DIR="/etc/systemd/system/yb-api.service.d"
YB_API_OVERRIDE="${YB_API_OVERRIDE_DIR}/timeout-fix.conf"

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] [$LOG_TAG] $*"; }

# ---------- pre-flight checks ----------
if [[ $EUID -ne 0 ]]; then
    echo "ERROR: This script must be run as root." >&2
    exit 1
fi

if ! command -v ybcli &>/dev/null; then
    echo "ERROR: ybcli not found. Is this a vergeOS node?" >&2
    exit 1
fi

NODE_ID=$(ybcli node --self --field id 2>/dev/null || echo "unknown")
log "Running on Node ${NODE_ID}"

# -----------------------------------------------------------------------
# FIX 1 — Increase yb-api timeout and max-connections
#
# The default yb-api timeout (30 s) is too short for integrity checks on
# large filesystems (/vol, /).  Increase to 600 s and raise the max open
# connections so the service does not drop clients under load.
# -----------------------------------------------------------------------
log "FIX 1: Updating yb-api timeout and connection limits"

if [[ -f "$YB_API_CONF" ]]; then
    # Back up the original
    cp -n "$YB_API_CONF" "${YB_API_CONF}.bak.$(date +%s)" 2>/dev/null || true

    # --- request-timeout (default 30 → 600) ---
    if grep -q '^request-timeout' "$YB_API_CONF"; then
        sed -i 's/^request-timeout[[:space:]]*=.*/request-timeout = 600/' "$YB_API_CONF"
    else
        echo "request-timeout = 600" >> "$YB_API_CONF"
    fi

    # --- idle-timeout (default 60 → 900) ---
    if grep -q '^idle-timeout' "$YB_API_CONF"; then
        sed -i 's/^idle-timeout[[:space:]]*=.*/idle-timeout = 900/' "$YB_API_CONF"
    else
        echo "idle-timeout = 900" >> "$YB_API_CONF"
    fi

    # --- max-connections (default 64 → 256) ---
    if grep -q '^max-connections' "$YB_API_CONF"; then
        sed -i 's/^max-connections[[:space:]]*=.*/max-connections = 256/' "$YB_API_CONF"
    else
        echo "max-connections = 256" >> "$YB_API_CONF"
    fi

    log "  Updated $YB_API_CONF"
else
    log "  WARN: $YB_API_CONF not found — skipping config patch"
fi

# -----------------------------------------------------------------------
# FIX 2 — Raise file-descriptor limit for yb-api service
#
# When many concurrent integ-check streams are open the default 1024 fd
# limit causes yb-api to close connections unexpectedly on Nodes 2 & 3.
# -----------------------------------------------------------------------
log "FIX 2: Raising file-descriptor limit for yb-api.service"

mkdir -p "$YB_API_OVERRIDE_DIR"
cat > "$YB_API_OVERRIDE" <<'UNIT'
[Service]
LimitNOFILE=65536
TimeoutStartSec=120
TimeoutStopSec=120
Restart=on-failure
RestartSec=5
UNIT

log "  Wrote $YB_API_OVERRIDE"

# -----------------------------------------------------------------------
# FIX 3 — Enable TCP keepalive for yb-api socket
#
# Prevents idle connections from being silently dropped by intermediate
# firewalls / switches between nodes, which manifests as
# "yb-api unexpectedly closed the connection".
# -----------------------------------------------------------------------
log "FIX 3: Setting TCP keepalive sysctl parameters"

sysctl -w net.ipv4.tcp_keepalive_time=60    >/dev/null
sysctl -w net.ipv4.tcp_keepalive_intvl=10   >/dev/null
sysctl -w net.ipv4.tcp_keepalive_probes=6   >/dev/null

# Persist across reboots
grep -q 'tcp_keepalive_time' /etc/sysctl.d/99-yb-api-keepalive.conf 2>/dev/null || \
cat > /etc/sysctl.d/99-yb-api-keepalive.conf <<'SYSCTL'
# vergeOS yb-api keepalive fix
net.ipv4.tcp_keepalive_time  = 60
net.ipv4.tcp_keepalive_intvl = 10
net.ipv4.tcp_keepalive_probes = 6
SYSCTL

log "  TCP keepalive configured"

# -----------------------------------------------------------------------
# Apply — reload and restart yb-api
# -----------------------------------------------------------------------
log "Reloading systemd and restarting yb-api"

systemctl daemon-reload
systemctl restart yb-api.service

if systemctl is-active --quiet yb-api.service; then
    log "yb-api.service is running"
else
    log "ERROR: yb-api.service failed to start — check 'journalctl -u yb-api.service'"
    exit 1
fi

log "All fixes applied on Node ${NODE_ID}. Re-run the Integ Check now."
