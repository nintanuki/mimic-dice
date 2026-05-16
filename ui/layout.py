"""Window-frame layout: where the tray, stats panel, and message log go.

The window is partitioned into three non-overlapping regions plus a uniform
outer padding (`LayoutSettings.PANEL_PADDING`) and a gap between the tray and
its neighbors (`LayoutSettings.PANEL_GAP`):

    +---------------------+----------+
    |                     |          |
    |     Dice tray       |  Stats   |
    |                     |  panel   |
    +---------------------+          |
    |     Message log     |          |
    +---------------------+----------+

Functions here are pure: given a window size, they return `pygame.Rect`
instances. Callers that own state (the tray, panel renderers, the log) read
their region from here on init and again on `pygame.VIDEORESIZE`, so layout
stays responsive without any cross-system coupling.
"""

import pygame

from settings import LayoutSettings


# -------------------------
# REGION HELPERS
# -------------------------


def _tray_available_size(window_size: tuple[int, int]) -> tuple[int, int]:
    """Compute the width/height available to the tray after panels are removed.

    Both panels sit outside the tray, separated by `PANEL_GAP`, and the whole
    layout is inset by `PANEL_PADDING` on every side.

    Args:
        window_size: Current `(width, height)` of the display surface.

    Returns:
        Tuple of `(available_width, available_height)` in window pixels. Values
        are clamped to zero so callers never see negative dimensions on tiny
        windows.
    """
    window_width, window_height = window_size
    available_width = (
        window_width
        - 2 * LayoutSettings.PANEL_PADDING
        - LayoutSettings.PANEL_GAP
        - LayoutSettings.STATS_PANEL_WIDTH
    )
    available_height = (
        window_height
        - 2 * LayoutSettings.PANEL_PADDING
        - LayoutSettings.PANEL_GAP
        - LayoutSettings.MESSAGE_LOG_HEIGHT
    )
    return max(0, available_width), max(0, available_height)


# -------------------------
# REGION RECTS
# -------------------------


def tray_region_rect(window_size: tuple[int, int]) -> pygame.Rect:
    """Return the rect the dice tray should occupy (top-left region)."""
    available_width, available_height = _tray_available_size(window_size)
    return pygame.Rect(
        LayoutSettings.PANEL_PADDING,
        LayoutSettings.PANEL_PADDING,
        available_width,
        available_height,
    )


def message_log_rect(window_size: tuple[int, int]) -> pygame.Rect:
    """Return the rect the message log should occupy (bottom strip)."""
    available_width, _ = _tray_available_size(window_size)
    _, window_height = window_size
    return pygame.Rect(
        LayoutSettings.PANEL_PADDING,
        window_height
        - LayoutSettings.PANEL_PADDING
        - LayoutSettings.MESSAGE_LOG_HEIGHT,
        available_width,
        LayoutSettings.MESSAGE_LOG_HEIGHT,
    )


def stats_panel_rect(window_size: tuple[int, int]) -> pygame.Rect:
    """Return the rect the stats panel should occupy (right column)."""
    window_width, window_height = window_size
    return pygame.Rect(
        window_width
        - LayoutSettings.PANEL_PADDING
        - LayoutSettings.STATS_PANEL_WIDTH,
        LayoutSettings.PANEL_PADDING,
        LayoutSettings.STATS_PANEL_WIDTH,
        max(0, window_height - 2 * LayoutSettings.PANEL_PADDING),
    )
