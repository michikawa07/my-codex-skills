---
name: quote-revised-manuscript
description: Fill, audit, or repair response-letter quotation blocks by copying only the corresponding revised text from a manuscript source such as main.tex. Use when Codex is asked to replace LaTeX response-letter TODO quotations, cite modified manuscript paragraphs in reviewer responses, verify whether quotations come from actual manuscript changes, add chapter/paragraph references for response letters, or enforce ellipsis formatting for partial manuscript excerpts.
---

# Quote Revised Manuscript

## Purpose

Use this skill to complete reviewer-response quotations from the revised manuscript without inventing context. The central rule is: quote only text that corresponds to actual manuscript changes, and keep the response-letter structure consistent.

## Required Workflow

1. Identify the response file, manuscript file, and requested comment range.
   - Common files are `review/.../responseLetter.tex` and `main.tex`.
   - If the user did not specify a manuscript root and `main.tex` exists, use `main.tex` as the root. If no root is specified and `main.tex` does not exist, stop and ask for the manuscript root.
   - Discover included manuscript files recursively from the root by reading uncommented `\input{...}` and `\include{...}` commands. Treat a command as commented out if the first non-space character on the source line is `%`.
   - Append `.tex` when an included path has no extension. Ignore conditional compilation branches unless the user identifies the active branch; if a needed quote depends on an ambiguous conditional branch, stop and ask.
   - Respect exclusions such as "ignore Comment 1-5" or "do not quote Comment 4-4".

2. Inspect manuscript changes before choosing quotes.
   - Identify every manuscript source file that can contain the revised text. Include `main.tex` and any relevant `\input`/`\include` files.
   - Compare the current working tree against `HEAD` for each relevant manuscript file. Treat staged and unstaged changes as the same current revision:
     ```bash
     git diff HEAD -- <manuscript-file>
     ```
   - Use `git diff HEAD -- <manuscript-file>` as the source of truth unless the user explicitly names another baseline.
   - Do not quote an unchanged paragraph merely because it gives useful context.

3. For each comment, map the response claim to changed manuscript text.
   - Break the response into individual claims that need manuscript support.
   - For each claim, classify support from the diff as `exact`, `partial`, or `none`.
     - `exact`: the claim is directly supported by one or more added diff lines (`+`, excluding `+++`) or by the added side of a nearby remove/add replacement pair.
     - `partial`: added diff lines support only part of the claim, or the claim also needs unchanged manuscript text.
     - `none`: no added/replacement diff line supports the claim.
   - Quote only `exact` support.
   - If support is `partial` or `none`, do not broaden the quote to nearby unchanged text. Stop and ask the user before editing that comment unless the user explicitly instructed to leave unresolved items.
   - If the user explicitly instructed to leave unresolved items, replace the quotation placeholder with exactly `\todo{NEEDS MANUSCRIPT CHANGE: <reason>}` and keep the reason under 12 words.
   - Find the exact changed paragraph(s) in the relevant manuscript source file.
   - Quote a full paragraph only when every prose source line in the quoted paragraph is an added diff line or the added side of a replacement pair. Otherwise quote a fragment.
   - For a partially revised paragraph, quote only the added/modified sentence or clause plus the minimum unchanged words needed for grammar.
   - If no changed text supports the response, do not invent a quotation. Ask or leave the quote absent according to the user's instruction.

