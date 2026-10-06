/*
 * fit.js — نمایش «تک‌صفحه‌ای» (بدون اسکرول)
 *
 * بوم هر صفحه ۱۰۸۰×۱۹۲۰ (نسبت استوری) طراحی شده تا هم حالت دسکتاپ و هم
 * اسکرین‌شات استوری دقیقاً اندازه بماند. این اسکریپت فقط وقتی وارد می‌شود که
 * صفحه در viewport فعلی جا نمی‌شود (معمولاً موبایل یا پنجره‌ی کوتاه):
 *   ۱) کلاس is-fit را روی <body> می‌گذارد،
 *   ۲) بوم را با scale مناسب روی صفحه می‌نشاند،
 *   ۳) ارتفاع بوم را دقیقاً با فضای زیر نوار ناوبری هم‌اندازه می‌کند تا
 *      فضای خالی به‌صورت یکنواخت توزیع شود و پایین صفحه به انتهای
 *      viewport بچسبد (پس هیچ اسکرولی لازم نیست).
 */
(function () {
  var canvas = document.querySelector('.canvas');
  if (!canvas) return;

  var nav = document.querySelector('.site-nav');
  var raf = 0;

  function fit() {
    raf = 0;

    // اول حالت fit را روشن می‌کنیم تا اسکرول‌بار (و در نتیجه عرض viewport)
    // درست اندازه‌گیری شود؛ بعد ابعاد طبیعی بوم را می‌سنجیم.
    document.body.classList.add('is-fit');
    canvas.style.removeProperty('--fit-scale');
    canvas.style.removeProperty('--fit-top');
    canvas.style.removeProperty('height');

    var vw = document.documentElement.clientWidth;
    var vh = window.innerHeight;
    var w = canvas.offsetWidth;
    var h = canvas.offsetHeight;

    if (!w || !h || vw <= 0 || vh <= 0) {
      document.body.classList.remove('is-fit');
      return;
    }

    // اگر صفحه در viewport جا می‌شود، دست نمی‌زنیم (حفظ اندازه‌ی استوری)
    if (vw >= w && vh >= h) {
      document.body.classList.remove('is-fit');
      return;
    }

    var navH = nav ? Math.round(nav.getBoundingClientRect().height) : 0;
    var availH = vh - navH;
    if (availH <= 0) {
      document.body.classList.remove('is-fit');
      return;
    }

    var scale = Math.min(vw / w, availH / h);
    if (!(scale > 0)) {
      document.body.classList.remove('is-fit');
      return;
    }

    // ۳) اعمال: ارتفاع بوم = فضای موجود / scale  → همیشه ≥ ارتفاع طبیعی
    document.body.classList.add('is-fit');
    canvas.style.setProperty('--fit-scale', String(scale));
    canvas.style.setProperty('--fit-top', navH + 'px');
    canvas.style.height = Math.ceil(availH / scale) + 'px';
  }

  function schedule() {
    if (raf) return;
    raf = window.requestAnimationFrame(fit);
  }

  window.addEventListener('resize', schedule);
  window.addEventListener('orientationchange', schedule);
  window.addEventListener('load', schedule);

  // بارگذاری فونت/تصاویر می‌تواند ارتفاع طبیعی بوم را عوض کند
  if (document.fonts && document.fonts.ready) {
    document.fonts.ready.then(schedule).catch(function () {});
  }
  Array.prototype.forEach.call(document.images, function (img) {
    if (!img.complete) img.addEventListener('load', schedule, { once: true });
  });

  fit();
})();
