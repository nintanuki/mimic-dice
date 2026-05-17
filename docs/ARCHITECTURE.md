# Mimic Dice — Architecture

This document explains **how the Mimic Dice code is put together and why**. It is meant for anyone touching the code — human or AI. It deliberately skips things any Pygame project does (open a window, fill a background, flip the buffer) and focuses on the parts that are specific to this game.

> **Maintenance rule:** every pass that meaningfully changes a system must update the matching section here. Out-of-date architecture docs are worse than none.

---

## 1. The shape of the program

```
                           +-------------------+
                           |   main.py         |
                           |   GameManager     |   (thin coordinator)
                           +---------+---------+
                                     |
       +-----------------+-----------+-----------+-------------------+
       |                 |                       |                   |
       v                 v                       v                   v
   DiceRoller          CRT                Input handlers        (future:
   (systems/)        (crt.py)             (in GameManager)      rules engine,
       |                                                         UI screens,
   +---+----+                                                    AI players)
   |        |
   v        v
 DiceTray  AnimatedDie x N
```

`GameManager` is intentionally thin. Its only jobs are:

- own the Pygame display, clock, and connected controllers,
- drain the event queue and route each event to a small handler,
- call `update(dt)` and `draw(...)` on the systems it owns,
- handle global concerns like fullscreen toggle and the quit combo.

Anything that has its *own* state (dice, post-process, future UI screens, future rules engine) lives in its own class. `GameManager` stitches them together; it does not implement them.

---

## 2. The frame loop

Each frame, in order:

1. **Quit-combo check.** Held `Start + Back + L1 + R1` exits immediately, even outside the event queue.
2. **`_process_events`** drains `pygame.event.get()` and dispatches by event type to a handler (`_handle_keydown`, `_handle_joybuttondown`, etc.). Window resize events are forwarded to `DiceRoller.resize`.
3. **`_update_world`** computes `dt` from the previous tick and advances every system by that much real time. Using `dt` instead of "one step per frame" is what makes the dice physics frame-rate independent.
4. **`_render_frame`** paints the background, then the gameplay layer, then the CRT overlay on top.
5. **`pygame.display.flip()`** then **`clock.tick(FPS)`** caps the frame rate.

The `update` and `render` methods are split on purpose: physics is deterministic given `dt`, render is a pure function of state. That split is what will let us pause, rewind, or screenshot cleanly later.

---

## 3. The dice subsystem

The dice are the most game-specific code in the repo, and they are split across three classes that each own one job.

```
DiceRoller   ── orchestrates a roll. The only entry point GameManager touches.
   ├── DiceTray         ── the rectangular play area dice live inside.
   └── AnimatedDie x N  ── one physics body + animation per die.
```

### 3.1 `DiceRoller` — orchestration

`DiceRoller` is the only dice-related object `GameManager` knows about. It:

- loads the sprite sheet **once** at construction,
- slices out the **tumble row** (the shared white in-flight frames) and **three colored pip-face rows** (one per `DieColor`, each holding the 1-6 pip faces), with every row scaled up using `DiceSettings.SCALE`,
- builds a `face_sprites: dict[(DieColor, pip_face_number), Surface]` map and shares it across every `AnimatedDie` (every die holds a reference to the same `Surface` objects — no per-die copies),
- owns one `DiceTray`,
- forwards `update(dt)` to every die using the tray's *inner* rect as physics bounds, and `draw(surface)` by drawing the tray first then each die on top,
- exposes `roll_with_results(colors, outcomes)` for the rules engine to trigger a fresh throw with pre-resolved per-die state.

Sharing the frame lists is the reason adding more dice is essentially free in terms of memory.

### 3.2 `DiceTray` — bounded play area

The tray is a UI region. It owns:

- `rect` — the visible border rect, in window pixels, anchored to the top-left of the window with padding from `DiceSettings.TRAY_PADDING` and size from `DiceSettings.TRAY_SIZE`. Recomputed on every window resize.
- `inner_rect(margin)` — the same rect shrunk by `margin` pixels per side. This is what physics uses, so a die's half-width fits **inside** the visible border rather than overlapping it.
- `draw(surface)` — fills the felt and outlines the rounded border.

We deliberately use a tray, not a visualized bag. The bag is a data structure — it holds the remaining dice — but it is never drawn. In real life most players shake the bag (or cup) and dump dice into a tray; the tray model matches the physical experience without the animation cost.

