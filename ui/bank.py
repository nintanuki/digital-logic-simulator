import pygame
from copy import deepcopy

from core.elements import Component, LED, SavedComponent, Switch
from fonts import Fonts
from settings import (
    ComponentSettings,
    InputSettings,
    MenuButtonSettings,
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


class MenuButton:
    """Bottom-left bank button + the popup it toggles above the bank.

    Lives at the far-left of the toolbox bank as a Windows-style "Start"
    button. Clicking the button toggles `is_open`; while open, the popup
    rect is drawn directly above the button with the file-ops items listed
    inside. Each item owns a vertical band (its hit-rect) inside the popup;
    the bank routes a popup-body click to `item_label_at` to look up which
    item was clicked and dispatches via the `menu_actions` it was given.
    Items render in `ITEM_ENABLED_COLOR` when an action is wired up for
    them and in `ITEM_DISABLED_COLOR` otherwise, so the live affordances
    are visually distinct from the placeholders without any per-frame
    state. Click-outside and Esc already dismiss the popup elsewhere — see
    `ComponentBank.handle_event` and `GameManager._handle_keydown`.
    `ports = ()` mirrors `TextTemplate` so GameManager's port-hover walker
    can iterate this object the same way it iterates Component templates
    without a special case (if it's ever asked to).
    """

    def __init__(self, x, y, enabled_labels):
        """Lay out the button + popup rects, item hit-rects, and label surfaces.

        Args:
            x (int): Top-left x in screen coordinates.
            y (int): Top-left y in screen coordinates.
            enabled_labels (set[str]): Item labels that have a backing
                action and should render as live (white) affordances.
                Labels not in the set render greyed out and will be
                rejected by the bank's dispatch path.
        """
        size = MenuButtonSettings.SIZE
        self.rect = pygame.Rect(x, y, size, size)
        # Empty tuple (not list) so accidental .append() in any walker would
        # fail loud rather than silently grow this button's "ports".
        self.ports = ()
        # Anchored to BANK_RECT.top so popup floor aligns with bank top regardless of button inset.
        self.popup_rect = pygame.Rect(
            x,
            UISettings.BANK_RECT.top - MenuButtonSettings.POPUP_GAP - MenuButtonSettings.POPUP_HEIGHT,
            MenuButtonSettings.POPUP_WIDTH,
            MenuButtonSettings.POPUP_HEIGHT,
        )
        self.is_open = False
        # The label never changes, so render it once and blit per frame.
        self._label_surf = Fonts.text_box.render(
            MenuButtonSettings.LABEL,
            True,
            MenuButtonSettings.LABEL_COLOR,
        )
        # Built once at construction; geometry is fixed.
        self._item_rects = [
            pygame.Rect(
                self.popup_rect.left,
                self.popup_rect.top + index * MenuButtonSettings.ITEM_HEIGHT,
                MenuButtonSettings.POPUP_WIDTH,
                MenuButtonSettings.ITEM_HEIGHT,
            )
            for index in range(len(MenuButtonSettings.ITEM_LABELS))
        ]
        self._item_label_surfs = [
            Fonts.text_box.render(
                label,
                True,
                MenuButtonSettings.ITEM_ENABLED_COLOR
                if label in enabled_labels
                else MenuButtonSettings.ITEM_DISABLED_COLOR,
            )
            for label in MenuButtonSettings.ITEM_LABELS
        ]

    def toggle(self):
        """Flip the popup open/closed.

        Exposed as a method (not a direct attribute write) so future
        side-effects on open/close — focus stealing, item state refresh —
        have a single place to land.
        """
        self.is_open = not self.is_open

    def item_label_at(self, pos):
        """Return the item label whose hit-rect contains `pos`, else None.

        Used by `ComponentBank.handle_event` to look up which popup item a
        click landed on without leaking the rect-array layout to the bank.
        Caller is expected to gate this on `is_open` and on the popup body
        rect already containing `pos` — items only exist while the popup
        is visible.

        Args:
            pos (tuple[int, int]): Cursor position in screen space.

        Returns:
            str | None: The matching label from ITEM_LABELS, or None if
                no item's band contains the position.
        """
        for rect, label in zip(self._item_rects, MenuButtonSettings.ITEM_LABELS):
            if rect.collidepoint(pos):
                return label
        return None

    def draw(self, surface):
        """Render the button and, if open, the popup with its item labels.

        Item labels are blit after the popup body+border so they layer on
        top of the fill but stay inside the border. Each label is rendered
        in either ITEM_ENABLED_COLOR or ITEM_DISABLED_COLOR at construction
        time, so this loop is purely positional.

        Args:
            surface (pygame.Surface): The surface to draw onto.
        """
        pygame.draw.rect(surface, MenuButtonSettings.BODY_COLOR, self.rect)
        pygame.draw.rect(
            surface,
            MenuButtonSettings.BORDER_COLOR,
            self.rect,
            MenuButtonSettings.BORDER_THICKNESS,
        )
        label_rect = self._label_surf.get_rect(center=self.rect.center)
        surface.blit(self._label_surf, label_rect)
        if self.is_open:
            pygame.draw.rect(
                surface,
                MenuButtonSettings.POPUP_BODY_COLOR,
                self.popup_rect,
            )
            pygame.draw.rect(
                surface,
                MenuButtonSettings.POPUP_BORDER_COLOR,
                self.popup_rect,
                MenuButtonSettings.POPUP_BORDER_THICKNESS,
            )
            for rect, surf in zip(self._item_rects, self._item_label_surfs):
                label_y = rect.y + (rect.height - surf.get_height()) // 2
                surface.blit(
                    surf,
                    (rect.left + MenuButtonSettings.ITEM_PADDING_X, label_y),
                )


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

    def __init__(self, text_boxes, menu_actions):
        """Build the bank rect and the row of templates with their spawners.

        Args:
            text_boxes (TextBoxManager): Manager that owns workspace text
                boxes. Captured by the TEXT template's spawn closure so a
                click on that template can drop a focused TextBox without
                routing back through GameManager.
            menu_actions (dict[str, Callable[[], None]]): Map from popup
                item label (matching an entry in
                `MenuButtonSettings.ITEM_LABELS`) to the zero-arg callback
                that runs when that item is clicked. Items whose label is
                not a key in this dict render disabled and consume their
                clicks without doing anything. The MenuButton is told the
                set of enabled labels at construction so the rendered
                labels match the live affordances without a per-frame
                lookup.
        """
        self.rect = UISettings.BANK_RECT
        self._text_boxes = text_boxes
        self._menu_actions = menu_actions
        # Built before templates so the row lays out flush to the button's right edge.
        self.menu_button = MenuButton(
            UISettings.BANK_PADDING_X,
            self.rect.y + (self.rect.height - MenuButtonSettings.SIZE) // 2,
            set(menu_actions),
        )
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
        x = self.menu_button.rect.right + UISettings.BANK_TEMPLATE_GAP
        entries = []
        for cls in self.TEMPLATE_CLASSES:
            tpl = cls(x, 0)
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
        x = self.menu_button.rect.right + UISettings.BANK_TEMPLATE_GAP
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
        self.menu_button.draw(surface)
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
        if self.menu_button.rect.collidepoint(event.pos):
            self.menu_button.toggle()
            return True
        # Popup body click: dispatch action if enabled, dismiss on miss.
        if self.menu_button.is_open:
            if self.menu_button.popup_rect.collidepoint(event.pos):
                label = self.menu_button.item_label_at(event.pos)
                action = self._menu_actions.get(label) if label else None
                if action is not None:
                    self.menu_button.toggle()
                    action()
                return True
            self.menu_button.toggle()
        for tpl, spawn_fn in self._templates_and_spawners:
            if tpl.rect.collidepoint(event.pos):
                spawn_fn(event.pos, components_list)
                return True
        return False
