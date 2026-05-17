"""The 13-die bag that dice are drawn from each turn.

The bag is a data structure only — it is never drawn or visualised. Players
draw from it conceptually each time they choose to roll.

Each die in the bag carries a `DieColor` so the engine can route it
through the right per-color face distribution. The bag holds the
`BagSettings.DICE_PER_COLOR` makeup (6 green / 4 purple / 3 red), drawn
randomly without replacement until the bag empties; mid-turn refills
bring TREASURE-outcome dice back so a long press-your-luck streak does
not strand the player with nothing to roll.

Usage pattern for one player's turn::

    bag = Bag()
    bag.reset()                            # called by TurnEngine.start_turn()
    colors = bag.draw(3)                   # first roll: 3 fresh die colors
    ...
    if bag.is_empty:
        bag.recycle(set_aside_colors,
                    set_aside_outcomes)    # mid-turn refill from TREASURE pile
    colors = bag.draw(dice_needed)         # subsequent rolls

The bag resets fully at the start of each player's turn (all 13 dice
return), so the mid-turn recycle scenario only arises when a player rolls
enough times in one turn to exhaust the full pool.
"""

import random

from settings import BagSettings
from systems.outcomes import DieColor, Outcome


class Bag:
    """A drawable pool of 13 colored dice.

    The bag stores actual `DieColor` values (not just counts) because the
    color of every drawn die matters to both the rules (per-color face
    distributions) and the visuals (per-color settled art). Draws are
    uniformly random without replacement; the order returned from
    `draw()` is the order in which dice will reach the felt.
    """

    def __init__(self) -> None:
        self._dice: list[DieColor] = []
        self.reset()

    # -------------------------
    # SETUP
    # -------------------------

    def reset(self) -> None:
        """Refill the bag to its full capacity (called at the start of each turn)."""
        self._dice = []
        for color, count in BagSettings.DICE_PER_COLOR.items():
            self._dice.extend([color] * count)
        random.shuffle(self._dice)

    # -------------------------
    # QUERIES
    # -------------------------

    @property
    def count(self) -> int:
        """Number of dice currently in the bag."""
        return len(self._dice)

    @property
    def is_empty(self) -> bool:
        """True when no dice remain to draw."""
        return not self._dice

    def count_color(self, color: DieColor) -> int:
        """Return how many dice of `color` remain in the bag.

        Used by AI strategies (Lizzie in particular) to gauge how much
        bust risk is still hiding inside the bag.
        """
        return self._dice.count(color)

    # -------------------------
    # ACTIONS
    # -------------------------

    def draw(self, n: int) -> list[DieColor]:
        """Draw up to *n* dice and return their colors.

        Draws as many dice as are available; may return fewer than *n* if
        the bag is nearly empty. The caller resolves each color through
        `roll_color` to get the matching `Outcome`.

        Args:
            n: Maximum number of dice to draw.

        Returns:
            List of `DieColor` values, one per die actually drawn. Length
            is in ``[0, min(n, self.count)]``.
        """
        take = min(n, len(self._dice))
        drawn = self._dice[:take]
        self._dice = self._dice[take:]
        return drawn

    def recycle(
        self,
        set_aside_colors: list[DieColor],
        set_aside_outcomes: list[Outcome],
    ) -> None:
        """Return TREASURE-outcome dice from the set-aside pile to the bag.

        Called mid-turn when the bag empties and the player still wants to
        roll. Only TREASURE dice are recycled (their colors are preserved);
        MIMIC dice stay permanently set aside for this turn; EMPTY dice
        are already in-hand (held over) and are not in *set_aside* at all.

        Args:
            set_aside_colors:   Colors of every die set aside this turn,
                                parallel to `set_aside_outcomes`.
            set_aside_outcomes: Outcomes of those set-aside dice. Only
                                entries equal to `Outcome.TREASURE` are
                                recycled.
        """
        recycled = [
            color for color, outcome
            in zip(set_aside_colors, set_aside_outcomes)
            if outcome == Outcome.TREASURE
        ]
        if recycled:
            self._dice.extend(recycled)
            random.shuffle(self._dice)
