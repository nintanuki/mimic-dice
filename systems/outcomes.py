"""The Outcome type and the face -> Outcome mapping used by the rules engine.

Mimic Dice resolves every settled die into one of three outcomes:

    MIMIC    - bust risk; three on a turn ends the turn with zero score.
    EMPTY    - the die persists into the next roll for that turn.
    TREASURE - banked as score when the player chooses to stop.

The shipping game will resolve those outcomes from per-color face
distributions on three different dice. Phase 0 ships a simpler model so
the engine, UI, AI bots, and full game loop can land first: a single
equal-odds 1-6 face die, with the two-step threshold mapping defined in
`settings.OutcomeSettings`.

This module is the seam between the dice subsystem (which still settles
on integer faces) and the rules engine (which only cares about
outcomes). Phase 1 keeps `Outcome` exactly as-is but replaces
`face_to_outcome` with a per-color distribution lookup; nothing
downstream of this seam should need to change.
"""

from enum import Enum

from settings import OutcomeSettings


# -------------------------
# OUTCOME TYPE
# -------------------------


class Outcome(Enum):
    """The three possible results of a single settled die."""

    MIMIC = "MIMIC"
    EMPTY = "EMPTY"
    TREASURE = "TREASURE"


# -------------------------
# FACE -> OUTCOME MAPPING
# -------------------------


def face_to_outcome(face: int) -> Outcome:
    """Map a 1-6 settled face to its Phase 0 placeholder outcome.

    The thresholds live in `settings.OutcomeSettings` so the equal-odds
    split (1-2 / 3-4 / 5-6) can be tuned without editing this function.

    Args:
        face: The settled face shown on the die, 1-based in [1, 6].

    Returns:
        The Outcome enum value that `face` resolves to.
    """
    if face <= OutcomeSettings.MIMIC_FACE_MAX:
        return Outcome.MIMIC
    if face <= OutcomeSettings.EMPTY_FACE_MAX:
        return Outcome.EMPTY
    return Outcome.TREASURE
