# Change Log

This file is an append-only record of every code change made to Mimic Dice
by a human, AI assistant, or copilot tool. Read it before making changes so you know the current state of the codebase.

## Format

Each entry covers one logical change (which may touch multiple files). Use the
template below, with one `**File:** ... **Why:** ...` block per file touched.

    ## YYYY-MM-DD HH:MM — short summary

    **File:** path/to/file.py
    **Lines (at time of edit):** 38-52 (modified)
    **Before:**
        [old code]
    **After:**
        [new code]
    **Why:** explanation

## Conventions

* Line numbers reflect the file as it existed at the moment of the edit. Edits
  above shift line numbers below, so older entries will not match the current
  file. Never go back and "fix" old line numbers.
* Entries are append-only. Never delete history. If a later edit reverts an
  earlier one, write a new entry that references the original.
* For new files, write `(new file)` instead of a line range. The "Before"
  block can be omitted or marked `(file did not exist)`.
* For deletes, write `(deleted)` and put the removed code in "Before" with no
  "After" block.
* Keep "Before" / "After" blocks short. If a change is huge, summarize with a
  diff-style excerpt of the most important lines plus a sentence describing the
  rest, instead of pasting the entire file.
* New Entries should be BELOW this line, do not add new log entries to the top. These instructions must stay on top.

---

## 2026-05-07 18:20 -04:00 — Physics-driven dice roll with bounded tray

**File:** systems/dice_tray.py
**Lines (at time of edit):** (new file)
**Before:** (file did not exist)
**After:** New `DiceTray` class owning a `pygame.Rect` anchored top-left via
`DiceSettings.TRAY_PADDING`/`TRAY_SIZE`, with `resize()`, `inner_rect()`, and
`draw()` for the visible border.
**Why:** The tray needed to be a discrete UI region so the rest of the window
could host other HUD elements later, and so dice physics had a single source
of truth for bounds.

**File:** systems/die.py
**Lines (at time of edit):** 1-160 (rewritten)
**Before:** Lerp from `HAND_Y_POS` straight up to a fixed target with random
face flicker; no physics, no tumble frames, no bounds awareness.
**After:** 2D physics body with `pos`/`vel`, `roll(tray_rect)` that spawns
just outside the configured tray corner and launches with a random
angle/speed in the configured spread, exponential drag, AABB wall reflection
with restitution, speed-scaled tumble-frame cycling, and settle-on-low-speed
that picks a random face from the face row.
**Why:** The previous animation looked unnatural; the rewrite gives each die
independent trajectory, in-tray bouncing, the bottom-row tumble animation,
and a settled face from the top row, all driven by `settings.py` constants.

**File:** systems/dice_manager.py
**Lines (at time of edit):** 1-70 (rewritten)
**Before:** Spaced 3 dice horizontally at fixed `(x, TABLE_CENTER_Y)` targets
and only loaded the face row of the sprite sheet.
**After:** Owns a `DiceTray`, loads both face row (`AssetPaths.DICE_FACE_ROW`)
and tumble row (`AssetPaths.DICE_TUMBLE_ROW`), constructs `DiceSettings.COUNT`
dice, exposes `resize()` for window changes, and feeds `tray.inner_rect(...)`
to each die's update for tray-relative collisions.
**Why:** `DiceManager` is now the single point of contact between
`GameManager` and the dice systems, per the architecture rules.

**File:** settings.py
**Lines (at time of edit):** 14-22, 65-103
**Before:** `ScreenSettings` carried dead dice constants (`DICE_Y_POS`,
`DICE_SCALE`, `TABLE_CENTER_Y`, `HAND_Y_POS`); `AssetPaths` only knew about
the face tile size.
**After:** Added `ScreenSettings.UI_BORDER_WIDTH`, removed dead constants,
extended `AssetPaths` with `DICE_FACE_ROW`/`DICE_TUMBLE_ROW`/
`DICE_TUMBLE_FRAME_COUNT`, and added a new `DiceSettings` class covering
`COUNT`, `SCALE`, tray padding/size/border, throw origin/angle/spread/speed,
linear drag/restitution/settle threshold, and tumble FPS range.
**Why:** Centralizes every dice-related knob in one place so size, position,
direction, and physics can all be tuned without code edits.

**File:** utils/spritesheet.py
**Lines (at time of edit):** 1-2, 30-34
**Before:** Imported `ScreenSettings` and scaled output by
`ScreenSettings.DICE_SCALE`.
**After:** Imports `DiceSettings` and scales by `DiceSettings.SCALE`.
**Why:** `DICE_SCALE` belongs with the rest of the dice knobs in
`DiceSettings`.

**File:** main.py
**Lines (at time of edit):** 22-32, 116-130
**Before:** Created the display with `pygame.SCALED`, instantiated
`DiceManager()` with no args, and the event loop ignored `VIDEORESIZE`.
**After:** Switched to `pygame.RESIZABLE`, passes `self.screen.get_size()`
to `DiceManager`, and forwards `VIDEORESIZE` events to
`DiceManager.resize(...)`.
**Why:** The user wants to move/resize the window and have the tray (and
dice) follow.
## 2026-05-07 18:47 -04:00 � Dice subsystem refactor: roles, naming, settings, no magic numbers

**File:** settings.py
**Lines (at time of edit):** 1-160 (rewritten)
**Before:** Inline numeric defaults for CRT scanline width (`1`), no tray
corner radius, no tray fill color; `AssetPaths` mixed `DIE_SIZE` /
`DICE_FACE_ROW` / `DICE_TUMBLE_ROW` / `DICE_TUMBLE_FRAME_COUNT` with
file paths under inconsistent names; only `WHITE`/`NERO` were available
as named colors; module-level docstring was missing.
**After:** Full module docstring; `ColorSettings` split into a raw palette
(adds `LIGHT_GREY`, `VELVET_GREEN`, `MAROON`) and role aliases
(`TRAY_BORDER_COLOR`, `TRAY_FILL_COLOR`); `ScreenSettings` adds
`CRT_SCANLINE_LINE_WIDTH`; `AssetPaths` renamed sheet-layout constants
to `DIE_TILE_SIZE`/`DIE_FACE_ROW`/`DIE_TUMBLE_ROW`/`DIE_FACE_COUNT`/
`DIE_TUMBLE_FRAME_COUNT` with explanatory comments; `DiceSettings` adds
`TRAY_CORNER_RADIUS = 8` and a header comment describing how
`DiceRoller` / `DiceTray` / `AnimatedDie` cooperate; every constant
has an inline comment explaining its meaning.
**Why:** User asked for zero magic numbers, role-based color naming, a
configurable corner radius, a tray fill color, and clear cross-class
documentation.

**File:** utils/spritesheet.py
**Lines (at time of edit):** 1-50 (rewritten)
**Before:** `SpriteSheet.get_image` imported `DiceSettings` and always
multiplied output dimensions by `DiceSettings.SCALE`.
**After:** Module docstring added; `get_image` takes an explicit
`scale: int = 1` argument and no longer imports `DiceSettings`.
**Why:** A generic sprite-sheet utility should not know about the dice
subsystem; callers now pass the scale they want.

**File:** systems/dice_tray.py
**Lines (at time of edit):** 1-85 (rewritten)
**Before:** Single-letter local names (`win_w`, `win_h`, `pad_x`,
`pad_y`, `max_w`, `max_h`, `w`, `h`); only drew the border
outline; no module docstring.
**After:** Module docstring describes the tray's role and how it fits
between `DiceRoller` and `AnimatedDie`; locals renamed to
`window_width`/`window_height`/`padding_x`/`padding_y`/
`max_width`/`max_height`/`tray_width`/`tray_height`;
`draw()` now paints `ColorSettings.TRAY_FILL_COLOR` first and the
border on top with `DiceSettings.TRAY_CORNER_RADIUS` rounding.
**Why:** Readability and the user-requested rounded, filled tray look.