4. Replace chapter/paragraph placeholders near the quote.
   - Replace placeholders like `\todo{0章0段落}` with concrete locations such as `III-C章2段落`, `V-C-2)章3段落`, or `VI-B章1段落`, using the section-number style of the target manuscript and response letter.
   - Make the location point to the quoted manuscript text, not to a nearby explanatory paragraph.
   - Do not hardcode subsubsection notation. Derive it from the target manuscript's document class, compiled/PDF numbering, or existing response-letter usage. For IEEE-style manuscripts where subsubsections appear as `V-B-3)`, write `V-B-3)章2段落`; for formats without the parenthesis, do not add one.
   - Count paragraphs in the compiled source order after resolving uncommented `\input`/`\include` files.
   - Count within the nearest numbered manuscript section, subsection, or subsubsection containing the quoted text.
   - Strip comment-only lines before detecting paragraph breaks. A line whose first non-space character is `%` is invisible for paragraph counting and does not create a blank paragraph boundary.
   - Treat `\noindent` as a formatting command, not as prose and not as a paragraph boundary. Remove only the command token, then judge the remaining visible text. If `\noindent` appears immediately after a section heading and the same line or following visible line contains prose, that prose is paragraph 1 of the new section. Never let `\noindent` merge text across a section boundary.
   - A counted prose paragraph is a contiguous block of visible prose in source order, outside `figure`, `table`, `itemize`, `enumerate`, and bibliography environments.
   - Display math environments such as `equation`, `align`, and `gather` do not create counted paragraphs. If prose before and after display math is connected without a real blank line after comments are stripped, count it as one prose paragraph.
   - If the quote is inside a list item, theorem-like environment, caption, or equation-only block, do not invent a paragraph number. Use the environment/item label if one exists, otherwise stop and ask for the desired location wording.

5. Preserve response-letter semantics.
   - Keep one comment's answer structure aligned with the user's existing style: response text, changed location, then quotation.
   - When two different manuscript regions are needed, use separate `quotation` blocks or clearly separate them in the response. Do not mix unrelated sections inside one quotation block.
   - Do not add extra claims, references, figures, or bibliography entries unless the user asked.

## Quotation Rules

- Quote only revised or newly added manuscript text from the relevant diff.
- Do not quote unchanged setup/background text unless the user explicitly asks for surrounding unchanged context.
- A full paragraph quote is allowed only when every prose source line in the quoted paragraph is an added diff line or the added side of a replacement pair.
- If omitted text exists before the quoted fragment within the same paragraph, start with:
  ```tex
  \ldots \\
  ```
- If omitted text exists after the quoted fragment within the same paragraph, end with:
  ```tex
  \\ \dots
  ```
- If two quoted fragments from the same paragraph are separated by omitted text, insert `\ldots \\` between them.
- If the quotation contains the whole visible prose paragraph, do not add `\ldots \\` or `\\ \dots`.
- Use separate `quotation` blocks for non-contiguous paragraphs unless the existing response for the same comment already uses one block for multiple paragraphs.
- Treat a TODO as a quote placeholder only when one of these is true:
  - it appears between `\begin{quotation}` and `\end{quotation}`;
  - it is on the nearest nonblank line immediately before `\begin{quotation}`;
  - it is on the nearest nonblank line immediately after `\end{quotation}`;
  - its text explicitly requests quoted revised manuscript text, such as `Done` or `該当部分を持ってくる`.

## Optional Add/Delete Markup

Apply `\add{}` and `\del{}` markup only when the user explicitly asks for add/delete markup, diff markup, or equivalent wording. Do not add this markup during ordinary quotation filling or auditing.

When add/delete markup is requested:

- Use `git diff HEAD -- <manuscript-file>` as the source of truth for the old and revised text.
- Edit only the response-letter quotation blocks requested by the user unless they ask for a broader range.
- Keep unchanged surrounding quote text unmarked.
- Represent deleted manuscript text with `\del{...}` and added manuscript text with `\add{...}`.
- Preserve the revised quotation text after ignoring `\del{...}` content; the visible added/current side must still match the revised manuscript quote.

Granularity rule:

1. Prefer the manuscript diff's visible color spans.
   - If a manuscript diff file exists, such as `main-diffHEAD.tex`, use it to decide the `\add{}` and `\del{}` boundaries.
   - Read the actual visible colored text, including commands such as `\DIFadd{...}`, `\DIFdel{...}`, `\DIFaddFL{...}`, and `\DIFdelFL{...}`.
   - Do not treat the whole outer range of `\DIFaddbegin ... \DIFaddend` or `\DIFdelbegin ... \DIFdelend` as one colored unit. Those wrappers can contain unchanged text and several independent colored spans.
   - If the `.tex` diff is hard to interpret, inspect the compiled diff PDF or the local manuscript context before deciding the colored spans.

