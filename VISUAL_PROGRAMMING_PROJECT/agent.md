# Agent Working Agreement

## Workflow

Always use subagents to carry out tasks. The coordinating agent manages handoffs, shares relevant context, checks completion gates, and summarizes status; it does not directly implement product changes.

For each task, follow these stages:

1. **Plan:** Start a planning subagent to define the goal, acceptance criteria, risks, and expected file list. Use its specification to guide the work.
2. **Develop:** Start a developer subagent to implement the approved specification and report the files changed, a brief change summary, and any unresolved issues.
3. **Review:** Start a reviewer subagent to assess requirement coverage, scope, correctness, maintainability, and regression risk. The reviewer must state whether the work is approved and identify issues with their severity.
4. **Revise when needed:** If the review raises substantial or complex issues, send the findings back to the developer. After revisions, run the review again. Repeat until the reviewer approves the work or a blocker is clearly documented.
5. **Test:** Start a unit tester subagent after review. It should verify behavior relevant to the change and report the test scope, results, and unresolved issues. If tests fail, send the findings to the developer, then repeat review and testing after the fix.
6. **Completion gate:** Mark a task complete only when the reviewer has approved it and the tests have passed. Otherwise, keep it open and report its current status and blockers.
7. **Activity record:** After completion, record a concise, traceable summary in `activity.md`, including the task, changed files, review decision, test results, and completion status.

Do not paste implementation details, full specifications, or test output into the user conversation. The final response must contain only a one-line summary; keep any necessary detail in `activity.md`.

## Handoff Responsibilities

- The planning subagent returns the specification, acceptance criteria, risks, and file list.
- The developer subagent returns the files implemented, a concise change summary, and any outstanding issues.
- The reviewer subagent returns an approval decision, findings with severity, and whether revision is needed.
- The unit tester subagent returns the coverage checked, pass or fail result, and any failures or limitations.
- The coordinating agent provides each subagent with the context it needs and uses the results to schedule revisions, re-review, testing, and completion tracking.

## Project Context and Boundaries

This project aims to provide a card-based visual programming experience. Users build programs by dragging, configuring, and connecting cards, while an agent completes bounded implementation work from card templates. Follow the project's card model, project graph, validation layer, runtime preview, and publishing or export boundaries. Keep changes scoped, inspectable, and reversible. Prioritize the initial focus on simple projects, and account for relevant configuration, connections, dependencies, permissions, errors, and preview behavior when changing a capability.

If the project documentation does not establish the behavior, acceptance criteria, or authorized scope, flag the ambiguity during planning rather than expanding the task independently.
