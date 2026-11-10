from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path("/Users/maksimizrailev/Desktop/climba-lending-2")
OUT = ROOT / "animation/output/animatic_end_card.png"
FONT = "/System/Library/Fonts/Supplemental/Arial.ttf"
FONT_BOLD = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"

im = Image.new("RGB", (1080, 1920), "#101116")
d = ImageDraw.Draw(im)

def centered(text: str, y: int, size: int, color: str, bold: bool = False) -> None:
    font = ImageFont.truetype(FONT_BOLD if bold else FONT, size)
    box = d.textbbox((0, 0), text, font=font)
    x = (1080 - (box[2] - box[0])) // 2
    d.text((x, y), text, font=font, fill=color)

centered("ПОГНАЛИ ЛАЗАТЬ", 760, 76, "white", True)
centered("ВМЕСТЕ С CLIMBA", 870, 66, "#ff603d", True)
centered("АНИМАТИК • ЧЕРНОВОЙ МОНТАЖ", 1810, 26, "#9a9ca5")
im.save(OUT)
print(OUT)
