from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter
import math
import subprocess

ROOT = Path(__file__).resolve().parents[1]
ICONSET = ROOT / "PremiumApps.iconset"
ICONSET.mkdir(exist_ok=True)

def make_icon(size):
    scale = 4
    n = size * scale
    im = Image.new("RGBA", (n, n), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    margin = int(n * .055)
    radius = int(n * .19)
    d.rounded_rectangle((margin, margin, n-margin, n-margin), radius=radius,
                        fill=(18, 18, 20, 255), outline=(85, 85, 85, 255), width=max(1, n//180))
    # Twelve-point burst, matching the supplied black-and-gold app mark.
    cx = cy = n / 2
    outer, inner = n * .36, n * .235
    pts = []
    for i in range(24):
        a = -math.pi / 2 + i * math.pi / 12
        r = outer if i % 2 == 0 else inner
        pts.append((cx + math.cos(a)*r, cy + math.sin(a)*r))
    shadow = [(x+n*.008, y+n*.018) for x,y in pts]
    d.polygon(shadow, fill=(0, 0, 0, 190))
    d.polygon(pts, fill=(210, 185, 0, 255))
    d.line(pts + [pts[0]], fill=(255, 231, 82, 255), width=max(2, n//90), joint="curve")
    im = im.filter(ImageFilter.GaussianBlur(radius=scale*.45))
    return im.resize((size, size), Image.Resampling.LANCZOS)

for size, name in [
    (16, "icon_16x16.png"), (32, "icon_16x16@2x.png"),
    (32, "icon_32x32.png"), (64, "icon_32x32@2x.png"),
    (128, "icon_128x128.png"), (256, "icon_128x128@2x.png"),
    (256, "icon_256x256.png"), (512, "icon_256x256@2x.png"),
    (512, "icon_512x512.png"), (1024, "icon_512x512@2x.png"),
]:
    make_icon(size).save(ICONSET / name)

subprocess.run(["iconutil", "-c", "icns", str(ICONSET), "-o", str(ROOT / "PremiumApps.icns")], check=True)
