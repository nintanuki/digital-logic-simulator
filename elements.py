import pygame

from settings import ColorSettings, ComponentSettings, InputSettings

class Component:
    def __init__(self, x, y, width=80, height=50, name="NAND"):
        self.rect = pygame.Rect(x, y, width, height)
        self.color = ComponentSettings.COLOR
        self.name = name
        self.dragging = False
        self.offset_x = 0
        self.offset_y = 0

        # Initialize font for names
        pygame.font.init()
        self.font = pygame.font.SysFont("Arial", 16, bold=True)

    def draw(self, surface):
        # Draw the main body (The Rectangle)
        pygame.draw.rect(surface, self.color, self.rect)
        
        # Draw the border
        pygame.draw.rect(
            surface, 
            ComponentSettings.BORDER_COLOR, 
            self.rect, 
            ComponentSettings.BORDER_THICKNESS
        )

        # Draw the Name Label
        text_surf = self.font.render(self.name, True, ColorSettings.WORD_COLORS["WHITE"])
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)
        
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == InputSettings.LEFT_CLICK and self.rect.collidepoint(event.pos):
                self.dragging = True
                # Capture where on the gate we clicked so it doesn't "snap" to top-left of the image
                self.offset_x = self.rect.x - event.pos[0]
                self.offset_y = self.rect.y - event.pos[1]
            elif event.button == InputSettings.RIGHT_CLICK:
                    return "DELETE"
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == InputSettings.LEFT_CLICK: self.dragging = False
        elif event.type == pygame.MOUSEMOTION:
            if self.dragging:
                self.rect.x = event.pos[0] + self.offset_x
                self.rect.y = event.pos[1] + self.offset_y