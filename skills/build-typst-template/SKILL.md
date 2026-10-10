---
name: build-typst-template
description: Build, reconstruct, or harden a reusable Typst document template from project-specific DOCX, PDF, TeX/LaTeX, or Typst evidence. Use when Codex must infer an author-facing API and layout rules from supplied publication sources, reproduce a reference document across its pages, or diagnose and repair template drift through structural and visual inspection.
---

# Build Typst Template

Reconstruct the document system evidenced by the project. Let Codex judge the
document semantics, relevant parameters, public API, Typst implementation, and
visual differences, then repair them until all conditions listed under Finish hold; use automation to expose mechanical facts.

## Goal

Port the publication format as an authoring system for a new author. The Typst
template owns the source layout machinery and publication policy; its user
supplies ordinary semantic document content through a small justified API and
standard Typst elements. The system must reproduce the official instance and
remain coherent when realistic titles,
authors, paragraphs, lists, equations, figures, tables, citations, references,
and page flow change. The deliverable combines faithful reproduction of the
official sample with reusable behavior under those author changes.

Use every source inspection, compile, crop, comparison, official/variation case, and element iteration to
improve this document-level authoring system. Track progress by the author
workflow, template-owned rule, and document-wide behavior secured by each local
decision. Keep layout knowledge in the template and semantic manuscript content
in the author source.

## Bound the Evidence

Define evidence as every user-named file plus every regular file recursively
contained in a user-named directory. Calibrate from that closed set. Expand the
set when the user names an additional parent, sibling, prior output, or symlink
target.

Inventory that set before editing. Render each reference and make a shallow
all-page pass recording pagination, page roles, and top-level hierarchy.
Complete detailed inspection as corresponding semantic elements become active;
by finish, inspect every named source and every page of each reference. When
sources disagree about a reusable rule, identify the exact conflict and ask the
user which source governs. Treat metadata, extracted text, XML properties,
bboxes, and pixels as observations interpreted beside the structural source and
rendered document.

For a layered source stack, trace each rule to its role. A base class supplies
inherited defaults, a publication style or package defines publication
overrides, an author template exposes the intended author workflow and official
content, and compiled output shows realized geometry and pagination. Treat the
structural definitions as primary evidence for semantics and rule ownership,
and the render as primary evidence for their realized effects.
When the structural source that owns a target rule states a direct value,
implement that value exactly. When the realized render suggests a different
value, surface the conflict and governing sources, and preserve the stated rule
until the governing source is resolved.

Promote a choice to a template default, public API, or document semantic when
the closed evidence or explicit user direction assigns it that reusable role.
Let structural publication rules and exact official content and formatting
govern the intended target. When portability, a generic convention, or
implementation convenience suggests an alternative, treat it as a reported
constraint or candidate user decision while preserving the evidenced target.

Before implementation, assign each observed item to exactly one owner:

- **author semantic** — content a new author is expected to supply or vary;
- **publication policy** — reusable behavior owned privately by the template;
- **official-fixture literal** — sample content specific to reproduction of the
  official instance; or
- **comparison-only exclusion** — non-public guidance or producer artifact that
  the user confirms is absent from authored/submitted output.

Let the public API contain the author-semantic set and the template internals
contain publication policy. Keep official-fixture literals in `usage.typ`.
Record every comparison-only exclusion and its exact masked region or object,
while keeping adjacent publication content visible in the comparison. Base any
reclassification on new source evidence or an explicit user decision.

For each exclusion, distinguish its visible ink or object, occupied layout
extent, and effect on surrounding and downstream flow. When editable source is
available and the excluded item participated in flow, create a clean reference
render with that item removed and compare the reflow produced after removal. For an
overlay, mask exactly its ink or object. Retain excluded space when separate
evidence assigns that space to publication policy.

## Core Workflow

For generated artifacts, use one authoring root and one system-temporary scratch root. The authoring root contains current
`template.typ`, official `usage.typ`, consolidated `variation.typ`, dependencies, assets, PDFs compiled after the latest
source edits, and completed `critic-findings.md`. The scratch root contains tool output, probe copies, focused sources,
logs, and intermediate builds; reuse it and make an empty subdirectory only when a tool requires one. At completion, copy
only evidence supporting the verified result or a user-accepted exception into one authoring-root `evidence/` directory.

Use these workflow terms throughout this file and its linked references:

