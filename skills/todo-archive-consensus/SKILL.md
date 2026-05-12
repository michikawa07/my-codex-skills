---
name: todo-archive-consensus
description: "Use when maintaining a project plan with TODO.md and ARCHIVE.md: keep TODO.md focused on future work plus one immediate task, and move completed decisions/results into ARCHIVE.md."
---

# TODO / ARCHIVE Consensus

Use this skill when planning or revising work through `TODO.md` and `ARCHIVE.md`.

## Roles

- `TODO.md` is the current forward-looking plan.
  - Keep future work there.
  - Keep exactly one immediate task there whenever actionable work remains.
  - Preserve useful future-task detail there.
  - Do not accumulate completed history there.

- `ARCHIVE.md` is the completed-work record.
  - Move completed task results there.
  - Preserve decisions, rationale, and consequences there.
  - Store settled context there when it no longer belongs in the current plan.

## Workflow

1. Read `TODO.md` and `ARCHIVE.md` if they exist.
2. Identify whether the user is planning, narrowing scope, challenging the plan, completing a task, or archiving results.
3. Keep the immediate task bounded.
4. If the immediate task becomes too broad, narrow it.
5. Move overflow detail into the relevant future-work item instead of deleting it.
6. When the immediate task is completed:
   - archive the result and decisions in `ARCHIVE.md`,
   - remove completed details from `TODO.md`,
   - rewrite `TODO.md` from the new present,
   - choose the next immediate task.

If `ARCHIVE.md` is missing and the workflow is being established, create it with a short purpose note; add entries only for completed content. If no archive style exists, use a dated heading and concise notes for results, decisions, rationale, and consequences.

Choose the immediate task as the smallest coherent action that unblocks the next decision or implementation step. If several tasks are equally plausible, prefer the one closest to the user's latest request and state the assumption briefly.

If overflow detail fits no existing future-work item, create a concise future-work item for it. If no actionable future work remains, say so instead of inventing a next task. Treat ambiguous status as unfinished unless the user or evidence marks it complete; archive only known evidence.

When completion is confirmed but result detail is thin, archive the confirmed facts and note unknowns as unknown instead of reconstructing them.

## TODO.md Shape

`TODO.md` should contain:

- operating note for this workflow,
- future work, with nested detail when useful,
- one immediate task,
- artifacts or outputs for that task,
- decisions needed for that task,
- completion conditions for that task.

Avoid checkbox-style accumulation of completed work.

## Scope Rules

Use these categories:

- Immediate task: bounded, actionable now, coherent as one step.
- Future work: important, but not required to finish the immediate task.
- Archive: completed work, completed decisions, or rationale worth preserving.

When in doubt, prefer a smaller immediate task and richer future-work notes.

## Key Rules

- If the immediate task becomes bloated, narrow it and move the overflow into future work.
- Do not discard useful detail when narrowing scope; preserve it under the relevant future task.
- Move completed information out of `TODO.md` and into `ARCHIVE.md`.
