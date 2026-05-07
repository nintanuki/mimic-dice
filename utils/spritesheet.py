import pygame

class SpriteSheet:
    """Utility for cropping images from a single sheet."""

    def __init__(self, filename: str):
        """Load the sheet and prepare for sub-surface extraction."""
        self.sheet = pygame.image.load(filename).convert_alpha()

    def get_image(self, x: int, y: int, width: int, height: int) -> pygame.Surface:
        """Extract a specific sprite from the sheet."""
        image = pygame.Surface((width, height), pygame.SRCALPHA)
        image.blit(self.sheet, (0, 0), (x, y, width, height))
        return image