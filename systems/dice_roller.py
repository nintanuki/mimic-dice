"""Dice roller: orchestrates a roll of multiple dice in a tray.

`DiceRoller` is the only entry point GameManager uses to interact with the
dice subsystem. It owns:
  * one `DiceTray` (the bounded play area),
  * the shared sprite frames (loaded once, shared by every die),
  * a list of `AnimatedDie` instances (`DiceSettings.COUNT` of them).

Per frame, GameManager calls `update(dt)` then `draw(surface)`. To trigger
a new roll driven by the rules engine, GameManager calls
`roll_with_results(faces, outcomes)`, which assigns each die its
pre-decided face value *and* Outcome and then throws it. Carrying both
keeps the displayed pip count consistent with the outcome color.

Sprite rows
-----------
The die sheet has separate rows for each outcome color:
  * Row `DIE_MIMIC_ROW`   (red)  — MIMIC outcome.
  * Row `DIE_EMPTY_ROW`   (grey) — EMPTY outcome.
  * Row `DIE_TREASURE_ROW`(green)— TREASURE outcome.
All three rows are loaded at construction and shared across every die so
adding more dice is essentially free in terms of memory.
"""

import pygame

from settings import AssetPaths, DiceSettings
from systems.animated_die import AnimatedDie
from systems.dice_tray import DiceTray
from systems.outcomes import Outcome
from utils.spritesheet import SpriteSheet


class DiceRoller:
    """Owns the tray, shared sprite frames, and every `AnimatedDie`."""

    def __init__(self, window_size: tuple[int, int]):
        """Load sprites, build the tray, and create `DiceSettings.COUNT` dice.

        Args:
            window_size: Initial (width, height) of the display surface.
        """
        sheet = SpriteSheet(AssetPaths.DICE_SHEET)

        # Load the three outcome-colored face rows and the tumble row.
        self.outcome_sprites: dict[Outcome, list[pygame.Surface]] = {
            Outcome.MIMIC:    self._load_sheet_row(sheet, AssetPaths.DIE_MIMIC_ROW,    AssetPaths.DIE_FACE_COUNT),
            Outcome.EMPTY:    self._load_sheet_row(sheet, AssetPaths.DIE_EMPTY_ROW,    AssetPaths.DIE_FACE_COUNT),
            Outcome.TREASURE: self._load_sheet_row(sheet, AssetPaths.DIE_TREASURE_ROW, AssetPaths.DIE_FACE_COUNT),
        }
        self.tumble_sprites = self._load_sheet_row(
            sheet, AssetPaths.DIE_TUMBLE_ROW, AssetPaths.DIE_TUMBLE_FRAME_COUNT
        )

        self.tray = DiceTray(window_size)
        self.dice: list[AnimatedDie] = [
            AnimatedDie(self.outcome_sprites, self.tumble_sprites)
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
    # QUERIES
    # -------------------------

    @property
    def all_settled(self) -> bool:
        """True when every die has come to rest (none still rolling)."""
        return all(not die.is_rolling for die in self.dice)

    # -------------------------
    # ACTIONS
    # -------------------------

    def roll_with_results(self, faces: list[int], outcomes: list[Outcome]) -> None:
        """Assign a pre-decided face and Outcome to each die, then throw them all.

        The rules engine calls this so the visual result always matches the
        logical result: each die settles onto the face color matching its
        outcome *and* the pip count matching its face value.

        Only the first `min(len(faces), len(outcomes))` dice are thrown;
        any extra dice (from a previous roll's held-overs that aren't in
        play this roll) remain as-is. Callers should pass exactly
        `DiceSettings.COUNT` faces and outcomes to throw all dice.

        Args:
            faces:    Pre-decided 1–6 face value per die, ordered to match
                      `self.dice` (index 0 = die 0, etc.).
            outcomes: Matching Outcome per die, parallel to `faces`.
        """
        for die, face, outcome in zip(self.dice, faces, outcomes):
            die.pending_outcome = outcome
            die.pending_face = face
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
