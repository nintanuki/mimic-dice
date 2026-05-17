"""Dice roller: orchestrates a roll of multiple dice in a tray.

`DiceRoller` is the only entry point GameManager uses to interact with the
dice subsystem. It owns:
  * one `DiceTray` (the bounded play area),
  * the shared sprite frames (loaded once, shared by every die),
  * a list of `AnimatedDie` instances that *grows* over the course of a turn.

Per frame, GameManager calls `update(dt)` then `draw(surface)`. To trigger
a new roll driven by the rules engine, GameManager calls
`roll_with_results(faces, outcomes)`, which assigns each die its
pre-decided face value *and* Outcome and then throws it. Carrying both
keeps the displayed pip count consistent with the outcome color.

Dice persistence within a turn
------------------------------
A turn starts with an empty dice list. Each `roll_with_results` call:
  1. Re-throws every die currently sitting on the felt as EMPTY (those
     are the held-overs; they get fresh faces / outcomes from the
     leading entries of `faces` and `outcomes`).
  2. Appends new `AnimatedDie` instances for any remaining (face, outcome)
     pairs — these are the fresh draws from the bag.
Dice that settled as MIMIC or TREASURE on an earlier roll never move
again until `clear_for_new_turn()` is called (bank or bust). The visual
result mirrors physical Zombie Dice: your brains/shotguns pile grows on
the table; your footsteps are the only thing you re-roll.

Sprite rows
-----------
The die sheet has separate rows for each outcome color:
  * Row `DIE_MIMIC_ROW`   (red)    — MIMIC outcome.
  * Row `DIE_EMPTY_ROW`   (white)  — EMPTY outcome.
  * Row `DIE_TREASURE_ROW`(yellow) — TREASURE outcome.
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
    """Owns the tray, shared sprite frames, and every `AnimatedDie` in play."""

    def __init__(self, window_size: tuple[int, int]):
        """Load sprites and build the tray. The dice list starts empty.

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
        # Grows during a turn as held-over EMPTY dice re-roll and fresh
        # draws append; reset on `clear_for_new_turn()`.
        self.dice: list[AnimatedDie] = []

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

    def _held_over_dice(self) -> list[AnimatedDie]:
        """Return the settled EMPTY dice — the ones a new roll will re-throw.

        Dice that are still rolling are skipped (a guard call to
        `roll_with_results` during a tumble would be a logic error elsewhere,
        but skipping keeps this method total).
        """
        return [
            die for die in self.dice
            if not die.is_rolling and die.pending_outcome == Outcome.EMPTY
        ]

    # -------------------------
    # ACTIONS
    # -------------------------

    def roll_with_results(self, faces: list[int], outcomes: list[Outcome]) -> None:
        """Re-throw any held-over EMPTY dice and append fresh draws.

        The rules engine returns its `RollResult.faces` / `outcomes` ordered
        held-over first, fresh draws after; we mirror that here. Existing
        MIMIC and TREASURE dice on the felt are left alone — they are the
        player's set-aside pile and only clear at turn end.

        Args:
            faces:    Pre-decided 1–6 face value per die, held-overs first.
            outcomes: Matching Outcome per die, parallel to `faces`.
        """
        held_over_dice = self._held_over_dice()
        held_count = len(held_over_dice)

        # Re-throw the held-overs with the leading slice of the new results.
        for die, face, outcome in zip(
            held_over_dice, faces[:held_count], outcomes[:held_count]
        ):
            die.pending_outcome = outcome
            die.pending_face = face
            die.roll(self.tray.rect)

        # Fresh draws append as brand-new dice so the felt visually grows.
        for face, outcome in zip(faces[held_count:], outcomes[held_count:]):
            die = AnimatedDie(self.outcome_sprites, self.tumble_sprites)
            die.pending_outcome = outcome
            die.pending_face = face
            die.roll(self.tray.rect)
            self.dice.append(die)

    def clear_for_new_turn(self) -> None:
        """Drop every die on the felt. Called on bank or bust."""
        self.dice = []

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
