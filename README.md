# Climba landing

Публичный лендинг [climba.ru](https://climba.ru) — Vite 6 + TypeScript.

Другому агенту: это **не** мобильное приложение. Приложение — отдельный стек (`com.redizit.climba`). Здесь только сайт, статика, деплой на VPS и черновики анимации маскота.

## Локально

```bash
npm install
npm run dev
```

Сборка: `npm run build` → `dist/` (`bundled/` = JS/CSS, `public/` копируется как есть).

## Деплой

Прод: VPS `193.109.78.205`, статика в `/home/maksim/climba/climba-lending/dist`, Caddy на `climba.ru`.

С машины с ключом `~/.ssh/id_france`:

```bash
./deploy.sh            # JS/CSS/HTML/favicon, без тяжёлого media
./deploy.sh --media    # то же + картинки/видео в dist/media
./deploy.sh --install  # ещё npm install
```

CI: push в `main` → GitHub Actions (`.github/workflows/deploy.yml`) по SSH запускает `./deploy.sh` на VPS. Secrets: `SSH_HOST`, `SSH_USER`, `SSH_PRIVATE_KEY`.

Полная карта доменов, портов, AASA/Universal Links и ограничений Caddy — **`docs/INFRASTRUCTURE.md`**.

## Карта репозитория

| Путь | Зачем |
|------|--------|
| `index.html`, `src/` | лендинг |
| `privacy/`, `eula/`, `delete-account/` | legal / App Store |
| `public/` | favicon, AASA, `/qr/` |
| `assets/` | исходники медиа; в прод часть уходит в `dist/media` через `deploy.sh --media` |
| `docs/` | инфраструктура и продуктовые брифы |
| `animation/` | исходники интро/аниматика (Blender-скрипты, промпты, референс маскота) |
| `deploy.sh` | выкладка на VPS |

Рендеры, mp4 из Magnific/Blender и курсовые **не** в git — они в `animation/**/output/` и игнорятся. Канон панды для интро: `animation/intro/refs/master_c.png`, сценарий `animation/intro/CLIMBA_INTRO_SCRIPT.md`, промпты `animation/intro/PROMPTS.md`.

## Чего здесь нет

- Исходников iOS/Android приложения
- Приватного SSH-ключа (только путь в `deploy.sh`)
- Backend Kestrel / climbbox Next.js — они на том же VPS, другие каталоги
