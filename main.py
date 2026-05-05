from __future__ import annotations

import pygame
import sys
from copy import deepcopy
import random

from elements import Component, LED, SavedComponent, Switch
from fonts import Fonts
from save_component_dialog import SaveComponentDialog
from settings import *
from signals import SignalManager
from text_boxes import TextBoxManager
from ui import ComponentBank
from crt import CRT
from wires import WireManager
from commands import (
    History,
    PlaceComponent, DeleteComponent,
    PlaceWire, DeleteWire,
    PlaceTextBox, DeleteTextBox,
)


class GameManager:
    def __init__(self):
        # -------- Pygame core --------
        pygame.init()
        # Load every shared Font once, before any object that calls .render().
        # ComponentBank instantiates a template Component below, so this must
        # come before the bank is built.
        Fonts.init()

        # -------- Display --------
        self.screen = pygame.display.set_mode(ScreenSettings.RESOLUTION)
        pygame.display.set_caption(ScreenSettings.TITLE)
        self.clock = pygame.time.Clock()
        self.crt = CRT(self.screen)

        # -------- Subsystems --------

        # -------- Managers --------

        # -------- Sprite groups --------
        # Text boxes are pure annotations — no signal, no ports. Built
        # before the bank so the TEXT template can capture this manager
        # in its spawn closure. Spawnable from the bank's TEXT template
        # and from the T keyboard shortcut at the cursor position.
        self.text_boxes = TextBoxManager()
        # Active modal dialog, or None when no dialog is open. Currently
        # only set by `save_as_component` (the SAVE AS COMPONENT popup
        # action); future dialogs (e.g. confirm-quit in Pass 2, project
        # main menu in Pass 3) will reuse this slot via the same
        # "active UI layer claims its events first" pattern. Initialized
        # before `bank` because `save_as_component` is bound into the
        # bank's menu_actions and would dereference `self.dialog` if a
        # click-through somehow fired before the next event loop tick.
        self.dialog = None
        # Saved component records produced by the SAVE AS COMPONENT
        # dialog. Pass 1 step 1 stub: each entry is a dict snapshotting
        # the user's dialog inputs. Pass 1 steps 2 (toolbox template)
        # and 3 (spawn-as-working-component) will replace this list
        # with the live (template_drawable, spawn_fn) pairs the bank
        # consumes. In-session only by design — disk persistence is
        # Pass 3.
        self.saved_components = []
        # Menu actions: QUIT (close_game) and SAVE AS COMPONENT
        # (open the rough Pass-1 dialog) are the two enabled items.
        # The other three (NEW PROJECT, LOAD PROJECT, SAVE PROJECT)
        # ship disabled until disk persistence lands in Pass 3. The
        # dict's keys mirror MenuButtonSettings.ITEM_LABELS exactly so
        # MenuButton can pre-render each label in the right color.
        self.bank = ComponentBank(
            self.text_boxes,
            menu_actions={
                "SAVE AS COMPONENT": self.save_as_component,
                "QUIT": self.close_game,
            },
        )
        self.components = [] # Start with an empty workspace. Components will be added by the user.
        self.wires = WireManager()
        self.signals = SignalManager()
        self.selected_components = []
        self._marquee_start = None
        self._marquee_end = None
        self._group_drag_anchor = None
        self._group_drag_start_positions = {}
        self._group_drag_moved = False
        self._click_candidate_component = None

        # -------- Undo / redo --------
        self.history = History()
        # Wire up mutation callbacks so every reversible action is recorded.
        # Lambdas stay here (not in the subsystems) so the command objects
        # can hold references to self.components / self.wires / self.text_boxes
        # without coupling those modules to commands.py.
        self.wires.on_commit = (
            lambda wire, displaced: self.history.push(PlaceWire(self.wires, wire, displaced))
        )
        self.wires.on_delete = (
            lambda wire: self.history.push(DeleteWire(self.wires, wire))
        )
        self.text_boxes.on_spawn = (
            lambda box: self.history.push(PlaceTextBox(self.text_boxes, box))
        )
        self.text_boxes.on_delete = (
            lambda box, idx: self.history.push(DeleteTextBox(self.text_boxes, box, idx))
        )
        # Pre-render static hotkey hint text once; blit each frame.
        self._hotkey_hint_surfs = self._build_hotkey_bar_text_surfaces()

    # -------------------------
    # BOOT / LIFECYCLE
    # -------------------------

    def close_game(self):
        pygame.quit()
        sys.exit()

    # -------------------------
    # GAMEPLAY ACTIONS
    # -------------------------

    def save_as_component(self):
        """Open the SAVE AS COMPONENT dialog.

        Bound into the bottom-left popup's menu_actions for the SAVE AS
        COMPONENT label. The dialog itself only collects the name; the
        workspace snapshot (switches → INPUTs, LEDs → OUTPUTs, both
        ordered by Y) happens here in `_finalize_save_as_component` at
        Save time. Reading the workspace at finalize is safe because
        the dialog is modal — events that could mutate `self.components`
        are blocked while the dialog is open.
        """
        self.dialog = SaveComponentDialog(
            on_save=self._finalize_save_as_component,
            on_cancel=self._dismiss_dialog,
        )

    def _finalize_save_as_component(self, name):
        """Auto-infer ports from the workspace, stash the record, dismiss.

        Per the "Save-as-Component port inference rule" in TODO Risks &
        Notes: every Switch in the workspace becomes an INPUT port and
        every LED becomes an OUTPUT port; ordering is ascending Y so
        the top-of-screen IN is port 0, the next one down is port 1,
        and so on. Y was picked over component-creation-order because
        the visual top-to-bottom column is what the student actually
        sees — picking the order from something invisible would break
        the spatial intuition.

        Pass 1 step 1 (v2) keeps this stub minimal: capture the
        inferred record and dismiss. Pass 1 step 2 (toolbox template)
        will consume `saved_components` to materialize each record as
        a clickable bank template, and step 3 (spawn-as-working-
        component) will turn that template into a usable sub-circuit.

        Args:
            name (str): Saved component's display name (uppercase,
                already trimmed by the dialog).
        """
        # `sorted(...)` returns a fresh list; the workspace's own
        # `self.components` ordering is left alone so the user's
        # bottom-of-stack drag/draw priority isn't disturbed.
        input_switches = sorted(
            (c for c in self.components if isinstance(c, Switch)),
            key=lambda s: s.rect.y,
        )
        output_leds = sorted(
            (c for c in self.components if isinstance(c, LED)),
            key=lambda l: l.rect.y,
        )
        definition = self._snapshot_workspace_definition(
            input_switches,
            output_leds,
        )
        record = {
            "name": name,
            "color": random.choice(ColorSettings.SAVED_COMPONENT_COLORS),
            "inputs": input_switches,
            "outputs": output_leds,
            "definition": definition,
        }
        self.saved_components.append(record)
        self.bank.add_saved_component_template(
            name,
            record["color"],
            deepcopy(definition),
        )
        self._clear_workspace()
        self._dismiss_dialog()

    def _clear_workspace(self):
        """Reset the live workspace to an empty canvas.

        Clears placed components, committed/pending wires, and text-box
        annotations. Used after Save-as-Component so the student can start
        the next abstraction layer immediately.
        """
        self.components.clear()
        self.wires.wires.clear()
        self.wires.pending_source = None
        self.text_boxes.text_boxes.clear()
        self.text_boxes.focused = None
        self._set_selected_components([])
        self._cancel_marquee()
        self._cancel_group_drag()
        # History holds references to the old components and wires.  Clear
        # it so undo can't resurrect objects from the previous workspace.
        self.history.clear()

    def _snapshot_workspace_definition(self, input_switches, output_leds):
        """Serialize the current workspace into a saved-component definition.

        Args:
            input_switches (list[Switch]): Switches selected as external inputs.
            output_leds (list[LED]): LEDs selected as external outputs.

        Returns:
            dict: Serialized sub-circuit payload for SavedComponent runtime.
        """
        component_indices = {
            comp: idx for idx, comp in enumerate(self.components)
        }
        component_defs = [
            self._serialize_component(comp) for comp in self.components
        ]
        wire_defs = []
        for wire in self.wires.wires:
            source_parent = wire.source.parent
            target_parent = wire.target.parent
            if source_parent not in component_indices:
                continue
            if target_parent not in component_indices:
                continue
            wire_defs.append({
                "source_component_index": component_indices[source_parent],
                "source_port_index": source_parent.ports.index(wire.source),
                "target_component_index": component_indices[target_parent],
                "target_port_index": target_parent.ports.index(wire.target),
            })
        return {
            "components": component_defs,
            "wires": wire_defs,
            "input_component_indices": [
                component_indices[switch]
                for switch in input_switches
                if switch in component_indices
            ],
            "output_component_indices": [
                component_indices[led]
                for led in output_leds
                if led in component_indices
            ],
        }

    @staticmethod
    def _serialize_component(comp):
        """Serialize one workspace component into a definition record.

        Args:
            comp (Component): Component instance to serialize.

        Returns:
            dict: Serialized component payload.
        """
        if isinstance(comp, Switch):
            return {
                "type": "switch",
                "x": comp.rect.x,
                "y": comp.rect.y,
                "state": comp._state,
            }
        if isinstance(comp, LED):
            return {
                "type": "led",
                "x": comp.rect.x,
                "y": comp.rect.y,
            }
        if isinstance(comp, SavedComponent):
            return {
                "type": "saved_component",
                "x": comp.rect.x,
                "y": comp.rect.y,
                "name": comp.name,
                "color": list(comp.color),
                "definition": deepcopy(comp.definition),
            }
        return {
            "type": "nand",
            "x": comp.rect.x,
            "y": comp.rect.y,
        }

    def _dismiss_dialog(self):
        """Close whichever dialog is currently open.

        Reaching this with `self.dialog is None` should not happen in
        practice — both Cancel and Esc paths inside the dialog go
        through here, and a no-op is the right safe default if a
        future caller somehow double-dismisses.
        """
        self.dialog = None

    # -------------------------
    # AUDIO / VOLUME ACTIONS
    # -------------------------

    # -------------------------
    # EVENT HANDLING
    # -------------------------

    def _process_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.close_game()
                continue

            # While a modal dialog is open it owns every event — the
            # workspace beneath is paused. Sits ahead of text_boxes so
            # a click that happens to land on a text box under the
            # dimmed backdrop edits the dialog, not the box. The dialog
            # itself routes Save / Cancel / Esc back through callbacks
            # that null out `self.dialog`, so the next event loop tick
            # falls through here normally.
            if self.dialog is not None:
                self.dialog.handle_event(event)
                continue

            # Text boxes get every event first: keystrokes while a box is
            # focused belong to the box (so typing 'n' types 'n' instead of
            # spawning a NAND), and clicks on a text box should edit it
            # rather than starting a wire on a port that happens to sit
            # underneath. The manager only consumes events it actually
            # uses, so empty-space clicks fall through to wires/components.
            if self.text_boxes.handle_event(event):
                continue

            # Route logic to specialized handlers
            if event.type == pygame.KEYDOWN:
                self._handle_keydown(event)
            elif event.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, pygame.MOUSEMOTION):
                self._handle_mouse(event)

    def _handle_keydown(self, event: pygame.event.Event) -> None:
        """Route a single keyboard press."""
        self._prune_selection()
        # Undo / redo - checked before any other key so Ctrl+Z/Y are never
        # intercepted by a focused text box (the manager consumes keydowns
        # while a box is focused, so these lines are only reached when no
        # box is active).
        mods = pygame.key.get_mods()
        if event.key == pygame.K_z and (mods & pygame.KMOD_CTRL):
            if mods & pygame.KMOD_SHIFT:
                self.history.redo()
            else:
                self.history.undo()
            return
        if event.key == pygame.K_y and (mods & pygame.KMOD_CTRL):
            self.history.redo()
            return

        if event.key in (pygame.K_DELETE, pygame.K_BACKSPACE):
            self._delete_selected_components()
            return

        # Global keys (always honored regardless of run state).
        if event.key == pygame.K_F11:
            pygame.display.toggle_fullscreen()
        if event.key == pygame.K_ESCAPE:
            # Esc dismisses the bottom-left popup if it's open before it
            # ever counts as a quit. Mirrors the text-box manager pattern
            # (Esc unfocuses an active editor) so Esc never leaks through
            # an open UI layer to kill the game. Future popups / dialogs
            # should add their dismiss check here, in priority order.
            if self.bank.menu_button.is_open:
                self.bank.menu_button.toggle()
                return
            self.close_game()
        # T spawns an annotation text box at the current cursor position
        # and immediately focuses it so the user can start typing. Only
        # reachable when no text box is already focused (the manager
        # consumes KEYDOWNs in that case so the 't' types instead).
        if event.key == pygame.K_t:
            self.text_boxes.spawn_at(pygame.mouse.get_pos())

    def _handle_mouse(self, event: pygame.event.Event) -> None:
        """Pass mouse events to the component manager or components directly."""
        self._prune_selection()
        # Hover updates ride along with motion events. Done here (not inside
        # Component) because every port in the world — workspace and toolbox
        # template alike — needs to reflect the same cursor, and only
        # GameManager owns both collections.
        if event.type == pygame.MOUSEMOTION:
            self._update_port_hover(event.pos)

        if self._is_group_dragging():
            self._handle_group_drag_event(event)
            return

        if self._is_marquee_selecting():
            self._handle_marquee_event(event)
            return

        # When the bottom-left popup menu is open, any mouse-button press
        # that lands on the popup body belongs to the popup — intercept it
        # before wires/components can react so a port that happens to sit
        # under the popup can't start a wire. Mirrors the text-box manager
        # pattern in `_process_events` (an active UI layer claims its
        # clicks before anything else). The bank's own handler owns the
        # left-click semantics (item dispatch lands here next); the
        # unconditional `return` also swallows right-clicks on the popup
        # body so the menu reads as opaque to the cursor while open.
        if (event.type == pygame.MOUSEBUTTONDOWN
                and self.bank.menu_button.is_open
                and self.bank.menu_button.popup_rect.collidepoint(event.pos)):
            self.bank.handle_event(event, self.components)
            return

        # Wires get the event before bank/components: a click that lands on a
        # port should start a wire, not drag the underlying component.
        if self.wires.handle_event(event, self.components):
            return

        # Try the bank first since it has priority for clicks in its area. If it returns True,
        # it handled the event and we can skip the rest.
        # Returns True if a new game was spawned
        before = len(self.components)
        if self.bank.handle_event(event, self.components):
            if len(self.components) > before:
                spawned_component = self.components[-1]
                self.history.push(PlaceComponent(self.components, self.wires, spawned_component))
                self._set_selected_components([spawned_component])
                # Spawned components should drag immediately if the mouse is held.
                self._start_group_drag(event.pos, click_candidate=None)
            return

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == InputSettings.LEFT_CLICK:
            clicked = self._component_at(event.pos)
            if clicked is None:
                self._set_selected_components([])
                self._start_marquee(event.pos)
                return
            if clicked in self.selected_components:
                self._start_group_drag(event.pos, click_candidate=clicked)
                return
            self._set_selected_components([clicked])
            self._start_group_drag(event.pos, click_candidate=clicked)
            return

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == InputSettings.RIGHT_CLICK:
            for i in range(len(self.components) - 1, -1, -1):
                comp = self.components[i]
                action = comp.handle_event(event)
                if action == "DELETE":
                    self._delete_component_at_index(i)
                    break

    def _update_port_hover(self, mouse_pos) -> None:
        """Refresh the hovered flag on every port given the current cursor.

        Walks all workspace components plus the toolbox template so a port in
        either place lights up under the cursor. Callers must invoke this on
        MOUSEMOTION; ports do not poll their own state.

        Args:
            mouse_pos (tuple[int, int]): Cursor position in screen space.
        """
        for comp in self.components:
            for port in comp.ports:
                port.hovered = port.rect.collidepoint(mouse_pos)
        for tpl in self.bank.templates:
            for port in tpl.ports:
                port.hovered = port.rect.collidepoint(mouse_pos)

    def _component_at(self, pos):
        """Return the top-most workspace component under the cursor."""
        for comp in reversed(self.components):
            if comp.rect.collidepoint(pos):
                return comp
        return None

    def _set_selected_components(self, components):
        """Set the active component selection and sync visual flags."""
        selected = [comp for comp in components if comp in self.components]
        selected_ids = set(selected)
        for comp in self.components:
            comp.selected = comp in selected_ids
        self.selected_components = selected

    def _prune_selection(self):
        """Drop stale selections when undo/redo removes selected components."""
        live = [comp for comp in self.selected_components if comp in self.components]
        if len(live) != len(self.selected_components):
            self._set_selected_components(live)

    def _delete_component_at_index(self, index):
        """Delete one component and record undo history for it."""
        comp = self.components[index]
        affected_wires = [
            w for w in self.wires.wires
            if w.source.parent is comp or w.target.parent is comp
        ]
        self.wires.drop_wires_for_component(comp)
        self.components.pop(index)
        self.history.push(DeleteComponent(self.components, self.wires, comp, affected_wires, index))
        if comp in self.selected_components:
            self._set_selected_components(
                [selected for selected in self.selected_components if selected is not comp]
            )

    def _delete_selected_components(self):
        """Delete every selected component in one keypress."""
        if not self.selected_components:
            return
        selected_ids = set(self.selected_components)
        for index in range(len(self.components) - 1, -1, -1):
            if self.components[index] in selected_ids:
                self._delete_component_at_index(index)
        self._set_selected_components([])
        self._cancel_group_drag()
        self._cancel_marquee()

    def _start_group_drag(self, mouse_pos, click_candidate):
        """Begin dragging all currently selected components together."""
        if not self.selected_components:
            return
        self._group_drag_anchor = mouse_pos
        self._group_drag_start_positions = {
            comp: (comp.rect.x, comp.rect.y)
            for comp in self.selected_components
        }
        self._group_drag_moved = False
        self._click_candidate_component = click_candidate

    def _is_group_dragging(self):
        return self._group_drag_anchor is not None

    def _cancel_group_drag(self):
        self._group_drag_anchor = None
        self._group_drag_start_positions = {}
        self._group_drag_moved = False
        self._click_candidate_component = None

    def _handle_group_drag_event(self, event):
        """Update or complete a multi-component drag gesture."""
        if self._group_drag_anchor is None:
            return
        if event.type == pygame.MOUSEMOTION:
            dx = event.pos[0] - self._group_drag_anchor[0]
            dy = event.pos[1] - self._group_drag_anchor[1]
            if dx or dy:
                self._group_drag_moved = True
            for comp, (start_x, start_y) in self._group_drag_start_positions.items():
                comp.rect.x = start_x + dx
                comp.rect.y = start_y + dy
                comp._clamp_to_workspace()
            return
        if event.type == pygame.MOUSEBUTTONUP and event.button == InputSettings.LEFT_CLICK:
            # Preserve click-without-drag behavior for single-component Switch toggles.
            if (not self._group_drag_moved
                    and self._click_candidate_component is not None
                    and len(self.selected_components) == 1
                    and self.selected_components[0] is self._click_candidate_component):
                self._click_candidate_component._on_click()
            self._cancel_group_drag()

    def _start_marquee(self, mouse_pos):
        """Start drawing a marquee selection rectangle."""
        self._marquee_start = mouse_pos
        self._marquee_end = mouse_pos

    def _is_marquee_selecting(self):
        return self._marquee_start is not None

    def _cancel_marquee(self):
        self._marquee_start = None
        self._marquee_end = None

    def _current_marquee_rect(self):
        """Return normalized marquee rect from the current drag endpoints."""
        if self._marquee_start is None or self._marquee_end is None:
            return pygame.Rect(0, 0, 0, 0)
        x0, y0 = self._marquee_start
        x1, y1 = self._marquee_end
        left = min(x0, x1)
        top = min(y0, y1)
        width = abs(x1 - x0)
        height = abs(y1 - y0)
        return pygame.Rect(left, top, width, height)

    def _handle_marquee_event(self, event):
        """Update or complete a marquee selection gesture."""
        if event.type == pygame.MOUSEMOTION:
            self._marquee_end = event.pos
            return
        if event.type == pygame.MOUSEBUTTONUP and event.button == InputSettings.LEFT_CLICK:
            self._marquee_end = event.pos
            marquee = self._current_marquee_rect()
            if (marquee.width < SelectionBoxSettings.MIN_DRAG_PIXELS
                    and marquee.height < SelectionBoxSettings.MIN_DRAG_PIXELS):
                self._set_selected_components([])
                self._cancel_marquee()
                return
            selected = [
                comp for comp in self.components
                if marquee.colliderect(comp.rect)
            ]
            self._set_selected_components(selected)
            self._cancel_marquee()

    def _build_hotkey_bar_text_surfaces(self):
        """Render and cache per-hint text surfaces for the top bar."""
        hotkey_hints = (
            "CTRL+Z UNDO",
            "CTRL+Y REDO",
            "T TEXT",
            "F11 FULLSCREEN",
            "ESC MENU/QUIT",
        )
        font = Fonts.text_box
        if font is None:
            raise RuntimeError("Fonts.init() must run before hotkey bar text render")
        return [
            font.render(hint, True, ShortcutBarSettings.TEXT_COLOR)
            for hint in hotkey_hints
        ]

    def _draw_hotkey_bar(self):
        """Draw an old-school top status strip listing keyboard shortcuts."""
        bar_rect = pygame.Rect(
            0,
            0,
            ScreenSettings.WIDTH,
            ShortcutBarSettings.HEIGHT,
        )
        pygame.draw.rect(self.screen, ShortcutBarSettings.BG_COLOR, bar_rect)
        pygame.draw.line(
            self.screen,
            ShortcutBarSettings.BORDER_COLOR,
            (0, bar_rect.bottom - 1),
            (ScreenSettings.WIDTH, bar_rect.bottom - 1),
            1,
        )
        hint_surfs = self._hotkey_hint_surfs
        if not hint_surfs:
            return

        # Distribute hint groups with true "space-evenly" spacing:
        # identical gap before the first item, between every item, and
        # after the last item.
        total_width = sum(surf.get_width() for surf in hint_surfs)
        gap_count = len(hint_surfs) + 1
        gap = max(0.0, (ScreenSettings.WIDTH - total_width) / gap_count)
        x = gap
        for surf in hint_surfs:
            text_rect = surf.get_rect()
            text_rect.x = round(x)
            text_rect.centery = bar_rect.centery
            self.screen.blit(surf, text_rect)
            x += surf.get_width() + gap

    # -------------------------
    # PER-FRAME UPDATE / RENDER
    # -------------------------

    def _update_world(self):
        """Advance per-frame simulation state.

        Wires hold the canonical list of connections. SignalManager reads
        port states, computes new outputs, applies them, and propagates
        through wires — see signals.py for the two-phase contract.
        """
        self.signals.update(self.components, self.wires.wires)

    def _draw(self):
        for comp in self.components:
            comp.draw(self.screen)
        # Wires sit above the components but below the toolbox bank, so a
        # wire routed through the toolbox area is hidden by the dark bank
        # rectangle drawn next.
        self.wires.draw(self.screen)
        # Annotation text boxes draw on top of components and wires so
        # labels stay legible even if a wire happens to pass underneath.
        # Still below the bank — text boxes are clamped out of the bank
        # area anyway, but drawing under it costs nothing and keeps the
        # toolbox visually authoritative.
        self.text_boxes.draw(self.screen)
        self._draw_selection_marquee()
        # Draw the bank above text boxes and components so the toolbox
        # always reads as the topmost workspace surface.
        self.bank.draw(self.screen)
        # Modal dialog draws above everything else (including the bank
        # and its popup) so its dimmed backdrop covers the workspace
        # uniformly. The CRT overlay still draws on top of this in
        # _render_frame, which keeps the retro aesthetic consistent
        # with the rest of the screen.
        if self.dialog is not None:
            self.dialog.draw(self.screen)

    def _draw_selection_marquee(self):
        """Draw the active marquee rectangle while drag-selecting."""
        if not self._is_marquee_selecting():
            return
        rect = self._current_marquee_rect()
        if rect.width == 0 or rect.height == 0:
            return
        fill = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        fill.fill(SelectionBoxSettings.FILL_COLOR)
        self.screen.blit(fill, rect.topleft)
        pygame.draw.rect(
            self.screen,
            SelectionBoxSettings.BORDER_COLOR,
            rect,
            SelectionBoxSettings.BORDER_THICKNESS,
        )

    def _draw_grid(self):
        grid_color = (ColorSettings.WORD_COLORS["WHITE"]) # Subtle light blue
        grid_size = ScreenSettings.GRID_SIZE

        # Draw Vertical Lines
        for x in range(0, ScreenSettings.WIDTH, grid_size):
            pygame.draw.line(self.screen, grid_color, (x, 0), (x, ScreenSettings.HEIGHT), 1)

        # Draw Horizontal Lines
        for y in range(0, ScreenSettings.HEIGHT, grid_size):
            pygame.draw.line(self.screen, grid_color, (0, y), (ScreenSettings.WIDTH, y), 1)

    def _render_frame(self):
        self.screen.fill(ScreenSettings.BG_COLOR)
        self._draw_grid()
        self._draw()
        self._draw_hotkey_bar()
        self.crt.draw()

    def run(self):
        while True:
            self._process_events()
            self._update_world()
            self._render_frame()
            pygame.display.flip()
            self.clock.tick(ScreenSettings.FPS)

# Main execution
if __name__ == '__main__':
    game_manager = GameManager()
    game_manager.run()

