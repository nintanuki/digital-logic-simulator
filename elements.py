import pygame

from settings import ColorSettings, ComponentSettings, InputSettings


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

        Args:
            surface (pygame.Surface): The surface to draw onto.
        """
        pygame.draw.circle(
            surface,
            ComponentSettings.PORT_COLOR,
            self.center,
            ComponentSettings.PORT_RADIUS,
        )


class Component:
    """A draggable circuit element (a NAND gate today, a saved sub-circuit later)."""

    def __init__(self, x, y, width=100, height=60, name="NAND"):
        """
        Args:
            x (int): Initial top-left x in screen coordinates.
            y (int): Initial top-left y in screen coordinates.
            width (int): Body width in pixels. Defaults to 100.
            height (int): Body height in pixels. Defaults to 60.
            name (str): Display label drawn on the body. Defaults to "NAND".
        """
        self.rect = pygame.Rect(x, y, width, height)
        self.color = ComponentSettings.COLOR
        self.name = name
        self.dragging = False
        self.offset_x = 0
        self.offset_y = 0

        # Initialize font for names
        pygame.font.init()
        self.font = pygame.font.Font(
            ComponentSettings.FONT,
            ComponentSettings.FONT_SIZE,
            )

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

    def draw(self, surface):
        """Render the component's ports, body, border, and name label.

        Args:
            surface (pygame.Surface): The surface to draw onto.
        """
        # Ports first so the body draws over the inner half of each circle,
        # giving the half-circle "stub" look that's already part of the design.
        for port in self.ports:
            port.draw(surface)

        # Draw the main body (The Rectangle)
        pygame.draw.rect(surface, self.color, self.rect)

        # Draw the border
        pygame.draw.rect(
            surface,
            ComponentSettings.BORDER_COLOR,
            self.rect,
            ComponentSettings.BORDER_THICKNESS
        )

        # Draw the Name Label
        text_surf = self.font.render(self.name, True, ColorSettings.WORD_COLORS["WHITE"])
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)

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
            elif event.button == InputSettings.RIGHT_CLICK:
                    return "DELETE"
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == InputSettings.LEFT_CLICK: self.dragging = False
        elif event.type == pygame.MOUSEMOTION:
            if self.dragging:
                self.rect.x = event.pos[0] + self.offset_x
                self.rect.y = event.pos[1] + self.offset_y
