from __future__ import annotations

import pygame
import sys

from systems.bag import Bag
from systems.dice_roller import DiceRoller
from systems.outcomes import Outcome
from systems.turn_engine import TurnEngine, TurnStatus
from ui import layout
from ui.message_log import MessageLog
from ui.stats_panel import StatsPanel
from crt import CRT
from settings import (
    ScreenSettings,
    InputSettings,
    ColorSettings,
    DebugSettings,
    LayoutSettings,
    MessageLogSettings,
    StatsPanelSettings,
    TurnSettings,
)


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
        self._player_score: int = 0
        # Simple flag: has a bank push crossed WIN_SCORE yet?
        self._final_round_triggered: bool = False

        # -------- Turn state --------
        # waiting_for_roll: player pressed SPACE; dice are still in flight.
        # We wait until all dice settle before accepting another SPACE or a
        # BANK so the log has something concrete to report.
        self._waiting_for_roll: bool = False
        # Populated by _do_roll; read by _on_dice_settled once all dice rest.
        self._last_roll_result = None

        # -------- UI panels --------
        self.message_log = MessageLog()
        self.stats_panel = StatsPanel(self.dice_roller.outcome_sprites)

        # -------- Post-processing --------
        self.full_screen = False
        self.crt = CRT(self.screen)

        # Start the first turn and greet the player. The log owns its own
        # opening line; we don't echo it here so the welcome only appears
        # once.
        self._turn_engine.start_turn()
        self.message_log.add_message(MessageLogSettings.WELCOME_LINE)

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
    # TURN LOGIC
    # -------------------------

    def _do_roll(self) -> None:
        """Ask the engine to roll, then throw the dice with the pre-decided results.

        Called when SPACE is pressed and the turn is still in ROLLING state.
        All dice are animated; the turn result is processed once they settle.
        """
        if not self._turn_engine.can_roll:
            return

        result = self._turn_engine.roll()

        # Pad the lists to DiceSettings.COUNT so `roll_with_results` always
        # gets exactly COUNT pairs (extra dice render as EMPTY filler at
        # face 3, which is a neutral EMPTY-mapped pip count).
        faces = list(result.faces)
        outcomes = list(result.outcomes)
        while len(faces) < 3:
            faces.append(3)
            outcomes.append(Outcome.EMPTY)

        self.dice_roller.roll_with_results(faces, outcomes)
        self._waiting_for_roll = True
        self._last_roll_result = result

    def _on_dice_settled(self) -> None:
        """Called the first frame all dice settle after a roll.

        Logs the roll result and checks for bust. Running totals live in the
        stats panel now, so the log focuses on events: the roll itself and
        any state change (bust / bank / win).
        """
        result = self._last_roll_result
        self._waiting_for_roll = False

        # Build a readable summary of this roll.
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
                f"BUST!  {result.turn_mimics} MIMICS.  SCORE: {self._player_score}"
            )
            self._turn_engine.start_turn()

    def _do_bank(self) -> None:
        """Bank the current turn's treasure.

        Ignored if dice are still rolling, the turn is already over, or the
        player hasn't rolled yet this turn.
        """
        if self._waiting_for_roll:
            return
        if not self._turn_engine.can_roll:
            return
        if self._turn_engine.turn_treasures == 0 and self._turn_engine.turn_mimics == 0:
            # Player hasn't rolled yet this turn — nothing to bank.
            self.message_log.add_message("ROLL FIRST!")
            return

        banked = self._turn_engine.bank()
        self._player_score += banked
        self.message_log.add_message(
            f"BANKED {banked} TREASURE.  TOTAL: {self._player_score}"
        )

        # Win condition: first to WIN_SCORE triggers the final round.
        # Phase 0 has no other players to give a final turn to, so for now
        # we celebrate the win and reset; Phase 0 Game-Flow will replace
        # this stub with the proper final-round logic.
        if self._player_score >= TurnSettings.WIN_SCORE and not self._final_round_triggered:
            self._final_round_triggered = True
            self.message_log.add_message(
                f"WIN!  REACHED {TurnSettings.WIN_SCORE} TREASURE."
            )
            self._turn_engine.start_turn()
            self._player_score = 0
            self._final_round_triggered = False
            return

        self._turn_engine.start_turn()

    # -------------------------
    # INPUT HANDLING
    # -------------------------

    def _handle_keydown(self, event) -> None:
        """Route one keyboard press to the appropriate UI/gameplay handler."""
        # F11 fullscreen toggle is global.
        if event.key == pygame.K_F11:
            pygame.display.toggle_fullscreen()
            self.full_screen = not self.full_screen

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
            player_name=StatsPanelSettings.HUMAN_PLAYER_NAME,
            score=self._player_score,
            set_aside_faces=self._turn_engine.set_aside_faces,
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