### 3.3 `AnimatedDie` — one die's physics + animation

Each die has two visual states:

- **Rolling** — cycling through tumble frames; frame rate scales with current speed.
- **Settled** — a single face frame chosen randomly the moment the die comes to rest.

The physics model is intentionally simple but frame-rate independent.

**Position and velocity.** Each die holds a `pygame.Vector2` for position and one for velocity. Velocity is in **pixels per second**, so `position += velocity * dt` is the only integration step.

**Spawn.** When `roll(tray_rect)` is called, the die is placed *just outside* one of the tray corners (`DiceSettings.THROW_ORIGIN`, offset by `THROW_SPAWN_OFFSET`). It is then launched with:

- a random angle around `THROW_ANGLE_DEG ± THROW_ANGLE_SPREAD_DEG`, so dice fan out instead of stacking,
- a random speed in `[THROW_SPEED_MIN, THROW_SPEED_MAX]`,
- a random starting tumble frame so dice don't appear synchronized.

**Drag.** Velocity decays exponentially: each second `velocity *= exp(-LINEAR_DRAG)`. This is the textbook frame-rate-independent friction — a per-frame multiplier would make the dice slow down faster on faster machines.

**Wall reflection.** `_bounce_against_walls` clamps the die's center inside the inner rect and reflects velocity. There's a subtle but important detail: it uses `abs(velocity)` (and `-abs(...)` for the opposite wall), **not** plain negation. That means a die that spawned outside the wall is always pulled back in on its first contact, even if its velocity was already pointing away from that wall on that frame. Each bounce multiplies retained speed by `RESTITUTION` (< 1), so dice naturally lose energy.

**Tumble frame rate.** While rolling, the tumble animation FPS is interpolated linearly from `TUMBLE_FPS_MIN` (near settle speed) to `TUMBLE_FPS_MAX` (at peak throw speed). Fast dice visibly spin faster, slow dice wind down — same trick a real die does.

**Settle.** When `velocity.length()` drops below `SETTLE_SPEED`, the die stops, velocity is zeroed, and a pip-face sprite is chosen from `face_sprites[(pending_color, pip_face_number)]`. The pip number is drawn via `outcomes.face_for_outcome(color, outcome)` so the *visible number* on the rested die maps deterministically to what the die rolled (see §3.4). **The animation does not determine the outcome** — the outcome is decided by the rules engine before the throw and only revealed visually at settle.

### 3.4 Per-color dice (current state)

The dice subsystem ships the real Zombie Dice composition: 13 dice across three color tiers — 6 GREEN, 4 YELLOW, 3 RED. Each die belongs to a `DieColor` and resolves its outcome through the per-color face distribution defined in `systems/outcomes.py::FACE_DISTRIBUTIONS`:

| Color  | Count | TREASURE | EMPTY | MIMIC |
|--------|-------|----------|-------|-------|
| GREEN  | 6     | 3        | 2     | 1     |
| YELLOW | 4     | 2        | 2     | 2     |
| RED    | 3     | 1        | 2     | 3     |

Each rolled die renders as a colored 1-6 pip face from the single `six_sided_die.png` sheet. `AssetPaths.DIE_FACE_ROWS` picks one row per color (red row 2, green row 8, yellow row 10; 0-indexed from the top); `DiceRoller` slices the 1-6 faces from each row at startup into a shared `face_sprites: dict[(DieColor, pip_face_number), Surface]` map.

At settle time the renderer chooses *which* pip number to show via the per-color outcome→face mapping in `systems/outcomes.py::OUTCOME_FACE_NUMBERS`. The mapping is banded so low pips read as MIMIC and high pips read as TREASURE for every color, with the *width* of each band reflecting the color's difficulty tier:

| Color  | MIMIC pips | EMPTY pips | TREASURE pips |
|--------|------------|------------|---------------|
| GREEN  | 1          | 2-3        | 4-6           |
| YELLOW | 1-2        | 3-4        | 5-6           |
| RED    | 1-3        | 4-5        | 6             |

Each band's size matches the matching outcome count in `FACE_DISTRIBUTIONS` (green has 3 TREASUREs and 3 TREASURE pips, etc.), so picking a pip uniformly from a band is statistically identical to picking from the face distribution directly. The rules engine never reads `OUTCOME_FACE_NUMBERS`; it is purely a rendering layer that gives the player something to *read* on a settled die.