| Term | Meaning in this workflow |
| --- | --- |
| **builder** | Agent that reads publication evidence and edits the current Typst authoring files. |
| **current authoring system** | Current author sources, template dependencies, assets, and PDFs compiled after the latest source edit. |
| **font face** | The complete resolved face name reported by the compiler that renders the source; if that report is unavailable, use the exact face name in the structural source; if neither is available, use the normalized PDF face name. The name includes family, weight, and style. A visually or metrically similar name is a different face. When reading a PDF face name, remove only a six-uppercase-letter subset prefix such as `ABCDEF+`. |
| **font role** | A coarse use that has one source-assigned font face, such as body text, heading text, captions, bibliography text, or display math. Split a role only when the source assigns a different face. |
| **font metric normalization** | One horizontal and one vertical scale factor shared by every occurrence of one substitute-font role. The scaled dimensions participate in Typst wrapping and flow; per-string factors are forbidden. |
| **font requirement** | One font role with its source evidence, expected and actual faces, current observation, optional font metric normalization, and optional user approval. When faces differ, record the alternatives, their shared factors, post-normalization differing ink-pixel count, text-width difference, top-to-bottom ink-extent difference, and the user decision. |
| **font gate** | Pre-layout check that every font role uses its expected face or a user-approved substitute whose shared factors make rendered text width and top-to-bottom ink extent equal to the reference at every compared occurrence. Every PDF face belongs to a role or a user-confirmed comparison-only exclusion. |
| **semantic / semantics** | Document meaning encoded by element type, structured content/order, counters, labels, and references rather than appearance alone. |
| **element** | One source container or content unit: page, title block, paragraph, list, equation, figure, table, etc. |
| **packet** | Linked reference for one element type; `Requires` lists prerequisites, `Owns` its rules/relations, `Emits` outputs, and `Recheck` later observations. |
| **router** | Ordered element list and packet links in `component-property-ledger.md`. |
| **target element list / inventory** | Target-specific Markdown list of default and discovered elements, occurrences, planned checks, and its completeness status. Store it at `<scratch>/target-elements.md`. |
| **branch property** | One named semantic or layout relation that the branch must reproduce. A layout relation determines placement, size, child arrangement, text formation, or effects on neighboring and later content; examples are author-block alignment, the gap between two author groups, continuation-line indent, and whether a figure stays with its caption. |
| **branch record** | One Markdown file under `<scratch>/branch-records/` containing an open, closed, or invalidated branch's source locations, required branch properties, Typst controls, official and variation observations, numeric checks, rechecks, children, and mismatches. |
| **valid prerequisite record** | An open or closed branch record, never an invalidated one, whose cited prerequisite relation has `Observed after last change: true` and is satisfying. A relation with a `Result` field is satisfying only with `match`, `accepted_mismatch` plus its exact user decision, or explicitly permitted `not_applicable`; a relation without a `Result` field is satisfying only when its observation establishes the prerequisite and no unresolved mismatch contradicts it. The whole record need not be closed when it supplies a current direct-parent relation to its active child. |
| **router cursor** | Small YAML record at `<scratch>/router-cursor.yaml`. It stores only inventory and font-gate status and record paths, the active branch and its branch-record path, waiting or suspended branch paths, closure summaries and branch-record paths, and critic state. Detailed element, font, measurement, and closure evidence stays in the referenced Markdown files. |
| **branch / active branch** | One element type or structural role whose shared layout/semantic rule is checked across all named occurrences / the only branch currently edited. |
| **critic group** | One of the eight numbered router groups in `component-property-ledger.md`. All target branches assigned to one group collectively count as one completed unit for intermediate critic scheduling. The root `Document` branch is final-only and is not a critic group. |
| **first affected branch** | Earliest branch in router dependency order whose owned rule or recorded relation must change to remove the observed failure. |
| **composite branch** | Branch whose direct children each require a branch record before the parent completes. |
| **closure entry / branch closure** | A completed branch record whose required observations were repeated after the latest edit that can affect that branch / the event that appends its branch path and record path to the cursor and advances it. An entry remains valid only until contradicted. |
| **author action** | One edit or call made through author-facing syntax. |
| **author route / call path** | That syntax plus its ordered wrapper, imported function, and template-rule sequence to output. |
| **activating variation** | Author action whose output exhibits the predicted element type/content or visible event that distinguishes the inferred rule. |
| **public author workflow** | Editing through those author-facing files/syntax and compiling without template-internal edits. |
| **natural flow** | Placement from document order/content size, without absolute coordinates or space reserved for one sample. |
| **internal formation / downstream relation** | Glyph/line/math-child/cell-child arrangement inside an element / position or flow of later content affected by it. |
| **governing cause** | Exact source construct or template rule whose change removes an observed failure without extra author-side layout code. |
| **critic finding** | Demonstrated author action/failure/harm, its governing cause, a repair or user decision, and the action/observation to repeat afterward. |
| **critic result** | `REVISE` for changed meaning, a second helper for the same concept, or wrong/overlapping/missing content or flow; otherwise `BLOCKED` if evidence/authority is missing; otherwise `CLEAR`. |
| **Finish conditions** | Inventory and the font gate are complete; every present or variation-required branch has a valid closure entry; every absent branch has absence evidence; final critic is `CLEAR`; builder has no unaccepted mismatch; and every critic finding has a resolving retest. |

