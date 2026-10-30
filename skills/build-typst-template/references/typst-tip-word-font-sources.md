# Font Sources for Word-Origin Documents

Past Word-origin templates exposed `/mnt/c/Windows/Fonts` to Typst when
compiling under WSL. That directory made Times New Roman, Arial, MS Mincho, MS
Gothic, MS PGothic, and Cambria Math available to Typst. Omitting the directory
caused fallback, changed wrapping, and in one case changed the page count.

OOXML run, style, default, and math assignments identified which Windows faces
the document requested. `pdffonts` on the PDF exported by Word identified the
faces Word actually embedded. These are separate observations when Word applies
theme substitution or fallback.
