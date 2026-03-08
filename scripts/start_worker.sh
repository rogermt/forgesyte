#!/usr/bin/env bash

set -euo pipefail

TAILSCALE_KEY="${TAILSCALE_KEY:?Set TAILSCALE_KEY}"
LAPTOP_IP="${LAPTOP_IP:?Set LAPTOP_IP to your laptop Tailscale IP}"

STATE_DIR="${STATE_DIR:-/teamspace/studios/this_studio/tailscale-data}"
TAILSCALE_HOSTNAME="${TAILSCALE_HOSTNAME:-forgesyte-lightning}"
TS_CONTAINER_NAME="${TS_CONTAINER_NAME:-tailscaled}"
RAY_PORT="${RAY_PORT:-6379}"

need_cmd() {
  command -v "$1" >/dev/null 2>&1 || {
    echo "❌ Missing command: $1"
    exit 1
  }
}

wait_for_tailscale() {
  local tries="${1:-30}"
  for i in $(seq 1 "$tries"); do
    if ip link show tailscale0 >/dev/null 2>&1; then
      return 0
    fi
    echo "   waiting for tailscale0... (${i}/${tries})"
    sleep 2
  done
  return 1
}

wait_for_tcp() {
  local host="$1"
  local port="$2"
  local tries="${3:-20}"

  for i in $(seq 1 "$tries"); do
    if timeout 3 bash -c "cat < /dev/null > /dev/tcp/${host}/${port}" 2>/dev/null; then
      return 0
    fi
    echo "   waiting for ${host}:${port}... (${i}/${tries})"
    sleep 2
  done
  return 1
}

need_cmd docker
need_cmd ray
need_cmd ip
need_cmd awk
need_cmd cut
need_cmd timeout

echo "🚀 Booting Lightning GPU worker..."
mkdir -p "$STATE_DIR"

echo "🧹 Cleaning up old Tailscale container..."
docker rm -f "$TS_CONTAINER_NAME" >/dev/null 2>&1 || true

echo "🦎 Starting Tailscale via Docker..."
docker run -d \
  --name "$TS_CONTAINER_NAME" \
  --network=host \
  --restart=unless-stopped \
  --cap-add=NET_ADMIN \
  --cap-add=SYS_MODULE \
  --device=/dev/net/tun \
  -v "$STATE_DIR:/var/lib/tailscale" \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -e TS_AUTHKEY="${TAILSCALE_KEY}" \
  -e TS_HOSTNAME="${TAILSCALE_HOSTNAME}" \
  -e TS_STATE_DIR=/var/lib/tailscale \
  -e TS_EXTRA_ARGS=--ssh \
  -e TS_USERSPACE=false \
  tailscale/tailscale >/dev/null

echo "⏳ Waiting for Tailscale network..."
wait_for_tailscale 30 || {
  echo "❌ tailscale0 did not appear"
  docker logs --tail=200 "$TS_CONTAINER_NAME" || true
  exit 1
}

# --- FIX: safe getter + safe assignment under set -u ---
get_tailscale_ip() {
  ip -4 -o addr show dev tailscale0 \
    | awk '{print $4}' \
    | cut -d/ -f1 \
    | head -n1
}

LIGHTNING_IP=""
tmp_ip="$(get_tailscale_ip || true)"
LIGHTNING_IP="${tmp_ip:-}"

if [[ -z "$LIGHTNING_IP" ]]; then
  echo "❌ Could not get Lightning Tailscale IP from tailscale0"
  docker logs --tail=200 "$TS_CONTAINER_NAME" || true
  exit 1
fi

echo "✅ Tailscale connected"
echo "   Lightning IP: ${LIGHTNING_IP}"
docker exec "$TS_CONTAINER_NAME" tailscale status

echo "🔌 Checking Ray head on ${LAPTOP_IP}:${RAY_PORT}..."
wait_for_tcp "$LAPTOP_IP" "$RAY_PORT" 20 || {
  echo "❌ Cannot reach Ray head at ${LAPTOP_IP}:${RAY_PORT}"
  echo "   Tailscale ping:"
  docker exec "$TS_CONTAINER_NAME" tailscale ping -c 3 "$LAPTOP_IP" || true
  exit 1
}

echo "🧠 Joining Ray cluster..."
ray stop -f || true
ray start \
  --address="${LAPTOP_IP}:${RAY_PORT}" \
  --node-ip-address="${LIGHTNING_IP}"

echo "✅ Success"
echo "   Worker IP: ${LIGHTNING_IP}"
echo "   Head IP:   ${LAPTOP_IP}"

