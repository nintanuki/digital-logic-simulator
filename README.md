# Circuit Builder

A digital logic sandbox written in Python with Pygame. Students drag NAND gates onto a grid, wire them together, and discover that every other gate (NOT, AND, OR, XOR, latches, adders) can be built from that one universal block.

## Background

Inspired by Sebastian Lague's [Digital Logic Sim](https://github.com/SebLague/Digital-Logic-Sim). The original is written in C# and Unity; this is a from-scratch reimagining in Python so it can be modified, extended, and used as a teaching tool in my classroom without an engine in the way.

## Classroom Use

Used in computer science class and during IT and coding enrichment to teach how logic gates compose into real computation. The intended progression is:

1. Start with a single NAND gate in the toolbox.
2. Wire NANDs together to build NOT, AND, OR, and XOR.
3. Save a finished circuit as a reusable, named "black box" component that drops back into the toolbox.
4. Use those components as building blocks for larger circuits like an AND-OR latch or a 4-bit ripple adder.

The point is abstraction: once a circuit works, students stop worrying about its internals and start treating it as a part.

## Current Status

Early prototype. The workspace, toolbox, NAND component and drag-and-drop are in place. Wiring, port logic, and saving are not yet implemented; see `docs/TODO.md` for the roadmap.

## Controls

| Action | Input |
| --- | --- |
| Spawn a NAND from the toolbox | Left-click the toolbox template |
| Move a component | Left-click and drag |
| Delete a component | Right-click |
| Spawn a NAND at (50, 50) | `N` |
| Toggle fullscreen | `F11` |
| Quit | `Esc` |

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
├── elements.py      # Component class (NAND today, more later)
├── ui.py            # ComponentBank (the toolbox)
├── crt.py           # CRT scanline / flicker overlay
├── settings.py      # All constants (colors, sizes, paths, input)
├── assets/          # Fonts and graphics
└── docs/
    ├── TODO.md      # Roadmap
    ├── TESTING.md   # Manual test checklist + refactoring rules
    └── CHANGELOG.md # Append-only history of changes
```

## Contributing

Read `docs/TESTING.md` before making changes. It defines the manual test checklist and the refactoring rules this project follows (PEP-8, constants in `settings.py`, no magic numbers, docstrings everywhere, etc.).
