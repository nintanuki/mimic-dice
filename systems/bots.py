"""AI opponents — Phase 0 stand-ins for the legacy bot personalities.

The legacy bots in `legacy/zombie-dice-bots/my_zombie.py` use a synchronous
turn loop (`while diceRollResults is not None: ...`) that doesn't fit our
real-time pygame loop. Phase 0 keeps the personalities but reshapes the
interface into a single per-roll decision so `GameManager` can drive bots
the same way it drives a human (one input per frame).

The Phase 0 strategies match the spirit (not the code) of two
easy-tier legacy bots, picked because their logic is one-line readable:
  * Alice  — "stop exactly at 2 mimics, no more, no less."
  * Bob    — "don't stop until 2 treasures."

Add more by writing a `Strategy = Callable[[int, int], BotDecision]` and
attaching it to a `Bot`. Phase 1 will fold in Lizzie once colored dice
exist and her red-counting logic actually makes sense.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Callable


class BotDecision(Enum):
    """Whether the bot wants to roll again or bank."""

    ROLL = "ROLL"
    BANK = "BANK"


# A strategy maps (turn_treasures, turn_mimics) to a decision. The bot is
# only consulted *after* a roll has settled, never mid-tumble; that means
# the bust check (`turn_mimics >= BUST_THRESHOLD`) is already handled by
# `TurnEngine` before the strategy sees the state.
Strategy = Callable[[int, int], BotDecision]


@dataclass(frozen=True)
class Bot:
    """A named AI opponent and the strategy that drives it."""

    name: str
    strategy: Strategy

    def decide(self, turn_treasures: int, turn_mimics: int) -> BotDecision:
        """Pick ROLL or BANK based on the post-roll state.

        Args:
            turn_treasures: TREASUREs accumulated so far on this turn.
            turn_mimics:    MIMICs accumulated so far on this turn.
        Returns:
            ROLL to push the player's luck again; BANK to lock in the
            current `turn_treasures` and end the turn.
        """
        return self.strategy(turn_treasures, turn_mimics)


# -------------------------
# STRATEGIES
# -------------------------


def alice_strategy(turn_treasures: int, turn_mimics: int) -> BotDecision:
    """Alice — "stop exactly at 2 mimics".

    Alice ignores treasure entirely. She keeps rolling until she's sitting
    on 2 mimics, then banks whatever treasure she has so the third mimic
    doesn't bust her.
    """
    del turn_treasures  # Alice doesn't care about treasure.
    return BotDecision.BANK if turn_mimics >= 2 else BotDecision.ROLL


def bob_strategy(turn_treasures: int, turn_mimics: int) -> BotDecision:
    """Bob — "don't stop until 2 treasures".

    Bob is stubborn: he refuses to bank until he has at least 2 treasures,
    even if he's already on 2 mimics. He busts a lot. (In the legacy bot
    table he wins 0.63% of games — a good sparring partner, not a threat.)
    """
    del turn_mimics  # Bob doesn't care about mimics.
    return BotDecision.BANK if turn_treasures >= 2 else BotDecision.ROLL


# -------------------------
# FACTORY
# -------------------------


_STRATEGY_BY_NAME: dict[str, Strategy] = {
    "ALICE": alice_strategy,
    "BOB":   bob_strategy,
}


def make_bot(name: str) -> Bot:
    """Build a `Bot` by looking the personality up by ALL-CAPS name.

    Unknown names fall back to Alice — a deliberately tame default so a
    typo in settings doesn't crash boot.
    """
    strategy = _STRATEGY_BY_NAME.get(name, alice_strategy)
    return Bot(name=name, strategy=strategy)
