"""Workspace interaction controller for selection, marquee, and group drag.

Keeps feature-specific interaction state and behavior out of GameManager so
GameManager can remain focused on orchestration.
"""

from __future__ import annotations

import pygame

from core.commands import DeleteComponent
from settings import InputSettings, SelectionBoxSettings


class WorkspaceInteractionController:
    """Own component selection, group drag, and marquee interactions.

    Args:
        components (list): Live workspace components list.
        wires: Wire manager used when deleting components.
        history: History manager used to record delete actions.
    """

    def __init__(self, components: list, wires, history) -> None:
        """Initialize interaction controller state.

        Args:
            components (list): Live workspace components.
            wires: Wire manager dependency.
            history: Undo/redo history dependency.
        """
        self._components = components
        self._wires = wires
        self._history = history

        self.selected_components: list = []
        self._marquee_start: tuple[int, int] | None = None
        self._marquee_end: tuple[int, int] | None = None
        self._group_drag_anchor: tuple[int, int] | None = None
        self._group_drag_start_positions: dict = {}
        self._group_drag_moved = False
        self._click_candidate_component = None
        self._click_started_on_bar = False

    def clear_interaction_state(self) -> None:
        """Reset selection and gesture state.

        Returns:
            None
        """
        self.set_selected_components([])
        self.cancel_marquee()
        self.cancel_group_drag()

    def update_port_hover(self, mouse_pos: tuple[int, int], bank_templates: list) -> None:
        """Refresh hovered flags for workspace and bank template ports.

        Also refreshes the wall drag-bar hover flag for Switch/LED so the
        bar lights up before the user grabs it.

        Args:
            mouse_pos (tuple[int, int]): Cursor position in screen space.
            bank_templates (list): Toolbox templates exposing ``ports``.

        Returns:
            None
        """
        for comp in self._components:
            for port in comp.ports:
                port.hovered = port.rect.collidepoint(mouse_pos)
            if hasattr(comp, "drag_bar_rect"):
                comp.bar_hovered = comp.drag_bar_rect.collidepoint(mouse_pos)
        for tpl in bank_templates:
            for port in tpl.ports:
                port.hovered = port.rect.collidepoint(mouse_pos)

    def component_at(self, pos: tuple[int, int]):
        """Return the top-most workspace component under ``pos``.

        Args:
            pos (tuple[int, int]): Cursor position in screen space.

        Returns:
            object | None: Top-most component under the cursor, else None.
        """
        for comp in reversed(self._components):
            if comp.rect.collidepoint(pos):
                return comp
        return None

    def set_selected_components(self, components: list) -> None:
        """Set active selection and synchronize component selected flags.

        Args:
            components (list): Components that should be selected.

        Returns:
            None
        """
        selected = [comp for comp in components if comp in self._components]
        selected_ids = set(selected)
        for comp in self._components:
            comp.selected = comp in selected_ids
        self.selected_components = selected

    def prune_selection(self) -> None:
        """Drop stale selections when undo/redo removed selected components.

        Returns:
            None
        """
        live = [comp for comp in self.selected_components if comp in self._components]
        if len(live) != len(self.selected_components):
            self.set_selected_components(live)

    def delete_component_at_index(self, index: int) -> None:
        """Delete one component and record undo history.

        Args:
            index (int): Index of component in the live components list.

        Returns:
            None
        """
        comp = self._components[index]
        affected_wires = [
            wire for wire in self._wires.wires
            if wire.source.parent is comp or wire.target.parent is comp
        ]
        self._wires.drop_wires_for_component(comp)
        self._components.pop(index)
        self._history.push(
            DeleteComponent(self._components, self._wires, comp, affected_wires, index)
        )
        if comp in self.selected_components:
            self.set_selected_components(
                [selected for selected in self.selected_components if selected is not comp]
            )

    def delete_selected_components(self) -> None:
        """Delete all selected components.

        Returns:
            None
        """
        if not self.selected_components:
            return
        selected_ids = set(self.selected_components)
        for index in range(len(self._components) - 1, -1, -1):
            if self._components[index] in selected_ids:
                self.delete_component_at_index(index)
        self.set_selected_components([])
        self.cancel_group_drag()
        self.cancel_marquee()

    def start_group_drag(self, mouse_pos: tuple[int, int], click_candidate) -> None:
        """Begin dragging the currently selected components.

        Args:
            mouse_pos (tuple[int, int]): Cursor position at drag start.
            click_candidate: Component that was directly clicked to start drag.

        Returns:
            None
        """
        if not self.selected_components:
            return
        self._group_drag_anchor = mouse_pos
        self._group_drag_start_positions = {
            comp: (comp.rect.x, comp.rect.y)
            for comp in self.selected_components
        }
        self._group_drag_moved = False
        self._click_candidate_component = click_candidate
        # If the user grabbed a wall component by its drag bar, suppress
        # the on-click action (Switch toggle) on release so dragging is
        # a clean gesture even when the cursor doesn't actually move.
        self._click_started_on_bar = bool(
            click_candidate is not None
            and hasattr(click_candidate, "drag_bar_rect")
            and click_candidate.drag_bar_rect.collidepoint(mouse_pos)
        )

    def cancel_group_drag(self) -> None:
        """Reset group-drag state.

        Returns:
            None
        """
        self._group_drag_anchor = None
        self._group_drag_start_positions = {}
        self._group_drag_moved = False
        self._click_candidate_component = None
        self._click_started_on_bar = False

    def is_group_drag_active(self) -> bool:
        """Return whether a group-drag gesture is in progress.

        Returns:
            bool: True when an active drag anchor exists.
        """
        return self._group_drag_anchor is not None

    def handle_group_drag_event(self, event: pygame.event.Event) -> bool:
        """Update or complete the current group-drag gesture.

        Args:
            event (pygame.event.Event): Mouse event to process.

        Returns:
            bool: True if the event was consumed by drag handling.
        """
        if self._group_drag_anchor is None:
            return False
        if event.type == pygame.MOUSEMOTION:
            dx = event.pos[0] - self._group_drag_anchor[0]
            dy = event.pos[1] - self._group_drag_anchor[1]
            if dx or dy:
                self._group_drag_moved = True
            for comp, (start_x, start_y) in self._group_drag_start_positions.items():
                comp.rect.x = start_x + dx
                comp.rect.y = start_y + dy
                comp._clamp_to_workspace()
            self._resolve_wall_collisions()
            return True
        if event.type == pygame.MOUSEBUTTONUP and event.button == InputSettings.LEFT_CLICK:
            if (
                not self._group_drag_moved
                and not self._click_started_on_bar
                and self._click_candidate_component is not None
                and len(self.selected_components) == 1
                and self.selected_components[0] is self._click_candidate_component
            ):
                self._click_candidate_component._on_click()
            self.cancel_group_drag()
            return True
        return False

    def _resolve_wall_collisions(self) -> None:
        """Block dragged wall components from passing through their siblings.

        Switches (left wall) and LEDs (right wall) are not allowed to
        overlap other same-wall components. After the per-frame clamp we
        compare each dragged wall component to every non-dragged same-wall
        component on the same side and snap the dragged one back to just
        before the obstacle if they overlap. This is what forces the user
        to rewire instead of dragging an IN/OUT past another one.

        Returns:
            None
        """
        dragged = set(self._group_drag_start_positions.keys())
        for comp, (_start_x, start_y) in self._group_drag_start_positions.items():
            wall = getattr(comp, "WALL_SIDE", None)
            if wall is None:
                continue
            moving_down = comp.rect.y >= start_y
            for other in self._components:
                if other is comp or other in dragged:
                    continue
                if getattr(other, "WALL_SIDE", None) != wall:
                    continue
                if not comp.rect.colliderect(other.rect):
                    continue
                # Snap back to just outside the obstacle on the side we
                # came from so a downward drag stops at the top of the
                # obstacle and an upward drag stops at its bottom.
                if moving_down:
                    comp.rect.y = other.rect.top - comp.rect.height
                else:
                    comp.rect.y = other.rect.bottom
            comp._clamp_to_workspace()

    def start_marquee(self, mouse_pos: tuple[int, int]) -> None:
        """Start a drag-to-select marquee.

        Args:
            mouse_pos (tuple[int, int]): Cursor position at marquee start.

        Returns:
            None
        """
        self._marquee_start = mouse_pos
        self._marquee_end = mouse_pos

    def cancel_marquee(self) -> None:
        """Reset marquee state.

        Returns:
            None
        """
        self._marquee_start = None
        self._marquee_end = None

    def is_marquee_active(self) -> bool:
        """Return whether a marquee gesture is in progress.

        Returns:
            bool: True when marquee has started.
        """
        return self._marquee_start is not None

    def handle_marquee_event(self, event: pygame.event.Event) -> bool:
        """Update or complete marquee selection gesture.

        Args:
            event (pygame.event.Event): Mouse event to process.

        Returns:
            bool: True if the event was consumed by marquee handling.
        """
        if self._marquee_start is None:
            return False
        if event.type == pygame.MOUSEMOTION:
            self._marquee_end = event.pos
            return True
        if event.type == pygame.MOUSEBUTTONUP and event.button == InputSettings.LEFT_CLICK:
            self._marquee_end = event.pos
            marquee = self._current_marquee_rect()
            if (
                marquee.width < SelectionBoxSettings.MIN_DRAG_PIXELS
                and marquee.height < SelectionBoxSettings.MIN_DRAG_PIXELS
            ):
                self.set_selected_components([])
                self.cancel_marquee()
                return True
            selected = [
                comp for comp in self._components
                if marquee.colliderect(comp.rect)
            ]
            self.set_selected_components(selected)
            self.cancel_marquee()
            return True
        return False

    def draw_selection_marquee(self, screen: pygame.Surface) -> None:
        """Draw active marquee rectangle.

        Args:
            screen (pygame.Surface): Surface to draw onto.

        Returns:
            None
        """
        if self._marquee_start is None:
            return
        rect = self._current_marquee_rect()
        if rect.width == 0 or rect.height == 0:
            return
        fill = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        fill.fill(SelectionBoxSettings.FILL_COLOR)
        screen.blit(fill, rect.topleft)
        pygame.draw.rect(
            screen,
            SelectionBoxSettings.BORDER_COLOR,
            rect,
            SelectionBoxSettings.BORDER_THICKNESS,
        )

    def _current_marquee_rect(self) -> pygame.Rect:
        """Build a normalized marquee rect from current drag endpoints.

        Returns:
            pygame.Rect: Normalized marquee rectangle.
        """
        if self._marquee_start is None or self._marquee_end is None:
            return pygame.Rect(0, 0, 0, 0)
        x0, y0 = self._marquee_start
        x1, y1 = self._marquee_end
        left = min(x0, x1)
        top = min(y0, y1)
        width = abs(x1 - x0)
        height = abs(y1 - y0)
        return pygame.Rect(left, top, width, height)
