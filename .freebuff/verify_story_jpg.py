"""بازرسی خودکار خروجی‌های story/: اندازه، فرمت، نبود نوار منو، نبود حاشیهٔ تیره، جا شدن محتوا."""
import pathlib, json
from PIL import Image

OUT = pathlib.Path('story')
rows = []
for f in sorted(OUT.glob('*.jpg')):
    im = Image.open(f)
    rgb = im.convert('RGB')
    W, H = rgb.size
    px = rgb.load()

    # رنگ کاغذ = میانهٔ چهار گوشهٔ حاشیهٔ بالا
    corners = [px[3, 3], px[W - 4, 3], px[3, H - 4], px[W - 4, H - 4]]
    bg = tuple(sorted(c[i] for c in corners)[1] for i in range(3))

    def dev(x, y):
        p = px[x, y]
        return max(abs(p[0] - bg[0]), abs(p[1] - bg[1]), abs(p[2] - bg[2]))

    # نوار منو اگر مانده باشد: متن + خطِ تمام‌عرض. شمارش پیکسل‌های مرکب در y<110
    ink = sum(1 for y in range(110) for x in range(0, W, 3) if dev(x, y) > 24)
    ink_frac = ink / (110 * (W // 3))
    full_rows = [y for y in range(110)
                 if sum(1 for x in range(0, W, 6) if dev(x, y) > 20) > (W // 6) * 0.8]

    # حاشیه‌های کناری: تیره نباشند
    side_max = max(dev(x, y) for x in (0, 2, W - 1, W - 2) for y in range(0, H, 11))

    # پایین‌ترین سطر دارای محتوا (برای اطمینان از جا شدن)
    last = max((y for y in range(H - 1, -1, -1)
                if any(dev(x, y) > 24 for x in range(0, W, 6))), default=-1)

    # نشانهٔ نوار منو: یک خط تمام‌عرضِ مرکب، یا تراکم متن بالای ۵٪ در باند بالا.
    # (منوی واقعی ۱۰۱px ارتفاع و ~۳۰٪ تراکم متن دارد؛ محتوای عادی صفحه زیر ۵٪ است.)
    nav_like = bool(full_rows) or ink_frac > 0.05
    ok_size = (W, H) == (1080, 1920)
    rows.append({
        "file": f.name, "size": f"{W}x{H}", "mode": rgb.mode, "fmt": im.format,
        "kb": round(f.stat().st_size / 1024),
        "bg": bg, "topBandInk%": round(ink_frac * 100, 2), "navLines": full_rows,
        "sideDev": side_max, "lastInkRow": last,
        "ok": ok_size and im.format == 'JPEG' and not nav_like and side_max <= 12 and last < H,
    })

bad = [r for r in rows if not r["ok"]]
print(f"{'file':34s} {'size':10s} {'fmt':4s} {'kb':>4s}  {'topInk%':>7s} {'navLine':>7s} {'sideDev':>7s} {'lastInk':>7s}")
for r in rows:
    flag = "" if r["ok"] else "   <== PROBLEM"
    print(f"{r['file']:34s} {r['size']:10s} {r['fmt']:4s} {r['kb']:4d}  "
          f"{r['topBandInk%']:7.2f} {len(r['navLines']):7d} {r['sideDev']:7d} {r['lastInkRow']:7d}{flag}")
print(f"\n{len(rows)} files | wrong size/format: {sum(1 for r in rows if r['size'] != '1080x1920' or r['fmt'] != 'JPEG')}"
      f" | nav-like top band in: {sum(1 for r in rows if r['topBandInk%'] > 5 or r['navLines'])}"
      f" | side border: {sum(1 for r in rows if r['sideDev'] > 12)}"
      f" | clipped bottom: {sum(1 for r in rows if r['lastInkRow'] >= 1920)}")
(OUT / 'verify.json').write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding='utf-8')
