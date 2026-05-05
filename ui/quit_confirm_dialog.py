import pygame

from fonts import Fonts
from settings import (
    InputSettings,
    QuitConfirmDialogSettings as DS,
    ScreenSettings,
)


class QuitConfirmDialog:
    """Modal "Are you sure you want to quit?" confirmation dialog.

    Shown when the user presses Esc and no other UI layer is open and the
    window is not fullscreen. Only "YES" actually quits; "NO" and Esc both
    dismiss. Modal: consumes every event while open so the workspace beneath
    is paused.
    """

    def __init__(self, on_confirm, on_cancel):
        """Lay out the dialog centered on the screen.

        Args:
            on_confirm (Callable[[], None]): Called when the user clicks YES.
            on_cancel (Callable[[], None]): Called when the user clicks NO or
                presses Esc.
        """
        self._on_confirm = on_confirm
        self._on_cancel = on_cancel

        self.rect = pygame.Rect(0, 0, DS.WIDTH, DS.HEIGHT)
        self.rect.center = (ScreenSettings.WIDTH // 2, ScreenSettings.HEIGHT // 2)

        self._backdrop = pygame.Surface(
            (ScreenSettings.WIDTH, ScreenSettings.HEIGHT)
        )
        self._backdrop.fill(DS.BACKDROP_COLOR)
        self._backdrop.set_alpha(DS.BACKDROP_ALPHA)

        # Pre-render static text surfaces.
        self._title_surf = Fonts.text_box.render(DS.TITLE, True, DS.TITLE_COLOR)
        self._message_surf = Fonts.text_box.render(DS.MESSAGE, True, DS.MESSAGE_COLOR)
        self._yes_label = Fonts.text_box.render(DS.BUTTON_LABEL_YES, True, DS.BUTTON_TEXT_COLOR)
        self._no_label = Fonts.text_box.render(DS.BUTTON_LABEL_NO, True, DS.BUTTON_TEXT_COLOR)

        # Layout: title then message centered, buttons centered at the bottom.
        cursor_y = self.rect.y + DS.PADDING
        self._title_rect = self._title_surf.get_rect(
            midtop=(self.rect.centerx, cursor_y)
        )
        cursor_y = self._title_rect.bottom + DS.SECTION_GAP
        self._message_rect = self._message_surf.get_rect(
            midtop=(self.rect.centerx, cursor_y)
        )

        # Two buttons centered horizontally, near the bottom.
        button_y = self.rect.bottom - DS.PADDING - DS.BUTTON_HEIGHT
        total_buttons_width = 2 * DS.BUTTON_WIDTH + DS.BUTTON_GAP
        buttons_left = self.rect.centerx - total_buttons_width // 2
        self._yes_rect = pygame.Rect(buttons_left, button_y, DS.BUTTON_WIDTH, DS.BUTTON_HEIGHT)
        self._no_rect = pygame.Rect(
            buttons_left + DS.BUTTON_WIDTH + DS.BUTTON_GAP,
            button_y, DS.BUTTON_WIDTH, DS.BUTTON_HEIGHT,
        )

    # -------------------------
    # EVENT HANDLING
    # -------------------------

    def handle_event(self, event):
        """Consume a single event; route to YES/NO or Esc-dismiss.

        Args:
            event (pygame.event.Event): The event to process.

        Returns:
            bool: Always True — the dialog claims all events while open.
        """
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self._on_cancel()
            elif event.key == pygame.K_RETURN or event.key == pygame.K_y:
                self._on_confirm()
            elif event.key == pygame.K_n:
                self._on_cancel()
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == InputSettings.LEFT_CLICK:
                self._handle_left_click(event.pos)
        return True

    def _handle_left_click(self, pos):
        if self._yes_rect.collidepoint(pos):
            self._on_confirm()
        elif self._no_rect.collidepoint(pos):
            self._on_cancel()
        # Clicks anywhere else on the backdrop or body are consumed (modal)
        # but do nothing — the user must make an explicit choice.

    # -------------------------
    # RENDER
    # -------------------------

    def draw(self, surface):
        """Paint the backdrop dim, dialog body, title, message, and buttons.

        Args:
            surface (pygame.Surface): The surface to draw onto.
        """
        surface.blit(self._backdrop, (0, 0))
        pygame.draw.rect(surface, DS.BODY_COLOR, self.rect)
        pygame.draw.rect(surface, DS.BORDER_COLOR, self.rect, DS.BORDER_THICKNESS)

        surface.blit(self._title_surf, self._title_rect)
        surface.blit(self._message_surf, self._message_rect)

        pygame.draw.rect(surface, DS.BUTTON_BG_YES, self._yes_rect)
        pygame.draw.rect(surface, DS.BUTTON_BORDER_COLOR, self._yes_rect, 1)
        yes_label_rect = self._yes_label.get_rect(center=self._yes_rect.center)
        surface.blit(self._yes_label, yes_label_rect)

        pygame.draw.rect(surface, DS.BUTTON_BG_NO, self._no_rect)
        pygame.draw.rect(surface, DS.BUTTON_BORDER_COLOR, self._no_rect, 1)
        no_label_rect = self._no_label.get_rect(center=self._no_rect.center)
        surface.blit(self._no_label, no_label_rect)
