"""Die colors, outcomes, the per-color face -> Outcome distributions, and
the per-(color, outcome) -> pip-face-number mapping used by the renderer.

Mimic Dice resolves every settled die into one of three outcomes:

    MIMIC    - bust risk; three on a turn ends the turn with zero score.
    EMPTY    - the die persists into the next roll for that turn.
    TREASURE - banked as score when the player chooses to stop.

Each die belongs to one of three colors (`DieColor`) whose face
distributions encode the difficulty tier inherited from Zombie Dice:

    GREEN  (6 dice) - 3 TREASURE / 2 EMPTY / 1 MIMIC. The "lucky" tier.
    YELLOW (4 dice) - 2 TREASURE / 2 EMPTY / 2 MIMIC. The "medium" tier;
                      matches Zombie Dice's yellow body color.
    RED    (3 dice) - 1 TREASURE / 2 EMPTY / 3 MIMIC. The "dangerous" tier.

The per-color distributions live here (instead of `settings.py`) because
they reference the `DieColor` and `Outcome` enums defined just above, and
moving them into `settings.py` would create a circular import. Per-color
*counts* (how many of each color belong in the bag) still live in
`BagSettings`, where it is natural to tune them alongside `TOTAL_DICE`.

Pip-face mapping
----------------
`OUTCOME_FACE_NUMBERS` is parallel to `FACE_DISTRIBUTIONS` but indexed by
`(color, outcome)` and answers a *visual* question: "given this die's
color resolved to this outcome, which 1-6 pip face should the renderer
draw?". Each set's size matches the count of that outcome in the
matching `FACE_DISTRIBUTIONS` entry (e.g. GREEN has 3 TREASUREs and 3
TREASURE faces 4/5/6), so picking a face uniformly at random from the
matching set is statistically equivalent to picking an index from
`FACE_DISTRIBUTIONS` directly. The mapping is intentionally banded
1/2/3 → MIMIC → EMPTY → TREASURE so the *number* of pips visible on the
die tells the player what the die did, and the *color* tells them how
risky the die was to roll.
"""

import random
from enum import Enum


# -------------------------
# COLOR + OUTCOME TYPES
# -------------------------


class DieColor(Enum):
    """The three difficulty tiers a die can belong to.

    The string values are the lower-case color names so they key directly
    into the per-color sheet-row lookup in `AssetPaths.DIE_FACE_ROWS`.
    """

    GREEN  = "green"
    YELLOW = "yellow"
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
    DieColor.YELLOW: (
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


# -------------------------
# (COLOR, OUTCOME) -> PIP FACE NUMBERS
# -------------------------


# Per-color visual mapping: given an outcome, which 1-6 pip faces represent
# it on the rendered die. The renderer picks one face uniformly at random
# from the matching set when a die settles. Set sizes mirror the matching
# counts in `FACE_DISTRIBUTIONS`, which keeps this purely a rendering layer
# — the rules engine never reads it.
OUTCOME_FACE_NUMBERS: dict[tuple[DieColor, Outcome], tuple[int, ...]] = {
    (DieColor.GREEN,  Outcome.MIMIC):    (1,),
    (DieColor.GREEN,  Outcome.EMPTY):    (2, 3),
    (DieColor.GREEN,  Outcome.TREASURE): (4, 5, 6),
    (DieColor.YELLOW, Outcome.MIMIC):    (1, 2),
    (DieColor.YELLOW, Outcome.EMPTY):    (3, 4),
    (DieColor.YELLOW, Outcome.TREASURE): (5, 6),
    (DieColor.RED,    Outcome.MIMIC):    (1, 2, 3),
    (DieColor.RED,    Outcome.EMPTY):    (4, 5),
    (DieColor.RED,    Outcome.TREASURE): (6,),
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


def face_for_outcome(color: DieColor, outcome: Outcome) -> int:
    """Pick a uniformly-random pip face that represents `outcome` for `color`.

    The renderer calls this at settle time to decide which of the 1-6
    colored die sprites to show. The rules engine never calls this — the
    outcome is already known by the time a die lands.

    Args:
        color: The die's color (difficulty tier).
        outcome: The outcome the engine already resolved for this die.

    Returns:
        An integer in [1, 6] that maps to a pip face on the sprite sheet.
    """
    return random.choice(OUTCOME_FACE_NUMBERS[(color, outcome)])
