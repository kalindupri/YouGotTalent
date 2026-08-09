import io
import re
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

# Branded template: dark background, red glow behind the logo badge, faint grid, bold
# uppercase headline, gray subtext, red pill CTA — matches the hand-made teaser graphic
# this replaces (see marketing feature discussion). Regenerated fresh from a post's
# topic/content each time it's needed (draft preview, then again at Facebook-publish time)
# rather than stored, since it's deterministic and cheap to render.

CANVAS = 1080
BG_COLOR = (10, 8, 11)
ACCENT_COLOR = (227, 28, 95)
WHITE = (255, 255, 255)
GRAY = (156, 163, 175)

FONT_DIR = Path("/usr/share/fonts/truetype/dejavu")
BOLD_FONT_PATH = FONT_DIR / "DejaVuSans-Bold.ttf"
REGULAR_FONT_PATH = FONT_DIR / "DejaVuSans.ttf"

_SITE_LINE_RE = re.compile(r"\s*Discover more at yougottalent\.lk\.?\s*$")
_LEADING_EMOJI_RE = re.compile(r"^[^\w\s]+\s*")


def content_to_subtext(content: str) -> str:
    text = _SITE_LINE_RE.sub("", content)
    text = _LEADING_EMOJI_RE.sub("", text)
    return text.strip()


def _font(path: Path, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(path), size)


def _wrap(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont, max_width: float, max_lines: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if draw.textlength(candidate, font=font) <= max_width or not current:
            current = candidate
        else:
            lines.append(current)
            current = word
        if len(lines) == max_lines:
            current = ""
            break
    if current:
        lines.append(current)
    return lines


def _fit_headline(draw: ImageDraw.ImageDraw, headline: str, max_width: float) -> tuple[ImageFont.FreeTypeFont, list[str]]:
    size = 76
    while size > 36:
        font = _font(BOLD_FONT_PATH, size)
        lines = _wrap(draw, headline, font, max_width, max_lines=3)
        if lines and all(draw.textlength(line, font=font) <= max_width for line in lines):
            return font, lines
        size -= 4
    font = _font(BOLD_FONT_PATH, size)
    return font, _wrap(draw, headline, font, max_width, max_lines=3)


def _draw_grid(img: Image.Image, spacing: int = 54) -> None:
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    w, h = img.size
    for x in range(0, w, spacing):
        draw.line([(x, 0), (x, h)], fill=(255, 255, 255, 10), width=1)
    for y in range(0, h, spacing):
        draw.line([(0, y), (w, y)], fill=(255, 255, 255, 10), width=1)
    img.alpha_composite(overlay)


def _draw_glow(img: Image.Image, center: tuple[int, int], radius: int, color: tuple[int, int, int]) -> None:
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    cx, cy = center
    draw.ellipse([cx - radius, cy - radius, cx + radius, cy + radius], fill=(*color, 90))
    overlay = overlay.filter(ImageFilter.GaussianBlur(radius // 3))
    img.alpha_composite(overlay)


def _centered_text(draw: ImageDraw.ImageDraw, y: float, text: str, font: ImageFont.FreeTypeFont, fill: tuple[int, int, int]) -> None:
    w = draw.textlength(text, font=font)
    draw.text((CANVAS / 2 - w / 2, y), text, font=font, fill=fill)


def generate_post_image(headline: str, subtext: str) -> bytes:
    img = Image.new("RGBA", (CANVAS, CANVAS), (*BG_COLOR, 255))
    _draw_glow(img, (CANVAS // 2, 260), 420, ACCENT_COLOR)
    _draw_grid(img)
    draw = ImageDraw.Draw(img)

    badge_size = 100
    badge_x0 = CANVAS // 2 - badge_size // 2
    badge_y0 = 70
    draw.rounded_rectangle(
        [badge_x0, badge_y0, badge_x0 + badge_size, badge_y0 + badge_size], radius=26, fill=ACCENT_COLOR
    )
    y_font = _font(BOLD_FONT_PATH, 56)
    y_bbox = draw.textbbox((0, 0), "Y", font=y_font)
    y_w, y_h = y_bbox[2] - y_bbox[0], y_bbox[3] - y_bbox[1]
    draw.text(
        (badge_x0 + badge_size / 2 - y_w / 2 - y_bbox[0], badge_y0 + badge_size / 2 - y_h / 2 - y_bbox[1]),
        "Y",
        font=y_font,
        fill=WHITE,
    )

    _centered_text(draw, badge_y0 + badge_size + 18, "YouGotTalent", _font(BOLD_FONT_PATH, 44), WHITE)
    _centered_text(draw, badge_y0 + badge_size + 76, "SRI LANKA'S TALENT MARKETPLACE", _font(BOLD_FONT_PATH, 18), ACCENT_COLOR)

    max_width = CANVAS - 140
    headline_font, lines = _fit_headline(draw, headline.upper(), max_width)
    line_height = headline_font.size + 12
    total_h = line_height * len(lines)
    headline_top = 420 - total_h / 2
    for i, line in enumerate(lines):
        color = ACCENT_COLOR if len(lines) > 1 and i == len(lines) - 1 else WHITE
        _centered_text(draw, headline_top + i * line_height, line, headline_font, color)

    subtext_font = _font(REGULAR_FONT_PATH, 26)
    sub_lines = _wrap(draw, subtext, subtext_font, CANVAS - 220, max_lines=3)
    sub_y = headline_top + total_h + 34
    for i, line in enumerate(sub_lines):
        _centered_text(draw, sub_y + i * 36, line, subtext_font, GRAY)

    pill_font = _font(BOLD_FONT_PATH, 26)
    pill_text = "yougottalent.lk"
    text_w = draw.textlength(pill_text, font=pill_font)
    pill_w = text_w + 70
    pill_h = 62
    pill_x0 = CANVAS / 2 - pill_w / 2
    pill_y0 = CANVAS - 140
    draw.rounded_rectangle(
        [pill_x0, pill_y0, pill_x0 + pill_w, pill_y0 + pill_h], radius=pill_h / 2, fill=ACCENT_COLOR
    )
    draw.text((CANVAS / 2 - text_w / 2, pill_y0 + pill_h / 2 - 16), pill_text, font=pill_font, fill=WHITE)

    buffer = io.BytesIO()
    img.convert("RGB").save(buffer, format="PNG")
    return buffer.getvalue()
