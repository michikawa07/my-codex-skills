# Source Baseline Pitch to Typst Leading

Use this when a source specifies baseline-to-baseline line pitch. Typst
`leading` controls additional inter-line space. Inside the actual local layout,
define a renderer with the target width and paragraph/text style, then render a
representative glyph sequence as one line and two lines with zero leading.

Calculate `tight-pitch = height(two-tight) - height(one-tight)` and
`leading = calc.max(0pt, target-pitch - tight-pitch)`. Render the real multiline
content with that `leading` and confirm at least two consecutive baseline
intervals. Keep the target pitch and typography at the owning text element.
