From the software engineering perspective I want the implementation to follow these principles:

- DRY (Don't Repeat Yourself): Avoid code duplication by centralizing the logic for loading environment variables in a single module. This will make the codebase cleaner and easier to maintain.
- KISS (Keep It Simple, Stupid): The solution should be straightforward and easy to understand. Avoid unnecessary complexity in the implementation.
- YAGNI (You Aren't Gonna Need It): Focus on the current requirements and avoid adding features or functionality that are not needed at this moment. The implementation should be focused on the task at hand without over-engineering.
- SOLID principles: Ensure that the code adheres to the SOLID principles of object-oriented design, promoting maintainability and scalability.
- Modularity: The code should be organized into modules that encapsulate specific functionality, making it easier to test and maintain.
- Readability: The code should be easy to read and understand, with clear naming conventions and comments where necessary.
- Zen of Python: The implementation should follow the principles outlined in the Zen of Python, such as simplicity, readability, and explicitness.
- Follow Martin Fowler's Refactoring Principles: The implementation should adhere to the refactoring principles outlined by Martin Fowler, promoting clean code and maintainability. The key is to write code that humans can understand easily.
- Code should be able to read like a book with clear structure and flow and clear and descriptive names.
- External functions should be at the top of the modules, functions used by top function should be directly below. Internal functions should be below that. it should be like reading a book and if you want to read more about a topic, you can easily find the relevant functions directly.
- Comments on code should be only used to explain why something is done, not what is done. The code must be self-explanatory as much as possible.

## Object Design and Boilerplate Avoidance

The use of dictionaries to encapsulate related data and functionality is prohibited and is an anti-pattern. Objects must be used instead to promote better structure and organization of the code.

**Critical Balance Principle**: When designing objects and abstractions, always seek the optimal balance between software engineering principles and human readability. **Readability for humans is the most important aspect** and should never be sacrificed for theoretical purity.

### Avoiding Unnecessary Boilerplate

Before creating new objects or abstractions, always ask:

1. **Does this object add genuine value?** Or is it just duplicating existing data structures?
2. **Am I solving a real problem?** Or creating complexity for the sake of "proper design"?
3. **Can I work directly with existing immutable objects?** Often, existing structures like dataclasses already provide what we need.
4. **Am I creating repetitive attribute mapping?** If you're copying fields from one object to another without transformation, consider working directly with the source.

### Guidelines for Object Creation

- **Favor composition over unnecessary abstraction**: Work directly with existing immutable objects when possible
- **Eliminate attribute duplication**: Avoid creating objects that simply mirror existing structures with different names
- **Question intermediate objects**: If an object exists solely to pass data between two points, consider direct manipulation
- **Prioritize clarity over architectural purity**: A simple, direct approach that reads well is better than a "properly architected" complex solution

The goal is code that reads like a book while avoiding unnecessary complexity and boilerplate that adds no real value.

The implementation should be straightforward and easy to understand, avoiding unnecessary complexity.

These are rules you must always follow:

- You must never commit any files. I used the staging directory to prepare changes before committing. If you commit a change, you mess with my workflow.
- You must never push any commits to any remote branches. I use commits to review changes before they are merged.
- You must never merge a PR. I use PRs to review changes before they are merged.
- To test the cli, use the uv run ... capture the output to a log file and inspect the log file to verify the output. The terminal output sometimes is cutoff.
- The terminal has been disconnecting, so when running cli commands, always capture the output to a log file and examine the log file to verify the output.
- If you need to run tests, use the pytest cli rather than the integrated test terminal, from time to time the integrated test terminal hangs and does not show the output of the tests, so it is better to run pytest from the cli.
- If you find areas of opportunity to improve the codebase for this task or other tasks, ask them to add them as notes on the issue.
- If you encounter obstacles or challenges during your work, you should document these issues in the issue thread and seek assistance from the team.
- If logging variables, log entries must use lazy loading. f-strings are prohibited.
- import statements should be grouped logically (e.g., standard library imports, third-party imports, local application imports) and separated by blank lines. They must also be at the top of the module so is easy to know what modules are being used.
