"""Local, stdlib-only IACGN document compositor; never execute research code.

Reads the reviewed Markdown and locally converted template, writes only new
derived files in this directory. Refuses to overwrite document/manifest files.
"""

from copy import deepcopy
from datetime import datetime, timezone
from hashlib import sha256
import argparse
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET
from zipfile import ZipFile, ZIP_DEFLATED

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
SOURCE = ROOT / ".research/writing/conference-article-2026-10-07.md"
TEMPLATE = OUT / "c2feffd4-7038-4707-ac0c-180520464337.docx"
W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
M = "http://schemas.openxmlformats.org/officeDocument/2006/math"
R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
ET.register_namespace("w", W)
ET.register_namespace("m", M)
ET.register_namespace("r", R)


def node(name, attrs=None, text=None, namespace=W):
    result = ET.Element(f"{{{namespace}}}{name}")
    for key, value in (attrs or {}).items():
        result.set(f"{{{namespace}}}{key}", str(value))
    if text is not None:
        result.text = text
    return result


def add(parent, name, attrs=None, text=None, namespace=W):
    result = node(name, attrs, text, namespace)
    parent.append(result)
    return result


def xml(element):
    return ET.tostring(element, encoding="utf-8", xml_declaration=True)


def plain_run(parent, text, bold=False, italic=False, subscript=False):
    r = add(parent, "r")
    if bold or italic or subscript:
        props = add(r, "rPr")
        if bold:
            add(props, "b")
        if italic:
            add(props, "i")
        if subscript:
            add(props, "vertAlign", {"val": "subscript"})
    # Use real Word sub/superscripts for the equation's recurring notation.
    t = add(r, "t", text=text)
    t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
    return r


def run(parent, text, bold=False, italic=False):
    # Typeset recurring mathematical subscripts without touching filenames.
    text = text.replace("Σ_{i∈C}", "Σ(i∈C)")
    pattern = r"\b(MAE|mean|prediction|e|y|B|L|M)_(i|L|C)\b"
    start = 0
    last = None
    for match in re.finditer(pattern, text):
        if match.start() > start:
            last = plain_run(parent, text[start:match.start()], bold, italic)
        last = plain_run(parent, match.group(1), bold, True)
        last = plain_run(parent, match.group(2), bold, True, subscript=True)
        start = match.end()
    if start < len(text) or last is None:
        last = plain_run(parent, text[start:], bold, italic)
    return last


def paragraph(text="", style="IMSBodyText", keep_next=False):
    p = node("p")
    pp = add(p, "pPr")
    add(pp, "pStyle", {"val": style})
    if keep_next:
        add(pp, "keepNext")
    if style == "IMSAbstract" and text.startswith("Abstract —"):
        run(p, "Abstract", italic=True)
        run(p, text[len("Abstract"):])
    else:
        run(p, text)
    return p


def section(columns, ending=False):
    s = node("sectPr")
    add(s, "type", {"val": "continuous"})
    # Geometry from the template prose: Letter portrait, .75/1/.625/.625 in.
    # Its converted XML had contradictory landscape attribute; use dimensions.
    add(s, "pgSz", {"w": 12240, "h": 15840, "orient": "portrait"})
    add(s, "pgMar", {"top": 1080, "bottom": 1440, "left": 900,
                       "right": 900, "header": 720, "footer": 720,
                       "gutter": 0})
    add(s, "cols", {"num": columns, "space": 360, "equalWidth": 1})
    return s


