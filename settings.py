import pygame

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

class ComponentSettings:
    COLOR = ColorSettings.WORD_COLORS["GRAY"]
    BORDER_THICKNESS = 2
    BORDER_COLOR = ColorSettings.WORD_COLORS["WHITE"]

class AudioSettings:
    pass

class AssetPaths:
    pass