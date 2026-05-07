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

/** Автоплей фонового видео; зацикливание через атрибут loop в разметке. */
function initHeroVideo(): void {
  const video = qs<HTMLVideoElement>("[data-hero-video]");
  if (!video) return;

  void video.play().catch(() => {
    // Автоплей может быть ограничен политикой браузера.
  });
}

function init(): void {
  applyStoreLinksFromQuery();
  initHeroVideo();
}

init();

