"""Generate simple mod thumbnails"""
from PIL import Image, ImageDraw
BITS = 32
WIDTH = 256
HEIGHT = 256


def make_thumb(text: str) -> Image:
    img = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.text((70, 80), "CC2", (32, 0, 0), font_size=64)
    draw.text((32, 32), text, (255, 0, 0), font_size=24)
    draw.text((162, 240), "A Cerebus Mod", (128, 0, 0))
    return img
