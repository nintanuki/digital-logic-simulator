import pygame

from fonts import Fonts
from settings import (
    InputSettings,
    LoadProjectDialogSettings as LD,
    SaveProjectDialogSettings as SD,
    ScreenSettings,
)


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

class _NameField:
    """Single-line text input for a project name (uppercase, capped length)."""

    def __init__(self, x, y, width, settings):
        self.rect = pygame.Rect(x, y, width, settings.NAME_FIELD_HEIGHT)
        self._s = settings
        self.text = ""
        self.focused = False
        self._focus_tick = 0

    def hit(self, pos):
        return self.rect.collidepoint(pos)

    def focus(self):
        self.focused = True
        self._focus_tick = pygame.time.get_ticks()

    def blur(self):
        self.focused = False

    def handle_key(self, event):
        s = self._s
        if event.key == pygame.K_BACKSPACE:
            self.text = self.text[:-1]
        elif event.unicode and event.unicode.isprintable():
            if len(self.text) >= s.NAME_MAX_LENGTH:
                return
            self.text += event.unicode.upper()
        else:
            return
        self._focus_tick = pygame.time.get_ticks()

    def draw(self, surface):
        s = self._s
        pygame.draw.rect(surface, s.NAME_FIELD_BG, self.rect)
        border = s.NAME_FIELD_BORDER_FOCUSED if self.focused else s.NAME_FIELD_BORDER
        pygame.draw.rect(surface, border, self.rect, 1)
        font = Fonts.text_box
        text_x = self.rect.x + s.NAME_FIELD_PADDING_X
        text_y = self.rect.y + (self.rect.height - font.get_height()) // 2
        if not self.text and not self.focused:
            surf = font.render(s.NAME_FIELD_PLACEHOLDER, True,
                               s.NAME_FIELD_PLACEHOLDER_COLOR)
            surface.blit(surf, (text_x, text_y))
        elif self.text:
            surf = font.render(self.text, True, s.NAME_FIELD_TEXT_COLOR)
            surface.blit(surf, (text_x, text_y))
        if self.focused and self._caret_visible():
            caret_x = text_x + font.size(self.text)[0]
            pygame.draw.rect(
                surface,
                s.NAME_FIELD_TEXT_COLOR,
                pygame.Rect(caret_x, text_y, s.NAME_CARET_WIDTH, font.get_height()),
            )

    def _caret_visible(self):
        elapsed = pygame.time.get_ticks() - self._focus_tick
        half = self._s.NAME_CARET_BLINK_MS // 2
        return (elapsed % self._s.NAME_CARET_BLINK_MS) < half


def _draw_button(surface, rect, label, enabled, bg_enabled, bg_disabled,
                 bg_cancel, text_enabled, text_disabled, border_color,
                 is_cancel=False):
    bg = bg_cancel if is_cancel else (bg_enabled if enabled else bg_disabled)
    text_color = text_enabled if enabled else text_disabled
    pygame.draw.rect(surface, bg, rect)
    pygame.draw.rect(surface, border_color, rect, 1)
    font = Fonts.text_box
    surf = font.render(label, True, text_color)
    label_rect = surf.get_rect(center=rect.center)
    surface.blit(surf, label_rect)


# ---------------------------------------------------------------------------
# SaveProjectDialog
# ---------------------------------------------------------------------------

