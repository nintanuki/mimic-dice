import pygame

from systems.die import Die
from systems.dice_tray import DiceTray
from utils.spritesheet import SpriteSheet
from settings import AssetPaths, DiceSettings


class DiceManager:
    """Owns the dice tray, dice instances, and shared sprite frames."""

    def __init__(self, window_size: tuple[int, int]):
        """Load sprites, build the tray, and create `DiceSettings.COUNT` dice.

        Args:
            window_size: Initial (width, height) of the display surface.
        """
        sheet = SpriteSheet(AssetPaths.DICE_SHEET)
        self.face_sprites = self._load_row(sheet, AssetPaths.DICE_FACE_ROW, 6)
        self.tumble_sprites = self._load_row(
            sheet, AssetPaths.DICE_TUMBLE_ROW, AssetPaths.DICE_TUMBLE_FRAME_COUNT
        )

        self.tray = DiceTray(window_size)
        self.dice: list[Die] = [
            Die(self.face_sprites, self.tumble_sprites)
            for _ in range(DiceSettings.COUNT)
        ]

    # -------------------------
    # SETUP
    # -------------------------

    @staticmethod
    def _load_row(sheet: SpriteSheet, row: int, count: int) -> list[pygame.Surface]:
        """Slice `count` consecutive tiles from `row` of the sprite sheet."""
        size = AssetPaths.DIE_SIZE
        return [
            sheet.get_image(i * size, row * size, size, size) for i in range(count)
        ]

    def resize(self, window_size: tuple[int, int]) -> None:
        """Resize the tray when the window changes size."""
        self.tray.resize(window_size)

    # -------------------------
    # ACTIONS
    # -------------------------

    def roll_all(self) -> None:
        """Throw every die from the configured tray corner."""
        for die in self.dice:
            die.roll(self.tray.rect)

    # -------------------------
    # UPDATE / DRAW
    # -------------------------

    def update(self, dt: float) -> None:
        """Advance physics for every die against the tray's inner bounds."""
        bounds = self.tray.inner_rect(DiceSettings.TRAY_INNER_MARGIN)
        for die in self.dice:
            die.update(dt, bounds)

    def draw(self, surface: pygame.Surface) -> None:
        """Render the tray border and every die on top of it."""
        self.tray.draw(surface)
        for die in self.dice:
            die.draw(surface)
