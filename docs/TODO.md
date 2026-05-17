# Mimic Dice — Roadmap

This file tracks work in **phases**. Each phase has a clear goal; finish a phase before moving on. Items inside a phase can move between phases as priorities shift, but Phase 0 is intentionally minimal — *get to a playable game first, then refine.*

---

## Phase 0 — Bare-Bones Playable

**Goal:** A complete, end-to-end game of Mimic Dice with simplified dice (all dice are mechanically identical, equal 1/3-1/3-1/3 odds) so the engine, UI, AI integration, and game loop all land before any color-distribution work begins. One human plus 3 random AI bots, full Zombie Dice rules otherwise, 1-6 number-faced dice rendered in red/grey/green by outcome. Lizzie sits out this phase because she needs real color variety to make decisions; she returns unchanged in Phase 1.

### Rules engine
- [x] Add `Outcome` constants (MIMIC / EMPTY / TREASURE) and a `face_to_outcome(face)` map: faces 1-2 → MIMIC, 3-4 → EMPTY, 5-6 → TREASURE.
- [x] Model a 13-die identical bag; draw 3 dice per roll; hold over empty-chest dice from the previous roll (they take their fresh outcome on the next roll) and refill from the bag to bring the hand back to 3.
- [x] When the bag empties mid-turn, recycle set-aside treasure chests back into the bag (not mimics).
- [x] Track per-turn treasure and per-turn mimics; bust at 3 mimics; bank action commits per-turn treasure to score.
- [x] Win condition: first to 13 treasure triggers a final round; highest score after the round wins.

### Visual placeholder mapping
- [x] Render each rolled die using the sprite sheet row that matches its outcome: MIMIC → row 3 (red), EMPTY → row 2 (grey), TREASURE → row 9 (green). All dice still have equal odds; the color is purely a readability cue.

### AI opponents
- [x] Copy the bots from `legacy/zombie-dice-bots/` into `systems/bots/` and adapt them to drive our engine (no edits to `legacy/`). *(Phase 0 ships two — Alice and Bob — reimplemented in `systems/bots.py` as a `decide(t, m) -> BotDecision` interface. The rest of the legacy roster lands when more personalities are needed.)*
- [x] Provide a thin adapter that gives each bot the same `roll()` dict shape it expects (`brains`, `shotgun`, `footsteps`, `rolls`), backed by our bag and outcomes. *(Replaced by the simpler per-decision interface above; legacy dict-shaped adapter is no longer needed.)*
- [x] Exclude Lizzie for Phase 0 (her strategy reads red-dice count, which is meaningless without real color variation).
- [x] Bot pacing delay so the player can see each AI roll resolve. *(`BotSettings.AFTER_ROLL_DELAY_S` / `END_OF_TURN_DELAY_S`, ticked by `GameManager._tick_bot`.)*

### UI windows
- [ ] Tall thin **stats panel** on the right: player names, scores, current-turn indicator, timer/round counter, bot difficulty icons (`aku.png` skulls for difficulty tier, `lau.png` flower for tutorial). *(Multi-player roster + active-turn `>` marker + per-player score + active-player held-dice rows are in. Timer / round counter / `aku.png` skulls and `lau.png` flowers are not yet drawn.)*
- [x] Wide **message log** on the bottom with a typewriter reveal ported from Dungeon Digger.
- [x] Wire log to game events: rolls, MIMIC, BUST, BANK, turn changes, WIN. (Bot turn changes land with the AI adapter.)

### Game flow
- [ ] New-game setup picks the human plus 3 random non-Lizzie bots. Lineup re-rolls each new game. *(Current setup is fixed: human + Alice + Bob from `BotSettings.DEFAULT_BOT_NAMES`. Random 3-bot lineup lands when the bot roster grows past two.)*
- [x] Game loop: turn rotation, roll/bank inputs for the human, automatic turns for bots.
- [ ] GAME OVER screen showing final scores; press A or ENTER to start a fresh random game. No other prompts.

### Smoke test + doc updates
- [ ] Walk through a full game start → win/lose → restart. Note anything off here.
- [ ] Update `ARCHITECTURE.md` with new sections (rules engine, AI adapter, UI panels, message log).
- [ ] Append `CHANGELOG.md` entries per the doc-maintenance rule.

---

## Phase 1 — Color-Distribution Dice

**Goal:** Replace the 1/3-1/3-1/3 placeholder bag from Phase 0 with the real Zombie Dice bag: 13 dice across three color tiers with different face distributions, and reintroduce Lizzie.

