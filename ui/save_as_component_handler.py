"""Save-as-component handler for creating reusable components.

Manages the process of saving a workspace circuit as a reusable component template.
Decouples this logic from GameManager to reduce its size and complexity.
"""

from typing import Any, Dict, List, Tuple
from copy import deepcopy
from core.elements import LED, Switch


class SaveAsComponentHandler:
    """Handles save-as-component workflow.
    
    Manages the dialog, workspace snapshotting, and component library updates
    when the user saves a circuit as a reusable component.
    """
    
    @staticmethod
    def snapshot_workspace_definition(
        components: List[Any],
        wires: List[Any],
        input_switches: List[Switch],
        output_leds: List[LED],
    ) -> Dict[str, Any]:
        """Serialize the current workspace into a saved-component definition.
        
        Args:
            components: All placed components.
            wires: All placed wires.
            input_switches: Switches selected as external inputs.
            output_leds: LEDs selected as external outputs.
        
        Returns:
            Dict[str, Any]: Serialized sub-circuit payload for SavedComponent runtime.
        """
        from core.project_manager import ProjectManager
        
        component_indices = {
            comp: idx for idx, comp in enumerate(components)
        }
        component_defs = [
            ProjectManager.serialize_component(comp) for comp in components
        ]
        wire_defs = []
        for wire in wires:
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
    def infer_component_ports(components: List[Any]) -> Tuple[List[Switch], List[LED]]:
        """Auto-infer ports from the workspace (Switches→INPUT, LEDs→OUTPUT).
        
        Per the "Save-as-Component port inference rule": every Switch in the
        workspace becomes an INPUT port and every LED becomes an OUTPUT port;
        ordering is ascending Y so the top-of-screen IN is port 0, the next one
        down is port 1, and so on. Y was picked over component-creation-order
        because the visual top-to-bottom column is what the student actually
        sees — picking the order from something invisible would break the
        spatial intuition.
        
        Args:
            components: All placed components.
        
        Returns:
            Tuple[List[Switch], List[LED]]: Inferred input switches and output LEDs.
        """
        input_switches = sorted(
            (c for c in components if isinstance(c, Switch)),
            key=lambda s: s.rect.y,
        )
        output_leds = sorted(
            (c for c in components if isinstance(c, LED)),
            key=lambda l: l.rect.y,
        )
        return input_switches, output_leds
