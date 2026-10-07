import "./styles.css";

const qs = <T extends Element>(selector: string): T | null => {
  return document.querySelector(selector);
};

const isHttpUrl = (value: string): boolean => /^https?:\/\//i.test(value);

type LinkUpdater = {
  selector: string;
  queryKey: "ios" | "android";
};

function applyStoreLinksFromQuery(): void {
  const params = new URLSearchParams(window.location.search);

  const updaters: LinkUpdater[] = [
    { selector: '[data-ios]', queryKey: "ios" },
    { selector: '[data-android]', queryKey: "android" },
  ];

  for (const upd of updaters) {
    const href = params.get(upd.queryKey);
    if (!href) continue;

    for (const el of document.querySelectorAll<HTMLAnchorElement>(upd.selector)) {
      el.href = href;

      if (isHttpUrl(href)) {
        el.target = "_blank";
        el.rel = "noopener noreferrer";
      } else {
        el.removeAttribute("target");
        el.removeAttribute("rel");
      }
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
      if (isHttpUrl(href)) {
        window.open(href, link.target || "_blank", "noopener,noreferrer");
      }
    },
    true,
  );
}

function init(): void {
  applyStoreLinksFromQuery();
  initHeroVideo();
  initDownloadTracking();
}

init();
