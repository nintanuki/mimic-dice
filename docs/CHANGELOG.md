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
