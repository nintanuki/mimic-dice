"""Message log: scrolling typewriter-animated history strip for game events.

Ported from Dungeon Digger's `ui/windows.py::MessageLog` so we never have to
reach back into that project. The renderer paints into a caller-supplied
`pygame.Rect`, so the layout system owns positioning and this class only
knows about typesetting.

Per-frame contract used by `GameManager`:

  * `add_message(text)`     - queue a new line; previous active line moves to
                              history.
  * `update()`              - advance the typewriter cursor by one frame.
  * `draw(surface, rect)`   - render history + in-progress line inside `rect`.

Highlighting is term-based. Substrings listed in
`MessageLogSettings.WORD_COLORS` render in their assigned color so MIMIC,
TREASURE, BUST, BANK, etc. read at a glance. Matches require non-word
boundaries on both sides so substrings of longer words don't get coloured.
"""

import pygame

from settings import ColorSettings, FontSettings, MessageLogSettings


class MessageLog:
    """Render and animate the scrolling in-game message log."""

    def __init__(self):
        """Initialize message history, highlighting rules, and typewriter state."""
        self.messages = list(MessageLogSettings.WELCOME_MESSAGE)
        self.font = pygame.font.Font(FontSettings.FONT, MessageLogSettings.FONT_SIZE)
        self.highlight_terms = self._build_highlight_terms()

        # Typewriter state
        self.full_text = ""
        self.active_message = ""
        self.char_index = 0
        self.type_speed = MessageLogSettings.TYPING_SPEED
        self.current_type_speed = self.type_speed
        self.is_typing = False

    # -------------------------
    # SETUP
    # -------------------------

    @staticmethod
    def _build_highlight_terms() -> list[tuple[str, tuple[int, int, int]]]:
        """Return highlight terms sorted longest-first so longer terms win.

        Sorting by length descending means a line containing both `BANK` and
        `BANKED` matches `BANKED` before falling back to `BANK`.
        """
        return sorted(
            MessageLogSettings.WORD_COLORS.items(),
            key=lambda item: len(item[0]),
            reverse=True,
        )

    # -------------------------
    # ACTIONS
    # -------------------------

    def add_message(self, text: str, type_speed: float | None = None) -> None:
        """Queue a new active message and start its typewriter animation.

        Args:
            text: Message text to display.
            type_speed: Optional characters-per-frame override for this line.
                When `None`, the default `MessageLogSettings.TYPING_SPEED` is
                used.
        """
        if self.full_text:
            # Move the just-finished active message into history; cap length.
            self.messages.append(self.full_text)
            if len(self.messages) > MessageLogSettings.MAX_MESSAGES:
                self.messages.pop(0)

        self.full_text = text
        self.active_message = ""
        self.char_index = 0
        self.current_type_speed = (
            type_speed if type_speed is not None else self.type_speed
        )
        self.is_typing = True

    # -------------------------
    # HIGHLIGHTING
    # -------------------------

    @staticmethod
    def _is_word_char(char: str) -> bool:
        """Return whether a character should count as part of a word."""
        return char.isalnum() or char == "_"

    def _has_word_boundaries(self, text: str, index: int, length: int) -> bool:
        """Require non-word boundaries around highlights to avoid partial matches."""
        before_ok = index == 0 or not self._is_word_char(text[index - 1])
        after_index = index + length
        after_ok = (
            after_index >= len(text)
            or not self._is_word_char(text[after_index])
        )
        return before_ok and after_ok

    def _find_match_at(
        self, text: str, upper_text: str, index: int
    ) -> tuple[str, tuple[int, int, int]] | None:
        """Find a highlight token that starts at a text index.

        Args:
            text: Original mixed-case text.
            upper_text: Uppercased version of the same text.
            index: Candidate start index.

        Returns:
            Tuple of (matched term, color) or `None` if no term matches here.
        """
        for term, color in self.highlight_terms:
            if (
                upper_text.startswith(term, index)
                and self._has_word_boundaries(text, index, len(term))
            ):
                return term, color
        return None

    def _split_colored_segments(
        self, text: str, default_color: tuple[int, int, int]
    ) -> list[tuple[str, tuple[int, int, int]]]:
        """Split text into render segments with per-term colors.

        Walks the string once; whenever a highlight term starts, the in-flight
        plain-text segment is flushed and the highlighted segment is emitted.
        Plain runs continue until the next highlight match.
        """
        if not text:
            return []

        segments: list[tuple[str, tuple[int, int, int]]] = []
        upper_text = text.upper()
        index = 0

        while index < len(text):
            match = self._find_match_at(text, upper_text, index)
            if match:
                term, color = match
                segments.append((text[index:index + len(term)], color))
                index += len(term)
                continue

            start = index
            index += 1
            while index < len(text):
                if self._find_match_at(text, upper_text, index):
                    break
                index += 1
            segments.append((text[start:index], default_color))

        return segments

    # -------------------------
    # RENDER
    # -------------------------

    def _draw_colored_line(
        self,
        surface: pygame.Surface,
        text: str,
        x: int,
        y: int,
        default_color: tuple[int, int, int],
    ) -> None:
        """Draw one line of text with inline segment coloring.

        Args:
            surface: Target surface for drawing.
            text: Text line to render.
            x: Start x pixel position.
            y: Baseline y pixel position.
            default_color: Color used for non-highlighted text in this line.
        """
        draw_x = x
        for segment_text, segment_color in self._split_colored_segments(
            text, default_color
        ):
            text_surface = self.font.render(segment_text, False, segment_color)
            surface.blit(text_surface, (draw_x, y))
            draw_x += text_surface.get_width()

    def draw(self, surface: pygame.Surface, rect: pygame.Rect) -> None:
        """Render history and active typewriter text inside `rect`.

        Args:
            surface: Target surface for the message window.
            rect: Bounded region the log occupies on the window. Text is
                inset by `MessageLogSettings.TEXT_PADDING`.
        """
        start_x = rect.x + MessageLogSettings.TEXT_PADDING
        start_y = rect.y + MessageLogSettings.TEXT_PADDING

        for index, message in enumerate(self.messages):
            y_pos = start_y + (index * MessageLogSettings.LINE_HEIGHT)
            self._draw_colored_line(
                surface, message, start_x, y_pos,
                ColorSettings.LOG_TEXT_DEFAULT,
            )

        if self.full_text:
            # The in-progress line renders directly below history.
            y_pos = start_y + (
                len(self.messages) * MessageLogSettings.LINE_HEIGHT
            )
            self._draw_colored_line(
                surface, self.active_message, start_x, y_pos,
                ColorSettings.LOG_TEXT_ACTIVE,
            )

    # -------------------------
    # UPDATE
    # -------------------------

    def update(self) -> None:
        """Advance the typewriter cursor by one frame's worth of characters."""
        if not self.is_typing:
            return
        self.char_index += self.current_type_speed
        # Clamp slicing by using an integer cursor and the full-text length.
        self.active_message = self.full_text[:int(self.char_index)]
        if self.char_index >= len(self.full_text):
            self.is_typing = False
