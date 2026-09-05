#!/usr/bin/env python3
"""Raport Markdown -> samodzielny HTML w stylu raportu usterek.

Uzycie: python tools/md2html.py raport-scenariusz-2.md [wyjscie.html]

Obsluguje to, czego uzywaja raporty agentow: naglowki #..###, akapity, listy
(-, 1.), tabele |a|b|, **pogrubienie**, `kod`. Nic wiecej - to nie parser Markdown.
"""
import sys, os, re, io, html

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

STYLE = """
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Bodoni+Moda:opsz,wght@6..96,500;6..96,700&family=IBM+Plex+Mono:wght@400;500&family=Source+Sans+3:wght@400;600&display=swap">
<style>
:root{--bg:#E8E7DE;--surface:#F5F4EE;--surface-2:#DEDDD3;--line:#C7C6BA;--ink:#1A1D17;--muted:#5D6157;--accent:#3D5A45;--bloker:#7E2B22;--blad:#9C5A11;--spoj:#3D5A45;--balans:#3A5570}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){--bg:#12140F;--surface:#1B1E17;--surface-2:#23261E;--line:#343829;--ink:#E7E8DE;--muted:#9AA091;--accent:#8CB18F;--bloker:#D9736A;--blad:#DFA054;--spoj:#8CB18F;--balans:#90AECC}}
:root[data-theme="dark"]{--bg:#12140F;--surface:#1B1E17;--surface-2:#23261E;--line:#343829;--ink:#E7E8DE;--muted:#9AA091;--accent:#8CB18F;--bloker:#D9736A;--blad:#DFA054;--spoj:#8CB18F;--balans:#90AECC}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font-family:"Source Sans 3","Segoe UI",system-ui,sans-serif;font-size:17px;line-height:1.55}
.wrap{max-width:900px;margin:0 auto;padding:48px 24px 96px}
h1{font-family:"Bodoni Moda","Times New Roman",serif;font-weight:700;font-size:clamp(32px,5vw,50px);line-height:1.05;margin:0 0 8px;text-wrap:balance}
h2{font-family:"Bodoni Moda","Times New Roman",serif;font-weight:500;font-size:28px;margin:44px 0 12px;padding-bottom:6px;border-bottom:3px double var(--line)}
h3{font-family:"Bodoni Moda","Times New Roman",serif;font-weight:500;font-size:21px;margin:28px 0 8px}
p{margin:0 0 14px;max-width:70ch}
p.meta{font-family:"IBM Plex Mono",ui-monospace,monospace;font-size:12px;letter-spacing:.12em;text-transform:uppercase;color:var(--muted);margin-bottom:28px}
ul,ol{margin:0 0 16px;padding-left:22px;max-width:75ch}
li{margin-bottom:6px}
code{font-family:"IBM Plex Mono",ui-monospace,monospace;font-size:.86em;background:var(--surface-2);padding:1px 5px}
.tw{overflow-x:auto;margin:0 0 18px;border:1px solid var(--line);background:var(--surface)}
table{border-collapse:collapse;width:100%;font-size:15px}
th,td{text-align:left;vertical-align:top;padding:8px 12px;border-bottom:1px solid var(--line)}
th{font-size:12px;letter-spacing:.1em;text-transform:uppercase;color:var(--muted);font-weight:600;background:var(--surface-2)}
td:first-child{white-space:nowrap}
td.sev{font-family:"IBM Plex Mono",ui-monospace,monospace;font-size:12px;letter-spacing:.06em;font-weight:500}
td.sev-BLOKER{color:var(--bloker)}td.sev-BLAD{color:var(--blad)}td.sev-SPOJNOSC{color:var(--spoj)}td.sev-BALANS{color:var(--balans)}
strong{font-weight:600}
</style>
"""
SEV = {"BLOKER": "BLOKER", "BŁĄD": "BLAD", "SPÓJNOŚĆ": "SPOJNOSC", "BALANS": "BALANS", "NIT": "NIT"}


def inline(s):
    s = html.escape(s, quote=False)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)
    return s


def convert(md):
    out, i, lines = [], 0, md.splitlines()
    title = None
    while i < len(lines):
        ln = lines[i]
        if ln.startswith("# "):
            title = ln[2:].strip()
            out.append("<h1>%s</h1>" % inline(title))
            if i + 2 < len(lines) and lines[i + 2].strip() and not lines[i + 2].startswith("#"):
                out.append('<p class="meta">%s</p>' % inline(lines[i + 2].strip())); i += 2
        elif ln.startswith("## "):
            out.append("<h2>%s</h2>" % inline(ln[3:]))
        elif ln.startswith("### "):
            out.append("<h3>%s</h3>" % inline(ln[4:]))
        elif ln.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].startswith("|"):
                rows.append([c.strip() for c in lines[i].strip().strip("|").split("|")]); i += 1
            head, body = rows[0], [r for r in rows[2:]]
            out.append('<div class="tw"><table><thead><tr>%s</tr></thead><tbody>'
                       % "".join("<th>%s</th>" % inline(h) for h in head))
            for r in body:
                cells = []
                for j, c in enumerate(r):
                    cls = ' class="sev sev-%s"' % SEV[c] if j == 0 and c in SEV else ""
                    cells.append("<td%s>%s</td>" % (cls, inline(c)))
                out.append("<tr>%s</tr>" % "".join(cells))
            out.append("</tbody></table></div>")
            continue
        elif re.match(r"^\s*[-*] ", ln) or re.match(r"^\s*\d+\. ", ln):
            ordered = bool(re.match(r"^\s*\d+\. ", ln))
            out.append("<ol>" if ordered else "<ul>")
            while i < len(lines) and (re.match(r"^\s*[-*] ", lines[i]) or re.match(r"^\s*\d+\. ", lines[i])):
                out.append("<li>%s</li>" % inline(re.sub(r"^\s*([-*]|\d+\.) ", "", lines[i]))); i += 1
            out.append("</ol>" if ordered else "</ul>")
            continue
        elif ln.strip():
            para = [ln]
            while i + 1 < len(lines) and lines[i + 1].strip() and not re.match(r"^(#|\||\s*[-*] |\s*\d+\. )", lines[i + 1]):
                i += 1; para.append(lines[i])
            out.append("<p>%s</p>" % inline(" ".join(para)))
        i += 1
    return title or "Raport", "\n".join(out)


def main():
    src = sys.argv[1]
    dst = sys.argv[2] if len(sys.argv) > 2 else os.path.splitext(src)[0] + ".html"
    title, body = convert(io.open(src, encoding="utf-8").read())
    page = "<title>%s</title>\n%s\n<div class=\"wrap\">\n%s\n</div>\n" % (html.escape(title), STYLE, body)
    io.open(dst, "w", encoding="utf-8", newline="\n").write(page)
    print(dst)


def selftest():
    t, b = convert("# Tytuł\n\nmeta linia\n\n## Sekcja\n\n| waga | x |\n|---|---|\n| BLOKER | **a** `b` |\n\n- jeden\n- dwa\n\nAkapit\nciąg dalszy.\n")
    assert t == "Tytuł" and 'class="meta"' in b and 'sev-BLOKER' in b, b
    assert "<strong>a</strong> <code>b</code>" in b and "<li>dwa</li>" in b and "Akapit ciąg dalszy." in b
    print("selftest OK")


if __name__ == "__main__":
    if sys.argv[1:] == ["--selftest"]:
        selftest()
    else:
        main()
