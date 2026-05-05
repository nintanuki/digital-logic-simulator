import pygame
from copy import deepcopy

from ui.fonts import Fonts

from settings import (
    ColorSettings,
    ComponentSettings,
    InputSettings,
    LedSettings,
    ScreenSettings,
    SwitchSettings,
    UISettings,
)


class Port:
    """A single input or output point on a Component.

    Ports are owned by their parent Component and stored as offsets from the
    component's top-left corner, so when the Component is dragged the Ports
    follow without any extra bookkeeping. Ports are also the future hit
    targets for hover highlighting, wiring, and live-signal display.
    """

    # Direction constants. Strings rather than ints so debug output is readable.
    INPUT = "INPUT"
    OUTPUT = "OUTPUT"

    def __init__(self, parent, offset_x, offset_y, name, direction):
        """
        Args:
            parent (Component): The component this port belongs to.
            offset_x (int): X offset of the port center from parent.rect.x.
            offset_y (int): Y offset of the port center from parent.rect.y.
            name (str): Port label, e.g. "A", "B", "OUT".
            direction (str): Port.INPUT or Port.OUTPUT.
        """
        self.parent = parent
        self.offset_x = offset_x
        self.offset_y = offset_y
        self.name = name
        self.direction = direction
        # Set by GameManager on MOUSEMOTION via rect.collidepoint. Drives the
        # highlight color in draw() and (later) the hover label.
        self.hovered = False
        # Set by SignalManager each frame: True if this port is currently
        # carrying a HIGH signal. Drives the live fill color in draw() and
        # the live wire color in Wire.draw.
        self.live = False

    @property
    def center(self):
        """Absolute (x, y) center of the port in screen coordinates.

        Returns:
            tuple[int, int]: Recomputed each call so the port follows its
                parent Component as it is dragged.
        """
        return (self.parent.rect.x + self.offset_x,
                self.parent.rect.y + self.offset_y)

    @property
    def rect(self):
        """Square hit rect centered on the port, used for hover/click tests.

        Returns:
            pygame.Rect: A rect of side 2 * PORT_RADIUS centered on the port.
        """
        r = ComponentSettings.PORT_RADIUS
        cx, cy = self.center
        return pygame.Rect(cx - r, cy - r, r * 2, r * 2)

    def draw(self, surface):
        """Draw the port as a filled circle on the given surface.

        Hover takes precedence over live so the cursor always gets immediate
        feedback even if the port also happens to be HIGH.

        Args:
            surface (pygame.Surface): The surface to draw onto.
        """
        if self.hovered:
            color = ComponentSettings.PORT_HIGHLIGHT_COLOR
        elif self.live:
            color = ComponentSettings.PORT_LIVE_COLOR
        else:
            color = ComponentSettings.PORT_COLOR
        pygame.draw.circle(
            surface,
            color,
            self.center,
            ComponentSettings.PORT_RADIUS,
        )

    def draw_label(self, surface):
        """Render the port's name beside it, but only while hovered.

        Split out from draw() so Component.draw can render every label after
        the body and border, guaranteeing labels stay on top of the component
        regardless of port position. INPUT ports anchor their label to the
        left of the port; OUTPUT ports anchor to the right, so labels always
        point outward from the component body.

        Args:
            surface (pygame.Surface): The surface to draw onto.
        """
        if not self.hovered:
            return
        label_surf = Fonts.port_label.render(
            self.name, True, ComponentSettings.PORT_LABEL_COLOR,
        )
        label_rect = label_surf.get_rect()
        cx, cy = self.center
        offset = ComponentSettings.PORT_LABEL_OFFSET
        if self.direction == Port.INPUT:
            label_rect.midright = (cx - offset, cy)
        else:
            label_rect.midleft = (cx + offset, cy)
        surface.blit(label_surf, label_rect)


