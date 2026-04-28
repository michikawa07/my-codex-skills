---
name: generate-ieee-response-letter
description: Generate an IEEE-style LaTeX responseLetter.tex skeleton from an IEEE review_summary.md. Use when the user asks to convert, draft, or prepare an IEEE reviewer-response letter template from review_summary.md, especially when response fields should be left blank for authors to fill later; if an existing responseLetter.tex is present in the same directory, reuse its preamble, metadata, inputs, and opening title block.
---

# Generate IEEE Response Letter

## Purpose

Create an IEEE response letter LaTeX skeleton from `review_summary.md`. This skill is for IEEE reviewer-response documents, not generic response letters.

Do not generate answer prose. The output is a template: reviewer/editor comments are copied into `itembox` blocks, and each `\paragraph{Response n}` is left empty.

## Inputs and Output

- Read the `review_summary.md` supplied by the user or found at the path they name.
- If `responseLetter.tex` already exists in the same directory as the input summary, read it as the local formatting source.
- Write the requested `responseLetter.tex` path. If no output path is specified, write next to the input summary as `responseLetter.tex`.
- Do not require any additional inputs.

## Base LaTeX

Prefer a same-directory existing `responseLetter.tex` when it exists.

When using an existing `responseLetter.tex`:

- Reuse everything from `\documentclass` through the opening block immediately before the first response section.
- Preserve the existing document class, packages, macros, `\input{...}` lines, author declarations, affiliations, title, date, `\maketitle`, thank-you text, and revised/previous manuscript-title block.
- Treat the first `\section{Response to Comments...}` or equivalent reviewer/editor response section as the start of old response content.
- Discard old response sections and answer text. Rebuild all editor/reviewer comment sections from `review_summary.md`.

When no same-directory `responseLetter.tex` exists:

- Start from `assets/ieee-response-letter-template.tex`.
- Keep its compile-safe placeholder text as ordinary LaTeX text.
- Do not invent author names, affiliations, manuscript titles, paper IDs, or revisions.

## Comment Selection

Include comments that require or reasonably invite an author response:

- Editor-in-Chief comments.
- Senior Editor, Associate Editor, and Editor comments.
- Reviewer sections titled `What are the additional ways in which the paper could be improved`.
- Reviewer sections titled `Comments to the Author`, unless the body says there are no comments.
- Any other reviewer/editor block that contains requests, criticisms, required changes, or questions.

Exclude blocks that are usually descriptive rather than requests:

- `What are the contributions of the paper`.
- Salutations, decision boilerplate, upload instructions, submission links, and signatures.
- Empty/no-comment notices such as `(There are no comments...)`.

If unsure whether a block is a request or only a summary, include it only when it asks the authors to revise, clarify, justify, add, remove, discuss, report, or explain something.

## Section Layout

Use this order:

1. Editor comments, if any are included.
2. Reviewer 1 comments.
3. Reviewer 2 comments.
4. Continue by reviewer number.

For editor comments, use:

```tex
\section{Response to Comments of Editors}
We thank the Editor-in-Chief and the Editors for their careful evaluation of our paper. Our responses to individual comments are as follows.
```

For reviewer comments, use:

```tex
\section{Response to Comments of Reviewer 1}
We would first like to thank you for your careful reading of our paper and your constructive and helpful comments. Our responses to individual comments are as follows.
```

For Reviewer 2 and later, use:

```tex
\section{Response to Comments of Reviewer 2}
We thank you for the constructive and helpful comments. Our responses to individual comments are as follows.
```

Insert `\newpage` before each top-level response section after the opening manuscript-title block.

## Comment Blocks

Number comments independently within each owner:

- Editors: `Comment E-1`, box title `Comment 1 of Editors`.
- Reviewer 1: `Comment 1-1`, box title `Comment 1 of Reviewer 1`.
- Reviewer 2: `Comment 2-1`, box title `Comment 1 of Reviewer 2`.

Use this exact skeleton when the source comment has an explicit short title:

```tex
\subsubsection*{Comment 1-1}
	\begin{itembox}[l]{Comment 1 of Reviewer 1: Short title}
		Reviewer comment text.
	\end{itembox}
	\paragraph{Response 1}

```

Leave one blank line after each `\paragraph{Response n}`. Do not add TODO markers, draft answers, explanatory comments, or placeholder text in the response area.

Do not infer short titles. Add `: Short title` to the `itembox` title only when the source text contains an explicit numbered-item heading, such as `1. Simplification of Technical Jargon:`. If a comment is a paragraph without such a heading, use only `Comment n of Reviewer r` or `Comment n of Editors`.

Normalize explicit short titles to sentence case to match the local IEEE response-letter style: keep the first word capitalized and lowercase later ordinary words. Preserve acronyms and proper nouns. For example, write `Simplification of technical jargon`, not `Simplification of Technical Jargon`.

## Splitting Comments

When a reviewer provides a numbered list of independent improvement items, split each numbered item into its own comment. Use the numbered-item heading as the short title when it has one.

Example Markdown:

```md
1. Simplification of Technical Jargon:
    Simplify the complex technical terms...
```

Output:

```tex
\subsubsection*{Comment 1-1}
	\begin{itembox}[l]{Comment 1 of Reviewer 1: Simplification of technical jargon}
		Simplify the complex technical terms...
	\end{itembox}
	\paragraph{Response 1}

```

When a reviewer provides multiple paragraphs without numbering, split by clearly separate requests or topics. Keep each paragraph as one comment if the paragraphs are independent. Do not invent topic labels for these comments.

When a reviewer provides a "minor comments" list after an introductory sentence, keep the whole minor-comments list as one comment and convert the list to `enumerate`.

## Markdown to LaTeX

Preserve the reviewer's wording as much as possible, but make it compile in LaTeX.

- Convert straight double quotes around quoted phrases to LaTeX quotes: ``...''.
- Escape literal percent signs as `\%`.
- Escape ampersands as `\&`.
- Preserve math-like reviewer text as literal reviewer wording when it is readable. For example, convert `u^i` to `u\^i`; do not rewrite it as `\(u^i\)` unless the source already uses LaTeX math.
- Write prose with one complete sentence per source line, but determine sentence boundaries semantically; do not mechanically split at every period because periods may appear inside abbreviations, initials, references, decimals, ellipses, section/figure labels, quoted phrases, and LaTeX commands.
- Preserve meaningful source line breaks inside reviewer comments when they separate phrases, policy notices, or continuation text. Do not collapse an IEEE policy notice and surrounding continuation text into one long line.
- Do not insert blank lines inside an `itembox` unless they are structurally needed before or after a nested LaTeX environment.
- Convert Markdown numbered lists inside a single comment to:

```tex
		\begin{enumerate}
			\item ...
		\end{enumerate}
```

- Remove Markdown bold markers such as `**...**` unless they are part of the reviewer's literal text.
- Do not translate comments.

## Final Check

Before finishing, inspect the generated `.tex` and confirm:

- No contribution-summary blocks were included.
- No no-comment notices were included.
- Every included comment has an empty response paragraph.
- Editor comments, if present, come before reviewer comments.
- Comment numbering is sequential within each owner.
- If an existing same-directory `responseLetter.tex` was present, its preamble, metadata, `\input` lines, and opening manuscript-title block were preserved.
- If no existing same-directory `responseLetter.tex` was present, the output uses the compile-safe fallback placeholders from the asset.
- The skill directory still contains no generation scripts.
- The file ends with `\end{document}`.
