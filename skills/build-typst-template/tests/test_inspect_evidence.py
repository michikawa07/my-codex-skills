import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

import inspect_evidence as evidence


class InspectEvidenceTests(unittest.TestCase):
    def test_text_and_docx_inventory(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            tex = root / "source.tex"
            tex.write_text(r"\def\title#1{#1}" + "\n" + r"\newcommand{\keywords}[1]{#1}", encoding="utf-8")
            docx = root / "source.docx"
            with zipfile.ZipFile(docx, "w") as archive:
                archive.writestr(
                    "word/document.xml",
                    '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
                    '<w:body><w:p/><w:tbl/><w:sectPr><w:pgSz w:w="11906" w:h="16838"/></w:sectPr></w:body>'
                    '</w:document>',
                )
            report = evidence.inspect([tex, docx], root / "out")
            tex_record = next(item for item in report["evidence"] if item["suffix"] == ".tex")
            docx_record = next(item for item in report["evidence"] if item["suffix"] == ".docx")
            self.assertEqual(tex_record["text"]["tex_definitions"], ["keywords", "title"])
            self.assertEqual(docx_record["docx"]["table_count"], 1)
            self.assertEqual(docx_record["docx"]["paragraph_count"], 1)

    def test_docx_property_facts_and_limited_style_resolution(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            docx = root / "properties.docx"
            document = '''
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"
 xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
 xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math"
 xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"
 xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">
 <w:body>
  <w:p>
   <w:pPr><w:pStyle w:val="BodyText"/><w:jc w:val="center"/><w:textAlignment w:val="top"/>
    <w:spacing w:before="40" w:line="240" w:lineRule="auto"/><w:ind w:left="720"/>
    <w:tabs><w:tab w:val="right" w:pos="9000" w:leader="dot"/></w:tabs>
    <w:keepNext/><w:pageBreakBefore w:val="0"/><w:rPr><w:sz w:val="24"/></w:rPr>
   </w:pPr>
   <w:r><w:rPr><w:b/><w:i w:val="1"/><w:spacing w:val="5"/><w:w w:val="90"/>
    <w:vertAlign w:val="superscript"/></w:rPr><w:t>Hello </w:t>
    <w:drawing><wp:inline><wp:extent cx="1270000" cy="2540000"/>
     <wp:docPr id="7" name="Figure 1" descr="fixture image"/>
     <a:graphic><a:graphicData><a:blip r:embed="rId9"/></a:graphicData></a:graphic>
    </wp:inline></w:drawing></w:r>
   <w:r><w:t>world</w:t></w:r><m:oMath/><w:bookmarkStart w:id="0" w:name="mark"/>
  </w:p>
  <w:p><w:pPr><w:sectPr><w:pgSz w:w="10000" w:h="15000"/><w:cols w:num="1"/></w:sectPr></w:pPr>
   <w:r><w:t>Plain</w:t></w:r></w:p>
  <w:tbl>
   <w:tblPr><w:tblStyle w:val="TableGrid"/><w:tblW w:w="6000" w:type="dxa"/><w:jc w:val="center"/>
    <w:tblCellMar><w:top w:w="80" w:type="dxa"/><w:start w:w="100" w:type="dxa"/>
     <w:bottom w:w="80" w:type="dxa"/><w:end w:w="100" w:type="dxa"/></w:tblCellMar>
    <w:tblBorders><w:top w:val="single" w:sz="8" w:color="000000"/>
     <w:insideH w:val="single" w:sz="4"/></w:tblBorders>
   </w:tblPr>
   <w:tblGrid><w:gridCol w:w="2400"/><w:gridCol w:w="3600"/></w:tblGrid>
   <w:tr><w:trPr><w:trHeight w:val="310" w:hRule="atLeast"/><w:tblHeader/><w:cantSplit/></w:trPr>
    <w:tc><w:tcPr><w:tcW w:w="2400" w:type="dxa"/><w:gridSpan w:val="2"/>
      <w:vMerge w:val="restart"/><w:vAlign w:val="center"/>
      <w:tcMar><w:top w:w="40" w:type="dxa"/></w:tcMar>
      <w:tcBorders><w:bottom w:val="double" w:sz="6"/></w:tcBorders>
     </w:tcPr><w:p><w:r><w:t>Cell A</w:t></w:r></w:p></w:tc>
    <w:tc><w:p><w:r><w:t>Cell B</w:t></w:r></w:p></w:tc>
   </w:tr>
  </w:tbl>
  <w:sectPr><w:headerReference w:type="default" r:id="rId1"/>
   <w:footerReference w:type="default" r:id="rId2"/>
   <w:pgSz w:w="11906" w:h="16838"/><w:pgMar w:top="1000" w:right="1100" w:bottom="1200" w:left="1300"/>
   <w:cols w:num="2" w:equalWidth="0" w:space="720"><w:col w:w="3000" w:space="360"/>
    <w:col w:w="4000" w:space="420"/></w:cols>
   <w:docGrid w:type="lines" w:linePitch="360"/>
  </w:sectPr>
 </w:body>
</w:document>'''
            styles = '''
<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
 <w:docDefaults><w:pPrDefault><w:pPr><w:spacing w:after="100"/></w:pPr></w:pPrDefault>
  <w:rPrDefault><w:rPr><w:rFonts w:ascii="Times New Roman" w:eastAsia="MS Mincho"/>
   <w:sz w:val="18"/></w:rPr></w:rPrDefault></w:docDefaults>
 <w:style w:type="paragraph" w:styleId="Normal" w:default="1"><w:name w:val="Normal"/>
  <w:pPr><w:spacing w:after="120"/><w:ind w:left="100"/></w:pPr><w:rPr><w:sz w:val="20"/></w:rPr>
 </w:style>
 <w:style w:type="paragraph" w:styleId="BodyText"><w:name w:val="Body Text"/>
  <w:basedOn w:val="Normal"/><w:pPr><w:spacing w:before="240"/></w:pPr><w:rPr><w:sz w:val="22"/></w:rPr>
 </w:style>
 <w:style w:type="character" w:styleId="Emphasis"><w:name w:val="Emphasis"/>
  <w:rPr><w:i/></w:rPr></w:style>
 <w:style w:type="table" w:styleId="TableGrid"><w:name w:val="Table Grid"/>
  <w:tblPr><w:tblLayout w:type="fixed"/></w:tblPr>
  <w:tcPr><w:tcMar><w:top w:w="60" w:type="dxa"/></w:tcMar></w:tcPr>
 </w:style>
 <w:style w:type="paragraph" w:styleId="MissingParent"><w:basedOn w:val="Ghost"/></w:style>
 <w:style w:type="paragraph" w:styleId="CycleA"><w:basedOn w:val="CycleB"/></w:style>
 <w:style w:type="paragraph" w:styleId="CycleB"><w:basedOn w:val="CycleA"/></w:style>
</w:styles>'''
            with zipfile.ZipFile(docx, "w") as archive:
                archive.writestr("word/document.xml", document)
                archive.writestr("word/styles.xml", styles)
            facts = evidence.docx_inventory(docx)

            section = facts["sections"][-1]
            self.assertEqual(section["page_size"], {"h": "16838", "w": "11906"})
            self.assertEqual(section["margins"]["left"], "1300")
            self.assertEqual([item["w"] for item in section["columns"]["items"]], ["3000", "4000"])
            self.assertEqual(section["headers"][0], {"id": "rId1", "type": "default"})
            self.assertEqual(section["document_grid"], {"linePitch": "360", "type": "lines"})
            self.assertAlmostEqual(section["normalized_points"]["page_size"]["w"], 595.3)

            by_id = {style["style_id"]: style for style in facts["styles"]}
            body = by_id["BodyText"]
            self.assertEqual((body["name"], body["type"], body["based_on"]), ("Body Text", "paragraph", "Normal"))
            self.assertEqual(body["resolved"]["chain"], ["Normal", "BodyText"])
            self.assertEqual(body["resolved"]["paragraph"]["indent"]["left"], "100")
            self.assertEqual(body["resolved"]["paragraph"]["spacing"], {"before": "240"})
            self.assertEqual(body["resolved"]["run"]["fonts"]["ascii"], "Times New Roman")
            self.assertEqual(body["resolved"]["run"]["size_half_points"]["val"], "22")
            self.assertEqual(by_id["MissingParent"]["resolved"]["unresolved_based_on"], "Ghost")
            self.assertIsNotNone(by_id["CycleA"]["resolved"]["cycle_at"])

            paragraph = facts["paragraphs"][0]
            self.assertEqual((paragraph["index"], paragraph["style_id"], paragraph["text"]), (1, "BodyText", "Hello world"))
            self.assertEqual(paragraph["direct"]["paragraph"]["alignment"]["val"], "center")
            self.assertEqual(paragraph["direct"]["paragraph"]["text_alignment"]["val"], "top")
            self.assertEqual(paragraph["direct"]["paragraph"]["spacing"]["lineRule"], "auto")
            self.assertEqual(paragraph["direct"]["paragraph"]["tabs"][0]["pos"], "9000")
            self.assertTrue(paragraph["direct"]["paragraph"]["keep_next"]["value"])
            self.assertFalse(paragraph["direct"]["paragraph"]["page_break_before"]["value"])
            self.assertEqual(paragraph["direct"]["paragraph_mark_run"]["size_half_points"]["val"], "24")
            self.assertTrue(paragraph["runs"][0]["direct"]["bold"]["value"])
            self.assertEqual(paragraph["runs"][0]["direct"]["tracking_twentieth_points"]["val"], "5")
            self.assertEqual((paragraph["math_count"], paragraph["drawing_count"]), (1, 1))
            drawing = paragraph["drawings"][0]
            self.assertEqual((drawing["kind"], drawing["extent"]), ("inline", {"cx": "1270000", "cy": "2540000"}))
            self.assertEqual(drawing["extent_points"], {"width": 100.0, "height": 200.0})
            self.assertEqual(drawing["doc_properties"]["name"], "Figure 1")
            self.assertEqual(drawing["blips"][0]["embed"], "rId9")
            self.assertEqual([event["kind"] for event in paragraph["inline_events"]], ["run", "drawing", "run", "math"])

            table = facts["tables"][0]
            self.assertEqual(table["style_id"], "TableGrid")
            self.assertEqual([column["w"] for column in table["grid"]], ["2400", "3600"])
            self.assertEqual(table["direct"]["width"], {"type": "dxa", "w": "6000"})
            self.assertEqual(table["direct"]["alignment"]["val"], "center")
            self.assertEqual(table["direct"]["cell_margins"]["top"]["w"], "80")
            self.assertEqual(table["direct"]["borders"]["insideH"]["sz"], "4")
            self.assertEqual(table["resolved_style"]["table"]["layout"]["type"], "fixed")
            self.assertEqual(table["resolved_style"]["cell"]["cell_margins"]["top"]["w"], "60")
            self.assertTrue(table["rows"][0]["direct"]["repeat_header"]["value"])
            cell = table["rows"][0]["cells"][0]
            self.assertEqual(cell["direct"]["grid_span"]["val"], "2")
            self.assertEqual(cell["direct"]["vertical_merge"]["val"], "restart")
            self.assertEqual(cell["direct"]["cell_margins"]["top"]["w"], "40")
            self.assertEqual(cell["direct"]["borders"]["bottom"]["val"], "double")
            self.assertEqual(cell["paragraph_ids"], [facts["paragraphs"][2]["id"]])
            self.assertEqual(
                [item["kind"] for item in facts["body_order"]],
                ["paragraph", "paragraph", "section_boundary", "table", "section"],
            )
            self.assertEqual(facts["paragraphs"][1]["section_break_id"], facts["sections"][0]["id"])

    @unittest.skipUnless(
        all(shutil.which(name) for name in ("typst", "pdfinfo", "pdffonts", "pdftotext")),
        "Typst and Poppler are required",
    )
    def test_pdf_pages_and_concatenated_text(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source.typ"
            source.write_text("FIRST PAGE\n#pagebreak()\nSECOND PAGE\n", encoding="utf-8")
            pdf = root / "source.pdf"
            subprocess.run(["typst", "compile", str(source), str(pdf)], check=True)
            report = evidence.inspect([pdf], root / "out")
            record = report["evidence"][0]["pdf"]
            self.assertEqual(record["pages"], 2)
            all_text = Path(record["text_all"]["path"])
            self.assertTrue(all_text.is_file())
            self.assertIn("\f", all_text.read_text(encoding="utf-8"))
            self.assertEqual(record["text_all"]["sha256"], evidence.sha256(all_text))
            saved = json.loads((root / "out" / "evidence.json").read_text())
            self.assertEqual(saved["kind"], "document-template-evidence")


if __name__ == "__main__":
    unittest.main()
