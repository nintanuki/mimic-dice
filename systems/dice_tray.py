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


class DiceTray:
    """Bounded play area drawn as a rounded, filled rectangle."""

    def __init__(self, window_size: tuple[int, int]):
        """Create the tray rect anchored to the window using DiceSettings.

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

        The tray anchors to the top-left of the window with configurable
        padding and uses a configurable size. It is clamped so it never
        spills outside the window.

        Args:
            window_size: New (width, height) of the display surface.
        """
        window_width, window_height = window_size
        padding_x, padding_y = DiceSettings.TRAY_PADDING
        max_width = max(0, window_width - padding_x)
        max_height = max(0, window_height - padding_y)
        tray_width = min(DiceSettings.TRAY_SIZE[0], max_width)
        tray_height = min(DiceSettings.TRAY_SIZE[1], max_height)
        self.rect = pygame.Rect(padding_x, padding_y, tray_width, tray_height)

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
