"""Export DOCX minimal en stdlib (zipfile + XML OOXML) — aucun paquet externe."""
import html
import zipfile

CONTENT_TYPES = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
<Default Extension="xml" ContentType="application/xml"/>
<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
</Types>"""

RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>"""


def _esc(t):
    return html.escape(str(t), quote=False)


def _p(text, style=None):
    st = f'<w:pPr><w:pStyle w:val="{style}"/></w:pPr>' if style else ""
    return f'<w:p>{st}<w:r><w:t xml:space="preserve">{_esc(text)}</w:t></w:r></w:p>'


def _table(rows):
    xml = ['<w:tbl><w:tblPr><w:tblBorders>'
           + "".join(f'<w:{s} w:val="single" w:sz="4"/>' for s in ("top", "left", "bottom", "right", "insideH", "insideV"))
           + '</w:tblBorders></w:tblPr>']
    for i, row in enumerate(rows):
        xml.append("<w:tr>")
        for cell in row:
            tag = "th" if i == 0 else "td"
            xml.append(f'<w:{tag}><w:p><w:r><w:t xml:space="preserve">{_esc(cell)}</w:t></w:r></w:p></w:{tag}>')
        xml.append("</w:tr>")
    xml.append("</w:tbl>")
    return "".join(xml)


def html_to_docx(html_text, out_path):
    """Convertit un sous-ensemble du rapport HTML (titres, paragraphes, tableaux) en DOCX."""
    import re
    body = []
    pos = 0
    pattern = re.compile(r"<(h[12]|h3|p|table|li|ul)>", re.I)
    # extraction simple : on découpe sur les balises ouvrantes reconnues
    tokens = re.split(r"(<h[123][^>]*>|</h[123]>|<p[^>]*>|</p>|<table[^>]*>|</table>|<tr[^>]*>|</tr>|<li[^>]*>|</li>|<ul[^>]*>|</ul>)", html_text, flags=re.I)
    table_rows = None
    for tok in tokens:
        tl = tok.lower()
        if tl.startswith("<h1"):
            body.append(("h1", None))
        elif tl.startswith("<h2"):
            body.append(("h2", None))
        elif tl.startswith("<h3"):
            body.append(("h3", None))
        elif tl.startswith("<table"):
            table_rows = []
        elif tl.startswith("</table>"):
            if table_rows:
                body.append(("table", table_rows))
            table_rows = None
        elif tl.startswith("<tr") and table_rows is not None:
            table_rows.append([])
        elif tl.startswith(("<p", "<li")):
            body.append(("p", None))
        elif tl in ("</p>", "</li>", "</h1>", "</h2>", "</h3>"):
            pass
    # reconstruction du texte par blocs
    out = []
    mode = None
    cur = []
    for kind, payload in body:
        if kind == "table":
            out.append(_table(payload))
            continue
        mode = kind
    # deuxième passe : extraire le texte des paragraphes/titres
    text_blocks = re.findall(r"<(h[123])[^>]*>(.*?)</\1>|<p[^>]*>(.*?)</p>|<li[^>]*>(.*?)</li>", html_text, flags=re.I | re.S)
    tables = re.findall(r"<table[^>]*>(.*?)</table>", html_text, flags=re.I | re.S)
    parts = []
    for h, htxt, ptxt, ltxt in text_blocks:
        content = htxt or ptxt or ltxt
        content = re.sub(r"<[^>]+>", "", content)
        content = html.unescape(content).strip()
        if not content:
            continue
        style = {"h1": "Heading1", "h2": "Heading2", "h3": "Heading3"}.get(h) if h else None
        parts.append(_p(content, style))
    for t in tables:
        rows = []
        for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", t, flags=re.I | re.S):
            cells = [html.unescape(re.sub(r"<[^>]+>", "", c)).strip() for c in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", tr, flags=re.I | re.S)]
            if cells:
                rows.append(cells)
        if rows:
            parts.append(_table(rows))
    styles = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
<w:style w:type="paragraph" w:styleId="Heading1"><w:name w:val="heading 1"/><w:rPr><w:b/><w:sz w:val="32"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="Heading2"><w:name w:val="heading 2"/><w:rPr><w:b/><w:sz w:val="28"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="Heading3"><w:name w:val="heading 3"/><w:rPr><w:b/><w:sz w:val="24"/></w:rPr></w:style>
</w:styles>"""
    document = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
                f"<w:body>{''.join(parts)}<w:sectPr/></w:body></w:document>")
    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", CONTENT_TYPES)
        z.writestr("_rels/.rels", RELS)
        z.writestr("word/document.xml", document)
        z.writestr("word/styles.xml", styles)
    return out_path
