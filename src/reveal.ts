/**
 * Плавное появление блоков при прокрутке (.reveal → .is-visible).
 * Без JS, без IntersectionObserver или при «Уменьшить движение» блоки просто видны.
 */
export function initReveal(): void {
  const items = document.querySelectorAll<HTMLElement>(".reveal");
  const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  if (items.length === 0 || reducedMotion || !("IntersectionObserver" in window)) return;

  const observer = new IntersectionObserver(
    (entries) => {
      for (const entry of entries) {
        if (!entry.isIntersecting) continue;
        entry.target.classList.add("is-visible");
        observer.unobserve(entry.target);
      }
    },
    { rootMargin: "0px 0px -8% 0px" },
  );

  document.documentElement.classList.add("has-reveal");
  for (const item of items) observer.observe(item);
}
