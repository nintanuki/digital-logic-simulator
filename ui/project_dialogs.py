import pygame

from fonts import Fonts
from settings import (
    FileNotFoundWarningDialogSettings as FW,
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
# SaveProjectDialog  (used for "Save As" — list of existing + name field)
# ---------------------------------------------------------------------------

class SaveProjectDialog:
    """Modal dialog for saving a project under a new or existing name.

    Shows a scrollable list of existing projects (clicking one fills the
    name field so the user can overwrite it), a text input to type a fresh
    name, an overwrite warning when the name collides with an existing
    project, and SAVE / CANCEL buttons.

    Args:
        existing_names (list[str]): Already-saved project names.
        on_save (Callable[[str], None]): Called with the trimmed uppercase
            name when SAVE is confirmed.
        on_cancel (Callable[[], None]): Called on CANCEL / Esc.
    """

    def __init__(self, existing_names, on_save, on_cancel):
        self._existing_names = existing_names
        self._on_save = on_save
        self._on_cancel = on_cancel

        self._selected_index = -1
        self._scroll_offset = 0
        self._hovered_index = -1

        self.rect = pygame.Rect(0, 0, SD.WIDTH, SD.HEIGHT)
        self.rect.center = (ScreenSettings.WIDTH // 2, ScreenSettings.HEIGHT // 2)

        self._title_surf = Fonts.text_box.render(SD.TITLE, True, SD.TITLE_COLOR)
        self._warning_surf = Fonts.text_box.render(SD.WARNING_TEXT, True, SD.WARNING_COLOR)

        # Backdrop
        self._backdrop = pygame.Surface(ScreenSettings.RESOLUTION, pygame.SRCALPHA)
        self._backdrop.fill((*SD.BACKDROP_COLOR, SD.BACKDROP_ALPHA))

        # Layout from top:  padding → title → section_gap → list → section_gap
        #                   → name_field → warning_row → section_gap → buttons → padding
        title_bottom = self.rect.y + SD.PADDING + self._title_surf.get_height()
        list_top = title_bottom + SD.SECTION_GAP
        list_height = SD.LIST_MAX_VISIBLE * SD.LIST_ITEM_HEIGHT
        list_width = SD.WIDTH - 2 * SD.PADDING
        self._list_rect = pygame.Rect(
            self.rect.x + SD.PADDING, list_top, list_width, list_height,
        )

        field_top = self._list_rect.bottom + SD.SECTION_GAP
        field_w = SD.WIDTH - 2 * SD.PADDING
        self._name_field = _NameField(
            self.rect.x + SD.PADDING, field_top, field_w, SD,
        )
        self._name_field.focus()

        buttons_top = self.rect.bottom - SD.PADDING - SD.BUTTON_HEIGHT
        total_buttons_width = SD.BUTTON_WIDTH * 2 + SD.BUTTON_GAP
        buttons_left = self.rect.centerx - total_buttons_width // 2
        self._save_rect = pygame.Rect(
            buttons_left, buttons_top, SD.BUTTON_WIDTH, SD.BUTTON_HEIGHT,
        )
        self._cancel_rect = pygame.Rect(
            buttons_left + SD.BUTTON_WIDTH + SD.BUTTON_GAP, buttons_top,
            SD.BUTTON_WIDTH, SD.BUTTON_HEIGHT,
        )

        self._empty_surf = Fonts.text_box.render(
            SD.EMPTY_MESSAGE, True, SD.EMPTY_MESSAGE_COLOR,
        )

    # ------------------------------------------------------------------
    # helpers
    # ------------------------------------------------------------------

    def _save_enabled(self):
        return bool(self._name_field.text.strip())

    def _name_collides(self):
        """Return True when the typed name matches an existing project."""
        return self._name_field.text.strip().upper() in (
            n.upper() for n in self._existing_names
        )

    def _item_rect(self, slot_index):
        return pygame.Rect(
            self._list_rect.x,
            self._list_rect.y + slot_index * SD.LIST_ITEM_HEIGHT,
            self._list_rect.width,
            SD.LIST_ITEM_HEIGHT,
        )

    def _clamp_scroll(self):
        max_offset = max(0, len(self._existing_names) - SD.LIST_MAX_VISIBLE)
        self._scroll_offset = max(0, min(self._scroll_offset, max_offset))

    def _ensure_selected_visible(self):
        if self._selected_index < 0:
            return
        if self._selected_index < self._scroll_offset:
            self._scroll_offset = self._selected_index
        elif self._selected_index >= self._scroll_offset + SD.LIST_MAX_VISIBLE:
            self._scroll_offset = self._selected_index - SD.LIST_MAX_VISIBLE + 1

    # ------------------------------------------------------------------
    # events
    # ------------------------------------------------------------------

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self._on_cancel()
                return True
            if event.key == pygame.K_RETURN and self._save_enabled():
                self._on_save(self._name_field.text.strip())
                return True
            if event.key == pygame.K_DOWN and self._existing_names:
                self._selected_index = min(
                    self._selected_index + 1, len(self._existing_names) - 1,
                )
                self._ensure_selected_visible()
                self._name_field.text = self._existing_names[self._selected_index]
                self._name_field._focus_tick = pygame.time.get_ticks()
                return True
            if event.key == pygame.K_UP and self._existing_names:
                if self._selected_index > 0:
                    self._selected_index -= 1
                    self._ensure_selected_visible()
                    self._name_field.text = self._existing_names[self._selected_index]
                    self._name_field._focus_tick = pygame.time.get_ticks()
                return True
            self._name_field.handle_key(event)
            # Typing de-selects any list item.
            self._selected_index = -1
            return True

        if event.type == pygame.MOUSEWHEEL:
            self._scroll_offset -= event.y
            self._clamp_scroll()
            return True

        if event.type == pygame.MOUSEMOTION:
            pos = event.pos
            self._hovered_index = -1
            if self._list_rect.collidepoint(pos):
                slot = (pos[1] - self._list_rect.y) // SD.LIST_ITEM_HEIGHT
                actual = self._scroll_offset + slot
                if 0 <= actual < len(self._existing_names):
                    self._hovered_index = actual
            return True

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == InputSettings.LEFT_CLICK:
            pos = event.pos
            if self._save_rect.collidepoint(pos) and self._save_enabled():
                self._on_save(self._name_field.text.strip())
                return True
            if self._cancel_rect.collidepoint(pos):
                self._on_cancel()
                return True
            if self._list_rect.collidepoint(pos) and self._existing_names:
                slot = (pos[1] - self._list_rect.y) // SD.LIST_ITEM_HEIGHT
                actual = self._scroll_offset + slot
                if 0 <= actual < len(self._existing_names):
                    self._selected_index = actual
                    self._name_field.text = self._existing_names[actual]
                    self._name_field._focus_tick = pygame.time.get_ticks()
            elif self.rect.collidepoint(pos):
                self._name_field.focus()
            return True

        return True  # Consume all events while modal.

    # ------------------------------------------------------------------
    # draw
    # ------------------------------------------------------------------

    def draw(self, surface):
        surface.blit(self._backdrop, (0, 0))
        pygame.draw.rect(surface, SD.BODY_COLOR, self.rect)
        pygame.draw.rect(surface, SD.BORDER_COLOR, self.rect, SD.BORDER_THICKNESS)

        # Title
        surface.blit(self._title_surf, (self.rect.x + SD.PADDING, self.rect.y + SD.PADDING))

        # Project list
        if not self._existing_names:
            empty_rect = self._empty_surf.get_rect(center=self._list_rect.center)
            surface.blit(self._empty_surf, empty_rect)
        else:
            clip = surface.get_clip()
            surface.set_clip(self._list_rect)
            visible = self._existing_names[
                self._scroll_offset: self._scroll_offset + SD.LIST_MAX_VISIBLE
            ]
            for slot_idx, name in enumerate(visible):
                actual_idx = self._scroll_offset + slot_idx
                item_rect = self._item_rect(slot_idx)
                if actual_idx == self._selected_index:
                    bg = SD.LIST_ITEM_BG_SELECTED
                elif actual_idx == self._hovered_index:
                    bg = SD.LIST_ITEM_BG_HOVER
                else:
                    bg = SD.LIST_ITEM_BG
                pygame.draw.rect(surface, bg, item_rect)
                pygame.draw.rect(surface, SD.LIST_ITEM_BORDER, item_rect, 1)
                font = Fonts.text_box
                text_surf = font.render(name, True, SD.LIST_ITEM_TEXT_COLOR)
                text_y = item_rect.y + (item_rect.height - text_surf.get_height()) // 2
                surface.blit(text_surf, (item_rect.x + 8, text_y))
            surface.set_clip(clip)

            # Scroll hint arrows
            font = Fonts.text_box
            if self._scroll_offset > 0:
                arrow = font.render("▲", True, SD.LIST_ITEM_TEXT_COLOR)
                surface.blit(arrow, (self._list_rect.right - arrow.get_width() - 6,
                                     self._list_rect.top + 4))
            if self._scroll_offset + SD.LIST_MAX_VISIBLE < len(self._existing_names):
                arrow = font.render("▼", True, SD.LIST_ITEM_TEXT_COLOR)
                surface.blit(arrow, (self._list_rect.right - arrow.get_width() - 6,
                                     self._list_rect.bottom - arrow.get_height() - 4))

        # Name field
        self._name_field.draw(surface)

        # Overwrite warning (only when the name collides)
        if self._save_enabled() and self._name_collides():
            warn_x = self.rect.x + SD.PADDING
            warn_y = (self._name_field.rect.bottom +
                      (self._save_rect.top - self._name_field.rect.bottom
                       - self._warning_surf.get_height()) // 2)
            surface.blit(self._warning_surf, (warn_x, warn_y))

        # Buttons
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


# ---------------------------------------------------------------------------
# FileNotFoundWarningDialog
# ---------------------------------------------------------------------------

class FileNotFoundWarningDialog:
    """Modal warning shown when a project file has disappeared from disk.

    Displays a red-bordered alert with a single OK button to dismiss.
    """

    def __init__(self, on_dismiss):
        """Lay out the dialog centered on the screen.

        Args:
            on_dismiss (Callable[[], None]): Called when the user clicks OK
                or presses Enter / Escape.
        """
        self._on_dismiss = on_dismiss

        self.rect = pygame.Rect(0, 0, FW.WIDTH, FW.HEIGHT)
        self.rect.center = (ScreenSettings.WIDTH // 2, ScreenSettings.HEIGHT // 2)

        self._backdrop = pygame.Surface(
            (ScreenSettings.WIDTH, ScreenSettings.HEIGHT)
        )
        self._backdrop.fill(FW.BACKDROP_COLOR)
        self._backdrop.set_alpha(FW.BACKDROP_ALPHA)

        self._title_surf = Fonts.text_box.render(FW.TITLE, True, FW.TITLE_COLOR)
        self._message_surf = Fonts.text_box.render(FW.MESSAGE, True, FW.MESSAGE_COLOR)
        self._ok_label = Fonts.text_box.render(FW.BUTTON_LABEL, True, FW.BUTTON_TEXT_COLOR)

        cursor_y = self.rect.y + FW.PADDING
        self._title_rect = self._title_surf.get_rect(
            midtop=(self.rect.centerx, cursor_y)
        )
        cursor_y = self._title_rect.bottom + FW.SECTION_GAP
        self._message_rect = self._message_surf.get_rect(
            midtop=(self.rect.centerx, cursor_y)
        )

        button_y = self.rect.bottom - FW.PADDING - FW.BUTTON_HEIGHT
        self._ok_rect = pygame.Rect(
            self.rect.centerx - FW.BUTTON_WIDTH // 2,
            button_y,
            FW.BUTTON_WIDTH,
            FW.BUTTON_HEIGHT,
        )

    def handle_event(self, event):
        """Consume a single event; dismiss on OK, Enter, or Escape.

        Returns:
            bool: Always True — the dialog claims all events while open.
        """
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_RETURN, pygame.K_ESCAPE, pygame.K_SPACE):
                self._on_dismiss()
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == InputSettings.LEFT_CLICK:
                if self._ok_rect.collidepoint(event.pos):
                    self._on_dismiss()
        return True

    def draw(self, surface):
        """Paint the backdrop, dialog body, title, message, and OK button."""
        surface.blit(self._backdrop, (0, 0))
        pygame.draw.rect(surface, FW.BODY_COLOR, self.rect)
        pygame.draw.rect(surface, FW.BORDER_COLOR, self.rect, FW.BORDER_THICKNESS)

        surface.blit(self._title_surf, self._title_rect)
        surface.blit(self._message_surf, self._message_rect)

        pygame.draw.rect(surface, FW.BUTTON_BG, self._ok_rect)
        pygame.draw.rect(surface, FW.BUTTON_BORDER_COLOR, self._ok_rect, 1)
        ok_label_rect = self._ok_label.get_rect(center=self._ok_rect.center)
        surface.blit(self._ok_label, ok_label_rect)
