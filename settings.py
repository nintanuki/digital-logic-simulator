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

    # Curated palette for saved-component body colors. Each save picks one
    # at random so sibling abstractions are visually distinct at a glance.
    # Colors are muted / medium-brightness so the white name label stays
    # readable on top without needing a separate contrast check.
    SAVED_COMPONENT_COLORS = (
        (180, 60, 60),   # carmine (existing default, kept in pool)
        (60, 120, 180),  # steel blue
        (60, 160, 80),   # muted green
        (160, 100, 40),  # amber
        (120, 60, 160),  # purple
        (155, 135, 40),  # gold
        (40, 140, 140),  # teal
        (160, 80, 130),  # rose
    )

class ScreenSettings:
    WIDTH = 1280
    HEIGHT = 720
    RESOLUTION = (WIDTH, HEIGHT)
    BG_COLOR = ColorSettings.WORD_COLORS["JELLYBEAN"]
    FPS = 60
    TITLE = "Digital Logic Simulator"
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


class ShortcutBarSettings:
    """Visual constants for the top-of-screen hotkey hint strip."""

    HEIGHT = 28
    BG_COLOR = ColorSettings.WORD_COLORS["BLACK"]
    TEXT_COLOR = ColorSettings.WORD_COLORS["WHITE"]
    BORDER_COLOR = ColorSettings.WORD_COLORS["GRAY"]
    PADDING_X = 8
    ITEM_MIN_GAP = 12


class ErrorBannerSettings:
    """Visual constants for the recoverable-error overlay banner.

    The banner appears just below the shortcut bar when the per-frame
    try/except in GameManager.run() catches an unhandled exception. It
    stays visible for DISPLAY_MS milliseconds then disappears, leaving
    the app in whatever state it was in before the crash so the student
    can keep working.
    """

    # How long the banner stays on screen before automatically clearing.
    DISPLAY_MS = 5000
    HEIGHT = 36
    BG_COLOR = (160, 30, 30)   # dark red — clearly an error, not a normal UI bar
    TEXT_COLOR = ColorSettings.WORD_COLORS["WHITE"]
    PADDING_X = 16

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
    # Saved-component wrappers compute height from exposed port count so
    # multi-input/output abstractions keep clear spacing. Height formula:
    # (max_ports - 1) * SAVED_PORT_PITCH + 2 * SAVED_PORT_VERTICAL_PADDING.
    SAVED_PORT_PITCH = 18
    SAVED_PORT_VERTICAL_PADDING = 15

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
    # Selection outline for selected components.
    SELECTION_COLOR = ColorSettings.WORD_COLORS["WHITE"]
    SELECTION_BORDER_THICKNESS = 2


class SelectionBoxSettings:
    """Visual constants for drag-to-select marquee rectangle."""

    BORDER_COLOR = ColorSettings.WORD_COLORS["WHITE"]
    FILL_COLOR = (255, 255, 255, 40)
    BORDER_THICKNESS = 1
    # Treat tiny drags as plain clicks (clear selection) instead of marquee.
    MIN_DRAG_PIXELS = 4

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
    """Visual constants for the manual ON/OFF input toggle ('IN') component.

    Switch is rendered as a horizontal sliding toggle: a rounded-rectangle
    body with a knob that moves left (OFF / 0) or right (ON / 1). A state
    label on the empty side of the knob shows the current value explicitly.
    """
    WIDTH = 80
    HEIGHT = 44
    KNOB_RADIUS = 16
    KNOB_MARGIN = 6          # gap between knob center and body edge
    BODY_CORNER = 10         # border_radius for the outer rounded rectangle
    BODY_OFF_COLOR = (50, 50, 50)
    BODY_ON_COLOR = (28, 65, 28)
    TRACK_COLOR = (22, 22, 22)
    TRACK_HEIGHT = 14
    KNOB_OFF_COLOR = (140, 140, 140)
    KNOB_ON_COLOR = (75, 185, 75)
    BORDER_COLOR = ColorSettings.WORD_COLORS["BLACK"]
    BORDER_THICKNESS = 2
    LABEL_COLOR = (210, 210, 210)