**File:** systems/animated_die.py
**Lines (at time of edit):** (new file)
**Before:** Logic lived in `systems/die.py` under class `Die`.
**After:** New file containing class `AnimatedDie` with module docstring
explaining its role (single die's physics + animation + sprite) and the
two non-obvious bits of math (frame-rate-independent exponential drag, and
absolute-value wall reflection so a die spawned outside the tray is pulled
in). Locals renamed: `self.pos` -> `self.position`, `self.vel` ->
`self.velocity`, `half` -> `half_size`, `decay` -> `drag_decay`,
`corners` -> `corner_positions`, `t` -> `speed_ratio`,
`speed_max` -> `peak_speed`; `_bounce_against` renamed to
`_bounce_against_walls`; sprite-sheet layout reads from the new
`DIE_FACE_COUNT`/`DIE_TUMBLE_FRAME_COUNT` constants.
**Why:** `Die` did not describe what the class does; `AnimatedDie`
makes the role obvious. Variable rename pass per the user's request to
eliminate single-letter names.

**File:** systems/die.py
**Lines (at time of edit):** (deleted)
**Before:** Held the previous `Die` class.
**After:** (removed)
**Why:** Replaced by `systems/animated_die.py`.

**File:** systems/dice_roller.py
**Lines (at time of edit):** (new file)
**Before:** Logic lived in `systems/dice_manager.py` under class
`DiceManager`.
**After:** New file containing class `DiceRoller` with module docstring
explaining that this is the only entry point `GameManager` uses to talk
to the dice subsystem. `_load_row` renamed to `_load_sheet_row`; loop
variable `i` renamed to `column_index`; passes
`DiceSettings.SCALE` explicitly to `SpriteSheet.get_image`.
**Why:** `DiceManager` did not communicate its role; `DiceRoller`
clearly describes what it does (rolls dice).

**File:** systems/dice_manager.py
**Lines (at time of edit):** (deleted)
**Before:** Held the previous `DiceManager` class.
**After:** (removed)
**Why:** Replaced by `systems/dice_roller.py`.

**File:** crt.py
**Lines (at time of edit):** 1-58 (rewritten)
**Before:** `from settings import *` star-import; hard-coded scanline
width of `1`; parameter `surf`, loop variable `y`; no module
docstring.
**After:** Explicit imports of `AssetPaths`/`ColorSettings`/
`ScreenSettings`; module docstring; uses
`ScreenSettings.CRT_SCANLINE_LINE_WIDTH`; renamed parameter to
`overlay` and loop variable to `line_y`.
**Why:** Eliminates wildcard imports, removes the last magic number, and
improves readability.

**File:** main.py
**Lines (at time of edit):** 6, 30-32, 91-93, 117-118, 130-141
**Before:** Imported `DiceManager` from `systems.dice_manager`;
attribute `self.dice_manager`; resize handler used `event.w`/`event.h`;
`_update_world` and `_render_frame` had no docstrings.
**After:** Imports `DiceRoller` from `systems.dice_roller`; attribute
renamed to `self.dice_roller`; resize handler uses `event.width`/
`event.height`; both helper methods now have one-line docstrings, and
the dt comment explains why milliseconds are converted to seconds.
**Why:** Wires up the renamed dice subsystem and clarifies the loop helpers.

## 2026-05-07 19:22 -04:00 � Documentation overhaul: phased roadmap, architecture manual, contributor rules

**File:** README.md
**Lines (at time of edit):** 1-95 (rewritten)
**Before:** Short description with project goal, theme mapping, and a Wikipedia rules quote.
**After:** Reorganized into About, Status, Rules, Requirements, Install & Run, Controls, Project Structure, Documentation map, and Credits. Adds explicit pointers to TODO, ARCHITECTURE, CHANGELOG, and copilot-instructions.
**Why:** README is the front door; it needed to clearly say what the project is, how to run it, and where every other doc lives.

**File:** docs/TODO.md
**Lines (at time of edit):** 1-110 (rewritten)
**Before:** Five flat bullet points.
**After:** Six-phase roadmap (Playable Prototype, Multiplayer, Theming, Audio, Polish, Cabinet Integration) with goals and checklists per phase, plus an Open Questions section and a Documentation Maintenance section. Adds explicit Phase 1 task to temporarily map 1-6 number dice to Zombie Dice outcomes; Phase 1 includes AI opponents via legacy bots.
**Why:** A flat list did not communicate priority or sequencing. Phases enforce 'get it playable, then refine.'

**File:** docs/ARCHITECTURE.md
**Lines (at time of edit):** (new file)
**Before:** (file did not exist)
**After:** Manual-style breakdown of the program shape, frame loop, dice subsystem (DiceRoller / DiceTray / AnimatedDie), CRT overlay, settings philosophy, asset pipeline, input model, and code conventions. Includes a placeholder note that current 1-6 dice will be mapped to Zombie Dice outcomes during Phase 1 and replaced in Phase 3.
**Why:** New required reading for contributors. Explains the parts unique to this game so editors do not have to reverse-engineer them.

**File:** .github/copilot-instructions.md
**Lines (at time of edit):** 1-80 (rewritten)
**Before:** Single-section refactoring rules with one short reading requirement and a UI-text rule.
**After:** Reorganized into Required reading order (README -> TODO -> ARCHITECTURE -> CHANGELOG -> source), Required actions after a change (CHANGELOG + ARCHITECTURE + TODO updates), Code style, Architecture rules, File and function layout (codifies the all-caps banner comment as the standard section separator and includes the literal template), Comments and docstrings, UI text, and the Mental testing checklist.
**Why:** Existing rules survived but were reorganized for clarity, and three new rules were added: doc reading order, ARCHITECTURE.md maintenance after system changes, and the codified section-banner comment style the user pointed at.

**File:** requirements.txt
**Lines (at time of edit):** (new file)
**Before:** (file did not exist)
**After:** Single line `pygame>=2.5`.
**Why:** Standard Python dependency manifest. Lets new contributors run `pip install -r requirements.txt` instead of guessing what to install.

**Editor:** Bryan, with GitHub Copilot (Claude Sonnet 4.5).

## 2026-05-16 15:20 +00:00 — Phase 0 plan, bag terminology, legacy/ read-only rule, ported message log, panel frames

**File:** docs/TODO.md
**Lines (at time of edit):** 1-50 (added), and scattered edits through later phases and Open Questions
**Before:** Phase 1 started directly with the full color-distribution bag; "cup" terminology throughout; an Open Question titled "Drawing animation" discussed why the cup is not visualized; later phases referenced brain/runner/shotgun.
**After:** Inserted Phase 0 ("Bare-Bones Playable") above Phase 1 covering equal-odds outcome mapping, full Zombie Dice rules with footsteps held over, dice rendered by outcome row, ported typewriter message log, stats panel + message log frames, AI bots ported and adapted (Lizzie sat out), 4-player random game, GAME OVER screen with restart. Phase 1 now reads as "Color-Distribution Dice" and reintroduces Lizzie. All "cup" references renamed to "bag" (matches how the user plays in person). Removed the "Drawing animation" Open Question (decision is settled) and added a one-line note that the bag is a data structure, never a sprite. Player-facing terms (brain/runner/shotgun) renamed to (treasure/empty chest/mimic) where they appeared.
**Why:** User wants a smaller, fully-playable end-to-end slice before the color-distribution work; user prefers "bag" over "cup" because that's the prop they actually use at the table; the cup-animation discussion is resolved and no longer an open question.

**File:** .github/copilot-instructions.md
**Lines (at time of edit):** 41-46 (new section inserted after Architecture rules)
**Before:** No rule about `legacy/`.
**After:** New section "The `legacy/` folder is read-only" stating that files under `legacy/` must not be edited/renamed/moved/deleted, must not be imported directly into shipped code (copy-and-adapt only), and that the bots' difficulty tiers were measured once via the original tournament-runner module and recorded in `docs/AI_OPPONENTS.md` — no further simulations are needed.
**Why:** User confirmed `legacy/` is reference material only; codifying the rule prevents future contributors (human or AI) from editing it by mistake.

**File:** docs/ARCHITECTURE.md
**Lines (at time of edit):** Section 3.2 (one paragraph) and Section 3.4 (rewritten)
**Before:** Section 3.2 talked about a "cup"; Section 3.4 described placeholder behavior as a single Phase 1 task.
**After:** Section 3.2 now talks about a "bag" (data structure, not visualized). Section 3.4 splits the migration into Phase 0 (introduce Outcome layer, render dice by outcome row, build the equal-odds bag and re-roll mechanics) and Phase 1 (replace the bag contents with the real color distribution and reintroduce Lizzie).
**Why:** Architecture doc must reflect the new Phase 0 plan; bag terminology must be consistent with TODO.

**File:** settings.py
**Lines (at time of edit):** 12-38 (ColorSettings expanded), 119-176 (new LayoutSettings + MessageLogSettings), 179-200 (DiceSettings: TRAY_PADDING/TRAY_SIZE removed, replaced by layout-driven sizing)
**Before:** ColorSettings had only tray/CRT role aliases; no LayoutSettings or MessageLogSettings class; `DiceSettings.TRAY_PADDING` and `TRAY_SIZE` owned the tray's position and size.
**After:** Added `YELLOW` to the raw palette and added role aliases `PANEL_BORDER_COLOR`, `PANEL_FILL_COLOR`, `LOG_TEXT_DEFAULT`, `LOG_TEXT_ACTIVE`, `LOG_HIGHLIGHT_MIMIC`, `LOG_HIGHLIGHT_TREASURE`, `LOG_HIGHLIGHT_EMPTY`. Introduced `LayoutSettings` (PANEL_PADDING, PANEL_GAP, STATS_PANEL_WIDTH=240, MESSAGE_LOG_HEIGHT=180, PANEL_BORDER_WIDTH=2, PANEL_BORDER_RADIUS=6) as the single source of truth for window-frame geometry. Introduced `MessageLogSettings` with MAX_MESSAGES, LINE_HEIGHT, TEXT_PADDING, FONT_SIZE, TYPING_SPEED, WELCOME_MESSAGE, and the WORD_COLORS map for inline highlighting (MIMIC, TREASURE, EMPTY, BUST, BANK, BANKED, WIN, WINS). Removed `DiceSettings.TRAY_PADDING` and `DiceSettings.TRAY_SIZE`; a comment in DiceSettings points readers to `ui.layout.tray_region_rect` for the new derivation.
**Why:** New UI panels need geometry constants; the message log needs its own tunables; tray placement now flows from one place so the three regions resize together.

**File:** ui/layout.py
**Lines (at time of edit):** (new file)
**Before:** (file did not exist)
**After:** New module with three pure functions — `tray_region_rect`, `message_log_rect`, `stats_panel_rect` — that take the current window size and return the rect each region should occupy. A private helper `_tray_available_size` does the shared subtraction so the three rects can never disagree on what's left over. Module docstring includes the ASCII layout sketch.
**Why:** A single place for layout math means panels, the tray, and `VIDEORESIZE` handling all read the same source. Pure functions keep this trivial to test and free of side effects.

**File:** ui/message_log.py
**Lines (at time of edit):** (new file)
**Before:** (file did not exist)
**After:** Port of Dungeon Digger's `MessageLog` from `ui/windows.py`. Same per-frame contract (`add_message`, `update`, `draw`), same typewriter animation, same term-based inline highlighting (now keyed by `MessageLogSettings.WORD_COLORS`). Stripped Dungeon-Digger-specific highlight terms (KEY, MONSTER, RUBY, etc.) and full-line warning overrides; those were game-specific and not relevant here. `draw()` now takes the target `rect` as an argument instead of reading static `LOG_X`/`LOG_Y`, so layout is decoupled from the log.
**Why:** Frankie explicitly asked for the Dungeon Digger typewriter; copying it here now means we never need to re-open the Dungeon Digger folder for that feature.

**File:** systems/dice_tray.py
**Lines (at time of edit):** 14-15 (import), 33-45 (resize)
**Before:** `resize()` read `DiceSettings.TRAY_PADDING` and `DiceSettings.TRAY_SIZE` and clamped manually.
**After:** Imports `from ui import layout` and `resize()` is one line: `self.rect = layout.tray_region_rect(window_size)`. Docstring rewritten to point at `ui.layout` as the new source of truth.
**Why:** Layout math belongs in `ui/layout.py`; the tray is now a passive consumer of the region it's given so it can shrink to fit when the stats panel and message log claim their space.

**File:** main.py
**Lines (at time of edit):** 1-16 (imports), 43-47 (MessageLog construction), 157-181 (new `_draw_panel_frames`), 183-189 (call site)
**Before:** No UI panel rendering; only the tray and CRT overlay drew above the background.
**After:** Imports `LayoutSettings`, `ui.layout`, and `MessageLog`. Constructs a `MessageLog` instance in `__init__` (kept available for the typewriter to be wired up in the next pass even though no events fire yet). Adds `_draw_panel_frames()` which uses `layout.stats_panel_rect` and `layout.message_log_rect` to draw both panels as rounded-corner filled rects with outlined borders. `_render_frame` now calls `_draw_panel_frames` between the dice and the CRT overlay.
**Why:** Frankie asked for the window frames to be drawn this pass (and nothing else inside them); the `MessageLog` instance lives now so the typewriter is in place when game events start firing.

**Editor:** Frankie, with Claude (claude-opus-4-7) via Cowork.

## 2026-05-16 15:30 +00:00 — Pre-Phase-0 grab: GAME OVER overlay, font scaffolding, color_with_alpha

**File:** settings.py
**Lines (at time of edit):** FontSettings (sizes added), new GameOverSettings inserted above DiceSettings
**Before:** FontSettings carried only the FONT path; the message-log size was the only font size in the project. No GameOverSettings.
**After:** FontSettings adds the Dungeon Digger size ladder: `HUD_SIZE = 10` (stats-panel rows), `SCORE_SIZE = 12` (banked-score numerals), `LARGE_SIZE = 16` (headings, play-again prompt), `ENDGAME_SIZE = 32` (centered GAME OVER title). New `GameOverSettings` class with `OVERLAY_ALPHA = 180`, `CONTINUE_DELAY_MS = 650` (input grace period after game over), `PROMPT_FADE_MS = 750` (fade-in for the play-again prompt), `PROMPT_OFFSET_Y = 42`, `SCORE_LINE_HEIGHT = 22`, `SCORE_TOP_GAP = 28`, and `CONTINUE_PROMPT = "PRESS A OR ENTER TO PLAY AGAIN"`.
**Why:** Phase 0 step 10 needs a GAME OVER screen with a centered title and a fade-in prompt, and the stats panel and final-scores list need larger font sizes than the log; centralizing the ladder now prevents magic numbers later.

**File:** ui/render_utils.py
**Lines (at time of edit):** (new file)
**Before:** (file did not exist)
**After:** New module hosting pygame-dependent rendering helpers. Initial helper: `color_with_alpha(color, alpha)` returns a `pygame.Color` with the requested alpha channel. Accepts any input `pygame.Color()` accepts (named string, RGB tuple, RGBA tuple, or `pygame.Color`).
**Why:** Phase 0 needs fade-in alpha on the play-again prompt; this is the same one-line helper Dungeon Digger uses, and keeps pygame imports out of settings.py.

**File:** ui/game_over.py
**Lines (at time of edit):** (new file)
**Before:** (file did not exist)
**After:** Port of Dungeon Digger's `draw_end_game_screens` pattern, generalized as `GameOverScreen`. Per-frame contract: `reset(now)` records the entry time, `is_input_accepted(now)` returns False during the `CONTINUE_DELAY_MS` grace window, `draw(surface, now, final_scores=None)` paints (1) a dim overlay across the full surface, (2) a centered "GAME OVER" title in `ENDGAME_SIZE`, (3) an optional ordered final-scores list with the winner tinted in the treasure-highlight color, (4) the "PRESS A OR ENTER TO PLAY AGAIN" prompt with a 0->255 alpha ramp over `PROMPT_FADE_MS`. The screen is a pure renderer with no game-state dependencies; `GameManager` will own when to enter the state, what scores to pass in, and what to do when the input is accepted.
**Why:** Frankie asked to grab this pattern before closing the session that had access to Dungeon Digger; the new session will work against the mimic-dice repo only.

**Editor:** Frankie, with Claude (claude-opus-4-7) via Cowork.

## 2026-05-16 23:29 +00:00 — Outcome type and face_to_outcome map (Phase 0, first rules-engine piece)

**File:** settings.py
**Lines (at time of edit):** 221-238 (new `OutcomeSettings` class inserted above `DiceSettings`)
**Before:** No outcome-related constants; faces 1-6 had no meaning beyond their sprite index.
**After:** New `OutcomeSettings` class with `MIMIC_FACE_MAX = 2` and `EMPTY_FACE_MAX = 4`, plus a class docstring explaining that this is the Phase 0 placeholder (equal-odds 1-2 → MIMIC, 3-4 → EMPTY, 5-6 → TREASURE) and that Phase 1 will retire the class along with the equal-odds bag.
**Why:** The face → outcome thresholds belong in `settings.py` per the no-magic-numbers rule. Keeping them in their own class (rather than folding them into `DiceSettings`) makes it obvious that this whole block is Phase 0 scaffolding that disappears when the color-distribution bag arrives.

**File:** systems/outcomes.py
**Lines (at time of edit):** (new file)
**Before:** (file did not exist)
**After:** New module with module docstring describing the seam between the dice subsystem and the rules engine. Defines `Outcome` (an `Enum` with `MIMIC` / `EMPTY` / `TREASURE`) and `face_to_outcome(face)`, which reads `OutcomeSettings.MIMIC_FACE_MAX` and `EMPTY_FACE_MAX` to map a 1-based face into the right `Outcome`. Sections are split with the project's `# ---- SECTION NAME ----` banner style: `OUTCOME TYPE` and `FACE -> OUTCOME MAPPING`. Verified the mapping by hand for all six faces (1,2 → MIMIC; 3,4 → EMPTY; 5,6 → TREASURE) before committing.
**Why:** First piece of the Phase 0 rules engine. The bag, hold-over, bust/bank, and win condition will all read outcomes through this type instead of raw face indexes, which means Phase 1 only needs to swap the implementation of `face_to_outcome` for a per-color distribution lookup — nothing downstream of this seam should need to change.

**File:** docs/TODO.md
**Lines (at time of edit):** 12 (Phase 0 → Rules engine → first bullet)
**Before:** `- [ ] Add Outcome constants ...`
**After:** `- [x] Add Outcome constants ...`
**Why:** The roadmap rule is `[ ]` → `[x]` once an item ships; do not delete.

**File:** docs/ARCHITECTURE.md
**Lines (at time of edit):** New Section 3.5 inserted after 3.4; Section 9's "Rules engine" bullet expanded
**Before:** Section 9 just said "Rules engine (turn state, cup, draw-3, bust, bank, win condition)." with no mention that any of it existed yet; no Section 3.5.
**After:** New Section 3.5 "The Outcome layer" explains the seam (Outcome as the type the rules engine speaks, face_to_outcome as the Phase 0 placeholder that gets swapped for a per-color lookup in Phase 1, without anything above the seam having to change). Section 9's rules-engine bullet now reads "bag" not "cup" (matches the rest of the docs) and notes that the Outcome type and `face_to_outcome` map already shipped.
**Why:** Architecture rule: any new system gets its own section; the unbuilt-systems list shrinks as pieces land.

**Editor:** Frankie, with Claude (claude-opus-4-7) via Cowork.

## 2026-05-16 23:42 +00:00 — Copilot instructions: OneDrive sync caveat for Cowork sessions

**File:** .github/copilot-instructions.md
**Lines (at time of edit):** New section "Verifying edits in a Cowork session (OneDrive sync caveat)" inserted directly above the Mental testing checklist
**Before:** No mention of the Windows / Linux-mount sync lag; contributors verifying just-edited code through `bash` would silently execute against the stale file and waste time chasing phantom errors.
**After:** New section explains that the Read / Write / Edit tools talk to Windows directly and are immediate, but `bash` (and any `python3` run through it) sees a OneDrive-synced Linux mount that can lag for seconds to minutes. Workarounds listed: (a) do not import just-edited Python through `bash`, (b) use a self-contained `python3 -c` equivalence test for behavior checks, (c) use the Read tool — not `cat` / `sed` / `wc` — for file-content checks, (d) run real pygame/runtime tests on the Windows side outside Cowork.
**Why:** This bit Frankie's Outcome / `face_to_outcome` verification step earlier in the same session — the bash import failed with a `NameError` that was actually just the truncated stale file. Capturing the workaround in copilot-instructions means future sessions (human or AI) don't repeat the same dead-end.

**Editor:** Frankie, with Claude (claude-opus-4-7) via Cowork.

## 2026-05-16 — Phase 0 rules engine: bag, turn engine, outcome-colored dice

**File:** settings.py
**Lines (at time of edit):** AssetPaths class (new constants), new BagSettings and TurnSettings classes inserted above DiceSettings
**Before:** AssetPaths had no outcome sprite row constants; no BagSettings or TurnSettings.
**After:** Added `DIE_MIMIC_ROW = 3`, `DIE_EMPTY_ROW = 2`, `DIE_TREASURE_ROW = 9` to AssetPaths. New `BagSettings` class with `TOTAL_DICE = 13`. New `TurnSettings` class with `DICE_PER_ROLL = 3`, `BUST_THRESHOLD = 3`, `WIN_SCORE = 13`.
**Why:** Centralizes all new rules-engine knobs per the no-magic-numbers rule; outcome row constants belong with the sprite-sheet layout data in AssetPaths.

**File:** systems/bag.py
**Lines (at time of edit):** (new file)
**Before:** (file did not exist)
**After:** New `Bag` class: integer counter (all 13 dice are identical in Phase 0), `reset()`, `draw(n)` resolves each die through `face_to_outcome`, `recycle(set_aside)` returns TREASURE-outcome dice to the pool when the bag empties mid-turn.
**Why:** Second rules-engine piece (first was `systems/outcomes.py`). Bag is a pure data structure, never drawn.

**File:** systems/turn_engine.py
**Lines (at time of edit):** (new file)
**Before:** (file did not exist)
**After:** New `TurnStatus` enum (ROLLING / BUST / BANKED), `RollResult` dataclass (outcomes list + running totals), and `TurnEngine` class. `start_turn()` resets counters and refills the bag. `roll()` re-rolls held-over EMPTY dice, draws fresh dice from the bag, classifies outcomes, fires mid-turn recycle if bag is short, checks bust at `BUST_THRESHOLD` mimics. `bank()` commits `turn_treasures` to the caller's score. Win condition detected in `GameManager` after each bank.
**Why:** Core rules engine for Phase 0. Logic tested with 1 000 simulated turns (38% bust rate, 62% bank rate, 0 unresolved turns).

**File:** systems/animated_die.py
**Lines (at time of edit):** 1–24 (module docstring), 39–63 (constructor), 159–172 (_settle), 196–201 (draw)
**Before:** Constructor took `face_sprites: list[Surface]` (single row); `_settle()` used `random.randrange(len(self.face_sprites))`; `draw()` referenced `self.face_sprites[self.face_index]`.
**After:** Constructor takes `outcome_sprites: dict[Outcome, list[Surface]]` and derives `self.size` from the first entry. Adds `pending_outcome: Optional[Outcome]` field and `_settled_sprites` cache. `_settle()` looks up `pending_outcome` in `outcome_sprites` and picks a random frame from the matching row; falls back to the first available row if outcome is unset. `draw()` uses `self._settled_sprites`.
**Why:** Architecture doc stated the engine should pre-decide outcomes and inject them at settle time rather than `random.randrange`; this pass wires that up while keeping the physics and animation logic unchanged.

**File:** systems/dice_roller.py
**Lines (at time of edit):** 1–94 (rewritten)
**Before:** Loaded one face row (`DIE_FACE_ROW = 0`, white); constructed `AnimatedDie(face_sprites, tumble_sprites)`; exposed only `roll_all()`.
**After:** Loads three outcome face rows (MIMIC=row 3, EMPTY=row 2, TREASURE=row 9) into `outcome_sprites: dict[Outcome, list[Surface]]`; constructs each `AnimatedDie(outcome_sprites, tumble_sprites)`. Adds `all_settled` property (True when no die is still rolling). Adds `roll_with_outcomes(outcomes)` which assigns `die.pending_outcome` then calls `die.roll()` for each die/outcome pair. Removed `roll_all()`.
**Why:** DiceRoller is the only dice-system entry point; loading outcome rows here and sharing them across all dice keeps memory flat and isolates sprite-sheet knowledge from GameManager and TurnEngine.

**File:** main.py
**Lines (at time of edit):** 1–221 (rewritten)
**Before:** Imported only DiceRoller, MessageLog, CRT; SPACE called `dice_roller.roll_all()` directly; message log not drawn; no rules-engine integration.
**After:** Imports `Bag`, `TurnEngine`, `TurnStatus`, `TurnSettings`. Constructs `_bag` and `_turn_engine` in `__init__`. SPACE calls `_do_roll()`: asks engine for outcomes, animates via `roll_with_outcomes`, sets `_waiting_for_roll`. A/Enter/JoyA calls `_do_bank()`. `_update_world` detects `all_settled` edge and calls `_on_dice_settled()`, which logs the roll summary + running totals + BUST message. Win detection resets the game (full final-round logic is a Phase 0 Game Flow task). Message log now drawn each frame.
**Why:** Phase 0 milestone: bag, turn engine, and animated outcome-colored dice are all wired into a playable single-player game loop.

**File:** docs/TODO.md
**Lines (at time of edit):** Phase 0 → Rules engine and Visual placeholder mapping sections
**Before:** `[ ]` for all four rules-engine items and the visual placeholder mapping item.
**After:** `[x]` for: bag + draw-3 + hold-over; mid-turn recycle; bust/bank tracking; win condition; outcome-colored sprite rows.
**Why:** Roadmap maintenance rule.

**File:** docs/ARCHITECTURE.md
**Lines (at time of edit):** Section 9 (new), old Section 9 renamed to 10
**Before:** Section 9 listed rules engine, AI adapter, UI screens, audio as unbuilt.
**After:** New Section 9 "The rules engine" documents Bag (9.1), TurnEngine (9.2), outcome-driven sprite rows (9.3), and the win-condition stub (9.4). Old unbuilt list is now Section 10 with the rules engine removed.
**Why:** Architecture doc must reflect every system that shipped.

**Editor:** Frankie, with Claude (claude-sonnet-4-6) via Cowork.

---

## 2026-05-17 02:02 +00:00 — Phase 1: colored bag (6 green / 4 purple / 3 red), per-color settled art, Lizzie back in the roster

**File:** systems/outcomes.py
**Lines (at time of edit):** 1-62 (rewritten)
**Before:**
    `Outcome` enum (MIMIC / EMPTY / TREASURE) plus a Phase 0 `face_to_outcome(face)` that mapped faces 1-2 → MIMIC, 3-4 → EMPTY, 5-6 → TREASURE via `OutcomeSettings`.
**After:**
    New `DieColor` enum (GREEN / PURPLE / RED — string values are the lower-case color names so they compose into asset paths). `Outcome` kept verbatim. Added module-level `FACE_DISTRIBUTIONS: dict[DieColor, tuple[Outcome, ...]]` with six-entry tuples per color (GREEN 3/2/1, PURPLE 2/2/2, RED 1/2/3) and a `roll_color(color)` helper. The threshold-based `face_to_outcome` is gone; nothing imports it anymore.
**Why:** Phase 1 swaps the equal-odds bag for the real Zombie Dice distribution. Keeping DieColor + Outcome + FACE_DISTRIBUTIONS in one module avoids the circular import we'd hit if the dict literal lived in `settings.py`.

**File:** settings.py
**Lines (at time of edit):** AssetPaths (113-147), OutcomeSettings (deleted), BagSettings (297-316), BotSettings (added LIZZIE constants)
**Before:**
    `AssetPaths` carried `DIE_FACE_ROW / DIE_MIMIC_ROW / DIE_EMPTY_ROW / DIE_TREASURE_ROW / DIE_FACE_COUNT` row indexes into the six-sided sheet. `OutcomeSettings` held `MIMIC_FACE_MAX = 2` and `EMPTY_FACE_MAX = 4`. `BagSettings.TOTAL_DICE = 13` was a hard-coded integer. `BotSettings.DEFAULT_BOT_NAMES = ("ALICE", "BOB")`.
**After:**
    `AssetPaths` lists only the tumble row of the sheet plus a new `SETTLED_SPRITES` dict keyed by `(color_value, outcome_value)` mapping to twelve standalone PNGs (the white art is shipped but not currently mapped to a die). `OutcomeSettings` deleted. `BagSettings` now imports `DieColor` inside the class body (to avoid top-level circular imports) and defines `DICE_PER_COLOR = {GREEN:6, PURPLE:4, RED:3}`; `TOTAL_DICE = sum(DICE_PER_COLOR.values())` so the two can't drift apart. `BotSettings.DEFAULT_BOT_NAMES = ("ALICE", "BOB", "LIZZIE")`; added `LIZZIE_BANK_AT_ONE_MIMIC_TREASURE = 6` and `LIZZIE_BANK_AT_TWO_MIMICS_TREASURE = 1`.
**Why:** Settings should reflect the real game's tunables, not the Phase 0 stubs. The sprite-row constants describe a sheet layout that no longer drives rendering; the per-color counts and Lizzie thresholds describe the actual gameplay.

**File:** systems/bag.py
**Lines (at time of edit):** 1-126 (rewritten)
**Before:**
    `Bag` was an integer counter; `draw(n) -> list[int]` returned 1-6 face values; `recycle(set_aside: list[Outcome])` counted TREASUREs and added that many back to the count.
**After:**
    `Bag` is a shuffled `list[DieColor]` populated from `BagSettings.DICE_PER_COLOR`. `draw(n) -> list[DieColor]` returns the colors of drawn dice in order (without replacement). `recycle(set_aside_colors, set_aside_outcomes)` reinserts only the TREASURE entries, preserving each die's color, and re-shuffles. New `count_color(color)` for AI strategies (Lizzie's red-tracking).