class SaveProjectDialog:
    """Modal dialog that collects a project name before saving to disk.

    Args:
        existing_names (list[str]): Already-used project names so the
            dialog can warn on overwrite (currently unused — placeholder
            for future validation).
        on_save (Callable[[str], None]): Called with the trimmed uppercase
            name when the user clicks the enabled SAVE button.
        on_cancel (Callable[[], None]): Called when the user clicks
            CANCEL or presses Esc.
    """

    def __init__(self, existing_names, on_save, on_cancel):
        self._existing_names = existing_names
        self._on_save = on_save
        self._on_cancel = on_cancel

        self.rect = pygame.Rect(0, 0, SD.WIDTH, SD.HEIGHT)
        self.rect.center = (ScreenSettings.WIDTH // 2, ScreenSettings.HEIGHT // 2)

        self._title_surf = Fonts.text_box.render(SD.TITLE, True, SD.TITLE_COLOR)

        # Backdrop
        self._backdrop = pygame.Surface(ScreenSettings.RESOLUTION, pygame.SRCALPHA)
        self._backdrop.fill((*SD.BACKDROP_COLOR, SD.BACKDROP_ALPHA))

        # Name field
        field_x = self.rect.x + SD.PADDING
        field_y = self.rect.y + SD.PADDING + self._title_surf.get_height() + SD.SECTION_GAP
        field_w = SD.WIDTH - 2 * SD.PADDING
        self._name_field = _NameField(field_x, field_y, field_w, SD)
        self._name_field.focus()

        # Buttons — centered at the bottom of the dialog
        buttons_top = self.rect.bottom - SD.PADDING - SD.BUTTON_HEIGHT
        total_buttons_width = SD.BUTTON_WIDTH * 2 + SD.BUTTON_GAP
        buttons_left = self.rect.centerx - total_buttons_width // 2
        self._save_rect = pygame.Rect(buttons_left, buttons_top,
                                      SD.BUTTON_WIDTH, SD.BUTTON_HEIGHT)
        self._cancel_rect = pygame.Rect(
            buttons_left + SD.BUTTON_WIDTH + SD.BUTTON_GAP, buttons_top,
            SD.BUTTON_WIDTH, SD.BUTTON_HEIGHT,
        )

    def _save_enabled(self):
        return bool(self._name_field.text.strip())

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self._on_cancel()
                return True
            if event.key == pygame.K_RETURN and self._save_enabled():
                self._on_save(self._name_field.text.strip())
                return True
            self._name_field.handle_key(event)
            return True
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == InputSettings.LEFT_CLICK:
            if self._save_rect.collidepoint(event.pos) and self._save_enabled():
                self._on_save(self._name_field.text.strip())
                return True
            if self._cancel_rect.collidepoint(event.pos):
                self._on_cancel()
                return True
            # Clicking inside the dialog body focuses the name field.
            if self.rect.collidepoint(event.pos):
                self._name_field.focus()
            return True
        return True  # Consume all events while modal.

    def draw(self, surface):
        surface.blit(self._backdrop, (0, 0))
        pygame.draw.rect(surface, SD.BODY_COLOR, self.rect)
        pygame.draw.rect(surface, SD.BORDER_COLOR, self.rect, SD.BORDER_THICKNESS)

        title_x = self.rect.x + SD.PADDING
        title_y = self.rect.y + SD.PADDING
        surface.blit(self._title_surf, (title_x, title_y))

        self._name_field.draw(surface)

        enabled = self._save_enabled()
        _draw_button(surface, self._save_rect, SD.BUTTON_LABEL_SAVE,
                     enabled, SD.BUTTON_BG_ENABLED, SD.BUTTON_BG_DISABLED,
                     SD.BUTTON_BG_CANCEL, SD.BUTTON_TEXT_COLOR_ENABLED,
                     SD.BUTTON_TEXT_COLOR_DISABLED, SD.BUTTON_BORDER_COLOR)
        _draw_button(surface, self._cancel_rect, SD.BUTTON_LABEL_CANCEL,
                     True, SD.BUTTON_BG_ENABLED, SD.BUTTON_BG_DISABLED,
                     SD.BUTTON_BG_CANCEL, SD.BUTTON_TEXT_COLOR_ENABLED,
                     SD.BUTTON_TEXT_COLOR_DISABLED, SD.BUTTON_BORDER_COLOR,
                     is_cancel=True)


# ---------------------------------------------------------------------------
# LoadProjectDialog
# ---------------------------------------------------------------------------

class LoadProjectDialog:
    """Modal dialog listing saved projects so the user can select one to load.

    Shows a scrollable list (mouse wheel or arrow keys) of project names
    read from disk at construction time. Selecting a name and clicking LOAD
    (or double-clicking a name) fires on_load(name).

    Args:
        project_names (list[str]): Sorted list of available project names.
        on_load (Callable[[str], None]): Called with the selected name.
        on_cancel (Callable[[], None]): Called when user clicks CANCEL / Esc.
    """

    def __init__(self, project_names, on_load, on_cancel):
        self._project_names = project_names
        self._on_load = on_load
        self._on_cancel = on_cancel
        self._selected_index = 0 if project_names else -1
        self._scroll_offset = 0   # first visible item index
        self._hovered_index = -1

        self.rect = pygame.Rect(0, 0, LD.WIDTH, LD.HEIGHT)
        self.rect.center = (ScreenSettings.WIDTH // 2, ScreenSettings.HEIGHT // 2)

        self._title_surf = Fonts.text_box.render(LD.TITLE, True, LD.TITLE_COLOR)

        # Backdrop
        self._backdrop = pygame.Surface(ScreenSettings.RESOLUTION, pygame.SRCALPHA)
        self._backdrop.fill((*LD.BACKDROP_COLOR, LD.BACKDROP_ALPHA))

        # List area
        list_top = self.rect.y + LD.PADDING + self._title_surf.get_height() + LD.SECTION_GAP
        list_height = LD.LIST_MAX_VISIBLE * LD.LIST_ITEM_HEIGHT
        list_width = LD.WIDTH - 2 * LD.PADDING
        self._list_rect = pygame.Rect(self.rect.x + LD.PADDING, list_top,
                                      list_width, list_height)

        # Buttons
        buttons_top = self.rect.bottom - LD.PADDING - LD.BUTTON_HEIGHT
        total_buttons_width = LD.BUTTON_WIDTH * 2 + LD.BUTTON_GAP
        buttons_left = self.rect.centerx - total_buttons_width // 2
        self._load_rect = pygame.Rect(buttons_left, buttons_top,
                                      LD.BUTTON_WIDTH, LD.BUTTON_HEIGHT)
        self._cancel_rect = pygame.Rect(
            buttons_left + LD.BUTTON_WIDTH + LD.BUTTON_GAP, buttons_top,
            LD.BUTTON_WIDTH, LD.BUTTON_HEIGHT,
        )

        # Empty message
        self._empty_surf = Fonts.text_box.render(
            LD.EMPTY_MESSAGE, True, LD.EMPTY_MESSAGE_COLOR,
        )

    # ------------------------------------------------------------------
    # helpers
    # ------------------------------------------------------------------

    def _load_enabled(self):
        return self._selected_index >= 0 and bool(self._project_names)

    def _item_rect(self, list_index):
        """Return the screen rect for the item at list_index (visible slot)."""
        return pygame.Rect(
            self._list_rect.x,
            self._list_rect.y + list_index * LD.LIST_ITEM_HEIGHT,
            self._list_rect.width,
            LD.LIST_ITEM_HEIGHT,
        )

    def _clamp_scroll(self):
        max_offset = max(0, len(self._project_names) - LD.LIST_MAX_VISIBLE)
        self._scroll_offset = max(0, min(self._scroll_offset, max_offset))

    def _ensure_selected_visible(self):
        if self._selected_index < 0:
            return
        if self._selected_index < self._scroll_offset:
            self._scroll_offset = self._selected_index
        elif self._selected_index >= self._scroll_offset + LD.LIST_MAX_VISIBLE:
            self._scroll_offset = self._selected_index - LD.LIST_MAX_VISIBLE + 1

    # ------------------------------------------------------------------
    # events
    # ------------------------------------------------------------------

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self._on_cancel()
                return True
            if event.key == pygame.K_RETURN and self._load_enabled():
                self._on_load(self._project_names[self._selected_index])
                return True
            if event.key == pygame.K_DOWN and self._project_names:
                self._selected_index = min(self._selected_index + 1,
                                           len(self._project_names) - 1)
                self._ensure_selected_visible()
                return True
            if event.key == pygame.K_UP and self._project_names:
                self._selected_index = max(self._selected_index - 1, 0)
                self._ensure_selected_visible()
                return True
            return True

        if event.type == pygame.MOUSEWHEEL:
            self._scroll_offset -= event.y
            self._clamp_scroll()
            return True

        if event.type == pygame.MOUSEMOTION:
            pos = event.pos
            self._hovered_index = -1
            if self._list_rect.collidepoint(pos):
                slot = (pos[1] - self._list_rect.y) // LD.LIST_ITEM_HEIGHT
                actual = self._scroll_offset + slot
                if 0 <= actual < len(self._project_names):
                    self._hovered_index = actual
            return True

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == InputSettings.LEFT_CLICK:
            pos = event.pos
            if self._load_rect.collidepoint(pos) and self._load_enabled():
                self._on_load(self._project_names[self._selected_index])
                return True
            if self._cancel_rect.collidepoint(pos):
                self._on_cancel()
                return True
            if self._list_rect.collidepoint(pos):
                slot = (pos[1] - self._list_rect.y) // LD.LIST_ITEM_HEIGHT
                actual = self._scroll_offset + slot
                if 0 <= actual < len(self._project_names):
                    if actual == self._selected_index:
                        # Double-click treated as immediate load on second tap.
                        # Since pygame doesn't expose double-click natively, a
                        # second click on the same item just loads it.
                        self._on_load(self._project_names[actual])
                    else:
                        self._selected_index = actual
            return True

        return True  # Consume all events while modal.

    # ------------------------------------------------------------------
    # draw
    # ------------------------------------------------------------------

    def draw(self, surface):
        surface.blit(self._backdrop, (0, 0))
        pygame.draw.rect(surface, LD.BODY_COLOR, self.rect)
        pygame.draw.rect(surface, LD.BORDER_COLOR, self.rect, LD.BORDER_THICKNESS)

        title_x = self.rect.x + LD.PADDING
        title_y = self.rect.y + LD.PADDING
        surface.blit(self._title_surf, (title_x, title_y))

        if not self._project_names:
            empty_rect = self._empty_surf.get_rect(center=self._list_rect.center)
            surface.blit(self._empty_surf, empty_rect)
        else:
            # Clip list drawing so items don't bleed outside the list area.
            clip = surface.get_clip()
            surface.set_clip(self._list_rect)
            visible = self._project_names[
                self._scroll_offset: self._scroll_offset + LD.LIST_MAX_VISIBLE
            ]
            for slot_idx, name in enumerate(visible):
                actual_idx = self._scroll_offset + slot_idx
                item_rect = self._item_rect(slot_idx)
                if actual_idx == self._selected_index:
                    bg = LD.LIST_ITEM_BG_SELECTED
                elif actual_idx == self._hovered_index:
                    bg = LD.LIST_ITEM_BG_HOVER
                else:
                    bg = LD.LIST_ITEM_BG
                pygame.draw.rect(surface, bg, item_rect)
                pygame.draw.rect(surface, LD.LIST_ITEM_BORDER, item_rect, 1)
                font = Fonts.text_box
                text_surf = font.render(name, True, LD.LIST_ITEM_TEXT_COLOR)
                text_y = item_rect.y + (item_rect.height - text_surf.get_height()) // 2
                surface.blit(text_surf, (item_rect.x + 8, text_y))
            surface.set_clip(clip)

            # Scroll hint arrows when there are off-screen items.
            font = Fonts.text_box
            if self._scroll_offset > 0:
                arrow = font.render("▲", True, LD.LIST_ITEM_TEXT_COLOR)
                surface.blit(arrow, (self._list_rect.right - arrow.get_width() - 6,
                                     self._list_rect.top + 4))
            if self._scroll_offset + LD.LIST_MAX_VISIBLE < len(self._project_names):
                arrow = font.render("▼", True, LD.LIST_ITEM_TEXT_COLOR)
                surface.blit(arrow, (self._list_rect.right - arrow.get_width() - 6,
                                     self._list_rect.bottom - arrow.get_height() - 4))

        enabled = self._load_enabled()
        _draw_button(surface, self._load_rect, LD.BUTTON_LABEL_LOAD,
                     enabled, LD.BUTTON_BG_ENABLED, LD.BUTTON_BG_DISABLED,
                     LD.BUTTON_BG_CANCEL, LD.BUTTON_TEXT_COLOR_ENABLED,
                     LD.BUTTON_TEXT_COLOR_DISABLED, LD.BUTTON_BORDER_COLOR)
        _draw_button(surface, self._cancel_rect, LD.BUTTON_LABEL_CANCEL,
                     True, LD.BUTTON_BG_ENABLED, LD.BUTTON_BG_DISABLED,
                     LD.BUTTON_BG_CANCEL, LD.BUTTON_TEXT_COLOR_ENABLED,
                     LD.BUTTON_TEXT_COLOR_DISABLED, LD.BUTTON_BORDER_COLOR,
                     is_cancel=True)
