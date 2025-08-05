Can you work on this issue "Return errors instead of empty/default body on some functions" #2. let's start by defining well the requirements, goals and work other agents need to do to acomplish this task. Before you add the plan to the issue as a new comment, share on this chat the plan to perform this task and if a requirement is not clear, point it out here so I can expand. Specifiy on the issue, that you are the author of the plan and not me, so it is clear who did what work.

Review carefully the first comment on the issue that describes the problem and examine carefully the output provided to understand what the user is asking.

From the software engineering perspective I want the implementation to follow these principles:

- DRY (Don't Repeat Yourself): Avoid code duplication by centralizing the logic for loading environment variables in a single module. This will make the codebase cleaner and easier to maintain.
- KISS (Keep It Simple, Stupid): The solution should be straightforward and easy to understand. Avoid unnecessary complexity in the implementation.
- YAGNI (You Aren't Gonna Need It): Focus on the current requirements and avoid adding features or functionality that are not needed at this moment. The implementation should be focused on the task at hand without over-engineering.
- SOLID principles: Ensure that the code adheres to the SOLID principles of object-oriented design, promoting maintainability and scalability.
- Modularity: The code should be organized into modules that encapsulate specific functionality, making it easier to test and maintain.
- Readability: The code should be easy to read and understand, with clear naming conventions and comments where necessary.
- Zen of Python: The implementation should follow the principles outlined in the Zen of Python, such as simplicity, readability, and explicitness.
- Follow Martin Fowler's Refactoring Principles: The implementation should adhere to the refactoring principles outlined by Martin Fowler, promoting clean code and maintainability. The key is to write code that humans can understand easily.

From the software engineering principles, readability is paramount and the most important aspect of the implementation. Then modularity and maintainability are also important, as they will help ensure that the code can be easily updated and extended in the future. The implementation should be straightforward and easy to understand, avoiding unnecessary complexity.

These are steps all agents must follow:

- To test the cli, use the uv run gnmibuddy.py ... capture the output to a log file and inspect the log file to verify the output. The terminal output sometimes is cutoff.
- If you need to run tests, use the pytest cli rather than the integrated test terminal, from time to time the integrated test terminal hangs and does not show the output of the tests, so it is better to run pytest from the cli.
- Request all the agents to review the implementation plan created on issue 19 so they have a clear understanding of the requirements and goals.
- If they find areas of opportunity to improve the codebase for this task or other tasks, ask them to add them as notes on the issue.
- After every agent finishes their work, they should add a comment on the issue with a summary of what they did, I don't want the agents to repeat what is already defined on the implementation plan, so the summary should be short, concise about the work they carried out.
- If any agent encounters obstacles or challenges during their work, they should document these issues in the issue thread and seek assistance from the team.

---

On the issue "Return errors instead of empty/default body on some functions" #2 of my github project, an agent had created an implementation plan. This plan is going to be implmented by LLM agents. Review the plan carefully in detail and help me to create the prompt other agents will use to perform the implementation plan. They always have to read the comments where the plan is outlined so they have the rigth context (first 4 comments). they must only work on their respective phase and should stick to what the phase is about, avoiding doing extra work. If they find an area of opportunity, they should report it. Once they finish their work, they must update the issue adding a new comment to it with a summary of the work done and any other note that they consider relevant. the summary should be short, I don't want a lot of text to read that is already part of the overall plan. write the prompts to a new markdown file, so I can copy paste. One new requirement not specified in the original plan is that the agents must not use dictionaries to encapsulate data, they must use a class to encapsulate data and provide methods to access it.
