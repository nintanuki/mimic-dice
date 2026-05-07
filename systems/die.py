import pygame
import random
import math

class Die:
    """Handles the animation and state of a single rolling die."""

    def __init__(self, x: int, y: int, sprites: list[pygame.Surface]):
        """
        Initialize the die's position, sprites, and animation state.
        
        Args:
            x: The X coordinate of the die's base position.
            y: The Y coordinate of the die's base position.
            sprites: A list of 6 pygame.Surface objects representing the die faces.
        """
        self.base_pos = pygame.Vector2(x, y)
        self.current_pos = pygame.Vector2(x, y)
        self.sprites = sprites
        self.current_frame = 0
        
        # Animation State
        self.is_rolling = False
        self.timer = 0
        self.duration = 1.0  # Total roll time in seconds
        self.peak_height = 240  # From your YouTube reference

    def roll(self) -> None:
        """Trigger the rolling animation."""
        if not self.is_rolling:
            self.is_rolling = True
            self.timer = 0

    def _ease_out_cubic(self, t: float) -> float:
        """
        Cubic easing out function for smooth animation.
        
        Args:
            t: A value between 0 and 1 representing the progress of the animation.
        Returns:
            The eased value corresponding to the input progress.
        """
        return 1 - pow(1 - t, 3)

    def _ease_in_cubic(self, t: float) -> float:
        """
        Cubic easing in function for smooth animation.
        
        Args:
            t: A value between 0 and 1 representing the progress of the animation.
        Returns:
            The eased value corresponding to the input progress.
        """
        return t * t * t

    def update(self, dt: float) -> None:
        """
        Calculate the Y offset based on the cubic easing logic.
        
        Args:
            dt: The time elapsed since the last update in seconds.
        """
        if not self.is_rolling:
            return

        self.timer += dt
        progress = self.timer / self.duration

        if progress < 0.5:
            # Phase 1: Going Up (0.0 to 0.5 progress)
            sub_t = progress * 2
            offset = self._ease_out_cubic(sub_t) * self.peak_height
            self.current_pos.y = self.base_pos.y - offset
        elif progress < 1.0:
            # Phase 2: Coming Down (0.5 to 1.0 progress)
            sub_t = (progress - 0.5) * 2
            offset = (1 - self._ease_in_cubic(sub_t)) * self.peak_height
            self.current_pos.y = self.base_pos.y - offset
        else:
            # Finish
            self.is_rolling = False
            self.current_pos.y = self.base_pos.y
            self.current_frame = random.randint(0, 5) # Final Result

        if self.is_rolling:
            # Rapidly swap frames for the "spinning" effect
            self.current_frame = random.randint(0, 5)

    def draw(self, surface: pygame.Surface) -> None:
        """Render the current die frame at the calculated position."""
        surface.blit(self.sprites[self.current_frame], self.current_pos)