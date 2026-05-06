import pygame
from copy import deepcopy

from core.elements import Component, LED, SavedComponent, Switch
from ui.fonts import Fonts
from settings import (
    BankIOButtonSettings,
    BankPopupButtonSettings,
    BankToolboxButtonSettings,
    ComponentSettings,
    InputSettings,
    ScreenSettings,
    TextTemplateSettings,
    TopMenuBarSettings,
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


class CompactSavedTemplate:
    """Compact toolbox preview for a saved component abstraction.

    Keeps large multi-port saved components visually manageable in the
    bottom toolbox by clamping preview size and showing only compact side
    port markers instead of a full runtime-sized body.
    """

    def __init__(self, x, y, name, color, input_count, output_count):
        """Initialize the clamped preview body.

        Args:
            x (int): Top-left x in screen coordinates.
            y (int): Top-left y in screen coordinates.
            name (str): Saved component display name.
            color (tuple[int, int, int]): RGB body color.
            input_count (int): Number of exposed inputs.
            output_count (int): Number of exposed outputs.
        """
        max_ports = max(input_count, output_count, 1)
        dynamic_height = (
            (max_ports - 1) * ComponentSettings.SAVED_PORT_PITCH
            + 2 * ComponentSettings.SAVED_PORT_VERTICAL_PADDING
        )
        label_width = Fonts.component_label.size(name)[0] + 24
        width = min(
            max(ComponentSettings.DEFAULT_WIDTH, label_width),
            UISettings.BANK_TEMPLATE_MAX_WIDTH,
        )
        height = min(
            max(ComponentSettings.DEFAULT_HEIGHT, dynamic_height),
            UISettings.BANK_TEMPLATE_MAX_HEIGHT,
        )
        self.rect = pygame.Rect(x, y, width, height)
        self.name = name
        self.color = color
        self.input_count = input_count
        self.output_count = output_count
        label_width = self.rect.width - 2 * UISettings.BANK_TEMPLATE_LABEL_PADDING_X
        self._label_surf = self._fit_label_surface(self.name, label_width)
        # Preview templates are spawn handles only; they do not expose real
        # bank-hover ports for wiring.
        self.ports = ()

    @staticmethod
    def _truncate_to_width(text, font, max_width):
        """Return text shortened with ellipsis so it fits max_width.

        Args:
            text (str): Original label text.
            font (pygame.font.Font): Font used for width checks.
            max_width (int): Max rendered width in pixels.

        Returns:
            str: Original or truncated label text.
        """
        if font.size(text)[0] <= max_width:
            return text
        ellipsis = "..."
        if font.size(ellipsis)[0] > max_width:
            return ""
        for cut in range(len(text), -1, -1):
            candidate = f"{text[:cut].rstrip()}{ellipsis}"
            if font.size(candidate)[0] <= max_width:
                return candidate
        return ellipsis

    @staticmethod
    def _fit_label_surface(text, max_width):
        """Build a label surface that always fits inside the preview body.

        Tries progressively smaller font sizes first, then falls back to
        ellipsis truncation at the minimum size.

        Args:
            text (str): Label text.
            max_width (int): Max rendered width in pixels.

        Returns:
            pygame.Surface: Fitted text surface.
        """
        max_size = ComponentSettings.FONT_SIZE
        min_size = UISettings.BANK_TEMPLATE_LABEL_MIN_FONT_SIZE
        for size in range(max_size, min_size - 1, -1):
            font = pygame.font.Font(ComponentSettings.FONT, size)
            if font.size(text)[0] <= max_width:
                return font.render(text, True, (255, 255, 255))
        min_font = pygame.font.Font(ComponentSettings.FONT, min_size)
        truncated = CompactSavedTemplate._truncate_to_width(text, min_font, max_width)
        return min_font.render(truncated, True, (255, 255, 255))

    @staticmethod
    def _preview_y_positions(count, height):
        """Return evenly spaced preview marker y offsets.

        Args:
            count (int): Number of ports to represent.
            height (int): Preview body height in pixels.

        Returns:
            list[int]: Relative y positions inside the preview rect.
        """
        capped = min(count, UISettings.BANK_TEMPLATE_PREVIEW_MAX_PORTS_PER_SIDE)
        if capped <= 0:
            return []
        if capped == 1:
            return [height // 2]
        top = ComponentSettings.SAVED_PORT_VERTICAL_PADDING
        bottom = height - ComponentSettings.SAVED_PORT_VERTICAL_PADDING
        span = max(0, bottom - top)
        return [top + (span * idx) // (capped - 1) for idx in range(capped)]

    @staticmethod
    def _preview_port_radius(port_count, height):
        """Return a dynamic preview marker radius based on shown port density.

        Low-port components keep the normal port size; dense components
        shrink markers enough to avoid overlap inside the compact preview.

        Args:
            port_count (int): Number of ports on one side before capping.
            height (int): Preview body height in pixels.

        Returns:
            int: Marker radius in pixels.
        """
        base_radius = ComponentSettings.PORT_RADIUS
        shown = min(port_count, UISettings.BANK_TEMPLATE_PREVIEW_MAX_PORTS_PER_SIDE)
        if shown <= 1:
            return base_radius
        top = ComponentSettings.SAVED_PORT_VERTICAL_PADDING
        bottom = height - ComponentSettings.SAVED_PORT_VERTICAL_PADDING
        span = max(1, bottom - top)
        pitch = span / (shown - 1)
        clearance = 2
        max_radius_from_pitch = int((pitch - clearance) // 2)
        min_radius = UISettings.BANK_TEMPLATE_PREVIEW_PORT_RADIUS
        return max(min_radius, min(base_radius, max_radius_from_pitch))

    def draw(self, surface):
        """Draw compact saved-component preview body and side markers.

        Args:
            surface (pygame.Surface): The surface to draw onto.
        """
        pygame.draw.rect(surface, self.color, self.rect)
        pygame.draw.rect(
            surface,
            ComponentSettings.BORDER_COLOR,
            self.rect,
            ComponentSettings.BORDER_THICKNESS,
        )

        text_rect = self._label_surf.get_rect(center=self.rect.center)
        surface.blit(self._label_surf, text_rect)

        left_radius = self._preview_port_radius(self.input_count, self.rect.height)
        right_radius = self._preview_port_radius(self.output_count, self.rect.height)
        left_x = self.rect.left
        right_x = self.rect.right
        for rel_y in self._preview_y_positions(self.input_count, self.rect.height):
            pygame.draw.circle(
                surface,
                ComponentSettings.PORT_COLOR,
                (left_x, self.rect.top + rel_y),
                left_radius,
            )
        for rel_y in self._preview_y_positions(self.output_count, self.rect.height):
            pygame.draw.circle(
                surface,
                ComponentSettings.PORT_COLOR,
                (right_x, self.rect.top + rel_y),
                right_radius,
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

    # Order is the left-to-right order shown in the toolbox. Switch and
    # LED used to live here as draggable templates but were moved into
    # the > IN/OUT popup so the user can only spawn IN/OUT through that
    # control surface. Text + NAND are the fixed base templates.
    TEMPLATE_CLASSES = (Component,)

    def __init__(self, text_boxes, components_provider=None,
                 on_save_component=None, on_spawn_wall_component=None):
        """Build the bank rect, leftmost popup buttons, and template row.

        Args:
            text_boxes (TextBoxManager): Manager that owns workspace text
                boxes. Captured by the TEXT template's spawn closure so a
                click on that template can drop a focused TextBox without
                routing back through GameManager.
            components_provider (Callable[[], list] | None): Callback that
                returns the live workspace components list. Used by the
                > IN/OUT popup so spawning IN-1 / OUT-1 can append into the
                same list the rest of the workspace renders from.
            on_save_component (Callable[[], None] | None): Callback bound
                to the TOOLBOX > SAVE COMPONENT menu item. Triggers the
                save-as-component dialog flow on the GameManager side.
            on_spawn_wall_component (Callable[[Component], None] | None):
                Optional callback fired after the bank spawns a Switch or
                LED via the > IN/OUT popup. Lets GameManager record the
                new component in undo history, mirroring how template
                spawns are tracked there.
        """
        self.rect = UISettings.BANK_RECT
        self._text_boxes = text_boxes
        self._components_provider = components_provider or (lambda: [])
        self._on_save_component = on_save_component
        self._on_spawn_wall_component = on_spawn_wall_component
        # Two left-anchored popup buttons. TOOLBOX hosts the component
        # library actions; > IN/OUT spawns input switches / output LEDs.
        self._popup_buttons = self._build_popup_buttons()
        self._active_popup_button = None
        self._templates_and_spawners = self._build_templates()
        self._protected_template_ids = set()
        self._protected_template_order_ids = []
        self._refresh_protected_template_ids()
        self._reflow_templates()
        self._drag_template = None
        self._drag_template_mouse_anchor = (0, 0)
        self._drag_template_rect_anchor = (0, 0)

    def _refresh_protected_template_ids(self):
        """Track non-removable base templates by object id.

        Returns:
            None
        """
        self._protected_template_ids = {
            id(tpl) for tpl, _spawn in self._templates_and_spawners
        }
        self._protected_template_order_ids = [
            id(tpl) for tpl, _spawn in self._templates_and_spawners
        ]

    def reset_to_default_templates(self):
        """Reset the bank to base templates and drop saved-component entries.

        Returns:
            None
        """
        self._templates_and_spawners = self._build_templates()
        self._refresh_protected_template_ids()
        self._reflow_templates()
        self._drag_template = None
        self._active_popup_button = None

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

        Templates start to the right of the leftmost popup buttons so the
        bank reads as: [TOOLBOX] [> IN/OUT] | [TEXT] [NAND] [saved...].
        Each template is vertically centered inside the bank regardless of
        its own height, so a future smaller / larger component still looks
        intentional. Spacing comes from UISettings so the layout has no
        magic numbers. Each template is paired with a spawn_fn closure that
        knows how to clone it onto the workspace at a click position.

        Returns:
            list[tuple]: (template_drawable, spawn_fn) pairs in display order.
        """
        x = self._templates_start_x()
        entries = []
        text_tpl = TextTemplate(x, 0)
        text_tpl.rect.y = self.rect.y + (self.rect.height - text_tpl.rect.height) // 2
        entries.append((text_tpl, self._make_textbox_spawner()))
        x += text_tpl.rect.width + UISettings.BANK_TEMPLATE_GAP
        for cls in self.TEMPLATE_CLASSES:
            tpl = cls(x, 0)
            tpl.rect.y = self.rect.y + (self.rect.height - tpl.rect.height) // 2
            entries.append((tpl, self._make_component_spawner(tpl, cls)))
            x += tpl.rect.width + UISettings.BANK_TEMPLATE_GAP
        return entries

    def _reflow_templates(self):
        """Snap templates into bank slots with fixed base-template ordering.

        Protected base templates (TEXT, NAND) are pinned to the left side
        of the component strip and cannot be rearranged. Non-protected
        templates preserve their current relative x order and are laid out
        to the right.

        Returns:
            None
        """
        protected_map = {
            id(tpl): (tpl, spawn)
            for tpl, spawn in self._templates_and_spawners
            if id(tpl) in self._protected_template_ids
        }
        ordered = [
            protected_map[tpl_id]
            for tpl_id in self._protected_template_order_ids
            if tpl_id in protected_map
        ]
        movable = [
            entry for entry in self._templates_and_spawners
            if id(entry[0]) not in self._protected_template_ids
        ]
        movable.sort(key=lambda entry: entry[0].rect.x)
        ordered.extend(movable)

        x = self._templates_start_x()
        center_y = self.rect.y + self.rect.height // 2
        for tpl, _spawn in ordered:
            tpl.rect.x = x
            tpl.rect.centery = center_y
            x = tpl.rect.right + UISettings.BANK_TEMPLATE_GAP
        self._templates_and_spawners = ordered

    def _templates_start_x(self):
        """Return the x where the draggable template row begins.

        The row is pushed right by the width of the popup-button cluster
        plus a visual separator gap so the controls and templates read as
        two distinct groups inside the same bank.

        Returns:
            int: Screen x in pixels.
        """
        if not self._popup_buttons:
            return self.rect.x + UISettings.BANK_PADDING_X
        last_button = self._popup_buttons[-1]
        return last_button["rect"].right + UISettings.BANK_BUTTON_GROUP_GAP

    def _templates_left_bound_x(self):
        """Return the minimum x draggable templates are allowed to use.

        Returns:
            int: Left clamp bound in screen coordinates.
        """
        return self._templates_start_x()

    def _group_divider_x(self):
        """Return x coordinate of the visual divider between button groups.

        Returns:
            int: Divider x in screen coordinates.
        """
        if not self._popup_buttons:
            return self.rect.x + UISettings.BANK_PADDING_X
        last_button = self._popup_buttons[-1]
        gap = UISettings.BANK_BUTTON_GROUP_GAP
        return last_button["rect"].right + gap // 2

    def _draw_group_divider(self, surface):
        """Draw vertical divider between left controls and component strip.

        Args:
            surface (pygame.Surface): The surface to draw onto.
        """
        x = self._group_divider_x()
        top = self.rect.top + UISettings.BANK_GROUP_DIVIDER_INSET_Y
        bottom = self.rect.bottom - UISettings.BANK_GROUP_DIVIDER_INSET_Y
        pygame.draw.line(
            surface,
            UISettings.BANK_GROUP_DIVIDER_COLOR,
            (x, top),
            (x, bottom),
            UISettings.BANK_GROUP_DIVIDER_THICKNESS,
        )

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
        x = self._templates_start_x()
        if self._templates_and_spawners:
            last_tpl, _last_spawn = self._templates_and_spawners[-1]
            x = last_tpl.rect.right + UISettings.BANK_TEMPLATE_GAP
        input_count = len(definition["input_component_indices"])
        output_count = len(definition["output_component_indices"])
        template = CompactSavedTemplate(
            x,
            0,
            name,
            color,
            input_count,
            output_count,
        )
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
        self._reflow_templates()

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
        """Render the bank background, separator line, popup buttons, templates, and any open popup.

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
        self._draw_popup_buttons(surface)
        self._draw_group_divider(surface)
        for tpl, _spawn in self._templates_and_spawners:
            tpl.draw(surface)
        # Active popup is drawn last so it floats above the bank and any
        # template body that happens to fall under it.
        self._draw_active_popup(surface)

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
        min_x = self._templates_left_bound_x()
        template.rect.x = max(min_x, min(template.rect.x, self.rect.right - template.rect.width))
        template.rect.y = max(self.rect.top, min(template.rect.y, self.rect.bottom - template.rect.height))

    def _end_template_drag(self):
        """Finish drag and keep template draw/hit order aligned to x position."""
        self._drag_template = None
        self._reflow_templates()

    def handle_event(self, event, components_list):
        """Route bank events: popup buttons first, then templates.

        Popup buttons (TOOLBOX, > IN/OUT) and any open popup own the event
        ahead of template clicks so a click on a popup item never falls
        through to the template under it. Each template's spawn_fn owns
        the actual placement logic — see _make_component_spawner — so the
        template loop only finds the clicked template and delegates.

        Args:
            event (pygame.event.Event): The event to inspect.
            components_list (list[Component]): The workspace's component
                list, passed through to spawn_fn for component templates.

        Returns:
            bool: True if the bank consumed the event.
        """
        if self._handle_popup_event(event):
            return True

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == InputSettings.MIDDLE_CLICK:
            hit = self._template_at(event.pos)
            if hit is None:
                return False
            tpl, _spawn_fn = hit
            if id(tpl) in self._protected_template_ids:
                return True
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
            self._reflow_templates()
            return True

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == InputSettings.LEFT_CLICK:
            hit = self._template_at(event.pos)
            if hit is None:
                return False
            _tpl, spawn_fn = hit
            spawn_fn(event.pos, components_list)
            return True
        return False

    # -------------------------
    # POPUP BUTTONS (TOOLBOX, > IN/OUT)
    # -------------------------

    def _build_popup_buttons(self):
        """Build the leftmost popup-button cluster for the bottom bank.

        Each entry is a dict carrying the button rect, label surface, and
        the popup configuration (items + per-item enabled flag + dispatch
        callback). The TOOLBOX button hosts component-library actions
        (SAVE COMPONENT, LOAD COMPONENT). The > IN/OUT button hosts the
        IN-1 / OUT-1 spawners for wall components.

        Returns:
            list[dict]: Popup button records in left-to-right order.
        """
        font = Fonts.text_box
        cy = self.rect.y + (self.rect.height - BankPopupButtonSettings.HEIGHT) // 2
        x = self.rect.x + UISettings.BANK_PADDING_X
        buttons = []
        for spec in self._popup_button_specs():
            label_surf = font.render(
                spec["label"], True, BankPopupButtonSettings.LABEL_COLOR,
            )
            width = label_surf.get_width() + 2 * BankPopupButtonSettings.LABEL_PADDING_X
            rect = pygame.Rect(x, cy, width, BankPopupButtonSettings.HEIGHT)
            buttons.append({
                "id": spec["id"],
                "label": spec["label"],
                "label_surf": label_surf,
                "rect": rect,
                "popup_width": spec["popup_width"],
                "items": spec["items"],
            })
            x = rect.right + BankPopupButtonSettings.GAP_X
        return buttons

    def _popup_button_specs(self):
        """Build per-button popup item specs (label + enabled + handler).

        Items are described as (item_id, label, handler_or_None). A None
        handler renders as a disabled (greyed) item — used for
        LOAD COMPONENT, which is reserved for a future feature.

        Returns:
            list[dict]: One spec per button.
        """
        toolbox_handlers = {
            "save_component": self._on_save_component,
            "load_component": None,
        }
        toolbox_items = [
            (item_id, label, toolbox_handlers.get(item_id))
            for item_id, label in BankToolboxButtonSettings.ITEMS
        ]
        io_handlers = {
            "spawn_switch": self._spawn_switch_on_left_wall,
            "spawn_led": self._spawn_led_on_right_wall,
        }
        io_items = [
            (item_id, label, io_handlers.get(item_id))
            for item_id, label in BankIOButtonSettings.ITEMS
        ]
        return [
            {
                "id": "toolbox",
                "label": BankToolboxButtonSettings.LABEL,
                "popup_width": BankToolboxButtonSettings.POPUP_WIDTH,
                "items": toolbox_items,
            },
            {
                "id": "io",
                "label": BankIOButtonSettings.LABEL,
                "popup_width": BankIOButtonSettings.POPUP_WIDTH,
                "items": io_items,
            },
        ]

    def _popup_rect_for(self, button):
        """Return the popup rect for ``button`` floating above the bank.

        Args:
            button (dict): Popup button record from _build_popup_buttons.

        Returns:
            pygame.Rect: Popup rect in screen coordinates.
        """
        height = len(button["items"]) * BankPopupButtonSettings.ITEM_HEIGHT
        top = button["rect"].top - BankPopupButtonSettings.POPUP_GAP - height
        return pygame.Rect(button["rect"].left, top, button["popup_width"], height)

    def _popup_item_rects(self, popup_rect, item_count):
        """Return per-item rects stacked top-down inside ``popup_rect``.

        Args:
            popup_rect (pygame.Rect): The popup container rect.
            item_count (int): Number of items in the popup.

        Returns:
            list[pygame.Rect]: One rect per item.
        """
        return [
            pygame.Rect(
                popup_rect.left,
                popup_rect.top + index * BankPopupButtonSettings.ITEM_HEIGHT,
                popup_rect.width,
                BankPopupButtonSettings.ITEM_HEIGHT,
            )
            for index in range(item_count)
        ]

    def _draw_popup_buttons(self, surface):
        """Draw the cluster of popup buttons on the left side of the bank.

        Args:
            surface (pygame.Surface): The surface to draw onto.
        """
        mouse_pos = pygame.mouse.get_pos()
        for button in self._popup_buttons:
            rect = button["rect"]
            is_active = self._active_popup_button is button
            is_hover = rect.collidepoint(mouse_pos)
            body_color = (
                BankPopupButtonSettings.BODY_HOVER_COLOR
                if is_active or is_hover
                else BankPopupButtonSettings.BODY_COLOR
            )
            pygame.draw.rect(surface, body_color, rect)
            pygame.draw.rect(
                surface,
                BankPopupButtonSettings.BORDER_COLOR,
                rect,
                BankPopupButtonSettings.BORDER_THICKNESS,
            )
            label_rect = button["label_surf"].get_rect(center=rect.center)
            surface.blit(button["label_surf"], label_rect)

    def _draw_active_popup(self, surface):
        """Draw the popup belonging to the currently open popup button.

        Args:
            surface (pygame.Surface): The surface to draw onto.
        """
        button = self._active_popup_button
        if button is None:
            return
        font = Fonts.text_box
        popup_rect = self._popup_rect_for(button)
        pygame.draw.rect(surface, BankPopupButtonSettings.POPUP_BODY_COLOR, popup_rect)
        pygame.draw.rect(
            surface,
            BankPopupButtonSettings.POPUP_BORDER_COLOR,
            popup_rect,
            BankPopupButtonSettings.POPUP_BORDER_THICKNESS,
        )
        mouse_pos = pygame.mouse.get_pos()
        item_rects = self._popup_item_rects(popup_rect, len(button["items"]))
        for (item_id, label, handler), rect in zip(button["items"], item_rects):
            enabled = handler is not None
            hovered = enabled and rect.collidepoint(mouse_pos)
            if hovered:
                pygame.draw.rect(surface, BankPopupButtonSettings.ITEM_HOVER_BG, rect)
            text_color = (
                BankPopupButtonSettings.ITEM_HOVER_TEXT if hovered else
                BankPopupButtonSettings.ITEM_ENABLED_COLOR if enabled else
                BankPopupButtonSettings.ITEM_DISABLED_COLOR
            )
            label_surf = font.render(label, True, text_color)
            surface.blit(
                label_surf,
                (rect.left + BankPopupButtonSettings.ITEM_PADDING_X,
                 rect.y + (rect.height - label_surf.get_height()) // 2),
            )

    def _handle_popup_event(self, event):
        """Handle clicks on popup buttons and any open popup.

        Returns True if the event was consumed so the rest of handle_event
        won't double-process it. Click-outside-the-popup closes the popup
        without dispatching; click-on-disabled-item is a no-op.

        Args:
            event (pygame.event.Event): The event to inspect.

        Returns:
            bool: True if the bank's popup machinery consumed the event.
        """
        if event.type != pygame.MOUSEBUTTONDOWN or event.button != InputSettings.LEFT_CLICK:
            return False
        # If a popup is open, route the click to the popup first.
        if self._active_popup_button is not None:
            button = self._active_popup_button
            popup_rect = self._popup_rect_for(button)
            if popup_rect.collidepoint(event.pos):
                item_rects = self._popup_item_rects(popup_rect, len(button["items"]))
                for (item_id, label, handler), rect in zip(button["items"], item_rects):
                    if rect.collidepoint(event.pos) and handler is not None:
                        self._active_popup_button = None
                        handler()
                        return True
                return True  # consumed (clicked a disabled item or padding)
            # Click outside the popup closes it. Also consume the click if
            # it landed on the same toggle button so re-clicking it just
            # closes the popup without immediately reopening it below.
            if button["rect"].collidepoint(event.pos):
                self._active_popup_button = None
                return True
            self._active_popup_button = None
            # Fall through so the click can hit a different popup button
            # or template behind the just-closed popup.

        for button in self._popup_buttons:
            if button["rect"].collidepoint(event.pos):
                self._active_popup_button = button
                return True
        return False

    # -------------------------
    # IN/OUT SPAWN PLACEMENT
    # -------------------------

    def _spawn_switch_on_left_wall(self):
        """Spawn a Switch glued to the left wall at a non-overlapping y.

        First spawn lands centered vertically in the workspace band; later
        spawns step downward by SPAWN_VERTICAL_PITCH and skip past any
        existing same-wall component so they don't pile up at the same y.

        Returns:
            None
        """
        components_list = self._components_provider()
        new_comp = Switch(0, 0)
        new_comp.rect.y = self._next_wall_spawn_y(new_comp, "LEFT", components_list)
        new_comp._clamp_to_workspace()
        components_list.append(new_comp)
        if self._on_spawn_wall_component is not None:
            self._on_spawn_wall_component(new_comp)

    def _spawn_led_on_right_wall(self):
        """Spawn an LED glued to the right wall at a non-overlapping y.

        Returns:
            None
        """
        components_list = self._components_provider()
        new_comp = LED(0, 0)
        new_comp.rect.y = self._next_wall_spawn_y(new_comp, "RIGHT", components_list)
        new_comp._clamp_to_workspace()
        components_list.append(new_comp)
        if self._on_spawn_wall_component is not None:
            self._on_spawn_wall_component(new_comp)

    @staticmethod
    def _next_wall_spawn_y(new_comp, wall_side, components_list):
        """Pick a y for a freshly spawned wall component that avoids overlap.

        Starts at the workspace center and walks downward (then upward if
        needed) in SPAWN_VERTICAL_PITCH steps until it finds a y where the
        new component doesn't intersect any existing same-wall component.

        Args:
            new_comp (Component): The component about to be placed.
            wall_side (str): "LEFT" or "RIGHT".
            components_list (list): Live workspace components.

        Returns:
            int: Top-y in screen coordinates for the new component.
        """
        workspace_top = TopMenuBarSettings.HEIGHT
        workspace_bottom = UISettings.BANK_RECT.top
        center_y = (workspace_top + workspace_bottom - new_comp.rect.height) // 2
        same_wall = [
            c for c in components_list
            if getattr(c, "WALL_SIDE", None) == wall_side
        ]
        pitch = new_comp.rect.height + BankIOButtonSettings.SPAWN_VERTICAL_PITCH

        def fits(candidate_y):
            candidate = pygame.Rect(
                0, candidate_y, new_comp.rect.width, new_comp.rect.height,
            )
            return not any(candidate.colliderect(c.rect) for c in same_wall)

        # Walk downward then upward from center until a clear slot is found.
        for step in range(0, 200):
            for direction in (1, -1) if step else (1,):
                candidate_y = center_y + direction * step * pitch
                if candidate_y < workspace_top:
                    continue
                if candidate_y > workspace_bottom - new_comp.rect.height:
                    continue
                if fits(candidate_y):
                    return candidate_y
        # Fall back to center if every candidate slot collided (workspace
        # is wall-to-wall full); _clamp_to_workspace will at least keep it
        # on screen, and the wall-collision rule will still apply on drag.
        return center_y