class LedSettings:
    """Visual constants for the read-only output LED bulb ('OUT') component.

    LED is rendered as a light-bulb silhouette: a round globe with a small
    rectangular base/lead below it. A wider glow ring appears around the
    globe when the signal is HIGH.
    """
    SIZE = 60                  # bounding box stays square
    BULB_RADIUS = 20
    BULB_Y_OFFSET = 22         # bulb center = rect.y + BULB_Y_OFFSET
    BASE_WIDTH = 18
    BASE_HEIGHT = 10
    BASE_Y_OFFSET = 46         # base rect.top = rect.y + BASE_Y_OFFSET
    BASE_CORNER = 3
    GLOW_EXTRA_RADIUS = 7      # glow circle radius = BULB_RADIUS + this
    OFF_GLOBE_COLOR = (55, 55, 55)
    ON_GLOBE_COLOR = (255, 220, 50)
    OFF_BASE_COLOR = (40, 40, 40)
    ON_BASE_COLOR = (175, 145, 25)
    GLOW_COLOR = (255, 200, 30)
    BORDER_COLOR = ColorSettings.WORD_COLORS["BLACK"]
    BORDER_THICKNESS = 2


class TextBoxSettings:
    """Visual + interaction constants for free-floating annotation text boxes.

    Text boxes are draggable, editable labels students drop on the workspace
    to annotate their circuits. They carry no signal and never appear on the
    toolbox bank — they're spawned via keyboard shortcut at the cursor.
    """
    # New text boxes start narrow, grow wider as the user types, then wrap
    # and grow downward once MAX_WIDTH is reached.
    MIN_WIDTH = 44
    MAX_WIDTH = 180
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
    PLACEHOLDER_TEXT = "..."
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
    Clicking the button toggles a popup that floats above the bank — file
    ops items (New / Load / Save / Quit) land in a follow-up step. Sized to
    match the existing template row so the bank reads as one consistent
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
    # Items shown in the popup, top-to-bottom.
    #
    # IMPORTANT: behavior dispatch must use stable IDs, not labels. Labels
    # are presentation-only and can be renamed freely in settings without
    # changing what each menu item does.
    ITEMS = (
        ("new_project", "NEW PROJECT"),
        ("load_project", "LOAD PROJECT"),
        ("save_project", "SAVE PROJECT"),
        ("save_project_as", "SAVE PROJECT AS"),
        ("save_as_component", "SAVE AS COMPONENT"),
        ("quit", "QUIT"),
    )
    ITEM_IDS = tuple(item_id for item_id, _label in ITEMS)
    ITEM_LABELS = tuple(label for _item_id, label in ITEMS)
    # Vertical pitch per item inside the popup. The label baseline and
    # (once it lands) each item's hit-rect both anchor to this value, so
    # bumping it shifts both in sync.
    ITEM_HEIGHT = 32
    # Horizontal inset for an item label from the popup's left edge, so
    # text doesn't kiss the popup border.
    ITEM_PADDING_X = 10
    # Greyed-out label color used while the item has no action wired up.
    # Dimmer than the white MENU label so an enabled item reads as the
    # active affordance against this disabled baseline.
    ITEM_DISABLED_COLOR = (140, 140, 140)
    # Label color used for an item that has an action wired up. Matches
    # the white MENU button label so the affordance reads as part of the
    # same control surface.
    ITEM_ENABLED_COLOR = ColorSettings.WORD_COLORS["WHITE"]
    # Popup container that appears above the button when the menu is open.
    # Width is sized to fit the longest item label ("SAVE AS COMPONENT"
    # measures ~197px in the Pixeled face at FONT_SIZE 12) with the
    # ITEM_PADDING_X inset on the left and a small visual margin on the
    # right; height is derived from the item count so adding/removing
    # entries only requires touching ITEM_LABELS. Color matches the
    # button body so the popup reads as an extension of the same control.
    POPUP_WIDTH = 220
    POPUP_HEIGHT = len(ITEMS) * ITEM_HEIGHT
    POPUP_BODY_COLOR = (60, 60, 60)
    POPUP_BORDER_COLOR = ColorSettings.WORD_COLORS["WHITE"]
    POPUP_BORDER_THICKNESS = 1
    # Vertical gap between the top of the button and the bottom of the
    # popup so the popup doesn't visually fuse with the button.
    POPUP_GAP = 4