The tumble row stays on the original `six_sided_die.png` so every color shares the same in-air silhouette; the per-color art only resolves at settle time. The standalone `assets/graphics/sprites/{treasure,empty_chest,mimic}_{green,yellow,red}.png` PNGs that an earlier Phase 1 pass loaded for the felt are no longer referenced — they remain on disk for possible later use, but `AssetPaths` no longer maps them.

### 3.5 The Outcome + DieColor layer

`systems/outcomes.py` defines the seam between the dice subsystem and everything downstream of it. It exposes:

- `DieColor` — an `Enum` with members `GREEN`, `YELLOW`, `RED`. The string values (`"green"`, `"yellow"`, `"red"`) key directly into `AssetPaths.DIE_FACE_ROWS`.
- `Outcome` — an `Enum` with members `MIMIC`, `EMPTY`, `TREASURE`. Every rules-engine decision (bust, bank, hold-over, score) reads outcomes through this type.
- `FACE_DISTRIBUTIONS` — `dict[DieColor, tuple[Outcome, ...]]` of length-6 tuples, one per color. The engine resolves a roll by picking a uniformly-random index in [0, 5] from the tuple keyed by the die's color, which makes the per-color difficulty curve a one-line edit.
- `OUTCOME_FACE_NUMBERS` — `dict[(DieColor, Outcome), tuple[int, ...]]` of pip faces. Parallel to `FACE_DISTRIBUTIONS` but flipped: given an outcome, which 1-6 pips visually represent it on that color's die. Used by the renderer only.
- `roll_color(color)` — random `choice` over a color's face distribution (used by `TurnEngine.roll`).
- `face_for_outcome(color, outcome)` — random `choice` over a (color, outcome) pip set (used by `AnimatedDie._settle`).

These pieces live together (instead of split between `settings.py` and `outcomes.py`) so the dict literals can reference the enums without a circular import. Per-color *counts* (how many of each color in the bag) still live in `BagSettings.DICE_PER_COLOR`, which is where it is natural to tune them alongside `TOTAL_DICE`.

---

## 4. The CRT post-process

`crt.py` adds two effects on top of the rendered frame:

- a **TV-frame image** (`assets/graphics/effects/tv.png`) blitted at a random alpha each frame, in the range `ScreenSettings.CRT_ALPHA_RANGE`. The randomness produces the flicker.
- **horizontal scanlines** drawn on a copy of that image so the overlay does not accumulate between frames.

It's the **last** thing drawn, so scanlines sit on top of everything else. It is automatically skipped while the window is fullscreen (it would tile poorly at arbitrary resolutions) and while `DebugSettings.DISABLE_CRT` is set.

---

## 5. Settings as the only knob panel

`settings.py` is the single place every tunable lives. Each class groups one subsystem (`ScreenSettings`, `DiceSettings`, `InputSettings`, ...). The rest of the codebase imports from here and never hard-codes a number.

This matters for two reasons:

1. **No magic numbers.** A reviewer reading gameplay code never has to guess what `1.6` means; they look up `LINEAR_DRAG` in `settings.py` and read the comment.
2. **Designer-friendly.** Tuning feel — drag, restitution, throw angle, tumble FPS — is editing one file with comments next to each value, not hunting through implementation.

Adding a new tunable? Put it in `settings.py` with a comment explaining its **units** and what changing it does.

---

## 6. The asset pipeline

Sprite sheets are sliced through `utils/spritesheet.py` (`SpriteSheet.get_image`). The slicer is generic — it takes raw pixel coordinates and an optional integer scale. Game-specific layout (which row is the face row, how big a tile is, how many frames in the tumble row) lives in `AssetPaths` so callers never reference raw sheet geometry directly.

When you add a new sheet:

1. Drop the file in `assets/graphics/sprites/`.
2. Add its path and layout constants (tile size, row indexes, frame counts) to `AssetPaths`.
3. Slice it in the system that uses it via `SpriteSheet(path).get_image(...)`.

---

## 7. Input model

Two parallel input paths share the same handlers:

- **Keyboard** events come in as `KEYDOWN` and route through `_handle_keydown`.
- **Controller** events come in as `JOYBUTTONDOWN`, `JOYHATMOTION`, `JOYAXISMOTION` and route through their respective handlers.

Two cross-cutting behaviors are global and intentionally fall through every other handler:

- **Fullscreen toggle.** `F11` on keyboard, `Back` on controller.
- **Quit combo.** `Start + Back + L1 + R1` held on any connected controller exits immediately. It's checked **both** at the top of every frame (for held-state quits) and inside `_handle_joybuttondown` (for instant response on press).

