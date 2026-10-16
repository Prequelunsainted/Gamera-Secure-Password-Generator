"""Imagens da interface, geradas a partir da silhueta do Gamera."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from PIL import Image, ImageChops, ImageFilter

ASSETS_DIR = Path(__file__).resolve().parent / "assets"
SILHOUETTE = ASSETS_DIR / "gamera.png"

Color = tuple[int, int, int]


def hex_to_rgb(value: str) -> Color:
    value = value.lstrip("#")
    return tuple(int(value[i : i + 2], 16) for i in (0, 2, 4))  # type: ignore[return-value]


@lru_cache(maxsize=1)
def _silhouette_mask() -> Image.Image:
    """Canal alfa da silhueta, recortado e sem as linhas brancas internas."""
    src = Image.open(SILHOUETTE).convert("RGBA")
    src = src.crop(src.getbbox())
    alpha = src.getchannel("A")
    not_white = src.convert("L").point(lambda v: 0 if v > 235 else 255)
    return ImageChops.multiply(alpha, not_white)


def _vertical_gradient(size: tuple[int, int], top: Color, bottom: Color) -> Image.Image:
    width, height = size
    strip = Image.new("RGB", (1, height))
    for y in range(height):
        t = y / max(height - 1, 1)
        strip.putpixel((0, y), tuple(round(a + (b - a) * t) for a, b in zip(top, bottom)))
    return strip.resize(size)


def hero_image(top: str, bottom: str, glow: str, glow_strength: float = 0.55) -> Image.Image:
    """Silhueta em degradê com um brilho suave ao redor."""
    mask = _silhouette_mask()
    margin = 36
    canvas_size = (mask.width + margin * 2, mask.height + margin * 2)

    padded = Image.new("L", canvas_size, 0)
    padded.paste(mask, (margin, margin))
    halo_alpha = padded.filter(ImageFilter.GaussianBlur(22)).point(
        lambda v: round(v * glow_strength)
    )
    canvas = Image.new("RGBA", canvas_size, hex_to_rgb(glow) + (0,))
    canvas.putalpha(halo_alpha)

    body = _vertical_gradient(mask.size, hex_to_rgb(top), hex_to_rgb(bottom)).convert("RGBA")
    body.putalpha(mask)
    canvas.alpha_composite(body, (margin, margin))
    return canvas


def icon_image(color: str, size: int = 64) -> Image.Image:
    """Ícone quadrado da janela."""
    mask = _silhouette_mask()
    scale = (size - 4) / max(mask.size)
    resized = mask.resize((round(mask.width * scale), round(mask.height * scale)), Image.LANCZOS)

    body = Image.new("RGBA", resized.size, hex_to_rgb(color) + (255,))
    body.putalpha(resized)
    icon = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    icon.alpha_composite(body, ((size - resized.width) // 2, (size - resized.height) // 2))
    return icon