class SaveComponentDialogSettings:
    """Visual + interaction constants for the SAVE AS COMPONENT dialog.

    A small modal panel that opens from the bottom-left popup's SAVE AS
    COMPONENT item. The left side captures the saved component name and
    save/cancel actions; the right side captures explicit RGB values for
    the wrapper body color.

    Modal: while the dialog is open it consumes every mouse + keyboard
    event so the workspace beneath is paused (mirrors how text-box
    editing pre-empts the rest of the input pipeline). Click-outside is
    deliberately a no-op rather than a dismiss — a typed-in name is too
    easy to lose accidentally, unlike the bottom-left popup where
    click-outside-cancels is fine because there's no in-flight work.
    """
    # Centered on the screen. Left panel stays compact for name/buttons;
    # right panel hosts three stacked RGB fields with matching side padding.
    WIDTH = 420
    HEIGHT = 220
    BODY_COLOR = (40, 40, 40)
    BORDER_COLOR = ColorSettings.WORD_COLORS["WHITE"]
    BORDER_THICKNESS = 2
    PADDING = 16
    # Vertical gap between the title and the name field.
    SECTION_GAP = 12
    PANEL_GAP = 12
    LEFT_PANEL_WIDTH = 260

    # Title
    TITLE = "SAVE AS COMPONENT"
    TITLE_COLOR = ColorSettings.WORD_COLORS["WHITE"]

    # Name field
    NAME_FIELD_HEIGHT = 32
    NAME_FIELD_BG = (60, 60, 60)
    NAME_FIELD_BORDER = (120, 120, 120)
    NAME_FIELD_BORDER_FOCUSED = ColorSettings.WORD_COLORS["WHITE"]
    NAME_FIELD_TEXT_COLOR = ColorSettings.WORD_COLORS["WHITE"]
    NAME_FIELD_PLACEHOLDER = "TYPE A NAME..."
    NAME_FIELD_PLACEHOLDER_COLOR = (140, 140, 140)
    NAME_FIELD_PADDING_X = 8
    # Caps both rendered width and save-file bloat. 24 fits "FULL ADDER"
    # / "RIPPLE CARRY ADDER 4BIT" comfortably; longer is a smell anyway.
    NAME_MAX_LENGTH = 24
    NAME_CARET_BLINK_MS = 1000
    NAME_CARET_WIDTH = 2

    # RGB fields (right panel)
    RGB_TITLE = "COLOR"
    RGB_LABEL_COLOR = ColorSettings.WORD_COLORS["WHITE"]
    RGB_FIELD_WIDTH = 78
    RGB_FIELD_HEIGHT = 30
    RGB_FIELD_GAP = 10
    RGB_LABEL_FIELD_GAP = 8
    RGB_FIELD_BG = NAME_FIELD_BG
    RGB_FIELD_BORDER = NAME_FIELD_BORDER
    RGB_FIELD_BORDER_FOCUSED = NAME_FIELD_BORDER_FOCUSED
    RGB_FIELD_TEXT_COLOR = NAME_FIELD_TEXT_COLOR
    RGB_FIELD_PLACEHOLDER = "RGB"
    RGB_FIELD_PLACEHOLDER_COLOR = NAME_FIELD_PLACEHOLDER_COLOR
    RGB_FIELD_PADDING_X = 8
    RGB_MAX_LENGTH = 3
    DEFAULT_RGB = ColorSettings.WORD_COLORS["MEDIUM_CARMINE"]

    # Live swatch between name field and action buttons.
    PREVIEW_LABEL = "PREVIEW"
    PREVIEW_LABEL_COLOR = ColorSettings.WORD_COLORS["WHITE"]
    PREVIEW_HEIGHT = 28
    PREVIEW_MIN_TOP_GAP = 14
    PREVIEW_MIN_BOTTOM_GAP = 14
    PREVIEW_BG = (24, 24, 24)
    PREVIEW_BORDER = (120, 120, 120)

    # Save / Cancel buttons
    BUTTON_WIDTH = 120
    BUTTON_HEIGHT = 36
    BUTTON_GAP = 12
    BUTTON_BG_ENABLED = (70, 110, 70)
    BUTTON_BG_DISABLED = (60, 60, 60)
    BUTTON_BG_CANCEL = (110, 60, 60)
    BUTTON_TEXT_COLOR_ENABLED = ColorSettings.WORD_COLORS["WHITE"]
    BUTTON_TEXT_COLOR_DISABLED = (140, 140, 140)
    BUTTON_BORDER_COLOR = (120, 120, 120)
    BUTTON_LABEL_SAVE = "SAVE"
    BUTTON_LABEL_CANCEL = "CANCEL"

    # Translucent backdrop dim while the dialog is open so the workspace
    # behind reads as "paused." Alpha is moderate — enough to push the
    # workspace back without making the dialog feel like it's floating in
    # the void.
    BACKDROP_COLOR = (0, 0, 0)
    BACKDROP_ALPHA = 140