Keep the task active until the Finish conditions hold. Use critic findings only as repair input. Maintain the cursor and the files it references with the exact records and transitions in step 9.
1. **Collect mechanical evidence.** First identify the user's actual Typst
   host/compiler and font settings from user or project evidence; ask if unclear.
   Apply [font resolution](references/typst-tip-font-resolution.md). Inventory files,
   formats, page geometry, embedded fonts, and images; render editable sources
   with their established application or compiler to expose appearance and pagination.
2. **Map the top level.** Read [the element router](references/component-property-ledger.md) once. Before implementation,
   complete `<scratch>/target-elements.md` from the structural source and every rendered reference page, including
   present/absent defaults, discovered elements, every official occurrence, and required numeric relations. Create
   `<scratch>/font-requirements.md` for the font-gate records. Then load the packet linked by the router for the single
   active branch; apply its detailed prompts only after every item in the packet's `Requires` section has a current
   Prerequisites row as specified by the router.
3. **Build and compile the skeleton.** Prefer a user-named target-adjacent Typst template/document over the bundled
   [`template.typ` + `usage.typ`](assets/scaffold/) pair as evidence for file division, imports, wrapper calls, and
   body-flow hooks; copy the best available pair into the authoring root. Before the font gate completes, derive only
   author API slots, semantic element roles, exact content needed to exercise fonts, and font requirements from structural
   and rendered evidence. Preserve free-form author content. Create only enough template rules and official or consolidated
   variation content to exercise every font requirement, then complete the font gate. A scratch-only focused source may
   identify which face a font-selection rule loads, but it does not satisfy a font requirement. While the gate is open,
   inspect sources; add content needed to exercise the roles; configure font discovery; and apply the font-resolution
   rules in Element Completion Loop item 5. Do not tune
   wrapping, spacing, page/container geometry, or downstream positions while the gate is open.
   After the gate completes, derive publication and content-dependent layout rules. The scaffold has one positional-body
   public wrapper and private `_render_body(body) = body` hook; replace that hook when target evidence requires different
   flow such as `columns(...)`, while keeping page, column, gutter, break, and flow policy private in the template.
   Establish page setup, major containers, rough natural flow, and one `variation.typ` containing a realistic author
   action. Add realistic additions, omissions, reordering, length changes, and page/column
   crossings early to expose duplicate author paths, misplaced policy, and fixed-flow assumptions; an early case does
   not close an unexamined element. Select cases from this one variation source. Use a scratch-only focused source to
   distinguish two plausible rules, then move any lasting case into the consolidated variation. Compile and render the
   official instance plus the smallest public-API change that distinguishes the current page/container/wrapper behavior
   before geometry tuning.
4. **Complete elements in dependency order.** Keep one branch active; open its packet after `Requires` observations
   exist and close it through `Emits` and `Recheck`. In a composite branch, complete one direct child at a time in
   reading order. Before geometry tuning, establish exact official content, author syntax/API, and one activating
   variation. Advance only after step 9 records all required official, variation, and `Recheck` observations. Reopen the
   first affected branch when later evidence contradicts a recorded relation.
5. **Deepen uncertain rules.** When the first official/varied pair leaves two plausible rules, isolate the minimum
   distinguishing content or flow, then apply the observed rule and activating case to the primary documents.
6. **Compare hierarchically.** Run the all-page comparison, then use the
   [visual comparison playbook](references/validation-playbook.md) on named regions, internal formation, downstream
   relations, and the last page. During repeated edits to the active branch, use the playbook command to render the one
   page of `usage.typ` or `variation.typ` that contains the occurrence being adjusted. For step 9 observations and the
   final judgment, compile every current official and variation source to PDF and run the playbook's `scan` command and
   any required `detail` command on those PDFs.
7. **Repair from a prediction.** For a step 9 mismatch, state the source-backed rule and exact direction/amount of the
   predicted correction. Test it, then record the affected parent, child, internal-formation, and downstream observations.
8. **Critique and refactor the author usage.** Each time step 9 closes an element,
   evaluate the critic group assigned to that branch in the target element list. Add the group name once only when every
   present or variation-required branch assigned to that group has a valid closure. Closing a child branch or a parent
   branch before the whole group is complete does not add a name. Trigger the Author-Usage Critic Loop on the complete
   current authoring system when two distinct critic groups have completed since the critic last loaded its inputs. Pass
   only current author sources,
   dependencies, assets, and the PDF compiled from each source after its latest
   edit; the builder retains the router cursor, active packet, branch records,
   and prior diagnosis. Start the
   next element while the critic runs. From each returned file/location and
   governing cause, the builder identifies the first affected branch in
   dependency order, reopens it when needed, and performs the stated retest.

Request a user decision when the evidence does not determine which source
governs, what a source item means, whether a file outside the named inputs may be
edited, or whether a named remaining mismatch may be accepted.

