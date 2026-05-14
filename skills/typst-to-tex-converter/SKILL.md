---
name: typst-to-tex-converter
description: Convert a Typst manuscript or document into TeX/LaTeX while preserving the Typst source meaning and adapting output syntax to the destination TeX style. Use when the user asks to translate, migrate, port, or convert `.typ` content into `.tex`, especially when an existing TeX file or template should be reused.
---

# Typst to TeX Converter

## Purpose

Convert Typst content into TeX/LaTeX. The source Typst file defines document content and structure; the destination TeX context defines the output style.

This skill is a conversion workflow, not a Typst or TeX syntax reference. Use official Typst, TeX, LaTeX, class, and package documentation for command syntax when needed instead of relying on memorized or invented mappings.

When the user asks for a plain `.tex` file without specifying raw Plain TeX, produce LaTeX.

For official documentation, prefer official online documentation when browsing is available and local installed documentation such as `texdoc` for TeX packages when browsing is not needed. If official documentation is unavailable, report that limitation instead of guessing package syntax.

Built-in LaTeX constructs provided by the selected class may be used without a package lookup. Package commands, class-specific commands, and non-core environments require destination inspection or official documentation.

## Source Of Truth

Use three sources of truth:

- Typst source: content, order, headings, labels, references, comments, equations, figures, tables, lists, and layout intent.
- Destination TeX context: document class, template scaffold, packages, macros, reference commands, math environments, figure style, list style, indentation, and build workflow.
- Official documentation: exact syntax and package behavior for Typst, TeX/LaTeX, classes, and packages.

If these sources conflict and the resolution is not mechanical, stop and ask the user.

## Workflow

1. Inspect the Typst source before editing.
2. Inspect the destination TeX file or template before editing, if one exists.
3. Identify protected destination scaffold that is not part of content conversion, and record it by visible markers, line ranges, or named regions before editing.
4. Split the source into small intervals aligned to headings, figures, equations, lists, or comment blocks.
5. Convert one interval at a time.
6. For each construct, use the resolution procedures below instead of a fixed global mapping table.
7. Verify the converted interval before moving to the next interval.
8. Compile or run the existing TeX build command after meaningful conversion chunks.

Use the smallest interval that can be converted and checked as one coherent unit. If one heading contains several independent figures, equations, lists, or comment clusters, split at those construct boundaries.

## Destination Style Resolution

Before emitting a TeX construct:

1. Find the same construct class nearby in the destination TeX, if available.
2. Reuse the destination's existing class, package, macro, environment, and indentation conventions.
3. If no local convention exists, consult official documentation for the relevant TeX command, class, or package.
4. If adding a package, changing the template, or changing the build toolchain appears necessary, stop and ask.

When no destination TeX file or template exists and the user asked for a plain TeX/LaTeX output:

1. Treat a minimal standalone LaTeX document as the destination style.
2. Use the standard `article` class unless the user explicitly asks for another standard class or the source metadata explicitly declares another document type.
3. Add only installed, general-purpose TeX-distribution packages that are directly required to represent constructs present in the Typst source.
4. Treat publisher, journal, thesis, house-style, uncommon, or purpose-specific packages as policy choices that require user confirmation.
5. Do not invent a publisher, journal, thesis, or house template.
6. Consult official documentation before using package commands.
7. Stop before making layout policy choices not implied by the source request.

If it is unclear whether a package is installed, general-purpose, or directly required, treat it as a decision point and ask.

When checking package availability, use the local TeX installation if available, for example `kpsewhich package.sty`. If availability cannot be checked, report that uncertainty instead of assuming the package exists.

## Construct Resolution

Use these procedures to decide how to convert constructs. Do not encode or invent exhaustive Typst-to-TeX syntax tables inside this skill.

### References

For each Typst reference:

1. Resolve the referenced label in the Typst source inventory.
2. Classify the target as equation, figure, table, section, subfigure, citation, or other.
3. Inspect the destination TeX for the established reference style for that target class.
4. Emit the reference using the destination style.
5. Stop if the target class or destination style cannot be determined.

### Labels

For each Typst label:

1. Preserve the label identity exactly unless TeX syntax makes that impossible.
2. Place the TeX label on the corresponding converted construct.
3. Update references to the preserved label.
4. If exact preservation is impossible, propose the smallest reversible spelling change and stop before applying it.
5. Stop before renaming labels for style consistency.

