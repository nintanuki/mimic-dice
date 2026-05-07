import pygame
from settings import DiceSettings, ScreenSettings


class DiceTray:
    """Bounded play area that constrains dice and is drawn as an outlined box."""

    def __init__(self, window_size: tuple[int, int]):
        """Create the tray rect anchored to the window using DiceSettings.

        Args:
            window_size: Current (width, height) of the display surface.
        """
        self.rect = pygame.Rect(0, 0, 0, 0)
        self.resize(window_size)

    def resize(self, window_size: tuple[int, int]) -> None:
        """Recompute the tray rect when the window size changes.

        The tray anchors to the top-left of the window with a configurable
        padding, and uses a configurable size. It is clamped so it never
        spills outside the window.

        Args:
            window_size: New (width, height) of the display surface.
        """
        win_w, win_h = window_size
        pad_x, pad_y = DiceSettings.TRAY_PADDING
        max_w = max(0, win_w - pad_x)
        max_h = max(0, win_h - pad_y)
        w = min(DiceSettings.TRAY_SIZE[0], max_w)
        h = min(DiceSettings.TRAY_SIZE[1], max_h)
        self.rect = pygame.Rect(pad_x, pad_y, w, h)

    def inner_rect(self, margin: int) -> pygame.Rect:
        """Return the rect shrunk by `margin` on every side.

        Used as the actual physics boundary so the die's half-extent fits
        inside the visible border.
        """
        return self.rect.inflate(-margin * 2, -margin * 2)

    def draw(self, surface: pygame.Surface) -> None:
        """Render the tray border."""
        pygame.draw.rect(
            surface,
            DiceSettings.TRAY_BORDER_COLOR,
            self.rect,
            ScreenSettings.UI_BORDER_WIDTH,
        )
