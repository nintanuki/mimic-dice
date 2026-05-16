"""Dice tray: the rectangular play area dice bounce inside.

The tray is purely a UI region. It exposes:
  * `rect`         - the visible border rect, in window pixels.
  * `inner_rect()` - the slightly-smaller rect used as physics bounds, so
                     dice don't visually clip into the border.
  * `draw()`       - render the felt fill and the rounded border.

`DiceRoller` owns one tray and feeds its bounds to each `AnimatedDie`.
"""

import pygame

from settings import ColorSettings, DiceSettings, ScreenSettings
from ui import layout


class DiceTray:
    """Bounded play area drawn as a rounded, filled rectangle."""

    def __init__(self, window_size: tuple[int, int]):
        """Create the tray rect from the current layout.

        Args:
            window_size: Current (width, height) of the display surface.
        """
        self.rect = pygame.Rect(0, 0, 0, 0)
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
        """Render the tray's felt fill and rounded border."""
        corner_radius = DiceSettings.TRAY_CORNER_RADIUS
        # Felt fill first, then the border on top so the outline stays crisp.
        pygame.draw.rect(
            surface,
            ColorSettings.TRAY_FILL_COLOR,
            self.rect,
            border_radius=corner_radius,
        )
        pygame.draw.rect(
            surface,
            ColorSettings.TRAY_BORDER_COLOR,
            self.rect,
            width=ScreenSettings.UI_BORDER_WIDTH,
            border_radius=corner_radius,
        )
