import pygame
from settings import UISettings, ScreenSettings, ComponentSettings
from elements import Component

class ComponentBank:
    def __init__(self):
        self.rect = UISettings.BANK_RECT
        # These are the "buttons" or templates students can click
        self.templates = [
            {"name": "AND", "rect": pygame.Rect(20, self.rect.y + 20, 60, 40)},
            {"name": "OR",  "rect": pygame.Rect(100, self.rect.y + 20, 60, 40)},
            {"name": "NOT", "rect": pygame.Rect(180, self.rect.y + 20, 60, 40)}
        ]

    def draw(self, surface):
        # Draw the bank background
        pygame.draw.rect(surface, UISettings.BANK_COLOR, self.rect)
        pygame.draw.line(surface, UISettings.BANK_LINE_COLOR, (0, self.rect.y), (ScreenSettings.WIDTH, self.rect.y), 2)

        # Draw the template options
        for temp in self.templates:
            pygame.draw.rect(surface, (60, 60, 60), temp["rect"])
            pygame.draw.rect(surface, (200, 200, 200), temp["rect"], 1)
            # (Optional) You'd eventually render text here for "AND", "OR", etc.

    def handle_event(self, event, components_list):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                for temp in self.templates:
                    if temp["rect"].collidepoint(event.pos):
                        # BINGO: Create a NEW component and add it to the world
                        new_comp = Component(event.pos[0] - 30, event.pos[1] - 20, name=temp["name"])
                        new_comp.dragging = True # Start dragging it immediately
                        components_list.append(new_comp)
                        return True # Event handled
        return False