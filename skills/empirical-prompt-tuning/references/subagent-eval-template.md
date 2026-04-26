# Subagent Evaluation Template

Use this template when dispatching a fresh evaluator for a prompt or skill.

## Evaluator Prompt

```text
You are a fresh executor reading an agent instruction artifact for the first time.
Do not assume any hidden context beyond what is written below.

Artifact under test:
<absolute file path or pasted artifact text>

Scenario:
<one realistic scenario>

Requirement checklist:
1. [critical] <minimum success condition>
2. <normal requirement>
3. <normal requirement>

Task:
1. Execute the artifact against the scenario as written.
2. Produce the requested output or execution summary.
3. End with the exact report structure below.

Report structure:
- Output: <artifact produced or concise execution summary>
- Requirements:
  - 1: pass | fail | partial - <reason>
  - 2: pass | fail | partial - <reason>
  - 3: pass | fail | partial - <reason>
- Ambiguities:
  - <unclear wording or missing decision rule>
- Discretionary fills:
  - <choices you made because the artifact did not decide them>
- Retries:
  - <count and reason>
- Optional runtime metadata:
  - <elapsed time / tool count only if the harness exposes it directly>
```

## Operator Notes

- Run one scenario per fresh agent.
- Keep the checklist fixed across iterations.
- Never give the evaluator your intended answer unless the artifact itself says it.
- Treat recurring discretionary fills as missing instruction, not acceptable variance.