Connected controllers are cached once in `setup_controllers` so the per-frame quit-combo check is just `joystick.get_button(...)` calls — no enumeration overhead.

---

## 8. Code conventions worth knowing

Most rules live in [.github/copilot-instructions.md](../.github/copilot-instructions.md). Two are worth surfacing here because they shape how files **look**:

**Section banners.** Inside any file with multiple logical groupings, sections are separated by an all-caps banner comment:

```python
    # -------------------------
    # SECTION NAME
    # -------------------------
```

This is what `main.py`, `dice_roller.py`, and `dice_tray.py` already use. Keep it consistent: matching length, all caps, name describes the role of the methods that follow.

**Function order inside a class.** Functions are grouped by role (setup, actions, physics, render, etc.). `update` and `run` go **last** and should only call other functions on the class — they are coordinators, not implementations.

---

---

## 9. The rules engine

The rules engine is split across two modules that each own one job.

```
systems/bag.py        — the 13-die draw pool
systems/turn_engine.py — per-turn state: hold-overs, bust, bank, win
```

`GameManager` owns one `Bag` and one `TurnEngine`. It calls `start_turn()` at the top of every turn and `roll()` / `bank()` in response to player input.

### 9.1 `Bag` — the draw pool

`Bag` is now a list of `DieColor` values (not an integer counter) because dice are no longer mechanically identical — every die has a color, and that color drives both the outcome distribution and the settled sprite. Its interface:

- `reset()` — refills to `BagSettings.DICE_PER_COLOR` (6 GREEN + 4 YELLOW + 3 RED = 13) and shuffles. Called once per turn by `TurnEngine.start_turn()`.
- `draw(n)` — removes up to *n* dice from the pool and returns their colors. The caller (`TurnEngine`) runs `roll_color` on each to resolve the outcome.
- `recycle(set_aside_colors, set_aside_outcomes)` — puts TREASURE-outcome dice from the set-aside pile back into the pool, preserving their colors. Called automatically by `TurnEngine.roll()` when the bag cannot supply the needed dice mid-turn.
- `count_color(color)` — returns how many dice of `color` remain. Used by AI strategies (Lizzie in particular) to gauge bust risk hiding inside the bag.

The bag is never drawn. It is a data structure — players reach into it conceptually each time they choose to roll.

### 9.2 `TurnEngine` — per-turn state machine

`TurnEngine` manages one player's turn from first draw to bust or bank. Key state:

- `turn_mimics` / `turn_treasures` — running totals for this turn.
- `held_over_colors` — list of `DieColor` for EMPTY dice in hand that carry into the next roll (not returned to the bag). Held-over dice keep their color when re-rolled because a die's color is a property of the *die*, not of the roll; only the face outcome is fresh on each push.
- `set_aside_colors` / `set_aside_outcomes` — parallel lists of every MIMIC + TREASURE die set aside so far this turn. `Bag.recycle()` reads both for the mid-turn TREASURE refill, and the stats panel reads them for the held-dice thumbs.
- `status` — a `TurnStatus` enum: `ROLLING`, `BUST`, or `BANKED`.
- `red_dice_remaining()` — derived helper: `bag.count_color(RED) + held_over_colors.count(RED)`. The Lizzie bot reads this to decide whether to push through "all the reds are already out, so the bust risk has been spent."

`roll()` flow:

1. Compute `dice_needed = DICE_PER_ROLL − held_over` (length of `held_over_colors`).
2. If `bag.count < dice_needed`, call `bag.recycle(self.set_aside_colors, self.set_aside_outcomes)` first.
3. Collect colors: `all_colors = held_over_colors + bag.draw(dice_needed)` (held-overs keep their color).
4. Resolve outcomes: `all_outcomes = [roll_color(color) for color in all_colors]`.
5. Classify into set-aside / held / mimic-count: MIMIC → increment counter + append color/outcome to set-aside; TREASURE → same; EMPTY → append color to new `held_over_colors`.
6. Check bust: if `turn_mimics >= BUST_THRESHOLD`, set `status = BUST`.
7. Return a `RollResult` dataclass with parallel `colors` + `outcomes` lists and all running totals.

`bank()` commits `turn_treasures` to the caller's score and sets `status = BANKED`.

### 9.3 Color- and outcome-driven settle art + on-felt persistence

