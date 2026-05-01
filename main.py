from __future__ import annotations

import pygame
import sys
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
            elif event.type == pygame.KEYDOWN:
                self._handle_keydown(event)

    def _handle_keydown(self, event: pygame.event.Event) -> None:
        """Route a single keyboard press."""
        # Global keys (always honored regardless of run state).
        if event.key == pygame.K_F11:
            pygame.display.toggle_fullscreen()
        if event.key == pygame.K_ESCAPE:
            self.close_game()

    # -------------------------
    # PER-FRAME UPDATE / RENDER
    # -------------------------

    def _update_world(self):
        pass

    def _draw(self):
        pass

    def _render_frame(self):
        self.screen.fill(ColorSettings.BG_COLOR)

    def run(self):
        while True:
            self._process_events()
            self._update_world()
            self._draw()
            self._render_frame()
            pygame.display.flip()
            self.clock.tick(ScreenSettings.FPS)

# Main execution
if __name__ == '__main__':
    game_manager = GameManager()
    game_manager.run()