# Testing Checklist

Run this after major changes to ensure nothing broke:

* Game loads
* Drag and drop still works
* Components can still be moved from toolbox to workspace
* Wiring still works
* Input/Output logic still works
* Right click still deletes components

# Refactoring Rules
* Update CHANGELOG.md for every code change (timestamp, file, line numbers, before/after, why) including which AI model made the change. Read it first before making changes so you know the current state.
* All code must be PEP-8 compliant.
* Less code is better than more code, but clean and readable code is the best.
* Keep "middlemen" minimal, if A calls B, and all B does is call C, A should just call C
* Keep code clean of dead imports, unused variables and functions, and legacy code.
* GameManager must be light, offload responsibilities to other classes
* GameManager is an orchestrator, not a feature container.
* GameManager should own app lifecycle, high-level state, and subsystem coordination.
* Feature logic should live in the class that owns that feature.
* State should live next to the behavior that uses it.
* Avoid passing the full GameManager into other classes unless absolutely necessary.
* Prefer explicit dependencies, narrow interfaces, and callbacks over giving a class access to all manager internals.
* "Communicate through GameManager" means coordination, not global access to shared mutable state.
* New features should not add large new blocks of logic directly into GameManager if a dedicated subsystem/controller is more appropriate.
* Event handling, rendering, persistence, and UI state should be separated by responsibility as much as reasonably possible.
* If a subsystem needs to trigger a cross-system action, prefer returning a result/action, calling a callback, or asking GameManager to coordinate it rather than directly reaching into another subsystem.
* When possible classes should communicate to each other through GameManager.
* Any new names for classes and functions must be clear regarding it's function
* Keep all constants declared in settings.py, avoid magic numbers
* All classes and functions must have a docstring.
* All docstrings must have a summary, Args (if applicable) and Returns (if applicable)
* Do not change function names (unless their role is now completely different)
* Keep functions organized and grouped by role. The update and run functions in classes should be the last function, and do as little as possible. Only call other functions if possible.
* Do not change variable names if not necessary.
* Function names and variable names must be descriptive.
* Do not remove comments.
* Comments must explain why, not just what.
* When making a change, do not leave a comment that a change was made, unless it was to fix a bug that wasn't obvious and to explain why something was done in an unconventional way.