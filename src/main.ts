import "./styles.css";

const qs = <T extends Element>(selector: string): T | null => {
  return document.querySelector(selector);
};

const isHttpUrl = (value: string): boolean => /^https?:\/\//i.test(value);

/** Только официальные сторы — иначе ?ios=/?android= = open redirect / phishing. */
const STORE_HOSTS = new Set([
  "apps.apple.com",
  "itunes.apple.com",
  "play.google.com",
]);

function isAllowedStoreUrl(value: string): boolean {
  if (!isHttpUrl(value)) return false;
  try {
    const url = new URL(value);
    if (url.protocol !== "https:") return false;
    const host = url.hostname.toLowerCase();
    return STORE_HOSTS.has(host) || [...STORE_HOSTS].some((h) => host.endsWith(`.${h}`));
  } catch {
    return false;
  }
}

type LinkUpdater = {
  selector: string;
  queryKey: "ios" | "android";
};

function applyStoreLinksFromQuery(): void {
  const params = new URLSearchParams(window.location.search);

  const updaters: LinkUpdater[] = [
    { selector: "[data-ios]", queryKey: "ios" },
    { selector: "[data-android]", queryKey: "android" },
  ];

  for (const upd of updaters) {
    const href = params.get(upd.queryKey);
    if (!href || !isAllowedStoreUrl(href)) continue;

    for (const el of document.querySelectorAll<HTMLAnchorElement>(upd.selector)) {
      el.href = href;
      el.target = "_blank";
      el.rel = "noopener noreferrer";
    }
  }
}

/** iOS/Safari: muted + playsinline + loop. Без звука — безопасный autoplay. */
function initHeroVideo(): void {
  const video = qs<HTMLVideoElement>("[data-hero-video]");
  if (!video) return;

  video.muted = true;
  video.defaultMuted = true;
  video.playsInline = true;
  video.controls = false;
  video.loop = true;
  video.autoplay = true;
  video.setAttribute("playsinline", "");
  video.setAttribute("webkit-playsinline", "");

  const showVideo = (): void => {
    video.classList.add("is-playing");
  };

  const play = (): void => {
    const promise = video.play();
    if (promise) {
      promise.then(showVideo).catch(() => {
        // iOS может заблокировать autoplay до касания.
      });
    }
  };

  video.addEventListener("playing", showVideo, { once: true });
  video.addEventListener("loadedmetadata", play, { once: true });
  video.addEventListener("canplay", play, { once: true });
  video.addEventListener("ended", () => {
    video.currentTime = 0;
    play();
  });
  window.addEventListener("pageshow", play, { once: true });

  play();

  let tries = 0;
  const timer = window.setInterval(() => {
    if (!video.paused) {
      window.clearInterval(timer);
      showVideo();
      return;
    }
    if (tries++ > 20) {
      window.clearInterval(timer);
      return;
    }
    play();
  }, 400);

  document.addEventListener("touchstart", play, { once: true, passive: true });
  document.addEventListener("click", play, { once: true });
}

type StorePlatform = "ios" | "android";

const DOWNLOAD_GOALS: Record<StorePlatform, string> = {
  ios: "download_ios",
  android: "download_android",
};

/** Клик по любой кнопке «Скачать» — одна цель на платформу (шапка и низ страницы). */
function initDownloadTracking(): void {
  const counterId = Number(document.documentElement.dataset.ymCounter || 0);
  if (counterId <= 0) return;

  document.addEventListener(
    "click",
    (event) => {
      const target = event.target;
      if (!(target instanceof Element)) return;

      const link = target.closest<HTMLAnchorElement>("[data-ios], [data-android]");
      if (!link) return;

      const platform: StorePlatform = link.hasAttribute("data-ios") ? "ios" : "android";

      // Не даём уйти на #ios / #android — иначе Метрика пишет просмотр URL, а не цель.
      event.preventDefault();

      const w = window as Window & { ym?: (...args: unknown[]) => void };
      if (typeof w.ym === "function") {
        w.ym(counterId, "reachGoal", DOWNLOAD_GOALS[platform], { platform });
      }

      const href = link.getAttribute("href") || "";
      // Только https-ссылки (сторы / заранее прошитые URL в HTML)
      if (isHttpUrl(href) && href.toLowerCase().startsWith("https:")) {
        window.open(href, "_blank", "noopener,noreferrer");
      }
    },
    true,
  );
}

