# ABAP Codex Usage and Development Instructions

## 1. Minimize Codex Usage

Codex usage is limited, so work efficiently.

- Read project instruction and progress files first, especially this `AGENTS.md`.
- Inspect only files relevant to the current task.
- Reuse information already discovered during the current session.
- Do not repeatedly open unchanged files unless necessary.
- Avoid unnecessary repository-wide searches.
- Keep reasoning and implementation focused on the current task.
- If a file's purpose is already understood, do not reread the entire file unless it changed or specific details are required.

## 2. Keep Tasks Focused

Do not turn a small request into a large multi-file redesign.

For each task:

1. Identify the smallest set of files requiring modification.
2. Make the required changes.
3. Test the affected functionality.
4. Fix problems caused by the change.
5. Stop when the requested task is complete.

Do not automatically implement future roadmap features unless Dennis specifically asks to continue.

## 3. Model Strategy

### Luna

Use for:

- Simple edits
- Repetitive coding
- Formatting
- Straightforward HTML, CSS, and template changes
- Small functions
- Simple tests
- Minor cleanup

### Terra — Default

Use for:

- Normal ABAP development
- Web framework development
- Routes and forms
- CRUD and database integration
- API implementation
- Authentication implementation
- Normal debugging and refactoring
- Tests
- Frontend and backend integration

### Sol

Reserve for:

- Difficult architecture decisions
- Complex multi-file bugs
- Difficult debugging where Terra is stuck
- Security architecture and review
- Complicated integrations
- Major design decisions
- Problems requiring deep reasoning

Do not use Sol simply because it is available.

## 4. Escalation Rule

- Start normal development with Terra.
- Continue with Terra when it can solve the task reliably.
- Use Luna when the task is clearly simple and repetitive.
- Escalate to Sol only when deeper reasoning is genuinely required or Terra has difficulty solving the problem.
- After Sol resolves the difficult problem or architectural decision, document the important decision and return normal implementation work to Terra.

Model selection applies where the active Codex environment permits choosing or delegating to these models.

## 5. Maintain Project Continuity

Record important architectural decisions, milestones, dependencies, security requirements, and roadmap changes in the appropriate project documentation or this file.

Maintain a concise record of:

- Project purpose
- Current architecture
- Completed milestones
- Current development phase
- Current task
- Important technical decisions
- Important security decisions
- Known issues
- Next planned step

The record should allow Sol, Terra, or Luna to continue without rediscovering the entire repository.

## 6. Protect Working Code

Before changing existing functionality:

- Understand why the relevant code exists.
- Preserve working behavior unless the task requires changing it.
- Avoid unnecessary refactoring.
- Run relevant tests after changes.
- Check for regressions when appropriate.

Do not rewrite large sections merely to make the code stylistically different.

## 7. Teach While Building

Dennis is learning while building ABAP.

When introducing an important concept:

- Briefly explain what it does.
- Explain why ABAP needs it.
- Identify the important files and functions involved.
- Keep explanations practical and connected to the project.
- Do not overwhelm with unnecessary theory.

The teaching process should gradually help Dennis explain the project independently.

## 8. End-of-Task Summary

At the end of each development task, provide a concise summary containing:

- **Completed:** What was implemented.
- **Files Changed:** Important modified files.
- **Why:** Why the changes were necessary.
- **Tests:** What was tested and whether it passed.
- **Current ABAP Status:** Current roadmap position.
- **Next Step:** Next logical task from the existing roadmap.

Keep this summary concise so future Codex sessions can quickly understand the project state.

## Primary Rule

Continue building the existing ABAP project according to its established roadmap while using the minimum necessary Codex context and model capability. Do not sacrifice code quality, security, testing, or learning merely to reduce usage.

Continue using the established step-by-step development and teaching style. Changing between Sol, Terra, or Luna changes only the model being used—not the roadmap, development process, learning style, or project direction.

