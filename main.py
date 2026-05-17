from __future__ import annotations

import pygame
import sys
from dataclasses import dataclass
from typing import Optional

from systems.bag import Bag
from systems.bots import Bot, BotContext, BotDecision, make_bot
from systems.dice_roller import DiceRoller
from systems.outcomes import Outcome
from systems.turn_engine import TurnEngine, TurnStatus
from ui import layout
from ui.message_log import MessageLog
from ui.stats_panel import PlayerView, StatsPanel
from crt import CRT
from settings import (
    ScreenSettings,
    InputSettings,
    ColorSettings,
    DebugSettings,
    LayoutSettings,
    MessageLogSettings,
    StatsPanelSettings,
    BotSettings,
    TurnSettings,
)


# -------------------------
# PLAYER MODEL
# -------------------------


@dataclass
class Player:
    """A seat at the table — either the human or a bot personality.

    `bot is None` means this seat is the human. Score persists across
    every turn; per-turn state lives in the shared `TurnEngine`.
    """

    name: str
    bot: Optional[Bot]
    score: int = 0

    @property
    def is_human(self) -> bool:
        """True for the lone human seat in Phase 0."""
        return self.bot is None


class GameManager:
    """Coordinate game state, flow, rendering phases, and input orchestration."""

    def __init__(self, start_fullscreen: bool = False):
        """Initialize the game, including pygame subsystems, window, and all game systems.

        Args:
            start_fullscreen: Whether to launch directly in fullscreen mode.
        """

        pygame.init()
        self.screen = pygame.display.set_mode(
            ScreenSettings.RESOLUTION, pygame.RESIZABLE
        )
        pygame.display.set_caption(ScreenSettings.TITLE)
        if start_fullscreen:
            pygame.display.toggle_fullscreen()
        self.clock = pygame.time.Clock()

        self.setup_controllers()

        # -------- Dice --------
        self.dice_roller = DiceRoller(self.screen.get_size())

        # -------- Rules engine --------
        self._bag = Bag()
        self._turn_engine = TurnEngine(self._bag)
        # Simple flag: has any bank push crossed WIN_SCORE yet this game?
        self._final_round_triggered: bool = False

        # -------- Players --------
        # Phase 0 seats one human plus the bots listed in BotSettings; the
        # roster is fixed for the life of one game. Phase 2's lobby will
        # let the player configure this.
        self.players: list[Player] = [
            Player(name=StatsPanelSettings.HUMAN_PLAYER_NAME, bot=None),
        ] + [
            Player(name=name, bot=make_bot(name))
            for name in BotSettings.DEFAULT_BOT_NAMES
        ]
        self._current_player_index: int = 0

        # -------- Turn state --------
        # _waiting_for_roll: dice are still in flight after a roll() call.
        # We wait until all dice settle before accepting the next input.
        self._waiting_for_roll: bool = False
        # Set by _do_roll; read by _on_dice_settled.
        self._last_roll_result = None
        # Countdown (seconds) gating the next bot action so the human has
        # time to read what just happened. Negative = ready to act.
        self._bot_action_timer: float = 0.0
        # True between a bust/bank and the corresponding `_advance_to_next_turn`
        # firing, so the pacing tick advances the turn instead of consulting
        # the bot strategy.
        self._turn_ending: bool = False
        # Bumped on every turn change so the panel can announce who is up.
        self._announced_current_player: int = -1

        # -------- UI panels --------
        self.message_log = MessageLog()
        self.stats_panel = StatsPanel(self.dice_roller.settled_sprites)

        # -------- Post-processing --------
        self.full_screen = False
        self.crt = CRT(self.screen)

        # Start the first turn and greet the player.
        self._turn_engine.start_turn()
        self.message_log.add_message(MessageLogSettings.WELCOME_LINE)
        self._announce_current_player()

    # -------------------------
    # BOOT / SETUP
    # -------------------------

    def setup_controllers(self) -> None:
        """Cache currently-connected controllers so quit-combo and event polling are cheap."""
        pygame.joystick.init()
        self.connected_joysticks = [
            pygame.joystick.Joystick(index)
            for index in range(pygame.joystick.get_count())
        ]

    def reset_game(self):
        """
        Restart the game by replacing the current GameManager instance
        with a brand new one.

        This is safer than trying to manually reset every subsystem,
        because it reuses the same startup path the game already uses
        when it first launches.
        """
        current_surface = pygame.display.get_surface()
        was_fullscreen = bool(current_surface and (current_surface.get_flags() & pygame.FULLSCREEN))

        new_game_manager = GameManager(start_fullscreen=was_fullscreen)
        new_game_manager.run()
        sys.exit()

    def close_game(self) -> None:
        """Close the game process cleanly."""
        pygame.quit()
        sys.exit()

    def quit_combo_pressed(self) -> bool:
        """Return True if START + SELECT + L1 + R1 are held on any controller."""
        required_buttons = InputSettings.JOY_BUTTON_QUIT_COMBO
        for joystick in self.connected_joysticks:
            if all(joystick.get_button(button) for button in required_buttons):
                return True
        return False

    # -------------------------
    # PLAYER ROTATION
    # -------------------------

    @property
    def _current_player(self) -> Player:
        """The player whose turn is currently active."""
        return self.players[self._current_player_index]

    def _announce_current_player(self) -> None:
        """Log who's up — once per turn change."""
        if self._announced_current_player == self._current_player_index:
            return
        player = self._current_player
        self.message_log.add_message(f"{player.name}'S TURN.")
        self._announced_current_player = self._current_player_index
        # Reset bot pacing so the new bot doesn't act on its first frame.
        self._bot_action_timer = BotSettings.AFTER_ROLL_DELAY_S

    def _advance_to_next_turn(self) -> None:
        """Clear the felt, rotate players, and start the new player's turn."""
        self.dice_roller.clear_for_new_turn()
        self._current_player_index = (
            (self._current_player_index + 1) % len(self.players)
        )
        self._turn_engine.start_turn()
        self._announce_current_player()

    # -------------------------
    # TURN LOGIC
    # -------------------------

    def _do_roll(self) -> None:
        """Ask the engine to roll, then animate the dice with the pre-decided results.

        Held-over EMPTY dice on the felt re-throw; fresh draws append as new
        dice (see `DiceRoller.roll_with_results`).
        """
        if self._waiting_for_roll:
            return
        if not self._turn_engine.can_roll:
            return

        result = self._turn_engine.roll()
        self.dice_roller.roll_with_results(
            list(result.colors), list(result.outcomes)
        )
        self._waiting_for_roll = True
        self._last_roll_result = result

    def _on_dice_settled(self) -> None:
        """Called the first frame all dice settle after a roll.

        Logs the roll result and reacts to bust. Running totals live in the
        stats panel, so the log only carries events (roll / bust / bank /
        win / turn change).
        """
        result = self._last_roll_result
        self._waiting_for_roll = False

        # Build a readable summary of this roll. Held-overs that re-rolled
        # plus any fresh draws all show up here.
        mimic_count    = result.outcomes.count(Outcome.MIMIC)
        treasure_count = result.outcomes.count(Outcome.TREASURE)
        empty_count    = result.outcomes.count(Outcome.EMPTY)

        parts: list[str] = []
        if mimic_count:
            parts.append(f"{mimic_count} MIMIC{'S' if mimic_count > 1 else ''}")
        if treasure_count:
            parts.append(f"{treasure_count} TREASURE")
        if empty_count:
            parts.append(f"{empty_count} EMPTY")
        roll_summary = ",  ".join(parts) if parts else "NOTHING"
        self.message_log.add_message(f"ROLLED: {roll_summary}")

        if result.status == TurnStatus.BUST:
            self.message_log.add_message(
                f"BUST!  {result.turn_mimics} MIMICS.  "
                f"{self._current_player.name} SCORES 0."
            )
            self._end_turn_after_delay()
            return

        # Roll resolved cleanly. Start (or reset) the bot pacing timer so
        # the bot waits a beat before its next decision; human turns just
        # leave this idle.
        self._bot_action_timer = BotSettings.AFTER_ROLL_DELAY_S

    def _do_bank(self) -> None:
        """Bank the current turn's treasure for the active player.

        Ignored if dice are still rolling, the turn is already over, or the
        player hasn't rolled yet this turn.
        """
        if self._waiting_for_roll:
            return
        if not self._turn_engine.can_roll:
            return
        if (
            self._turn_engine.turn_treasures == 0
            and self._turn_engine.turn_mimics == 0
        ):
            # Player hasn't rolled yet this turn — nothing to bank.
            self.message_log.add_message("ROLL FIRST!")
            return

        player = self._current_player
        banked = self._turn_engine.bank()
        player.score += banked
        self.message_log.add_message(
            f"{player.name} BANKED {banked} TREASURE.  TOTAL: {player.score}"
        )

        # Win condition: first to WIN_SCORE triggers the final round.
        # Phase 0 still ships a stub: announce the win and reset all
        # scores. The proper final-round rotation lands with the rest of
        # the Phase 0 Game-Flow tasks.
        if player.score >= TurnSettings.WIN_SCORE and not self._final_round_triggered:
            self._final_round_triggered = True
            self.message_log.add_message(
                f"{player.name} WINS!  REACHED {TurnSettings.WIN_SCORE} TREASURE."
            )
            for seat in self.players:
                seat.score = 0
            self._final_round_triggered = False

        self._end_turn_after_delay()

    def _end_turn_after_delay(self) -> None:
        """Queue an `_advance_to_next_turn()` for after the end-of-turn beat.

        Setting the bot timer to the end-of-turn delay works whether the
        outgoing turn was a bot's or the human's: the next-turn logic in
        `_update_world` ticks the timer down and fires the advance.
        """
        self._bot_action_timer = BotSettings.END_OF_TURN_DELAY_S
        # Flag the engine so `_update_world` knows to advance, not to
        # consult the bot's strategy.
        self._turn_ending = True

    # -------------------------
    # BOT DRIVER
    # -------------------------

    def _tick_bot(self, dt: float) -> None:
        """Advance the bot pacing timer and act when it expires.

        Runs every frame. Three cases gate the call to the bot strategy:
          * dice are still rolling → wait,
          * the turn just ended (bust / bank) → fire `_advance_to_next_turn`,
          * the timer hasn't expired yet → just decrement.
        """
        if self._waiting_for_roll:
            return
        self._bot_action_timer -= dt
        if self._bot_action_timer > 0:
            return

        # End-of-turn advance has priority over consulting a bot strategy
        # (this branch also fires after a *human* bank/bust, which is why
        # the timer is shared rather than bot-only).
        if self._turn_ending:
            self._turn_ending = False
            self._advance_to_next_turn()
            return

        player = self._current_player
        if player.is_human:
            return  # Humans drive input directly; no auto-action.

        decision = player.bot.decide(
            BotContext(
                turn_treasures=self._turn_engine.turn_treasures,
                turn_mimics=self._turn_engine.turn_mimics,
                red_dice_remaining=self._turn_engine.red_dice_remaining(),
            )
        )
        if decision is BotDecision.ROLL:
            self._do_roll()
        else:
            self._do_bank()

    # -------------------------
    # INPUT HANDLING
    # -------------------------

    def _handle_keydown(self, event) -> None:
        """Route one keyboard press to the appropriate UI/gameplay handler.

        Inputs are ignored while a bot is acting so a stray keypress
        doesn't roll on the bot's behalf.
        """
        # F11 fullscreen toggle is global.
        if event.key == pygame.K_F11:
            pygame.display.toggle_fullscreen()
            self.full_screen = not self.full_screen

        if not self._current_player.is_human:
            return

        # Roll.
        if event.key == pygame.K_SPACE:
            self._do_roll()

        # Bank (A or Enter).
        if event.key in (pygame.K_a, pygame.K_RETURN):
            self._do_bank()

    def _handle_joybuttondown(self, event) -> None:
        """Route one controller button press."""
        if self.quit_combo_pressed():
            self.close_game()

        # Back is the global fullscreen toggle.
        if event.button == InputSettings.JOY_BUTTON_BACK:
            pygame.display.toggle_fullscreen()
            self.full_screen = not self.full_screen

        if not self._current_player.is_human:
            return

        # A button: bank.
        if event.button == InputSettings.JOY_BUTTON_A:
            self._do_bank()

        # B button: roll.
        if event.button == InputSettings.JOY_BUTTON_B:
            self._do_roll()

    def _handle_joyhatmotion(self, event) -> None:
        """Route a D-pad direction event."""
        pass

    def _handle_joyaxismotion(self, event) -> None:
        """Route a joystick or trigger motion event."""
        pass

    def _process_events(self) -> None:
        """Drain pygame's event queue and dispatch by event type."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.close_game()
            elif event.type == pygame.VIDEORESIZE:
                self.dice_roller.resize((event.width, event.height))
            elif event.type == pygame.KEYDOWN:
                self._handle_keydown(event)
            elif event.type == pygame.JOYBUTTONDOWN:
                self._handle_joybuttondown(event)
            elif event.type == pygame.JOYHATMOTION:
                self._handle_joyhatmotion(event)
            elif event.type == pygame.JOYAXISMOTION:
                self._handle_joyaxismotion(event)

    # -------------------------
    # MAIN LOOP
    # -------------------------

    def _update_world(self) -> None:
        """Advance every gameplay system by one frame."""
        dt = self.clock.get_time() / 1000.0
        self.dice_roller.update(dt)
        self.message_log.update()

        # Detect when all dice have finished rolling after a triggered roll.
        if self._waiting_for_roll and self.dice_roller.all_settled:
            self._on_dice_settled()

        # Tick pacing for either bot decisions or post-turn cleanup.
        self._tick_bot(dt)

    def _draw_panel_frames(self) -> None:
        """Draw the message log frame.

        The stats panel paints its own frame and contents in `_render_frame`;
        the log frame is drawn here so the log text can blit on top of it
        cleanly.
        """
        window_size = self.screen.get_size()
        log_rect = layout.message_log_rect(window_size)

        pygame.draw.rect(
            self.screen,
            ColorSettings.PANEL_FILL_COLOR,
            log_rect,
            border_radius=LayoutSettings.PANEL_BORDER_RADIUS,
        )
        pygame.draw.rect(
            self.screen,
            ColorSettings.PANEL_BORDER_COLOR,
            log_rect,
            width=LayoutSettings.PANEL_BORDER_WIDTH,
            border_radius=LayoutSettings.PANEL_BORDER_RADIUS,
        )

    def _render_frame(self) -> None:
        """Composite one frame: background, gameplay, UI panels, then CRT overlay."""
        self.screen.fill(ColorSettings.BG_COLOR)

        self.dice_roller.draw(self.screen)
        self._draw_panel_frames()

        window_size = self.screen.get_size()
        log_rect = layout.message_log_rect(window_size)
        stats_rect = layout.stats_panel_rect(window_size)
        self.message_log.draw(self.screen, log_rect)
        self.stats_panel.draw(
            self.screen,
            stats_rect,
            players=[
                PlayerView(name=p.name, score=p.score) for p in self.players
            ],
            active_player_index=self._current_player_index,
            set_aside_colors=self._turn_engine.set_aside_colors,
            set_aside_outcomes=self._turn_engine.set_aside_outcomes,
        )

        if not self.full_screen and not DebugSettings.DISABLE_CRT:
            self.crt.draw()

    def run(self):
        """Run the main game loop until the player quits."""
        while True:
            if self.quit_combo_pressed():
                self.close_game()
            self._process_events()
            self._update_world()
            self._render_frame()
            pygame.display.flip()
            self.clock.tick(ScreenSettings.FPS)


if __name__ == "__main__":
    game_manager = GameManager()
    game_manager.run()
