"""The 13-die bag that dice are drawn from each turn.

The bag is a data structure only — it is never drawn or visualised. Players
draw from it conceptually each time they choose to roll.

Phase 0: all 13 dice are mechanically identical (equal 1/3 odds per
outcome). Each draw produces a fresh 1–6 face; the caller (`TurnEngine`)
runs `face_to_outcome` to classify it. Returning faces — not outcomes —
lets the dice renderer show the same face value that drove the outcome,
so a die showing "1" is always a MIMIC and a die showing "6" is always a
TREASURE under the Phase 0 threshold mapping. Phase 1 will swap this
random-face draw for a per-color distribution lookup; the
faces-out / outcomes-resolved-elsewhere split stays.

Usage pattern for one player's turn::

    bag = Bag()
    bag.reset()                           # called by TurnEngine.start_turn()
    faces = bag.draw(3)                   # first roll: 3 fresh face values
    ...
    if bag.is_empty:
        bag.recycle(set_aside_outcomes)   # mid-turn refill from TREASURE pile
    faces = bag.draw(dice_needed)         # subsequent rolls

The bag resets fully at the start of each player's turn (all 13 dice
return), so the mid-turn recycle scenario only arises when a player rolls
enough times in one turn to exhaust the full pool.
"""

import random

from settings import BagSettings
from systems.outcomes import Outcome


class Bag:
    """A drawable pool of 13 mechanically-identical dice.

    All state is an integer count; there is no per-die identity in Phase 0
    because every die is statistically interchangeable.
    """

    def __init__(self) -> None:
        self._count: int = 0
        self.reset()

    # -------------------------
    # SETUP
    # -------------------------

    def reset(self) -> None:
        """Refill the bag to its full capacity (called at the start of each turn)."""
        self._count = BagSettings.TOTAL_DICE

    # -------------------------
    # QUERIES
    # -------------------------

    @property
    def count(self) -> int:
        """Number of dice currently in the bag."""
        return self._count

    @property
    def is_empty(self) -> bool:
        """True when no dice remain to draw."""
        return self._count == 0

    # -------------------------
    # ACTIONS
    # -------------------------

    def draw(self, n: int) -> list[int]:
        """Draw up to *n* dice and return their rolled face values.

        Draws as many dice as are available; may return fewer than *n* if
        the bag is nearly empty. Each drawn die produces a uniformly-random
        face in ``[1, 6]``; the caller runs `face_to_outcome` to classify
        the face into a MIMIC / EMPTY / TREASURE outcome.

        Args:
            n: Maximum number of dice to draw.

        Returns:
            List of integer faces in ``[1, 6]``, one per die actually
            drawn. Length is in ``[0, min(n, self.count)]``.
        """
        drawn = min(n, self._count)
        self._count -= drawn
        return [random.randint(1, 6) for _ in range(drawn)]

    def recycle(self, set_aside: list[Outcome]) -> None:
        """Return TREASURE-outcome dice from the set-aside pile to the bag.

        Called mid-turn when the bag empties and the player still wants to
        roll. Only TREASURE dice are recycled; MIMIC dice stay permanently
        set aside for this turn; EMPTY dice are already in-hand (held over)
        and are not in *set_aside* at all.

        Args:
            set_aside: The accumulated MIMIC + TREASURE outcomes set aside
                       so far this turn. Only TREASURE items are counted.
        """
        treasure_count = sum(1 for outcome in set_aside if outcome == Outcome.TREASURE)
        self._count += treasure_count
