# Body Flow

**Requires** — Stable page region and frontmatter transition, with inherited
typography and the intended reading order known.

**Owns** — The usable body region, columns, paragraph and heading flow, and the
coordinate system inherited by body children.

**Emits** — Natural paragraph/heading layout plus stable insertion contexts for
lists, equations, figures, tables, citations, and references.

**Recheck** — Frontmatter-to-body transition, column/page continuation,
heading-to-content attachment, downstream displacement, and final-page tails.

Process one direct child at a time: establish Columns, then complete Paragraphs
and each observed Heading level separately in reading order. Reopen Columns
when a child exposes a wrong available width, gutter, span, or break context.

- **Body container [C]** — usable region; section flow; frontmatter
  transition; page and column balancing policy.
  - **Columns [C]** — count, widths, gutter, rules, balance, span behavior,
    reading order, column/page breaks.
    - **Paragraphs [T]** — paragraph semantics; justification and hyphenation;
      first/hanging indent; inter-paragraph policy.
    - **Heading level 1..N [C,T]** — identify every observed level separately;
      hierarchy, counter/reset, numbering/prefix/suffix, punctuation, outline
      and bookmark behavior; run-in/block form; keep with following content.

Inspect relationships as well as isolated elements: inherited versus local
fonts, parent content width versus child wrapping, spacing collapse, and
baseline alignment between mixed content. Then vary the smallest relevant
content dimension to test whether the chosen rule generalizes.