`TurnEngine.roll()` returns a `RollResult` whose `colors` and `outcomes` are parallel lists ordered so that held-over dice come first and freshly-drawn dice follow. `GameManager._do_roll()` calls `dice_roller.roll_with_results(colors, outcomes)`, which re-throws the felt's current held-over EMPTY dice with the leading entries of the lists and **appends new `AnimatedDie` instances** for any remaining (color, outcome) pairs. Dice that settled as MIMIC or TREASURE on a previous roll are left alone — they stay on the felt as the player's set-aside pile until `clear_for_new_turn()` is called on bank or bust. This mirrors physical Zombie Dice: brains/shotguns pile up on the table; footsteps are the only thing you re-roll.

When a die settles, `AnimatedDie._settle()` asks `outcomes.face_for_outcome(pending_color, pending_outcome)` for a pip face number in [1, 6] and renders the matching sprite from `face_sprites[(pending_color, pip_face_number)]`. The pip mapping is banded per color (see §3.4): on a green die a TREASURE shows pips 4-6, on a red die TREASURE shows only pip 6, etc. — so the *number on the die* is a legible cue for what just happened, and the *color of the die* is the cue for how risky it was. Mid-tumble frames stay on the shared white tumble row of `six_sided_die.png` so every color looks the same in flight; the color and pip number reveal together at settle.

### 9.4 Stats panel

`ui/stats_panel.py::StatsPanel` paints the right-side column every frame from data passed in by `GameManager`: the **roster** of players (human + bots) with their banked scores, and the **set-aside outcomes** for the currently-active player's turn. The active player's row gets the active marker (`>`) and a highlight color. Treasure thumbs and mimic thumbs render on separate labeled rows; both rows reset on `TurnEngine.start_turn()` (bank or bust), while banked scores persist on each `Player` until the next game.

The right-side icons are deliberately **color-agnostic**. The panel loads three flat sprites from `AssetPaths.FLAT_OUTCOME_SPRITES` (`mimic.png`, `empty_chest.png`, `treasure.png`) and renders one thumb per set-aside outcome regardless of which color die produced it. A banked green TREASURE and a banked red TREASURE both show the same treasure icon. The color story belongs to the felt; the panel focuses on counts.

### 9.5 Win condition (Phase 0 stub)

The first player to bank enough treasure to reach `TurnSettings.WIN_SCORE` (13) triggers the final round. Phase 0 logs a WIN message and resets immediately; the full final-round rotation (every other player gets one more turn) is wired up as part of the Phase 0 Game Flow tasks.

### 9.6 Players, rotation, and bots

`GameManager.players` is the ordered seat list: a `Player` per seat with `name`, optional `bot`, and `score`. Phase 0 seats one human plus the names listed in `BotSettings.DEFAULT_BOT_NAMES` (`("ALICE", "BOB")`). `_current_player_index` rotates each time a turn ends.

Bots live in `systems/bots.py`. Each `Bot` is a `(name, strategy)` pair where `strategy(context: BotContext) -> BotDecision`. The single `BotContext` dataclass (treasures, mimics, red-dice-remaining) is what lets a newer color-aware bot like Lizzie read more state without breaking existing strategies that only care about counts. The strategy is consulted *after* each roll settles — never mid-tumble — and is shielded from busted states because `TurnEngine` flips status to `BUST` before the bot ever sees the post-roll counts. The current roster is Alice (bank at 2 mimics), Bob (bank at 2 treasures), and Lizzie (tracks remaining red dice; banks at the `BotSettings.LIZZIE_*` thresholds unless every red die is already out, in which case she keeps pushing). Legacy bots in `legacy/zombie-dice-bots/` remain reference-only and are not imported.

Bot pacing lives entirely in `GameManager._tick_bot`. After each roll settles or a turn ends, the `_bot_action_timer` is set to one of two values from `BotSettings` (`AFTER_ROLL_DELAY_S`, `END_OF_TURN_DELAY_S`). The same timer gates both bot decisions and post-turn advancement, so the loop reads naturally for human turns too (when there's no decision to make, only the post-turn advance ever fires).

---

## 10. What's *not* here yet

The following systems will get their own sections in this document as they're built. If you're implementing one of these, please add the section as part of your pass:

- AI player adapter (wraps the bots in `legacy/zombie-dice-bots/` to use our dice + rules).
- UI screens (title, lobby, stats panel content, win screen).
- Audio system.
