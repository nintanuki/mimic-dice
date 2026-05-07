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