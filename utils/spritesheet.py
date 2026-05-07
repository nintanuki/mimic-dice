import pygame
from settings import ScreenSettings

class SpriteSheet:
    """Utility for cropping images from a single sheet."""

    def __init__(self, filename: str):
        """
        Load the sheet and prepare for sub-surface extraction.
        
        Args:
            filename: Path to the image file containing the sprite sheet.
        """
        self.sheet = pygame.image.load(filename).convert_alpha()

    def get_image(self, x: int, y: int, width: int, height: int) -> pygame.Surface:
        """
        Extract a specific sprite from the sheet.

        Args:
            x: The x-coordinate of the top-left corner of the sprite.
            y: The y-coordinate of the top-left corner of the sprite.
            width: The width of the sprite.
            height: The height of the sprite.

        Returns:
            A pygame.Surface object containing the extracted sprite.
        """
        image = pygame.Surface((width, height), pygame.SRCALPHA)
        image.blit(self.sheet, (0, 0), (x, y, width, height))
        
        # Can't we just do this in settings.py?
        new_size = (width * ScreenSettings.DICE_SCALE, height * ScreenSettings.DICE_SCALE)
        return pygame.transform.scale(image, new_size)