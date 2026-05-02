import pygame

from elements import Component, LED, Switch
from settings import InputSettings, ScreenSettings, UISettings


class ComponentBank:
    """The toolbox at the bottom of the screen — templates students drag onto the workspace.

    Holds one template per spawnable kind. Clicking a template runs its
    associated spawn_fn, which is responsible for placing a fresh instance
    on the workspace under the cursor with dragging primed. Storing
    (template_drawable, spawn_fn) pairs (instead of just classes) keeps
    the bank open to non-Component spawnables like the upcoming TEXT
    label (which spawns a TextBox via the manager) and future saved
    sub-circuits — see docs/TODO.md "Toolbar TEXT button".
    """

    # Order is the left-to-right order shown in the toolbox.
    TEMPLATE_CLASSES = (Switch, Component, LED)

    def __init__(self):
        """Build the bank rect and the row of templates with their spawners."""
        self.rect = UISettings.BANK_RECT
        # List of (template_drawable, spawn_fn) tuples in display order. Each
        # spawn_fn is a closure that knows how to clone its template onto
        # the workspace at a click position; see _make_component_spawner.
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
