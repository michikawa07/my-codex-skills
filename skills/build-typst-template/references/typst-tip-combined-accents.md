# Combined Math Accents

Use a semantic combined accent when the source equation contains a multi-mark
accent. In Typst 0.14.2, nested `$ dot(dot(x)) $` places two single-dot accents
vertically, whereas `$ dot.double(x) $` produces a horizontal double dot.

Confirm the mark count and placement in a focused high-resolution render after
compilation. Re-probe the case after an engine upgrade.
