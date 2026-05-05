from .elements import Port


class SignalManager:
    """Two-phase per-frame propagation of live signals through gates and wires.

    Each tick:
      1. Read every component's current INPUT ports and compute new OUTPUT
         values into a temporary buffer (no port writes yet).
      2. Apply the buffer to the actual OUTPUT ports.
      3. Reset every INPUT port to LOW, then for each wire copy
         source.live to target.live. Resetting first means an INPUT that
         lost its wire falls back to LOW instead of latching the value
         from the now-deleted connection.

    The buffer phase exists because gate evaluation order would otherwise
    change the result for any feedback circuit (SR latches, ring
    oscillators). With two-phase, every gate sees the same snapshot of
    inputs in a given frame.
    """

    def update(self, components, wires):
        """Advance the simulation by one frame.

        Args:
            components (list[Component]): Every component on the workspace.
                Toolbox templates are excluded — their state is irrelevant
                to the simulation.
            wires (list[Wire]): Every committed wire on the workspace.
        """
        # Phase 1: compute new outputs from current inputs into a buffer so
        # writes don't disturb other gates' reads in the same frame.
        output_buffer = {}
        for comp in components:
            comp.update_logic(output_buffer)

        # Phase 2: apply the buffered outputs to the actual ports.
        for port, value in output_buffer.items():
            port.live = value

        # Phase 3: refresh inputs from wires. Reset first so a disconnected
        # input reads LOW instead of holding the value from a removed wire.
        for comp in components:
            for port in comp.ports:
                if port.direction == Port.INPUT:
                    port.live = False
        for wire in wires:
            wire.target.live = wire.source.live
