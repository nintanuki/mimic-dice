# Mimic Dice — Roadmap

This file tracks work in **phases**. Each phase has a clear goal; finish a phase before moving on. Items inside a phase can move between phases as priorities shift, but Phase 1 is intentionally minimal — *get to a playable game first, then refine.*

---

## Phase 1 — Playable Prototype

**Goal:** A complete, end-to-end game of Mimic Dice that follows the official Zombie Dice rules using the existing 1–6 number-faced dice as placeholders. One human player versus AI opponents. Ugly is fine; it must be playable from start to win screen.

### Rules engine
- [ ] Build the 13-die cup with the correct color distribution (6 green, 4 yellow, 3 red).
- [ ] Draw 3 dice per roll; replenish drawn-from-runners back to 3 each subsequent roll.
- [ ] Map each color's face distribution to roll outcomes (brain / runner / shotgun).
- [ ] Track per-turn brains and per-turn shotguns; bust at 3 shotguns.
- [ ] Bank action commits per-turn brains to the player's score.
- [ ] Win condition: first to 13 brains triggers a final round; highest score after the round wins.

### Visual placeholder mapping
- [ ] Temporarily map the existing 6-sided number dice to Zombie Dice outcomes (e.g. 1–3 = brain, 4 = shotgun, 5–6 = runner per the green-die distribution) so the engine has something to render against. Document the mapping in `ARCHITECTURE.md` so it is obvious that this is placeholder behavior.

### AI opponents
- [ ] Port the bots in `legacy/zombie-dice-bots/` into the live game so 1 human can play against 1–3 AI.
- [ ] Add a turn-flow controller that alternates between human and AI players and waits on AI "thinking" time so rolls are visible.

### Minimum UI
- [ ] Display whose turn it is.
- [ ] Display each player's banked score.
- [ ] Display this turn's running brains and shotguns.
- [ ] Roll / Bank prompts.
- [ ] Win screen with restart prompt.

### Input
- [ ] Bind Roll and Bank to keyboard and controller.
- [ ] Keep the existing global fullscreen toggle and quit combo.

---

## Phase 2 — Multiplayer & Game Flow

**Goal:** Up to 4 mixed human / AI players with proper turn order, lobby, and scoreboard.

- [ ] 1–4 player support. Decide hot-seat vs. shared-controller (see Open Questions).
- [ ] Pre-game lobby: pick number of players, assign each slot human or AI, pick AI personality from `legacy/zombie-dice-bots/`.
- [ ] Persistent scoreboard widget visible during play.
- [ ] Final-round logic when a player reaches 13 brains (every other player gets one more turn).
- [ ] Tie-break rule (rolls until tied players differ, per Zombie Dice convention).

---

## Phase 3 — Theming & Assets

**Goal:** Replace placeholder visuals with the treasure / mimic theme.

- [ ] Final dice art: treasure chest (brain), empty chest (runner), mimic (shotgun) on green/yellow/red dice bodies.
- [ ] Update `assets/graphics/sprites/six_sided_die.png` (or replace with new sheets) and refresh sheet-layout constants in `AssetPaths`.
- [ ] Tray reskin: dungeon table / treasure-room aesthetic.
- [ ] Background art and per-player avatar / character portraits for AI personalities.
- [ ] Refresh `assets/graphics/sprites/attributions.md` with new sources.

---

## Phase 4 — Audio & Feel

**Goal:** Make the game feel alive.

- [ ] Dice impact / tumble / settle SFX.
- [ ] Mimic snarl on shotgun outcome; chest creak on brain.
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
- **Drawing animation.** A literal cup is hard to depict; the tray-only model is intentional for this build (mirrors how the physical game is actually played: shake the cup, dump into a tray). Documented in `ARCHITECTURE.md`.
- **AI pacing.** Bots resolve a turn instantly; we'll need an artificial delay between AI rolls so the player can see what happened.
- **Re-roll mechanics.** Runners must persist across rolls within a turn while drawing fresh dice from the cup to bring the count back to 3. The data model for "dice in play this turn" needs to handle that cleanly.

---

## Documentation maintenance

Every phase pass must:

1. Update `docs/ARCHITECTURE.md` to reflect any system that changed shape.
2. Append entries to `docs/CHANGELOG.md` per the format in that file.
3. Move completed items here from `[ ]` to `[x]` (do not delete — leave as a record).