class Component:
    """A draggable circuit element (a NAND gate today, a saved sub-circuit later)."""

    def __init__(self, x, y, width=None, height=None, name="NAND"):
        """
        Args:
            x (int): Initial top-left x in screen coordinates.
            y (int): Initial top-left y in screen coordinates.
            width (int | None): Body width in pixels. Defaults to
                ComponentSettings.DEFAULT_WIDTH when omitted.
            height (int | None): Body height in pixels. Defaults to
                ComponentSettings.DEFAULT_HEIGHT when omitted.
            name (str): Display label drawn on the body. Defaults to "NAND".
        """
        if width is None:
            width = ComponentSettings.DEFAULT_WIDTH
        if height is None:
            height = ComponentSettings.DEFAULT_HEIGHT
        self.rect = pygame.Rect(x, y, width, height)
        self.color = ComponentSettings.COLOR
        self.name = name
        self.dragging = False
        self.offset_x = 0
        self.offset_y = 0
        self.selected = False
        # Tracks whether the cursor moved between MOUSEBUTTONDOWN and
        # MOUSEBUTTONUP. Used by handle_event to distinguish a stationary
        # click (which fires _on_click — useful for Switch) from a drag
        # (which never fires it). Reset on each fresh MOUSEBUTTONDOWN.
        self._moved_while_dragging = False

        # Two inputs on the left, one output on the right (NAND layout).
        self.ports = self._build_ports()

    def _build_ports(self):
        """Create the input and output ports in the default 2-in / 1-out layout.

        Returns:
            list[Port]: Inputs A and B on the left edge, output OUT on the right.
        """
        inset = ComponentSettings.INPUT_PORT_INSET
        return [
            Port(self, 0,                inset,                      "A",   Port.INPUT),
            Port(self, 0,                self.rect.height - inset,   "B",   Port.INPUT),
            Port(self, self.rect.width,  self.rect.height // 2,      "OUT", Port.OUTPUT),
        ]

    def update_logic(self, output_buffer):
        """Compute new OUTPUT port values from current INPUT port states.

        Default implementation is a 2-input NAND: the single OUTPUT port goes
        HIGH unless both INPUTs are HIGH. Subclasses with different gate
        logic (Switch) or no logic at all (LED) override this method.

        Writes go into output_buffer rather than directly to port.live so
        every component reads consistent inputs during the same frame —
        essential for feedback circuits like SR latches. SignalManager
        applies the buffer once every component has been read.

        Args:
            output_buffer (dict[Port, bool]): Map of OUTPUT port to its new
                value for this frame.
        """
        a, b, out = self.ports
        output_buffer[out] = not (a.live and b.live)

    def _on_click(self):
        """Hook fired when the user clicks the body without dragging.

        Default no-op so plain Components ignore body clicks. Switch
        overrides this to flip its toggle state.
        """
        pass

    def draw(self, surface):
        """Render the component's ports, body, border, and name label.

        Args:
            surface (pygame.Surface): The surface to draw onto.
        """
        # Ports first so the body draws over the inner half of each circle,
        # giving the half-circle "stub" look that's already part of the design.
        for port in self.ports:
            port.draw(surface)

        # Body shape is delegated so Switch / LED can render circles.
        self._draw_body(surface)

        if self.selected:
            highlight_rect = self.rect.inflate(8, 8)
            pygame.draw.rect(
                surface,
                ComponentSettings.SELECTION_COLOR,
                highlight_rect,
                ComponentSettings.SELECTION_BORDER_THICKNESS,
            )

        # Draw the Name Label
        text_surf = Fonts.component_label.render(self.name, True, ColorSettings.WORD_COLORS["WHITE"])
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)

    def _draw_body(self, surface):
        """Draw the rectangular body and border.

        Split out from draw() so Switch and LED can override with circle
        bodies while reusing the rest of draw() (ports, name label, hover
        labels).

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

    def handle_event(self, event):
        """Handle a single pygame event for this component (drag, delete).

        Args:
            event (pygame.event.Event): The event to process.

        Returns:
            str | None: "DELETE" if the user right-clicked to delete, else None.
        """
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == InputSettings.LEFT_CLICK and self.rect.collidepoint(event.pos):
                self.dragging = True
                # Capture where on the gate we clicked so it doesn't "snap" to top-left of the image
                self.offset_x = self.rect.x - event.pos[0]
                self.offset_y = self.rect.y - event.pos[1]
                # Reset the click-vs-drag tracker: this press is a click
                # until the cursor actually moves.
                self._moved_while_dragging = False
            elif event.button == InputSettings.RIGHT_CLICK and self.rect.collidepoint(event.pos):
                return "DELETE"
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == InputSettings.LEFT_CLICK:
                # If the press never produced motion, treat it as a click and
                # let subclasses react via _on_click (Switch toggles here).
                if self.dragging and not self._moved_while_dragging:
                    self._on_click()
                self.dragging = False
                self._moved_while_dragging = False
        elif event.type == pygame.MOUSEMOTION:
            if self.dragging:
                self.rect.x = event.pos[0] + self.offset_x
                self.rect.y = event.pos[1] + self.offset_y
                self._clamp_to_workspace()
                self._moved_while_dragging = True
        return None

    def _clamp_to_workspace(self):
        """Constrain self.rect to the visible playfield above the toolbox.

        The bottom edge of the workspace is the top of the toolbox bank, not
        the bottom of the screen, so a dragged component cannot disappear
        behind the toolbox or fall off any screen edge.
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


