import pygame
from copy import deepcopy

from core.elements import Component, LED, SavedComponent, Switch
from fonts import Fonts
from settings import (
    ComponentSettings,
    InputSettings,
    ScreenSettings,
    TextTemplateSettings,
    UISettings,
)


class TextTemplate:
    """Bank-side template that spawns a focused TextBox on click.

    Visually a small square with the word "TEXT" centered on it, sized to
    match Switch/LED so the row of templates reads as one row. Has no ports
    because text boxes carry no signal — `ports` is exposed as an empty
    tuple so GameManager's port-hover walker can iterate this template the
    same way it iterates Component templates without a special case.
    """

    def __init__(self, x, y):
        """Lay out the template's rect and pre-render its static label.

        Args:
            x (int): Top-left x in screen coordinates.
            y (int): Top-left y in screen coordinates.
        """
        size = TextTemplateSettings.SIZE
        self.rect = pygame.Rect(x, y, size, size)
        # Empty tuple (not list) so accidental .append() in the hover walker
        # would fail loud rather than silently grow the template's "ports".
        self.ports = ()
        # The label never changes, so render it once and blit per frame.
        self._label_surf = Fonts.text_box.render(
            TextTemplateSettings.LABEL,
            True,
            TextTemplateSettings.LABEL_COLOR,
        )

    def draw(self, surface):
        """Render the template body, border, and centered TEXT label.

        Args:
            surface (pygame.Surface): The surface to draw onto.
        """
        pygame.draw.rect(surface, TextTemplateSettings.BODY_COLOR, self.rect)
        pygame.draw.rect(
            surface,
            TextTemplateSettings.BORDER_COLOR,
            self.rect,
            TextTemplateSettings.BORDER_THICKNESS,
        )
        label_rect = self._label_surf.get_rect(center=self.rect.center)
        surface.blit(self._label_surf, label_rect)