**Why:** Every die now has a color that drives both its outcome distribution and its settled sprite, so the bag has to remember individual dice instead of just a count.

**File:** systems/turn_engine.py
**Lines (at time of edit):** 1-218 (rewritten)
**Before:**
    `RollResult.faces: list[int]` paired with `outcomes`; engine carried `held_over: int` and `set_aside_faces: list[int]`; `roll()` generated 1-6 faces with `random.randint`, ran `face_to_outcome` to classify.
**After:**
    `RollResult.colors: list[DieColor]` paired with `outcomes`; engine carries `held_over_colors: list[DieColor]` (a property `held_over` still returns its length) and `set_aside_colors: list[DieColor]`. `roll()` builds `all_colors = held_over_colors + bag.draw(...)` so held-overs keep their original color across re-rolls, then resolves outcomes via `roll_color(color)` per die. New `red_dice_remaining()` helper that bots can ask for.
**Why:** Color is now a property of the die (not the roll), so it has to follow held-over dice from one push to the next. Lizzie needs `red_dice_remaining()` to drive her bust-risk heuristic.

**File:** systems/animated_die.py
**Lines (at time of edit):** 1-220 (rewritten)
**Before:**
    Constructor took `outcome_sprites: dict[Outcome, list[Surface]]`; `pending_outcome` + `pending_face: Optional[int]`; `_settle()` picked `outcome_sprites[pending_outcome][pending_face - 1]` (column = face value).
