/**
 * Hero-видео без звука. Постер (со слоганом) виден всегда — даже если
 * автоплей заблокирован (iOS Low Power Mode, Data Saver) или включено
 * «Уменьшить движение»: тогда видео просто не запускаем.
 */
export function initHeroVideo(): void {
  const video = document.querySelector<HTMLVideoElement>("[data-hero-video]");
  if (!video) return;

  const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");

  const play = (): void => {
    if (reducedMotion.matches) return;
    video.muted = true; // требование autoplay-политик всех браузеров
    void video.play()?.catch(() => {
      // Автоплей запрещён — остаётся постер. Повторим на первом касании.
    });
  };

  reducedMotion.addEventListener?.("change", () => {
    if (reducedMotion.matches) video.pause();
    else play();
  });

  // Safari при возврате по bfcache ставит видео на паузу.
  window.addEventListener("pageshow", play);
  document.addEventListener("pointerdown", play, { once: true, passive: true });

  play();
}
