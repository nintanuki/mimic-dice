"""Animated die: one die's physics body, frame animation, and sprite.

An `AnimatedDie` is owned by a `DiceRoller` and constrained by a `DiceTray`.
It has two visual states:
  * Rolling - cycles through tumble frames; speed-driven frame rate.
  * Settled - shows a face frame chosen from the sprite row that matches the
    die's pre-decided `pending_outcome`.

Physics notes:
  * Velocity uses pixels/second, integrated each frame by `dt`.
  * Drag is exponential: each second `vel` is multiplied by exp(-LINEAR_DRAG),
    which is frame-rate independent (unlike a flat per-frame multiplier).
  * Wall reflection in `_bounce_against_walls` uses `abs(vel)` rather than
    plain negation. This guarantees a die spawned just outside the tray is
    pulled back in even if its velocity already pointed away from the wall.

Outcome-driven sprite rows
--------------------------
Before calling `roll()`, the rules engine sets `die.pending_outcome` to the
pre-decided `Outcome` for that die *and* `die.pending_face` to the 1–6 face
value that produced that outcome under the Phase 0 threshold map. When the
die settles, `_settle()` picks the sprite from the outcome's row at the
pending face's column, so the pips you read on the die always match the
face value the engine rolled (face 1 → MIMIC, face 6 → TREASURE, etc.).
This keeps the animation system decoupled from the rules engine: the
engine decides what happened; the die only knows how to show it.
"""

import math
import random
from typing import Optional

import pygame

from settings import DiceSettings
from systems.outcomes import Outcome


