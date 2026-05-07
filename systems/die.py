import math
import random
import pygame

from settings import DiceSettings


class Die:
    """A single die animated by simple 2D physics inside a `DiceTray`."""

    def __init__(
        self,
        face_sprites: list[pygame.Surface],
        tumble_sprites: list[pygame.Surface],
    ):
        """Store the sprite frames; spawn idle until `roll()` is called.

        Args:
            face_sprites: 6 settled-face frames (indexed 0..5 = faces 1..6).
            tumble_sprites: Mid-tumble frames cycled while moving.
        """
        self.face_sprites = face_sprites
        self.tumble_sprites = tumble_sprites
        self.size = face_sprites[0].get_width()

        self.pos = pygame.Vector2(0, 0)
        self.vel = pygame.Vector2(0, 0)
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
            tray_rect: The current tray bounds (window pixels).
        """
        self.pos = pygame.Vector2(self._spawn_point(tray_rect))
        angle_deg = DiceSettings.THROW_ANGLE_DEG + random.uniform(
            -DiceSettings.THROW_ANGLE_SPREAD_DEG,
            DiceSettings.THROW_ANGLE_SPREAD_DEG,
        )
        speed = random.uniform(
            DiceSettings.THROW_SPEED_MIN, DiceSettings.THROW_SPEED_MAX
        )
        angle_rad = math.radians(angle_deg)
        self.vel = pygame.Vector2(
            math.cos(angle_rad) * speed, math.sin(angle_rad) * speed
        )
        self.is_rolling = True
        self.tumble_timer = 0.0
        self.tumble_index = random.randrange(len(self.tumble_sprites))

    def _spawn_point(self, tray_rect: pygame.Rect) -> tuple[float, float]:
        """Return a spawn position just outside the configured tray corner."""
        offset = DiceSettings.THROW_SPAWN_OFFSET
        corners = {
            "bottom_left": (tray_rect.left - offset, tray_rect.bottom + offset),
            "bottom_right": (tray_rect.right + offset, tray_rect.bottom + offset),
            "top_left": (tray_rect.left - offset, tray_rect.top - offset),
            "top_right": (tray_rect.right + offset, tray_rect.top - offset),
        }
        return corners[DiceSettings.THROW_ORIGIN]

    # -------------------------
    # PHYSICS
    # -------------------------

    def _apply_drag(self, dt: float) -> None:
        """Exponentially decay velocity to mimic table friction."""
        decay = math.exp(-DiceSettings.LINEAR_DRAG * dt)
        self.vel *= decay

    def _bounce_against(self, bounds: pygame.Rect) -> None:
        """Clamp position into `bounds` and reflect velocity on each hit.

        Uses absolute-value reflection (not simple negation) so a die that
        spawns outside the tray cannot keep ricocheting back out.
        """
        half = self.size / 2
        min_x = bounds.left + half
        max_x = bounds.right - half
        min_y = bounds.top + half
        max_y = bounds.bottom - half

        if self.pos.x < min_x:
            self.pos.x = min_x
            self.vel.x = abs(self.vel.x) * DiceSettings.RESTITUTION
        elif self.pos.x > max_x:
            self.pos.x = max_x
            self.vel.x = -abs(self.vel.x) * DiceSettings.RESTITUTION

        if self.pos.y < min_y:
            self.pos.y = min_y
            self.vel.y = abs(self.vel.y) * DiceSettings.RESTITUTION
        elif self.pos.y > max_y:
            self.pos.y = max_y
            self.vel.y = -abs(self.vel.y) * DiceSettings.RESTITUTION

    def _advance_tumble(self, dt: float) -> None:
        """Cycle the tumble frame at a rate proportional to current speed."""
        speed = self.vel.length()
        speed_max = DiceSettings.THROW_SPEED_MAX
        t = 0.0 if speed_max <= 0 else min(1.0, speed / speed_max)
        fps = (
            DiceSettings.TUMBLE_FPS_MIN
            + (DiceSettings.TUMBLE_FPS_MAX - DiceSettings.TUMBLE_FPS_MIN) * t
        )
        self.tumble_timer += dt * fps
        if self.tumble_timer >= 1.0:
            steps = int(self.tumble_timer)
            self.tumble_timer -= steps
            self.tumble_index = (self.tumble_index + steps) % len(self.tumble_sprites)

    def _settle(self) -> None:
        """Stop the die and pick a final face."""
        self.is_rolling = False
        self.vel.update(0, 0)
        self.face_index = random.randrange(len(self.face_sprites))

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
        self.pos += self.vel * dt
        self._bounce_against(bounds)
        self._advance_tumble(dt)

        if self.vel.length() < DiceSettings.SETTLE_SPEED:
            self._settle()

    def draw(self, surface: pygame.Surface) -> None:
        """Render the current frame centered on `pos`."""
        sprite = (
            self.tumble_sprites[self.tumble_index]
            if self.is_rolling
            else self.face_sprites[self.face_index]
        )
        render_pos = (
            int(self.pos.x - self.size / 2),
            int(self.pos.y - self.size / 2),
        )
        surface.blit(sprite, render_pos)
