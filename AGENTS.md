# gNMIBuddy — Project Instructions

gNMIBuddy is a Python CLI and MCP server for querying network devices via the gNMI protocol.

## Operational Rules

These rules apply to all work in this repository without exception:

- Never commit files — staging is reserved for the developer's workflow
- Never push commits to any remote branch
- Never merge a PR
- To test the CLI: `uv run ...` and capture output to a log file, then inspect the file
- Terminal output can be cut off, so always redirect CLI command output to a log file
- Run tests with `pytest` from the terminal — the integrated test terminal can hang
- If you find improvement opportunities while working on a task, note them on the issue
- If you hit a blocker, document it in the issue thread and ask for help

## Python Conventions

These apply to every Python file in this project:

- Log entries must use lazy evaluation — f-strings inside logging calls are prohibited
- Import statements must be grouped (standard library → third-party → local application), separated by blank lines, and placed at the top of each module

## Coding and Design Work

When doing implementation, refactoring, code review, or object design work, load the
`python-engineering` skill for the full set of engineering principles (DRY, KISS, YAGNI,
SOLID, object design, readability, and Martin Fowler's refactoring guidelines).
