"""Animated die: one die's physics body, frame animation, and sprite.

An `AnimatedDie` is owned by a `DiceRoller` and constrained by a `DiceTray`.
It has two visual states:
  * Rolling - cycles through the shared white tumble frames; the frame rate
    scales with the die's speed so fast dice visibly spin faster.
  * Settled - shows the single sprite keyed by `(pending_color, pending_outcome)`,
    which renders the per-color chest / mimic / treasure art.

Physics notes:
  * Velocity uses pixels/second, integrated each frame by `dt`.
  * Drag is exponential: each second `vel` is multiplied by exp(-LINEAR_DRAG),
    which is frame-rate independent (unlike a flat per-frame multiplier).
  * Wall reflection in `_bounce_against_walls` uses `abs(vel)` rather than
    plain negation. This guarantees a die spawned just outside the tray is
    pulled back in even if its velocity already pointed away from the wall.

Color- and outcome-driven settle sprite
---------------------------------------
Before calling `roll()`, the rules engine sets `die.pending_color` and
`die.pending_outcome`. When the die settles, `_settle()` looks up the
matching settled sprite in `settled_sprites[(color, outcome)]` and renders
it. The tumble row stays shared (all colors mid-air look the same) — this
keeps memory low and emphasises the outcome-reveal at settle time.
"""

import math
import random
from typing import Optional

import pygame

from settings import DiceSettings
from systems.outcomes import DieColor, Outcome


class AnimatedDie:
    """A single die animated by simple 2D physics inside a `DiceTray`."""

    def __init__(
        self,
        settled_sprites: dict[tuple[DieColor, Outcome], pygame.Surface],
        tumble_sprites: list[pygame.Surface],
    ):
        """Store the sprite frames; the die stays idle until `roll()` runs.

        Args:
            settled_sprites: Map from (color, outcome) to the single settled
                sprite for that combination. At settle time the die picks
                the sprite keyed by `(pending_color, pending_outcome)`.
            tumble_sprites:  Mid-tumble frames cycled while the die moves.
                Shared across every color (one white tumble row).
        """
        self.settled_sprites = settled_sprites
        self.tumble_sprites = tumble_sprites

        # Use any sprite to derive the die's rendered size; every sprite is
        # the same source tile size scaled by `DiceSettings.SCALE`.
        first_sprite = next(iter(settled_sprites.values()))
        self.size = first_sprite.get_width()

        # `pending_color` + `pending_outcome` are set by DiceRoller (from the
        # rules engine) before each roll. `_settle()` reads both to pick the
        # right settled sprite.
        self.pending_color: Optional[DieColor] = None
        self.pending_outcome: Optional[Outcome] = None
        # The sprite shown once the die has settled.
        self._settled_sprite: pygame.Surface = first_sprite

        self.position = pygame.Vector2(0, 0)
        self.velocity = pygame.Vector2(0, 0)
        self.is_rolling = False
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
        """Stop the die and pick the settled sprite from (color, outcome).

        If either `pending_color` or `pending_outcome` is missing, the die
        falls back to the first sprite in the map so a misuse renders
        something visible rather than crashing.
        """
        self.is_rolling = False
        self.velocity.update(0, 0)
        key = (self.pending_color, self.pending_outcome)
        if key in self.settled_sprites:
            self._settled_sprite = self.settled_sprites[key]
        else:
            self._settled_sprite = next(iter(self.settled_sprites.values()))

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
            else self._settled_sprite
        )
        render_position = (
            int(self.position.x - self.size / 2),
            int(self.position.y - self.size / 2),
        )
        surface.blit(sprite, render_position)
