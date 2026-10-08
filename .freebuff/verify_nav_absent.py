"""آزمون قطعیِ نبودِ نوار منو: مقایسهٔ خروجی با رندر «منو پنهان» و «منو پیدا»."""
import pathlib, json
from PIL import Image, ImageChops
from playwright.sync_api import sync_playwright

ROOT = pathlib.Path('.').resolve()
ORDER = json.loads((ROOT / 'story' / 'export.json').read_text(encoding='utf-8'))
SAMPLE = {"00-index.jpg", "01-edu-1-bachelor.jpg", "07-proj-1-overview.jpg",
          "11-teach-1-overview.jpg", "18-pub-4-full-list.jpg", "26-mentor-3-team-lead.jpg"}

PREP = """(hide) => {
  const nav = document.querySelector('.site-nav');
  if (nav) nav.style.display = hide ? 'none' : '';
  document.body.classList.remove('is-fit');
  const c = document.querySelector('.canvas');
  c.style.removeProperty('height'); c.style.removeProperty('--fit-scale'); c.style.removeProperty('--fit-top');
  c.style.transformOrigin = 'top center';
  c.style.transform = 'scale(' + Math.min(1, 1920 / c.offsetHeight) + ')';
  c.style.margin = '0 auto';
  const paper = getComputedStyle(c).backgroundColor;
  document.documentElement.style.background = paper; document.body.style.background = paper;
  document.documentElement.style.overflow = 'hidden'; document.body.style.overflow = 'hidden';
  return nav ? Math.round(nav.getBoundingClientRect().height) : 0;
}"""

def mad(a, b, box=None):
    d = ImageChops.difference(a.crop(box) if box else a, b.crop(box) if box else b).convert('L')
    px = list(d.getdata())
    return sum(px) / len(px)

rows = []
with sync_playwright() as p:
    b = p.chromium.launch(channel="chrome")
    pg = b.new_context(viewport={"width": 1080, "height": 1920}, device_scale_factor=1).new_page()
    pg.route("**/fit.js", lambda r: r.abort())
    for rec in ORDER:
        if rec["file"] not in SAMPLE:
            continue
        jpg = Image.open(ROOT / 'story' / rec["file"]).convert('RGB')
        out = {}
        for hide in (True, False):
            pg.goto((ROOT / rec["page"]).as_uri(), wait_until="load")
            pg.evaluate("document.fonts.ready"); pg.wait_for_timeout(200)
            navh = pg.evaluate(PREP, hide); pg.wait_for_timeout(150)
            tmp = ROOT / 'story' / '_t.png'
            pg.screenshot(path=str(tmp), type="png")
            im = Image.open(tmp).convert('RGB'); tmp.unlink()
            out[hide] = (mad(im, jpg, (0, 0, 1080, 110)), mad(im, jpg, (0, 110, 1080, 1920)))
        rows.append({"file": rec["file"], "navHeight": navh,
                     "hiddenTop": round(out[True][0], 2), "visibleTop": round(out[False][0], 2),
                     "hiddenRest": round(out[True][1], 2), "visibleRest": round(out[False][1], 2)})
    b.close()

print(f"{'file':34s} {'navH':>5s} {'منو پنهان: باند بالا':>22s} {'منو پیدا':>9s} | {'پنهان: بدنه':>12s} {'پیدا':>6s}")
for r in rows:
    print(f"{r['file']:34s} {r['navHeight']:5d} {r['hiddenTop']:22.2f} {r['visibleTop']:9.2f} | "
          f"{r['hiddenRest']:12.2f} {r['visibleRest']:6.2f}")
# index.html عنصر .site-nav ندارد؛ پس فقط صفحه‌های دارای منو آزمون‌شدنی‌اند.
with_nav = [r for r in rows if r["navHeight"] > 0]
ok = all(r["hiddenTop"] < 1.0 and r["visibleTop"] > 10 for r in with_nav)
print(f"\n{len(with_nav)} صفحهٔ دارای منو، {len(rows) - len(with_nav)} صفحهٔ بدون منو (index.html)")
print(f"باند بالای خروجی‌ها عیناً برابرِ رندرِ بدونِ منو است و با رندرِ منو‌دار تفاوت چشمگیر دارد: {ok}")
(ROOT / 'story' / 'nav_absent.json').write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding='utf-8')
