import { trackDownload, type StorePlatform } from "./analytics";

/** Только официальные сторы — иначе ?ios=/?android= = open redirect / фишинг. */
const STORE_HOSTS: ReadonlySet<string> = new Set([
  "apps.apple.com",
  "itunes.apple.com",
  "play.google.com",
]);

const SELECTORS: Record<StorePlatform, string> = {
  ios: "[data-ios]",
  android: "[data-android]",
};

export function isAllowedStoreUrl(value: string): boolean {
  try {
    const url = new URL(value);
    return url.protocol === "https:" && STORE_HOSTS.has(url.hostname.toLowerCase());
  } catch {
    return false;
  }
}

/** ?ios=<url>&android=<url> — подмена ссылок (кампании), только на сторы. */
export function applyStoreLinksFromQuery(search: string = window.location.search): void {
  const params = new URLSearchParams(search);

  for (const platform of Object.keys(SELECTORS) as StorePlatform[]) {
    const href = params.get(platform);
    if (!href || !isAllowedStoreUrl(href)) continue;

    for (const link of document.querySelectorAll<HTMLAnchorElement>(SELECTORS[platform])) {
      link.href = href;
    }
  }
}

/**
 * Одна цель на платформу при клике по любой кнопке «Скачать».
 * Переход делает сам браузер (обычная ссылка target=_blank rel=noopener):
 * без preventDefault/window.open — нет двойных вкладок и блокировщика попапов.
 */
export function initDownloadTracking(counterId: number): void {
  document.addEventListener("click", (event) => {
    const target = event.target;
    if (!(target instanceof Element)) return;

    const link = target.closest<HTMLAnchorElement>(`${SELECTORS.ios}, ${SELECTORS.android}`);
    if (!link) return;

    trackDownload(counterId, link.matches(SELECTORS.ios) ? "ios" : "android");
  });
}
