// Скан QR-наклейки: цель qr_scan в счётчике 111839566 → лендинг с UTM.
// Внешний файл (не inline) — совместим со строгим CSP.
(function () {
  var COUNTER = 111839566;
  var TARGET = "/?utm_source=gym&utm_medium=qr&utm_campaign=panda_stand";
  var TAG = "https://mc.yandex.ru/metrika/tag.js?id=" + COUNTER;

  window.ym =
    window.ym ||
    function () {
      (window.ym.a = window.ym.a || []).push(arguments);
    };
  window.ym.l = Date.now();

  var s = document.createElement("script");
  s.async = true;
  s.src = TAG;
  document.head.appendChild(s);

  new Image().src = "https://mc.yandex.ru/watch/" + COUNTER + "?ut=noindex&rn=" + Date.now();

  window.ym(COUNTER, "init", {
    clickmap: true,
    trackLinks: true,
    accurateTrackBounce: true,
    webvisor: true,
  });
  // Цель считается КАЖДЫЙ раз (визиты в Метрике группируются по сессии ~30 мин)
  window.ym(COUNTER, "reachGoal", "qr_scan");

  setTimeout(function () {
    location.replace(TARGET);
  }, 600);
})();
