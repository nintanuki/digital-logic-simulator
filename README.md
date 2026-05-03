# Circuit Builder

A digital logic sandbox written in Python with Pygame. Students drag NAND gates onto a grid, wire them together, and discover that every other gate (NOT, AND, OR, XOR, latches, adders) can be built from that one universal block.

## Background

Inspired by Sebastian Lague's [Digital Logic Sim](https://github.com/SebLague/Digital-Logic-Sim). The original is written in C# and Unity; this is a from-scratch reimagining in Python so it can be modified, extended, and used as a teaching tool in my classroom without an engine in the way.

## Classroom Use

Used in computer science class and during IT and coding enrichment to teach how logic gates compose into real computation. The intended progression is:

1. Start with a NAND gate, a Switch (input), and an LED (output) in the toolbox.
2. Wire NANDs together to build NOT, AND, OR, and XOR.
3. Save a finished circuit as a reusable, named "black box" component that drops back into the toolbox.
4. Use those components as building blocks for larger circuits like an SR latch or a 4-bit ripple adder.

The point is abstraction: once a circuit works, students stop worrying about its internals and start treating it as a part.

## Current Status

Working prototype. Drag-and-drop, wiring, port logic, live signal propagation, the Switch / LED input-output components, and free-floating annotation text boxes are all in.

**Next up: Pass 1 — Save as Component (in-session).** The selling point of this project is the abstraction loop — build a circuit from NANDs, save it as a named component, drop it into the next circuit as a black box, build with that, save *that*, and keep climbing the layers. Pass 1 gets the loop working end-to-end as a rough first version (everything lives in memory; closing the program loses the saved components). Disk save/load comes in Pass 3. See `docs/TODO.md` for the full pass-based roadmap.

The roadmap is organized around iterative passes rather than milestones — the project goes through the codebase several times, each pass leaving it more usable than the last. There is no deadline; this is an enrichment project for a future classroom unit, not a product.

The program is designed to be fully usable with the mouse alone. Keyboard shortcuts exist as a convenience for power users but never replace a clickable equivalent.

## Controls

### Mouse

| Action | Input |
| --- | --- |
| Spawn a component from the toolbox | Left-click the template |
| Move a component or text box | Left-click and drag |
| Toggle a Switch (IN) | Left-click without dragging |
| Wire two ports | Left-click-drag from one port, release on the other |
| Cancel an in-flight wire | Right-click during the drag, or release in empty space |
| Delete a component, wire, or text box | Right-click it |
| Edit a text box | Left-click to focus, then type |
| Stop editing a text box | Click somewhere else, or press `Esc` |

### Keyboard (power user)

| Action | Input |
| --- | --- |
| Spawn a NAND at (50, 50) | `N` |
| Spawn a text box at the cursor | `T` |
| Toggle fullscreen | `F11` |
| Quit | `Esc` (only when no text box is focused) |

## Requirements

- Python 3.10+
- Pygame

```bash
pip install pygame
python main.py
```

## Project Layout

```
circuit-builder/
├── main.py          # GameManager: event loop, lifecycle, rendering
├── elements.py      # Port, Component (default = NAND), Switch, LED
├── wires.py         # Wire + WireManager (drag-to-connect, hit-test delete)
├── signals.py       # SignalManager: per-frame two-phase signal propagation
├── text_boxes.py    # TextBox + TextBoxManager (annotation labels)
├── ui.py            # ComponentBank (the toolbox)
├── fonts.py         # Fonts: shared Font instances cached at boot
├── crt.py           # CRT scanline / flicker overlay
├── settings.py      # All constants (colors, sizes, paths, input)
├── assets/          # Fonts and graphics
└── docs/
    ├── TODO.md      # Roadmap (Now / Next / Later / Brainstorming / Far future)
    ├── TESTING.md   # Manual test checklist + refactoring rules
    └── CHANGELOG.md # Append-only history of changes
```

## Contributing

Read `docs/TESTING.md` before making changes. It defines the manual test checklist and the refactoring rules this project follows (PEP-8, constants in `settings.py`, no magic numbers, docstrings everywhere, etc.). Then skim recent entries in `docs/CHANGELOG.md` so you know the current state of the codebase. Pick the next item from `docs/TODO.md` (top of the file = highest priority).
