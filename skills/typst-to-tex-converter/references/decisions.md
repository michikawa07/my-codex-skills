# Typst-to-TeX Decisions

Record only user-approved conversion rules discovered through `STOP:`. Keep each entry short and actionable.

## Decisions

- If active authors reference affiliation ids but no active affiliation records exist, emit the corresponding TeX affiliation/address fields with blank content. Do not promote commented-out Typst affiliation text or unrelated TeX evidence affiliation text to active metadata.
- Convert scoped Typst enum blocks such as `#{ set enum(numbering: "(A)", indent: 10pt, spacing: 10pt) ... }` to LaTeX `enumerate` using `enumitem` options that preserve the visual label, indentation, and item spacing as closely as TeX permits.
- Convert `subpar_grid` spacing options such as `gutter` and `gap` to explicit editable TeX spacing placeholders between `\subfloat`s. Use `\hspace{0pt}` for horizontal gaps and `\vspace{0pt}` for row gaps by default; do not copy Typst spacing values directly because Typst and TeX/subfig layout metrics are not equivalent.
- When `subpar_grid` omits active `columns`, treat it as Typst `subpar.grid` default stacked layout: convert child figures to vertically stacked full-width `\subfloat`s. Use full available line width for each child image unless an active child width says otherwise, and place `\vspace{0pt}` between rows as the editable spacing placeholder.
