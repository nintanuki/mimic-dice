"""Die colors, outcomes, and the per-color face -> Outcome distributions.

Mimic Dice resolves every settled die into one of three outcomes:

    MIMIC    - bust risk; three on a turn ends the turn with zero score.
    EMPTY    - the die persists into the next roll for that turn.
    TREASURE - banked as score when the player chooses to stop.

Each die belongs to one of three colors (`DieColor`) whose face
distributions encode the difficulty tier inherited from Zombie Dice:

    GREEN  (6 dice) - 3 TREASURE / 2 EMPTY / 1 MIMIC. The "lucky" tier.
    PURPLE (4 dice) - 2 TREASURE / 2 EMPTY / 2 MIMIC. The "medium" tier;
                      stands in for Zombie Dice's yellow body color.
    RED    (3 dice) - 1 TREASURE / 2 EMPTY / 3 MIMIC. The "dangerous" tier.

The per-color distributions live here (instead of `settings.py`) because
they reference the `DieColor` and `Outcome` enums defined just above, and
moving them into `settings.py` would create a circular import. Per-color
*counts* (how many of each color belong in the bag) still live in
`BagSettings`, where it is natural to tune them alongside `TOTAL_DICE`.
"""

import random
from enum import Enum


# -------------------------
# COLOR + OUTCOME TYPES
# -------------------------


class DieColor(Enum):
    """The three difficulty tiers a die can belong to.

    The string values are the lower-case color names so they can be
    composed directly into asset paths (`empty_chest_green.png`, etc.).
    """

    GREEN  = "green"
    PURPLE = "purple"
    RED    = "red"


class Outcome(Enum):
    """The three possible results of a single settled die."""

    MIMIC    = "MIMIC"
    EMPTY    = "EMPTY"
    TREASURE = "TREASURE"


# -------------------------
# COLOR -> FACE DISTRIBUTION
# -------------------------


# Six entries per tuple matches the six faces of a physical die so the
# per-Outcome counts read at a glance. The engine resolves a roll by
# picking a uniformly-random index in [0, 5] from the tuple keyed by
# the die's color. Tuning the game's difficulty curve is one edit here.
FACE_DISTRIBUTIONS: dict[DieColor, tuple[Outcome, ...]] = {
    DieColor.GREEN: (
        Outcome.TREASURE, Outcome.TREASURE, Outcome.TREASURE,
        Outcome.EMPTY,    Outcome.EMPTY,
        Outcome.MIMIC,
    ),
    DieColor.PURPLE: (
        Outcome.TREASURE, Outcome.TREASURE,
        Outcome.EMPTY,    Outcome.EMPTY,
        Outcome.MIMIC,    Outcome.MIMIC,
    ),
    DieColor.RED: (
        Outcome.TREASURE,
        Outcome.EMPTY,    Outcome.EMPTY,
        Outcome.MIMIC,    Outcome.MIMIC,    Outcome.MIMIC,
    ),
}


def roll_color(color: DieColor) -> Outcome:
    """Roll one die of `color` and return the settled `Outcome`.

    Uses the module-level `random` so callers don't have to thread an
    rng through every layer. Tests that need determinism should seed
    `random` before driving the engine.

    Args:
        color: The die's color (difficulty tier).

    Returns:
        The Outcome that came up on this roll.
    """
    return random.choice(FACE_DISTRIBUTIONS[color])
