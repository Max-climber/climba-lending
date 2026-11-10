"""Extract the vector "climba" logo-mark from the brand guidebook PDF into an SVG.

Usage: python3 extract_logo_svg.py <guidebook.pdf> <out.svg>
Requires: pymupdf (pip install pymupdf)
"""

import sys

import fitz

PAGE_INDEX = 6  # "Вариации начертания логотипа"
LOGO_AREA = fitz.Rect(200, 340, 840, 510)  # top-left "Лого-марка" card
LETTERS = "climba"


def _pt(p: fitz.Point, origin: fitz.Point) -> str:
    return f"{p.x - origin.x:.3f},{p.y - origin.y:.3f}"


def drawing_to_path(drawing: dict, origin: fitz.Point) -> str:
    """Convert one PyMuPDF drawing into SVG path data, starting a subpath on every gap."""
    parts: list[str] = []
    cursor = None
    for item in drawing["items"]:
        kind, start = item[0], item[1]
        if cursor is None or abs(start - cursor) > 0.01:
            if cursor is not None:
                parts.append("Z")
            parts.append(f"M{_pt(start, origin)}")
        if kind == "l":
            parts.append(f"L{_pt(item[2], origin)}")
            cursor = item[2]
        elif kind == "c":
            parts.append(f"C{_pt(item[2], origin)} {_pt(item[3], origin)} {_pt(item[4], origin)}")
            cursor = item[4]
        else:
            raise ValueError(f"Unsupported path item: {kind}")
    parts.append("Z")
    return " ".join(parts)


def main(pdf_path: str, out_path: str) -> None:
    page = fitz.open(pdf_path)[PAGE_INDEX]
    glyphs = sorted(
        (d for d in page.get_drawings() if d.get("fill") and LOGO_AREA.contains(d["rect"])),
        key=lambda d: d["rect"].x0,
    )
    if len(glyphs) != len(LETTERS):
        raise SystemExit(f"Expected {len(LETTERS)} glyphs, found {len(glyphs)}")

    bounds = fitz.Rect(glyphs[0]["rect"])
    for g in glyphs[1:]:
        bounds |= g["rect"]

    paths = "\n".join(
        f'  <path id="{letter}" fill="#000714" fill-rule="{"evenodd" if g.get("even_odd") else "nonzero"}" '
        f'd="{drawing_to_path(g, bounds.tl)}"/>'
        for letter, g in zip(LETTERS, glyphs)
    )
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {bounds.width:.3f} {bounds.height:.3f}">\n'
        f"{paths}\n</svg>\n"
    )
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"Saved {out_path} ({bounds.width:.0f}x{bounds.height:.0f})")


if __name__ == "__main__":
    main(*sys.argv[1:3])
