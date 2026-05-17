"""Dice roller: orchestrates a roll of multiple dice in a tray.

`DiceRoller` is the only entry point GameManager uses to interact with the
dice subsystem. It owns:
  * one `DiceTray` (the bounded play area),
  * the shared sprite frames (loaded once, shared by every die),
  * a list of `AnimatedDie` instances that *grows* over the course of a turn.

Per frame, GameManager calls `update(dt)` then `draw(surface)`. To trigger
a new roll driven by the rules engine, GameManager calls
`roll_with_results(colors, outcomes)`, which assigns each die its
pre-decided color *and* Outcome and then throws it. Carrying both keeps
the displayed art (per-color chest / mimic / treasure) consistent with
both the die's color and the outcome the engine resolved.

Dice persistence within a turn
------------------------------
A turn starts with an empty dice list. Each `roll_with_results` call:
  1. Re-throws every die currently sitting on the felt as EMPTY (those
     are the held-overs; they keep their existing color and get fresh
     outcomes from the leading entries of `colors` and `outcomes`).
  2. Appends new `AnimatedDie` instances for any remaining (color, outcome)
     pairs — these are the fresh draws from the bag.
Dice that settled as MIMIC or TREASURE on an earlier roll never move
again until `clear_for_new_turn()` is called (bank or bust). The visual
result mirrors physical Zombie Dice: your brains/shotguns pile grows on
the table; your footsteps are the only thing you re-roll.

Sprite sources
--------------
Mid-tumble frames come from the shared white tumble row of the original
six-sided sheet, so every color looks the same in the air. The settled
art comes from twelve standalone PNGs — three outcomes × three colors —
loaded from the paths listed in `AssetPaths.SETTLED_SPRITES`.
"""

import pygame

from settings import AssetPaths, DiceSettings
from systems.animated_die import AnimatedDie
from systems.dice_tray import DiceTray
from systems.outcomes import DieColor, Outcome
from utils.spritesheet import SpriteSheet


class DiceRoller:
    """Owns the tray, shared sprite frames, and every `AnimatedDie` in play."""

    def __init__(self, window_size: tuple[int, int]):
        """Load sprites and build the tray. The dice list starts empty.

        Args:
            window_size: Initial (width, height) of the display surface.
        """
        # Tumble row stays on the original six-sided sheet because every
        # color shares the same in-air silhouette; that keeps memory low
        # and lets the per-color art read clearly only at settle time.
        sheet = SpriteSheet(AssetPaths.DICE_SHEET)
        self.tumble_sprites = self._load_sheet_row(
            sheet, AssetPaths.DIE_TUMBLE_ROW, AssetPaths.DIE_TUMBLE_FRAME_COUNT
        )

        # One settled sprite per (color, outcome) loaded from standalone
        # PNGs. The map's keys are the actual enums; AssetPaths uses string
        # tuples (color.value, outcome.value) so the asset table stays
        # readable without importing the enums into settings.
        self.settled_sprites: dict[tuple[DieColor, Outcome], pygame.Surface] = {
            (DieColor(color_value), Outcome(outcome_value)):
                self._load_settled_sprite(path)
            for (color_value, outcome_value), path
            in AssetPaths.SETTLED_SPRITES.items()
        }

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

    @staticmethod
    def _load_settled_sprite(path: str) -> pygame.Surface:
        """Load one standalone settled sprite from `path`, scaled to match dice."""
        raw = pygame.image.load(path).convert_alpha()
        width, height = raw.get_size()
        scale = DiceSettings.SCALE
        if scale == 1:
            return raw
        return pygame.transform.scale(raw, (width * scale, height * scale))

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

    def roll_with_results(
        self,
        colors: list[DieColor],
        outcomes: list[Outcome],
    ) -> None:
        """Re-throw any held-over EMPTY dice and append fresh draws.

        The rules engine returns its `RollResult.colors` / `outcomes` ordered
        held-over first, fresh draws after; we mirror that here. Existing
        MIMIC and TREASURE dice on the felt are left alone — they are the
        player's set-aside pile and only clear at turn end.

        Args:
            colors:   Per-die `DieColor`, held-overs first. The held-over
                      entries match the colors of the dice already on the
                      felt (they keep their identity across re-rolls).
            outcomes: Matching Outcome per die, parallel to `colors`.
        """
        held_over_dice = self._held_over_dice()
        held_count = len(held_over_dice)

        # Re-throw the held-overs with the leading slice of the new results.
        # Color stays unchanged (a held-over die keeps its identity), but we
        # re-assign it from the engine anyway so the two sides agree.
        for die, color, outcome in zip(
            held_over_dice, colors[:held_count], outcomes[:held_count]
        ):
            die.pending_color = color
            die.pending_outcome = outcome
            die.roll(self.tray.rect)

        # Fresh draws append as brand-new dice so the felt visually grows.
        for color, outcome in zip(colors[held_count:], outcomes[held_count:]):
            die = AnimatedDie(self.settled_sprites, self.tumble_sprites)
            die.pending_color = color
            die.pending_outcome = outcome
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
