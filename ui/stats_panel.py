"""Stats panel: right-side column showing the roster and held-dice pile.

The panel reads three things every frame:

    * `players`              - the seat list (human + bots), each with a
                               banked-score running total.
    * `active_player_index`  - whose turn is currently up; that row gets a
                               highlight and the held-dice section shows
                               their this-turn pile.
    * `set_aside_outcomes`   - the MIMIC + TREASURE outcomes the active
                               player has accumulated so far this turn.
                               EMPTY dice are on the felt (held over) and
                               are intentionally absent here.

The panel is read-only: `GameManager` passes the data each frame; the panel
draws its own frame (filled rounded rect + border) so callers don't have
to coordinate frame ordering.

Color-agnostic icon row
-----------------------
The held-dice section shows two clearly-labelled rows so a glance tells
the player both *how close to busting* they are and *how much treasure
they'd lock in if they banked right now*. Thumbs render from the three
flat outcome icons in `AssetPaths.FLAT_OUTCOME_SPRITES` — every TREASURE
shows the same `treasure.png` regardless of which color die it came
from. The felt is where the per-color difficulty story lives; the panel
focuses on counts. Banked treasure persists in each player's `score`
(rendered in the roster); the held-dice thumbs reset on the next
`start_turn()` (bank or bust).
"""

from dataclasses import dataclass

import pygame

from settings import (
    AssetPaths,
    ColorSettings,
    DiceSettings,
    FontSettings,
    LayoutSettings,
    StatsPanelSettings,
)
from systems.outcomes import Outcome


@dataclass(frozen=True)
class PlayerView:
    """The minimum the panel needs to render one roster row."""

    name: str
    score: int


class StatsPanel:
    """Render the player roster, banked scores, and this-turn held dice."""

    def __init__(self) -> None:
        """Load the flat outcome icons and panel fonts.

        The panel owns its own sprite map (independent of `DiceRoller`)
        because the right-side art is color-agnostic by design: one icon
        per outcome, not per (color, outcome).
        """
        self.outcome_sprites: dict[Outcome, pygame.Surface] = {
            Outcome(name): self._load_flat_sprite(path)
            for name, path in AssetPaths.FLAT_OUTCOME_SPRITES.items()
        }
        self.name_font = pygame.font.Font(FontSettings.FONT, FontSettings.HUD_SIZE)
        self.score_font = pygame.font.Font(FontSettings.FONT, FontSettings.SCORE_SIZE)
        self.label_font = pygame.font.Font(FontSettings.FONT, FontSettings.HUD_SIZE)

        # Every outcome sprite is the same source tile scaled by
        # `DiceSettings.SCALE`, so deriving once works for any thumb.
        first_sprite = next(iter(self.outcome_sprites.values()))
        self.die_size = first_sprite.get_width()

    # -------------------------
    # SETUP
    # -------------------------

    @staticmethod
    def _load_flat_sprite(path: str) -> pygame.Surface:
        """Load one flat outcome icon and scale it to match the felt dice.

        Args:
            path: Path to the icon PNG relative to the working directory.

        Returns:
            The icon scaled by `DiceSettings.SCALE` so its size matches
            the colored die sprites the felt renders.
        """
        raw = pygame.image.load(path).convert_alpha()
        width, height = raw.get_size()
        scale = DiceSettings.SCALE
        if scale == 1:
            return raw
        return pygame.transform.scale(raw, (width * scale, height * scale))

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
        count: int,
        outcome: Outcome,
        y: int,
    ) -> int:
        """Draw one labelled row of held-outcome thumbs and return the next y.

        Thumbs wrap to a new row when they would overflow `rect.right`.

        Args:
            surface: Target surface.
            rect:    Panel rect; used for left/right inset.
            label:   ALL-CAPS section heading drawn above the thumbs.
            count:   Number of thumbs to draw. Each thumb is the same flat
                     icon for `outcome` (color-agnostic by design).
            outcome: Outcome whose row of thumbs is being drawn (MIMIC or
                     TREASURE). The label color matches this outcome.
            y:       Top y where the label starts.

        Returns:
            Y coordinate just below the last drawn thumb (or the label,
            if `count` is zero).
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

        if count <= 0:
            # Render an em-dash so an empty row still occupies vertical
            # space and the section ordering stays stable as dice arrive.
            return self._draw_text(
                surface, self.label_font, "—", left, y,
                ColorSettings.STATS_TEXT_COLOR,
            )

        sprite = self.outcome_sprites[outcome]
        spacing = StatsPanelSettings.HELD_DICE_SPACING
        row_gap = StatsPanelSettings.HELD_DICE_ROW_GAP
        cursor_x = left
        row_y = y
        for _ in range(count):
            if cursor_x + sprite.get_width() > right:
                cursor_x = left
                row_y += self.die_size + row_gap
            surface.blit(sprite, (cursor_x, row_y))
            cursor_x += sprite.get_width() + spacing
        return row_y + self.die_size

    def draw(
        self,
        surface: pygame.Surface,
        rect: pygame.Rect,
        players: list[PlayerView],
        active_player_index: int,
        set_aside_outcomes: list[Outcome],
    ) -> None:
        """Paint the panel: frame, roster, held-outcome rows for the active player.

        Args:
            surface:             Target surface.
            rect:                Panel rect from `ui.layout.stats_panel_rect`.
            players:             All seats in turn order (human + bots).
            active_player_index: Index into `players` of the player who is
                                 currently rolling.
            set_aside_outcomes:  Outcomes set aside this turn for the active
                                 player. The panel counts MIMICs and
                                 TREASUREs from this list; colors are not
                                 consulted because the right-side icons are
                                 deliberately color-agnostic.
        """
        self._draw_frame(surface, rect)

        y = rect.top + StatsPanelSettings.TEXT_PADDING

        # Roster up top so the eye lands on who-is-who first.
        y = self._draw_roster(surface, rect, players, active_player_index, y)

        # Held outcomes (active player, this turn only). Treasure first
        # because it's the "good" pile the player is trying to grow; mimics
        # below so the bust risk reads as the cost of pushing your luck.
        treasure_count = set_aside_outcomes.count(Outcome.TREASURE)
        mimic_count    = set_aside_outcomes.count(Outcome.MIMIC)
        y += StatsPanelSettings.SECTION_GAP
        y = self._draw_held_row(
            surface, rect, "TREASURE", treasure_count, Outcome.TREASURE, y,
        )
        y += StatsPanelSettings.SECTION_GAP
        self._draw_held_row(
            surface, rect, "MIMICS", mimic_count, Outcome.MIMIC, y,
        )
