import pygame

from elements import Port
from settings import InputSettings, WireSettings


class Wire:
    """A committed connection from an OUTPUT port to an INPUT port.

    Endpoints are stored as Port references, never as cached coordinates, so
    the wire automatically follows whenever either parent component is
    dragged. Source is always the output side and target the input side; the
    WireManager normalizes orientation on commit.
    """

    def __init__(self, source, target):
        """
        Args:
            source (Port): The OUTPUT port that drives this wire.
            target (Port): The INPUT port that receives this wire.
        """
        self.source = source
        self.target = target

    def hit(self, pos):
        """Return True if pos is within HIT_THRESHOLD pixels of the segment.

        Implements point-to-segment distance so a user clicking anywhere along
        the visible line can delete it, not just on its mathematical center.

        Args:
            pos (tuple[int, int]): The cursor position in screen coordinates.

        Returns:
            bool: True if the wire should be considered clicked.
        """
        sx, sy = self.source.center
        tx, ty = self.target.center
        px, py = pos
        dx, dy = tx - sx, ty - sy
        seg_len_sq = dx * dx + dy * dy
        if seg_len_sq == 0:
            # Degenerate (zero-length) wire, e.g. both endpoints overlap.
            closest_x, closest_y = sx, sy
        else:
            t = ((px - sx) * dx + (py - sy) * dy) / seg_len_sq
            t = max(0.0, min(1.0, t))
            closest_x = sx + t * dx
            closest_y = sy + t * dy
        dist_sq = (px - closest_x) ** 2 + (py - closest_y) ** 2
        return dist_sq <= WireSettings.HIT_THRESHOLD ** 2

    def draw(self, surface):
        """Render the wire as a straight line between its two endpoints.

        Wire color tracks the source port's live state so a HIGH signal
        reads continuously from the output port, through the wire, into
        the receiving input port.

        Args:
            surface (pygame.Surface): The surface to draw onto.
        """
        color = WireSettings.LIVE_COLOR if self.source.live else WireSettings.COLOR
        pygame.draw.line(
            surface,
            color,
            self.source.center,
            self.target.center,
            WireSettings.THICKNESS,
        )


