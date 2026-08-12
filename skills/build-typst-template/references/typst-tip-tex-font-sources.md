# Font Sources for TeX-Origin Documents

Past TeX-origin work compiled the supplied TeX source with its project
toolchain and read the resulting PDF with `pdffonts`. This exposed the faces
used by the renderer when source-level family declarations alone did not.

OpenType and TrueType files supplied by the project or TeX distribution were
usable when Typst listed them. In one prior TeX source, Harano Aji OpenType
faces were loadable, but the Computer Modern faces were supplied as Type 1 PFB
files and were not listed by Typst 0.14.2. Latin Modern was therefore a
substitute, not the same font.
