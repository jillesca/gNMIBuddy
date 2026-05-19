---
name: python-engineering
description: Python software engineering standards for gNMIBuddy. Load when doing coding, implementation, refactoring, code review, or object design work. Covers DRY, KISS, YAGNI, SOLID, object design, readability, and Martin Fowler's refactoring guidelines.
user-invocable: true
---

# Python Engineering Standards

## Core Principles

Apply all of the following to every code change:

- **DRY** — Centralise shared logic; do not duplicate it across modules
- **KISS** — Choose the simplest solution that satisfies the requirement
- **YAGNI** — Implement only what is needed now; do not add speculative features
- **SOLID** — Follow Single Responsibility, Open/Closed, Liskov Substitution, Interface Segregation, and Dependency Inversion
- **Modularity** — Encapsulate distinct concerns in separate modules so each is independently testable
- **Zen of Python** — Favour simplicity, readability, and explicitness (`import this`)

## Readability and Structure

Code must read like a book — a reader should be able to follow the flow top to bottom without jumping around:

- Use clear, descriptive names for every symbol; abbreviations are not acceptable
- Place public/external functions at the top of a module
- Place helper functions used by a public function directly below it
- Place internal/private functions after the helpers
- Comments explain **why** something is done, never **what** — the code itself must be self-explanatory
- Follow Martin Fowler's refactoring principles: write code that humans understand easily

## Object Design and Boilerplate Avoidance

Using dictionaries to encapsulate related data or behaviour **is prohibited** — use objects instead.

Before creating any new class or abstraction, ask:

1. Does this object add genuine value, or is it duplicating an existing data structure?
2. Am I solving a real problem, or adding complexity for the sake of design purity?
3. Can I work directly with an existing immutable object (e.g. a dataclass)?
4. Am I copying fields between objects with no transformation? If so, work directly with the source.

**Critical balance**: readability for humans is the most important quality and must never be sacrificed for theoretical purity. A simple, direct approach that reads well beats a "properly architected" complex solution.

Guidelines:

- Favour composition over unnecessary abstraction
- Eliminate attribute duplication — never mirror an existing structure with different names
- Remove intermediate objects that exist only to pass data from one point to another
- Prefer clarity over architectural purity
