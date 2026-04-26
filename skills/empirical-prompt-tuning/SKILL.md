---
name: empirical-prompt-tuning
description: Evaluate and harden an agent-facing prompt, skill, slash command, instruction block, or workflow by handing it to fresh agents, collecting ambiguity reports plus outcome metrics, and iterating until the results stabilize. Use when Codex needs to improve a newly written or heavily revised prompt/skill, diagnose whether failures come from unclear instructions, or increase reproducibility for high-value automation.
---

# Empirical Prompt Tuning

Improve prompts by testing them on fresh agents rather than re-reading them yourself. Keep scenarios fixed, collect both executor-side ambiguity reports and operator-side outcome checks, patch one theme at a time, and stop only when new ambiguity stops appearing.

## Quick Start

1. Freeze the artifact under test.
2. Check that the frontmatter, title, and body describe the same scope.
3. Define 2-3 fixed scenarios: one median case and 1-2 edge cases.
4. Define a checklist with 3-7 items per scenario and mark at least one item as `[critical]`.
5. Run each scenario on a fresh agent with the template in `references/subagent-eval-template.md`.
6. Record:
   - requirement results (`pass`, `fail`, `partial`)
   - unclear instructions
   - places where the agent filled gaps with its own judgment
   - retry count
   - optional runtime metadata if the harness exposes it
7. Patch the smallest useful ambiguity.
8. Re-run on fresh agents. Do not reuse the prior evaluator.

## Delegation Rules

- Use fresh agents only when the user explicitly asks for agent-based validation, parallel evaluation, delegation, or explicitly invokes this skill.
- If delegation is not allowed in the current harness, explain the workflow and offer a local-only review instead.
- Prefer `fork_context: false` so the evaluator does not inherit hidden context from the current conversation.
- Pass the artifact path, scenario, and checklist explicitly in the delegated prompt.

## Workflow

### 1. Align the artifact before testing

- Read the artifact's trigger description and body separately.
- Remove scope drift first. If the description promises behavior that the body does not support, fix that before agent evaluation.
- Do not treat a passing result as valid if the evaluator had to infer missing scope from the description.

### 2. Build fixed scenarios

- Use realistic scenarios that represent how the prompt or skill will actually be used.
- Keep the scenarios fixed across iterations.
- Include at least one edge case that is likely to expose ambiguity.
- Write the checklist before evaluation and do not move the goalposts afterward.

### 3. Dispatch clean evaluators

- Launch one fresh agent per scenario.
- Give the agent only the artifact under test, the scenario, and the checklist.
- Do not pass your diagnosis, suspected fix, or preferred answer unless the artifact itself contains it.
- Ask for a structured report exactly once at the end.

### 4. Judge from both sides

- Treat executor self-report as evidence of ambiguity, not as final success criteria.
- Treat `[critical]` items as binary gates. If any critical item is not `pass`, mark the scenario as failed.
- Compute accuracy from the whole checklist:
  - `pass = 1`
  - `partial = 0.5`
  - `fail = 0`
- Record retries separately from accuracy.
- If agent usage metadata such as elapsed time or tool counts is available in the harness, record it. If not, omit it rather than inventing a proxy.

### 5. Patch one theme per iteration

- Fix the smallest set of wording problems that explains the observed failure.
- State which checklist item or ambiguity the patch addresses.
- Avoid mixing unrelated improvements into the same iteration.
- Re-run the same scenarios on fresh agents after every patch.

### 6. Stop with evidence

- Stop when two consecutive rounds produce no new ambiguity on the fixed scenarios and accuracy has plateaued.
- Use one holdout scenario if the prompt matters enough to justify it.
- Call out the residual risk explicitly if the artifact still depends on unstated assumptions.

## Codex Execution Notes

- Use `spawn_agent` for delegated evaluation when allowed.
- Use `wait_agent` only when the next step depends on the result.
- Prefer parallel evaluators for independent scenarios.
- Ask evaluators to list ambiguities, discretionary fills, retries, and checklist results in plain text so the parent agent can compare runs quickly.
- If the artifact under test is a local file, include its absolute path in the evaluator prompt.

## Output Format For Each Evaluation Round

Produce a compact summary with:

1. artifact under test
2. scenarios run
3. per-scenario result:
   - success or failure
   - checklist score
   - failed critical items
   - ambiguities
   - discretionary fills
   - retries
   - optional runtime metadata
4. smallest next patch
5. stop or continue decision

## Reference

- Use `references/subagent-eval-template.md` as the base prompt template for fresh evaluators.