After a context compaction or resumed run, restore the Goal and read, in order,
the router cursor, the active branch record, that record's one target entry in
`<scratch>/target-elements.md`, the active packet, and only the prerequisite
branch records named by the active record. Read other target entries only when
inventory or dependency routing is needed, and read
`<scratch>/font-requirements.md` only when the font gate is active or rechecked.
Resume at the first unmet branch-completion condition in the order listed by
the router. Advance only from step 9.

Record elapsed time only after obtaining every closure entry, successful
activating variations, final critic `CLEAR`, and no unaccepted builder mismatch.
Then shorten the same verified path toward roughly 30 minutes.

## Element Completion Loop

Apply this loop to the active branch selected by the router. Attach each rule to
one of the four owner categories and close the branch through its packet
relations.

When a branch becomes active, create or reopen its branch record. Read the active
packet and add its required starter branch properties to that record. Before
changing the branch, inspect the governing structural source and rendered
occurrences and add a branch property for every additional semantic or layout relation found by the extraction
rules in the router. Identify the author action or publication rule it supports,
its parent/earlier constraints, and the later content it can move. After changing
it, record its internal formation and the observed effects on those named
relations in the same branch record.
Treat pixel scores, elapsed time, compiled fixtures, and visited elements only
as auxiliary observations.

For each element, connect five concrete facts in its branch record: its author
syntax/content, the file that owns its formatting rule, the Typst control
implementing that rule, its official rendered relations, and its observed
activating variation. Use the current packet for its starter properties and
rechecks; use the router for the full element list, dependency order, common
starter properties, and target-specific property extraction.

The parent container establishes the child's coordinate system, available
width, inherited rules, and flow context. Interpret and tune child parameters
inside that established context. Typography is structural too: font face,
size, tracking, and line pitch change wrapping and element extent, which moves
downstream content. Therefore establish parents before children, close composite
parents after their children, and work earlier flow elements before later ones.

Complete the following observations for one active element before moving to the
next. Revisit an earlier element when later evidence invalidates its record:

1. **Parent context.** Establish the coordinate system, available width,
   inherited rules, flow context, sibling relationships, and downstream effects
   supplied by the established parent and earlier elements.
2. **Document role, owner, and author syntax/call path.** State what document
   concept the element represents, its boundary, relations expected not to
   change, and one of the four owners above. For a
   standard document element, first write the ordinary Typst author syntax:
   headings, lists, equations, figures, tables, labels/references, citations,
   or bibliography as applicable. Put publication behavior in template
   `set`/`show` rules. Introduce a public helper only for an author-supplied
   document concept that no standard Typst element/argument represents; record
   that concept and the standard syntax tested. Select the
   smallest author-controlled content or flow change that can distinguish its
   inferred reusable behavior from an official-instance workaround. Include any
   project-specific element found in the source hierarchy.
   For prose references, exercise the ordinary standard reference syntax,
   normally `@label` and explicitly `#ref(<label>)` where a lexical boundary
   requires it. Let template-owned reference styling derive the target-kind
   prefix, punctuation, and numbering form; keep this distinct from caption
   supplements and verify equation, figure, and table prose separately.
3. **Official content.** Establish exact correspondence for the active element's
   wording, symbols, equations, assets, citations, order, and deliberate breaks.
4. **Activating variation.** Change one legitimate author input to distinguish
   the inferred rule. Before rendering, predict the visible event, the relations
   that change, and the relations expected not to change. Increase or alter the
   author content and rerender the same case until that event appears. Observe
   it directly through multiple title baselines, sentinels crossing a page or
   column, table-row identifiers around a boundary and its repeated header, or
   the next normal anchor after optional-field omission. Record how the result
   affects the parent, neighbors, and downstream flow.
5. **Branch properties, controls, and owner.** Before editing, put the common
   layout starter properties for the branch's `[C]` or `[T]` markers and the
   packet's branch-specific starter properties into its branch record. Inspect the source
   rules that apply directly or by inheritance, the source containers that group
   and order direct children, every official rendered occurrence, and the
   selected author variation. Add a separate property row for every additional
   content identity, order, counter, label, link, placement, size,
   child-arrangement, text-formation, neighbor, or downstream relation found
   there. Record a source location and target relation for each
   row; `not_applicable` requires a source- or structure-based reason. Complete
   this property list before tuning the branch.

   Map every property to its governing Typst file and control and one of the four
   owner categories. Cover the applicable typography, alignment, width/wrap,
   spacing, breaks, numbering, strokes, padding, markers, and asset treatment.
   When a source names a geometric relation, record its definition and
   endpoints, then map it to the Typst control that governs the same relation.
   Verify that relation at two repeated instances, or record the unique
   element's actual endpoints. Use those endpoints as the calibration target.
   Wrong font metrics invalidate later layout calibration. Before layout, resolve each source-assigned face through the final Typst compile environment, using project, source-application,
   operating-system, and compiler font locations. If the exact face is unavailable, compare alternatives that contain
   every character used by that font role and retain the source-assigned serif, sans-serif, Mincho, or Gothic class,
   weight, and style.
   For each alternative, use one horizontal and one vertical scale factor for that font role across every official
   occurrence that uses the role, or every variation occurrence when the official
   instance lacks the role. The scaled box must govern Typst wrapping and flow. Reject per-string scaling, tracking,
   inserted spaces, and positional compensation. An alternative is eligible only when the shared factors make rendered
   text width and top-to-bottom ink extent equal to the reference at every compared occurrence; among eligible alternatives, recommend
   the one with the smallest total differing ink-pixel count. Ask the user to approve the face and both factors. If none
   is eligible, request another font or the user's decision on an allowed non-identical rendering before layout work. Record the comparison and
   load the Typst font-resolution tips.
