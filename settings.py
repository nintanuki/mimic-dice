import os

class ColorSettings:
    """Class to hold all the color settings for the game."""
    BLACK = (0, 0, 0)
    NERO = (30, 30, 30)
    WHITE = (255, 255, 255)
    RED = (255, 0, 0)
    GREEN = (0, 255, 0)
    BLUE = (0, 0, 255)

    BG_COLOR = NERO
    OVERLAY_BACKGROUND = WHITE

class ScreenSettings:
    """Class to hold all the settings related to the screen."""
    WIDTH = 800
    HEIGHT = 600
    RESOLUTION = (WIDTH, HEIGHT)
    FPS = 60
    CRT_ALPHA_RANGE = (75, 90)
    CRT_SCANLINE_HEIGHT = 3
    TITLE = "Mimic Dice"
    UI_BORDER_WIDTH = 2

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
    MUTE_MUSIC = False  # Keep music disabled while retaining sound effects.
    MUSIC_VOLUME = 1  # Background music volume in the range [0.0, 1.0].

class AssetPaths:
    """Class to hold all the file paths for assets."""
    DICE_SHEET = "assets/graphics/sprites/six_sided_die.png"
    DIE_SIZE = 16  # Source tile size on the sprite sheet (square).
    DICE_FACE_ROW = 0     # Row index on the sheet for settled white faces.
    DICE_TUMBLE_ROW = 14  # Row index on the sheet for white tumble poses.
    DICE_TUMBLE_FRAME_COUNT = 6
    TV = "assets/graphics/effects/tv.png"

class DiceSettings:
    """Dice rendering, tray bounds, and roll physics."""

    # ---- Visuals ----
    COUNT = 3
    SCALE = 2  # Source-pixel scale factor applied to every die sprite.

    # ---- Tray placement (top-left anchored, in window pixels) ----
    TRAY_PADDING = (32, 32)        # Empty space left/top of the tray.
    TRAY_SIZE = (480, 360)         # Tray width/height in window pixels.
    TRAY_BORDER_COLOR = (220, 220, 220)
    TRAY_INNER_MARGIN = 4          # Physics inset from the visible border.

    # ---- Throw ----
    # Origin corner of the tray that dice are thrown from.
    # One of: "bottom_left", "bottom_right", "top_left", "top_right".
    THROW_ORIGIN = "bottom_left"
    THROW_SPAWN_OFFSET = 24        # How far outside the tray dice spawn (px).
    THROW_ANGLE_DEG = -55          # Aim angle (0=right, -90=up).
    THROW_ANGLE_SPREAD_DEG = 25    # +/- random spread per die so they fan out.
    THROW_SPEED_MIN = 600          # Initial speed range in px/sec.
    THROW_SPEED_MAX = 850

    # ---- Physics ----
    LINEAR_DRAG = 1.6              # Per-second exponential velocity decay.
    RESTITUTION = 0.65             # Velocity retained after a wall bounce.
    SETTLE_SPEED = 40              # Below this speed (px/sec) the die settles.

    # ---- Tumble animation ----
    TUMBLE_FPS_MIN = 10            # Tumble frame rate near settle.
    TUMBLE_FPS_MAX = 30            # Tumble frame rate at peak speed.

class DebugSettings:
    """Settings related to debugging features."""
    MUTE = False # Force mute all sound output during testing.
    DISABLE_CRT = True # Disable the CRT overlay for easier visual debugging.