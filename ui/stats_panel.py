"""Stats panel: right-side column showing player, score, and held dice.

The panel reads three things every frame:

    * Player name   - shown at the top.
    * Banked score  - the running total of TREASURE banked across turns.
    * Held dice     - the MIMIC + TREASURE dice set aside so far this turn.
                      EMPTY dice are in-hand (re-rolled each turn) and
                      stay in the tray, so they are intentionally absent
                      from this panel.

The panel is read-only: `GameManager` passes the data each frame; the panel
draws its own frame (filled rounded rect + border) so callers don't have
to coordinate frame ordering.

The held-dice section shows two clearly-labelled rows so a glance tells
the player both *how close to busting* they are and *how much treasure
they'd lock in if they banked right now*. Treasure persists across turns
through the banked-score number above; the held-treasure thumbs reset
to empty on the next `start_turn()` (bank or bust), same as the held
mimics. That matches the player's mental model of "carry your earned
score forward, but the dice you set aside this turn reset on every new
turn".
"""

import pygame

from settings import (
    ColorSettings,
    FontSettings,
    LayoutSettings,
    StatsPanelSettings,
)
from systems.outcomes import Outcome


class StatsPanel:
    """Render the player name, banked score, and this-turn held dice."""

    def __init__(
        self,
        outcome_sprites: dict[Outcome, list[pygame.Surface]],
    ):
        """Cache references to the die sprite frames and panel fonts.

        Args:
            outcome_sprites: Mapping from each Outcome to its list of
                settled-face frames. The panel reads from this so the
                held-dice thumbs share the same artwork as the tray dice.
        """
        self.outcome_sprites = outcome_sprites
        self.name_font = pygame.font.Font(FontSettings.FONT, FontSettings.HUD_SIZE)
        self.score_font = pygame.font.Font(FontSettings.FONT, FontSettings.SCORE_SIZE)
        self.label_font = pygame.font.Font(FontSettings.FONT, FontSettings.HUD_SIZE)

        # Derive the rendered die size once; all rows share it.
        first_row = next(iter(outcome_sprites.values()))
        self.die_size = first_row[0].get_width()

    # -------------------------
    # RENDER
    # -------------------------

    def _draw_frame(self, surface: pygame.Surface, rect: pygame.Rect) -> None:
        """Paint the filled rounded-rect frame and its border."""
        pygame.draw.rect(
            surface,
            ColorSettings.PANEL_FILL_COLOR,
            rect,
            border_radius=LayoutSettings.PANEL_BORDER_RADIUS,
        )
        pygame.draw.rect(
            surface,
            ColorSettings.PANEL_BORDER_COLOR,
            rect,
            width=LayoutSettings.PANEL_BORDER_WIDTH,
            border_radius=LayoutSettings.PANEL_BORDER_RADIUS,
        )

    def _draw_text(
        self,
        surface: pygame.Surface,
        font: pygame.font.Font,
        text: str,
        x: int,
        y: int,
        color: tuple[int, int, int],
    ) -> int:
        """Blit `text` at (x, y) and return the next-row baseline y."""
        text_surface = font.render(text, False, color)
        surface.blit(text_surface, (x, y))
        return y + text_surface.get_height()

    def _draw_held_row(
        self,
        surface: pygame.Surface,
        rect: pygame.Rect,
        label: str,
        faces: list[int],
        outcome: Outcome,
        y: int,
    ) -> int:
        """Draw one labelled row of held-die thumbs and return the next y.

        Thumbs wrap to a new row when they would overflow `rect.right`.

        Args:
            surface: Target surface.
            rect:    Panel rect; used for left/right inset.
            label:   ALL-CAPS section heading drawn above the thumbs.
            faces:   Face values (1–6) of each held die in display order.
            outcome: Outcome whose sprite row supplies the thumb artwork.
            y:       Top y where the label starts.

        Returns:
            Y coordinate just below the last drawn thumb (or the label,
            if `faces` is empty).
        """
        left = rect.left + StatsPanelSettings.TEXT_PADDING
        right = rect.right - StatsPanelSettings.TEXT_PADDING

        # Label color matches the outcome highlight color so the row reads
        # at a glance even at small font sizes.
        label_color = {
            Outcome.MIMIC:    ColorSettings.LOG_HIGHLIGHT_MIMIC,
            Outcome.TREASURE: ColorSettings.LOG_HIGHLIGHT_TREASURE,
            Outcome.EMPTY:    ColorSettings.LOG_HIGHLIGHT_EMPTY,
        }[outcome]
        y = self._draw_text(surface, self.label_font, label, left, y, label_color)
        y += StatsPanelSettings.HELD_DICE_LABEL_GAP

        if not faces:
            # Render an em-dash so an empty row still occupies vertical
            # space and the section ordering stays stable as dice arrive.
            return self._draw_text(
                surface, self.label_font, "—", left, y,
                ColorSettings.STATS_TEXT_COLOR,
            )

        sprites = self.outcome_sprites[outcome]
        spacing = StatsPanelSettings.HELD_DICE_SPACING
        row_gap = StatsPanelSettings.HELD_DICE_ROW_GAP
        cursor_x = left
        row_y = y
        for face in faces:
            # Clamp to a safe column index; out-of-range faces fall back to
            # the first column rather than crashing.
            column = (face - 1) if 1 <= face <= len(sprites) else 0
            sprite = sprites[column]
            if cursor_x + sprite.get_width() > right:
                cursor_x = left
                row_y += self.die_size + row_gap
            surface.blit(sprite, (cursor_x, row_y))
            cursor_x += sprite.get_width() + spacing
        return row_y + self.die_size

    def _split_set_aside_by_outcome(
        self,
        faces: list[int],
        outcomes: list[Outcome],
    ) -> tuple[list[int], list[int]]:
        """Partition the set-aside faces into (treasure_faces, mimic_faces)."""
        treasure_faces: list[int] = []
        mimic_faces: list[int] = []
        for face, outcome in zip(faces, outcomes):
            if outcome == Outcome.TREASURE:
                treasure_faces.append(face)
            elif outcome == Outcome.MIMIC:
                mimic_faces.append(face)
        return treasure_faces, mimic_faces

    def draw(
        self,
        surface: pygame.Surface,
        rect: pygame.Rect,
        player_name: str,
        score: int,
        set_aside_faces: list[int],
        set_aside_outcomes: list[Outcome],
    ) -> None:
        """Paint the panel: frame, player line, score line, held dice rows.

        Args:
            surface:            Target surface.
            rect:               Panel rect from `ui.layout.stats_panel_rect`.
            player_name:        Display name shown at the top of the panel.
            score:              Banked treasure score across all turns so far.
            set_aside_faces:    Face values set aside this turn (parallel
                                to `set_aside_outcomes`).
            set_aside_outcomes: Outcomes set aside this turn (MIMIC + TREASURE).
        """
        self._draw_frame(surface, rect)

        left = rect.left + StatsPanelSettings.TEXT_PADDING
        y = rect.top + StatsPanelSettings.TEXT_PADDING

        # Player and score live at the top so the eye lands on them first.
        y = self._draw_text(
            surface, self.name_font, player_name, left, y,
            ColorSettings.STATS_TEXT_COLOR,
        )
        y += StatsPanelSettings.LINE_HEIGHT - self.name_font.get_height()
        y = self._draw_text(
            surface, self.score_font, f"SCORE: {score}", left, y,
            ColorSettings.LOG_HIGHLIGHT_TREASURE,
        )

        # Held dice (this turn only). Treasure first because it's the
        # "good" pile the player is trying to grow; mimics below so the
        # bust risk reads as the cost of pushing your luck.
        treasure_faces, mimic_faces = self._split_set_aside_by_outcome(
            set_aside_faces, set_aside_outcomes,
        )
        y += StatsPanelSettings.SECTION_GAP
        y = self._draw_held_row(
            surface, rect, "TREASURE", treasure_faces, Outcome.TREASURE, y,
        )
        y += StatsPanelSettings.SECTION_GAP
        self._draw_held_row(
            surface, rect, "MIMICS", mimic_faces, Outcome.MIMIC, y,
        )