2. Compare one response-letter quotation block at a time.
   - For each requested quotation block, locate the same revised text in the manuscript and the corresponding old text from the diff.
   - Compare the response-letter markup against the manuscript diff's colored spans in source order.
   - Treat adjacent response-letter `\add{}` or `\del{}` spans as one unit only when they are separated by whitespace or unchanged punctuation that belongs to the same continuous edit.

3. Make response-letter units match the manuscript diff units.
   - If one response-letter `\add{...}` or `\del{...}` covers multiple independently colored manuscript-diff spans, split it.
   - If several response-letter spans divide one continuous manuscript-diff colored span, merge them.
   - Leave unchanged words outside `\add{}` and `\del{}` even when they are in the same sentence as a change.
   - Do not mark a whole sentence only because a local phrase changed inside that sentence.
   - Use sentence-level markup only when the manuscript diff colors the whole sentence, or when the entire sentence was added or deleted.

4. Fallback when no manuscript diff file exists.
   - Infer units from `git diff HEAD -- <manuscript-file>`.
   - Prefer clause-level units bounded by punctuation: sentence start to comma, comma to comma, comma to period, semicolon to comma/period, or colon to comma/period.
   - For very local edits inside a clause, use a short phrase-level unit rather than expanding to the whole clause.
   - Do not copy raw character-level or single-token diff noise unless the single token is the complete semantic change.
   - Do not collapse multiple independent edits into one large sentence-level span.

Examples:

```tex
% Local replacement inside a sentence: correct
The stimulation intensity was \del{set as an empirical constant}\add{empirically fixed}, so arbitrarily specified weights could not be presented.

% Local replacement inside a sentence: too coarse
\del{The stimulation intensity was set as an empirical constant, so arbitrarily specified weights could not be presented.}\add{The stimulation intensity was empirically fixed, so arbitrarily specified weights could not be presented.}

% Whole added sentence: correct only when the manuscript diff colors the whole sentence
\add{Sierotowicz and Castellini [15] proposed a control method for omnidirectional endpoint force generation via EMS based on a musculoskeletal model.}
```

- If `\del{...}` contains math or fragile macros and compilation fails because `\sout` cannot process them, wrap only the fragile math/macro fragment in `\mbox` inside `\del`, for example `\del{\mbox{$\Wtar$}}` or `\del{\mbox{\SI{1.0}{kg}}}`.
- Do not replace failed deletion markup with plain `\textcolor{red}{...}`. If `\mbox` is unsuitable, leave the fragile fragment unmarked or ask the user how to display it.

## LaTeX Conversion Rules

Response letters often cannot use manuscript-only macros or citation commands directly.

- Convert manuscript `\figref{...}` to the printed figure form used in the response letter, such as `Fig.~6` or `Fig.~7`.
- Convert manuscript `\cite{...}` to hardcoded citation numbers from the paper/PDF/bbl, such as `[32]`. Do not add bibliography entries to the response letter.
- Convert figure, table, equation, and citation references only when the printed number can be verified from the compiled PDF, `.aux`, `.bbl`, or existing response-letter usage.
- If a printed number is not verifiable, stop and ask. Do not guess figure, table, equation, or citation numbers.
- Keep math macros that are already available in the response letter. If unsure whether a macro is available, inspect the response preamble before changing it.
- Do not silently introduce new macros or packages.

## Verification Checklist

Before finishing:

- Every quotation line can be traced to a relevant changed line or changed paragraph in `git diff HEAD -- <manuscript-file>`.
- No unchanged-only paragraph was added as a quotation.
- All required `\todo{Done, ...}` quote placeholders in the requested range were replaced.
- All required `\todo{0章0段落}` placeholders in the requested range were replaced with concrete locations.
- Partial paragraph quotes have `\\ \dots` or `\ldots \\` as required.
- `\begin{quotation}` and `\end{quotation}` counts match.
- No `\cite{...}` or unsupported manuscript-only macros were introduced.
- Do not compile unless the user asks or the task explicitly requires validation.