class Switch(Component):
    """A manual ON/OFF toggle that drives a single OUTPUT port.

    Clicking the body without dragging flips the toggle. Holding and moving
    drags the component as usual. Switches are how students inject signal
    into a circuit — they sit on the left and wire into a gate's inputs.
    """

    def __init__(self, x, y):
        """
        Args:
            x (int): Initial top-left x in screen coordinates.
            y (int): Initial top-left y in screen coordinates.
        """
        # Body label "IN" is retained on the object so serialization and any
        # future code that inspects the name still works, but Switch.draw()
        # does not render it at the body center — the toggle shape itself
        # communicates "input you control".
        super().__init__(
            x, y,
            width=SwitchSettings.WIDTH,
            height=SwitchSettings.HEIGHT,
            name="IN",
        )
        # Toggle state. Mirrored to the output port every frame by
        # update_logic so SignalManager can drive wires from it.
        self._state = False

    def _build_ports(self):
        """One OUTPUT port on the right edge, vertically centered.

        Returns:
            list[Port]: A single OUTPUT port named "OUT".
        """
        return [
            Port(self, self.rect.width, self.rect.height // 2, "OUT", Port.OUTPUT),
        ]

    def update_logic(self, output_buffer):
        """Drive the single OUTPUT port from the current toggle state.

        Args:
            output_buffer (dict[Port, bool]): Per-frame buffer for OUTPUT
                writes. See Component.update_logic for the contract.
        """
        output_buffer[self.ports[0]] = self._state

    def _on_click(self):
        """Flip the toggle state. Called when the user clicks without dragging."""
        self._state = not self._state

    def draw(self, surface):
        """Render ports, toggle body, and selection outline — no name label.

        The sliding-knob shape communicates the role clearly enough without
        a redundant text label at the center.

        Args:
            surface (pygame.Surface): The surface to draw onto.
        """
        for port in self.ports:
            port.draw(surface)
        self._draw_body(surface)
        if self.selected:
            highlight_rect = self.rect.inflate(8, 8)
            pygame.draw.rect(
                surface,
                ComponentSettings.SELECTION_COLOR,
                highlight_rect,
                ComponentSettings.SELECTION_BORDER_THICKNESS,
            )

    def _draw_body(self, surface):
        """Render the switch as a horizontal sliding toggle.

        Background rounded rectangle + recessed track + sliding knob.
        A state label ("1" or "0") is drawn on the empty side of the knob
        so the current value is always explicit.

        Args:
            surface (pygame.Surface): The surface to draw onto.
        """
        r = self.rect
        knob_r = SwitchSettings.KNOB_RADIUS
        margin = SwitchSettings.KNOB_MARGIN

        # Rounded-rectangle background
        body_color = (
            SwitchSettings.BODY_ON_COLOR if self._state
            else SwitchSettings.BODY_OFF_COLOR
        )
        pygame.draw.rect(
            surface, body_color, r,
            border_radius=SwitchSettings.BODY_CORNER,
        )
        pygame.draw.rect(
            surface, SwitchSettings.BORDER_COLOR, r,
            SwitchSettings.BORDER_THICKNESS,
            border_radius=SwitchSettings.BODY_CORNER,
        )

        # Recessed track (horizontal groove)
        th = SwitchSettings.TRACK_HEIGHT
        track_rect = pygame.Rect(
            r.x + margin + knob_r - 2,
            r.centery - th // 2,
            r.width - 2 * (margin + knob_r) + 4,
            th,
        )
        pygame.draw.rect(
            surface, SwitchSettings.TRACK_COLOR, track_rect,
            border_radius=th // 2,
        )

        # Sliding knob
        knob_cx = (
            r.right - margin - knob_r if self._state
            else r.x + margin + knob_r
        )
        knob_cy = r.centery
        knob_color = (
            SwitchSettings.KNOB_ON_COLOR if self._state
            else SwitchSettings.KNOB_OFF_COLOR
        )
        pygame.draw.circle(surface, knob_color, (knob_cx, knob_cy), knob_r)
        pygame.draw.circle(
            surface, SwitchSettings.BORDER_COLOR, (knob_cx, knob_cy), knob_r, 1,
        )

        # State label on the empty side of the knob
        if self._state:
            # Knob is on the right; label goes in the center of the left half
            label_text = "1"
            label_cx = r.x + (knob_cx - knob_r - r.x) // 2
        else:
            # Knob is on the left; label goes in the center of the right half
            label_text = "0"
            label_cx = (knob_cx + knob_r + r.right) // 2
        label_surf = Fonts.port_label.render(
            label_text, True, SwitchSettings.LABEL_COLOR,
        )
        label_rect = label_surf.get_rect(center=(label_cx, knob_cy))
        surface.blit(label_surf, label_rect)


class LED(Component):
    """A read-only output display whose body color reflects its INPUT port.

    LEDs are how students see the result of a circuit — they sit on the
    right and wire from a gate's output. No update_logic override: an LED
    has no outputs to compute.
    """

    def __init__(self, x, y):
        """
        Args:
            x (int): Initial top-left x in screen coordinates.
            y (int): Initial top-left y in screen coordinates.
        """
        size = LedSettings.SIZE
        # Body label "OUT" so students reading the workspace see the role,
        # not the implementation detail. See Switch for the parallel naming.
        super().__init__(x, y, width=size, height=size, name="OUT")

    def _build_ports(self):
        """One INPUT port on the left edge, vertically centered.

        Returns:
            list[Port]: A single INPUT port named "IN".
        """
        return [
            Port(self, 0, self.rect.height // 2, "IN", Port.INPUT),
        ]

    def update_logic(self, output_buffer):
        """No-op: an LED has no OUTPUT ports to update.

        Defined explicitly so the base class's NAND logic doesn't run on a
        component that has only one port.

        Args:
            output_buffer (dict[Port, bool]): Unused; LED reads its input
                visually in _draw_body and writes nothing here.
        """
        return

    def draw(self, surface):
        """Render ports, bulb body, and selection outline — no name label.

        The light-bulb silhouette communicates "output" clearly enough
        without a text label overlapping the globe.

        Args:
            surface (pygame.Surface): The surface to draw onto.
        """
        for port in self.ports:
            port.draw(surface)
        self._draw_body(surface)
        if self.selected:
            highlight_rect = self.rect.inflate(8, 8)
            pygame.draw.rect(
                surface,
                ComponentSettings.SELECTION_COLOR,
                highlight_rect,
                ComponentSettings.SELECTION_BORDER_THICKNESS,
            )

    def _draw_body(self, surface):
        """Render the LED as a light-bulb silhouette.

        A round globe (circle) sits in the upper part of the bounding rect;
        a small rectangular base/lead sits below it. When the input signal
        is HIGH a wider glow ring is drawn behind the globe.

        Args:
            surface (pygame.Surface): The surface to draw onto.
        """
        r = self.rect
        lit = self.ports[0].live

        bulb_cx = r.centerx
        bulb_cy = r.y + LedSettings.BULB_Y_OFFSET
        bulb_radius = LedSettings.BULB_RADIUS

        # Glow ring behind the globe when lit
        if lit:
            glow_r = bulb_radius + LedSettings.GLOW_EXTRA_RADIUS
            pygame.draw.circle(
                surface, LedSettings.GLOW_COLOR, (bulb_cx, bulb_cy), glow_r,
            )

        # Globe
        globe_color = (
            LedSettings.ON_GLOBE_COLOR if lit else LedSettings.OFF_GLOBE_COLOR
        )
        pygame.draw.circle(surface, globe_color, (bulb_cx, bulb_cy), bulb_radius)
        pygame.draw.circle(
            surface, LedSettings.BORDER_COLOR, (bulb_cx, bulb_cy),
            bulb_radius, LedSettings.BORDER_THICKNESS,
        )

        # Base / lead below the globe
        base_w = LedSettings.BASE_WIDTH
        base_h = LedSettings.BASE_HEIGHT
        base_rect = pygame.Rect(
            bulb_cx - base_w // 2,
            r.y + LedSettings.BASE_Y_OFFSET,
            base_w,
            base_h,
        )
        base_color = LedSettings.ON_BASE_COLOR if lit else LedSettings.OFF_BASE_COLOR
        pygame.draw.rect(
            surface, base_color, base_rect,
            border_radius=LedSettings.BASE_CORNER,
        )
        pygame.draw.rect(
            surface, LedSettings.BORDER_COLOR, base_rect, 1,
            border_radius=LedSettings.BASE_CORNER,
        )


class _InternalWire:
    """Minimal internal wire used by SavedComponent's hidden simulation.

    Kept local to this module so SavedComponent can run a private
    sub-circuit without importing the draw-oriented `Wire` class from
    wires.py (which would create a circular import).
    """

    def __init__(self, source, target):
        """Store source/target internal Port references.

        Args:
            source (Port): Internal OUTPUT port.
            target (Port): Internal INPUT port.
        """
        self.source = source
        self.target = target


class SavedComponent(Component):
    """A wrapped sub-circuit that exposes only inferred external ports.

    Runtime model for Pass 1 step 3: each instance owns a hidden clone of
    the saved sub-circuit (components + wires), then maps wrapper INPUT
    ports into the sub-circuit's saved input switches and maps saved output
    LEDs back out through wrapper OUTPUT ports.
    """

    def __init__(self, x, y, name, color, definition):
        """Create a wrapped saved component from a serialized definition.

        Args:
            x (int): Initial top-left x in screen coordinates.
            y (int): Initial top-left y in screen coordinates.
            name (str): Display name shown on the wrapper body.
            color (tuple[int, int, int]): RGB body color.
            definition (dict): Serialized sub-circuit definition.
        """
        self.definition = deepcopy(definition)
        self._input_count = len(self.definition["input_component_indices"])
        self._output_count = len(self.definition["output_component_indices"])
        width, height = self._compute_body_size(name)
        super().__init__(x, y, width=width, height=height, name=name)
        self.color = color
        self._inner_components = []
        self._inner_wires = []
        self._inner_input_switches = []
        self._inner_output_leds = []
        self._build_internal_runtime()

    def _compute_body_size(self, name):
        """Compute wrapper body size from port count and label width.

        Args:
            name (str): Wrapper label text.

        Returns:
            tuple[int, int]: (width, height) in pixels.
        """
        max_ports = max(self._input_count, self._output_count, 1)
        dynamic_height = (
            (max_ports - 1) * ComponentSettings.SAVED_PORT_PITCH
            + 2 * ComponentSettings.SAVED_PORT_VERTICAL_PADDING
        )
        height = max(ComponentSettings.DEFAULT_HEIGHT, dynamic_height)
        label_width = Fonts.component_label.size(name)[0]
        width = max(ComponentSettings.DEFAULT_WIDTH, label_width + 24)
        return width, height

    def _build_ports(self):
        """Build wrapper-side ports from saved input/output counts.

        Returns:
            list[Port]: INPUT ports first, then OUTPUT ports.
        """
        ports = []
        for index, y in enumerate(self._port_y_offsets(self._input_count)):
            ports.append(Port(self, 0, y, chr(65 + index), Port.INPUT))
        for index, y in enumerate(self._port_y_offsets(self._output_count)):
            name = "OUT" if index == 0 else f"OUT{index}"
            ports.append(Port(self, self.rect.width, y, name, Port.OUTPUT))
        return ports

    def _port_y_offsets(self, count):
        """Return evenly spaced y offsets for `count` ports.

        Args:
            count (int): Number of ports on one side.

        Returns:
            list[int]: Port-center y offsets inside this component rect.
        """
        if count <= 0:
            return []
        if count == 1:
            return [self.rect.height // 2]
        top = ComponentSettings.SAVED_PORT_VERTICAL_PADDING
        bottom = self.rect.height - ComponentSettings.SAVED_PORT_VERTICAL_PADDING
        span = bottom - top
        return [top + (span * idx) // (count - 1) for idx in range(count)]

    def _build_internal_runtime(self):
        """Instantiate hidden internal components/wires from definition."""
        for comp_def in self.definition["components"]:
            self._inner_components.append(self._instantiate_component(comp_def))

        for wire_def in self.definition["wires"]:
            source_comp = self._inner_components[wire_def["source_component_index"]]
            target_comp = self._inner_components[wire_def["target_component_index"]]
            source_port = source_comp.ports[wire_def["source_port_index"]]
            target_port = target_comp.ports[wire_def["target_port_index"]]
            self._inner_wires.append(_InternalWire(source_port, target_port))

        self._inner_input_switches = [
            self._inner_components[index]
            for index in self.definition["input_component_indices"]
        ]
        self._inner_output_leds = [
            self._inner_components[index]
            for index in self.definition["output_component_indices"]
        ]

    def _instantiate_component(self, comp_def):
        """Build one internal component instance from its serialized record.

        Args:
            comp_def (dict): One serialized component record.

        Returns:
            Component: Fresh internal component instance.
        """
        comp_type = comp_def["type"]
        if comp_type == "switch":
            comp = Switch(comp_def["x"], comp_def["y"])
            comp._state = comp_def.get("state", False)
            return comp
        if comp_type == "led":
            return LED(comp_def["x"], comp_def["y"])
        if comp_type == "saved_component":
            return SavedComponent(
                comp_def["x"],
                comp_def["y"],
                comp_def["name"],
                tuple(comp_def["color"]),
                comp_def["definition"],
            )
        return Component(comp_def["x"], comp_def["y"])

    def _input_ports(self):
        """Return wrapper INPUT ports in saved-order mapping.

        Returns:
            list[Port]: External INPUT ports.
        """
        return self.ports[:self._input_count]

    def _output_ports(self):
        """Return wrapper OUTPUT ports in saved-order mapping.

        Returns:
            list[Port]: External OUTPUT ports.
        """
        return self.ports[self._input_count:]

    def update_logic(self, output_buffer):
        """Advance hidden sub-circuit and publish wrapper output values.

        Args:
            output_buffer (dict[Port, bool]): Parent simulation output map.
        """
        for ext_port, switch in zip(self._input_ports(), self._inner_input_switches):
            switch._state = ext_port.live

        # Run several internal passes so deep combinational chains and
        # feedback-heavy sub-circuits settle before exporting wrapper outputs.
        settle_steps = max(1, len(self._inner_components))
        for _ in range(settle_steps):
            internal_output_buffer = {}
            for comp in self._inner_components:
                comp.update_logic(internal_output_buffer)

            for port, value in internal_output_buffer.items():
                port.live = value

            for comp in self._inner_components:
                for port in comp.ports:
                    if port.direction == Port.INPUT:
                        port.live = False
            for wire in self._inner_wires:
                wire.target.live = wire.source.live

        for ext_port, led in zip(self._output_ports(), self._inner_output_leds):
            output_buffer[ext_port] = led.ports[0].live
