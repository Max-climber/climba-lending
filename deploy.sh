#!/usr/bin/env bash
# Быстрый деплой climba.ru
#   ./deploy.sh           — build + JS/CSS/HTML/favicon (без тяжёлого media)
#   ./deploy.sh --media   — то же + картинки/видео в /media/
#   ./deploy.sh --install — ещё и npm install
#   ./deploy.sh --skip-build — только заливка уже собранного dist/
set -euo pipefail

HOST="193.109.78.205"
PORT="2244"
USER="maksim"
KEY="${HOME}/.ssh/id_france"
REMOTE="/home/maksim/climba/climba-lending"
# Unix socket path ≤104 байт на macOS — короткий путь в /tmp
CONTROL="/tmp/cd-%C"

DO_BUILD=1
DO_INSTALL=0
DO_MEDIA=0

for arg in "$@"; do
  case "$arg" in
    --media|--all) DO_MEDIA=1 ;;
    --install) DO_INSTALL=1 ;;
    --skip-build) DO_BUILD=0 ;;
    -h|--help)
      sed -n '2,7p' "$0"
      exit 0
      ;;
    *)
      echo "Unknown flag: $arg (see --help)" >&2
      exit 1
      ;;
  esac
done

# Одно multiplex-соединение на весь деплой (rsync/ssh переиспользуют его)
SSH_OPTS="-p ${PORT} -i ${KEY} \
  -o ControlMaster=auto \
  -o ControlPath=${CONTROL} \
  -o ControlPersist=60 \
  -o ConnectTimeout=12 \
  -o ServerAliveInterval=5 \
  -o ServerAliveCountMax=3"

ssh_cmd() {
  # shellcheck disable=SC2086
  ssh ${SSH_OPTS} "${USER}@${HOST}" "$@"
}

ssh_retry() {
  local attempt=1 max=6
  while true; do
    if ssh_cmd "$@"; then
      return 0
    fi
    if (( attempt >= max )); then
      echo "SSH failed after ${max} attempts" >&2
      return 1
    fi
    echo "SSH retry ${attempt}/${max}..."
    sleep $(( attempt * 2 ))
    attempt=$(( attempt + 1 ))
  done
}

open_mux() {
  local attempt=1 max=6
  while true; do
    # -fN: master в фоне; дальше все клиенты цепляются к сокету
    # shellcheck disable=SC2086
    if ssh ${SSH_OPTS} -o ControlMaster=yes -fN "${USER}@${HOST}"; then
      return 0
    fi
    if (( attempt >= max )); then
      echo "Cannot open SSH ControlMaster" >&2
      return 1
    fi
    echo "SSH connect retry ${attempt}/${max}..."
    sleep $(( attempt * 2 ))
    attempt=$(( attempt + 1 ))
  done
}

close_mux() {
  # shellcheck disable=SC2086
  ssh ${SSH_OPTS} -O exit "${USER}@${HOST}" 2>/dev/null || true
}

rsync_code() {
  # shellcheck disable=SC2086
  rsync -avz --timeout=30 -e "ssh ${SSH_OPTS}" "$@"
}

rsync_media() {
  # mp4 уже сжато — без -z меньше CPU на тухлом канале
  # shellcheck disable=SC2086
  rsync -av --timeout=90 -e "ssh ${SSH_OPTS}" "$@"
}

cleanup() { close_mux; }
trap cleanup EXIT

if (( DO_BUILD )); then
  git pull || true
  if (( DO_INSTALL )) || [[ ! -d node_modules ]]; then
    CI=true npm install
  fi
  CI=true npm run build
fi

echo "Opening SSH (one connection)..."
open_mux

rsync_code dist/bundled/ "${USER}@${HOST}:${REMOTE}/dist/bundled/"
rsync_code dist/qr/ "${USER}@${HOST}:${REMOTE}/dist/qr/"
rsync_code dist/index.html "${USER}@${HOST}:${REMOTE}/dist/index.html"

rsync_code \
  dist/favicon.ico \
  dist/favicon-16x16.png \
  dist/favicon-32x32.png \
  dist/apple-touch-icon.png \
  dist/android-chrome-192x192.png \
  dist/android-chrome-512x512.png \
  dist/site.webmanifest \
  "${USER}@${HOST}:${REMOTE}/dist/"

ssh_retry "chmod 644 ${REMOTE}/dist/favicon.ico ${REMOTE}/dist/favicon-*.png ${REMOTE}/dist/apple-touch-icon.png ${REMOTE}/dist/android-chrome-*.png ${REMOTE}/dist/site.webmanifest"

if (( DO_MEDIA )); then
  ssh_retry "mkdir -p ${REMOTE}/dist/media"
  rsync_media \
    assets/main-video-background.mp4 \
    assets/hero-poster.jpg \
    assets/hero-poster.webp \
    assets/climba-logo.webp \
    assets/climba-logo.png \
    assets/panda-3d-map.png \
    assets/panda-3d-map.webp \
    assets/panda-streak2.4.webp \
    assets/panda-scanning.webp \
    assets/panda-analitics2.0.webp \
    assets/friends.webp \
    assets/friends.png \
    "${USER}@${HOST}:${REMOTE}/dist/media/"
  ssh_retry "chmod 755 ${REMOTE}/dist/media && chmod 644 ${REMOTE}/dist/media/*"
  echo "Media synced."
else
  echo "Skip media (pass --media if assets changed)."
fi

echo "Deployed to https://climba.ru/"
