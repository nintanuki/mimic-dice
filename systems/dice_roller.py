"""Dice roller: orchestrates a roll of multiple dice in a tray.

`DiceRoller` is the only entry point GameManager uses to interact with the
dice subsystem. It owns:
  * one `DiceTray` (the bounded play area),
  * the shared face/tumble sprite frames (loaded once, shared by every die),
  * a list of `AnimatedDie` instances (`DiceSettings.COUNT` of them).

Per frame, GameManager calls `update(dt)` then `draw(surface)`. To trigger
a new roll, GameManager calls `roll_all()`.
"""

import pygame

from settings import AssetPaths, DiceSettings
from systems.animated_die import AnimatedDie
from systems.dice_tray import DiceTray
from utils.spritesheet import SpriteSheet


class DiceRoller:
    """Owns the tray, shared sprite frames, and every `AnimatedDie`."""

    def __init__(self, window_size: tuple[int, int]):
        """Load sprites, build the tray, and create `DiceSettings.COUNT` dice.

        Args:
            window_size: Initial (width, height) of the display surface.
        """
        sheet = SpriteSheet(AssetPaths.DICE_SHEET)
        self.face_sprites = self._load_sheet_row(
            sheet, AssetPaths.DIE_FACE_ROW, AssetPaths.DIE_FACE_COUNT
        )
        self.tumble_sprites = self._load_sheet_row(
            sheet, AssetPaths.DIE_TUMBLE_ROW, AssetPaths.DIE_TUMBLE_FRAME_COUNT
        )

        self.tray = DiceTray(window_size)
        self.dice: list[AnimatedDie] = [
            AnimatedDie(self.face_sprites, self.tumble_sprites)
            for _ in range(DiceSettings.COUNT)
        ]

    # -------------------------
    # SETUP
    # -------------------------

    @staticmethod
    def _load_sheet_row(
        sheet: SpriteSheet, row_index: int, frame_count: int
    ) -> list[pygame.Surface]:
        """Slice `frame_count` consecutive tiles from a row of the sheet."""
        tile_size = AssetPaths.DIE_TILE_SIZE
        scale = DiceSettings.SCALE
        return [
            sheet.get_image(
                column_index * tile_size,
                row_index * tile_size,
                tile_size,
                tile_size,
                scale=scale,
            )
            for column_index in range(frame_count)
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
        """Render the tray (felt + border) and every die on top of it."""
        self.tray.draw(surface)
        for die in self.dice:
            die.draw(surface)
