from __future__ import annotations

import pygame
import sys
from elements import Component
from fonts import Fonts
from settings import *
from signals import SignalManager
from ui import ComponentBank
from crt import CRT
from wires import WireManager


class GameManager:
    def __init__(self):
        # -------- Pygame core --------
        pygame.init()
        # Load every shared Font once, before any object that calls .render().
        # ComponentBank instantiates a template Component below, so this must
        # come before the bank is built.
        Fonts.init()

        # -------- Display --------
        self.screen = pygame.display.set_mode(ScreenSettings.RESOLUTION)
        pygame.display.set_caption(ScreenSettings.TITLE)
        self.clock = pygame.time.Clock()
        self.crt = CRT(self.screen)

        # -------- Subsystems --------

        # -------- Managers --------

        # -------- Sprite groups --------
        self.bank = ComponentBank()
        self.components = [] # Start with an empty workspace. Components will be added by the user.
        self.wires = WireManager()
        self.signals = SignalManager()

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
        # Hover updates ride along with motion events. Done here (not inside
        # Component) because every port in the world — workspace and toolbox
        # template alike — needs to reflect the same cursor, and only
        # GameManager owns both collections.
        if event.type == pygame.MOUSEMOTION:
            self._update_port_hover(event.pos)

        # Wires get the event before bank/components: a click that lands on a
        # port should start a wire, not drag the underlying component.
        if self.wires.handle_event(event, self.components):
            return

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
                # Drop any wires touching this component before it disappears,
                # otherwise wires would dangle on a freed Port reference.
                self.wires.drop_wires_for_component(comp)
                self.components.pop(i) # This is the "What then?"—we remove it!
                break # Stop checking others so one click only deletes one gate

    def _update_port_hover(self, mouse_pos) -> None:
        """Refresh the hovered flag on every port given the current cursor.

        Walks all workspace components plus the toolbox template so a port in
        either place lights up under the cursor. Callers must invoke this on
        MOUSEMOTION; ports do not poll their own state.

        Args:
            mouse_pos (tuple[int, int]): Cursor position in screen space.
        """
        for comp in self.components:
            for port in comp.ports:
                port.hovered = port.rect.collidepoint(mouse_pos)
        for tpl in self.bank.templates:
            for port in tpl.ports:
                port.hovered = port.rect.collidepoint(mouse_pos)

    # -------------------------
    # PER-FRAME UPDATE / RENDER
    # -------------------------

    def _update_world(self):
        """Advance per-frame simulation state.

        Wires hold the canonical list of connections. SignalManager reads
        port states, computes new outputs, applies them, and propagates
        through wires — see signals.py for the two-phase contract.
        """
        self.signals.update(self.components, self.wires.wires)

    def _draw(self):
        for comp in self.components:
            comp.draw(self.screen)
        # Wires sit above the components but below the toolbox bank, so a
        # wire routed through the toolbox area is hidden by the dark bank
        # rectangle drawn next.
        self.wires.draw(self.screen)
        # Draw the bank last so it stays on top of everything
        self.bank.draw(self.screen)

    def _draw_grid(self):
        grid_color = (ColorSettings.WORD_COLORS["WHITE"]) # Subtle light blue
        grid_size = ScreenSettings.GRID_SIZE
        
        # Draw Vertical Lines
        for x in range(0, ScreenSettings.WIDTH, grid_size):
            pygame.draw.line(self.screen, grid_color, (x, 0), (x, ScreenSettings.HEIGHT), 1)
            
        # Draw Horizontal Lines
        for y in range(0, ScreenSettings.HEIGHT, grid_size):
            pygame.draw.line(self.screen, grid_color, (0, y), (ScreenSettings.WIDTH, y), 1)

    def _render_frame(self):
        self.screen.fill(ScreenSettings.BG_COLOR)
        self._draw_grid()
        self._draw()
        self.crt.draw()

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