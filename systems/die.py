import pygame
import random
import math
from settings import ScreenSettings

class Die:
    """Handles the animation and state of a single rolling die."""

    def __init__(self, target_x: int, target_y: int, sprites: list[pygame.Surface]):
        """
        Initialize the die's position, sprites, and animation state.
        
        Args:
            target_x: The X coordinate of the die's target position.
            target_y: The Y coordinate of the die's target position.
            sprites: A list of 6 pygame.Surface objects representing the die faces.
        """
        self.target_pos = pygame.Vector2(target_x, target_y)
        self.start_pos = pygame.Vector2(target_x, ScreenSettings.HAND_Y_POS)
        self.current_pos = pygame.Vector2(self.start_pos)
        
        self.sprites = sprites
        self.current_frame = 0
        self.is_rolling = False
        
        self.timer = 0
        self.duration = 0.8

    def roll(self) -> None:
        """Trigger the rolling animation."""
        if not self.is_rolling:
            self.is_rolling = True
            self.timer = 0
            self.current_pos = pygame.Vector2(self.start_pos)

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

        if progress < 1.0:
            # Calculate easing
            eased_t = self._ease_out_cubic(progress)
            
            # Move from Hand to Table
            self.current_pos = self.start_pos.lerp(self.target_pos, eased_t)
            
            # Spin the frames while moving
            self.current_frame = random.randint(0, 5)
        else:
            # Animation complete
            self.is_rolling = False
            self.current_pos = pygame.Vector2(self.target_pos)
            self.current_frame = random.randint(0, 5) # Final result

    def draw(self, surface: pygame.Surface) -> None:
        """Render the current die frame at the calculated position."""
        # Offset by half sprite size to center the image on the coordinate
        size = self.sprites[0].get_width()
        render_pos = (self.current_pos.x - size // 2, self.current_pos.y - size // 2)
        surface.blit(self.sprites[self.current_frame], render_pos)