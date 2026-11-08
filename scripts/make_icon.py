from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter
import math
import platform
import subprocess

ROOT = Path(__file__).resolve().parents[1]

def make_icon(size):
    scale = 3
    n = size * scale
    im = Image.new("RGBA", (n, n), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    m = int(n * .055)
    d.rounded_rectangle((m, m, n-m, n-m), radius=int(n*.19),
                        fill=(18,18,20,255), outline=(85,85,85,255), width=max(1,n//180))
    cx=cy=n/2
    pts=[]
    for i in range(24):
        a=-math.pi/2+i*math.pi/12
        r=n*(.36 if i%2==0 else .235)
        pts.append((cx+math.cos(a)*r,cy+math.sin(a)*r))
    d.polygon([(x+n*.008,y+n*.018) for x,y in pts],fill=(0,0,0,180))
    d.polygon(pts,fill=(210,185,0,255))
    d.line(pts+[pts[0]],fill=(255,231,82,255),width=max(2,n//90),joint="curve")
    return im.resize((size,size),Image.Resampling.LANCZOS)

if platform.system() == "Darwin":
    iconset=ROOT/"PremiumApps.iconset"
    iconset.mkdir(exist_ok=True)
    for size,name in [(16,"icon_16x16.png"),(32,"icon_16x16@2x.png"),
                      (32,"icon_32x32.png"),(64,"icon_32x32@2x.png"),
                      (128,"icon_128x128.png"),(256,"icon_128x128@2x.png"),
                      (256,"icon_256x256.png"),(512,"icon_256x256@2x.png"),
                      (512,"icon_512x512.png"),(1024,"icon_512x512@2x.png")]:
        make_icon(size).save(iconset/name)
    subprocess.run(["iconutil","-c","icns",str(iconset),"-o",str(ROOT/"PremiumApps.icns")],check=True)
else:
    make_icon(256).save(ROOT/"PremiumApps.ico",format="ICO",sizes=[(16,16),(32,32),(48,48),(64,64),(128,128),(256,256)])