6. **Shared implementation.** Use the same ordinary Typst syntax and
   template-owned rules for the official and varied instances, with
   `set`/`show` rules, and natural flow. Use contextual measurement when local
   available space governs the result. Place reusable constants in the file
   assigned by the owner category; keep sample text, equations, figures, and
   tables as ordinary content in `usage.typ`.
7. **Official local confirmation.** Compare the active official element against
   its source through exact text and symbols, math form, glyphs/fonts,
   widths/heights, padding, strokes/borders, and its relations to parent,
   neighbors, and following flow. Compare three relations separately: the
   element container's placement and extent within its parent; direct-child box
   placement, insets, alignment, spacing, and flow inside that container; and
   each child's internal formation. For prose, observe first, continuation, and
   final line edges, alignment, wrapping, line pitch, and indents. For structured
   children, observe shared edges, row/cell alignment, padding, wrapping, rules,
   and boundaries. Record a match or the exact mismatch for every applicable
   relation; a missing observation or unaccepted mismatch leaves the branch
   active.
8. **Variation call-path confirmation.** Record the author input changed, its actual
   call path, the predicted visible event and relations expected not to change,
   the observed element type/content or rendered event, and downstream behavior.
9. **Branch closure and transition.** After the last branch edit, rerender the
   official case and its activating variation through the public author workflow.
   Update the active branch record using the Markdown format in the router, then
   update `<scratch>/router-cursor.yaml` in this compact shape:

```yaml
inventory:
  status: open
  record_file: "<scratch>/target-elements.md"
font_gate:
  status: open
  record_file: "<scratch>/font-requirements.md"
open_parents: []
active:
  branch: ""
  record_file: ""
  status: open
closures: []
suspended: []
critic:
  state: idle
  last_result: ""
  completed_groups_since_last_input_load: []
  unresolved_findings: []
```

   Store font details in `<scratch>/font-requirements.md`:

```markdown
# Font requirements
reference_inventory_complete: false
no_font_requirements_reason:

## Requirements
| font_role | source_evidence | expected_face | actual_face | font_metric_normalization | observation_summary_and_evidence_id | observed_after_last_change | approved_substitution |
| --- | --- | --- | --- | --- | --- | --- | --- |

## PDF comparisons
| reference_pdf | candidate_pdf | comparator_index | unexplained_faces | observed_after_last_change |
| --- | --- | --- | --- | --- |

## Comparison-only font exclusions
| pdf_side_and_face_name | user_confirmed_exclusion |
| --- | --- |

## Evidence
### F-001
Command and unedited output:
~~~text
...
~~~
```

   Each `open_parents`, `closures`, or `suspended` entry contains `branch` and
   `record_file`; a closure entry also contains `critic_group`. Detailed state
   belongs in the referenced file, not in the cursor. Every observation names
   both locations and the visible, extracted, or measured relation. A table cell
   stores a short observation and an evidence ID; the same file's Evidence
   section stores multiline commands and unedited output in fenced blocks. Use
   `not_applicable: <reason>` only where justified; each accepted mismatch
   records the exact item and user decision. Apply these transitions:

   Store `reference_inventory_complete`, `no_font_requirements_reason`, requirements, PDF comparisons, and
   comparison-only font exclusions in `<scratch>/font-requirements.md` using the schema above. Each
   `unexplained_faces` entry contains `pdf_side`, `face_name`, and
   `reason_not_assigned`. Set `reference_inventory_complete: true` only after every present or
   `Variation required: true` target branch containing
   text or math for which the structural source or PDF extractor reports a font face is assigned to every applicable
   font role, every such role has one requirement, and every normalized face
   name extracted from every reference PDF is assigned to a role or an existing user-confirmed comparison-only
   exclusion. Fill `no_font_requirements_reason` only when no present or `Variation required: true` target branch contains a
   structural font assignment or PDF text or math associated with an extracted font face. Rasterized or outlined
   lettering is checked with its containing figure, table, or drawing component instead.

   Complete the font gate only when the inventory is complete; every requirement and PDF comparison is current and has
   its required fields and evidence block; every scan has no unexplained face; and each role either uses the exact face
   with factors `1,1`, or has the recorded user-approved face and factors and equal text width and top-to-bottom ink
   extent to the reference at every compared occurrence.

