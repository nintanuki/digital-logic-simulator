import pygame

from settings import ComponentSettings


class Fonts:
    """Shared Font instances used across the game.

    pygame's font subsystem is global, but every `pygame.font.Font(path, size)`
    call still re-reads the .ttf from disk. Component used to do that inside
    its __init__, so each spawned gate reloaded the same face. This class
    loads each face once via init() and exposes the cached instances as class
    attributes for the rest of the codebase to use.
    """

    # Populated by init(). Declared here so editors can autocomplete and so a
    # render() call before init() fails loudly with AttributeError on None
    # rather than silently using a default font.
    component_label = None
    port_label = None

    @classmethod
    def init(cls):
        """Initialize the font subsystem and load every cached face.

        Must be called once at startup, after pygame.init() and before any
        draw() that renders text.
        """
        pygame.font.init()
        cls.component_label = pygame.font.Font(
            ComponentSettings.FONT,
            ComponentSettings.FONT_SIZE,
        )
        cls.port_label = pygame.font.Font(
            ComponentSettings.FONT,
            ComponentSettings.PORT_LABEL_FONT_SIZE,
        )