### Comments And Notes

For each Typst comment, commented-out block, or note:

1. Bind it to the nearest following, enclosing, or explicitly annotated Typst construct.
2. Convert it to an appropriate TeX comment or existing note mechanism.
3. Place it adjacent to the corresponding converted TeX construct.
4. Preserve the original text verbatim when it is inside a TeX comment.
5. Escape or adapt comment text only when it must become active TeX content.

### Math

For each Typst math block or inline expression:

1. Preserve the mathematical meaning, expression order, labels, and reference targets.
2. Inspect the destination TeX for established math environments and notation macros.
3. Use official package documentation for unfamiliar math commands.
4. Stop if preserving the notation requires a semantic choice not present in the source or destination context.

### Figures And Tables

For each Typst figure, table, or grouped figure:

1. Extract the logical structure: parent object, child objects, captions, labels, image paths, layout ratios, spacing, and placement intent.
2. Inspect the destination TeX for the established figure, table, caption, and subfigure mechanisms.
3. Emit a TeX structure that preserves the extracted logical structure.
4. Stop if preserving the structure requires a new package or layout policy decision.

A layout policy decision is any choice that changes or newly defines grouping, child-label representation, caption/subcaption model, float placement policy, column-ratio approximation, gutter interpretation, visual order, or package mechanism beyond what the source and destination context already determine.

If the destination TeX has neither subfigure examples nor an existing subfigure-related package or macro, treating a grouped figure as subfigures is a layout policy decision.

When stopping for a layout decision, report the extracted Typst facts, observed destination TeX facts, the unresolved representation choice, and the minimum user decision needed.

For any stop condition, report: the source construct, relevant Typst facts, relevant destination TeX facts, candidate choices if they are known, why the skill cannot choose mechanically, and one concrete question for the user.

Do not modify the destination file with a partial placeholder after a stop condition is reached. Candidate choices in the stop report must come from the destination context or official documentation; do not invent them.

### Lists

For each Typst list:

1. Preserve item text, item order, nesting, numbering, indentation intent, and spacing intent.
2. Inspect the destination TeX for list packages and list style.
3. Use the destination list mechanism to reproduce the visible structure.
4. Stop if the required numbering or spacing cannot be represented by the available local style.

### Units, Symbols, And Package Commands

For units, symbols, and package-specific commands:

1. Determine the semantic role from the Typst source.
2. Inspect the destination TeX for existing package usage and notation style.
3. Consult official package documentation for the exact command syntax.
4. Emit syntax consistent with the destination style.
5. Stop if multiple TeX notations are plausible and the destination context does not choose one.

## True No-Op Prohibitions

These are actions to avoid entirely, not alternate methods to replace with a different method:

- Do not paraphrase or summarize source content.
- Do not invent source content.
- Do not rename labels for style consistency.
- Do not delete destination template scaffold during content conversion.
- Do not change the build toolchain without explicit user instruction.
- Do not make a package, class, or template policy change without explicit user instruction.

## Interval Verification

Before leaving each interval, verify:

- Source content appears in the converted output without meaning changes.
- Labels and references preserve identity and target.
- Comments and notes are placed at corresponding locations.
- Equations, figures, tables, and lists preserve logical structure.
- Destination TeX style is followed.
- Protected scaffold was not modified.
- Any compile error is attributable to the current interval before changing anything else.

An interval is verified only when every applicable item above is checked against the source and destination text. If a check cannot be performed, keep the interval open and report the blocker.

## Build Command Resolution

Use this order when choosing how to compile:

1. User-provided command.
2. Existing project or editor build configuration.
3. Existing repository documentation or scripts.
4. For a new standalone TeX output only, `latexmk -pdf` if available, otherwise `pdflatex -interaction=nonstopmode -file-line-error`, when compatible with the generated source.

If multiple existing commands conflict, or if the engine choice affects Unicode, CJK, fonts, bibliography, shell escape, or package behavior, stop and ask before compiling with a different policy.

## Final Verification

Before finishing, verify:

- All requested Typst content has been converted.
- No catch-all migrated-comments block was created.
- No labels were renamed for style consistency.
- No destination scaffold was removed.
- The existing TeX build command has been run when available, or the reason it was not run is reported.
- For a new standalone TeX output with no existing build command, apply Build Command Resolution.
- Remaining warnings, unresolved mappings, and user decisions are reported separately.