### Rules engine
- [x] Build the 13-die bag with the correct color distribution (6 green, 4 purple, 3 red). *(Purple replaces Zombie Dice's yellow body color; counts live in `BagSettings.DICE_PER_COLOR`.)*
- [x] Draw 3 dice per roll; replenish drawn-from-empty-chest holdovers back to 3 each subsequent roll, drawing fresh dice from the bag. *(Already shipped in Phase 0; held-overs now keep their original color across re-rolls.)*
- [x] Map each color's face distribution to roll outcomes (treasure / empty chest / mimic). *(See `systems/outcomes.py::FACE_DISTRIBUTIONS` — green 3/2/1, purple 2/2/2, red 1/2/3.)*
- [x] Track per-turn treasure and per-turn mimics; bust at 3 mimics.
- [x] Bank action commits per-turn treasure to the player's score.
- [x] Win condition: first to 13 treasure triggers a final round; highest score after the round wins.

### Visual placeholder mapping
- [x] Temporarily map the existing 6-sided number dice to Zombie Dice outcomes per-color so the engine has something to render against. *(Skipped — the new per-color chest / mimic / treasure PNGs landed in this pass, so the engine renders final art directly. Phase 3's "Final dice art" item is therefore already done as a side-effect.)*

### AI opponents
- [x] Reintroduce Lizzie (she was sat out for Phase 0 because her strategy depends on red-dice counts). *(`lizzie_strategy` in `systems/bots.py`, fed by `TurnEngine.red_dice_remaining()` through the new `BotContext`.)*

### Minimum UI
- [ ] Display this turn's running treasure and mimics (extends the stats panel built in Phase 0).

### Input
- [ ] Bind Roll and Bank to keyboard and controller.
- [ ] Keep the existing global fullscreen toggle and quit combo.

---

## Phase 2 — Multiplayer & Game Flow

**Goal:** Up to 4 mixed human / AI players with proper turn order, lobby, and scoreboard.

- [ ] 1–4 player support. Decide hot-seat vs. shared-controller (see Open Questions).
- [ ] Pre-game lobby: pick number of players, assign each slot human or AI, pick AI personality from the in-game bot roster.
- [ ] Persistent scoreboard widget visible during play.
- [ ] Final-round logic when a player reaches 13 treasure (every other player gets one more turn).
- [ ] Tie-break rule (rolls until tied players differ, per Zombie Dice convention).

---

## Phase 3 — Theming & Assets

**Goal:** Replace placeholder visuals with the treasure / mimic theme.

- [x] Final dice art: treasure chest, empty chest, mimic icons on green / purple / red dice bodies. *(Twelve standalone PNGs landed during the Phase 1 colored-bag pass; tumble row still comes from the original `six_sided_die.png` for the rolling animation.)*
- [x] Update `assets/graphics/sprites/six_sided_die.png` (or replace with new sheets) and refresh sheet-layout constants in `AssetPaths`. *(Sheet kept as the tumble-row source only; settled-art paths now live in `AssetPaths.SETTLED_SPRITES`.)*
- [ ] Tray reskin: dungeon table / treasure-room aesthetic.
- [ ] Background art and per-player avatar / character portraits for AI personalities.
- [ ] Refresh `assets/graphics/sprites/attributions.md` with new sources.

---

## Phase 4 — Audio & Feel

**Goal:** Make the game feel alive.

- [ ] Dice impact / tumble / settle SFX.
- [ ] Mimic snarl on mimic outcome; chest creak on treasure.
- [ ] Bank / bust stings.
- [ ] Background music tracks (lobby, gameplay, win).
- [ ] Screen shake on bust.
- [ ] Per-die settle "thud" timing tied to the physics settle event.

---

## Phase 5 — Polish

**Goal:** Make it feel like a real arcade cabinet game.

- [ ] Title screen and attract mode (idle demo loop).
- [ ] Settings screen (volume, CRT toggle, controller config).
- [ ] Smooth transitions between screens.
- [ ] Tune `DiceSettings` (drag, restitution, throw spread) to taste.
- [ ] Tune CRT overlay to look great on the cabinet's actual display.
- [ ] Ensure all UI text remains ALL CAPS (project rule).

---

## Phase 6 — Cabinet Integration

**Goal:** Ship into the arcade launcher.

- [ ] Hook into the Arcade Launcher manifest.
- [ ] Verify quit-combo (`Start + Back + L1 + R1`) returns control cleanly.
- [ ] Verify fullscreen behavior on the cabinet display.
- [ ] Smoke test full game from launcher cold-boot to win screen.

---

## Open Questions / Known Challenges

- **Multi-human input on one cabinet.** Hot-seat (one controller, pass it) vs. multi-controller (each player has their own). Defer until Phase 2.
- **AI pacing.** Bots resolve a turn instantly; we'll need an artificial delay between AI rolls so the player can see what happened.
- **Re-roll mechanics.** Empty-chest dice must persist across rolls within a turn while drawing fresh dice from the bag to bring the count back to 3. The data model for "dice in play this turn" needs to handle that cleanly.

Note: the bag is intentionally not visualized — it is a data structure, not a sprite. Players reach into the bag conceptually each time they choose to roll.

---

## Documentation maintenance

Every phase pass must:

1. Update `docs/ARCHITECTURE.md` to reflect any system that changed shape.
2. Append entries to `docs/CHANGELOG.md` per the format in that file.
3. Move completed items here from `[ ]` to `[x]` (do not delete — leave as a record).