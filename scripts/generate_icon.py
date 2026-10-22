#!/usr/bin/env python3
"""Build a Greek α → A Windows icon. Pillow is a build-time-only dependency.

This source file, not opaque binary data, is the reproducible icon asset.
"""
from __future__ import annotations
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / 'assets'
SIZE = 1024


def choose_font(size):
    for candidate in ('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
                      'C:/Windows/Fonts/arial.ttf', 'DejaVuSans.ttf', 'arial.ttf'):
        try:
            return ImageFont.truetype(candidate, size)
        except OSError:
            continue
    raise RuntimeError('A font supporting Greek alpha is needed to build the Windows icon.')


def generate():
    TARGET.mkdir(parents=True, exist_ok=True)
    image = Image.new('RGBA', (SIZE, SIZE), (0, 0, 0, 0))
    pen = ImageDraw.Draw(image)
    for y in range(35, 988):
        ratio=(y-35)/952
        color=(round(11+3*ratio), round(34+78*ratio), round(63+75*ratio), 255)
        pen.line((35,y,989,y),fill=color,width=1)
    mask=Image.new('L',(SIZE,SIZE),0)
    ImageDraw.Draw(mask).rounded_rectangle((35,35,990,990),radius=205,fill=255)
    image.putalpha(mask)
    pen=ImageDraw.Draw(image)
    pen.rounded_rectangle((35,35,990,990),radius=205,outline=(72,185,191,255),width=12)
    pen.text((109,92),'α',font=choose_font(605),fill='white',stroke_width=3,stroke_fill='white')
    pen.line((514,595,658,595),fill=(174,245,234,255),width=47)
    pen.polygon([(650,512),(743,595),(650,678)],fill=(174,245,234,255))
    pen.ellipse((743,429,980,666),fill=(3,127,138,255),outline=(191,249,240,255),width=8)
    pen.text((766,414),'A',font=choose_font(275),fill='white')
    image.save(TARGET/'GreeklishRenamer.png')
    image.save(TARGET/'GreeklishRenamer.ico', sizes=[(16,16),(24,24),(32,32),
                                                        (48,48),(64,64),(128,128),(256,256)])
    print('Generated', TARGET/'GreeklishRenamer.ico', TARGET/'GreeklishRenamer.png')


if __name__ == '__main__':
    generate()
