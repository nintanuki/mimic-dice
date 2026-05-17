"""AI opponents — stand-ins for the legacy bot personalities.

The legacy bots in `legacy/zombie-dice-bots/my_zombie.py` use a synchronous
turn loop (`while diceRollResults is not None: ...`) that doesn't fit our
real-time pygame loop. Phase 0 reshaped the interface into a single
per-roll decision so `GameManager` can drive bots the same way it drives a
human (one input per frame).

The roster keeps the spirit (not the code) of the legacy bots, picked
because each line of logic is one-line readable:
  * Alice  — "stop exactly at 2 mimics, no more, no less."
  * Bob    — "don't stop until 2 treasures."
  * Lizzie — "the gambler": tracks how many red dice are still in play and
             keeps pushing whenever the bust risk has already been spent.

Add more by writing a `Strategy = Callable[[BotContext], BotDecision]`
and attaching it to a `Bot`. The shared `BotContext` is what lets newer
personalities (e.g. Lizzie) read color-aware state without breaking
older strategies that only care about treasure / mimic counts.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Callable

from settings import BotSettings


class BotDecision(Enum):
    """Whether the bot wants to roll again or bank."""

    ROLL = "ROLL"
    BANK = "BANK"


@dataclass(frozen=True)
class BotContext:
    """Snapshot of the live turn passed to a strategy after every roll.

    Strategies receive a single context object (instead of a long argument
    list) so adding a new state field for a future bot does not break the
    signature of every existing one. Older bots simply ignore the fields
    they do not care about.

    Attributes:
        turn_treasures:      TREASUREs accumulated so far this turn.
        turn_mimics:         MIMICs accumulated so far this turn.
        red_dice_remaining:  Red dice still in play this turn (unseen in
                             the bag plus any held-over reds about to be
                             re-rolled). Used by Lizzie to gauge bust risk.
    """

    turn_treasures: int
    turn_mimics: int
    red_dice_remaining: int


# A strategy maps a `BotContext` to a decision. The bot is only consulted
# *after* a roll has settled, never mid-tumble; the bust check
# (`turn_mimics >= BUST_THRESHOLD`) is already handled by `TurnEngine`
# before the strategy sees the state.
Strategy = Callable[[BotContext], BotDecision]


@dataclass(frozen=True)
class Bot:
    """A named AI opponent and the strategy that drives it."""

    name: str
    strategy: Strategy

    def decide(self, context: BotContext) -> BotDecision:
        """Pick ROLL or BANK based on the post-roll state.

        Args:
            context: Snapshot of the live turn (treasure / mimic counts
                     plus color-aware fields like `red_dice_remaining`).
        Returns:
            ROLL to push the player's luck again; BANK to lock in the
            current `turn_treasures` and end the turn.
        """
        return self.strategy(context)


# -------------------------
# STRATEGIES
# -------------------------


def alice_strategy(context: BotContext) -> BotDecision:
    """Alice — "stop exactly at 2 mimics".

    Alice ignores treasure entirely. She keeps rolling until she's sitting
    on 2 mimics, then banks whatever treasure she has so the third mimic
    doesn't bust her.
    """
    return BotDecision.BANK if context.turn_mimics >= 2 else BotDecision.ROLL


def bob_strategy(context: BotContext) -> BotDecision:
    """Bob — "don't stop until 2 treasures".

    Bob is stubborn: he refuses to bank until he has at least 2 treasures,
    even if he's already on 2 mimics. He busts a lot. (In the legacy bot
    table he wins 0.63% of games — a good sparring partner, not a threat.)
    """
    return BotDecision.BANK if context.turn_treasures >= 2 else BotDecision.ROLL


def lizzie_strategy(context: BotContext) -> BotDecision:
    """Lizzie — "the gambler", tracks remaining red dice.

    Lizzie banks at two greed thresholds (mirrors the legacy Lizzie):
      * mimics >= 1 AND treasures >= LIZZIE_BANK_AT_ONE_MIMIC_TREASURE
      * mimics >= 2 AND treasures >= LIZZIE_BANK_AT_TWO_MIMICS_TREASURE
    Otherwise she keeps rolling. The clever bit: when every red die has
    already been drawn (none left in the bag or held over), the bust risk
    for the rest of the turn drops sharply, so she pushes regardless of
    the thresholds above. That same "statistically safe" instinct is
    what drops her from Hard into Medium tier — sometimes the remaining
    greens / purples still bust her.
    """
    if context.red_dice_remaining == 0:
        return BotDecision.ROLL
    if (
        context.turn_mimics >= 1
        and context.turn_treasures >= BotSettings.LIZZIE_BANK_AT_ONE_MIMIC_TREASURE
    ):
        return BotDecision.BANK
    if (
        context.turn_mimics >= 2
        and context.turn_treasures >= BotSettings.LIZZIE_BANK_AT_TWO_MIMICS_TREASURE
    ):
        return BotDecision.BANK
    return BotDecision.ROLL


# -------------------------
# FACTORY
# -------------------------


_STRATEGY_BY_NAME: dict[str, Strategy] = {
    "ALICE":  alice_strategy,
    "BOB":    bob_strategy,
    "LIZZIE": lizzie_strategy,
}


def make_bot(name: str) -> Bot:
    """Build a `Bot` by looking the personality up by ALL-CAPS name.

    Unknown names fall back to Alice — a deliberately tame default so a
    typo in settings doesn't crash boot.
    """
    strategy = _STRATEGY_BY_NAME.get(name, alice_strategy)
    return Bot(name=name, strategy=strategy)