class QuitConfirmDialogSettings:
    """Visual + interaction constants for the Esc quit-confirmation dialog."""

    WIDTH = 300
    HEIGHT = 160
    BODY_COLOR = (40, 40, 40)
    BORDER_COLOR = ColorSettings.WORD_COLORS["WHITE"]
    BORDER_THICKNESS = 2
    PADDING = 20
    SECTION_GAP = 14

    TITLE = "QUIT?"
    TITLE_COLOR = ColorSettings.WORD_COLORS["WHITE"]
    MESSAGE = "ARE YOU SURE?"
    MESSAGE_COLOR = (200, 200, 200)

    BUTTON_WIDTH = 100
    BUTTON_HEIGHT = 36
    BUTTON_GAP = 16
    BUTTON_BG_YES = (130, 50, 50)
    BUTTON_BG_NO = (60, 60, 60)
    BUTTON_TEXT_COLOR = ColorSettings.WORD_COLORS["WHITE"]
    BUTTON_BORDER_COLOR = (120, 120, 120)
    BUTTON_LABEL_YES = "YES"
    BUTTON_LABEL_NO = "NO"

    BACKDROP_COLOR = (0, 0, 0)
    BACKDROP_ALPHA = 140


class SaveProjectDialogSettings:
    """Visual + interaction constants for the SAVE AS dialog.

    The dialog shows a scrollable list of existing projects (click to select /
    overwrite) plus a text field to type a new name.  A warning row appears
    when the typed name matches an existing project that was *not* selected
    from the list, reminding the user that saving will overwrite it.
    """

    WIDTH = 380
    HEIGHT = 370
    BODY_COLOR = (40, 40, 40)
    BORDER_COLOR = ColorSettings.WORD_COLORS["WHITE"]
    BORDER_THICKNESS = 2
    PADDING = 16
    SECTION_GAP = 10

    TITLE = "SAVE AS"
    TITLE_COLOR = ColorSettings.WORD_COLORS["WHITE"]

    # Scrollable list of existing projects (mirrors LoadProjectDialogSettings).
    LIST_ITEM_HEIGHT = 32
    LIST_ITEM_BG = (55, 55, 55)
    LIST_ITEM_BG_HOVER = (80, 80, 80)
    LIST_ITEM_BG_SELECTED = (60, 100, 60)
    LIST_ITEM_TEXT_COLOR = ColorSettings.WORD_COLORS["WHITE"]
    LIST_ITEM_BORDER = (80, 80, 80)
    LIST_MAX_VISIBLE = 5
    EMPTY_MESSAGE = "NO SAVED PROJECTS YET"
    EMPTY_MESSAGE_COLOR = (140, 140, 140)

    # Name input field shown below the list.
    NAME_FIELD_HEIGHT = 32
    NAME_FIELD_BG = (60, 60, 60)
    NAME_FIELD_BORDER = (120, 120, 120)
    NAME_FIELD_BORDER_FOCUSED = ColorSettings.WORD_COLORS["WHITE"]
    NAME_FIELD_TEXT_COLOR = ColorSettings.WORD_COLORS["WHITE"]
    NAME_FIELD_PLACEHOLDER = "NEW PROJECT NAME..."
    NAME_FIELD_PLACEHOLDER_COLOR = (140, 140, 140)
    NAME_FIELD_PADDING_X = 8
    NAME_MAX_LENGTH = 32
    NAME_CARET_BLINK_MS = 1000
    NAME_CARET_WIDTH = 2

    # Warning shown when the typed name collides with an existing project.
    WARNING_TEXT = "OVERWRITE AN EXISTING PROJECT?!"
    WARNING_COLOR = (220, 160, 60)
    WARNING_HEIGHT = 20

    BUTTON_WIDTH = 120
    BUTTON_HEIGHT = 36
    BUTTON_GAP = 12
    BUTTON_BG_ENABLED = (70, 110, 70)
    BUTTON_BG_DISABLED = (60, 60, 60)
    BUTTON_BG_CANCEL = (110, 60, 60)
    BUTTON_TEXT_COLOR_ENABLED = ColorSettings.WORD_COLORS["WHITE"]
    BUTTON_TEXT_COLOR_DISABLED = (140, 140, 140)
    BUTTON_BORDER_COLOR = (120, 120, 120)
    BUTTON_LABEL_SAVE = "SAVE"
    BUTTON_LABEL_CANCEL = "CANCEL"

    BACKDROP_COLOR = (0, 0, 0)
    BACKDROP_ALPHA = 140


