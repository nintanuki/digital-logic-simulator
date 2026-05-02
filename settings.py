import pygame

class ColorSettings:
    WORD_COLORS = {
        "BLACK": (0, 0, 0),
        "WHITE": (255, 255, 255),
        "GRAY": (128, 128, 128),
        "RED": (255, 0, 0),
        "GREEN": (0, 255, 0),
        "BLUE": (0, 0, 255),
        "ALLPORTS": (25, 75, 120),
        "JELLYBEAN": (70, 110, 140),
        "BERMUDA_GRAY": (120, 150, 160),
        "MEDIUM_CARMINE": (180, 60, 60),
        "GUARDSMEN_RED": (150, 45, 45),
        
    }

class ScreenSettings:
    WIDTH = 1280
    HEIGHT = 720
    RESOLUTION = (WIDTH, HEIGHT)
    BG_COLOR = ColorSettings.WORD_COLORS["JELLYBEAN"]
    FPS = 60
    TITLE = "Mr. Navarro's Logic Circuit Builder"
    CRT_ALPHA_RANGE = (75, 90)
    CRT_SCANLINE_HEIGHT = 3 # vertical pixels between scanlines drawn on the CRT overlay
    GRID_SIZE = 32

class InputSettings:
    LEFT_CLICK = 1
    MIDDLE_CLICK = 2
    RIGHT_CLICK = 3

class FontSettings:
    TEXT_COLOR = ColorSettings.WORD_COLORS["WHITE"]

class UISettings:
    BANK_HEIGHT = 100
    BANK_COLOR = (30, 30, 30)  # Darker than the background
    BANK_LINE_COLOR = (100, 100, 100)
    # The area at the bottom of the screen
    BANK_RECT = pygame.Rect(0, ScreenSettings.HEIGHT - BANK_HEIGHT, ScreenSettings.WIDTH, BANK_HEIGHT)

class AssetPaths:
    FONT = "assets/font/Pixeled.ttf"
    TV = "assets/graphics/tv.png"

class ComponentSettings:
    # Default body size for a freshly spawned component, used by
    # Component.__init__ when no explicit width/height is passed.
    DEFAULT_WIDTH = 100
    DEFAULT_HEIGHT = 60
    COLOR = ColorSettings.WORD_COLORS["MEDIUM_CARMINE"]
    BORDER_COLOR = ColorSettings.WORD_COLORS["GUARDSMEN_RED"]
    BORDER_THICKNESS = 2
    PORT_COLOR = ColorSettings.WORD_COLORS["BLACK"]
    # Highlight color used by Port.draw when the port is hovered. White was
    # chosen because it contrasts strongly with both the black resting color
    # and the dark red body, so the hover state reads at a glance. Reserve
    # green/red for future live-signal state per the roadmap.
    PORT_HIGHLIGHT_COLOR = ColorSettings.WORD_COLORS["WHITE"]
    PORT_RADIUS = 10
    # Vertical inset of the two input ports from the component's top and bottom
    # edges, in pixels. Used by Component when laying out its default ports.
    INPUT_PORT_INSET = 15

    # Font settings for component labels
    FONT = AssetPaths.FONT
    FONT_SIZE = 16
    BOLD = True

    # Port hover label. PORT_LABEL_OFFSET is the gap (in pixels) between the
    # port's center and the closest edge of the rendered text, so the label
    # sits clear of the port circle and the component body.
    PORT_LABEL_COLOR = ColorSettings.WORD_COLORS["WHITE"]
    PORT_LABEL_FONT_SIZE = 12
    PORT_LABEL_OFFSET = PORT_RADIUS + 6

class WireSettings:
    """Visual + interaction constants for wires between component ports."""
    COLOR = ColorSettings.WORD_COLORS["BLACK"]
    # Lighter gray so the in-flight ghost reads as "not yet committed".
    GHOST_COLOR = ColorSettings.WORD_COLORS["GRAY"]
    THICKNESS = 3
    # Pixel distance from the cursor to the wire segment that still counts as
    # a "hit" for right-click delete. Bigger than THICKNESS so users don't
    # have to land on the line exactly.
    HIT_THRESHOLD = 6


class AudioSettings:
    pass