def styles():
    # Reuse the actual named template styles as the base, not a generic design.
    with ZipFile(TEMPLATE) as z:
        inherited = ET.fromstring(z.read("word/styles.xml"))
    result = node("styles")
    defaults = add(result, "docDefaults")
    dr = add(add(defaults, "rPrDefault"), "rPr")
    add(dr, "rFonts", {"ascii": "Times", "hAnsi": "Times", "cs": "Times"})
    add(dr, "sz", {"val": 20})
    add(dr, "lang", {"val": "en-US"})
    definitions = {
        "Normal": (20, 240, "both", 0, 0, 0, False, False, False),
        "IMSTitle": (36, None, "center", 120, 120, 0, False, False, False),
        "IMSAuthorList": (24, None, "center", 120, 120, 0, False, False, False),
        "Affiliation": (24, None, "center", 120, 120, 0, False, False, False),
        "IMSAbstract": (18, 200, "both", 0, 0, 180, True, False, False),
        "IMSBodyText": (20, 240, "both", 0, 0, 180, False, False, False),
        "IMSHeading1": (20, 240, "center", 360, 120, 0, False, False, True),
        "IMSHeading2": (20, 240, "left", 120, 120, 0, False, True, False),
        "IMSHeadingReferences": (20, 240, "center", 360, 120, 0, False, False, True),
        "IMSReferences": (18, 200, "both", 0, 0, 0, False, False, False),
        "TableTitle": (16, 200, "center", 140, 80, 0, False, False, True),
        "TableContents": (17, 210, "center", 0, 0, 0, False, False, False),
        "IMSEquation": (20, None, "center", 120, 120, 0, False, False, False),
    }
    for sid, (size, line, align, before, after, indent, bold, italic, caps) in definitions.items():
        old = inherited.find(f"w:style[@w:styleId='{sid}']", {"w": W})
        st = deepcopy(old) if old is not None else node("style", {"type": "paragraph", "styleId": sid})
        # Preserve identity, normalize contradictory inherited formatting to
        # explicit instructions visible in the template body.
        for child in list(st):
            st.remove(child)
        add(st, "name", {"val": sid})
        add(st, "qFormat")
        pp = add(st, "pPr")
        add(pp, "widowControl")
        add(pp, "spacing", {"before": before, "after": after,
                            "line": line if line else 240,
                            "lineRule": "exact" if line else "auto"})
        add(pp, "jc", {"val": align})
        if indent:
            add(pp, "ind", {"firstLine": indent})
        if sid == "IMSReferences":
            add(pp, "ind", {"left": 360, "hanging": 360})
            add(pp, "keepLines")
        if "Heading" in sid or sid in {"TableTitle", "IMSTitle", "IMSAuthorList", "Affiliation"}:
            add(pp, "keepNext")
        rp = add(st, "rPr")
        add(rp, "rFonts", {"ascii": "Times", "hAnsi": "Times", "cs": "Times"})
        add(rp, "sz", {"val": size})
        add(rp, "szCs", {"val": size})
        if bold:
            add(rp, "b")
        if italic:
            add(rp, "i")
        if caps:
            add(rp, "smallCaps")
        result.append(st)
    return result


def math_run(parent, text):
    r = add(parent, "r", namespace=M)
    props = add(r, "rPr", namespace=M)
    add(props, "sty", {"val": "p"}, namespace=M)
    wp = add(r, "rPr")
    add(wp, "rFonts", {"ascii": "Times", "hAnsi": "Times"})
    add(wp, "sz", {"val": 20})
    add(r, "t", text=text, namespace=M)


def equation():
    p = paragraph("", "IMSEquation")
    p.remove(p.find("w:r", {"w": W}))
    # Native editable Word equation, not a raster image or raw TeX syntax.
    mp = add(p, "oMathPara", namespace=M)
    mpr = add(mp, "oMathParaPr", namespace=M)
    add(mpr, "jc", {"val": "center"}, namespace=M)
    om = add(mp, "oMath", namespace=M)
    def sub(parent, base, index):
        s = add(parent, "sSub", namespace=M)
        e = add(s, "e", namespace=M)
        math_run(e, base)
        idx = add(s, "sub", namespace=M)
        math_run(idx, index)

    sub(om, "M", "L")
    math_run(om, " = ")
    frac = add(om, "f", namespace=M)
    num = add(frac, "num", namespace=M)
    sub(num, "Σ", "i∈K")
    sub(num, "B", "i")
    math_run(num, " + ")
    sub(num, "Σ", "i∈U")
    sub(num, "L", "i")
    den = add(frac, "den", namespace=M)
    math_run(den, "N")
    math_run(om, " ≤ ")
    sub(om, "mean", "C")
    math_run(om, "(B).")
    run(p, "  (1)")
    return p


