"""Stats panel: right-side column showing the roster and held-dice pile.

The panel reads three things every frame:

    * `players`              - the seat list (human + bots), each with a
                               banked-score running total.
    * `active_player_index`  - whose turn is currently up; that row gets a
                               highlight and the held-dice section shows
                               their this-turn pile.
    * `set_aside_colors` +
      `set_aside_outcomes`   - the MIMIC + TREASURE dice the active player
                               has accumulated so far this turn. EMPTY dice
                               are on the felt (held over) and are
                               intentionally absent here.

The panel is read-only: `GameManager` passes the data each frame; the panel
draws its own frame (filled rounded rect + border) so callers don't have
to coordinate frame ordering.

The held-dice section shows two clearly-labelled rows so a glance tells
the player both *how close to busting* they are and *how much treasure
they'd lock in if they banked right now*. Each thumb is rendered from the
per-(color, outcome) settled sprite map shared with `DiceRoller`, so a
banked green TREASURE shows the green chest, a banked red MIMIC shows the
red mimic, and so on. Banked treasure persists in each player's `score`
(rendered in the roster); the held-dice thumbs reset on the next
`start_turn()` (bank or bust).
"""

from dataclasses import dataclass

import pygame

from settings import (
    ColorSettings,
    FontSettings,
    LayoutSettings,
    StatsPanelSettings,
)
from systems.outcomes import DieColor, Outcome


@dataclass(frozen=True)
class PlayerView:
    """The minimum the panel needs to render one roster row."""

    name: str
    score: int


