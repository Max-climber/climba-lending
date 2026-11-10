# Climba — инфраструктура (prod)

> Проверено: 2026-08-21. Источник: VPS `193.109.78.205`, `curl`, SSH.

## Домены и DNS

| Домен | A-запись | Назначение |
|-------|----------|------------|
| `climba.ru` | `193.109.78.205` | Лендинг + API + Universal Links |
| `www.climba.ru` | → редирект на `climba.ru` | Caddy |
| `climbbox.ru` | `193.109.78.205` | Отдельное веб-приложение (Next.js) |
| `www.climbbox.ru` | → редирект на `climbbox.ru` | Caddy |

NS: Timeweb. Панель хостинга Timeweb для `climbbox.ru` **не обслуживает** прод — оба домена смотрят на VPS.

## VPS

| Параметр | Значение |
|----------|----------|
| IP | `193.109.78.205` |
| SSH | `ssh -p 2244 -i ~/.ssh/id_france maksim@193.109.78.205` |
| Hostname | `climba` |
| Reverse proxy | **Caddy** (`/etc/caddy/Caddyfile`) |

## Маршрутизация `climba.ru` (Caddy)

```
climba.ru
├── /api*, /swagger*, /apple-app-site-association, /.well-known/*
│   └── reverse_proxy → localhost:3701  (Kestrel / .NET backend)
└── всё остальное
    └── file_server → /home/maksim/climba/climba-lending/dist  (статический лендинг)
```

**Важно:** AASA отдаёт **бэкенд (Kestrel)**, не папка `dist/`. Файлы в `public/apple-app-site-association` репозитория попадут в prod только если изменить Caddy или backend.

## Лендинг (этот репозиторий)

| Параметр | Значение |
|----------|----------|
| Путь на VPS | `/home/maksim/climba/climba-lending` |
| Статика | `/home/maksim/climba/climba-lending/dist` |
| Деплой | push в `main` → GitHub Actions → `./deploy.sh` |
| `deploy.sh` | `git pull && CI=true npm install && CI=true npm run build` |
| Workflow | `.github/workflows/deploy.yml` (secrets: `SSH_HOST`, `SSH_USER`, `SSH_PRIVATE_KEY`) |

## Universal Links (iOS) — QR на скалодроме

**Проблема была:** AASA содержал `"*"` → любой URL на `climba.ru` открывал приложение TestFlight.

**Текущее состояние (prod, 2026-08-21):** AASA исправлен — только deep links:

```json
{
  "applinks": {
    "details": [{
      "appIDs": ["KPFH462529.com.redizit.climba"],
      "components": [
        { "/": "/open/*" },
        { "/": "/app/*" }
      ]
    }]
  }
}
```

Проверка:

```bash
curl -s https://climba.ru/apple-app-site-association
```

**Не путать:** `/.well-known/assetlinks.json` — только **Android** App Links. На iOS не влияет.

**После смены AASA на iPhone:** удалить TestFlight-сборку Climba → подождать ~24 ч (кэш Apple CDN) → снова сканировать QR.

## `climbbox.ru`

| Параметр | Значение |
|----------|----------|
| Caddy | `reverse_proxy → localhost:3700` |
| Процесс | PM2 `climbbox` |
| Путь | `/home/maksim/standalone/server.js` |
| Стек | Next.js |

## Прочие сервисы на VPS (порты)

| Порт | Назначение |
|------|------------|
| 3701 | Kestrel backend (climba API + AASA) |
| 3700 | climbbox Next.js |
| 9090 | Prometheus (`climba.ru:780`) |
| 3000 | Grafana (`climba.ru:781`) |

## QR-трекинг (локально в репо, не задеплоено)

- UTM: `?utm_source=luch&utm_medium=qr&utm_campaign=panda_stand`
- Страница `/qr/` → редирект с UTM (`public/qr/index.html`)
- Яндекс.Метрика: закомментирована в `index.html`, нужен ID счётчика

## Рекомендация по поддомену

**Поддомен не нужен** для решения QR: достаточно исправленного AASA. Лендинг остаётся на `climba.ru` — 0 ₽.

Поддомен (`landing.climba.ru`) имеет смысл только если нужно разделить «точку QR» и «основной сайт» по разным URL.

## Контакты приложения

- iOS bundle: `com.redizit.climba`
- Apple Team ID: `KPFH462529`
- Android package: `com.redizit.climba`