class AnimatedDie:
    """A single die animated by simple 2D physics inside a `DiceTray`."""

    def __init__(
        self,
        outcome_sprites: dict[Outcome, list[pygame.Surface]],
        tumble_sprites: list[pygame.Surface],
    ):
        """Store the sprite frames; the die stays idle until `roll()` runs.

        Args:
            outcome_sprites: Mapping from each Outcome to its list of settled-
                face frames.  At settle time, the die picks the sprite at
                `pending_face - 1` from the list keyed by `pending_outcome`,
                so the displayed pip count matches the engine's rolled face.
            tumble_sprites: Mid-tumble frames cycled while the die moves.
        """
        self.outcome_sprites = outcome_sprites
        self.tumble_sprites = tumble_sprites

        # Use any sprite list to derive the die's rendered size.
        first_sprites = next(iter(outcome_sprites.values()))
        self.size = first_sprites[0].get_width()

        # pending_outcome + pending_face are set by DiceRoller (from the rules
        # engine) before each roll. _settle() reads them to pick the right
        # sprite row (outcome) and column (face value).
        self.pending_outcome: Optional[Outcome] = None
        self.pending_face: Optional[int] = None
        # The sprite list used for the current settled state.
        self._settled_sprites: list[pygame.Surface] = first_sprites

        self.position = pygame.Vector2(0, 0)
        self.velocity = pygame.Vector2(0, 0)
        self.is_rolling = False
        self.face_index = 0
        self.tumble_index = 0
        self.tumble_timer = 0.0

    # -------------------------
    # ROLL / SPAWN
    # -------------------------

    def roll(self, tray_rect: pygame.Rect) -> None:
        """Launch the die from the configured tray corner with random spread.

        Args:
            tray_rect: The current tray bounds, in window pixels.
        """
        self.position = pygame.Vector2(self._spawn_point(tray_rect))
        angle_deg = DiceSettings.THROW_ANGLE_DEG + random.uniform(
            -DiceSettings.THROW_ANGLE_SPREAD_DEG,
            DiceSettings.THROW_ANGLE_SPREAD_DEG,
        )
        speed = random.uniform(
            DiceSettings.THROW_SPEED_MIN, DiceSettings.THROW_SPEED_MAX
        )
        angle_rad = math.radians(angle_deg)
        self.velocity = pygame.Vector2(
            math.cos(angle_rad) * speed, math.sin(angle_rad) * speed
        )
        self.is_rolling = True
        self.tumble_timer = 0.0
        self.tumble_index = random.randrange(len(self.tumble_sprites))

    def _spawn_point(self, tray_rect: pygame.Rect) -> tuple[float, float]:
        """Return a spawn position just outside the configured tray corner."""
        offset = DiceSettings.THROW_SPAWN_OFFSET
        corner_positions = {
            "bottom_left":  (tray_rect.left - offset,  tray_rect.bottom + offset),
            "bottom_right": (tray_rect.right + offset, tray_rect.bottom + offset),
            "top_left":     (tray_rect.left - offset,  tray_rect.top - offset),
            "top_right":    (tray_rect.right + offset, tray_rect.top - offset),
        }
        return corner_positions[DiceSettings.THROW_ORIGIN]

    # -------------------------
    # PHYSICS
    # -------------------------

    def _apply_drag(self, dt: float) -> None:
        """Exponentially decay velocity to mimic table friction."""
        drag_decay = math.exp(-DiceSettings.LINEAR_DRAG * dt)
        self.velocity *= drag_decay

    def _bounce_against_walls(self, bounds: pygame.Rect) -> None:
        """Clamp position into `bounds` and reflect velocity on each wall hit."""
        half_size = self.size / 2
        min_x = bounds.left + half_size
        max_x = bounds.right - half_size
        min_y = bounds.top + half_size
        max_y = bounds.bottom - half_size

        if self.position.x < min_x:
            self.position.x = min_x
            self.velocity.x = abs(self.velocity.x) * DiceSettings.RESTITUTION
        elif self.position.x > max_x:
            self.position.x = max_x
            self.velocity.x = -abs(self.velocity.x) * DiceSettings.RESTITUTION

        if self.position.y < min_y:
            self.position.y = min_y
            self.velocity.y = abs(self.velocity.y) * DiceSettings.RESTITUTION
        elif self.position.y > max_y:
            self.position.y = max_y
            self.velocity.y = -abs(self.velocity.y) * DiceSettings.RESTITUTION

    def _advance_tumble(self, dt: float) -> None:
        """Cycle the tumble frame at a rate proportional to current speed."""
        speed = self.velocity.length()
        peak_speed = DiceSettings.THROW_SPEED_MAX
        # Linear interpolation: 0 at standstill, 1 at peak throw speed.
        speed_ratio = 0.0 if peak_speed <= 0 else min(1.0, speed / peak_speed)
        fps = (
            DiceSettings.TUMBLE_FPS_MIN
            + (DiceSettings.TUMBLE_FPS_MAX - DiceSettings.TUMBLE_FPS_MIN)
            * speed_ratio
        )
        self.tumble_timer += dt * fps
        if self.tumble_timer >= 1.0:
            steps = int(self.tumble_timer)
            self.tumble_timer -= steps
            self.tumble_index = (
                (self.tumble_index + steps) % len(self.tumble_sprites)
            )

    def _settle(self) -> None:
        """Stop the die and pick a final face frame from the outcome's sprite row.

        If `pending_outcome` is set and present in `outcome_sprites`, that
        outcome's sprite list is used; otherwise the first available list
        acts as the fallback so the die always renders something sensible.
        Within the chosen row, `pending_face` (1–6) picks the column so the
        displayed pips always match the engine's rolled face. If
        `pending_face` is unset we fall back to a random column.
        """
        self.is_rolling = False
        self.velocity.update(0, 0)
        if self.pending_outcome is not None and self.pending_outcome in self.outcome_sprites:
            self._settled_sprites = self.outcome_sprites[self.pending_outcome]
        else:
            self._settled_sprites = next(iter(self.outcome_sprites.values()))
        if self.pending_face is not None and 1 <= self.pending_face <= len(self._settled_sprites):
            self.face_index = self.pending_face - 1
        else:
            self.face_index = random.randrange(len(self._settled_sprites))

    # -------------------------
    # UPDATE / DRAW
    # -------------------------

    def update(self, dt: float, bounds: pygame.Rect) -> None:
        """Advance physics, bounce off tray walls, and animate frames.

        Args:
            dt: Seconds since last frame.
            bounds: Current physics bounds (already inset from tray border).
        """
        if not self.is_rolling:
            return

        self._apply_drag(dt)
        self.position += self.velocity * dt
        self._bounce_against_walls(bounds)
        self._advance_tumble(dt)

        if self.velocity.length() < DiceSettings.SETTLE_SPEED:
            self._settle()

    def draw(self, surface: pygame.Surface) -> None:
        """Render the current frame centered on `position`."""
        sprite = (
            self.tumble_sprites[self.tumble_index]
            if self.is_rolling
            else self._settled_sprites[self.face_index]
        )
        render_position = (
            int(self.position.x - self.size / 2),
            int(self.position.y - self.size / 2),
        )
        surface.blit(sprite, render_position)
