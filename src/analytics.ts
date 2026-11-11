/**
 * Яндекс.Метрика: загрузка тега + цели кнопок «Скачать».
 * Вынесено из inline-скриптов index.html, чтобы можно было включить строгий CSP
 * (script-src без 'unsafe-inline').
 */

type Ym = ((counterId: number, method: string, ...args: unknown[]) => void) & {
  a?: unknown[];
  l?: number;
};

declare global {
  interface Window {
    ym?: Ym;
  }
}

const TAG_SRC = "https://mc.yandex.ru/metrika/tag.js";

export type StorePlatform = "ios" | "android";

const DOWNLOAD_GOALS: Record<StorePlatform, string> = {
  ios: "download_ios",
  android: "download_android",
};

function loadTag(): void {
  if (!window.ym) {
    const queue: Ym = (...args: unknown[]) => {
      (queue.a = queue.a || []).push(args);
    };
    queue.l = Date.now();
    window.ym = queue;
  }
  if (document.querySelector(`script[src="${TAG_SRC}"]`)) return;

  const script = document.createElement("script");
  script.async = true;
  script.src = TAG_SRC;
  document.head.append(script);
}

export function initAnalytics(counterId: number): void {
  if (!Number.isInteger(counterId) || counterId <= 0) return;

  loadTag();
  window.ym?.(counterId, "init", {
    clickmap: true,
    trackLinks: true,
    accurateTrackBounce: true,
    webvisor: true,
  });
}

export function trackDownload(counterId: number, platform: StorePlatform): void {
  window.ym?.(counterId, "reachGoal", DOWNLOAD_GOALS[platform], { platform });
}
