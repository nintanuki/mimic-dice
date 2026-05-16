"""Small rendering helpers shared by UI and overlay modules.

`settings.py` is intentionally declarative (constants only); anything that
needs `pygame` at import time lives here instead so settings stay safe to
import from any context (including tests and tools).
"""

import pygame


def color_with_alpha(color, alpha: int) -> pygame.Color:
    """Return a `pygame.Color` with an explicit alpha channel.

    Accepts any input `pygame.Color()` accepts: a named color string, a
    `(r, g, b)` tuple, a `(r, g, b, a)` tuple, or another `pygame.Color`.
    Mimic Dice stores colors as `(r, g, b)` tuples in `ColorSettings`, but
    the helper is intentionally permissive so it remains compatible with
    code paths that pass strings in.

    Args:
        color: Source color in any `pygame.Color()`-accepted form.
        alpha: Alpha channel value in the 0-255 range. Values outside the
            range are silently clamped by `pygame.Color`.

    Returns:
        A new `pygame.Color` with the requested transparency. The input is
        not mutated.
    """
    rgba = pygame.Color(color)
    rgba.a = alpha
    return rgba
