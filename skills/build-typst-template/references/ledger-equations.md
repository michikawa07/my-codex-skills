# Equations

**Requires** — Established body/column width, paragraph rules, inherited
typography, global counters/links, and page/column flow.

**Owns** — Inline/display math semantics, equation placement and numbering,
labels, and equation-reference rendering.

**Emits** — Standard Typst math and reference routes whose official and varied
instances place, number, and render coherently.

**Recheck** — Inline/display math, official equation extent and formation,
tall and long equations, equation numbers, references in prose, links, and
following flow.

Process Equations first, then open Equation references as its one direct child.
Close reference prose against the established counter, label, and display
number before closing Equations.

- **Equations [C,T]** — inline/display semantics; math font and glyph
  treatment; alignment and indent; space above and below display equations;
  counter/reset, number format and prefix/suffix; number position;
  label/reference semantics; keep/break.
  - **Equation references [T]** — actual author syntax; localized prose
    prefix; parentheses and number format; spacing, link target, and the
    observed inline result.

Trace each claimed author syntax to its expected semantic output and its
observed extracted or rendered output. Confirm inline math retains its own
evidenced policy after display-equation styling.

In Typst, the block spacing settings `above` and `below` inherit paragraph spacing
when `auto`. If the inherited spacing differs from the source's display-equation
spacing, set explicit values in a show rule that applies only to display equations.
Verify the resulting gaps in the rendered output.
