"""
Synthetic avatar image generator + R2 upload for the presentation seed.

Generates clearly-synthetic portrait avatars using Pillow — no real people,
no copyright issues. Each avatar is a coloured circle with an initial, rendered
with a slight gradient/glow to look distinct and polished enough for a demo.
"""
from __future__ import annotations

import io
import math
import uuid
from datetime import UTC, datetime

from PIL import Image, ImageDraw, ImageFilter

from app.config import get_settings
from app.models.media import MediaAsset
from app.services.r2_storage import R2Storage

# ---------------------------------------------------------------------------
# Palette — distinct colours per seed_index bucket
# ---------------------------------------------------------------------------
_PALETTES: list[tuple[int, int, int]] = [
    (91, 143, 209),   # blue
    (230, 100, 90),   # coral
    (80, 185, 130),   # teal-green
    (200, 130, 70),   # warm amber
    (150, 90, 200),   # violet
    (220, 70, 130),   # rose
    (60, 160, 190),   # cerulean
    (180, 150, 50),   # gold
    (100, 190, 80),   # lime green
    (190, 80, 160),   # magenta
    (50, 140, 160),   # dark teal
    (220, 120, 50),   # burnt orange
]

_IMG_SIZE = 400
_MIME_TYPE = "image/jpeg"
_PROVIDER = "r2"
_MEDIA_TYPE = "profile_media"


def _pick_colour(seed_index: int, gender: str) -> tuple[int, int, int]:
    """Deterministically pick a palette colour from the seed index."""
    base = _PALETTES[(seed_index - 1) % len(_PALETTES)]
    if gender == "female":
        # Slightly warmer tint
        r = min(255, base[0] + 15)
        g = base[1]
        b = max(0, base[2] - 10)
        return (r, g, b)
    return base


def _generate_avatar(seed_index: int, initials: str, gender: str) -> bytes:
    """
    Create a 400×400 JPEG avatar: coloured circle with white initials.
    Returns raw JPEG bytes.
    """
    size = _IMG_SIZE
    colour = _pick_colour(seed_index, gender)

    # Background
    img = Image.new("RGB", (size, size), (245, 245, 245))
    draw = ImageDraw.Draw(img)

    # Soft outer glow — draw progressively lighter larger circles
    cx, cy, r = size // 2, size // 2, size // 2
    for step in range(20, 0, -1):
        factor = step / 20.0
        glow_r = int(r + step * 1.5)
        alpha_col = tuple(
            int(c * factor + 245 * (1 - factor)) for c in colour
        )
        draw.ellipse(
            (cx - glow_r, cy - glow_r, cx + glow_r, cy + glow_r),
            fill=alpha_col,  # type: ignore[arg-type]
        )

    # Main circle
    draw.ellipse((5, 5, size - 5, size - 5), fill=colour)

    # Apply slight blur for soft edges
    img = img.filter(ImageFilter.GaussianBlur(radius=1))
    draw = ImageDraw.Draw(img)

    # Draw initials using default PIL bitmap font (always available)
    # We'll render each character individually for sizing control
    text = initials[:2].upper()
    # Use a large truetype-style approach: draw scaled characters
    font_size = size // 3
    # PIL default font is small; we draw a scaled version by compositing
    # a small text image and upscaling it
    txt_img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    txt_draw = ImageDraw.Draw(txt_img)
    # Draw at font size using default font with manual approach
    char_w = font_size // 2
    char_h = font_size
    total_w = len(text) * char_w
    x_start = (size - total_w) // 2
    y_start = (size - char_h) // 2

    # Use stroke/fill approach with scaling
    # Draw the text as a high-res render then downscale for antialiasing
    hi_size = size * 4
    hi = Image.new("RGB", (hi_size, hi_size), colour)
    hi_draw = ImageDraw.Draw(hi)
    # Estimate text bounding: default font 10px; scale to hi_size/size
    scale = hi_size // size
    # Draw white filled rectangle blocks for each character (abstract initial)
    # Simple block-letter approach: render using PIL's default font at large scale
    hi_draw.text(
        (hi_size // 2, hi_size // 2),
        text,
        fill=(255, 255, 255),
        anchor="mm",
    )
    hi_resized = hi.resize((size, size), Image.LANCZOS)
    img = Image.alpha_composite(
        img.convert("RGBA"),
        hi_resized.convert("RGBA"),
    ).convert("RGB")

    # Encode to JPEG
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85, optimize=True)
    return buf.getvalue()


def _upload_to_r2(r2: R2Storage, object_key: str, data: bytes) -> None:
    """Directly upload bytes to R2 (bypasses presigned URL flow for seeding)."""
    r2._call(
        "put_object",
        Bucket=r2.settings.r2_bucket,
        Key=object_key,
        Body=data,
        ContentType=_MIME_TYPE,
    )


async def create_avatar_media_asset(
    session,
    user_id: str,
    seed_index: int,
    first_name: str,
    last_name: str,
    gender: str,
) -> MediaAsset:
    """
    Generate a synthetic avatar, upload it to R2, and persist a MediaAsset
    record with processing_status=ready and moderation_status=approved.
    Returns the persisted MediaAsset.
    """
    settings = get_settings()
    r2 = R2Storage(settings)

    initials = (first_name[:1] + last_name[:1]).upper()
    image_bytes = _generate_avatar(seed_index, initials, gender)

    media_id = str(uuid.uuid4())
    object_key = f"profile/{media_id}/original.jpg"

    _upload_to_r2(r2, object_key, image_bytes)

    now = datetime.now(UTC)
    asset = MediaAsset(
        id=media_id,
        user_id=user_id,
        media_type=_MEDIA_TYPE,
        storage_provider=_PROVIDER,
        object_key=object_key,
        processing_status="ready",
        moderation_status="approved",
        visibility="profile_only",
        mime_type=_MIME_TYPE,
        size_bytes=len(image_bytes),
        width=_IMG_SIZE,
        height=_IMG_SIZE,
        sort_order=0,
        created_at=now,
        updated_at=now,
    )
    session.add(asset)
    # Don't commit here — let the caller batch-commit
    return asset
