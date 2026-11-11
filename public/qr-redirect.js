// Наклейка-QR ведёт на https://climba.ru/ без параметров → считаем скан на /qr/.
// Внешний файл (не inline) — совместим со строгим CSP.
// Переходы внутри сайта (лого, «На главную») и из поиска приходят с referrer —
// их не редиректим, иначе они засчитываются как скан QR и ломают метрику.
(function () {
  var path = location.pathname;
  if ((path === "/" || path === "/index.html") && !location.search && !document.referrer) {
    location.replace("/qr/");
  }
})();
