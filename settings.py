class ColorSettings:
    WORD_COLORS = {
        "BLACK": (0, 0, 0),
        "WHITE": (255, 255, 255),
        "GRAY": (128, 128, 128),
        "RED": (255, 0, 0),
        "GREEN": (0, 255, 0),
        "BLUE": (0, 0, 255)
    }

class ScreenSettings:
    WIDTH = 800
    HEIGHT = 600
    RESOLUTION = (WIDTH, HEIGHT)
    BG_COLOR = ColorSettings.WORD_COLORS["BLACK"]
    FPS = 60
    TITLE = "Mr. Navarro's Logic Circuit Builder"

class FontSettings:
    TEXT_COLOR = ColorSettings.WORD_COLORS["WHITE"]

class UISettings:
    pass

class ComponentSettings:
    COLOR = ColorSettings.WORD_COLORS["GRAY"]
    BORDER_THICKNESS = 2
    BORDER_COLOR = ColorSettings.WORD_COLORS["WHITE"]

class AudioSettings:
    pass

class AssetPaths:
    pass