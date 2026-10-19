"""Check derived document layout and copied numbers, not experimental validity."""

from hashlib import sha256
import argparse
import json
from pathlib import Path
import subprocess
import re
import xml.etree.ElementTree as ET
from zipfile import ZipFile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
STEM = "Elmanov_IACGN_2026_final"
W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
NS = {"w": W}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stem", default=STEM)
    parser.add_argument("--change-scope", choices=["affiliation", "related-work"], default="affiliation")
    parser.add_argument("--reference-count", type=int)
    args = parser.parse_args()
    stem = args.stem
    if not re.fullmatch(r"[A-Za-z0-9_-]+", stem):
        raise ValueError("Simple local output stem required")
    out = HERE / ("final-quality-check.json" if stem == STEM else stem + ".quality-check.json")
    if out.exists():
        raise FileExistsError("Quality record is immutable; use a new version")
    docx, pdf = [HERE / (stem + ext) for ext in (".docx", ".pdf")]
    manifest = json.loads((HERE / (stem + ".build.json")).read_text())
    assert sha256(docx.read_bytes()).hexdigest() == manifest["docx_sha256"]
    assert sha256((ROOT / manifest["source"]).read_bytes()).hexdigest() == manifest["source_sha256"]
    source = (ROOT / manifest["source"]).read_text()
    assert (HERE / (stem + ".md")).read_bytes() == (ROOT / manifest["source"]).read_bytes()
    with ZipFile(docx) as z:
        assert z.testzip() is None
        root = ET.fromstring(z.read("word/document.xml"))
        style = ET.fromstring(z.read("word/styles.xml"))
        assert not any("header" in name or "footer" in name or "vba" in name.lower() for name in z.namelist())
    tables = root.findall(".//w:tbl", NS)
    assert len(tables) == 3
    assert all(len(t.findall("w:tr", NS)) == 5 for t in tables)
    sections = root.findall(".//w:sectPr", NS)
    assert [s.find("w:cols", NS).get(f"{{{W}}}num") for s in sections] == ["1", "2"]
    for s in sections:
        size = s.find("w:pgSz", NS)
        assert size.get(f"{{{W}}}w") == "12240" and size.get(f"{{{W}}}h") == "15840"
    body = style.find("w:style[@w:styleId='IMSBodyText']", NS)
    assert body.find("w:rPr/w:sz", NS).get(f"{{{W}}}val") == "20"
    assert body.find("w:pPr/w:spacing", NS).get(f"{{{W}}}line") == "240"
    assert body.find("w:pPr/w:spacing", NS).get(f"{{{W}}}lineRule") == "exact"
    assert body.find("w:rPr/w:rFonts", NS).get(f"{{{W}}}ascii") == "Times"
    rows = [["".join(c.itertext()) for c in row.findall("w:tc", NS)]
            for t in tables for row in t.findall("w:tr", NS)]
    visible = (HERE / ("final-rendered.txt" if stem == STEM else stem + ".rendered.txt")).read_text()
    if "DSTU, Rostov-on-Don, Russia" in source:
        assert "DSTU, Rostov-on-Don, Russia" in visible
        assert "to be confirmed]" not in visible
    affiliation = "Don State Technical University, Rostov-on-Don, Russia"
    if affiliation in source:
        assert affiliation in " ".join(visible.split())
        assert "to be confirmed]" not in visible
        if args.change_scope == "affiliation":
            prior = (HERE / "Elmanov_IACGN_2026_DSTU.md").read_text()
            assert source == prior.replace("DSTU, Rostov-on-Don, Russia", affiliation, 1)
    if args.change_scope == "related-work":
        prior = (HERE / "Elmanov_IACGN_2026_Don_State.md").read_text()
        assert source.split("## II. Related Work", 1)[0] == prior.split("## II. Related Work", 1)[0]
        unchanged = lambda text: text.split("## III. Methods", 1)[1].split("## References", 1)[0]
        assert unchanged(source) == unchanged(prior)
    reference_numbers = re.findall(r"^\[(\d+)\]", source.split("## References", 1)[1], flags=re.M)
    assert reference_numbers == [str(i) for i in range(1, len(reference_numbers) + 1)]
    assert all(f"[{number}]" in visible for number in reference_numbers)
    if args.reference_count is not None:
        assert len(reference_numbers) == args.reference_count
    saved = json.loads((ROOT / "submission/overwrite-results.json").read_text())
    compared = []
    for item in saved["selected_results"]:
        if item["window"] != "pooled":
            continue
        values = [f'{item["observed_reads"]:,}', f'{item["all_writes"]:,}',
                  f'{item["observed_read"]["mae_seconds"]:,.2f}',
                  f'{item["observed_read"]["mean_overwrite_lower_seconds"]:,.2f}',
                  f'{item["pass_lower"] * 100:.2f}–{item["pass_upper"] * 100:.2f}%',
                  f'{item["paired_n"]:,}', f'{item["paired"]["ratio"]:.4f}']
        assert all(any(value in cell for row in rows for cell in row) for value in values)
        assert all(value in visible for value in values)
        compared.append({"workload": item["workload"], "rule": item["rule"], "values": values})
    assert len(compared) == 4
    info = subprocess.run(["pdfinfo", str(pdf)], check=True, capture_output=True, text=True).stdout
    pages = int(next(line.split(":", 1)[1].strip() for line in info.splitlines() if line.startswith("Pages:")))
    assert 3 <= pages <= 6
    fonts = subprocess.run(["pdffonts", str(pdf)], check=True, capture_output=True, text=True).stdout
    assert "NimbusRoman-Regular" in fonts and "NimbusRoman-Bold" in fonts
    assert not any(word in visible for word in ("abc@company.com", "homer@thesimpsons.com", "Magnetic Properties"))
    result = {
        "scope": "Document consistency, formatting and copied numbers ONLY; no experimental rerun or raw-result integrity audit",
        "passed": True, "docx_sha256": sha256(docx.read_bytes()).hexdigest(),
        "pdf_sha256": sha256(pdf.read_bytes()).hexdigest(), "pdf_pages": pages,
        "docx_table_count": 3, "all_tables_four_data_rows": True,
        "body_font_times_pt": 10, "body_exact_line_pt": 12,
        "title_single_column_body_double_column": True,
        "pdf_font_report": fonts, "pdfinfo": info, "copied_pooled_values": compared,
        "source_sha256": manifest["source_sha256"],
        "full_university_affiliation_checked": affiliation in source,
        "reference_count": len(reference_numbers),
        "change_scope_checked": args.change_scope,
        "remaining": ["Author declarations/rights and final submission approval", "R031 parent pass-array audit gap disclosed"]
                     + (["Affiliation placeholder"] if "to be confirmed]" in source else []),
    }
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
