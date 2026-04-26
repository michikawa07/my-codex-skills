---
name: dynamixel-handler-release-notes
description: Draft public release notes for DynamixelHandler_ in the same style as the repository's existing GitHub Releases. Use when Codex needs to write a release body for DynamixelHandler_, summarize a tag range into short Japanese sections such as `軽微な変更`, `機能追加`, `動作改善` or `デバッグ・修正`, and keep the output close to the repository's published release-note format rather than an internal review memo.
---

# Dynamixel Handler Release Notes

Write the public release body that would fit naturally on the DynamixelHandler_ GitHub Releases page. Review diffs and shipped artifacts carefully, but keep that analysis internal. The default output is the public note itself, in Japanese, with the same tone, sectioning, and compression level as this repository's existing releases.

## First Principle

This skill is not a generic release-note generator. It is a DynamixelHandler_-specific GitHub release writer.

- Match the repository's existing public release style before matching any generic documentation convention.
- Treat commit review and shipped-artifact verification as internal evidence gathering.
- Do not expose internal audit structure in the default output unless the user explicitly asks for it.
- Do not use the target release body itself as generation input when the target release is already published. Use nearby published releases only as style references, and use the git history plus shipped artifacts as the content source.

## Quick Start

1. Identify the exact release range the user asked for.
2. Inspect the repository's recent published GitHub Releases first.
3. Infer the current public style from those releases:
   - language
   - section names
   - note length
   - bullet density
   - level of implementation detail
4. Review the diff range and shipped artifacts.
5. Compress the findings into a short public release body that matches the existing DynamixelHandler_ release style.

## Public Style Rules

- Default to Japanese unless the user explicitly asks for another language.
- Prefer the repository's established heading pattern, such as:
  - `軽微な変更`
  - `機能追加`
  - `動作改善`
  - `デバッグ・修正`
  - `互換性に影響のある変更`
- Start from the public note itself. Do not prepend internal sections such as:
  - target range
  - reviewed commits
  - verification performed
  - residual risks
- Keep the body compact. Published DynamixelHandler_ releases are concise, not exhaustive.
- Prefer a short introductory line such as `以下の変更を加えました．` when it matches the surrounding releases.
- Use flat bullets with short nested bullets only when the published releases use them naturally.

## Shape Selection Rules

- For a tiny release:
  - prefer no opener or one short opener
  - prefer one short section
  - if the change is mostly a small bug fix, prefer a heading such as `軽微なバグ修正`
  - if the change is small but mixed, prefer `軽微な変更`
- For a medium release:
  - prefer a short opener such as `以下の変更を加えました．`
  - prefer 2-4 short sections
  - prefer only the headings that map cleanly to the actual public changes
- For a broader release:
  - keep the note compact, but allow several short sections
  - allow nested bullets only when they enumerate public sub-items more clearly than repeating top-level bullets
- Do not choose section count by commit count alone. Choose it by how many distinct public-facing change groups the repository would realistically publish.
- If uncertain between a flatter and a more expanded structure, prefer the more compressed public note.

## Workflow

### 1. Learn the current repo style first

- Read 2-3 nearby GitHub Releases from this repository before drafting.
- Use published releases only to learn style: language, sectioning, note length, opener feel, and bullet density.
- If the target release is already published, do not read its body as source material for generation. Treat the target release body as evaluation-only material after drafting.
- When browsing is available, inspect nearby GitHub Releases pages directly before drafting.
- If browsing is unavailable or the release pages cannot be fetched, fall back to `references/public-release-style.md`.
- Use `references/public-release-style.md` as the fallback summary of the observed style.
- If the current published releases differ from the reference summary, prefer the published releases.

### 2. Review the actual changes

- Read the diff for each relevant commit in the requested range.
- Do not summarize from commit titles alone.
- Inspect shipped artifacts in the final tagged tree.
- Use `references/shipped-artifacts-checklist.md` while verifying the final tree.
- Treat git history, shipped configs, shipped docs, shipped examples, message definitions, and launch files as the content source of truth.

### 3. Decide what belongs in the public note

- Include externally visible behavior, API or message changes, config-default changes, sample-usage changes, launch-flow changes, and compatibility-relevant behavior.
- Exclude internal-only implementation details unless users can observe the effect.
- Exclude commit lists, verification notes, and methodology unless the user explicitly asks for an internal handoff or audit memo.
- Prefer the level of detail used in the repository's published releases, even when the internal analysis was broader.

### 4. Choose sections the way this repo does

- Use only the sections that fit the actual release.
- Do not force every release into the same headings.
- When the change is small, one short section may be enough.
- When the release is broad, use the small set of headings already established by the repository's published releases.

### 5. Write bullets in the repo's public tone

- Keep bullets short and concrete.
- Name the public-facing subject first.
- Prefer user-facing behavior over internal mechanism.
- Use nested bullets when the published releases use them to enumerate sub-items or conditions.
- Avoid turning the note into a design review, a changelog dump, or a test report.

## Internal Review Rules

These rules guide analysis, not default output.

- Distinguish between `implemented in code` and `reachable in the shipped package`.
- If code exists but shipped params, defaults, docs, or examples prevent normal use, reflect that in the public wording only if it materially affects users.
- Cross-check user-visible claims against tests or regression notes when available.
- If a change is minor in code but large in shipped examples, docs, config defaults, or interface files, treat it as user-visible.
- If the target release is already published, compare your drafted output against the published body only after generation, and only as a validation step.

## Output Modes

### Default

Produce only the public GitHub release body, matching the repo's established style.

### Only When Explicitly Requested

Add supporting sections such as:

- commit review summary
- verification performed
- compatibility risk memo
- internal rationale for wording

Do not add those sections by default.

## Parallel Review

- If the user explicitly asks for sub-agent or parallel review and the harness allows it, use sub-agents only for internal evidence gathering.
- Keep the final public note single-voiced and stylistically consistent with the repository's published releases.

## Reference

- Read `references/public-release-style.md` for the observed public release style.
- Read `references/shipped-artifacts-checklist.md` for internal verification of shipped behavior.