**After:**
    Constructor takes `settled_sprites: dict[tuple[DieColor, Outcome], pygame.Surface]`; `pending_color: Optional[DieColor]` replaces `pending_face`. `_settle()` looks up the single sprite at `(pending_color, pending_outcome)` and renders it; tumble path unchanged.
**Why:** The art pipeline shipped twelve standalone PNGs (one per color × outcome), so a die has exactly one settled sprite to render — no column index needed.

**File:** systems/dice_roller.py
**Lines (at time of edit):** 1-189 (rewritten)
**Before:**
    Loaded three outcome face rows from `six_sided_die.png` into `self.outcome_sprites: dict[Outcome, list[Surface]]`. `roll_with_results(faces, outcomes)` assigned `pending_face` + `pending_outcome` per die.
**After:**
    Loads the tumble row from `six_sided_die.png` (shared by every color) plus twelve standalone settled PNGs from `AssetPaths.SETTLED_SPRITES` into `self.settled_sprites: dict[(DieColor, Outcome), Surface]`. `roll_with_results(colors, outcomes)` assigns `pending_color` + `pending_outcome` per die. New static `_load_settled_sprite(path)` scales the per-color PNGs by `DiceSettings.SCALE` to match the tumble row.
**Why:** Tumble frames stay shared so memory stays low and dice in the air all look the same; settle reveals the per-color art that matches the engine-decided outcome.

