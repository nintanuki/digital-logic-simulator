import pygame
from settings import InputSettings, UISettings, ScreenSettings, ComponentSettings
from elements import Component

class ComponentBank:
    def __init__(self):
        self.rect = UISettings.BANK_RECT
        # These are the "buttons" or templates students can click
        # We start with just the universal NAND gate
        self.template = Component(20, self.rect.y + 25, name="NAND")

    def draw(self, surface):
        # Draw background
        pygame.draw.rect(surface, UISettings.BANK_COLOR, self.rect)
        pygame.draw.line(surface, UISettings.BANK_LINE_COLOR, (0, self.rect.y), (ScreenSettings.WIDTH, self.rect.y), 2)

        # Draw the visual representations
        self.template.draw(surface)

    def handle_event(self, event, components_list):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == InputSettings.LEFT_CLICK:
            if self.template.rect.collidepoint(event.pos):
                # Spawn a new NAND gate
                new_comp = Component(event.pos[0] - 40, event.pos[1] - 25, name=self.template.name)
                new_comp.dragging = True # Start dragging it immediately
                components_list.append(new_comp)
                return True # Event handled
        return False