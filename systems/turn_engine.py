"""Turn engine: bag draws, hold-overs, bust detection, banking, and win condition.

One `TurnEngine` instance is shared across all players' turns; call
`start_turn()` at the top of each player's turn to reset per-turn state
while preserving the shared `Bag`.

Mimic Dice turn sequence
------------------------
1. `start_turn()` — resets counters and refills the bag.
2. `roll()` — draws dice to bring the hand to 3 (held-over EMPTY dice count
   toward the 3; only the shortfall is drawn from the bag).  Returns a
   `RollResult` describing every die's outcome, the running totals, and
   whether the player busted.
3. Repeat step 2 as long as `can_roll` is True and the player chooses to
   keep going.
4. `bank()` — commits `turn_treasures` to the caller's score; marks the turn
   done.  Returns the number of treasures banked.

Terminology (Zombie Dice → Mimic Dice):
    brains    → TREASURE
    footsteps → EMPTY  (held over)
    shotguns  → MIMIC  (bust risk)

Win condition:
    The first player to reach `TurnSettings.WIN_SCORE` triggers a final
    round: every *other* player gets exactly one more turn, then the
    player with the highest total wins.  `TurnEngine` tracks the
    `trigger_player_index` (set when a bank pushes a score to WIN_SCORE)
    so `GameManager` knows when the final round begins and ends.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from enum import Enum

from settings import TurnSettings
from systems.bag import Bag
from systems.outcomes import Outcome, face_to_outcome


# -------------------------
# RESULT TYPES
# -------------------------


class TurnStatus(Enum):
    """The current lifecycle state of a player's turn."""

    ROLLING = "ROLLING"   # Player may roll again or bank.
    BUST    = "BUST"      # 3+ mimics accumulated; turn ends, 0 treasures scored.
    BANKED  = "BANKED"    # Player chose to bank; turn_treasures committed.


@dataclass
class RollResult:
    """Everything the caller needs to know about one roll within a turn.

    ``faces`` and ``outcomes`` are parallel lists ordered held-over dice
    (re-rolled) first, freshly-drawn dice after. Carrying both means the
    animated dice can show the *same* face value that produced their
    outcome (face 1 → MIMIC, face 5 → TREASURE under the Phase 0
    threshold map), so the visible pips never disagree with the log.
    """

    faces: list[int]           # One face value (1–6) per die this roll.
    outcomes: list[Outcome]    # Matching Outcome per face this roll.
    status: TurnStatus         # Turn state after resolving this roll.
    turn_mimics: int           # Running mimic count for this turn.
    turn_treasures: int        # Running treasure count for this turn.
    held_over: int             # EMPTY dice carried into the *next* roll.


# -------------------------
# ENGINE
# -------------------------


class TurnEngine:
    """Manages one player's turn from first draw to bust or bank.

    The engine owns the bag reference; callers create one bag and pass it in
    so all players share the same object across the game.

    Args:
        bag: The shared dice bag. `start_turn()` calls `bag.reset()` at the
             top of every turn so each player always starts with 13 dice.
    """

    def __init__(self, bag: Bag) -> None:
        self.bag = bag
        self.status = TurnStatus.ROLLING
        self.turn_mimics: int = 0
        self.turn_treasures: int = 0
        self.held_over: int = 0         # EMPTY dice in-hand from the last roll.
        # MIMIC + TREASURE set-aside from every roll this turn, in roll order.
        # The stats panel reads this to draw the held-dice thumbs, and the bag
        # uses it for the mid-turn TREASURE recycle.
        self.set_aside_faces: list[int] = []
        self.set_aside_outcomes: list[Outcome] = []

    # -------------------------
    # SETUP
    # -------------------------

    def start_turn(self) -> None:
        """Reset per-turn counters and refill the bag for a new player's turn."""
        self.bag.reset()
        self.status = TurnStatus.ROLLING
        self.turn_mimics = 0
        self.turn_treasures = 0
        self.held_over = 0
        self.set_aside_faces = []
        self.set_aside_outcomes = []

    # -------------------------
    # QUERIES
    # -------------------------

    @property
    def can_roll(self) -> bool:
        """True while the player is still in the ROLLING state."""
        return self.status == TurnStatus.ROLLING

    # -------------------------
    # ACTIONS
    # -------------------------

    def roll(self) -> RollResult:
        """Execute one roll: re-roll held-over EMPTY dice and draw fresh ones.

        The hand is always brought to `TurnSettings.DICE_PER_ROLL` (3) dice:
        held-over EMPTY dice count toward that total, and the shortfall is
        drawn from the bag.  If the bag cannot supply the shortfall, the
        mid-turn recycle fires first (TREASURE set-asides go back into the
        bag) before drawing.

        Held-over EMPTY dice get a brand-new face / outcome each roll
        (they are re-rolled, not carried as EMPTY again automatically).

        Returns:
            A `RollResult` with per-die faces *and* outcomes (parallel
            lists), running totals, and the turn's new status. Both lists
            are ordered: held-over dice first, then freshly-drawn dice.
        """
        dice_needed = TurnSettings.DICE_PER_ROLL - self.held_over

        # Mid-turn bag refill: if the bag can't supply the needed dice,
        # recycle TREASURE set-asides back into the bag before drawing.
        if self.bag.count < dice_needed:
            self.bag.recycle(self.set_aside_outcomes)

        # Resolve held-over EMPTY dice — each gets a completely fresh face.
        held_faces: list[int] = [
            random.randint(1, 6) for _ in range(self.held_over)
        ]

        # Draw fresh dice from the bag (may be fewer than dice_needed if the
        # bag is still short even after recycling).
        fresh_faces: list[int] = self.bag.draw(dice_needed)

        all_faces: list[int] = held_faces + fresh_faces
        all_outcomes: list[Outcome] = [face_to_outcome(face) for face in all_faces]

        # Classify results and update running totals.
        new_held = 0
        for face, outcome in zip(all_faces, all_outcomes):
            if outcome == Outcome.MIMIC:
                self.turn_mimics += 1
                self.set_aside_faces.append(face)
                self.set_aside_outcomes.append(outcome)
            elif outcome == Outcome.TREASURE:
                self.turn_treasures += 1
                self.set_aside_faces.append(face)
                self.set_aside_outcomes.append(outcome)
            else:  # EMPTY: stay in hand for the next roll.
                new_held += 1

        self.held_over = new_held

        # Bust check: 3 or more mimics ends the turn with 0 scored treasure.
        if self.turn_mimics >= TurnSettings.BUST_THRESHOLD:
            self.status = TurnStatus.BUST

        return RollResult(
            faces=all_faces,
            outcomes=all_outcomes,
            status=self.status,
            turn_mimics=self.turn_mimics,
            turn_treasures=self.turn_treasures,
            held_over=self.held_over,
        )

    def bank(self) -> int:
        """Commit this turn's treasure to the caller's score and end the turn.

        Should only be called when `can_roll` is True (i.e., in ROLLING
        state).  Calling it after a bust is a no-op (returns 0).

        Returns:
            The number of TREASURE outcomes accumulated this turn that are
            now added to the player's total score.
        """
        if self.status != TurnStatus.ROLLING:
            return 0
        self.status = TurnStatus.BANKED
        return self.turn_treasures