/** Реальная высота fixed-nav → --headerH (отступ hero). Жёсткий cap — без петли на весь экран. */
function syncHeaderHeight(): void {
  const nav = qs<HTMLElement>(".nav");
  if (!nav) return;
  // top:0 fixed → height === bottom; не пишем это обратно в min-height шапки
  const h = Math.ceil(nav.getBoundingClientRect().height);
  const capped = Math.min(Math.max(h, 56), 148);
  document.documentElement.style.setProperty("--headerH", `${capped}px`);
}

/**
 * Кнопки в одну строку с логотипом:
 * 1) сужаем горизонтальный padding (текст не трогаем)
 * 2) если при min padding всё ещё налезают на лого / край — второй уровень
 */
function fitNavDownloadButtons(): void {
  const inner = qs<HTMLElement>(".nav__inner");
  const right = qs<HTMLElement>(".nav__right");
  const logo = qs<HTMLElement>(".nav__logo");
  if (!inner || !right || !logo) return;

  const buttons = Array.from(
    right.querySelectorAll<HTMLAnchorElement>(".downloadBtn"),
  );
  if (buttons.length === 0) return;

  const MAX_PAD = 18;
  const MIN_PAD = 8;
  // Запас: иначе на SE кнопка визуально ест хвост «climba» (шрифт/субпиксели).
  const MIN_GAP = 16;
  // Только совсем узкие экраны; на 400+ сначала жмём padding, не второй ряд.
  const FORCE_STACK_WIDTH = 340;

  const clearInlinePad = (): void => {
    for (const btn of buttons) {
      btn.style.paddingLeft = "";
      btn.style.paddingRight = "";
    }
  };

  const setPad = (pad: number): void => {
    for (const btn of buttons) {
      btn.style.paddingLeft = `${pad}px`;
      btn.style.paddingRight = `${pad}px`;
    }
  };

  const stack = (): void => {
    clearInlinePad();
    inner.classList.add("nav__inner--stacked");
    syncHeaderHeight();
  };

  /** Не scrollWidth: лого сжималось и «влезало» визуально наезжая. */
  const collides = (): boolean => {
    const innerBox = inner.getBoundingClientRect();
    const logoBox = logo.getBoundingClientRect();
    const rightBox = right.getBoundingClientRect();
    const first = buttons[0].getBoundingClientRect();
    const last = buttons[buttons.length - 1].getBoundingClientRect();

    // Одна линия: сравниваем по Y, иначе после wrap ложное «пересечение» по X.
    const sameRow = Math.abs(first.top - logoBox.top) < 12;
    if (sameRow && first.left < logoBox.right + MIN_GAP) return true;
    if (sameRow && rightBox.left < logoBox.right + MIN_GAP) return true;
    if (last.right > innerBox.right - 0.5) return true;
    if (inner.scrollWidth > inner.clientWidth + 0.5) return true;
    return false;
  };

  if (inner.clientWidth <= FORCE_STACK_WIDTH) {
    stack();
    return;
  }

  // Сброс в однострочный режим
  inner.classList.remove("nav__inner--stacked");
  clearInlinePad();
  setPad(MAX_PAD);
  // reflow перед замером
  void inner.offsetWidth;

  if (!collides()) {
    syncHeaderHeight();
    return;
  }

  for (let pad = MAX_PAD - 1; pad >= MIN_PAD; pad -= 1) {
    setPad(pad);
    void inner.offsetWidth;
    if (!collides()) {
      syncHeaderHeight();
      return;
    }
  }

  // Min padding всё ещё мало — второй уровень, нормальный padding
  stack();
}

function initNavLayout(): void {
  const nav = qs<HTMLElement>(".nav");
  if (!nav) return;

  let scheduled = 0;
  const run = (): void => {
    if (scheduled) cancelAnimationFrame(scheduled);
    scheduled = requestAnimationFrame(() => {
      scheduled = 0;
      fitNavDownloadButtons();
    });
  };

  run();
  window.addEventListener("resize", run, { passive: true });
  // Не ResizeObserver на .nav — смена --headerH/stacked сама меняет размер и зациклит.

  for (const img of nav.querySelectorAll("img")) {
    if (!img.complete) img.addEventListener("load", run, { once: true });
  }

  // Rubik может подгрузиться позже и расширить кнопки → снова проверить.
  if (document.fonts?.ready) {
    void document.fonts.ready.then(run);
  }
  document.fonts?.addEventListener?.("loadingdone", run);
}

function init(): void {
  applyStoreLinksFromQuery();
  initNavLayout();
  initHeroVideo();
  initDownloadTracking();
}

init();
