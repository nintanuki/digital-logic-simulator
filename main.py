from __future__ import annotations

import pygame
import sys
from elements import Component
from settings import *

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
        self.components = [Component(100, 100)] # Start with one on screen

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
        for comp in self.components:
            comp.handle_event(event)

    # -------------------------
    # PER-FRAME UPDATE / RENDER
    # -------------------------

    def _update_world(self):
        pass

    def _draw(self):
        for comp in self.components:
            comp.draw(self.screen)

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