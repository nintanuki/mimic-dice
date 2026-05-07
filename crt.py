"""CRT post-processing overlay.

Blits a TV-frame image with a per-frame random alpha (creates a flicker)
and overlays horizontal scanlines on top of the rendered scene. The CRT
overlay is the last thing drawn each frame.
"""

import random

import pygame

from settings import AssetPaths, ColorSettings, ScreenSettings


class CRT:
    """CRT-style flicker + scanline overlay drawn on top of the screen."""

    def __init__(self, screen):
        """Load and pre-scale the TV frame to the current resolution.

        Args:
            screen: Display surface to render the CRT effect onto.
        """
        self.screen = screen
        self.base_tv = pygame.image.load(AssetPaths.TV).convert_alpha()
        self.base_tv = pygame.transform.scale(
            self.base_tv, ScreenSettings.RESOLUTION
        )

    def create_crt_lines(self, overlay: pygame.Surface) -> None:
        """Draw evenly-spaced horizontal scanlines onto `overlay`.

        Args:
            overlay: Surface that receives the scanline strokes.
        """
        spacing = ScreenSettings.CRT_SCANLINE_HEIGHT
        line_width = ScreenSettings.CRT_SCANLINE_LINE_WIDTH
        line_color = ColorSettings.OVERLAY_BACKGROUND
        for line_y in range(0, ScreenSettings.HEIGHT, spacing):
            pygame.draw.line(
                overlay,
                line_color,
                (0, line_y),
                (ScreenSettings.WIDTH, line_y),
                line_width,
            )

    def draw(self) -> None:
        """Composite the flicker layer and scanlines onto the screen."""
        # Copy per frame so the overlay does not accumulate between frames.
        overlay = self.base_tv.copy()
        overlay.set_alpha(random.randint(*ScreenSettings.CRT_ALPHA_RANGE))
        self.create_crt_lines(overlay)
        self.screen.blit(overlay, (0, 0))