class WireManager:
    """Owns every wire on the workspace plus the in-flight wire being drawn.

    Lifts the wiring state and validation off GameManager so the manager
    stays light per the project's architectural rules. GameManager forwards
    mouse events here before the bank/component handlers so a click on a
    port starts a wire instead of dragging the underlying component.
    """

    def __init__(self):
        # Committed wires currently on the workspace.
        self.wires = []
        # The OUTPUT/INPUT port the user grabbed when starting a wire, or
        # None when no drag is in flight. Used to draw the ghost line.
        self.pending_source = None
        # Last-known cursor position so the ghost wire can extend to it
        # every frame even on frames without a fresh MOUSEMOTION.
        self.cursor_pos = (0, 0)

    # -------------------------
    # EVENT HANDLING
    # -------------------------

    def handle_event(self, event, components):
        """Try to consume a mouse event for wiring purposes.

        Args:
            event (pygame.event.Event): The event to inspect.
            components (list[Component]): Workspace components whose ports
                are valid wiring endpoints. Toolbox templates are excluded
                deliberately — wiring from a template makes no sense.

        Returns:
            bool: True if the event was consumed and the caller should not
                forward it to the bank/components.
        """
        if event.type == pygame.MOUSEMOTION:
            # Always track the cursor so the ghost line follows it, but
            # never consume MOUSEMOTION — port hover and component drag
            # both need to see it too.
            self.cursor_pos = event.pos
            return False

        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == InputSettings.LEFT_CLICK:
                hit = self._port_at(event.pos, components)
                if hit is not None:
                    self.pending_source = hit
                    self.cursor_pos = event.pos
                    return True
            elif event.button == InputSettings.RIGHT_CLICK:
                # Right-click during a drag cancels the in-flight wire,
                # otherwise it tries to delete a committed wire under
                # the cursor. Cancel takes precedence so a user mid-drag
                # never accidentally deletes an unrelated wire.
                if self.pending_source is not None:
                    self.pending_source = None
                    return True
                wire = self._wire_at(event.pos)
                if wire is not None:
                    self.wires.remove(wire)
                    return True

        if event.type == pygame.MOUSEBUTTONUP:
            if event.button == InputSettings.LEFT_CLICK and self.pending_source is not None:
                target = self._port_at(event.pos, components)
                if target is not None and self._is_valid(self.pending_source, target):
                    self._commit(self.pending_source, target)
                # Whether or not the release landed on a valid port, the
                # drag is over. Releasing on empty space silently cancels
                # per the roadmap spec.
                self.pending_source = None
                return True

        return False

    # -------------------------
    # COMPONENT LIFECYCLE
    # -------------------------

    def drop_wires_for_component(self, component):
        """Remove every wire attached to the given component.

        Called by GameManager when a component is deleted so dangling wires
        don't keep referencing a port whose parent is gone.

        Args:
            component (Component): The component being removed.
        """
        self.wires = [
            w for w in self.wires
            if w.source.parent is not component and w.target.parent is not component
        ]
        # Also cancel an in-flight wire whose source belonged to the component.
        if self.pending_source is not None and self.pending_source.parent is component:
            self.pending_source = None

    # -------------------------
    # RENDER
    # -------------------------

    def draw(self, surface):
        """Render every committed wire plus the ghost line if a drag is in flight.

        Args:
            surface (pygame.Surface): The surface to draw onto.
        """
        for wire in self.wires:
            wire.draw(surface)
        if self.pending_source is not None:
            pygame.draw.line(
                surface,
                WireSettings.GHOST_COLOR,
                self.pending_source.center,
                self.cursor_pos,
                WireSettings.THICKNESS,
            )

    # -------------------------
    # INTERNAL HELPERS
    # -------------------------

    def _port_at(self, pos, components):
        """Return the first port whose hit-rect contains pos, or None.

        Args:
            pos (tuple[int, int]): Cursor position in screen coordinates.
            components (list[Component]): Workspace components to search.

        Returns:
            Port | None: The matching port, or None if pos hits no port.
        """
        for comp in components:
            for port in comp.ports:
                if port.rect.collidepoint(pos):
                    return port
        return None

    def _wire_at(self, pos):
        """Return the first committed wire under pos, or None.

        Args:
            pos (tuple[int, int]): Cursor position in screen coordinates.

        Returns:
            Wire | None: The matching wire, or None if pos hits no wire.
        """
        for wire in self.wires:
            if wire.hit(pos):
                return wire
        return None

    def _is_valid(self, a, b):
        """Decide whether a wire between two ports is allowed.

        Two ports must straddle the input/output divide (output-to-output
        and input-to-input are illegal) and must not belong to the same
        component (a gate cannot wire to itself, at least not directly).

        Args:
            a (Port): The port the user dragged from.
            b (Port): The port the user released on.

        Returns:
            bool: True if a wire can be committed between a and b.
        """
        if a.parent is b.parent:
            return False
        if a.direction == b.direction:
            return False
        return True

    def _commit(self, a, b):
        """Add a normalized Wire between a and b, replacing any prior input wire.

        Inputs may have at most one incoming connection, so any pre-existing
        wire on the same target input is dropped first. Source/target order
        is normalized so source.direction is always OUTPUT regardless of
        which port the user dragged from.

        Args:
            a (Port): One endpoint of the new connection.
            b (Port): The other endpoint of the new connection.
        """
        source = a if a.direction == Port.OUTPUT else b
        target = b if a.direction == Port.OUTPUT else a
        self.wires = [w for w in self.wires if w.target is not target]
        self.wires.append(Wire(source, target))
