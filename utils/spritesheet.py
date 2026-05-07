"""Generic sprite-sheet slicer.

`SpriteSheet` knows how to load a single image and cut sub-rectangles out of
it. It is intentionally agnostic of what the sheet contains - callers pass
explicit coordinates and an optional scale factor so this class stays
reusable across different sheets.
"""

import pygame


class SpriteSheet:
    """Load an image once and extract scaled sub-surfaces on demand."""

    def __init__(self, filename: str):
        """Load the sheet from disk.

        Args:
            filename: Path to the image file containing the sprite sheet.
        """
        self.sheet = pygame.image.load(filename).convert_alpha()

    def get_image(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        scale: int = 1,
    ) -> pygame.Surface:
        """Return one tile from the sheet, optionally scaled up.

        Args:
            x: Left edge of the source tile in sheet pixels.
            y: Top edge of the source tile in sheet pixels.
            width: Source tile width in pixels.
            height: Source tile height in pixels.
            scale: Integer multiplier applied to width and height. Use 1 to
                keep the sheet's native size.

        Returns:
            A new `pygame.Surface` with per-pixel alpha containing the tile.
        """
        tile = pygame.Surface((width, height), pygame.SRCALPHA)
        tile.blit(self.sheet, (0, 0), (x, y, width, height))
        if scale == 1:
            return tile
        return pygame.transform.scale(tile, (width * scale, height * scale))
