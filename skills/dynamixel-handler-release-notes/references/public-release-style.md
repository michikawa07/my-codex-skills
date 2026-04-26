# DynamixelHandler Public Release Style

Use this file as a compact fallback summary of the repository's published GitHub Releases. If the current release pages differ, prefer the actual published pages.

## Observed Traits

- Language: Japanese
- Tone: concise and public-facing
- Output target: GitHub Releases body, not an internal release memo
- Typical opener: `以下の変更を加えました．`
- Typical structure: a small number of titled sections

## Common Section Names

- `軽微な変更`
- `機能追加`
- `動作改善`
- `デバッグ・修正`
- `互換性に影響のある変更`
- Small releases may use only one section, such as `軽微なバグ修正`.

## What Published Notes Usually Do

- Summarize user-visible changes only
- Use short bullets
- Use nested bullets to enumerate notable sub-items
- Keep implementation detail only when it helps explain public behavior
- Mention message fields, topics, parameters, or commands when they are part of the public interface

## What Published Notes Usually Avoid

- commit review logs
- explicit methodology sections
- lists of reviewed commits
- separate verification sections
- broad residual-risk sections unless the release body itself needs them
- exhaustive changelog coverage

## Compression Rule

If the internal analysis finds many changes, compress them to the subset that best matches what the repository would realistically publish as release notes.
