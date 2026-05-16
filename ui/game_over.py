"""GAME OVER overlay: centered title, optional final scores, fade-in prompt.

Pattern ported from Dungeon Digger's `draw_end_game_screens` so the cabinet
has a consistent end-of-run look across its games. Mimic Dice doesn't have
"win" and "loss" as separate states (everyone reaches an end and the highest
score wins), so the screen always shows GAME OVER + the winner + a per-player
score list.

Per-frame contract used by `GameManager` when in the game-over state:

  * `reset(current_ms)`        - call once when entering the screen so the
                                 prompt-fade timer starts from zero.
  * `is_input_accepted(now)`   - returns False during the short input grace
                                 period so a held button doesn't restart
                                 instantly.
  * `draw(surface, now, ...)`  - paint the dim overlay, title, optional
                                 final-scores rows, and the play-again
                                 prompt with its fade-in alpha.

The screen does not own game state; it is a pure renderer. The
`GameManager` decides when to enter the state, what scores to show, and
what to do when the A / ENTER input is accepted.
"""

import pygame

from settings import ColorSettings, FontSettings, GameOverSettings
from ui.render_utils import color_with_alpha


class GameOverScreen:
    """Render the GAME OVER overlay, final scores, and play-again prompt."""

    def __init__(self):
        """Pre-build the three fonts we use so we don't re-open them per frame."""
        self.title_font = pygame.font.Font(
            FontSettings.FONT, FontSettings.ENDGAME_SIZE
        )
        self.score_font = pygame.font.Font(
            FontSettings.FONT, FontSettings.SCORE_SIZE
        )
        self.prompt_font = pygame.font.Font(
            FontSettings.FONT, FontSettings.LARGE_SIZE
        )

        # `reset()` overwrites this; the initial 0 is just a placeholder
        # so `is_input_accepted` and `draw` can run before `reset`.
        self.start_ms = 0

    # -------------------------
    # STATE
    # -------------------------

    def reset(self, current_ms: int) -> None:
        """Record the moment the screen became active.

        The input grace period and the prompt fade both start from here.

        Args:
            current_ms: `pygame.time.get_ticks()` at entry.
        """
        self.start_ms = current_ms

    def is_input_accepted(self, current_ms: int) -> bool:
        """Return True once enough time has passed to accept restart input.

        Args:
            current_ms: `pygame.time.get_ticks()` at this frame.

        Returns:
            False during `GameOverSettings.CONTINUE_DELAY_MS` after `reset`,
            True afterwards.
        """
        return (current_ms - self.start_ms) >= GameOverSettings.CONTINUE_DELAY_MS

    # -------------------------
    # RENDER HELPERS
    # -------------------------

    @staticmethod
    def _draw_dim_overlay(surface: pygame.Surface) -> None:
        """Cover the gameplay area with a semi-transparent dim so text stands out."""
        overlay = pygame.Surface(surface.get_size())
        overlay.set_alpha(GameOverSettings.OVERLAY_ALPHA)
        overlay.fill(ColorSettings.BLACK)
        surface.blit(overlay, (0, 0))

    def _draw_title(
        self, surface: pygame.Surface, center_x: int, center_y: int
    ) -> pygame.Rect:
        """Draw the centered GAME OVER title and return its rect."""
        title_surf = self.title_font.render(
            "GAME OVER", False, ColorSettings.RED
        )
        title_rect = title_surf.get_rect(center=(center_x, center_y))
        surface.blit(title_surf, title_rect)
        return title_rect

    def _draw_scores(
        self,
        surface: pygame.Surface,
        center_x: int,
        top_y: int,
        final_scores: list[tuple[str, int]] | None,
    ) -> int:
        """Draw the per-player final-scores list under the title.

        Args:
            surface: Target surface for drawing.
            center_x: Horizontal center the rows align around.
            top_y: Y-coordinate of the first row.
            final_scores: Ordered list of `(player_name, score)` pairs, or
                `None` to skip rendering (useful before the game has a
                concept of finished players).

        Returns:
            The Y-coordinate immediately below the last row drawn, or
            `top_y` unchanged when nothing was drawn.
        """
        if not final_scores:
            return top_y

        line_height = GameOverSettings.SCORE_LINE_HEIGHT
        current_y = top_y
        for index, (name, score) in enumerate(final_scores):
            # The leading row is the winner; tint it the treasure color so
            # the eye lands on the winner first.
            color = (
                ColorSettings.LOG_HIGHLIGHT_TREASURE
                if index == 0
                else ColorSettings.WHITE
            )
            row_text = f"{name.upper()}  {score}"
            row_surf = self.score_font.render(row_text, False, color)
            row_rect = row_surf.get_rect(center=(center_x, current_y))
            surface.blit(row_surf, row_rect)
            current_y += line_height
        return current_y

    def _prompt_alpha(self, current_ms: int) -> int:
        """Return the per-frame alpha for the play-again prompt.

        Alpha is 0 while input is still gated, then ramps from 0 to 255 over
        `GameOverSettings.PROMPT_FADE_MS` so the prompt eases in instead of
        popping.
        """
        if not self.is_input_accepted(current_ms):
            return 0
        elapsed = (
            current_ms - self.start_ms - GameOverSettings.CONTINUE_DELAY_MS
        )
        ratio = elapsed / max(1, GameOverSettings.PROMPT_FADE_MS)
        return max(0, min(255, int(ratio * 255)))

    def _draw_prompt(
        self, surface: pygame.Surface, center_x: int, center_y: int, alpha: int
    ) -> None:
        """Draw the play-again prompt with the given alpha, if visible."""
        if alpha <= 0:
            return
        color = color_with_alpha(ColorSettings.LOG_TEXT_ACTIVE, alpha)
        prompt_surf = self.prompt_font.render(
            GameOverSettings.CONTINUE_PROMPT, False, color
        )
        prompt_rect = prompt_surf.get_rect(center=(center_x, center_y))
        surface.blit(prompt_surf, prompt_rect)

    # -------------------------
    # DRAW
    # -------------------------

    def draw(
        self,
        surface: pygame.Surface,
        current_ms: int,
        final_scores: list[tuple[str, int]] | None = None,
    ) -> None:
        """Composite the full GAME OVER screen onto `surface`.

        Args:
            surface: Target surface (typically the full window).
            current_ms: `pygame.time.get_ticks()` at this frame, used to
                drive the input grace period and the prompt fade-in.
            final_scores: Optional ordered list of `(player_name, score)`
                with the winner first. When omitted, only the title and
                prompt render.
        """
        surface_width, surface_height = surface.get_size()
        center_x = surface_width // 2
        title_y = surface_height // 2

        self._draw_dim_overlay(surface)
        title_rect = self._draw_title(surface, center_x, title_y)

        scores_top = title_rect.bottom + GameOverSettings.SCORE_TOP_GAP
        scores_bottom = self._draw_scores(
            surface, center_x, scores_top, final_scores
        )

        # If scores rendered, anchor the prompt below them; otherwise sit
        # just below the title at the configured offset.
        prompt_y = (
            scores_bottom + GameOverSettings.PROMPT_OFFSET_Y
            if final_scores
            else title_rect.bottom + GameOverSettings.PROMPT_OFFSET_Y
        )
        self._draw_prompt(
            surface, center_x, prompt_y, self._prompt_alpha(current_ms)
        )
