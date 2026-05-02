import pygame

from elements import Component, LED, Switch
from fonts import Fonts
from settings import (
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
        # Held so _make_textbox_spawner's closure can reach the manager
        # without bank.handle_event needing a wider signature.
        self._text_boxes = text_boxes
        # List of (template_drawable, spawn_fn) tuples in display order. Each
        # spawn_fn is a closure that knows how to clone its template onto
        # the workspace at a click position; see _make_component_spawner
        # and _make_textbox_spawner.
        self._templates_and_spawners = self._build_templates()

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
        x = UISettings.BANK_PADDING_X
        entries = []
        for cls in self.TEMPLATE_CLASSES:
            # Instantiate at a placeholder y, then vertically center based
            # on the component's actual height (which the class decides).
            tpl = cls(x, 0)
            tpl.rect.y = self.rect.y + (self.rect.height - tpl.rect.height) // 2
            entries.append((tpl, self._make_component_spawner(tpl, cls)))
            x += tpl.rect.width + UISettings.BANK_TEMPLATE_GAP
        # The TEXT template lives in the same row as the component templates
        # so the bank stays one homogeneous list of (drawable, spawn_fn)
        # pairs. It spawns through TextBoxManager rather than into the
        # components list — see _make_textbox_spawner.
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
            # The new component is the same runtime class as the clicked
            # template (so a click on the Switch template spawns a Switch,
            # etc.). It's dropped into the workspace centered on the
            # cursor with dragging already on, so the next MOUSEMOTION
            # carries it where the user is going.
            new_comp = cls(
                event_pos[0] - tpl.rect.width // 2,
                event_pos[1] - tpl.rect.height // 2,
            )
            new_comp.dragging = True
            # Match Component.handle_event's grip math so the spawned
            # component tracks the cursor cleanly on the next MOUSEMOTION.
            new_comp.offset_x = new_comp.rect.x - event_pos[0]
            new_comp.offset_y = new_comp.rect.y - event_pos[1]
            # The spawn drag was started by the bank, not by the
            # component's own MOUSEBUTTONDOWN, so suppress the click
            # hook on the upcoming release. Otherwise a Switch spawned
            # via a stationary click would toggle on the way out of
            # the bank.
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
            # components_list is part of the shared spawn protocol but a
            # text box is an annotation, not a circuit element — drop it
            # into the text-box manager and ignore the list.
            text_boxes.spawn_at(event_pos)
        return spawn

    def spawn_component(self, cls, event_pos, components_list):
        """Spawn an instance of `cls` through the bank's own spawn path.

        Exposed so keyboard shortcuts (e.g. `main.py`'s K_n) share the
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
        # `type(tpl) is cls` (not isinstance) so a Switch template doesn't
        # match a request for its Component base class — each template kind
        # owns its exact spawner.
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
        if event.type != pygame.MOUSEBUTTONDOWN or event.button != InputSettings.LEFT_CLICK:
            return False
        for tpl, spawn_fn in self._templates_and_spawners:
            if tpl.rect.collidepoint(event.pos):
                spawn_fn(event.pos, components_list)
                return True
        return False
