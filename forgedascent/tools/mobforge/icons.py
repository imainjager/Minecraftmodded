"""16x16 item icons for the Eye of Cthulhu content (hand-built pixel art, no other mod's textures)."""
import math
from pathlib import Path

from PIL import Image

OUT = Path(__file__).resolve().parents[2] / "src/main/resources/assets/forgedascent/textures/item"


def suspicious_eye():
    img = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    px = img.load()
    cx = cy = 7.3
    for y in range(16):
        for x in range(16):
            dx, dy = x - cx, y - cy
            d = math.hypot(dx, dy)
            if d > 6.7:
                continue
            if d > 5.7:
                px[x, y] = (86, 22, 38, 255)                      # dark rim
                continue
            shade = 0.5 + 0.5 * (-dx - dy) / 8.0                    # light from the top left
            base = (250, 244, 232) if shade > 0.55 else (232, 216, 202) if shade > 0.3 else (206, 182, 172)
            px[x, y] = (*base, 255)
            if d < 3.5:                                             # iris
                ring = (30, 86, 108) if d > 2.9 else (92, 160, 62) if d > 1.8 else (232, 176, 44)
                px[x, y] = (*ring, 255)
            if d < 1.7:                                             # pupil
                px[x, y] = (10, 6, 12, 255)
    for x, y in ((5, 5), (4, 4)):                                   # glint
        px[x, y] = (255, 255, 255, 255)
    for x, y in ((3, 8), (2, 9), (3, 6), (2, 5), (10, 3), (11, 2), (11, 6), (12, 7), (10, 10), (11, 11), (7, 11), (6, 12), (8, 11)):
        px[x, y] = (176, 28, 40, 255)                               # veins
    for x, y, c in ((12, 12, (206, 84, 98)), (13, 13, (186, 64, 82)), (13, 14, (160, 48, 70)), (14, 14, (160, 48, 70))):
        px[x, y] = (*c, 255)                                        # little nerve stalk
    OUT.mkdir(parents=True, exist_ok=True)
    img.save(OUT / "suspicious_looking_eye.png")
    img.resize((128, 128), Image.NEAREST).save(Path(__file__).parent / "shots" / "icon_suspicious_eye_x8.png")


if __name__ == "__main__":
    (Path(__file__).parent / "shots").mkdir(exist_ok=True)
    suspicious_eye()
    print("icons written")
