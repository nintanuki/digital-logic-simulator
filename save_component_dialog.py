import pygame

from fonts import Fonts
from settings import (
    InputSettings,
    SaveComponentDialogSettings as DS,
    ScreenSettings,
)


class _NameField:
    """Single-line text field for the saved component's name.

    Mirrors the input model used by `TextBox` (uppercase printable input,
    Backspace deletes, blink caret while focused) but stays single-line
    and caps its character count at NAME_MAX_LENGTH so the rendered width
    is bounded. Drawn with a focus-aware border so the user can see when
    keystrokes are being captured. Private to the dialog module — the
    field never appears outside a dialog instance.
    """

    def __init__(self, x, y, width):
        """Lay out the field rect and seed its text/focus state empty.

        Args:
            x (int): Top-left x in screen coordinates.
            y (int): Top-left y in screen coordinates.
            width (int): Field width in pixels (height comes from
                DS.NAME_FIELD_HEIGHT so the dialog can rely on a fixed
                vertical pitch).
        """
        self.rect = pygame.Rect(x, y, width, DS.NAME_FIELD_HEIGHT)
        self.text = ""
        self.focused = False
        # Tick at which focus was last gained. Used only for caret blink
        # phase so the caret restarts visible on every focus change
        # instead of mid-blink (matches TextBox's _focus_tick behavior).
        self._focus_tick = 0

    def hit(self, pos):
        """Return True if pos lies inside the field's body.

        Args:
            pos (tuple[int, int]): Cursor position in screen coordinates.

        Returns:
            bool: True if the cursor is over this field.
        """
        return self.rect.collidepoint(pos)

    def focus(self):
        """Mark the field as receiving keystrokes; reset caret blink phase."""
        self.focused = True
        self._focus_tick = pygame.time.get_ticks()

    def blur(self):
        """Stop receiving keystrokes."""
        self.focused = False

    def handle_key(self, event):
        """Apply a keystroke to the field while it has focus.

        Backspace removes the last character; printable unicode is
        uppercased and appended (text in this project is uppercase by
        convention — every component label, port name, and text-box
        string follows the same rule). Other keys are ignored so
        modifiers and arrows don't insert junk.

        Args:
            event (pygame.event.Event): A KEYDOWN event the dialog
                forwarded after deciding this field has focus.
        """
        if event.key == pygame.K_BACKSPACE:
            self.text = self.text[:-1]
        elif event.unicode and event.unicode.isprintable():
            if len(self.text) >= DS.NAME_MAX_LENGTH:
                # Refuse the keystroke instead of truncating later, so
                # the caret stops advancing at the cap and the user
                # gets immediate feedback that the field is full.
                return
            # str.upper() is a no-op for digits/punctuation/already-
            # uppercase letters, so this is safe unconditionally.
            self.text += event.unicode.upper()
        else:
            return
        # Reset the blink so the caret stays visible immediately after a
        # keystroke instead of disappearing for half a period.
        self._focus_tick = pygame.time.get_ticks()

    def draw(self, surface):
        """Render the field body, border, text (or placeholder), and caret.

        Args:
            surface (pygame.Surface): The surface to draw onto.
        """
        pygame.draw.rect(surface, DS.NAME_FIELD_BG, self.rect)
        border = (DS.NAME_FIELD_BORDER_FOCUSED
                  if self.focused else DS.NAME_FIELD_BORDER)
        pygame.draw.rect(surface, border, self.rect, 1)
        font = Fonts.text_box
        text_x = self.rect.x + DS.NAME_FIELD_PADDING_X
        text_y = self.rect.y + (self.rect.height - font.get_height()) // 2
        if not self.text and not self.focused:
            # Show placeholder only when both empty AND unfocused, so the
            # caret has a clean empty field to blink in once focused.
            surf = font.render(DS.NAME_FIELD_PLACEHOLDER, True,
                               DS.NAME_FIELD_PLACEHOLDER_COLOR)
            surface.blit(surf, (text_x, text_y))
        elif self.text:
            surf = font.render(self.text, True, DS.NAME_FIELD_TEXT_COLOR)
            surface.blit(surf, (text_x, text_y))
        if self.focused and self._caret_visible():
            text_w = font.size(self.text)[0]
            caret_x = text_x + text_w
            pygame.draw.rect(
                surface,
                DS.NAME_FIELD_TEXT_COLOR,
                pygame.Rect(caret_x, text_y,
                            DS.NAME_CARET_WIDTH, font.get_height()),
            )

    def _caret_visible(self):
        """Return True if the caret should be drawn this frame.

        Returns:
            bool: True during the first half of each blink period.
        """
        elapsed = pygame.time.get_ticks() - self._focus_tick
        half = DS.NAME_CARET_BLINK_MS // 2
        return (elapsed % DS.NAME_CARET_BLINK_MS) < half


