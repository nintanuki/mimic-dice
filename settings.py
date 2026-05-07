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
    TV = "assets/graphics/effects/tv.png"

class DebugSettings:
    """Settings related to debugging features."""
    MUTE = False # Force mute all sound output during testing.