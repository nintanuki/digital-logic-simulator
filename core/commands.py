"""Undo/redo command objects for the digital-logic simulator.

Every mutating workspace action (place/delete component, commit/delete wire,
spawn/delete text box) is recorded here so GameManager can reverse or
replay it.  The pattern:

  1. The mutation happens immediately in the normal event path.
  2. GameManager wraps it in a concrete Action and calls history.push().
  3. Ctrl+Z calls history.undo() → action.undo() reverses the mutation.
  4. Ctrl+Y calls history.redo() → action.do() re-applies it.

SaveAsComponent is intentionally NOT tracked: it clears the workspace,
which would require snapshotting the entire world.  The history is cleared
on every save-as-component so stale references can never surface.

Text content edits (keystrokes inside a TextBox) are NOT tracked individually
— only TextBox creation and deletion are undoable.  Granular keystroke undo
would require a separate inner undo stack per box and is deferred.
"""

from __future__ import annotations

from collections import deque
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .elements import Component
    from .wires import Wire, WireManager
    from ..ui.text_boxes import TextBox, TextBoxManager


# Maximum number of steps remembered.  Older entries are silently discarded
# when the deque is full so memory stays bounded.
_HISTORY_MAX = 100


# ---------------------------------------------------------------------------
# Base
# ---------------------------------------------------------------------------

class Action:
    """Abstract base for a reversible workspace mutation."""

    def do(self):
        """Re-apply the action (used by redo)."""

    def undo(self):
        """Reverse the action."""


# ---------------------------------------------------------------------------
# Component actions
# ---------------------------------------------------------------------------

class PlaceComponent(Action):
    """Records a component being added to the workspace.

    Undo removes it (and saves any wires that were attached so redo can
    restore them).  Redo re-inserts the component and its wires.
    """

    def __init__(self, components: list, wire_manager, component):
        self._components = components
        self._wm = wire_manager
        self._component = component
        # Populated on the first undo so redo can put them back.
        self._saved_wires: list = []

    def undo(self):
        # Capture wires attached to this component before dropping them.
        self._saved_wires = [
            w for w in self._wm.wires
            if w.source.parent is self._component
            or w.target.parent is self._component
        ]
        self._wm.drop_wires_for_component(self._component)
        if self._component in self._components:
            self._components.remove(self._component)

    def do(self):
        if self._component not in self._components:
            self._components.append(self._component)
        for wire in self._saved_wires:
            if wire not in self._wm.wires:
                self._wm.wires.append(wire)
        self._saved_wires = []


class DeleteComponent(Action):
    """Records a component being removed from the workspace.

    Undo re-inserts the component at its original stack index and restores
    the wires that were dropped alongside it.
    """

    def __init__(
        self,
        components: list,
        wire_manager,
        component,
        removed_wires: list,
        index: int,
    ):
        self._components = components
        self._wm = wire_manager
        self._component = component
        self._removed_wires = list(removed_wires)
        self._index = index

    def undo(self):
        # Re-insert at the original position (clamped so it's always valid).
        insert_at = min(self._index, len(self._components))
        self._components.insert(insert_at, self._component)
        for wire in self._removed_wires:
            if wire not in self._wm.wires:
                self._wm.wires.append(wire)

    def do(self):
        # Re-capture affected wires in case state shifted since last undo.
        self._removed_wires = [
            w for w in self._wm.wires
            if w.source.parent is self._component
            or w.target.parent is self._component
        ]
        self._wm.drop_wires_for_component(self._component)
        if self._component in self._components:
            self._index = self._components.index(self._component)
            self._components.remove(self._component)


# ---------------------------------------------------------------------------
# Wire actions
# ---------------------------------------------------------------------------

class PlaceWire(Action):
    """Records a wire being committed between two ports.

    If committing the wire displaced a pre-existing wire on the same input
    port, that displaced wire is saved so undo can restore it.
    """

    def __init__(self, wire_manager, wire, displaced_wire):
        self._wm = wire_manager
        self._wire = wire
        self._displaced = displaced_wire

    def undo(self):
        if self._wire in self._wm.wires:
            self._wm.wires.remove(self._wire)
        if self._displaced is not None and self._displaced not in self._wm.wires:
            self._wm.wires.append(self._displaced)

    def do(self):
        if self._displaced is not None and self._displaced in self._wm.wires:
            self._wm.wires.remove(self._displaced)
        if self._wire not in self._wm.wires:
            self._wm.wires.append(self._wire)


class DeleteWire(Action):
    """Records a wire being deleted by right-click."""

    def __init__(self, wire_manager, wire):
        self._wm = wire_manager
        self._wire = wire

    def undo(self):
        if self._wire not in self._wm.wires:
            self._wm.wires.append(self._wire)

    def do(self):
        if self._wire in self._wm.wires:
            self._wm.wires.remove(self._wire)


# ---------------------------------------------------------------------------
# Text-box actions
# ---------------------------------------------------------------------------

class PlaceTextBox(Action):
    """Records a text box being spawned on the workspace."""

    def __init__(self, text_box_manager, text_box):
        self._tbm = text_box_manager
        self._box = text_box

    def undo(self):
        if self._tbm.focused is self._box:
            self._tbm._blur()
        if self._box in self._tbm.text_boxes:
            self._tbm.text_boxes.remove(self._box)

    def do(self):
        if self._box not in self._tbm.text_boxes:
            self._tbm.text_boxes.append(self._box)
        self._tbm._focus(self._box)


class DeleteTextBox(Action):
    """Records a text box being deleted by right-click."""

    def __init__(self, text_box_manager, text_box, index: int):
        self._tbm = text_box_manager
        self._box = text_box
        self._index = index

    def undo(self):
        insert_at = min(self._index, len(self._tbm.text_boxes))
        self._tbm.text_boxes.insert(insert_at, self._box)

    def do(self):
        if self._box in self._tbm.text_boxes:
            self._index = self._tbm.text_boxes.index(self._box)
            if self._tbm.focused is self._box:
                self._tbm._blur()
            self._tbm.text_boxes.remove(self._box)


# ---------------------------------------------------------------------------
# History manager
# ---------------------------------------------------------------------------

class History:
    """Two-stack (undo / redo) history with a bounded undo depth."""

    def __init__(self):
        self._undo: deque[Action] = deque(maxlen=_HISTORY_MAX)
        self._redo: deque[Action] = deque()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def push(self, action: Action) -> None:
        """Record a completed action and clear the redo stack."""
        self._undo.append(action)
        self._redo.clear()

    def undo(self) -> None:
        """Reverse the most recent action, if any."""
        if not self._undo:
            return
        action = self._undo.pop()
        action.undo()
        self._redo.append(action)

    def redo(self) -> None:
        """Re-apply the most recently undone action, if any."""
        if not self._redo:
            return
        action = self._redo.pop()
        action.do()
        self._undo.append(action)

    def clear(self) -> None:
        """Discard all history (called when the workspace is cleared)."""
        self._undo.clear()
        self._redo.clear()