class StatsPanel:
    """Render the player roster, banked scores, and this-turn held dice."""

    def __init__(
        self,
        settled_sprites: dict[tuple[DieColor, Outcome], pygame.Surface],
    ):
        """Cache references to the die sprite frames and panel fonts.

        Args:
            settled_sprites: Map from (color, outcome) to the single settled
                sprite for that combination. The panel reads from this so
                the held-dice thumbs share the same artwork as the tray
                dice — a green TREASURE thumb is the same sprite the felt
                shows when a green die lands TREASURE.
        """
        self.settled_sprites = settled_sprites
        self.name_font = pygame.font.Font(FontSettings.FONT, FontSettings.HUD_SIZE)
        self.score_font = pygame.font.Font(FontSettings.FONT, FontSettings.SCORE_SIZE)
        self.label_font = pygame.font.Font(FontSettings.FONT, FontSettings.HUD_SIZE)

        # Derive the rendered die size once; every settled sprite is the
        # same source tile size scaled by `DiceSettings.SCALE`.
        first_sprite = next(iter(settled_sprites.values()))
        self.die_size = first_sprite.get_width()

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

    def _draw_roster(
        self,
        surface: pygame.Surface,
        rect: pygame.Rect,
        players: list[PlayerView],
        active_index: int,
        y: int,
    ) -> int:
        """Draw one row per player; active player gets a marker + highlight.

        Returns the y just below the last row.
        """
        left = rect.left + StatsPanelSettings.TEXT_PADDING
        right = rect.right - StatsPanelSettings.TEXT_PADDING

        for index, player in enumerate(players):
            is_active = index == active_index
            marker = (
                StatsPanelSettings.ACTIVE_MARKER
                if is_active
                else StatsPanelSettings.INACTIVE_MARKER
            )
            name_color = (
                ColorSettings.LOG_HIGHLIGHT_TREASURE
                if is_active
                else ColorSettings.STATS_TEXT_COLOR
            )

            name_surface = self.name_font.render(
                f"{marker}{player.name}", False, name_color,
            )
            score_surface = self.score_font.render(
                str(player.score), False, ColorSettings.STATS_TEXT_COLOR,
            )

            surface.blit(name_surface, (left, y))
            # Right-align the score in the row so multi-digit scores still
            # land flush with the panel inset.
            surface.blit(
                score_surface,
                (right - score_surface.get_width(), y),
            )
            y += StatsPanelSettings.PLAYER_ROW_HEIGHT
        return y

    def _draw_held_row(
        self,
        surface: pygame.Surface,
        rect: pygame.Rect,
        label: str,
        colors: list[DieColor],
        outcome: Outcome,
        y: int,
    ) -> int:
        """Draw one labelled row of held-die thumbs and return the next y.

        Thumbs wrap to a new row when they would overflow `rect.right`.

        Args:
            surface: Target surface.
            rect:    Panel rect; used for left/right inset.
            label:   ALL-CAPS section heading drawn above the thumbs.
            colors:  Die color of each held entry, in display order. Each
                     thumb is the settled sprite for `(color, outcome)`.
            outcome: Outcome whose row of thumbs is being drawn (MIMIC or
                     TREASURE). The label color matches this outcome.
            y:       Top y where the label starts.

        Returns:
            Y coordinate just below the last drawn thumb (or the label,
            if `colors` is empty).
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

        if not colors:
            # Render an em-dash so an empty row still occupies vertical
            # space and the section ordering stays stable as dice arrive.
            return self._draw_text(
                surface, self.label_font, "—", left, y,
                ColorSettings.STATS_TEXT_COLOR,
            )

        spacing = StatsPanelSettings.HELD_DICE_SPACING
        row_gap = StatsPanelSettings.HELD_DICE_ROW_GAP
        cursor_x = left
        row_y = y
        for color in colors:
            sprite = self.settled_sprites[(color, outcome)]
            if cursor_x + sprite.get_width() > right:
                cursor_x = left
                row_y += self.die_size + row_gap
            surface.blit(sprite, (cursor_x, row_y))
            cursor_x += sprite.get_width() + spacing
        return row_y + self.die_size

    def _split_set_aside_by_outcome(
        self,
        colors: list[DieColor],
        outcomes: list[Outcome],
    ) -> tuple[list[DieColor], list[DieColor]]:
        """Partition the set-aside colors into (treasure_colors, mimic_colors)."""
        treasure_colors: list[DieColor] = []
        mimic_colors: list[DieColor] = []
        for color, outcome in zip(colors, outcomes):
            if outcome == Outcome.TREASURE:
                treasure_colors.append(color)
            elif outcome == Outcome.MIMIC:
                mimic_colors.append(color)
        return treasure_colors, mimic_colors

    def draw(
        self,
        surface: pygame.Surface,
        rect: pygame.Rect,
        players: list[PlayerView],
        active_player_index: int,
        set_aside_colors: list[DieColor],
        set_aside_outcomes: list[Outcome],
    ) -> None:
        """Paint the panel: frame, roster, held-dice rows for the active player.

        Args:
            surface:             Target surface.
            rect:                Panel rect from `ui.layout.stats_panel_rect`.
            players:             All seats in turn order (human + bots).
            active_player_index: Index into `players` of the player who is
                                 currently rolling.
            set_aside_colors:    Colors set aside this turn (parallel to
                                 `set_aside_outcomes`).
            set_aside_outcomes:  Outcomes set aside this turn (MIMIC + TREASURE).
        """
        self._draw_frame(surface, rect)

        y = rect.top + StatsPanelSettings.TEXT_PADDING

        # Roster up top so the eye lands on who-is-who first.
        y = self._draw_roster(surface, rect, players, active_player_index, y)

        # Held dice (active player, this turn only). Treasure first because
        # it's the "good" pile the player is trying to grow; mimics below
        # so the bust risk reads as the cost of pushing your luck.
        treasure_colors, mimic_colors = self._split_set_aside_by_outcome(
            set_aside_colors, set_aside_outcomes,
        )
        y += StatsPanelSettings.SECTION_GAP
        y = self._draw_held_row(
            surface, rect, "TREASURE", treasure_colors, Outcome.TREASURE, y,
        )
        y += StatsPanelSettings.SECTION_GAP
        self._draw_held_row(
            surface, rect, "MIMICS", mimic_colors, Outcome.MIMIC, y,
        )
