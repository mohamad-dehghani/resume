import pathlib, json
from PIL import Image
from playwright.sync_api import sync_playwright

ROOT = pathlib.Path('.').resolve()
OUT = ROOT / 'story'
OUT.mkdir(exist_ok=True)

# ترتیب پست‌کردن: فهرست، بعد ۳۲ صفحه به ترتیب فصل‌ها
ORDER = [
    "index.html",
    "01-Education/edu-1-bachelor.html", "01-Education/edu-2-master.html", "01-Education/edu-3-phd.html",
    "02-Work-experience/work-1-overview.html", "02-Work-experience/work-2-history.html", "02-Work-experience/work-3-skills.html",
    "03-Projects/proj-1-overview.html", "03-Projects/proj-2-health-assistant.html",
    "03-Projects/proj-3-market-prediction.html", "03-Projects/proj-4-profanity-detection.html",
    "04-Teaching/teach-1-overview.html", "04-Teaching/teach-2-courses.html", "04-Teaching/teach-3-courses part 2.html",
    "05-Papers/pub-0-overview-v2.html", "05-Papers/pub-1-distributed-dl-v2.html", "05-Papers/pub-2-snp-bert-v2.html",
    "05-Papers/pub-3-sustainable-energy-v2.html", "05-Papers/pub-4-full-list.html",
    "06-Recommendation-Professional/letters-1-intro.html", "06-Recommendation-Professional/letters-2-lifeweb.html",
    "06-Recommendation-Professional/letters-3-nikamooz.html", "06-Recommendation-Professional/letters-4-aron.html",
    "06-Recommendation-Professional/letters-5-zobahan.html",
    "07-Recommendation-Academic/mentor-1-intro.html", "07-Recommendation-Academic/mentor-2-mansouri.html",
    "07-Recommendation-Academic/mentor-3-team-lead.html", "07-Recommendation-Academic/mentor-4-vafaei.html",
    "07-Recommendation-Academic/mentor-5-akhoondzadeh.html",
    "08-Books/book-1-deep-learning.html", "08-Books/book-2-ml.html", "08-Books/book-3-nlp.html",
]

PREP = """(H) => {
  const nav = document.querySelector('.site-nav');
  if (nav) nav.style.display = 'none';           // نوار منو داخل خروجی نباشد
  document.body.classList.remove('is-fit');
  const c = document.querySelector('.canvas');
  c.style.removeProperty('height');
  c.style.removeProperty('--fit-scale');
  c.style.removeProperty('--fit-top');
  const h = c.offsetHeight;
  const s = Math.min(1, H / h);                  // صفحه‌های بلندتر از ۱۹۲۰ مقیاس می‌خورند
  c.style.transformOrigin = 'top center';
  c.style.transform = 'scale(' + s + ')';
  c.style.margin = '0 auto';
  // پس‌زمینه‌ی صفحه هم‌رنگ کاغذِ بوم تا حاشیه‌های کناری هم‌رنگ استوری بمانند
  const paper = getComputedStyle(c).backgroundColor;
  document.documentElement.style.background = paper;
  document.body.style.background = paper;
  document.documentElement.style.overflow = 'hidden';
  document.body.style.overflow = 'hidden';
  return { natural: h, scale: s, nav: nav ? getComputedStyle(nav).display : 'absent' };
}"""

report = []
with sync_playwright() as p:
    b = p.chromium.launch(channel="chrome")
    ctx = b.new_context(viewport={"width": 1080, "height": 1920}, device_scale_factor=2)
    pg = ctx.new_page()
    pg.route("**/fit.js", lambda r: r.abort())   # چیدمان را خودمان کنترل می‌کنیم
    for i, rel in enumerate(ORDER):
        pg.goto(pathlib.Path(ROOT, rel).as_uri(), wait_until="load")
        pg.evaluate("document.fonts.ready")
        pg.wait_for_timeout(200)
        info = pg.evaluate(PREP, 1920)
        pg.wait_for_timeout(140)
        name = f"{i:02d}-index.jpg" if rel == "index.html" else f"{i:02d}-{pathlib.Path(rel).stem}.jpg"
        tmp = OUT / (name + ".png")
        pg.screenshot(path=str(tmp), type="png")             # 2160×3840 با dsf=2
        Image.open(tmp).convert('RGB').resize((1080, 1920), Image.LANCZOS).save(
            OUT / name, 'JPEG', quality=97, subsampling=0, optimize=True, progressive=True)
        tmp.unlink()
        report.append({"seq": i, "file": name, "page": rel, "natural": info["natural"],
                       "scale": round(info["scale"], 4), "navDisplay": info["nav"]})
    b.close()

(OUT / 'export.json').write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding='utf-8')
scaled = [r for r in report if r['scale'] < 1]
for r in report:
    print(f"{r['file']:40s} {r['page']:52s} H={r['natural']:5d} scale={r['scale']:.3f} nav={r['navDisplay']}")
print(f"\n{len(report)} JPGs written to story/")
print(f"{len(scaled)} tall pages scaled to fit 1920:")
for r in scaled:
    print(f"   {r['file']:40s} {r['natural']} -> 1920 (x{r['scale']:.3f})")