| Guard or event | Required transition |
| --- | --- |
| `inventory.status` is `open` | Keep `active` empty and finish the target element file; set it `complete` only under the inventory rules in the router, then evaluate the font gate before creating the first branch. |
| `inventory.status` is `complete` and `font_gate.status` is `open` | Exercise every required role, run the font scan for each official PDF pair, and follow the font-resolution rules in Element Completion Loop item 5 for unavailable faces. When a substitute choice still requires a user decision, ask one consolidated question for the eligible face-and-factor choices and record the decision. Complete the gate only when the test above passes. |
| `inventory.status` and `font_gate.status` are both `complete`, and `active` is empty before element work begins | Create the first required active branch and its branch record. |
| After the font gate completed, a governing structural source or rendered reference is added or removed, or a source-side font assignment or governing reference file changes | Set `inventory.status: open`, `font_gate.status: open`, and `reference_inventory_complete: false` in the font record. Mark every existing branch record `Status: invalidated`; clear `active`, `open_parents`, `closures`, `suspended`, font comparisons, and `critic.completed_groups_since_last_input_load`. Rebuild the target element and font records from the current evidence. Preserve an explicit user decision only as source evidence; do not preserve its prior observation or result. Create new blank branch records when branch work restarts, and complete the inventory and font gate before recreating the first required branch. |
| After the font gate completed, font selection, normalization, available fonts, compile environment, or exercised font roles change | Reopen the gate, mark affected font observations and branch closures stale, recompile and rescan them, and apply the completion test above. If it fails, invalidate branch records and resolve the gate before layout work resumes. |
| An active composite has a present or variation-required direct child without a valid closure | Push the current branch and branch-record path onto `open_parents` and create the child's branch record; after the child closes, restore the last parent pointer as `active` and add the child's branch path to the parent record's child-closure section. |
| An active child contradicts a relation owned by an entry in `open_parents` | Move every parent pointer above the affected parent, then the child pointer, to `suspended` in parent-to-child order. Make the affected parent active, repair its record and source, and recompile it, then push it back onto `open_parents` without closing it. Restore each moved parent from oldest ancestor to youngest, repair and recompile it, and push it back without closing it. Finally restore the moved child as active; the normal child-to-parent closures then resume. |
| An edit can affect a branch's official or variation result | Apply the router's edit-invalidation rule before compiling. Remove from `critic.completed_groups_since_last_input_load` every group made incomplete by that invalidation. |
| Any applicable branch-completion condition in the router fails; the active branch record has `Last change recompiled: false`; or its Unresolved mismatches section is nonempty | Keep `active.status: open`; continue this branch. |
| `font_gate.status` is `complete`, every applicable branch-completion condition in the router holds, and the active branch record has `Last change recompiled: true` | Mark the branch record closed and append its branch, record path, and `critic_group` to `closures`. If this closure makes every present or variation-required branch with the same `critic_group` valid, append that group name to `critic.completed_groups_since_last_input_load` unless it is already present; `final_only` never appends. Then restore the last parent pointer from `open_parents` or create the next branch in dependency and reading order. |
| A later observation contradicts a closure outside the active ancestor chain | Move any branch pointers in `open_parents`, then the `active` pointer, to `suspended` in parent-to-child order and clear `open_parents`; move the first affected closure pointer in dependency order to `active`, set it open, and reopen its branch record. After the repaired branch closes, restore all but the last suspended pointer to `open_parents` and the last to `active`; if none existed, continue with the next required branch or final review. |
| A later pass finds an omitted occurrence or element with a different shared rule | Add the occurrence to its existing branch or add the new branch path. If it changes the font inventory or adds a role absent from `requirements`, first apply the structural-source/font-inventory reset above. Otherwise activate the affected branch and invalidate each closure whose direct-child placement or downstream relation depends on it. |
| Source authority or acceptance is missing | Keep the branch open and request the user's decision. |

   Compilation, warnings, page count, visited files, and aggregate pixel
   scores cannot populate the relation fields. Resume a suspended branch at its
   first empty or contradicted field after the reopened branch closes again.

Except for a branch-property row that satisfies the router's explicit
`not_applicable` rule, do not enter `Result` as an independent judgment. Derive
it from the fields beside it: an image `match` requires no visible difference
in its named regions; a numeric `match` requires the recorded `Expected
relation` to produce `true` from the current measured values; and a variation
or recheck `match` requires every predicted event and every relation predicted
not to change to be named and observed. Use `mismatch` whenever those fields
contradict `match`, and correct the label before evaluating a closure.

Request the user's decision when source authority or acceptance leaves a closure
field unresolved. Classify a difference as renderer-origin only after recording
matching content, semantics, font/glyph choice, formation, and layout relation.

