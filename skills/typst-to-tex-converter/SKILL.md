---
name: typst-to-tex-converter
description: Convert a Typst manuscript or document into TeX/LaTeX while preserving the Typst source meaning and adapting output syntax to the destination TeX style. Use when the user asks to translate, migrate, port, or convert `.typ` content into `.tex`, especially when an existing TeX file or template should be reused.
---

# Typst to TeX Converter

## Core Contract

- Typst source is the content authority: wording, order, active/commented status, labels, references, equations, figures, tables, lists, comments, notes, bibliography, and line-break intent.
- TeX evidence is style/scaffold authority only. Preserve reusable template setup, macros, packages, class-specific metadata placeholders, and build conventions; do not copy unrelated article body content.
- Convert by semantic element, not by arbitrary text chunks and not by whole-document generation. Semantic elements include metadata fields, headings, comment blocks, paragraphs, equations, figures, captions, grouped figures, lists, tables, and bibliography entries.
- Inspect all constructs inside the next semantic element before converting that element. If every construct is covered by `references/rules.md`, `references/decisions.md`, TeX evidence, or official docs, convert the enclosing element as one TeX fragment.
- If any contained construct is unknown, do not convert that semantic element. Return `STOP:` with the exact source lines, the smallest unknown construct, and one concrete question asking the user to choose the TeX mapping. After the user decides, add the rule to `references/decisions.md` and resume from the same element.
- Never paste active Typst syntax into the visible TeX body as a workaround. Active Typst syntax is allowed only in source-preserving comments or local fallback markers while stopped.

## Rulebook

- Read `references/rules.md` before converting. It contains the stable known rules.
- Read `references/decisions.md` when it exists. It contains user-approved project/local rules discovered through `STOP:` decisions.
- Do not create YAML/JSON rule registries for conversion rules. The rulebook is Markdown so that ambiguous Typst-to-TeX decisions remain human-reviewable.
- Keep the rulebook compact. Add only decisions that change future conversion behavior; do not add generic Typst or LaTeX documentation that can be checked from official docs.

## Workflow

1. Select the Typst source, requested TeX output, and any TeX evidence named by the user.
2. If the output is new, create a scaffold seed:
   `scripts/seed_tex_skeleton.py source.typ output.tex --tex-evidence evidence.tex --block-ledger .typst-to-tex/block-ledger.json`
   Omit `--tex-evidence` only when none exists.
3. Process source order from top to bottom. Use:
   `scripts/next_conversion_block.py .typst-to-tex/block-ledger.json output.tex`
   to find the next pending source span, then identify the first semantic element in that span.
4. Inspect the element locally. Convert it only if every contained construct is known. Write the TeX fragment to a temporary file and replace exactly that block with:
   `scripts/replace_block.py output.tex <block-id> fragment.tex --block-ledger .typst-to-tex/block-ledger.json`
   When creating fragment files from a shell, use a single-quoted heredoc such as `cat <<'EOF'`; never use `echo -e`, unquoted `printf`, or string literals that interpret backslash escapes.
5. If a seed block contains multiple semantic elements, convert only when all of them are known and belong together syntactically. Otherwise split the work manually by replacing the block with the first converted element plus a fresh local marker for the remaining source lines.
6. Run `scripts/scan_typst_preservation.py source.typ --output .typst-to-tex/source-scan.json` for final auditing and unresolved-source detection, not as a precondition that all source constructs have been globally classified.
7. After all markers are replaced, normalize indentation only:
   `scripts/format_tex_indent.py output.tex`
   This is a post-processing step, not a conversion step. It must not change tokens, line order, comments, labels, command arguments, or blank/nonblank line count except leading whitespace.
8. Then run:
   `scripts/run_conversion_checks.py source.typ output.tex --tex-evidence evidence.tex -- <build command>`
   The wrapper audits before building. Omit `--tex-evidence` only when none exists.
   Use the user's requested build command and working-directory conventions exactly. If validation is done in an isolated copy, copy or expose required TeX class/style/font/image assets so the command sees the same files as it would in the project.

## Prohibited Shortcuts

- Do not create or run a custom whole-document converter that writes the requested output `.tex`.
- If conversion output was produced by a whole-document generator or script, discard it as invalid validation output and return to the block replacement workflow.
- Do not use generated TeX from another converter as the final output base.
- Do not satisfy checks with invisible/audit-only TeX such as `\phantom`, `\hphantom`, `\vphantom`, `\smash`, `\llap`, `\rlap`, or hidden source dumps.
- Do not globally replace all references, labels, quantities, or comments without checking their local source context.
- Do not collapse multi-line Typst bracket/parenthesis blocks into one-line TeX arguments unless TeX syntax or the build requires it.
- Do not move TeX evidence preamble comments or macro definitions into the document body while adding CJK wrappers, metadata, or converted source fragments.
- Do not write ASCII control characters to TeX output. Backslashes in TeX commands must remain literal bytes.

## Completion Gate

Before reporting success, verify:

- no `% BEGIN typst-to-tex block`, `% END typst-to-tex block`, or `% FIXME typst-to-tex:` marker remains
- audit passes with TeX evidence when available
- the build command passes, or the response is a `STOP:` for one specific unconvertible source construct
- source wording, paragraph boundaries, labels, reference targets, comments, notes, figures, tables, and bibliography are preserved in source order
- each source comment appears once at the corresponding location, including inside converted caption/bracket blocks
- active Typst command/reference/label syntax remains only in comments or fallback markers
- units, subfigures, math notation, references, and protected scaffold follow the rulebook and TeX evidence

If any gate fails, return to the source element that caused it. Do not repair by rewriting the whole document.
