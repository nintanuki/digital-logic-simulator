"""Project manager for disk save/load operations.

Handles all project serialization, deserialization, and file I/O.
Decouples project management from GameManager to reduce its size and complexity.
"""

import json
import os
from copy import deepcopy
from typing import Any, Dict, List, Optional

from core.elements import Component, LED, SavedComponent, Switch
from core.wires import Wire


class ProjectManager:
    """Manages project persistence operations.
    
    Handles saving projects to disk, loading projects from disk, listing available
    projects, and serializing/deserializing workspace state to/from JSON format.
    
    Args:
        projects_dir: Directory path where projects are stored.
    """
    
    def __init__(self, projects_dir: str) -> None:
        """Initialize ProjectManager with projects directory path.
        
        Args:
            projects_dir: Directory path where projects are stored.
        """
        self.projects_dir = projects_dir
    
    def list_project_names(self) -> List[str]:
        """Return sorted list of project names available on disk.
        
        Returns:
            List[str]: Sorted list of project file names (without .json extension).
        """
        if not os.path.isdir(self.projects_dir):
            return []
        names = []
        for filename in os.listdir(self.projects_dir):
            if filename.lower().endswith(".json"):
                names.append(os.path.splitext(filename)[0])
        return sorted(names)
    
    def save_project(self, name: str, workspace_data: Dict[str, Any]) -> str:
        """Serialize and save a project to disk.
        
        Args:
            name: Project name (will be sanitized for filesystem).
            workspace_data: Workspace state containing components, wires, etc.
        
        Returns:
            str: Sanitized project name as saved to disk.
        """
        os.makedirs(self.projects_dir, exist_ok=True)
        safe_name = "".join(
            c if c.isalnum() or c in (" ", "-", "_") else "_" for c in name
        ).strip()
        path = os.path.join(self.projects_dir, safe_name + ".json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(workspace_data, f, indent=2)
        return safe_name
    
    def load_project(self, safe_name: str) -> Optional[Dict[str, Any]]:
        """Load and deserialize a project from disk.
        
        Args:
            safe_name: Sanitized project name (without .json extension).
        
        Returns:
            Optional[Dict[str, Any]]: Deserialized project payload, or None if file not found.
        """
        path = os.path.join(self.projects_dir, safe_name + ".json")
        try:
            with open(path, "r", encoding="utf-8") as f:
                payload = json.load(f)
            return payload
        except FileNotFoundError:
            return None
    
    @staticmethod
    def serialize_component(comp: Component) -> Dict[str, Any]:
        """Serialize one workspace component into a definition record.
        
        Args:
            comp: Component instance to serialize.
        
        Returns:
            Dict[str, Any]: Serialized component payload.
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
    
    @staticmethod
    def deserialize_component(comp_def: Dict[str, Any]) -> Component:
        """Build a workspace Component from a serialized record.
        
        Args:
            comp_def: Serialized component definition.
        
        Returns:
            Component: Reconstructed component instance.
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
    
    @staticmethod
    def serialize_workspace(
        name: str,
        components: List[Component],
        wires: List[Wire],
        text_boxes: Any,
        saved_components: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Serialize the entire workspace into a project dict.
        
        Args:
            name: Project name.
            components: Placed components.
            wires: Placed wires.
            text_boxes: Placed text boxes.
            saved_components: Saved component records.
        
        Returns:
            Dict[str, Any]: JSON-serializable project payload.
        """
        component_indices = {comp: idx for idx, comp in enumerate(components)}
        component_defs = [ProjectManager.serialize_component(comp) for comp in components]
        
        wire_defs = []
        for wire in wires:
            src = wire.source.parent
            tgt = wire.target.parent
            if src not in component_indices or tgt not in component_indices:
                continue
            wire_defs.append({
                "source_component_index": component_indices[src],
                "source_port_index": src.ports.index(wire.source),
                "target_component_index": component_indices[tgt],
                "target_port_index": tgt.ports.index(wire.target),
            })
        
        text_box_defs = [
            {"x": tb.rect.x, "y": tb.rect.y, "text": tb.text}
            for tb in text_boxes
        ]
        saved_component_defs = [
            {
                "name": rec["name"],
                "color": list(rec["color"]),
                "definition": deepcopy(rec["definition"]),
            }
            for rec in saved_components
        ]
        
        return {
            "version": 1,
            "name": name,
            "components": component_defs,
            "wires": wire_defs,
            "text_boxes": text_box_defs,
            "saved_components": saved_component_defs,
        }
    
    @staticmethod
    def deserialize_workspace(
        payload: Dict[str, Any],
        components: List[Component],
        wires: Any,
        text_boxes: Any,
        bank: Any,
        saved_components: List[Dict[str, Any]],
    ) -> None:
        """Reconstruct the workspace from a serialized project dict.
        
        Args:
            payload: Serialized project payload.
            components: Live components list to populate.
            wires: Live wire manager to populate.
            text_boxes: Live text box manager to populate.
            bank: Live component bank for template registration.
            saved_components: Live saved components list to populate.
        """
        components.clear()
        wires.wires.clear()
        wires.pending_source = None
        text_boxes.text_boxes.clear()
        text_boxes.focused = None
        
        # Reset the saved-component library and bank templates
        saved_components.clear()
        bank.reset_to_default_templates()
        
        # Restore saved-component library first so spawned SavedComponents in the workspace exist in the bank
        for rec in payload.get("saved_components", []):
            definition = rec["definition"]
            color = tuple(rec["color"])
            name = rec["name"]
            saved_components.append({
                "name": name,
                "color": color,
                "definition": definition,
            })
            bank.add_saved_component_template(name, color, deepcopy(definition))
        
        # Restore components
        for comp_def in payload.get("components", []):
            comp = ProjectManager.deserialize_component(comp_def)
            components.append(comp)
        
        # Restore wires
        for wire_def in payload.get("wires", []):
            src_comp = components[wire_def["source_component_index"]]
            tgt_comp = components[wire_def["target_component_index"]]
            src_port = src_comp.ports[wire_def["source_port_index"]]
            tgt_port = tgt_comp.ports[wire_def["target_port_index"]]
            wires.wires.append(Wire(src_port, tgt_port))
        
        # Restore text boxes
        for tb_def in payload.get("text_boxes", []):
            tb = text_boxes.spawn_at(
                (tb_def["x"], tb_def["y"]), focus=False
            )
            if tb is not None:
                tb.text = tb_def.get("text", "")
                tb._layout_to_text()
