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
    WIDTH = 800
    HEIGHT = 600
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
    COLOR = ColorSettings.WORD_COLORS["MEDIUM_CARMINE"]
    BORDER_COLOR = ColorSettings.WORD_COLORS["GUARDSMEN_RED"]
    BORDER_THICKNESS = 2
    PORT_COLOR = ColorSettings.WORD_COLORS["BLACK"]
    PORT_RADIUS = 10
    # Vertical inset of the two input ports from the component's top and bottom
    # edges, in pixels. Used by Component when laying out its default ports.
    INPUT_PORT_INSET = 15

    # Font settings for component labels
    FONT = AssetPaths.FONT
    FONT_SIZE = 16
    BOLD = True

class AudioSettings:
    pass