class SaveComponentDialog:
    """Modal "Save as Component" dialog opened from the bottom-left popup.

    Pass 1 step 1 (v2) — minimum-viable scope:
      * single-line name field (uppercase, capped at NAME_MAX_LENGTH)
      * Save / Cancel buttons; Save stays disabled until the name is
        non-empty after stripping whitespace

    Whatever Switches and LEDs are in the workspace at save time
    become the new component's INPUT and OUTPUT ports — the dialog
    itself never asks the user to pick or order them. Auto-inference
    happens in `GameManager._finalize_save_as_component` (which sees
    the live workspace), not here, so the dialog stays decoupled from
    component types. See TODO's "Save-as-Component port inference
    rule" entry for the ordering logic.

    Modal: while the dialog is open it consumes every mouse and
    keyboard event so the workspace beneath it is paused. Esc
    dismisses (mirrors the bottom-left popup's Esc dismiss in
    `GameManager._handle_keydown`). Click-outside-the-body is a no-op
    (NOT dismiss) — a typed name is too easy to lose accidentally,
    unlike the popup where click-outside-cancels is fine because
    there's no in-flight work.
    """

    def __init__(self, on_save, on_cancel):
        """Lay out the dialog and its sub-widgets centered on the screen.

        Args:
            on_save (Callable[[str], None]): Called with the trimmed
                uppercase name when the user clicks the enabled Save
                button. The dialog itself does not dismiss after Save —
                the caller is expected to dispose of the dialog as part
                of finalize so close-vs-stay-open stays the caller's
                policy, not the dialog's.
            on_cancel (Callable[[], None]): Called with no args when the
                user clicks Cancel or presses Esc.
        """
        self._on_save = on_save
        self._on_cancel = on_cancel
        # Centered on screen.
        self.rect = pygame.Rect(0, 0, DS.WIDTH, DS.HEIGHT)
        self.rect.center = (ScreenSettings.WIDTH // 2,
                            ScreenSettings.HEIGHT // 2)
        # Pre-rendered title surface; the title label never changes so a
        # one-time render is cheaper than a per-frame Fonts.text_box call.
        self._title_surf = Fonts.text_box.render(
            DS.TITLE, True, DS.TITLE_COLOR,
        )
        # Backdrop surface dims the workspace behind the dialog. Built
        # once at construction with per-surface alpha so per-frame draw
        # is a single blit (rather than re-rendering the alpha rect).
        self._backdrop = pygame.Surface(
            (ScreenSettings.WIDTH, ScreenSettings.HEIGHT)
        )
        self._backdrop.fill(DS.BACKDROP_COLOR)
        self._backdrop.set_alpha(DS.BACKDROP_ALPHA)
        # Lay out the (small) widget set top-to-bottom inside the
        # dialog body. Title at top-left of the inner padding; name
        # field below it; Save/Cancel anchored to the bottom-right so
        # any earlier-section size tweak doesn't shove them off-rect.
        cursor_y = self.rect.y + DS.PADDING
        self._title_pos = (self.rect.x + DS.PADDING, cursor_y)
        cursor_y += self._title_surf.get_height() + DS.SECTION_GAP
        inner_width = DS.WIDTH - 2 * DS.PADDING
        self._name_field = _NameField(
            self.rect.x + DS.PADDING, cursor_y, inner_width,
        )
        # Make typing immediate when the dialog opens.
        self._name_field.focus()
        # Buttons: Save right-edge primary, Cancel to its left.
        button_y = (self.rect.bottom
                    - DS.PADDING - DS.BUTTON_HEIGHT)
        self._save_rect = pygame.Rect(
            self.rect.right - DS.PADDING - DS.BUTTON_WIDTH,
            button_y,
            DS.BUTTON_WIDTH, DS.BUTTON_HEIGHT,
        )
        self._cancel_rect = pygame.Rect(
            self._save_rect.left - DS.BUTTON_GAP - DS.BUTTON_WIDTH,
            button_y,
            DS.BUTTON_WIDTH, DS.BUTTON_HEIGHT,
        )
        # Pre-render the button labels — they never change, and the
        # Save label's color depends only on enabled state which the
        # draw method swaps via two pre-rendered surfaces.
        self._save_label_enabled = Fonts.text_box.render(
            DS.BUTTON_LABEL_SAVE, True, DS.BUTTON_TEXT_COLOR_ENABLED,
        )
        self._save_label_disabled = Fonts.text_box.render(
            DS.BUTTON_LABEL_SAVE, True, DS.BUTTON_TEXT_COLOR_DISABLED,
        )
        self._cancel_label = Fonts.text_box.render(
            DS.BUTTON_LABEL_CANCEL, True, DS.BUTTON_TEXT_COLOR_ENABLED,
        )

    # -------------------------
    # VALIDATION
    # -------------------------

    def _is_save_enabled(self):
        """Return True if the form is in a valid save state.

        Save requires only that the name is non-empty after stripping
        whitespace. Inputs/outputs are not the dialog's concern in v2 —
        they're auto-inferred by the manager from the workspace at
        save time.

        Returns:
            bool: True if Save should be clickable this frame.
        """
        return bool(self._name_field.text.strip())

    # -------------------------
    # EVENT HANDLING
    # -------------------------

    def handle_event(self, event):
        """Consume a single event for the dialog.

        Modal: every event the dialog sees is treated as belonging to
        the dialog. The return value is currently unused (the manager
        always continues the loop after dispatching to the dialog) but
        kept truthy so the contract stays consistent with other
        consumers (text-box manager, bank, wires).

        Args:
            event (pygame.event.Event): The event to process.

        Returns:
            bool: Always True — the dialog claims everything while open.
        """
        if event.type == pygame.KEYDOWN:
            self._handle_keydown(event)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == InputSettings.LEFT_CLICK:
                self._handle_left_click(event.pos)
        # MOUSEBUTTONUP and MOUSEMOTION are intentionally swallowed
        # without further routing — nothing in the dialog reacts to them
        # (no drag, no hover state) but consuming them keeps the modal
        # contract honest so a release-outside doesn't end a drag the
        # dialog never started.
        return True

    def _handle_keydown(self, event):
        """Route a KEYDOWN to either Esc-dismiss or the focused name field.

        Args:
            event (pygame.event.Event): The KEYDOWN event.
        """
        if event.key == pygame.K_ESCAPE:
            self._on_cancel()
            return
        if self._name_field.focused:
            self._name_field.handle_key(event)

    def _handle_left_click(self, pos):
        """Route a left-click to the right widget inside the dialog body.

        Click priority: Save → Cancel → name field → anywhere else
        inside the body (unfocus the name field). A click outside the
        body is consumed (modal) but does nothing.

        Args:
            pos (tuple[int, int]): Cursor position in screen coordinates.
        """
        if self._save_rect.collidepoint(pos):
            if self._is_save_enabled():
                self._on_save(self._name_field.text.strip())
            return
        if self._cancel_rect.collidepoint(pos):
            self._on_cancel()
            return
        if self._name_field.hit(pos):
            self._name_field.focus()
            return
        # Click on dialog body but not on any widget: drop focus from
        # the name field so a stray click on padding can't leave the
        # caret blinking. Clicks fully outside the dialog body are
        # also handled by this path (modal — no fall-through).
        self._name_field.blur()

    # -------------------------
    # RENDER
    # -------------------------

    def draw(self, surface):
        """Paint the backdrop dim, the dialog body, and every sub-widget.

        Args:
            surface (pygame.Surface): The surface to draw onto.
        """
        surface.blit(self._backdrop, (0, 0))
        pygame.draw.rect(surface, DS.BODY_COLOR, self.rect)
        pygame.draw.rect(surface, DS.BORDER_COLOR, self.rect,
                         DS.BORDER_THICKNESS)
        surface.blit(self._title_surf, self._title_pos)
        self._name_field.draw(surface)
        self._draw_buttons(surface)

    def _draw_buttons(self, surface):
        """Render the Save and Cancel buttons in their current states.

        Save's fill + label both swap based on `_is_save_enabled()` so a
        disabled Save reads as a placeholder rather than a live
        affordance (same disabled-vs-enabled treatment the bottom-left
        popup uses for its items).

        Args:
            surface (pygame.Surface): The surface to draw onto.
        """
        save_enabled = self._is_save_enabled()
        save_bg = (DS.BUTTON_BG_ENABLED if save_enabled
                   else DS.BUTTON_BG_DISABLED)
        pygame.draw.rect(surface, save_bg, self._save_rect)
        pygame.draw.rect(surface, DS.BUTTON_BORDER_COLOR, self._save_rect, 1)
        save_label = (self._save_label_enabled if save_enabled
                      else self._save_label_disabled)
        save_label_rect = save_label.get_rect(center=self._save_rect.center)
        surface.blit(save_label, save_label_rect)
        pygame.draw.rect(surface, DS.BUTTON_BG_CANCEL, self._cancel_rect)
        pygame.draw.rect(surface, DS.BUTTON_BORDER_COLOR,
                         self._cancel_rect, 1)
        cancel_label_rect = self._cancel_label.get_rect(
            center=self._cancel_rect.center,
        )
        surface.blit(self._cancel_label, cancel_label_rect)
