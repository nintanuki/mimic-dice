"""Central configuration for Mimic Dice.

All tunable values live here so the rest of the code never contains magic
numbers. Each settings class groups constants by subsystem; comments explain
what every value means in plain language so designers can tweak feel without
reading the gameplay code.
"""

import os


class ColorSettings:
    """Named RGB colors and the role-based aliases that reference them."""

    # ---- Raw palette (only add new named colors here) ----
    BLACK = (0, 0, 0)
    NERO = (30, 30, 30)            # Near-black used for the window background.
    WHITE = (255, 255, 255)
    RED = (255, 0, 0)
    GREEN = (0, 255, 0)
    BLUE = (0, 0, 255)
    LIGHT_GREY = (220, 220, 220)
    VELVET_GREEN = (24, 78, 56)    # Deep felt green, classic gaming-table look.
    MAROON = (96, 28, 36)          # Deep red felt, alternative tray color.

    # ---- Role aliases (reference the palette above) ----
    BG_COLOR = NERO                # Color filled behind everything each frame.
    OVERLAY_BACKGROUND = WHITE     # Base color used by the CRT scanline overlay.
    TRAY_BORDER_COLOR = LIGHT_GREY # Outline drawn around the dice tray.
    TRAY_FILL_COLOR = VELVET_GREEN # Inside of the dice tray (felt surface).


class ScreenSettings:
    """Window, frame-rate, and post-processing constants."""

    WIDTH = 800
    HEIGHT = 600
    RESOLUTION = (WIDTH, HEIGHT)
    FPS = 60
    TITLE = "Mimic Dice"

    # Width in pixels of any thin UI outline (tray border, debug rects, ...).
    UI_BORDER_WIDTH = 2

    # CRT overlay: per-frame random alpha (min, max) creates the flicker.
    CRT_ALPHA_RANGE = (75, 90)
    CRT_SCANLINE_HEIGHT = 3        # Vertical spacing between scanlines (px).
    CRT_SCANLINE_LINE_WIDTH = 1    # Thickness of each scanline (px).


class InputSettings:
    """Controller button and axis mappings used by gameplay and menus.

    Constants are named after the physical button on the controller, not the
    action it performs. The only exception is JOY_BUTTON_QUIT_COMBO, which is
    a special multi-button chord rather than a single button.
    """

    JOY_BUTTON_A = 0
    JOY_BUTTON_B = 1
    JOY_BUTTON_X = 2
    JOY_BUTTON_Y = 3
    JOY_BUTTON_L1 = 4
    JOY_BUTTON_R1 = 5
    JOY_BUTTON_BACK = 6
    JOY_BUTTON_START = 7
    JOY_BUTTON_QUIT_COMBO = (7, 6, 4, 5)

    JOY_AXIS_LEFT_X = 0
    JOY_AXIS_LEFT_Y = 1
    JOY_AXIS_L2 = 4
    JOY_AXIS_R2 = 5
    JOY_TRIGGER_THRESHOLD = 0.5


class FontSettings:
    """Font files, sizes, and text-color mappings for UI rendering."""

    FONT = os.path.join(
        os.path.dirname(__file__), 'assets', 'font', 'Pixeled.ttf'
    )


class AudioSettings:
    """Global audio toggles and mixer-level defaults."""

    MUTE = False
    MUTE_MUSIC = False             # Keep music off while sound effects play.
    MUSIC_VOLUME = 1               # Background music volume in [0.0, 1.0].


class AssetPaths:
    """File paths for every external asset, plus sprite-sheet layout info.

    Keeping the row/frame-count constants here means the rest of the code
    never references the sheet's raw geometry directly.
    """

    # ---- Files ----
    DICE_SHEET = "assets/graphics/sprites/six_sided_die.png"
    TV = "assets/graphics/effects/tv.png"

    # ---- Dice sprite sheet layout ----
    DIE_TILE_SIZE = 16             # Source tile size on the sheet (square px).
    DIE_FACE_ROW = 0               # Row index for settled white faces (1..6).
    DIE_TUMBLE_ROW = 14            # Row index for white mid-tumble poses.
    DIE_FACE_COUNT = 6             # Number of distinct settled faces.
    DIE_TUMBLE_FRAME_COUNT = 6     # Number of mid-tumble frames in that row.


class DiceSettings:
    """Visuals, tray geometry, and roll physics for the animated dice.

    The dice subsystem is composed of three roles:
      * `DiceRoller`  - orchestrates a roll: owns the tray and the dice list.
      * `DiceTray`    - the rectangular play area dice bounce inside.
      * `AnimatedDie` - one die's physics body + frame animation + sprite.

    A frame of gameplay flows: GameManager -> DiceRoller.update(dt)
    -> AnimatedDie.update(dt, tray bounds) for each die.
    """

    # ---- Visuals ----
    COUNT = 3                      # How many dice are rolled at once.
    SCALE = 2                      # Pixel-art scale factor for every die sprite.

    # ---- Tray placement (top-left anchored, in window pixels) ----
    TRAY_PADDING = (32, 32)        # Empty space left/top of the tray.
    TRAY_SIZE = (480, 360)         # Tray width/height in window pixels.
    TRAY_CORNER_RADIUS = 8         # Border-corner curvature in pixels (0 = sharp).
    TRAY_INNER_MARGIN = 4          # Physics inset from the visible border.

    # ---- Throw ----
    # Origin corner of the tray that dice are thrown from.
    # One of: "bottom_left", "bottom_right", "top_left", "top_right".
    THROW_ORIGIN = "bottom_left"
    THROW_SPAWN_OFFSET = 24        # How far outside the tray dice spawn (px).
    THROW_ANGLE_DEG = -55          # Aim angle (0 = right, -90 = straight up).
    THROW_ANGLE_SPREAD_DEG = 25    # +/- random spread per die so they fan out.
    THROW_SPEED_MIN = 600          # Initial speed range, in pixels/second.
    THROW_SPEED_MAX = 850

    # ---- Physics ----
    # Exponential drag: each second the speed is multiplied by exp(-LINEAR_DRAG).
    # Higher values = dice slow down faster. Frame-rate independent.
    LINEAR_DRAG = 1.6
    RESTITUTION = 0.65             # Velocity retained after a wall bounce.
    SETTLE_SPEED = 40              # Below this speed (px/s) the die settles.

    # ---- Tumble animation ----
    # The tumble frame rate scales linearly between MIN (near settle speed)
    # and MAX (at peak throw speed) so fast dice visibly spin faster.
    TUMBLE_FPS_MIN = 10
    TUMBLE_FPS_MAX = 30


class DebugSettings:
    """Toggles useful while developing; should all be False for release."""

    MUTE = False                   # Force-mute every sound channel.
    DISABLE_CRT = True             # Skip the CRT overlay for cleaner visuals.