**File:** systems/bots.py
**Lines (at time of edit):** 1-148 (rewritten)
**Before:**
    `Strategy = Callable[[int, int], BotDecision]`; `Bot.decide(turn_treasures, turn_mimics)`; Alice and Bob; no Lizzie.
**After:**
    New `BotContext` dataclass (treasures, mimics, red_dice_remaining); `Strategy = Callable[[BotContext], BotDecision]`; `Bot.decide(context)` takes the snapshot object. Added `lizzie_strategy`: banks at `BotSettings.LIZZIE_BANK_AT_ONE_MIMIC_TREASURE` once a single mimic is on the table or at `LIZZIE_BANK_AT_TWO_MIMICS_TREASURE` once two mimics are on; pushes regardless when `red_dice_remaining == 0`. Lizzie added to the name→strategy factory.
**Why:** Lizzie needs color-aware state, and a one-shot context object lets future bots ask for more fields without breaking every existing strategy's signature.

**File:** main.py
**Lines (at time of edit):** import block (9), DiceRoller wiring (113), `_do_roll` call (208-210), bot call (334-340), stats panel call (468-475)
**Before:**
    `from systems.bots import Bot, BotDecision, make_bot`; `StatsPanel(self.dice_roller.outcome_sprites)`; `roll_with_results(result.faces, result.outcomes)`; `player.bot.decide(turn_treasures, turn_mimics)`; stats panel got `set_aside_faces`.
