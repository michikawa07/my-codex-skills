import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

import check_fixtures as checks


class CheckFixtureUnitTests(unittest.TestCase):
    def make_project(self, root: Path) -> Path:
        (root / "fixtures").mkdir()
        (root / "evidence").mkdir()
        (root / "template.typ").write_text(
            "#let _private-helper(body) = body\n"
            "#let paper(title: [], body) = { title; body }\n",
            encoding="utf-8",
        )
        sources = {
            "official.typ": '#import "../template.typ": paper\n#show: paper.with(title: [Official])\nOFFICIAL\n',
            "front.typ": '#import "../template.typ": *\n#show: paper.with(title: [Long])\nFRONT-END BODY-START\n',
            "flow.typ": (
                '#import "../template.typ": paper\n#show: paper\n'
                'LIST-START LIST-END LIST-AFTER\nTABLE-START TABLE-END TABLE-AFTER\n'
            ),
        }
        for name, text in sources.items():
            (root / "fixtures" / name).write_text(text, encoding="utf-8")
        (root / "evidence" / "reference.pdf").write_bytes(b"not inspected by load_config")
        config = {
            "template_entry": "template.typ",
            "entry_symbol": "paper",
            "fixtures": [
                {
                    "id": "official", "kind": "official", "source": "fixtures/official.typ",
                    "reference_pdf": "evidence/reference.pdf", "required_text": ["OFFICIAL"],
                    "geometry_tolerance_pt": 0.1,
                    "text_thresholds": {
                        "reference_coverage": 0.95, "candidate_precision": 0.95,
                        "ordered_similarity": 0.90,
                    },
                },
                {
                    "id": "front", "kind": "frontmatter", "source": "fixtures/front.typ",
                    "ordered_text": ["FRONT-END", "BODY-START"],
                },
                {
                    "id": "flow", "kind": "body-flow", "source": "fixtures/flow.typ",
                    "minimum_pages": 2,
                    "page_flows": [
                        {"start": "LIST-START", "end": "LIST-END", "following": "LIST-AFTER"},
                        {"start": "TABLE-START", "end": "TABLE-END", "following": "TABLE-AFTER"},
                    ],
                },
            ],
        }
        path = root / "checks.json"
        path.write_text(json.dumps(config), encoding="utf-8")
        return path

    def test_config_is_closed(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = self.make_project(Path(temporary))
            value = json.loads(path.read_text())
            value["profile"] = "academic-paper-v1"
            path.write_text(json.dumps(value), encoding="utf-8")
            with self.assertRaisesRegex(checks.InputError, "unknown=profile"):
                checks.load_config(path)
        with tempfile.TemporaryDirectory() as temporary:
            path = self.make_project(Path(temporary))
            value = json.loads(path.read_text())
            value["fixtures"][1]["metadata_policy"] = {}
            path.write_text(json.dumps(value), encoding="utf-8")
            with self.assertRaisesRegex(checks.InputError, "unknown=metadata_policy"):
                checks.load_config(path)
        with tempfile.TemporaryDirectory() as temporary:
            path = self.make_project(Path(temporary))
            value = json.loads(path.read_text())
            value["required_fonts"] = ["worker-selected"]
            path.write_text(json.dumps(value), encoding="utf-8")
            with self.assertRaisesRegex(checks.InputError, "unknown=required_fonts"):
                checks.load_config(path)

    def test_config_requires_exactly_three_unique_kinds(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = self.make_project(Path(temporary))
            value = json.loads(path.read_text())
            value["fixtures"][2]["kind"] = "frontmatter"
            path.write_text(json.dumps(value), encoding="utf-8")
            with self.assertRaisesRegex(checks.InputError, "one unique"):
                checks.load_config(path)

    def test_config_rejects_weakened_official_contract(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = self.make_project(Path(temporary))
            value = json.loads(path.read_text())
            value["fixtures"][0]["text_thresholds"]["reference_coverage"] = 0.94
            path.write_text(json.dumps(value), encoding="utf-8")
            with self.assertRaisesRegex(checks.InputError, "at least 0.95"):
                checks.load_config(path)
            value["fixtures"][0]["text_thresholds"]["reference_coverage"] = 0.95
            value["fixtures"][0]["geometry_tolerance_pt"] = 0.11
            path.write_text(json.dumps(value), encoding="utf-8")
            with self.assertRaisesRegex(checks.InputError, "between 0 and 0.1"):
                checks.load_config(path)
            value["fixtures"][0]["geometry_tolerance_pt"] = 0.1
            value["comparison_dpi"] = 299
            path.write_text(json.dumps(value), encoding="utf-8")
            with self.assertRaisesRegex(checks.InputError, "300 to 1200"):
                checks.load_config(path)

    def test_body_flow_requires_list_and_table_flow_contracts(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = self.make_project(Path(temporary))
            value = json.loads(path.read_text())
            value["fixtures"][2]["page_flows"] = value["fixtures"][2]["page_flows"][:1]
            path.write_text(json.dumps(value), encoding="utf-8")
            with self.assertRaisesRegex(checks.InputError, "at least two"):
                checks.load_config(path)

    def test_source_lint_accepts_named_and_wildcard_imports(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = self.make_project(Path(temporary))
            config = checks.load_config(path)
            for fixture in config["fixtures"][:2]:
                result = checks.lint_source(config["template"], fixture["source"], "paper")
                self.assertEqual(result["entry_symbol"], "paper")

    def test_source_lint_rejects_shadow_and_private_use(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = self.make_project(Path(temporary))
            config = checks.load_config(path)
            fixture = config["fixtures"][0]["source"]
            fixture.write_text(
                '#import "../template.typ": paper\n#let paper(body) = body\n#show: paper\n',
                encoding="utf-8",
            )
            with self.assertRaisesRegex(checks.InputError, "shadows"):
                checks.lint_source(config["template"], fixture, "paper")
            fixture.write_text(
                '#import "../template.typ": *\n#show: paper\n#_private-helper[bad]\n',
                encoding="utf-8",
            )
            with self.assertRaisesRegex(checks.InputError, "private template symbol"):
                checks.lint_source(config["template"], fixture, "paper")

    def test_source_lint_rejects_symbol_mentioned_only_as_text(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = self.make_project(Path(temporary))
            config = checks.load_config(path)
            fixture = config["fixtures"][0]["source"]
            fixture.write_text(
                '#import "../template.typ": paper\nThe word "paper" is not a wrapper call.\n',
                encoding="utf-8",
            )
            with self.assertRaisesRegex(checks.InputError, "does not call/show"):
                checks.lint_source(config["template"], fixture, "paper")
            fixture.write_text(
                '#import "../template.typ": paper\npaper() is rendered prose, not Typst code.\n',
                encoding="utf-8",
            )
            with self.assertRaisesRegex(checks.InputError, "does not call/show"):
                checks.lint_source(config["template"], fixture, "paper")

    def test_text_metrics_preserve_order_signal(self):
        metrics = checks.text_metrics(["ABC ABC"], ["CBA CBA"])
        self.assertEqual(metrics["reference_coverage"], 1.0)
        self.assertEqual(metrics["candidate_precision"], 1.0)
        self.assertLess(metrics["ordered_similarity"], 0.8)
        normalized = checks.text_metrics(["Ａ B\nC"], ["A B C"])
        self.assertEqual(normalized["ordered_similarity"], 1.0)

    def test_locked_text_must_come_from_reference_and_candidate(self):
        result = checks.locked_required_text_checks(
            ["REFERENCE CONTENT"], ["REFERENCE CONTENT CANDIDATE-ONLY"], ["CANDIDATE-ONLY"],
        )
        self.assertFalse(result["pass"])
        self.assertFalse(result["reference"]["pass"])
        self.assertTrue(result["candidate"]["pass"])

    def test_page_flow_requires_unique_natural_crossing(self):
        flow = [{"start": "LIST-START", "end": "LIST-END", "following": "LIST-AFTER"}]
        passing = checks.page_flow_checks(["LIST-START", "LIST-END LIST-AFTER"], flow)
        self.assertTrue(passing["pass"])
        same_page = checks.page_flow_checks(["LIST-START LIST-END LIST-AFTER"], flow)
        self.assertFalse(same_page["pass"])
        duplicate = checks.page_flow_checks(["LIST-START", "LIST-END LIST-END LIST-AFTER"], flow)
        self.assertFalse(duplicate["pass"])

    def test_geometry_checks_boxes_and_font_subset_names(self):
        reference = {
            "pages": 1,
            "geometry": [{
                "page": 1, "width_pt": 100.0, "height_pt": 200.0, "rotation": 0,
                "MediaBox": [0.0, 0.0, 100.0, 200.0], "CropBox": [0.0, 0.0, 100.0, 200.0],
            }],
        }
        candidate = json.loads(json.dumps(reference))
        candidate["geometry"][0]["CropBox"][2] = 100.2
        self.assertFalse(checks.geometry_metrics(reference, candidate, 0.1)["pass"])
        same = checks.embedded_font_comparison(
            ["ABCDEF+TimesNewRomanPSMT", "ArialMT"],
            ["UVWXYZ+TimesNewRomanPSMT", "ArialMT"],
        )
        self.assertTrue(same["pass"])
        changed = checks.embedded_font_comparison(
            ["ABCDEF+TimesNewRomanPSMT", "ArialMT"],
            ["UVWXYZ+TimesNewRomanPSMT", "NewCMMath-Book"],
        )
        self.assertFalse(changed["pass"])
        self.assertEqual(changed["missing_reference_faces"], [["ArialMT"]])
        self.assertEqual(changed["extra_candidate_faces"], [["NewCMMath-Book"]])
        self.assertFalse(checks.font_family_match("Arial", "Arial-BoldMT"))

    def test_source_inventory_reports_line_evidence_without_banning(self):
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "fixture.typ"
            source.write_text(
                "#place(dx: 2mm, dy: -1pt)[Author choice]\n"
                "#v(-4mm)\n"
                "#figure(rect(width: 10mm), caption: [Caption])\n",
                encoding="utf-8",
            )
            inventory = checks.source_layout_inventory(source)
            self.assertTrue(inventory["observation_only"])
            self.assertEqual([item["line"] for item in inventory["records"]], [1, 2, 3])
            self.assertIn("-4mm", inventory["records"][1]["absolute_dimensions"])
            self.assertIn("place", inventory["records"][0]["constructs"])

    def test_bibliography_and_standard_structure_inventory(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            path = self.make_project(root)
            style = root / "style.csl"
            style.write_text("style", encoding="utf-8")
            value = json.loads(path.read_text())
            value["bibliography_style_asset"] = "style.csl"
            path.write_text(json.dumps(value), encoding="utf-8")
            with self.assertRaisesRegex(checks.InputError, "requires bibliography_data"):
                checks.load_config(path)

            source = root / "structures.typ"
            source.write_text(
                "A citation @source.\n$ x = 1 $\n"
                "#figure(rect(width: 10pt), caption: [Observed caption])\n"
                '#bibliography("refs.bib")\n',
                encoding="utf-8",
            )
            bibliography = checks.bibliography_semantics(source)
            structures = checks.standard_structure_inventory(source)
            self.assertTrue(bibliography["has_citation"])
            self.assertTrue(bibliography["has_bibliography"])
            self.assertTrue(structures["has_display_equation"])
            self.assertTrue(structures["has_figure_caption"])

    def test_repair_targets_expose_positive_values_and_correction_directions(self):
        first = {
            "page": 1, "tokens": ["ABSTRACT", "FIXTURE", "TEXT"], "token_count": 3,
            "reference_line": 1, "candidate_line": 1, "deltas": {
                "left_dx_pt": 2.0, "center_dx_pt": 2.0, "top_dy_pt": -0.5,
            },
            "reference": {"left_pt": 10.0, "center_x_pt": 20.0, "top_pt": 20.0},
            "candidate": {"left_pt": 12.0, "center_x_pt": 22.0, "top_pt": 19.5},
        }
        maximum = {
            "page": 1, "tokens": ["BODY", "FLOW", "TEXT"], "token_count": 3,
            "reference_line": 2, "candidate_line": 2, "deltas": {
                "left_dx_pt": 4.0, "center_dx_pt": 4.0, "top_dy_pt": 9.0,
            },
            "reference": {"left_pt": 11.0, "center_x_pt": 16.0, "top_pt": 40.0},
            "candidate": {"left_pt": 15.0, "center_x_pt": 20.0, "top_pt": 49.0},
        }
        equation = {
            "index": 1, "reference_number": "(1)", "candidate_number": "(1)",
            "reference_page": 1, "candidate_page": 1,
            "reference_number_left_pt": 180.0, "candidate_number_left_pt": 182.0,
            "reference_number_top_pt": 100.0, "candidate_number_top_pt": 101.0,
            "reference_body_left_pt": 70.0, "candidate_body_left_pt": 72.0,
            "deltas": {"number_left_dx_pt": 2.0, "number_top_dy_pt": 1.0, "body_left_dx_pt": 2.0},
        }
        structure = {
            "page": 1, "tile": "p001-r001-c001-tile", "box_pt": [0, 0, 50, 50],
            "failures": ["local dense row/column structure differs"],
            "reference": {"ink": {"center_x": 10, "center_y": 10, "width": 20, "height": 10}},
            "candidate": {"ink": {"center_x": 12, "center_y": 10, "width": 20, "height": 10}},
            "deltas": {"center_dx_pt": 0.48, "center_dy_pt": 0.0, "width_delta_pt": 0.0, "height_delta_pt": 0.0},
            "structure_deltas": [{
                "direction": "horizontal_bands", "band": 0, "edge": "start",
                "reference_pt": 4.0, "candidate_pt": 5.2, "delta_pt": 1.2,
            }],
        }
        report = {"fixtures": [{"kind": "official", "official": {
            "embedded_fonts": {
                "pass": False, "reference": {"arial": ["Arial"]},
                "candidate": {"newcm": ["NewCM"]},
                "missing_reference_faces": [["Arial"]], "extra_candidate_faces": [["NewCM"]],
            },
            "layout_preflight": {"pages": [{
                "page": 1, "earliest_coherent_divergence": first,
                "maximum_coherent_divergence": maximum,
            }]},
            "equation_preflight": {"expected_equations": 1, "violations": [equation]},
            "comparison": {"structure_gate": {
                "dpi": 300, "pages": [{"page": 1, "representative_violation": structure}],
            }},
        }}]}
        targets, truncated = checks.build_repair_targets(report)
        self.assertFalse(truncated)
        self.assertEqual([item["kind"] for item in targets], [
            "font_inventory", "equation_anchor", "text_anchor", "local_structure",
        ])
        self.assertEqual([item["priority"] for item in targets], [1, 2, 3, 4])
        self.assertEqual(targets[0]["delta"]["missing_reference_faces"], [["Arial"]])
        self.assertEqual(targets[1]["equations"][0]["reference"]["number_left_pt"], 180.0)
        self.assertEqual(targets[1]["equations"][0]["candidate"]["number_left_pt"], 182.0)
        self.assertEqual(targets[2]["earliest"]["tokens"][0], "ABSTRACT")
        self.assertEqual(targets[2]["maximum"]["delta"]["top_dy_pt"], 9.0)
        self.assertEqual(targets[2]["maximum"]["correction_to_reference"]["top_dy_pt"], -9.0)
        representative = targets[3]["representative"]
        self.assertEqual(representative["source"], "dense structure band")
        self.assertEqual((representative["reference"], representative["candidate"], representative["delta"]), (4.0, 5.2, 1.2))
        self.assertIn("up 1.200 pt", targets[3]["correction_direction"])
        self.assertIn("missing=1 extra=1", checks.repair_target_summary(targets[0]))
        self.assertIn("180.000->182.000", checks.repair_target_summary(targets[1]))
        self.assertIn("40.000->49.000", checks.repair_target_summary(targets[2]))
        self.assertIn("4.000->5.200", checks.repair_target_summary(targets[3]))

    def test_repair_targets_are_capped_without_changing_gate_status(self):
        pages = []
        for page in range(1, 20):
            violation = {
                "page": page, "text": f"P{page}",
                "deltas": {"left_dx_pt": float(page), "center_dx_pt": float(page), "top_dy_pt": 0.0},
                "reference": {"left_pt": 1.0, "top_pt": 1.0, "right_pt": 2.0, "bottom_pt": 2.0},
                "candidate": {"left_pt": 1.0 + page, "top_pt": 1.0, "right_pt": 2.0 + page, "bottom_pt": 2.0},
            }
            violation.update({
                "tokens": [f"P{page}", "CONTEXT", "TOKEN"], "token_count": 3,
                "reference_line": 1, "candidate_line": 1,
            })
            pages.append({
                "page": page, "earliest_coherent_divergence": violation,
                "maximum_coherent_divergence": violation,
            })
        equation = {
            "index": 1, "reference_number": "(1)", "candidate_number": "(1)",
            "reference_page": 1, "candidate_page": 1,
            "reference_number_left_pt": 90.0, "candidate_number_left_pt": 91.0,
            "reference_number_top_pt": 50.0, "candidate_number_top_pt": 50.0,
            "reference_body_left_pt": 30.0, "candidate_body_left_pt": 31.0,
            "deltas": {"number_left_dx_pt": 1.0, "number_top_dy_pt": 0.0, "body_left_dx_pt": 1.0},
        }
        report = {"status": "fail", "fixtures": [{"kind": "official", "official": {
            "embedded_fonts": {"pass": True}, "layout_preflight": {"pages": pages},
            "equation_preflight": {"violations": [equation]}, "comparison": {"structure_gate": {"pages": []}},
        }}]}
        targets, truncated = checks.build_repair_targets(report)
        self.assertTrue(truncated)
        self.assertEqual(len(targets), checks.REPAIR_TARGET_LIMIT)
        self.assertEqual(targets[0]["kind"], "equation_anchor")
        self.assertEqual(report["status"], "fail")

    def test_coherent_clusters_reject_isolated_repeated_word_maximum(self):
        def word(text, left, top, line=1):
            return {
                "page": 1, "line": line, "text": text, "left_pt": left, "top_pt": top,
                "right_pt": left + 8, "bottom_pt": top + 5, "center_x_pt": left + 4,
                "center_y_pt": top + 2.5,
            }

        coherent_reference = [word(text, left, 10) for text, left in zip(("A", "B", "C"), (10, 20, 30))]
        coherent_candidate = [word(text, left + 2, 11) for text, left in zip(("A", "B", "C"), (10, 20, 30))]
        repeated_reference = word("manuscript", 10, 30, line=2)
        repeated_candidate = word("manuscript", 447, 30, line=9)
        clusters = checks.coherent_anchor_clusters([
            list(zip(coherent_reference, coherent_candidate)),
            [(repeated_reference, repeated_candidate)],
        ])
        self.assertEqual(len(clusters), 1)
        self.assertEqual(clusters[0]["tokens"], ["A", "B", "C"])
        self.assertEqual(clusters[0]["deltas"]["left_dx_pt"], 2)


def integration_tools_available() -> bool:
    commands = ("typst", "pdfinfo", "pdffonts", "pdftotext", "pdftoppm")
    imagemagick = shutil.which("magick") or all(shutil.which(name) for name in ("compare", "convert", "identify"))
    return all(shutil.which(name) for name in commands) and bool(imagemagick)


@unittest.skipUnless(integration_tools_available(), "Typst, Poppler, and ImageMagick are required")
class CheckFixtureIntegrationTests(unittest.TestCase):
    def test_three_fixture_compile_and_compare(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "fixtures").mkdir()
            (root / "evidence").mkdir()
            (root / "template.typ").write_text(
                "#let _internal-gap = 2pt\n"
                "#let paper(title: [], body) = {\n"
                "  set page(paper: \"a4\", margin: 20mm)\n"
                "  set math.equation(numbering: \"(1)\", number-align: right)\n"
                "  if title != [] { title; parbreak() }\n"
                "  body\n"
                "}\n",
                encoding="utf-8",
            )
            (root / "references.bib").write_text(
                "@article{fixture,\n"
                "  author = {Doe, Jane},\n"
                "  title = {Fixture Reference},\n"
                "  journal = {Test Journal},\n"
                "  year = {2024}\n"
                "}\n",
                encoding="utf-8",
            )
            official = (
                '#import "../template.typ": paper\n'
                '#show: paper.with(title: [Official title])\n'
                'OFFICIAL REQUIRED TEXT @fixture\n'
                '$ x = 1 $\n'
                '#figure(rect(width: 20pt, height: 10pt), caption: [Official figure caption])\n'
                '#bibliography("../references.bib")\n'
            )
            front = (
                '#import "../template.typ": *\n'
                '#show: paper.with(title: [A deliberately longer frontmatter title])\n'
                'FRONTMATTER-LAST\nBODY-FIRST\n'
            )
            list_items = ["- LIST-START First naturally flowing list item with ordinary body text."]
            list_items.extend(
                f"- List item {index} contains enough ordinary prose to exercise natural wrapping and pagination."
                for index in range(1, 90)
            )
            list_items.append("- LIST-END Final naturally flowing list item.")
            table_cells = ["[TABLE-START], [First naturally flowing table row],"]
            table_cells.extend(
                f"[{index}], [Table row {index} contains ordinary breakable content],"
                for index in range(1, 100)
            )
            table_cells.append("[TABLE-END], [Final naturally flowing table row],")
            flow = (
                '#import "../template.typ": paper\n#show: paper.with(title: [Flow])\n'
                + "\n".join(list_items)
                + "\n\nLIST-AFTER\n\n#table(\n  columns: (1fr, 3fr),\n"
                + "\n".join("  " + cell for cell in table_cells)
                + "\n)\n\nTABLE-AFTER\n\n"
                + "$ y = 2 $\n"
                + "#figure(rect(width: 20pt, height: 10pt), caption: [Flow figure caption])\n"
                + "Flow citation @fixture.\n#bibliography(\"../references.bib\")\n"
            )
            for name, source in (("official.typ", official), ("front.typ", front), ("flow.typ", flow)):
                (root / "fixtures" / name).write_text(source, encoding="utf-8")
            reference = root / "evidence" / "official.pdf"
            subprocess.run(
                ["typst", "compile", "--root", str(root), str(root / "fixtures" / "official.typ"), str(reference)],
                check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            )
            config = {
                "template_entry": "template.typ", "entry_symbol": "paper", "comparison_dpi": 300,
                "bibliography_data": "references.bib",
                "fixtures": [
                    {
                        "id": "official", "kind": "official", "source": "fixtures/official.typ",
                        "reference_pdf": "evidence/official.pdf", "required_text": ["OFFICIAL REQUIRED TEXT"],
                        "geometry_tolerance_pt": 0.1,
                        "text_thresholds": {
                            "reference_coverage": 1.0, "candidate_precision": 1.0,
                            "ordered_similarity": 1.0,
                        },
                    },
                    {
                        "id": "frontmatter", "kind": "frontmatter", "source": "fixtures/front.typ",
                        "ordered_text": ["FRONTMATTER-LAST", "BODY-FIRST"],
                    },
                    {
                        "id": "body-flow", "kind": "body-flow", "source": "fixtures/flow.typ",
                        "minimum_pages": 3,
                        "page_flows": [
                            {"start": "LIST-START", "end": "LIST-END", "following": "LIST-AFTER"},
                            {"start": "TABLE-START", "end": "TABLE-END", "following": "TABLE-AFTER"},
                        ],
                    },
                ],
            }
            config_path = root / "checks.json"
            config_path.write_text(json.dumps(config), encoding="utf-8")
            report = checks.run(config_path, root / "audit")
            self.assertEqual(report["status"], "pass", report["failures"])
            self.assertEqual(len(report["fixtures"]), 3)
            official_result = next(item for item in report["fixtures"] if item["kind"] == "official")
            self.assertTrue(official_result["official"]["geometry"]["pass"])
            self.assertEqual(official_result["official"]["text_metrics"]["ordered_similarity"], 1.0)
            self.assertTrue(official_result["official"]["locked_required_text"]["pass"])
            self.assertTrue(official_result["official"]["embedded_fonts"]["pass"])
            self.assertTrue(official_result["official"]["layout_preflight"]["pass"])
            self.assertTrue(official_result["official"]["equation_preflight"]["pass"])
            self.assertEqual(report["repair_targets"], [])
            self.assertFalse(report["repair_targets_truncated"])
            self.assertIn("repair_targets: 0", (root / "audit" / "summary.txt").read_text())
            self.assertTrue(official_result["bibliography_dependencies"]["data_consumed"])
            self.assertTrue(official_result["dependencies"]["template_consumed"])
            self.assertTrue((root / "audit" / "comparison" / "index.json").is_file())
            flow_result = next(item for item in report["fixtures"] if item["kind"] == "body-flow")
            self.assertNotIn("#pagebreak", (root / "fixtures" / "flow.typ").read_text())
            for contract in flow_result["page_flow"]["flows"]:
                self.assertLess(contract["pages"]["start"], contract["pages"]["end"])

    def test_layout_preflight_passes_aligned_and_rejects_center_half_or_two_point_shift(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            sources = {
                "reference.typ": '#set page(width: 200pt, height: 100pt, margin: 10pt)\n#align(left)[ANCHOR TEXT]\n',
                "center.typ": '#set page(width: 200pt, height: 100pt, margin: 10pt)\n#align(center)[ANCHOR TEXT]\n',
                "half.typ": '#set page(width: 200pt, height: 100pt, margin: 10pt)\n#move(dx: 0.5pt)[ANCHOR TEXT]\n',
                "shift.typ": '#set page(width: 200pt, height: 100pt, margin: 10pt)\n#move(dx: 2pt)[ANCHOR TEXT]\n',
            }
            pdfs = {}
            for name, source in sources.items():
                typ = root / name
                typ.write_text(source, encoding="utf-8")
                pdf = root / name.replace(".typ", ".pdf")
                subprocess.run(
                    ["typst", "compile", str(typ), str(pdf)],
                    check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                )
                pdfs[name] = pdf
            self.assertTrue(checks.line_layout_preflight(pdfs["reference.typ"], pdfs["reference.typ"])["pass"])
            centered = checks.line_layout_preflight(pdfs["reference.typ"], pdfs["center.typ"])
            half = checks.line_layout_preflight(pdfs["reference.typ"], pdfs["half.typ"])
            shifted = checks.line_layout_preflight(pdfs["reference.typ"], pdfs["shift.typ"])
            self.assertFalse(centered["pass"])
            self.assertFalse(half["pass"])
            self.assertFalse(shifted["pass"])
            self.assertEqual(half["tolerance_pt"], 0.25)
            self.assertEqual(shifted["tolerance_pt"], 0.25)
            self.assertGreater(abs(half["maximum_displacement"]["left_dx_pt"]), 0.49)
            self.assertGreater(abs(shifted["maximum_displacement"]["left_dx_pt"]), 1.9)


@unittest.skipUnless(
    os.environ.get("BUILD_TYPST_TEMPLATE_REGRESSION_ROOT"),
    "set BUILD_TYPST_TEMPLATE_REGRESSION_ROOT to run retained bad-pair regressions",
)
class RetainedBadPairRegressionTests(unittest.TestCase):
    def test_robomech_and_mecj_bad_pairs_fail_both_official_preflights(self):
        root = Path(os.environ["BUILD_TYPST_TEMPLATE_REGRESSION_ROOT"]).resolve()
        pairs = {
            "robomech": (
                root / "tmp_skill_test/robomech_typst_eval_lean1/fixtures/official.typ",
                root / "tmp_skill_test/robomech_typst_eval_lean1/evidence/official.pdf",
                root / "tmp_skill_test/robomech_typst_eval_lean1/audit/run-final/pdf/official.pdf",
            ),
            "mecj": (
                root / "tmp_skill_test/mecj_word_typst_eval_lean1/fixtures/official.typ",
                root / "tmp_skill_test/mecj_word_typst_eval_lean1/evidence/official.pdf",
                root / "tmp_skill_test/mecj_word_typst_eval_lean1/audit/run-final-4/pdf/official.pdf",
            ),
        }
        for name, (source, reference, candidate) in pairs.items():
            with self.subTest(name=name):
                for path in (source, reference, candidate):
                    self.assertTrue(path.is_file(), path)
                equation_count = len(checks.standard_structure_inventory(source)["display_equations"])
                anchors = checks.line_layout_preflight(reference, candidate)
                aligned_equations = checks.equation_anchor_preflight(reference, reference, equation_count)
                bad_equations = checks.equation_anchor_preflight(reference, candidate, equation_count)
                with tempfile.TemporaryDirectory() as temporary:
                    scan = Path(temporary) / "scan"
                    subprocess.run(
                        [
                            sys.executable, str(SCRIPTS / "compare_pdfs.py"), "scan",
                            str(reference), str(candidate), str(scan), "--dpi", "300",
                        ],
                        check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                    )
                    structure = checks.local_ink_structure_gate(scan / "index.json")
                self.assertFalse(anchors["pass"])
                self.assertTrue(aligned_equations["pass"])
                self.assertFalse(bad_equations["pass"])
                self.assertFalse(structure["pass"])
                self.assertEqual(anchors["tolerance_pt"], 0.25)
                self.assertEqual(structure["tolerance_pt"], 0.25)
                self.assertGreater(anchors["violation_count"], 0)
                self.assertGreater(bad_equations["violation_count"], 0)
                self.assertGreater(structure["violation_count"], 0)
                repair_report = {"fixtures": [{"kind": "official", "official": {
                    "embedded_fonts": {"pass": True}, "layout_preflight": anchors,
                    "equation_preflight": bad_equations,
                    "comparison": {"structure_gate": structure},
                }}]}
                repair_targets, truncated = checks.build_repair_targets(repair_report)
                self.assertFalse(truncated)
                target_kinds = [target["kind"] for target in repair_targets]
                expected_layout_pages = {
                    page["page"] for page in anchors["pages"] if page["coherent_violation_count"]
                }
                if expected_layout_pages:
                    self.assertLess(target_kinds.index("equation_anchor"), target_kinds.index("text_anchor"))
                self.assertEqual(
                    {target["page"] for target in repair_targets if target["kind"] == "text_anchor"},
                    expected_layout_pages,
                )
                self.assertEqual(
                    {target["page"] for target in repair_targets if target["kind"] == "local_structure"},
                    {page["page"] for page in structure["pages"] if page["violation_count"]},
                )


if __name__ == "__main__":
    unittest.main()