For every claimed author syntax/call path, trace it to its expected output or
policy and its observed extracted or rendered output. Do this for standard
Typst syntax as well as wrapper fields, including references and bibliography
entries.

## Author-Usage Critic Loop

Start a review when `completed_groups_since_last_input_load` contains two distinct group names. Compile the official usage and every
current case in `variation.typ` with the current dependency files first. Start a fresh
maximum-reasoning subagent without conversation history. Pass the current
authoring sources, dependencies, assets, the PDF compiled from each source after
its latest edit, the authoring-root
`CRITIC_FINDINGS_PATH` for `critic-findings.md`, and
[`author-usage-critic.md`](references/author-usage-critic.md). Withhold the
builder diagnosis, intended answer, prior reports, notes, and rejected outputs.

| Critic state and event | Required transition |
| --- | --- |
| `idle` + a closure completes the first distinct critic group | Keep `idle`; begin the next branch. |
| `idle` + a closure completes the second distinct critic group | Set `loading`; start one fresh critic of all supplied current authoring files and PDFs; keep those files unchanged until `INPUTS_LOADED`. |
| `loading` + `INPUTS_LOADED` | Set `running`; reset `completed_groups_since_last_input_load` to `[]`; begin the next element and compare every reference page with the PDF compiled from its source after the latest edit. |
| `running` + another branch closure | Keep the current critic; append a group name only when that closure completes a critic group under step 9. |
| `running` + completed report + fewer than two later completed critic groups | Store `CLEAR`, `REVISE`, or `BLOCKED` in `last_result`; set `idle`; process the completed `critic-findings.md`. |
| `running` + completed report + two or more later completed critic groups | Store its result and findings, set `loading`, and immediately start one fresh critic on the current files. Keep those files unchanged until `INPUTS_LOADED`, then process the prior findings while the fresh critic runs. |
| No fresh subagent slot | Preserve builder state, consult the user immediately, and await the decision. |
Use only `idle`, `loading`, or `running` in `critic.state`. Keep `completed_groups_since_last_input_load` as a list with no duplicate names. Record the report's `CLEAR`, `REVISE`, or `BLOCKED` value in `critic.last_result`.

For each returned cause/location, repeat its retest against the current authoring files and mark a finding resolved only from that observation. Route every repair through the step 9 transition table: repair an active-branch rule there; use its active-ancestor transition for a waiting parent; otherwise use its closed-branch transition for an earlier element or shared template rule.

Use this handoff with the current paths:

```text
Act as a fresh, independent critic of the generated Typst authoring system.
Read CRITIC_GUIDE completely. Read every CURRENT_SOURCE_FILE and inspect every
page of every CURRENT_OUTPUT_PDF, then send INPUTS_LOADED. Keep them read-only.
Use system-temporary copies for adaptive probes. Review the whole supplied
authoring system using only these inputs. Write the guide's bounded report
directly to CRITIC_FINDINGS_PATH and return its path and status.
```

In scratch, record each critic finding ID, its current unresolved/resolved state,
and the retest observation; use a new fresh critic for each review. Intermediate
`CLEAR` is repair input. After all closure entries remain valid and earlier findings are resolved, finish and process any running critic using the transition table above. Compile the
official usage and all retained variation cases, then leave the current inputs
unchanged. Regardless of `completed_groups_since_last_input_load`, run the final fresh critic and the
builder's raw-source, every-reference-page, and every-variation-page audit concurrently. Finish
only with final `CLEAR`, no unaccepted builder mismatch, and no unresolved critic
finding; otherwise reopen the first affected branch in dependency order.

## Mechanical Evidence Helpers

Use the bundled inspector when it supports the input formats available. Pass it
the regular files from the closed evidence set and interpret its observation
inventory beside the structural sources and renders:

```bash
python3 <skill-dir>/scripts/inspect_evidence.py \
  <scratch>/inspect source.docx source.tex reference.pdf
```

For a user-named directory, enumerate the regular files physically contained in
that directory recursively. Treat a symlink target as additional evidence after
the user names it. Invoke the inspector with the resulting files, read extracted
text page by page beside the page render, and inspect the original source to
recover semantics and reading order.

Render Typst with the project's established command and font paths. Render DOCX
or other editable formats with the application that produced or officially
exports them when available. Record tool versions when renderer differences
might explain a remaining difference.

Use the PDF comparator for disposable all-page evidence:

```bash
python3 <skill-dir>/scripts/compare_pdfs.py scan \
  reference.pdf candidate.pdf <scratch>/scan --dpi 200

python3 <skill-dir>/scripts/compare_pdfs.py detail \
  <scratch>/scan <scratch>/detail --finding <finding-id> --dpi 300
```

Here `<scratch>` is the run's single system-temporary scratch root. Prepare the
named subdirectory as new or empty when the helper requires it, and place all
such disposable trees in that scratch root.