**After:**
    Imports `BotContext`. `StatsPanel(self.dice_roller.settled_sprites)`. `roll_with_results(result.colors, result.outcomes)`. `player.bot.decide(BotContext(turn_treasures, turn_mimics, self._turn_engine.red_dice_remaining()))`. Stats panel gets `set_aside_colors`.
**Why:** GameManager is the seam between the engine and the renderer + bots; both now speak colors instead of faces.

**File:** ui/stats_panel.py
**Lines (at time of edit):** 1-271 (rewritten)
**Before:**
    Constructor took `outcome_sprites: dict[Outcome, list[Surface]]`; `_draw_held_row(label, faces, outcome, ...)` indexed by `face - 1`; `draw()` accepted `set_aside_faces`.
**After:**
    Constructor takes `settled_sprites: dict[(DieColor, Outcome), Surface]`; `_draw_held_row(label, colors, outcome, ...)` looks up `settled_sprites[(color, outcome)]` per thumb; `draw()` accepts `set_aside_colors` instead.
**Why:** Held-dice thumbs now share the per-color settled art with the tray, so a banked green TREASURE shows the green chest sprite the player just saw land.

**File:** README.md
**Lines (at time of edit):** Status and Rules sections
**Before:**
    Status read "Phase 1 — Playable Prototype (in progress)". Rules section listed 6 green / 4 yellow / 3 red dice using brain / shotgun / runner terminology from Zombie Dice.
**After:**
    Status reads "Phase 1 — Color-Distribution Dice (landed)". Rules section reads 6 green / 4 PURPLE / 3 red with explicit per-color treasure / empty / mimic counts and notes that purple replaces Zombie Dice's yellow body. Goal text uses treasure / empty / mimic, not brain / runner / shotgun.
**Why:** Public-facing rules now match the actual game.

**File:** docs/TODO.md
**Lines (at time of edit):** Phase 1 rules engine + AI sections; Phase 3 art bullets
**Before:**
    `[ ]` for every Phase 1 rules-engine item, the visual-placeholder bullet, the Lizzie-reintroduction bullet, and the Phase 3 "final dice art" bullets.
**After:**
    `[x]` for the rules-engine list (with the purple replacement called out), the AI Lizzie bullet (with a pointer to the new strategy and context plumbing), and the Phase 3 art bullets (the standalone PNGs already replaced the placeholder rendering).
**Why:** Roadmap maintenance rule.

**File:** docs/ARCHITECTURE.md
**Lines (at time of edit):** Section 3.4-3.5, 9.1-9.4, bots paragraph in 9.6
**Before:**
    3.4 described the Phase-0 number-die placeholder with row indexes 2/0/10. 3.5 documented `face_to_outcome` as the Phase-0 seam. 9.1-9.3 described `Bag` as an integer counter, `RollResult.faces`, `set_aside_faces`, and `AnimatedDie._settle()` indexing by face column. 9.6 described bots as `(turn_treasures, turn_mimics)` callables with Lizzie still excluded.
**After:**
    3.4 documents the real per-color bag (counts + face distribution table) and the per-color settled PNG art. 3.5 documents DieColor, FACE_DISTRIBUTIONS, and `roll_color`. 9.1 describes the typed-dice Bag with `count_color`. 9.2 describes `held_over_colors` and `red_dice_remaining()`. 9.3 documents the (color, outcome) settled sprite map with a per-color asset table. 9.6 describes `BotContext` and Lizzie's thresholds.
**Why:** Architecture doc must reflect every system that shipped.

**Editor:** Frankie, with Claude (claude-opus-4-7) via Cowork.

## 2026-05-16 — Phase 0 rules-engine pass: row remap, face-to-sprite plumbing, stats panel, log cleanup

This is one logical change (post-Sonnet review). Sonnet's preceding pass shipped colors that didn't match what the sprite sheet actually contained, a face-vs-outcome disconnect that confused the player, duplicated welcome lines, and a placeholder stats panel.

**File:** settings.py
**Lines (at time of edit):** ColorSettings (~22-38), AssetPaths (~133-140), MessageLogSettings (~182-185), new StatsPanelSettings (~202-219)
**Before:** `DIE_MIMIC_ROW = 3` (hot pink in the sheet), `DIE_EMPTY_ROW = 2` (red), `DIE_TREASURE_ROW = 9` (lime); `LOG_HIGHLIGHT_TREASURE = GREEN`; `WELCOME_MESSAGE` was a 2-line list seeded into the log; no StatsPanelSettings.
**After:** `DIE_MIMIC_ROW = 2` (red), `DIE_EMPTY_ROW = 0` (white — sheet has no grey row), `DIE_TREASURE_ROW = 10` (yellow); new `TREASURE_YELLOW` palette entry; `LOG_HIGHLIGHT_TREASURE = TREASURE_YELLOW`; new `STATS_TEXT_COLOR`; `WELCOME_LINE` is a single string owned by GameManager; new `StatsPanelSettings` with text padding, line height, section gap, held-dice spacing, and `HUMAN_PLAYER_NAME`.
**Why:** Sonnet's row indices were verified by pixel-sampling `six_sided_die.png` and were all wrong — the sheet has no grey row, and the row labeled "green" was actually lime. The user asked for yellow treasure; the closest in-sheet match is row 10. Centralising the panel + welcome constants keeps `settings.py` the only knob panel.

**File:** systems/bag.py
**Lines (at time of edit):** module docstring (1-24), `draw` (69-86)
**Before:** `Bag.draw(n) -> list[Outcome]` — called `face_to_outcome` internally so the rolled face was thrown away.
**After:** `Bag.draw(n) -> list[int]` — returns raw 1–6 face values; `TurnEngine` runs `face_to_outcome`. Docstrings updated to explain why faces leave the bag instead of outcomes.
**Why:** The face value has to survive the bag draw if the rendered pip count is going to match the outcome. Without this, a "1"-pipped die could land in the treasure row and the player would (correctly) read that as inconsistent.

**File:** systems/turn_engine.py
**Lines (at time of edit):** RollResult dataclass (56-76), `__init__` (95-105), `start_turn` (107-115), `roll` (130-195)
**Before:** `RollResult` had `outcomes` only; `_set_aside: list[Outcome]` was private; `roll()` consumed outcomes directly from `Bag.draw`.
**After:** `RollResult` now has parallel `faces: list[int]` and `outcomes: list[Outcome]`. `set_aside_faces` / `set_aside_outcomes` are public on `TurnEngine` (the stats panel reads them). `roll()` pulls faces from `Bag.draw`, runs `face_to_outcome` over them, and bookkeeps both lists.
**Why:** Stats-panel rendering needs the same face values that drove each outcome, and the rules layer is the natural seam to do `face → outcome` resolution.

**File:** systems/animated_die.py
**Lines (at time of edit):** module docstring (17-26), `__init__` (54-65), `_settle` (159-180)
**Before:** `_settle()` picked a random column from `outcome_sprites[pending_outcome]`, so a TREASURE die could show a "1"-pip face.
**After:** New `pending_face: Optional[int]` set alongside `pending_outcome`. `_settle()` uses `pending_face - 1` as the column index, with a random fallback if `pending_face` is unset.
**Why:** Locks the displayed pip count to the engine's rolled face, which is what removes the user-facing "5 is a mimic / 1 is treasure" confusion.

