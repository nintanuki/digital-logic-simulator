import pygame

from settings import ColorSettings, ComponentSettings

class Component:
    def __init__(self, x, y, width=60, height=40, name="AND"):
        self.rect = pygame.Rect(x, y, width, height)
        self.color = ComponentSettings.COLOR
        self.name = name
        self.dragging = False
        self.offset_x = 0
        self.offset_y = 0

    def draw(self, surface):
        # Draw the main body
        pygame.draw.rect(surface, self.color, self.rect)
        # Add a border
        pygame.draw.rect(surface, ComponentSettings.BORDER_COLOR, self.rect, ComponentSettings.BORDER_THICKNESS)
        
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1 and self.rect.collidepoint(event.pos):
                self.dragging = True
                # Capture where on the gate we clicked so it doesn't "snap" to top-left
                self.offset_x = self.rect.x - event.pos[0]
                self.offset_y = self.rect.y - event.pos[1]
                
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                self.dragging = False
            
        elif event.type == pygame.MOUSEMOTION:
            if self.dragging:
                self.rect.x = event.pos[0] + self.offset_x
                self.rect.y = event.pos[1] + self.offset_y