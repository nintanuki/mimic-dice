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
the displayed art consistent with both the die's color (which tier of
face PNG to draw from) and the outcome the engine resolved (which of
the three face PNGs in that color: MIMIC, EMPTY, or TREASURE).

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
Tumble frames come from a single-row sheet
(`AssetPaths.DIE_TUMBLE_SHEET`) shared across every color so every die in
flight reads identically. Settled faces are one PNG per (color, outcome)
pair listed in `AssetPaths.DIE_FACE_SPRITES`: green/yellow/red bodies
each with a MIMIC, EMPTY, and TREASURE face. The color tells the player
how risky the die was; the face tells them what happened on this roll.
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
        # Tumble row is shared by every color — every die in flight reads
        # the same in-air silhouette, which keeps memory low and means the
        # color/outcome reveal lands at settle time.
        tumble_sheet = SpriteSheet(AssetPaths.DIE_TUMBLE_SHEET)
        self.tumble_sprites = self._load_sheet_row(
            tumble_sheet, 0, AssetPaths.DIE_TUMBLE_FRAME_COUNT
        )

        # face_sprites: (DieColor, Outcome) -> Surface. The settled art is
        # one PNG per (color, outcome) pair; the renderer simply looks up
        # the die's resolved (color, outcome) at settle time. No numbered
        # pip step anymore — the face *is* the outcome.
        self.face_sprites: dict[tuple[DieColor, Outcome], pygame.Surface] = {}
        for (color_value, outcome_value), path in AssetPaths.DIE_FACE_SPRITES.items():
            color = DieColor(color_value)
            outcome = Outcome(outcome_value)
            self.face_sprites[(color, outcome)] = self._load_face_sprite(path)

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
    def _load_face_sprite(path: str) -> pygame.Surface:
        """Load one settled-face PNG and scale it up to match the tumble row.

        Args:
            path: Path to a 16x16 (color, outcome) face PNG.

        Returns:
            The image scaled by `DiceSettings.SCALE` so it lines up
            pixel-for-pixel with the tumble frames on the felt.
        """
        raw = pygame.image.load(path).convert_alpha()
        scale = DiceSettings.SCALE
        if scale == 1:
            return raw
        width, height = raw.get_size()
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
            die = AnimatedDie(self.face_sprites, self.tumble_sprites)
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
