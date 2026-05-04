import pygame

from fonts import Fonts

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

        # Draw the Name Label
        text_surf = Fonts.component_label.render(self.name, True, ColorSettings.WORD_COLORS["WHITE"])
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)

        # Hover labels last so they always sit on top of the body and border.
        for port in self.ports:
            port.draw_label(surface)

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
        size = SwitchSettings.SIZE
        # Body label "IN" because, from a student's circuit-building point
        # of view, this is an INPUT to the workspace. The class name
        # "Switch" describes what it is; the body label describes its role.
        super().__init__(x, y, width=size, height=size, name="IN")
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

    def _draw_body(self, surface):
        """Render the switch as a colored circle reflecting toggle state.

        Args:
            surface (pygame.Surface): The surface to draw onto.
        """
        body_color = SwitchSettings.ON_COLOR if self._state else SwitchSettings.OFF_COLOR
        center = self.rect.center
        radius = self.rect.width // 2
        pygame.draw.circle(surface, body_color, center, radius)
        pygame.draw.circle(
            surface,
            SwitchSettings.BORDER_COLOR,
            center,
            radius,
            SwitchSettings.BORDER_THICKNESS,
        )


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

    def _draw_body(self, surface):
        """Render the LED as a colored circle reflecting INPUT live state.

        Args:
            surface (pygame.Surface): The surface to draw onto.
        """
        body_color = (
            LedSettings.ON_COLOR if self.ports[0].live else LedSettings.OFF_COLOR
        )
        center = self.rect.center
        radius = self.rect.width // 2
        pygame.draw.circle(surface, body_color, center, radius)
        pygame.draw.circle(
            surface,
            LedSettings.BORDER_COLOR,
            center,
            radius,
            LedSettings.BORDER_THICKNESS,
        )


class SavedComponentStub(Component):
    """Pass-1 placeholder for a user-saved component.

    This is the visual/runtime stub used by Pass 1 step 2 so a freshly
    saved component can appear in the toolbox and be dropped into the
    workspace right away. It intentionally has no ports and no logic yet;
    Pass 1 step 3 will replace it with the working wrapped sub-circuit
    runtime model.
    """

    def __init__(self, x, y, name, color):
        """Create a rectangular component stub with a custom label/color.

        Args:
            x (int): Initial top-left x in screen coordinates.
            y (int): Initial top-left y in screen coordinates.
            name (str): Saved component display name.
            color (tuple[int, int, int]): RGB body color.
        """
        super().__init__(x, y, name=name)
        self.color = color
        # No exposed ports in the step-2 stub.
        self.ports = []

    def update_logic(self, output_buffer):
        """No-op: step-2 stubs have no ports and no simulation behavior.

        Args:
            output_buffer (dict[Port, bool]): Unused by this placeholder.
        """
        return
