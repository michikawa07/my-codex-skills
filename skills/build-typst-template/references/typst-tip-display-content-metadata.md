# Display Content and PDF Metadata

Read this tip when one title or author record supplies both visible document
content and PDF metadata.

Typst `content` can contain styling and document elements. PDF metadata fields
accept parameter-specific value types. Check each `document` parameter
separately: in Typst 0.14.2, `title` accepts `auto`, a string, or `content`,
while `author` accepts a string or an array of strings. Do not pass `content` to a
string-only field, and do not use `repr(...)` to manufacture metadata text from
arbitrary content.

Keep each title or author value in one record. When possible, store the plain
string and derive its visible styling:

```typst
#let author = (name-en: "Taro Yamada", affiliation-ids: ("lab-a",))
#let display-name(author) = text(weight: "bold", author.at("name-en"))
#let metadata-name(author) = author.at("name-en")
```

Render affiliation marks, presenter marks, and other styling from separate
semantic fields rather than embedding them in the metadata string. If the
author-facing API accepts display content for a metadata field whose `document`
parameter requires strings, require an explicit metadata string in the same
record and state that the display and metadata values represent the same title
or author.

Validate every metadata value required by the governing publication source
before layout. Change one source record and confirm that visible text and
extracted PDF metadata change together. Also test the source-defined behavior
for an empty value, an incomplete record, and a styled display value. Recheck
the installed Typst version before relying on a specific metadata field type.