def table(lines):
    rows = [[c.strip() for c in line.strip().strip("|").split("|")] for line in lines]
    rows = [row for row in rows if not all(re.fullmatch(r":?-+:?", cell) for cell in row)]
    count = len(rows[0])
    widths = ([480, 1490, 1510, 1560] if count == 4 else [450, 900, 1020, 1020, 1650])
    assert sum(widths) == 5040
    tbl = node("tbl")
    props = add(tbl, "tblPr")
    add(props, "tblW", {"w": 5040, "type": "dxa"})
    add(props, "jc", {"val": "center"})
    add(props, "tblLayout", {"type": "fixed"})
    margins = add(props, "tblCellMar")
    for side in ("top", "bottom", "left", "right"):
        add(margins, side, {"w": 45, "type": "dxa"})
    borders = add(props, "tblBorders")
    for side in ("top", "bottom", "insideH"):
        add(borders, side, {"val": "single", "sz": 4, "color": "777777"})
    for side in ("left", "right", "insideV"):
        add(borders, side, {"val": "nil"})
    grid = add(tbl, "tblGrid")
    for width in widths:
        add(grid, "gridCol", {"w": width})
    for index, row in enumerate(rows):
        assert len(row) == count
        tr = add(tbl, "tr")
        tp = add(tr, "trPr")
        add(tp, "cantSplit")
        if index == 0:
            add(tp, "tblHeader")
        for col, text in enumerate(row):
            tc = add(tr, "tc")
            cp = add(tc, "tcPr")
            add(cp, "tcW", {"w": widths[col], "type": "dxa"})
            add(cp, "vAlign", {"val": "center"})
            if index == 0:
                add(cp, "shd", {"fill": "EEEEEE", "val": "clear"})
            # Chain rows to keep a small four-row results table in one column.
            p = paragraph(text, "TableContents", keep_next=index < len(rows) - 1)
            if index == 0:
                for rr in p.findall("w:r", {"w": W}):
                    rp = rr.find("w:rPr", {"w": W})
                    if rp is None:
                        rp = node("rPr")
                        rr.insert(0, rp)
                    add(rp, "b")
            tc.append(p)
    return tbl


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stem", default="Elmanov_IACGN_2026_article_v2")
    args = parser.parse_args()
    if not re.fullmatch(r"[A-Za-z0-9_-]+", args.stem):
        raise ValueError("Simple local output stem required")
    target = OUT / (args.stem + ".docx")
    manifest_path = OUT / (args.stem + ".build.json")
    md_path = OUT / (args.stem + ".md")
    for path in (target, manifest_path, md_path):
        if path.exists():
            raise FileExistsError(f"Refusing overwrite: {path}")
    text = SOURCE.read_text()
    document = node("document")
    body = add(document, "body")
    title_block = True
    references = False
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        i += 1
        if not line:
            continue
        if line.startswith("# "):
            body.append(paragraph(line[2:], "IMSTitle"))
        elif line.startswith("Abstract —"):
            # One-column author block, then continuous double-column text.
            boundary = paragraph("", "Normal")
            pp = boundary.find("w:pPr", {"w": W})
            add(pp, "spacing", {"before": 0, "after": 0, "line": 240, "lineRule": "exact"})
            pp.append(section(1))
            body.append(boundary)
            title_block = False
            body.append(paragraph(line, "IMSAbstract"))
        elif line.startswith("Keywords —"):
            body.append(paragraph(line, "IMSAbstract"))
        elif line.startswith("### "):
            body.append(paragraph(line[4:], "IMSHeading2"))
        elif line.startswith("## "):
            heading = line[3:]
            references = heading == "References"
            body.append(paragraph(heading, "IMSHeadingReferences" if references else "IMSHeading1"))
        elif line.startswith("TABLE "):
            body.append(paragraph(line, "TableTitle", keep_next=True))
        elif line.startswith("|"):
            group = [line]
            while i < len(lines) and lines[i].strip().startswith("|"):
                group.append(lines[i].strip())
                i += 1
            body.append(table(group))
        elif line.startswith("M_L ="):
            body.append(equation())
        elif title_block:
            body.append(paragraph(line, "IMSAuthorList" if line.startswith("Elmanov Ilia") else "Affiliation"))
        else:
            body.append(paragraph(line, "IMSReferences" if references else "IMSBodyText"))
    body.append(section(2, ending=True))
    rel_ns = "http://schemas.openxmlformats.org/package/2006/relationships"
    rels = ET.Element("Relationships", {"xmlns": rel_ns})
    ET.SubElement(rels, "Relationship", {"Id": "rId1", "Type": R + "/officeDocument", "Target": "word/document.xml"})
    wr = ET.Element("Relationships", {"xmlns": rel_ns})
    ET.SubElement(wr, "Relationship", {"Id": "rId1", "Type": R + "/styles", "Target": "styles.xml"})
    ET.SubElement(wr, "Relationship", {"Id": "rId2", "Type": R + "/settings", "Target": "settings.xml"})
    ct = ET.Element("Types", {"xmlns": "http://schemas.openxmlformats.org/package/2006/content-types"})
    ET.SubElement(ct, "Default", {"Extension": "rels", "ContentType": "application/vnd.openxmlformats-package.relationships+xml"})
    ET.SubElement(ct, "Default", {"Extension": "xml", "ContentType": "application/xml"})
    for part, typ in (("document", "document.main"), ("styles", "styles"), ("settings", "settings")):
        ET.SubElement(ct, "Override", {"PartName": f"/word/{part}.xml", "ContentType": f"application/vnd.openxmlformats-officedocument.wordprocessingml.{typ}+xml"})
    settings = node("settings")
    add(settings, "defaultTabStop", {"val": 720})
    with ZipFile(target, "x", compression=ZIP_DEFLATED) as z:
        for name, content in {"[Content_Types].xml": xml(ct), "_rels/.rels": xml(rels),
                              "word/document.xml": xml(document), "word/styles.xml": xml(styles()),
                              "word/settings.xml": xml(settings), "word/_rels/document.xml.rels": xml(wr)}.items():
            z.writestr(name, content)
    md_path.write_text(text)
    abstract = next(line for line in lines if line.startswith("Abstract —"))[len("Abstract —"):]
    manifest = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source": str(SOURCE.relative_to(ROOT)), "source_sha256": sha256(SOURCE.read_bytes()).hexdigest(),
        "template_local": TEMPLATE.name, "template_sha256": sha256(TEMPLATE.read_bytes()).hexdigest(),
        "script_sha256": sha256(Path(__file__).read_bytes()).hexdigest(),
        "docx": target.name, "docx_sha256": sha256(target.read_bytes()).hexdigest(),
        "approx_word_count_including_tables": len(text.split()), "abstract_words": len(abstract.split()),
        "paper": "Letter portrait", "margins_inch": {"top": .75, "bottom": 1, "left": .625, "right": .625},
        "body_columns": 2, "column_width_inch": 3.5, "column_gap_inch": .25,
        "font": "Times (locally resolves to Nimbus Roman; template permits Times)",
        "body_pt": 10, "body_exact_line_pt": 12, "header_footer_page_numbers": False,
        "template_normalizations": ["Geometry follows visible instructions, not contradictory landscape attribute", "Named styles use Times as explicitly allowed", "No template sample text/figures/headers/footers retained"],
        "pending": ["PDF render/page-fit check", "Declarations and final author submission approval"]
                   + (["Author affiliation"] if "to be confirmed]" in text else []),
    }
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
