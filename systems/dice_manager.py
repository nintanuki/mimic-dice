import pygame
from systems.die import Die
from utils.spritesheet import SpriteSheet
from settings import AssetPaths, ScreenSettings

class DiceManager:
    """Manages a collection of Die objects and their shared assets."""

    def __init__(self):
        self.dice: list[Die] = []
        self.sprites = self._load_dice_sprites()
        
        # Initialize 3 dice for the start (standard for Zombie Dice)
        self.setup_dice(3)

    def _load_dice_sprites(self) -> list[pygame.Surface]:
        """Slices the first row of the sprite sheet for the 6 faces."""
        sheet = SpriteSheet(AssetPaths.DICE_SHEET)
        return [
            sheet.get_image(i * AssetPaths.DIE_SIZE, 0, AssetPaths.DIE_SIZE, AssetPaths.DIE_SIZE)
            for i in range(6)
        ]

    def setup_dice(self, count: int):
        """Creates die instances spaced across the screen."""
        self.dice = []
        spacing = ScreenSettings.WIDTH // (count + 1)
        for i in range(count):
            # Target X is spaced out, Target Y is the table center
            tx = spacing * (i + 1)
            ty = ScreenSettings.TABLE_CENTER_Y
            self.dice.append(Die(tx, ty, self.sprites))

    def roll_all(self):
        """Triggers the roll animation for all active dice."""
        for die in self.dice:
            die.roll()

    def update(self, dt: float):
        """Updates animation logic for all dice."""
        for die in self.dice:
            die.update(dt)

    def draw(self, surface: pygame.Surface):
        """Renders all dice to the screen."""
        for die in self.dice:
            die.draw(surface)