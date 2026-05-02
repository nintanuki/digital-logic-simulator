# Change Log

This file is an append-only record of every code change made to Dungeon Digger
by a human, AI assistant, or copilot tool. Read it before making changes so you
know the current state of the codebase.

## Format

Each entry covers one logical change (which may touch multiple files). Use the
template below, with one `**File:** ... **Why:** ...` block per file touched.

    ## YYYY-MM-DD HH:MM — short summary

    **File:** path/to/file.py
    **Lines (at time of edit):** 38-52 (modified)
    **Before:**
        [old code]
    **After:**
        [new code]
    **Why:** explanation
    **Editor:** name of human or AI model

## Conventions

* Line numbers reflect the file as it existed at the moment of the edit. Edits
  above shift line numbers below, so older entries will not match the current
  file. Never go back and "fix" old line numbers.
* Entries are append-only. Never delete history. If a later edit reverts an
  earlier one, write a new entry that references the original.
* For new files, write `(new file)` instead of a line range. The "Before"
  block can be omitted or marked `(file did not exist)`.
* For deletes, write `(deleted)` and put the removed code in "Before" with no
  "After" block.
* Keep "Before" / "After" blocks short. If a change is huge, summarize with a
  diff-style excerpt of the most important lines plus a sentence describing the
  rest, instead of pasting the entire file.

## 2026-05-01 — Rewrite README for a professional tone

**File:** README.md
**Lines (at time of edit):** 1-5 (replaced; file grew to ~55 lines)
**Before:**
    # circuit-builder

    This project is my attempt at creating my own version of Sebastian Lague's digital logic simulator: https://github.com/SebLague/Digital-Logic-Sim

    ^ It is inspired by this original project but I wanted to have creative control and I don't know C# or Unity, so intead of trying to edit it I decided to try recreating it in Python using Pygame and making it my own. This will be used in computer science class as well as IT and coding classes during enrichment to teach students about how logic gates are used in computation.

    Students can drag and drop components onto the mat from the toolbox. Each component has at least one input and one output. We start with a NAND. These NANDs can be wired together to create NOT, OR and AND gates. Once a student has completed their circuit of components, they can save it as a component itself, name it, and it becomes a "black box" abstacted away into a named component that goes into their toobox. They no longer need to worry about the internal circuitry, just wiring up to the inputs and output. Circuits such as the AND-OR-LATCH or a 4-Bit Ripple Adder can be created using this too.
**After:**
    # Circuit Builder

    A digital logic sandbox written in Python with Pygame. Students drag NAND
    gates onto a grid, wire them together, and discover that every other gate
    (NOT, AND, OR, XOR, latches, adders) can be built from that one universal
    block.

    [...sections for Background, Classroom Use, Current Status, Controls,
    Requirements, Project Layout, Contributing...]
**Why:** Original draft read like a private note: typos (intead, abstacted, toobox, too), no install/run steps, no controls reference, no project layout, no link to the roadmap. New version is structured for someone discovering the repo cold, fixes the typos, and points contributors at TESTING.md.
**Editor:** Claude (Opus)