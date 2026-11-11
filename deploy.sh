#!/usr/bin/env bash
# Ручной деплой climba.ru С ЛОКАЛЬНОЙ МАШИНЫ (rsync по SSH).
# На VPS из CI запускается scripts/server-deploy.sh, а не этот файл.
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
  git pull --ff-only
  if (( DO_INSTALL )) || [[ ! -d node_modules ]]; then
    CI=true npm install
  fi
  CI=true npm run build
fi

echo "Opening SSH (one connection)..."
open_mux

# Весь dist, кроме тяжёлого media (оно ниже, по флагу). Так в прод не забываются
# новые файлы (например qr-redirect.js) — раньше список был ручным.
rsync_code --exclude 'media/' dist/ "${USER}@${HOST}:${REMOTE}/dist/"
ssh_retry "find ${REMOTE}/dist -path ${REMOTE}/dist/media -prune -o -type f -exec chmod 644 {} +"
if (( DO_MEDIA )); then
  ssh_retry "mkdir -p ${REMOTE}/dist/media"
  # -L: public/media — симлинки на assets/, заливаем сами файлы
  rsync_media -L public/media/ \
    "${USER}@${HOST}:${REMOTE}/dist/media/"
  ssh_retry "chmod 755 ${REMOTE}/dist/media && chmod 644 ${REMOTE}/dist/media/*"
  echo "Media synced."
else
  echo "Skip media (pass --media if assets changed)."
fi

echo "Deployed to https://climba.ru/"
