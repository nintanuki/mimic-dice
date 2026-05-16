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
- slices out the **face row** (settled poses, indexes 0–5 = faces 1–6) and the **tumble row** (mid-air spinning poses), with both rows scaled up using `DiceSettings.SCALE`,
- creates `DiceSettings.COUNT` `AnimatedDie` instances and **shares** those frame lists with all of them (every die holds a reference to the same `Surface` objects — no per-die copies),
- owns one `DiceTray`,
- forwards `update(dt)` to every die using the tray's *inner* rect as physics bounds, and `draw(surface)` by drawing the tray first then each die on top,
- exposes `roll_all()` for the game to trigger a fresh throw.

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

**Settle.** When `velocity.length()` drops below `SETTLE_SPEED`, the die stops, velocity is zeroed, and a random `face_index` is picked from the face row. **The animation does not determine the outcome** — the outcome is decided at settle time. That's an important design choice for the future: when we wire up the real rules engine, the engine will pre-decide each die's outcome and we'll just inject that into `face_index` at settle, instead of `random.randrange`.

### 3.4 Current placeholder behavior

Right now the sheet contains a generic 1–6 numbered six-sided die. Mimic Dice ultimately needs three colored dice with treasure/empty-chest/mimic faces in different distributions. The roadmap takes that in two steps:

- **Phase 0** introduces an `Outcome` layer (`MIMIC` / `EMPTY` / `TREASURE`) and a `face_to_outcome` map (1-2 → MIMIC, 3-4 → EMPTY, 5-6 → TREASURE). All dice in Phase 0 are mechanically identical (equal 1/3 odds for each outcome), but each rolled die is rendered using the sprite-sheet row that matches its outcome — row 3 (red) for MIMIC, row 2 (grey) for EMPTY, row 9 (green) for TREASURE — so the player can read the outcome at a glance without changing the underlying probabilities. The bag (13 dice) and re-roll mechanics are implemented during Phase 0 even though every die is statistically identical, so Phase 1 only needs to change the contents of the bag, not the engine that uses it.
- **Phase 1** replaces Phase 0's equal-odds bag with the real Zombie Dice distribution (6 green / 4 yellow / 3 red dice with per-color face distributions) and reintroduces Lizzie, who was held out of Phase 0 because her strategy depends on red-dice counts.
- **Phase 3** replaces the placeholder number art entirely with treasure/empty-chest/mimic icons.

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

## 9. What's *not* here yet

The following systems will get their own sections in this document as they're built. If you're implementing one of these, please add the section as part of your pass:

- Rules engine (turn state, cup, draw-3, bust, bank, win condition).
- AI player adapter (wraps the bots in `legacy/zombie-dice-bots/` to use our dice + rules).
- UI screens (title, lobby, in-game HUD, win screen).
- Audio system.