class LoadProjectDialogSettings:
    """Visual + interaction constants for the LOAD PROJECT dialog."""

    WIDTH = 380
    HEIGHT = 320
    BODY_COLOR = (40, 40, 40)
    BORDER_COLOR = ColorSettings.WORD_COLORS["WHITE"]
    BORDER_THICKNESS = 2
    PADDING = 16
    SECTION_GAP = 10

    TITLE = "LOAD PROJECT"
    TITLE_COLOR = ColorSettings.WORD_COLORS["WHITE"]

    EMPTY_MESSAGE = "NO SAVED PROJECTS FOUND"
    EMPTY_MESSAGE_COLOR = (140, 140, 140)

    # Scrollable list of project entries.
    LIST_ITEM_HEIGHT = 32
    LIST_ITEM_BG = (55, 55, 55)
    LIST_ITEM_BG_HOVER = (80, 80, 80)
    LIST_ITEM_BG_SELECTED = (60, 100, 60)
    LIST_ITEM_TEXT_COLOR = ColorSettings.WORD_COLORS["WHITE"]
    LIST_ITEM_BORDER = (80, 80, 80)
    LIST_MAX_VISIBLE = 6   # items shown without scrolling

    BUTTON_WIDTH = 120
    BUTTON_HEIGHT = 36
    BUTTON_GAP = 12
    BUTTON_BG_ENABLED = (70, 110, 70)
    BUTTON_BG_DISABLED = (60, 60, 60)
    BUTTON_BG_CANCEL = (110, 60, 60)
    BUTTON_TEXT_COLOR_ENABLED = ColorSettings.WORD_COLORS["WHITE"]
    BUTTON_TEXT_COLOR_DISABLED = (140, 140, 140)
    BUTTON_BORDER_COLOR = (120, 120, 120)
    BUTTON_LABEL_LOAD = "LOAD"
    BUTTON_LABEL_CANCEL = "CANCEL"

    BACKDROP_COLOR = (0, 0, 0)
    BACKDROP_ALPHA = 140


class AudioSettings:
    pass