Read `index.json`, page rasters, overlays, absolute differences, text diffs,
font inventories, bboxes, and projection/band measurements as complementary
signals. Compare the reference and candidate in their native page coordinates.
Choose crops from named document elements and the first region where a mismatch
appears or disappears, including
large pixel hotspots when they correspond to those regions.

Automate compile, render, extract, inventory, count, and observation of each
activating variation's predicted event. Let the project choose its source/case
layout. Use numeric summaries and fixture results to check owner categories,
step 9 observations, named accepted mismatches, and Finish conditions.

Read [implementation patterns](references/implementation-patterns.md) when
content-dependent layout or ownership is unclear. Read the
[visual comparison playbook](references/validation-playbook.md) when a remaining difference
needs focused diagnosis. These references supply implementation and diagnostic
guidance; the Element Completion Loop owns artifact choice and acceptance.

Load each short Typst or CSL tip when its named issue becomes active:

- [preserving a standard element's natural size, flow, counters, labels, and links when adding a wrapper, helper, or manual rendering](references/typst-tip-preserve-built-in-behavior.md);
- [natural width versus wrapped extent](references/typst-tip-natural-width.md);
- [source baseline pitch versus Typst leading](references/typst-tip-line-pitch.md);
- [Word-origin font sources under WSL](references/typst-tip-word-font-sources.md);
- [TeX-rendered font sources and Type 1 limitations](references/typst-tip-tex-font-sources.md);
- [reusing the same Typst font environment](references/typst-tip-font-resolution.md);
- [combined math accents](references/typst-tip-combined-accents.md);
- [run-in labels and continuation-line alignment](references/typst-tip-run-in-label-continuation.md);
- [stable author and affiliation identifiers](references/typst-tip-author-affiliation-identifiers.md);
- [display content and PDF metadata types](references/typst-tip-display-content-metadata.md);
- [localized standard references and CJK lexical boundaries](references/typst-tip-localized-references.md);
- [numeric citation brackets and vertical position](references/typst-tip-csl-citation-number.md);
- [CSL default language](references/typst-tip-csl-default-locale.md);
- [publication-specific CSL term overrides](references/typst-tip-csl-term-overrides.md);
- [first-line indentation on injected prose](references/typst-tip-injected-paragraph.md).

These references supply reusable techniques. Derive target values and publication policies from source evidence.

## Judgment Guide

Use positive evidence to distinguish:

- author content from reusable template policy;
- fixed publication dimensions from content-dependent extents;
- deliberate line/page breaks from natural flow;
- font or glyph substitution from geometry drift;
- upstream container errors from downstream accumulated displacement;
- asset differences from layout differences;
- renderer-only raster differences from structural differences.

Classify a remaining difference as renderer-only after exact content, semantic structure,
applicable font/glyph choice, line formation, strokes, and governing layout
rules agree. Use disagreement in any of those relations to continue causal
inspection.

Treat a uniform block displacement as evidence to inspect its shared
alignment, inset, or placement rule. Treat accumulating vertical drift as
evidence to inspect the earliest repeated line pitch or block spacing. Treat
matching text anchors with differing rules as evidence to inspect strokes.
Treat a wrong image extent as evidence to inspect its intrinsic asset, sizing,
fit, and container width. First inspect the implicated element and its parents;
then choose a repair from the semantic and structural evidence.

## Finish

Finish when a new author can perform every author action recorded in valid
closure entries through the public wrapper/functions and standard Typst content,
while the template owns publication policy. The
official instance and justified variations must render robustly, every reference
page must be inspected, and each recorded mismatch must be repaired and retested
or individually accepted by the user. Apply the step 9 closure records and final
critic conditions below to decide whether Finish conditions hold.

After the last change to the template, usage, asset, bibliography data, or style,
compile the official instance and every variation case recorded in valid closure
entries from the current source. Recheck every font requirement and font comparison against those compiled PDFs and
mark them observed only after that compile; do not enter final review while the font gate is open. Enter the final iteration of the Author-Usage
Critic Loop: run the fresh
critic and the builder's raw-source, all-reference-page, all-varied-page, public
API, ownership, and render audit concurrently while those current files remain
unchanged.
The Finish conditions require all step 9 official relations, activating
variations, and owner assignments together. For any unaccepted mismatch or
critic finding, locate
its source rule, reopen the first affected branch in dependency order, repair and
retest it, replace its closure entry, and run a new final review.

After every required branch has a valid closure entry, the final critic reports `CLEAR`, the final builder audit records no
unaccepted mismatch, and every critic finding has a resolving retest observation, return the generated template, usage,
variation, and PDF paths with one sentence naming the compiled documents, inspected pages, activated variations, and final
critic status. Leave regenerable bulk renders and superseded iterations in the system-temporary
scratch root. When unavailable source authority or a required user choice leaves
a closure field unresolved, consult the user and keep that branch active until
the decision is available.