class ComponentBank:
    """The toolbox at the bottom of the screen — templates students drag onto the workspace.

    Holds one template per spawnable kind. Clicking a template runs its
    associated spawn_fn, which is responsible for placing a fresh instance
    on the workspace under the cursor with dragging primed. Storing
    (template_drawable, spawn_fn) pairs (instead of just classes) keeps
    the bank open to non-Component spawnables like the TEXT label (which
    spawns a TextBox via the manager) and future saved sub-circuits.
    """

    # Order is the left-to-right order shown in the toolbox.
    TEMPLATE_CLASSES = (Switch, Component, LED)

    def __init__(self, text_boxes):
        """Build the bank rect and the row of templates with their spawners.

        Args:
            text_boxes (TextBoxManager): Manager that owns workspace text
                boxes. Captured by the TEXT template's spawn closure so a
                click on that template can drop a focused TextBox without
                routing back through GameManager.
        """
        self.rect = UISettings.BANK_RECT
        self._text_boxes = text_boxes
        self._templates_and_spawners = self._build_templates()
        self._protected_template_ids = {
            id(tpl) for tpl, _spawn in self._templates_and_spawners
        }
        self._drag_template = None
        self._drag_template_mouse_anchor = (0, 0)
        self._drag_template_rect_anchor = (0, 0)

    @property
    def templates(self):
        """The drawable templates in display order.

        Exposed as a property so external callers (GameManager's port-hover
        routing) can iterate templates without learning about the
        spawn_fn pairing.

        Returns:
            list: The template drawables in left-to-right display order.
        """
        return [tpl for tpl, _ in self._templates_and_spawners]

    def _build_templates(self):
        """Lay out one template per spawnable kind, left-to-right inside the bank.

        Each template is vertically centered inside the bank regardless of
        its own height, so a future smaller / larger component still looks
        intentional. Spacing comes from UISettings so the layout has no
        magic numbers. Each template is paired with a spawn_fn closure that
        knows how to clone it onto the workspace at a click position.

        Returns:
            list[tuple]: (template_drawable, spawn_fn) pairs in display order.
        """
        x = self.rect.x + UISettings.BANK_PADDING_X
        entries = []
        for cls in self.TEMPLATE_CLASSES:
            tpl = cls(x, 0)
            if cls is LED:
                tpl.rect.x += UISettings.BANK_LED_SHIFT_X
            tpl.rect.y = self.rect.y + (self.rect.height - tpl.rect.height) // 2
            entries.append((tpl, self._make_component_spawner(tpl, cls)))
            x += tpl.rect.width + UISettings.BANK_TEMPLATE_GAP
        text_tpl = TextTemplate(x, 0)
        text_tpl.rect.y = self.rect.y + (self.rect.height - text_tpl.rect.height) // 2
        entries.append((text_tpl, self._make_textbox_spawner()))
        return entries

    @staticmethod
    def _make_component_spawner(tpl, cls):
        """Build a spawn_fn that drops a fresh cls(...) onto the workspace.

        The returned callable takes (event_pos, components_list) and
        appends a new Component subclass instance positioned under the
        cursor with dragging primed — the same protocol the previous
        inline spawn used, just lifted into a closure so non-Component
        spawnables can plug in beside it.

        Args:
            tpl (Component): The template instance whose width/height
                determine the cursor-centering offset on spawn.
            cls (type[Component]): The Component subclass to instantiate.

        Returns:
            Callable[[tuple[int, int], list[Component]], None]: The spawn
                function described above.
        """
        def spawn(event_pos, components_list):
            new_comp = cls(
                event_pos[0] - tpl.rect.width // 2,
                event_pos[1] - tpl.rect.height // 2,
            )
            new_comp.dragging = True
            new_comp.offset_x = new_comp.rect.x - event_pos[0]
            new_comp.offset_y = new_comp.rect.y - event_pos[1]
            new_comp._moved_while_dragging = True
            components_list.append(new_comp)
        return spawn

    def _make_textbox_spawner(self):
        """Build a spawn_fn that drops a fresh focused TextBox via the manager.

        The closure captures the TextBoxManager passed into the bank at
        construction time so the bank doesn't have to look it up on every
        click. Spawned text boxes are immediately focused — see
        TextBoxManager.spawn_at — so the student can start typing without a
        follow-up click.

        Returns:
            Callable[[tuple[int, int], list], None]: Spawner that ignores
                components_list (text boxes aren't components) and routes to
                the text-box manager instead.
        """
        text_boxes = self._text_boxes
        def spawn(event_pos, components_list):
            text_boxes.spawn_at(event_pos)
        return spawn

    @staticmethod
    def _prime_spawn_drag(new_comp, event_pos):
        """Prime a freshly spawned component for drag-on-spawn behavior.

        Args:
            new_comp (Component): The spawned component instance.
            event_pos (tuple[int, int]): Cursor position at spawn time.
        """
        new_comp.dragging = True
        new_comp.offset_x = new_comp.rect.x - event_pos[0]
        new_comp.offset_y = new_comp.rect.y - event_pos[1]
        # Spawned via template click, so suppress click action on release.
        new_comp._moved_while_dragging = True

    def add_saved_component_template(self, name, color, definition):
        """Append a new saved-component template to the right end of the bank.

        Pass 1 step 2: this exposes save results immediately in-session.
        In step 3+, spawned instances are working wrapped sub-circuits.

        Args:
            name (str): Saved component display name.
            color (tuple[int, int, int]): RGB body color.
            definition (dict): Serialized sub-circuit definition.
        """
        x = self.rect.x + UISettings.BANK_PADDING_X
        if self._templates_and_spawners:
            last_tpl, _last_spawn = self._templates_and_spawners[-1]
            x = last_tpl.rect.right + UISettings.BANK_TEMPLATE_GAP
        template = SavedComponent(x, 0, name, color, definition)
        template.rect.y = self.rect.y + (self.rect.height - template.rect.height) // 2

        def spawn(event_pos, components_list):
            new_comp = SavedComponent(
                event_pos[0] - template.rect.width // 2,
                event_pos[1] - template.rect.height // 2,
                name,
                color,
                deepcopy(definition),
            )
            self._prime_spawn_drag(new_comp, event_pos)
            components_list.append(new_comp)

        self._templates_and_spawners.append((template, spawn))

    def spawn_component(self, cls, event_pos, components_list):
        """Spawn an instance of `cls` through the bank's own spawn path.

        Exposed so keyboard shortcuts share the
        bank's cursor-centering and drag-priming logic instead of
        reimplementing it — keeps the click and hotkey entry points honest.

        Args:
            cls (type[Component]): The Component subclass to instantiate.
                Must match a template currently in the bank.
            event_pos (tuple[int, int]): Cursor position the new component
                should be centered on.
            components_list (list[Component]): The workspace component list
                the new instance is appended to.

        Returns:
            None.

        Raises:
            KeyError: If `cls` is not a known template class on this bank.
        """
        for tpl, spawn_fn in self._templates_and_spawners:
            if type(tpl) is cls:
                spawn_fn(event_pos, components_list)
                return
        raise KeyError(f"No bank template for {cls.__name__}")

    def draw(self, surface):
        """Render the bank background, separator line, and every template.

        Args:
            surface (pygame.Surface): The surface to draw onto.
        """
        pygame.draw.rect(surface, UISettings.BANK_COLOR, self.rect)
        pygame.draw.line(
            surface,
            UISettings.BANK_LINE_COLOR,
            (0, self.rect.y),
            (ScreenSettings.WIDTH, self.rect.y),
            2,
        )
        for tpl, _spawn in self._templates_and_spawners:
            tpl.draw(surface)

    def _template_at(self, pos):
        """Return top-most bank template and spawn_fn under pos, else None."""
        for tpl, spawn_fn in reversed(self._templates_and_spawners):
            if tpl.rect.collidepoint(pos):
                return tpl, spawn_fn
        return None

    def _begin_template_drag(self, tpl, mouse_pos):
        """Start dragging a template inside the bank area."""
        self._drag_template = tpl
        self._drag_template_mouse_anchor = mouse_pos
        self._drag_template_rect_anchor = (tpl.rect.x, tpl.rect.y)

    def _update_template_drag(self, mouse_pos):
        """Move active dragged template while clamping it to bank bounds."""
        if self._drag_template is None:
            return
        dx = mouse_pos[0] - self._drag_template_mouse_anchor[0]
        dy = mouse_pos[1] - self._drag_template_mouse_anchor[1]
        template = self._drag_template
        template.rect.x = self._drag_template_rect_anchor[0] + dx
        template.rect.y = self._drag_template_rect_anchor[1] + dy
        template.rect.x = max(self.rect.left, min(template.rect.x, self.rect.right - template.rect.width))
        template.rect.y = max(self.rect.top, min(template.rect.y, self.rect.bottom - template.rect.height))

    def _end_template_drag(self):
        """Finish drag and keep template draw/hit order aligned to x position."""
        self._drag_template = None
        self._templates_and_spawners.sort(key=lambda entry: entry[0].rect.x)

    def handle_event(self, event, components_list):
        """Route a left-click on a template through to its spawn_fn.

        Each template's spawn_fn owns the actual placement logic — see
        _make_component_spawner — so this loop only finds the clicked
        template and delegates.

        Args:
            event (pygame.event.Event): The event to inspect.
            components_list (list[Component]): The workspace's component
                list, passed through to spawn_fn for component templates.

        Returns:
            bool: True if a template was clicked and the event was handled.
        """
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == InputSettings.MIDDLE_CLICK:
            hit = self._template_at(event.pos)
            if hit is None:
                return False
            tpl, _spawn_fn = hit
            self._begin_template_drag(tpl, event.pos)
            return True

        if event.type == pygame.MOUSEMOTION and self._drag_template is not None:
            self._update_template_drag(event.pos)
            return True

        if event.type == pygame.MOUSEBUTTONUP and event.button == InputSettings.MIDDLE_CLICK:
            if self._drag_template is None:
                return False
            self._end_template_drag()
            return True

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == InputSettings.RIGHT_CLICK:
            hit = self._template_at(event.pos)
            if hit is None:
                return False
            tpl, _spawn_fn = hit
            if id(tpl) in self._protected_template_ids:
                return True
            self._templates_and_spawners = [
                entry for entry in self._templates_and_spawners
                if entry[0] is not tpl
            ]
            return True

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == InputSettings.LEFT_CLICK:
            hit = self._template_at(event.pos)
            if hit is None:
                return False
            _tpl, spawn_fn = hit
            spawn_fn(event.pos, components_list)
            return True
        return False
