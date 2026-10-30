# Stable Author and Affiliation Identifiers

Read this tip when author records refer to affiliations, presenter roles, or
other records whose visible numbers can change after insertion, deletion, or
reordering.

A **stable identifier** is a string stored in the authoring data that names one
record without encoding its current display position. Store stable identifiers,
not visible affiliation numbers, in author records:

```typst
#let authors = (
  (name: "Taro Yamada", affiliation-ids: ("lab-a",)),
)

#let affiliations = (
  (id: "lab-a", body: [Department of Engineering]),
)
```

Apply the source policy for unused affiliation records first, then derive
visible numbers for the affiliation records that will be rendered. Obtain the
rendered ordering rule from the source: some publications use declaration
order, while others use first appearance in the author list. Apply that one
order to both affiliation lines and author markers.

Before rendering:

- require each affiliation identifier to be unique;
- require every referenced identifier to exist;
- store a presenter or corresponding-author role on the author record itself,
  for example `presenter: true`, or refer to that author through an explicit
  stable author `id`; never encode a movable role as the author's current array
  index.

Do not store both an affiliation identifier and a separately editable visible
number for the same relation. Reorder affiliations, delete an author, remove an
unused affiliation, and give one author multiple affiliations; confirm that
every marker and line is renumbered from the same records.
