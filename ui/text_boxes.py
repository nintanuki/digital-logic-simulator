import pygame
from typing import Callable

from fonts import Fonts
from settings import (
    InputSettings,
    ScreenSettings,
    TextBoxSettings,
    UISettings,
)


class TextBox:
    """A draggable, editable annotation label sitting on the workspace.

    Text boxes carry no signal and never appear on the toolbox bank — they
    exist purely so students can label parts of their circuit ("clock",
    "carry-out", "this is the AND gate built from two NANDs"). New boxes
    start narrow, expand width while typing, then wrap and grow downward
    after reaching a configured max width.

    Focus, drag, and delete semantics mirror Component as closely as
    possible: left-click focuses + may begin a drag, right-click on the
    body deletes, drag is constrained inside the workspace. Edits happen
    via KEYDOWN forwarded by the TextBoxManager whenever this box is the
    focused one.
    """

    def __init__(self, x, y):
        """
        Args:
            x (int): Initial top-left x in screen coordinates.
            y (int): Initial top-left y in screen coordinates.
        """
        self.text = ""
        # Drag state mirrors Component: offsets capture grab point so the
        # box doesn't snap to the cursor's top-left on the first motion.
        self.dragging = False
        self.offset_x = 0
        self.offset_y = 0
        # Focus is owned by TextBoxManager but cached here so draw() can
        # branch on border color and caret visibility without a back-ref.
        self.focused = False
        # Time (in pygame ticks) when this box most recently gained focus.
        # Used only for caret blink phase so the caret restarts visible
        # every time the user re-focuses, instead of mid-blink.
        self._focus_tick = 0

        self.rect = pygame.Rect(x, y, TextBoxSettings.MIN_WIDTH,
                                TextBoxSettings.MIN_HEIGHT)
        self._lines = [""]
        self._layout_to_text()

    # -------------------------
    # FOCUS / DRAG / EDIT API (called by TextBoxManager)
    # -------------------------

    def focus(self):
        """Mark this box as receiving keystrokes; reset caret blink phase."""
        self.focused = True
        self._focus_tick = pygame.time.get_ticks()

    def blur(self):
        """Stop receiving keystrokes."""
        self.focused = False

    def start_drag(self, pos):
        """Begin dragging this box from cursor position pos.

        Args:
            pos (tuple[int, int]): Cursor position in screen coordinates.
        """
        self.dragging = True
        self.offset_x = self.rect.x - pos[0]
        self.offset_y = self.rect.y - pos[1]

    def end_drag(self):
        """Stop dragging this box. Safe to call when not dragging."""
        self.dragging = False

    def handle_motion(self, pos):
        """Update box position while dragging.

        Args:
            pos (tuple[int, int]): Cursor position in screen coordinates.
        """
        if not self.dragging:
            return
        self.rect.x = pos[0] + self.offset_x
        self.rect.y = pos[1] + self.offset_y
        self._clamp_to_workspace()

    def handle_key(self, event):
        """Apply a keystroke to the focused text box.

        Backspace removes the last character; Return inserts a newline; any
        other key with a printable unicode value is uppercased and appended
        (text boxes are uppercase to match every other label in the
        workspace — component names, port labels, IN/OUT). Caret stays
        implicitly at the end of the text — there is no cursor navigation
        in v1, which keeps the editing model dead simple for students.

        Args:
            event (pygame.event.Event): A KEYDOWN event the manager
                forwarded after deciding this box has focus.
        """
        if event.key == pygame.K_BACKSPACE:
            self.text = self.text[:-1]
        elif event.key == pygame.K_RETURN:
            self.text += "\n"
        elif event.unicode and event.unicode.isprintable():
            # str.upper() is a no-op for digits, punctuation, and already-
            # uppercase letters, so this is safe to call unconditionally.
            self.text += event.unicode.upper()
        else:
            # Non-printable, non-edit key (arrows, F-keys, modifiers) —
            # ignore so the user doesn't see junk characters appear.
            return
        # Re-layout on every meaningful edit so width grows first, then
        # height once the max width cap is reached.
        self._layout_to_text()
        # Re-clamp in case growing the box pushed it past the workspace
        # bottom (the toolbox edge).
        self._clamp_to_workspace()
        # Reset the blink so the caret stays visible immediately after a
        # keystroke instead of disappearing for half a period.
        self._focus_tick = pygame.time.get_ticks()

    # -------------------------
    # HIT-TEST
    # -------------------------

    def hit(self, pos):
        """Return True if pos lies inside the box's body.

        Args:
            pos (tuple[int, int]): Cursor position in screen coordinates.

        Returns:
            bool: True if the cursor is over this text box.
        """
        return self.rect.collidepoint(pos)

    # -------------------------
    # RENDER
    # -------------------------

    def draw(self, surface):
        """Render the body, border, text (or placeholder), and caret.

        Args:
            surface (pygame.Surface): The surface to draw onto.
        """
        pygame.draw.rect(surface, TextBoxSettings.BODY_COLOR, self.rect)
        border_color = (
            TextBoxSettings.BORDER_FOCUSED_COLOR
            if self.focused else TextBoxSettings.BORDER_COLOR
        )
        pygame.draw.rect(surface, border_color, self.rect,
                         TextBoxSettings.BORDER_THICKNESS)
        self._draw_text(surface)
        if self.focused and self._caret_visible():
            self._draw_caret(surface)

    def _draw_text(self, surface):
        """Render either the wrapped lines or, if empty + unfocused, placeholder.

        Args:
            surface (pygame.Surface): The surface to draw onto.
        """
        font = Fonts.text_box
        y = self.rect.y + TextBoxSettings.PADDING
        if not self.text and not self.focused:
            # Show placeholder only when both empty AND unfocused, so the
            # caret has a clean empty box to blink in once the user clicks.
            line_surf = font.render(TextBoxSettings.PLACEHOLDER_TEXT, True,
                                    TextBoxSettings.PLACEHOLDER_COLOR)
            x = self._line_x(TextBoxSettings.PLACEHOLDER_TEXT)
            surface.blit(line_surf, (x, y))
            return
        for line in self._lines:
            line_surf = font.render(line, True, TextBoxSettings.TEXT_COLOR)
            x = self._line_x(line)
            surface.blit(line_surf, (x, y))
            y += font.get_linesize()

    def _draw_caret(self, surface):
        """Render the blinking caret at the end of the last text line.

        Args:
            surface (pygame.Surface): The surface to draw onto.
        """
        font = Fonts.text_box
        last_line = self._lines[-1] if self._lines else ""
        text_width = font.size(last_line)[0]
        x = self._line_x(last_line) + text_width
        # Caret sits on the same row as the last line; total y offset is
        # padding plus all lines above the last.
        rows_above = max(len(self._lines) - 1, 0)
        y = self.rect.y + TextBoxSettings.PADDING + rows_above * font.get_linesize()
        pygame.draw.rect(
            surface,
            TextBoxSettings.CARET_COLOR,
            pygame.Rect(x, y, TextBoxSettings.CARET_WIDTH, font.get_height()),
        )

    def _caret_visible(self):
        """Return True if the caret should be drawn this frame.

        Returns:
            bool: True during the first half of each blink period.
        """
        elapsed = pygame.time.get_ticks() - self._focus_tick
        return (elapsed % TextBoxSettings.CARET_BLINK_MS) < (TextBoxSettings.CARET_BLINK_MS // 2)

    # -------------------------
    # INTERNAL HELPERS
    # -------------------------

    def _layout_to_text(self):
        """Update wrapped lines and rect size from the current text."""
        inner_width = self._target_inner_width()
        self._lines = self._wrap_lines(inner_width)
        self._resize_to_lines(inner_width)

    def _line_x(self, line):
        """Return the x-coordinate to horizontally center line in the box."""
        text_width = Fonts.text_box.size(line)[0]
        left = self.rect.x + TextBoxSettings.PADDING
        right = self.rect.right - TextBoxSettings.PADDING
        inner_center = (left + right) // 2
        return inner_center - text_width // 2

    def _target_inner_width(self):
        """Choose current inner width between MIN_WIDTH and MAX_WIDTH."""
        font = Fonts.text_box
        min_inner = max(1, TextBoxSettings.MIN_WIDTH - 2 * TextBoxSettings.PADDING)
        max_inner = max(min_inner, TextBoxSettings.MAX_WIDTH - 2 * TextBoxSettings.PADDING)
        paragraphs = self.text.split("\n") if self.text else [""]
        longest = max(font.size(line)[0] for line in paragraphs)
        return max(min_inner, min(longest, max_inner))

    def _wrap_lines(self, inner_width):
        """Word-wrap self.text to fit inside the inner width of the box.

        Honors explicit '\\n' line breaks first, then greedy-wraps each
        paragraph word by word. Words longer than the inner width are
        force-broken character by character so they can't overflow.

        Returns:
            list[str]: The lines the text should render as.
        """
        font = Fonts.text_box
        wrapped = []
        for paragraph in self.text.split("\n"):
            if not paragraph:
                # Preserve blank lines so Enter-Enter visibly grows the box.
                wrapped.append("")
                continue
            current = ""
            for word in paragraph.split(" "):
                candidate = word if not current else current + " " + word
                if font.size(candidate)[0] <= inner_width:
                    current = candidate
                    continue
                # Candidate doesn't fit. Flush current line, then place word.
                if current:
                    wrapped.append(current)
                if font.size(word)[0] > inner_width:
                    # Word alone is too wide — force-break it.
                    current = self._break_long_word(word, inner_width, wrapped)
                else:
                    current = word
            if current:
                wrapped.append(current)
        # Always return at least one row so caret has somewhere to render.
        if not wrapped:
            wrapped.append("")
        return wrapped

    def _break_long_word(self, word, inner_width, wrapped):
        """Append force-broken chunks of word to wrapped, return the last partial.

        Used by _wrap_lines when a single word is wider than the box. All
        but the final chunk are appended to wrapped in place; the remainder
        becomes the start of the next line for further wrapping.

        Args:
            word (str): The word to split.
            inner_width (int): Pixel budget per line.
            wrapped (list[str]): Output list to append full chunks into.

        Returns:
            str: The final, partial chunk that did not need flushing yet.
        """
        font = Fonts.text_box
        chunk = ""
        for ch in word:
            if font.size(chunk + ch)[0] <= inner_width:
                chunk += ch
            else:
                wrapped.append(chunk)
                chunk = ch
        return chunk

    def _resize_to_lines(self, inner_width):
        """Resize self.rect.height to exactly fit self._lines.

        Width is driven by the current text and clamped to [MIN_WIDTH,
        MAX_WIDTH]. Height is at least MIN_HEIGHT so an empty box stays
        grabbable.
        """
        self.rect.width = inner_width + 2 * TextBoxSettings.PADDING
        line_height = Fonts.text_box.get_linesize()
        needed = len(self._lines) * line_height + 2 * TextBoxSettings.PADDING
        self.rect.height = max(TextBoxSettings.MIN_HEIGHT, needed)

    def _clamp_to_workspace(self):
        """Keep the rect inside the workspace, above the toolbox bank.

        Mirrors Component._clamp_to_workspace so a dragged or grown box
        cannot disappear behind the toolbox or off any screen edge.
        """
        max_x = ScreenSettings.WIDTH - self.rect.width
        max_y = UISettings.BANK_RECT.top - self.rect.height
        if self.rect.x < 0:
            self.rect.x = 0
        elif self.rect.x > max_x:
            self.rect.x = max_x
        if self.rect.y < 0:
            self.rect.y = 0
        elif self.rect.y > max_y:
            self.rect.y = max_y


class TextBoxManager:
    """Owns every text box on the workspace plus focus/drag routing.

    Lifts text-box state and event routing off GameManager per the project's
    architectural rule that GameManager stays light. GameManager forwards
    every event here first, before wires/bank/components, so a click on a
    text box edits it instead of starting a wire on a port that happens to
    sit underneath, and KEYDOWN events while a box is focused don't double
    as game shortcuts (e.g. typing "n" doesn't spawn a NAND).
    """

    def __init__(self):
        # Top of the list is the bottom of the visual stack. Append on
        # spawn so the newest box draws on top, matching the user's mental
        # model that what you just dropped is in front.
        self.text_boxes = []
        # The currently focused box, or None. Mirrored on each box's
        # .focused flag so draw() doesn't need a back-ref to the manager.
        self.focused = None
        # Optional callbacks set by GameManager to record undo/redo actions.
        # on_spawn(box) - called after a text box is created.
        # on_delete(box, index) - called after a text box is right-click deleted.
        self.on_spawn: Callable[[TextBox], None] | None = None
        self.on_delete: Callable[[TextBox, int], None] | None = None

    # -------------------------
    # SPAWN / LIFECYCLE
    # -------------------------

    def spawn_at(self, pos, focus=True):
        """Create a fresh text box centered on pos and optionally focus it.

        Args:
            pos (tuple[int, int]): Cursor position in screen coordinates.
            focus (bool): Whether to give the new box keyboard focus
                immediately. Defaults to True. Pass False when restoring
                from a saved project so the caret doesn't appear on the
                first box loaded.

        Returns:
            TextBox: The newly created box.
        """
        x = pos[0] - TextBoxSettings.MIN_WIDTH // 2
        y = pos[1] - TextBoxSettings.MIN_HEIGHT // 2
        box = TextBox(x, y)
        # Spawning slightly outside the workspace (e.g. cursor near the
        # toolbox) should still land cleanly inside it.
        box._clamp_to_workspace()
        self.text_boxes.append(box)
        if focus:
            self._focus(box)
        if self.on_spawn:
            self.on_spawn(box)
        return box

    def clear_all(self):
        """Remove all text boxes and clear focus state.

        Returns:
            None
        """
        self.text_boxes.clear()
        self._blur()

    # -------------------------
    # EVENT HANDLING
    # -------------------------

    def handle_event(self, event):
        """Try to consume an event for text-box editing/dragging/deletion.

        Args:
            event (pygame.event.Event): The event to inspect.

        Returns:
            bool: True if the event was consumed and the caller should not
                forward it to wires, bank, or components.
        """
        if event.type == pygame.KEYDOWN:
            return self._handle_keydown(event)
        if event.type == pygame.MOUSEMOTION:
            # Forward motion to whichever box is mid-drag (at most one).
            # Never consume — port hover and wire ghost both depend on
            # seeing every MOUSEMOTION.
            for box in self.text_boxes:
                box.handle_motion(event.pos)
            return False
        if event.type == pygame.MOUSEBUTTONDOWN:
            return self._handle_mouse_down(event)
        if event.type == pygame.MOUSEBUTTONUP:
            if event.button == InputSettings.LEFT_CLICK:
                # End drag on every box defensively. Don't consume so
                # components can also see their own mouse-up.
                for box in self.text_boxes:
                    box.end_drag()
            return False
        return False

    def _handle_keydown(self, event):
        """Forward a KEYDOWN to the focused box, if any.

        Args:
            event (pygame.event.Event): The KEYDOWN event.

        Returns:
            bool: True if a box absorbed the key (so GameManager's own
                keydown routing is skipped).
        """
        if self.focused is None:
            return False
        # Escape unfocuses without inserting anything — gives the user a
        # quick way out of editing back into the keyboard shortcuts.
        if event.key == pygame.K_ESCAPE:
            self._blur()
            return True
        self.focused.handle_key(event)
        return True

    def _handle_mouse_down(self, event):
        """Route a mouse-button press to focus, drag, or delete a box.

        Args:
            event (pygame.event.Event): The MOUSEBUTTONDOWN event.

        Returns:
            bool: True if a box was hit and the event was consumed.
        """
        hit = self._top_box_at(event.pos)
        if event.button == InputSettings.LEFT_CLICK:
            if hit is not None:
                self._focus(hit)
                hit.start_drag(event.pos)
                return True
            # Click on empty space drops focus but lets the click fall
            # through to wires / bank / components.
            self._blur()
            return False
        if event.button == InputSettings.RIGHT_CLICK:
            if hit is not None:
                if self.focused is hit:
                    self._blur()
                idx = self.text_boxes.index(hit)
                self.text_boxes.remove(hit)
                if self.on_delete:
                    self.on_delete(hit, idx)
                return True
        return False

    # -------------------------
    # RENDER
    # -------------------------

    def draw(self, surface):
        """Render every text box in stack order (oldest first, newest on top).

        Args:
            surface (pygame.Surface): The surface to draw onto.
        """
        for box in self.text_boxes:
            box.draw(surface)

    # -------------------------
    # INTERNAL HELPERS
    # -------------------------

    def _top_box_at(self, pos):
        """Return the topmost (last-drawn) text box under pos, or None.

        Args:
            pos (tuple[int, int]): Cursor position in screen coordinates.

        Returns:
            TextBox | None: The matching box, or None if pos hits no box.
        """
        for box in reversed(self.text_boxes):
            if box.hit(pos):
                return box
        return None

    def _focus(self, box):
        """Make box the focused one, blurring whichever was focused before.

        Args:
            box (TextBox): The box to focus.
        """
        if self.focused is box:
            return
        if self.focused is not None:
            self.focused.blur()
        self.focused = box
        box.focus()

    def _blur(self):
        """Clear focus from whichever box currently has it. Safe to call always."""
        if self.focused is not None:
            self.focused.blur()
            self.focused = None
