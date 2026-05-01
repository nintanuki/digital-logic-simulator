from __future__ import annotations

import pygame
import sys
from elements import Component
from settings import *
from ui import ComponentBank

class GameManager:
    def __init__(self):
        # -------- Pygame core --------
        pygame.init()

        # -------- Display --------
        self.screen = pygame.display.set_mode(ScreenSettings.RESOLUTION)
        pygame.display.set_caption(ScreenSettings.TITLE)
        self.clock = pygame.time.Clock()

        # -------- Subsystems --------

        # -------- Managers --------

        # -------- Sprite groups --------
        self.bank = ComponentBank()
        self.components = [] # Start with an empty workspace. Components will be added by the user.

    # -------------------------
    # BOOT / LIFECYCLE
    # -------------------------

    def close_game(self):
        pygame.quit()
        sys.exit()

    # -------------------------
    # GAMEPLAY ACTIONS
    # -------------------------

    # -------------------------
    # AUDIO / VOLUME ACTIONS
    # -------------------------

    # -------------------------
    # EVENT HANDLING
    # -------------------------

    def _process_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.close_game()
            
            # Route logic to specialized handlers
            elif event.type == pygame.KEYDOWN:
                self._handle_keydown(event)
            elif event.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, pygame.MOUSEMOTION):
                self._handle_mouse(event)

    def _handle_keydown(self, event: pygame.event.Event) -> None:
        """Route a single keyboard press."""
        # Global keys (always honored regardless of run state).
        if event.key == pygame.K_F11:
            pygame.display.toggle_fullscreen()
        if event.key == pygame.K_ESCAPE:
            self.close_game()
        # Centralized place to spawn components
        if event.key == pygame.K_n:
            self.components.append(Component(50, 50))

    def _handle_mouse(self, event: pygame.event.Event) -> None:
        """Pass mouse events to the component manager or components directly."""
        # Try the bank first since it has priority for clicks in its area. If it returns True,
        # it handled the event and we can skip the rest.
        # Returns True if a new game was spawned
        if self.bank.handle_event(event, self.components):
            return # If the bank handled it, we're done.
        
        # Check components (backwards for proper layering/removal)
        for i in range(len(self.components) - 1, -1, -1):
            comp = self.components[i]
            
            # Catch the return value from the component
            action = comp.handle_event(event)
            
            if action == "DELETE":
                self.components.pop(i) # This is the "What then?"—we remove it!
                break # Stop checking others so one click only deletes one gate

    # -------------------------
    # PER-FRAME UPDATE / RENDER
    # -------------------------

    def _update_world(self):
        pass

    def _draw(self):
        for comp in self.components:
            comp.draw(self.screen)
        # Draw the bank last so it stays on top of everything
        self.bank.draw(self.screen)

    def _render_frame(self):
        self.screen.fill(ScreenSettings.BG_COLOR)
        self._draw()

    def run(self):
        while True:
            self._process_events()
            self._update_world()
            self._render_frame()
            pygame.display.flip()
            self.clock.tick(ScreenSettings.FPS)

# Main execution
if __name__ == '__main__':
    game_manager = GameManager()
    game_manager.run()