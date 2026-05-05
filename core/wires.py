import pygame
from typing import Callable

from .elements import Port
from settings import InputSettings, WireSettings


class Wire:
    """A committed connection from an OUTPUT port to an INPUT port.

    Endpoints are stored as Port references, never as cached coordinates, so
    the wire automatically follows whenever either parent component is
    dragged. Source is always the output side and target the input side; the
    WireManager normalizes orientation on commit.
    """

    def __init__(self, source, target, points=None):
        """
        Args:
            source (Port): The OUTPUT port that drives this wire.
            target (Port): The INPUT port that receives this wire.
            points (list[tuple[int, int]] | None): Optional intermediate
                bend points in screen coordinates.
        """
        self.source = source
        self.target = target
        self.points = list(points or [])

    def _polyline_points(self):
        """Return the full ordered point list for hit/draw operations.

        Returns:
            list[tuple[int, int]]: Source center, optional bend points,
                then target center.
        """
        return [self.source.center, *self.points, self.target.center]

    def hit(self, pos):
        """Return True if pos is within HIT_THRESHOLD pixels of the segment.

        Implements point-to-segment distance so a user clicking anywhere along
        the visible line can delete it, not just on its mathematical center.

        Args:
            pos (tuple[int, int]): The cursor position in screen coordinates.

        Returns:
            bool: True if the wire should be considered clicked.
        """
        px, py = pos
        hit_threshold_sq = WireSettings.HIT_THRESHOLD ** 2
        points = self._polyline_points()
        for start, end in zip(points, points[1:]):
            if self._distance_sq_to_segment((px, py), start, end) <= hit_threshold_sq:
                return True
        return False

    @staticmethod
    def _distance_sq_to_segment(pos, start, end):
        """Return squared distance from pos to segment start-end.

        Args:
            pos (tuple[int, int]): Point being tested.
            start (tuple[int, int]): Segment start.
            end (tuple[int, int]): Segment end.

        Returns:
            float: Squared distance from pos to the closest point on segment.
        """
        px, py = pos
        sx, sy = start
        tx, ty = end
        dx, dy = tx - sx, ty - sy
        seg_len_sq = dx * dx + dy * dy
        if seg_len_sq == 0:
            closest_x, closest_y = sx, sy
        else:
            t = ((px - sx) * dx + (py - sy) * dy) / seg_len_sq
            t = max(0.0, min(1.0, t))
            closest_x = sx + t * dx
            closest_y = sy + t * dy
        return (px - closest_x) ** 2 + (py - closest_y) ** 2

    def draw(self, surface):
        """Render the wire as a polyline between its two endpoint ports.

        Wire color tracks the source port's live state so a HIGH signal
        reads continuously from the output port, through the wire, into
        the receiving input port.

        Args:
            surface (pygame.Surface): The surface to draw onto.
        """
        color = WireSettings.LIVE_COLOR if self.source.live else WireSettings.COLOR
        points = self._polyline_points()
        if len(points) >= 2:
            pygame.draw.lines(surface, color, False, points, WireSettings.THICKNESS)


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
        # Intermediate bend points for the sticky in-flight wire.
        self.pending_points = []
        # Last-known cursor position so the ghost wire can extend to it
        # every frame even on frames without a fresh MOUSEMOTION.
        self.cursor_pos = (0, 0)
        # Optional callbacks set by GameManager to record undo/redo actions.
        # on_commit(wire, displaced_wire_or_None) - called after a wire is committed.
        # on_delete(wire) - called after a wire is right-click deleted.
        self.on_commit: Callable[[Wire, Wire | None], None] | None = None
        self.on_delete: Callable[[Wire], None] | None = None

    # -------------------------
    # EVENT HANDLING
    # -------------------------

    def handle_event(self, event, components, workspace_rect=None):
        """Try to consume a mouse event for wiring purposes.

        Args:
            event (pygame.event.Event): The event to inspect.
            components (list[Component]): Workspace components whose ports
                are valid wiring endpoints. Toolbox templates are excluded
                deliberately — wiring from a template makes no sense.
            workspace_rect (pygame.Rect | None): Optional workspace bounds.
                During a sticky wire draw, a left-click in this rect adds a
                bend point; left-clicks outside it cancel the in-flight wire.

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
                self.cursor_pos = event.pos
                hit = self._port_at(event.pos, components)

                if self.pending_source is None:
                    if hit is not None:
                        self.pending_source = hit
                        self.pending_points = []
                        return True
                    return False

                if hit is not None:
                    if self._is_valid(self.pending_source, hit):
                        new_wire, displaced = self._commit(
                            self.pending_source,
                            hit,
                            self.pending_points,
                        )
                        if self.on_commit:
                            self.on_commit(new_wire, displaced)
                        self._cancel_pending_wire()
                    return True

                if (workspace_rect is not None
                        and workspace_rect.collidepoint(event.pos)
                        and not self._component_at(event.pos, components)):
                    if not self.pending_points or self.pending_points[-1] != event.pos:
                        self.pending_points.append(event.pos)
                    return True

                self._cancel_pending_wire()
                return True
            elif event.button == InputSettings.RIGHT_CLICK:
                # Right-click during a drag cancels the in-flight wire,
                # otherwise it tries to delete a committed wire under
                # the cursor. Cancel takes precedence so a user mid-drag
                # never accidentally deletes an unrelated wire.
                if self.pending_source is not None:
                    self._cancel_pending_wire()
                    return True
                wire = self._wire_at(event.pos)
                if wire is not None:
                    self.wires.remove(wire)
                    if self.on_delete:
                        self.on_delete(wire)
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
            self._cancel_pending_wire()

    def clear_all(self):
        """Clear committed and in-flight wiring state.

        Returns:
            None
        """
        self.wires.clear()
        self._cancel_pending_wire()

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
            preview_points = [
                self.pending_source.center,
                *self.pending_points,
                self.cursor_pos,
            ]
            if len(preview_points) >= 2:
                pygame.draw.lines(
                    surface,
                    WireSettings.GHOST_COLOR,
                    False,
                    preview_points,
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

    @staticmethod
    def _component_at(pos, components):
        """Return the top-most component containing pos, or None.

        Args:
            pos (tuple[int, int]): Cursor position in screen coordinates.
            components (list[Component]): Workspace components to search.

        Returns:
            Component | None: Matching component body under the cursor.
        """
        for comp in reversed(components):
            if comp.rect.collidepoint(pos):
                return comp
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

    def _cancel_pending_wire(self):
        """Reset sticky wire state for the current in-flight wire."""
        self.pending_source = None
        self.pending_points = []

    def _commit(self, a, b, points=None):
        """Add a normalized Wire between a and b, replacing any prior input wire.

        Inputs may have at most one incoming connection, so any pre-existing
        wire on the same target input is dropped first. Source/target order
        is normalized so source.direction is always OUTPUT regardless of
        which port the user dragged from.

        Args:
            a (Port): One endpoint of the new connection.
            b (Port): The other endpoint of the new connection.
            points (list[tuple[int, int]] | None): Intermediate bend points
                captured while routing a sticky wire.

        Returns:
            tuple[Wire, Wire | None]: The newly committed wire and the wire
                it displaced (or None if the input was previously unconnected).
        """
        source = a if a.direction == Port.OUTPUT else b
        target = b if a.direction == Port.OUTPUT else a
        displaced = next((w for w in self.wires if w.target is target), None)
        self.wires = [w for w in self.wires if w.target is not target]
        new_wire = Wire(source, target, points=points)
        self.wires.append(new_wire)
        return new_wire, displaced
