# Climba landing — безопасность

Аудит: 2026-11-10. Что исправлено в коде и что нужно сделать руками на VPS / в GitHub.

## Исправлено в репозитории

| # | Проблема | Риск | Что сделано |
|---|----------|------|-------------|
| 1 | `appleboy/ssh-action@master` | Supply chain: владелец экшена (или взломщик) меняет `master` → код с вашим SSH-ключом от прод-сервера | Пин на SHA тега v1.2.5, `permissions: {}`, `concurrency`, таймаут |
| 2 | `npm audit`: 4 high (vite ≤6.4.3, postcss, nanoid, source-map-js) | Dev-сервер: чтение файлов вне корня, cross-origin выполнение | vite 6.4.6, `npm audit` = 0 |
| 3 | Inline-скрипты + `onclick` в HTML | Невозможно включить строгий CSP (нужен `'unsafe-inline'`) | Весь JS во внешних файлах: `src/analytics.ts`, `public/qr-redirect.js`, `public/qr/qr.js` |
| 4 | Три обработчика клика по «Скачать» (inline capture, `onclick`, `main.ts`) + `window.open` | Двойные/тройные вкладки, двойные цели в Метрике, блокировщик попапов | Один обработчик, только `reachGoal`; переход делает обычная ссылка `target=_blank rel=noopener noreferrer` |
| 5 | Google Fonts | IP каждого посетителя уходит Google (152-ФЗ, трансграничная передача), лишний origin в CSP | Rubik self-hosted через `@fontsource-variable/rubik` |
| 6 | `public/assets → ../assets` | В прод публиковались все исходники (`image.png`, `panda_qr_code.png`, …) | Симлинк удалён, в `public/media/` только то, что использует страница |
| 7 | `git pull \|\| true` в деплое | Тихо деплоится старый код, ошибка не видна | `git merge --ff-only`, `set -euo pipefail`, сборка в `dist.next` + атомарная подмена |
| 8 | `?ios=` / `?android=` принимали поддомены сторов | Слишком широкий allow-list | Только точные хосты `apps.apple.com`, `itunes.apple.com`, `play.google.com`, только `https:` |

## Сделать на VPS: заголовки безопасности в Caddy

Сейчас статика отдаётся без CSP/HSTS/защиты от фрейминга. Добавить в блок `climba.ru` в `/etc/caddy/Caddyfile`:

```caddy
climba.ru {
	header {
		Strict-Transport-Security "max-age=31536000; includeSubDomains"
		X-Content-Type-Options "nosniff"
		Referrer-Policy "strict-origin-when-cross-origin"
		Permissions-Policy "camera=(), microphone=(), geolocation=(), payment=(), usb=()"
		Cross-Origin-Opener-Policy "same-origin"
		# Сначала Report-Only: неделю смотреть консоль/Метрику, потом убрать "-Report-Only"
		Content-Security-Policy-Report-Only "default-src 'self'; script-src 'self' https://mc.yandex.ru https://yastatic.net; style-src 'self' 'unsafe-inline'; img-src 'self' data: https://mc.yandex.ru https://mc.yandex.com; connect-src 'self' https://mc.yandex.ru https://mc.yandex.com; frame-src https://mc.yandex.ru https://mc.yandex.com; child-src blob: https://mc.yandex.ru https://mc.yandex.com; media-src 'self'; font-src 'self'; object-src 'none'; base-uri 'self'; form-action 'self'; frame-ancestors 'self' https://webvisor.com https://*.webvisor.com https://metrika.yandex.ru"
		-Server
	}

	# Кэш: хешированные бандлы — навсегда, медиа — неделя, HTML — всегда свежий
	@hashed path /bundled/*
	header @hashed Cache-Control "public, max-age=31536000, immutable"
	@media path /media/*
	header @media Cache-Control "public, max-age=604800"
	@html path / /*.html /*/
	header @html Cache-Control "no-cache"

	encode zstd gzip
	# ...существующие reverse_proxy /api* и file_server...
}
```

`frame-ancestors` разрешает только сам сайт и Вебвизор (иначе сломается просмотр записей). `style-src 'unsafe-inline'` нужен Вебвизору и атрибутам `style`, которые выставляет tag.js.

Проверка после `sudo systemctl reload caddy`:

```bash
curl -sI https://climba.ru/ | grep -iE 'strict|content-security|x-content|referrer|permissions'
```

## Сделать в GitHub

1. **Репозиторий публичный**, а в нём `docs/INFRASTRUCTURE.md` (IP, SSH-порт 2244, логин, путь к ключу, внутренние порты), маркетинговые брифы и xlsx. Рекомендация: сделать репозиторий **private** (история git хранит всё, удаление файла не поможет). Перед этим настроить deploy-ключ на VPS, иначе сервер не сможет тянуть код.
2. Secrets: добавить `SSH_PORT` = `2244` (раньше порт в workflow не передавался — CI шёл на 22) и, по желанию, `SSH_HOST_FINGERPRINT` (защита от MITM):
   ```bash
   ssh-keygen -lf <(ssh-keyscan -p 2244 193.109.78.205 2>/dev/null) | grep ED25519
   ```
3. Ключ `SSH_PRIVATE_KEY` — отдельный deploy-ключ с ограничением в `~/.ssh/authorized_keys` на VPS:
   `command="cd /home/maksim/climba/climba-lending && git fetch -q origin main && git merge --ff-only origin/main && ./scripts/server-deploy.sh",no-port-forwarding,no-agent-forwarding,no-pty ssh-ed25519 AAAA...`
4. Включить Dependabot alerts + `dependabot.yml` для npm и github-actions.

## Сделать на VPS: прочее

- **Prometheus `:780` и Grafana `:781` открыты в интернет** (см. INFRASTRUCTURE.md). Prometheus не имеет авторизации — метрики, таргеты и внутренние адреса видны всем. Закрыть файрволом (`ufw deny 780`) или `basic_auth` в Caddy; Grafana — проверить, что нет `admin/admin` и анонимного доступа.
- `/swagger*` проксируется наружу — на проде лучше выключить или закрыть `basic_auth`.
- SSH: `PasswordAuthentication no`, `PermitRootLogin no`, fail2ban.

## Приватность

- Вебвизор записывает сессии. В `/privacy.ru` должно быть явно указано использование Яндекс.Метрики и Вебвизора (cookies, запись действий на сайте) — проверить формулировку у юриста.
