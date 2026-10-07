#!/usr/bin/env bash
set -euo pipefail

HOST="193.109.78.205"
PORT="2244"
KEY="${HOME}/.ssh/id_france"
REMOTE="/home/maksim/climba/climba-lending"
SSH="ssh -p ${PORT} -i ${KEY} maksim@${HOST}"
RSYNC="rsync -avz -e \"ssh -p ${PORT} -i ${KEY}\""

git pull || true
CI=true npm install
CI=true npm run build

# dist/assets/ на VPS только для чтения — деплоим в dist/bundled/
# плюс точечно новые публичные файлы hero (видео/постер)
eval "${RSYNC} dist/bundled/ maksim@${HOST}:${REMOTE}/dist/bundled/"
eval "${RSYNC} dist/qr/ maksim@${HOST}:${REMOTE}/dist/qr/"
eval "${RSYNC} dist/index.html maksim@${HOST}:${REMOTE}/dist/index.html"
${SSH} "mkdir -p ${REMOTE}/dist/media"
eval "${RSYNC} assets/main-video-background.mp4 assets/hero-poster.jpg maksim@${HOST}:${REMOTE}/dist/media/"
eval "${RSYNC} dist/assets/panda-scanning.png maksim@${HOST}:${REMOTE}/dist/assets/"

echo "Deployed to https://climba.ru/"
