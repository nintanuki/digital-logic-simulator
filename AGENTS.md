# AGENTS.md

Entry point for AI agents (Claude Code, Cursor, Codex CLI, GitHub Copilot, and
any other tool that looks for a top-level `AGENTS.md` by convention).

This file is intentionally a **pointer**, not a rules file. Duplicated rules
drift. The single source of truth for editor rules \u2014 reading order, code
style, architecture rules, comment policy, the manual testing checklist \u2014
lives in:

> [.github/copilot-instructions.md](.github/copilot-instructions.md)

Read that file before doing anything in this repo. Then read the project
documentation it links to:

1. [README.md](README.md) \u2014 what the project is and how to run it.
2. [docs/CHANGELOG.md](docs/CHANGELOG.md) \u2014 most recent entries; current state of the codebase.
3. [docs/TESTING.md](docs/TESTING.md) \u2014 how to test changes, manual checklist, full refactoring rules.
4. [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) \u2014 how the code is put together and why.
5. [docs/TODO.md](docs/TODO.md) \u2014 current pass and roadmap.

Every code change must append an entry to
[docs/CHANGELOG.md](docs/CHANGELOG.md) per the format defined at the top of
that file. No exceptions.

If you are an AI agent and asked *why* code was written a certain way, that
is a request for an **explanation**, not a code change. Do not modify code
unless the user explicitly asks for a change.