**File:** systems/dice_roller.py
**Lines (at time of edit):** module docstring (10-15), `roll_with_outcomes` → `roll_with_results` (99-122)
**Before:** `roll_with_outcomes(outcomes)` — assigned `pending_outcome` only.
**After:** Renamed `roll_with_results(faces, outcomes)`; assigns both `pending_outcome` and `pending_face` per die.
**Why:** Matches the new `RollResult` shape and forces the call site to pass both values together (you can't accidentally pair the wrong arrays).

**File:** ui/message_log.py
**Lines (at time of edit):** `__init__` (29-38)
**Before:** `self.messages = list(MessageLogSettings.WELCOME_MESSAGE)` — the log shipped pre-seeded.
**After:** `self.messages = []` and GameManager owns the single opening line.
**Why:** Sonnet's pass seeded the welcome lines in *both* `MessageLog.__init__` *and* `GameManager.__init__`, so the log opened with each line duplicated. One source now.

**File:** ui/stats_panel.py
**Lines (at time of edit):** (new file)
**Before:** (file did not exist)
**After:** New `StatsPanel` class. Draws its own rounded-rect frame, a player-name + score header, and two labeled rows of held-die thumbs (TREASURE first, MIMICS below). Reads `outcome_sprites` from the shared roller so the thumb art matches the tray. Thumb rows wrap horizontally if the panel is too narrow.
**Why:** Player asked for held dice + score visible alongside the player name; replaces the empty placeholder frame the previous pass drew.

**File:** main.py
**Lines (at time of edit):** imports (~6-21), `__init__` (~62-72), `_do_roll` (~119-141), `_on_dice_settled` (~143-175), `_do_bank` (~196-212), `_draw_panel_frames` (~291-313), `_render_frame` (~315-340)
**Before:** Built only the message log; seeded welcome lines redundantly; sent `outcomes` only to `DiceRoller.roll_with_outcomes`; logged a "THIS TURN: …" line every roll (duplicated by the new panel); win prompt read "YOU REACHED 13!  WINS!".
**After:** Constructs `StatsPanel`; greets via `WELCOME_LINE` only; sends `faces + outcomes` to `DiceRoller.roll_with_results`; drops the "THIS TURN" log noise (panel covers it); renders the panel via `stats_panel.draw(...)`; win prompt now reads "WIN!  REACHED 13 TREASURE.".
**Why:** Wires the new face plumbing, removes the log/panel duplication, and tightens the copy.

**File:** docs/ARCHITECTURE.md
**Lines (at time of edit):** Section 9 (9.1 bag, 9.2 turn engine, 9.3 sprite rows, new 9.4 stats panel, renumbered 9.5 win-condition stub)
**Before:** Bag described as returning outcomes; sprite-row table was wrong; no stats panel section.
**After:** Bag now described as returning face values; sprite-row table reflects red/white/yellow remap; new 9.4 documents the stats panel; old 9.4 (win condition stub) renumbered to 9.5.
**Why:** Architecture doc must reflect every system that shipped.

**Editor:** Frankie, with Claude (claude-opus-4-7) via Cowork.

## 2026-05-16 — Felt persistence within a turn + player rotation with two starter bots

Two related changes shipped together because the bot-rotation work is only demoable once the felt holds onto kept dice within a turn.

**File:** systems/dice_roller.py
**Lines (at time of edit):** module docstring (1-32), `__init__` (49-72), new `_held_over_dice` (104-115), `roll_with_results` (120-152), new `clear_for_new_turn` (154-156)
**Before:** `__init__` built `DiceSettings.COUNT` (3) dice up front; `roll_with_results` re-threw all of them every roll, so brains/shotguns were never visually preserved.
**After:** `__init__` starts with `self.dice = []`. `roll_with_results` only re-throws settled EMPTY dice (matched to the held-over slice of the new lists) and appends new `AnimatedDie` instances for fresh draws. `clear_for_new_turn()` empties the list on bank or bust. Module docstring documents the per-turn growth model.
**Why:** Faithful to the source-game feel: only footsteps re-roll; brains/shotguns stack on the table. Frankie called this out directly.

**File:** settings.py
**Lines (at time of edit):** `StatsPanelSettings` (renamed/extended), new `BotSettings` class
**Before:** `StatsPanelSettings` carried single-player constants only; no `BotSettings` existed.
**After:** Added `PLAYER_ROW_HEIGHT`, `ACTIVE_MARKER`, `INACTIVE_MARKER` to `StatsPanelSettings`. New `BotSettings` class with `AFTER_ROLL_DELAY_S = 0.85`, `END_OF_TURN_DELAY_S = 1.10`, and `DEFAULT_BOT_NAMES = ("ALICE", "BOB")`.
**Why:** Centralises every new constant — no magic numbers in the gameplay code.

**File:** systems/bots.py
**Lines (at time of edit):** (new file)
**Before:** (file did not exist)
**After:** New `Bot` dataclass with `decide(turn_treasures, turn_mimics) -> BotDecision`. Two strategies: `alice_strategy` (bank at 2 mimics) and `bob_strategy` (bank at 2 treasures). `make_bot(name)` factory keys into a lookup table with a safe Alice fallback.
**Why:** Phase 0 needs at least one bot so a single human can test rotation, pacing, and the held-dice panel without playing both sides. Strategies match the *spirit* of two of the easy-tier legacy bots without importing from `legacy/` (which is read-only).

**File:** ui/stats_panel.py
**Lines (at time of edit):** new `PlayerView` dataclass (43-50), `_draw_roster` (113-152), `draw` signature (218-249)
**Before:** Single-player only: `draw(..., player_name, score, set_aside_*)`.
**After:** `draw(..., players: list[PlayerView], active_player_index, set_aside_*)`. New `_draw_roster` renders one row per player with right-aligned score and the active marker beside the active player's name. Held-dice rows still show the active player's set-aside pile only.
**Why:** Multi-player roster + active-turn highlight is what the panel is for once bots exist.

**File:** main.py
**Lines (at time of edit):** imports + new `Player` dataclass (1-58), `__init__` (78-117), new `_announce_current_player` / `_advance_to_next_turn` (151-176), reworked `_do_roll` / `_on_dice_settled` / `_do_bank` (181-269), new `_end_turn_after_delay` / `_tick_bot` (272-321), input guards (333-371), `_render_frame` (412-441)
**Before:** Single human player; rolled all 3 dice each press; bust/bank auto-restarted the same player's turn.
**After:** Owns a `players: list[Player]` list (human + bots) and a `_current_player_index`. Bust/bank queues a delayed `_advance_to_next_turn()` via `_end_turn_after_delay`. `_tick_bot` runs every frame: it ticks the pacing timer, fires the queued turn advance when it expires, and otherwise consults the active bot's `decide()`. `_do_roll` now refuses re-entry while `_waiting_for_roll` is True. Input handlers ignore presses unless the active player is human. Render pass passes the player list + active index to the panel.
**Why:** The dice-stay-on-felt change is hard to demo alone; the rotation work is what makes the demo actually playable.

**File:** docs/ARCHITECTURE.md
**Lines (at time of edit):** §9.3 retitled and extended; §9.4 updated to mention multi-player; new §9.6
**Before:** §9.3 described every-die-re-throws-each-roll; §9.4 was single-player-only; no bot section.
**After:** §9.3 explains the per-turn growth of the dice list. §9.4 reflects multi-player roster + active marker. New §9.6 covers `Player`, rotation, `Bot`, strategies, and the shared pacing timer.
**Why:** Architecture doc must reflect every system that shipped.

**Editor:** Frankie, with Claude (claude-opus-4-7) via Cowork.

## 2026-05-17 03:35 +00:00 — Phase 1 revision: PURPLE → YELLOW rename and colored-pip renderer (drop per-color settled PNGs)

The Phase 1 pass shipped per-color chest / mimic / treasure PNGs for the felt and called the middle tier PURPLE. The new look reverts to colored 1-6 pip dice from `six_sided_die.png`, with the *pip number* on a settled die mapping to its outcome via a per-color band (green 1=MIMIC / 2-3=EMPTY / 4-6=TREASURE, yellow 1-2 / 3-4 / 5-6, red 1-3 / 4-5 / 6). Probabilities are unchanged — band widths match `FACE_DISTRIBUTIONS` counts, so the pip pick is statistically identical to a `roll_color` pick. The middle tier is renamed YELLOW everywhere to match Zombie Dice naming. The standalone per-color PNGs (`mimic_*.png`, `empty_chest_*.png`, `treasure_*.png`) stay on disk but are no longer referenced. The stats panel switches to three color-agnostic flat icons (`mimic.png`, `empty_chest.png`, `treasure.png`).

**File:** settings.py
**Lines (at time of edit):** AssetPaths (~113-156), BagSettings.DICE_PER_COLOR (~311-315)
**Before:**
    `AssetPaths` listed `SETTLED_SPRITES: dict[(color_value, outcome_value), path]` mapping nine standalone PNGs (green/purple/red × mimic/empty/treasure). `BagSettings.DICE_PER_COLOR` keyed PURPLE.
**After:**
    `AssetPaths` drops `SETTLED_SPRITES`. New `DIE_FACE_COUNT = 6` (pip columns per row). New `DIE_FACE_ROWS = {"red": 2, "green": 8, "yellow": 10}` (0-indexed sheet rows for the three colored pip rows). New `FLAT_OUTCOME_SPRITES = {"MIMIC": "…/mimic.png", "EMPTY": "…/empty_chest.png", "TREASURE": "…/treasure.png"}` for the stats panel. `BagSettings.DICE_PER_COLOR` keys YELLOW instead of PURPLE.
**Why:** Pulls the felt's per-color pip rows out of the existing single sheet (one row per color, 1-6 left to right) and gives the right-side panel its own color-agnostic icon set. PURPLE → YELLOW matches Zombie Dice naming now that the design no longer needs the purple-as-yellow stand-in.

**File:** systems/outcomes.py
**Lines (at time of edit):** 1-150 (rewritten)
**Before:**
    `DieColor` had `PURPLE = "purple"`. `FACE_DISTRIBUTIONS` keyed `DieColor.PURPLE`. Only `roll_color` was exposed.
**After:**
    `DieColor.PURPLE` renamed to `YELLOW = "yellow"`. `FACE_DISTRIBUTIONS` re-keyed under `DieColor.YELLOW` (same 2/2/2 tuple). New module-level `OUTCOME_FACE_NUMBERS: dict[(DieColor, Outcome), tuple[int, ...]]` that maps each (color, outcome) to the pip faces representing it (green {1}/{2,3}/{4,5,6}, yellow {1,2}/{3,4}/{5,6}, red {1,2,3}/{4,5}/{6}). New `face_for_outcome(color, outcome) -> int` helper that random-choices a pip from the matching set.
**Why:** Visual layer over the existing outcome model: the rules engine still picks Outcome from `FACE_DISTRIBUTIONS`, the renderer picks a pip from the matching band. Band widths mirror outcome counts so probabilities are mathematically identical.

**File:** systems/animated_die.py
**Lines (at time of edit):** 1-220 (rewritten)
**Before:**
    Constructor took `settled_sprites: dict[(DieColor, Outcome), Surface]`. `_settle()` blitted `settled_sprites[(pending_color, pending_outcome)]` directly.
**After:**
    Constructor takes `face_sprites: dict[(DieColor, int), Surface]` keyed by (color, pip face 1-6). `_settle()` calls `face_for_outcome(pending_color, pending_outcome)` for a pip in [1, 6] and blits `face_sprites[(pending_color, pip)]`.
**Why:** The felt is now numbered colored dice (1-6 per color), not three glyphs per color. The constructor's sprite-map shape changes to match what the renderer needs to look up.

**File:** systems/dice_roller.py
**Lines (at time of edit):** 1-180 (rewritten)
**Before:**
    Loaded the tumble row plus nine standalone PNGs via `_load_settled_sprite(path)` into `self.settled_sprites`. Passed `settled_sprites` to each `AnimatedDie`.
**After:**
    Loads only `six_sided_die.png` once. Slices the tumble row (unchanged) plus three colored pip-face rows from `AssetPaths.DIE_FACE_ROWS` into `self.face_sprites: dict[(DieColor, int), Surface]` (column 0 → pip 1, column 5 → pip 6). Passes `face_sprites` to each `AnimatedDie`. `_load_settled_sprite` removed (no standalone PNG loading anymore).
**Why:** Single-sheet load is simpler, matches the new renderer, and keeps the asset table inside `AssetPaths` instead of split between row constants and a per-PNG dict.

**File:** ui/stats_panel.py
**Lines (at time of edit):** 1-260 (rewritten)
**Before:**
    Constructor took `settled_sprites: dict[(DieColor, Outcome), Surface]` from `DiceRoller`. `_split_set_aside_by_outcome` partitioned a `colors: list[DieColor]` into treasure/mimic lists; `_draw_held_row(label, colors, outcome, …)` blitted `settled_sprites[(color, outcome)]` per thumb. `draw(...)` accepted both `set_aside_colors` and `set_aside_outcomes`.
**After:**
    Constructor takes no args; loads three flat icons from `AssetPaths.FLAT_OUTCOME_SPRITES` into `self.outcome_sprites: dict[Outcome, Surface]` via new static `_load_flat_sprite(path)`. `_split_set_aside_by_outcome` removed (no color routing needed). `_draw_held_row(label, count: int, outcome, …)` blits the same icon `count` times. `draw(...)` accepts only `set_aside_outcomes` and counts MIMIC / TREASURE inline.
**Why:** The right bar drops color entirely — banked green TREASURE and banked red TREASURE render as the same `treasure.png`. Color belongs to the felt only.

**File:** main.py
**Lines (at time of edit):** `StatsPanel` construction (~113), `stats_panel.draw` call (~471-480)
**Before:**
    `self.stats_panel = StatsPanel(self.dice_roller.settled_sprites)`; the draw call passed both `set_aside_colors=…` and `set_aside_outcomes=…`.
**After:**
    `self.stats_panel = StatsPanel()`; the draw call passes only `set_aside_outcomes=…`. The panel no longer reaches into `DiceRoller` for sprites.
**Why:** Matches the panel's new color-agnostic constructor + draw signature.

**File:** systems/bag.py
**Lines (at time of edit):** module docstring (~8)
**Before:**
    "(6 green / 4 purple / 3 red)".
**After:**
    "(6 green / 4 yellow / 3 red)".
**Why:** Reflects the renamed middle tier.

**File:** systems/bots.py
**Lines (at time of edit):** `lizzie_strategy` docstring (~122-123)
**Before:**
    "sometimes the remaining greens / purples still bust her".
**After:**
    "sometimes the remaining greens / yellows still bust her".
**Why:** Reflects the renamed middle tier.

**File:** README.md
**Lines (at time of edit):** Status (~22) and Rules section (~29)
**Before:**
    Status: "6 green / 4 purple / 3 red … per-color face distributions and the per-color settled-die art". Rules: "**4 purple dice** … (medium tier; replaces Zombie Dice's yellow body)".
**After:**
    Status: "6 green / 4 yellow / 3 red … Each die renders as a colored 1-6 pip face; the *number* on the die maps to its outcome via a per-color band". Rules: "**4 yellow dice** — 2 treasure, 2 empty, 2 mimic (medium tier)".
**Why:** Public-facing rules now match the actual game.

**File:** docs/ARCHITECTURE.md
**Lines (at time of edit):** §3.1 (DiceRoller bullets), §3.3 (settle paragraph), §3.4 (rewritten — per-color dice + pip-band table), §3.5 (Outcome + DieColor layer), §9.1 (bag reset), §9.3 (settle paragraph), §9.4 (stats panel)
**Before:**
    §3.1 referenced the single face row and `roll_all()`. §3.3 settle described picking a random face from the face row. §3.4 documented PURPLE and the per-(color, outcome) PNG table. §3.5 listed `DieColor.PURPLE` and only `roll_color`. §9.1 listed "6 GREEN + 4 PURPLE + 3 RED". §9.3 described `settled_sprites[(color, outcome)]` lookup. §9.4 described the panel sharing the tray's `settled_sprites`.
**After:**
    §3.1 documents the three pip rows + tumble row load and the `roll_with_results` entry point. §3.3 settle reads the pip face from `face_for_outcome`. §3.4 documents YELLOW, the per-color pip-band mapping with a new table, and notes the standalone PNGs are no longer mapped. §3.5 documents `DieColor.YELLOW`, `OUTCOME_FACE_NUMBERS`, and `face_for_outcome`. §9.1 lists "6 GREEN + 4 YELLOW + 3 RED". §9.3 settle reads the pip-face mapping. §9.4 documents the color-agnostic flat-icon panel.
**Why:** Architecture doc must reflect every system that changed shape.

**File:** docs/TODO.md
**Lines (at time of edit):** Phase 1 header block
**Before:**
    Phase 1 opened straight into the rules-engine `[x]` list with no callout.
**After:**
    Added a "Post-Phase 1 revision (2026-05-16)" blockquote at the top of Phase 1 explaining the PURPLE → YELLOW rename, the renderer rollback to colored 1-6 pip dice, the new per-color outcome → pip band, and the color-agnostic flat icons in the stats panel. Existing `[x]` items remain marked complete per the roadmap-maintenance rule; their parentheticals describe the original Phase 1 implementation, not the revised state.
**Why:** Roadmap-maintenance rule forbids unmarking completed items; the revision note keeps the file honest about the current code without rewriting history.

**Editor:** Frankie, with Claude (claude-opus-4-7) via Cowork.
