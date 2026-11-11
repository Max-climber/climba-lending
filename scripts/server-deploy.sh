#!/usr/bin/env bash
# Выполняется НА VPS из GitHub Actions (.github/workflows/deploy.yml).
# Собирает лендинг в dist.next и атомарно подменяет dist — сайт не отдаёт 404
# во время сборки, а упавшая сборка не трогает рабочую версию.
set -euo pipefail

# Код обновляет workflow (git merge --ff-only) до вызова этого скрипта.
cd "$(dirname "$0")/.."

CI=true npm ci --no-audit --no-fund
npx tsc --noEmit
CI=true npx vite build --outDir dist.next --emptyOutDir

# Симлинки public/media → assets копируются как файлы; права для Caddy
find dist.next -type d -exec chmod 755 {} +
find dist.next -type f -exec chmod 644 {} +

rm -rf dist.prev
[[ -d dist ]] && mv dist dist.prev
mv dist.next dist
echo "Deployed $(git rev-parse --short HEAD) → $(pwd)/dist"
