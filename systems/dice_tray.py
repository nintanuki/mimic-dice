"""Dice tray: the rectangular play area dice bounce inside.

The tray is purely a UI region. It exposes:
  * `rect`         - the visible border rect, in window pixels.
  * `inner_rect()` - the slightly-smaller rect used as physics bounds, so
                     dice don't visually clip into the border.
  * `draw()`       - render the brown radial gradient fill and rounded border.

`DiceRoller` owns one tray and feeds its bounds to each `AnimatedDie`.

Tray fill
---------
The fill is a radial gradient that goes from `TRAY_FILL_CENTER` (warm tan)
at the middle to `TRAY_FILL_EDGE` (dark walnut) at the corners — gives
the play area a lit-from-above wood-table look. The gradient is rendered
at low resolution (`_GRADIENT_RESOLUTION`) and smooth-scaled up to the
tray's current size, then masked by a filled rounded rect so the
gradient honors the same `TRAY_CORNER_RADIUS` the border does. We cache
the rendered gradient and only rebuild on a `resize()` or first draw, so
the per-frame cost is just one blit + one outline.
"""

import math
from typing import Optional

import pygame

from settings import ColorSettings, DiceSettings, ScreenSettings
from ui import layout


# Low-res working size for the gradient before smoothscale. Small enough
# that the per-pixel loop is cheap, big enough that the upscale stays smooth.
_GRADIENT_RESOLUTION = 64


class DiceTray:
    """Bounded play area drawn as a rounded, gradient-filled rectangle."""

    def __init__(self, window_size: tuple[int, int]):
        """Create the tray rect from the current layout.

        Args:
            window_size: Current (width, height) of the display surface.
        """
        self.rect = pygame.Rect(0, 0, 0, 0)
        # Cached gradient surface sized to `self.rect`; rebuilt on resize.
        self._gradient_cache: Optional[pygame.Surface] = None
        self.resize(window_size)

    # -------------------------
    # GEOMETRY
    # -------------------------

    def resize(self, window_size: tuple[int, int]) -> None:
        """Recompute the tray rect when the window size changes.

        The tray occupies the top-left region returned by `ui.layout`, which
        subtracts the right-hand stats panel and bottom message log from the
        window so all three regions share one source of truth and stay
        responsive to `VIDEORESIZE`.

        Args:
            window_size: New (width, height) of the display surface.
        """
        self.rect = layout.tray_region_rect(window_size)
        # Invalidate the gradient cache; it'll rebuild on the next draw at
        # the new size. Done here (not in draw) so a layout change is the
        # only trigger — draws stay free of size comparisons.
        self._gradient_cache = None

    def inner_rect(self, margin: int) -> pygame.Rect:
        """Return the rect shrunk by `margin` pixels on every side.

        Used as the physics boundary so the die's half-extent fits inside
        the visible border instead of overlapping it.
        """
        return self.rect.inflate(-margin * 2, -margin * 2)

    # -------------------------
    # RENDER
    # -------------------------

    def draw(self, surface: pygame.Surface) -> None:
        """Render the tray's gradient fill and rounded border."""
        corner_radius = DiceSettings.TRAY_CORNER_RADIUS

        # A zero-area tray (extreme resize) has nothing to render and the
        # gradient builder would divide by zero — bail before either.
        if self.rect.width <= 0 or self.rect.height <= 0:
            return

        if self._gradient_cache is None:
            self._gradient_cache = self._build_gradient(
                self.rect.size, corner_radius,
            )

        surface.blit(self._gradient_cache, self.rect.topleft)

        # Border on top of the fill so the outline stays crisp at any radius.
        pygame.draw.rect(
            surface,
            ColorSettings.TRAY_BORDER_COLOR,
            self.rect,
            width=ScreenSettings.UI_BORDER_WIDTH,
            border_radius=corner_radius,
        )

    @staticmethod
    def _build_gradient(
        size: tuple[int, int], corner_radius: int,
    ) -> pygame.Surface:
        """Render the radial brown gradient clipped to a rounded rect.

        Two-step pipeline so we don't pay for a full-resolution per-pixel
        loop every resize:
          1. Build a low-res (`_GRADIENT_RESOLUTION`) gradient where each
             pixel's color lerps between `TRAY_FILL_CENTER` (at the center)
             and `TRAY_FILL_EDGE` (at the farthest corner), keyed by
             normalized distance from the center.
          2. `smoothscale` it up to `size` and mask the alpha by a filled
             rounded rect so the corners match the border's `corner_radius`.

        Args:
            size: Final (width, height) of the gradient surface in pixels.
            corner_radius: Rounded-corner radius in pixels (matches border).

        Returns:
            An RGBA surface of `size` with the gradient inside the rounded
            rect and full transparency outside it. Ready to blit at the
            tray's `topleft`.
        """
        width, height = size

        # ---- Step 1: low-res radial gradient ----
        small_w = small_h = _GRADIENT_RESOLUTION
        small = pygame.Surface((small_w, small_h), pygame.SRCALPHA)
        center_x, center_y = small_w / 2, small_h / 2
        # Distance to a corner is the largest distance any pixel can have,
        # so dividing by it gives a normalized [0, 1] gradient parameter.
        max_distance = math.sqrt(center_x ** 2 + center_y ** 2)
        center_r, center_g, center_b = ColorSettings.TRAY_FILL_CENTER
        edge_r,   edge_g,   edge_b   = ColorSettings.TRAY_FILL_EDGE
        for y in range(small_h):
            for x in range(small_w):
                dx, dy = x - center_x, y - center_y
                t = min(1.0, math.sqrt(dx * dx + dy * dy) / max_distance)
                r = int(center_r * (1 - t) + edge_r * t)
                g = int(center_g * (1 - t) + edge_g * t)
                b = int(center_b * (1 - t) + edge_b * t)
                small.set_at((x, y), (r, g, b, 255))

        # ---- Step 2: smoothscale + rounded-corner mask ----
        scaled = pygame.transform.smoothscale(small, (width, height))

        # Mask = white rounded rect on a fully-transparent surface. Using
        # BLEND_RGBA_MIN with the scaled gradient keeps the gradient's RGB
        # intact (mask RGB is 255 everywhere inside the rect) while
        # clamping alpha to the mask's alpha — so anything outside the
        # rounded rect becomes transparent.
        mask = pygame.Surface((width, height), pygame.SRCALPHA)
        pygame.draw.rect(
            mask,
            (255, 255, 255, 255),
            pygame.Rect(0, 0, width, height),
            border_radius=corner_radius,
        )
        scaled.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
        return scaled
