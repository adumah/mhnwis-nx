#!/usr/bin/env python3
"""The homebrew menu icon of the Switch build, from your own disc: the game's dashboard art (nxeart, the 420x320
picture the Xbox 360 dashboard showed), cut to a square and scaled to 256x256, as elf2nro wants.

    python3 tools/disc_icon.py <game folder> <out.jpg>

Game art: made at build time from your copy into out/, never committed. Without nxeart or a picture in it, the
project's own icon (app/switch/icon.jpg, original artwork) is copied instead.
"""
import io
import os
import re
import shutil
import sys

game, out = sys.argv[1], sys.argv[2]
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
fallback = os.path.join(root, 'app', 'switch', 'icon.jpg')
os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)


def disc_picture():
    try:
        from PIL import Image
    except ImportError:
        print('disc icon: no Pillow (python3 -m pip install pillow)')
        return None
    path = next((os.path.join(game, n) for n in os.listdir(game) if n.lower() == 'nxeart'), None)
    if not path:
        return None
    data = open(path, 'rb').read()
    best = None
    for m in re.finditer(b'\xff\xd8\xff[\xe0\xe1\xdb]', data):
        try:
            im = Image.open(io.BytesIO(data[m.start():]))
            im.load()
        except Exception:
            continue
        if im.width >= 256 and im.height >= 256 and (best is None or im.width * im.height > best.width * best.height):
            best = im
    if best is None:
        return None
    side = min(best.width, best.height)
    left, top = (best.width - side) // 2, (best.height - side) // 2
    return best.convert('RGB').crop((left, top, left + side, top + side)).resize((256, 256), Image.LANCZOS)


picture = disc_picture()
if picture is not None:
    picture.save(out, 'JPEG', quality=95)
    print(f'disc icon: {out}, from your disc')
else:
    shutil.copyfile(fallback, out)
    print(f'disc icon: no dashboard art found, the project icon instead: {out}')
