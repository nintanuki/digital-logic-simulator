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
    # Horizontal padding for the first toolbox template and the gap between
    # adjacent templates. Pulled out of ComponentBank so the layout has no
    # magic numbers.
    BANK_PADDING_X = 20
    BANK_TEMPLATE_GAP = 20

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
    # and the dark red body, so the hover state reads at a glance.
    PORT_HIGHLIGHT_COLOR = ColorSettings.WORD_COLORS["WHITE"]
    # Fill color used by Port.draw when the port is carrying a live (HIGH)
    # signal and not currently hovered. Hover takes precedence so the user
    # always gets immediate cursor feedback.
    PORT_LIVE_COLOR = ColorSettings.WORD_COLORS["GREEN"]
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
    # Color used while the wire's source port is HIGH. Matches the live port
    # fill so a live signal reads continuously from output port through wire
    # to input port.
    LIVE_COLOR = ColorSettings.WORD_COLORS["GREEN"]
    # Lighter gray so the in-flight ghost reads as "not yet committed".
    GHOST_COLOR = ColorSettings.WORD_COLORS["GRAY"]
    THICKNESS = 3
    # Pixel distance from the cursor to the wire segment that still counts as
    # a "hit" for right-click delete. Bigger than THICKNESS so users don't
    # have to land on the line exactly.
    HIT_THRESHOLD = 6


class SwitchSettings:
    """Visual constants for the manual ON/OFF input source ('IN') component.

    Switch is rendered as a circle that fills the bounding rect, color-coded
    by toggle state. Border keeps it distinguishable against the background.
    """
    SIZE = 60
    OFF_COLOR = ColorSettings.WORD_COLORS["GRAY"]
    ON_COLOR = ColorSettings.WORD_COLORS["GREEN"]
    BORDER_COLOR = ColorSettings.WORD_COLORS["BLACK"]
    BORDER_THICKNESS = 2


class LedSettings:
    """Visual constants for the read-only output display ('OUT') component.

    LED is rendered as a circle whose fill color follows the live state of
    its single input port — bright when HIGH, dim when LOW.
    """
    SIZE = 60
    OFF_COLOR = ColorSettings.WORD_COLORS["GRAY"]
    ON_COLOR = ColorSettings.WORD_COLORS["GREEN"]
    BORDER_COLOR = ColorSettings.WORD_COLORS["BLACK"]
    BORDER_THICKNESS = 2


class TextBoxSettings:
    """Visual + interaction constants for free-floating annotation text boxes.

    Text boxes are draggable, editable labels students drop on the workspace
    to annotate their circuits. They carry no signal and never appear on the
    toolbox bank — they're spawned via keyboard shortcut at the cursor.
    """
    # Default body size for a freshly spawned text box. Width is fixed; the
    # box grows downward as wrapped text needs more lines, never below
    # MIN_HEIGHT so an empty box is still visibly grabbable.
    WIDTH = 180
    MIN_HEIGHT = 32
    # Inner padding between the body edge and the rendered text, in pixels.
    PADDING = 6
    # Body fill, border, and text colors. Body uses an alpha-less near-black
    # that reads against both the JELLYBEAN background and the toolbox bank.
    BODY_COLOR = (40, 40, 40)
    BORDER_COLOR = ColorSettings.WORD_COLORS["GRAY"]
    BORDER_THICKNESS = 1
    # Border switches to white while the box is focused so the user can see
    # which box is receiving keystrokes.
    BORDER_FOCUSED_COLOR = ColorSettings.WORD_COLORS["WHITE"]
    TEXT_COLOR = ColorSettings.WORD_COLORS["WHITE"]
    PLACEHOLDER_COLOR = ColorSettings.WORD_COLORS["GRAY"]
    PLACEHOLDER_TEXT = "Type here..."
    # Font face is reused across the project; size is its own knob so labels
    # don't have to match component-label sizing.
    FONT = AssetPaths.FONT
    FONT_SIZE = 12
    # Caret blink period (in milliseconds) and width. Caret is hidden during
    # the second half of each period so the eye sees it pulse.
    CARET_COLOR = ColorSettings.WORD_COLORS["WHITE"]
    CARET_WIDTH = 2
    CARET_BLINK_MS = 1000


class TextTemplateSettings:
    """Visual constants for the bank-side TEXT label that spawns text boxes.

    Renders as a square (matches Switch/LED) with the word "TEXT" centered on
    it, in the dark body color of an empty text box so the template visually
    previews what a click will spawn. No ports — text boxes carry no signal.
    """
    SIZE = 60
    # Mirror TextBoxSettings so the template reads as "the thing that spawns".
    BODY_COLOR = TextBoxSettings.BODY_COLOR
    BORDER_COLOR = TextBoxSettings.BORDER_COLOR
    BORDER_THICKNESS = TextBoxSettings.BORDER_THICKNESS
    LABEL = "TEXT"
    LABEL_COLOR = TextBoxSettings.TEXT_COLOR


class MenuButtonSettings:
    """Visual constants for the bottom-left MENU button on the toolbox bank.

    Anchors the far-left of the bank as a Windows-style "Start" affordance.
    The button itself only renders for now; clicking it will eventually open
    a vertical popup with project file ops (New / Load / Save / Quit). Sized
    to match the existing template row so the bank reads as one consistent
    strip.
    """
    SIZE = 60
    # Slightly lighter than BANK_COLOR so the button reads as a raised
    # control against the bank background instead of disappearing into it.
    BODY_COLOR = (60, 60, 60)
    BORDER_COLOR = ColorSettings.WORD_COLORS["WHITE"]
    BORDER_THICKNESS = 1
    LABEL = "MENU"
    LABEL_COLOR = ColorSettings.WORD_COLORS["WHITE"]


class AudioSettings:
    pass
