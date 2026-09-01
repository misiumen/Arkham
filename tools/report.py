#!/usr/bin/env python3
"""Generuje raport HTML z usterkami kart: python tools/report.py [plik_wyjsciowy]

Dane bierze z arkham_cards.lint_findings(), szablon z tools/report_template.html.
Wynik to jeden samodzielny plik HTML (bez zaleznosci zewnetrznych poza Google Fonts).
"""
import io, os, re, sys, json, html, datetime, collections

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from arkham_cards import lint_findings, load, name_of, SEVERITY, ROOT

TEMPLATE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "report_template.html")
GROUP_LABEL = {
    "Karty Badaczy": "Karty badaczy i talii startowych",
    "Karty Lokacji": "Lokacje",
    "Karty Scenariusza": "Akty, tajemnice i karty scenariusza",
    "Karty Spotkań": "Talia spotkań",
    "(zbiorczo)": "Cała kampania zbiorczo",
}


def group_of(path):
    """Katalog scenariusza: dwa pierwsze poziomy sciezki."""
    parts = path.split("/")
    return "/".join(parts[:2]) if len(parts) > 2 else parts[0]


def build(paths=None):
    cards, findings, notes = lint_findings(paths)
    meta = {p: c for p, c in cards}

    by_path = collections.OrderedDict()
    for code, path, field, msg in findings:
        by_path.setdefault(path, []).append({"code": code, "field": field, "msg": html.escape(msg)})

    groups = collections.OrderedDict()
    for path, items in by_path.items():
        c = meta.get(path, {})
        worst = min(items, key=lambda f: SEVERITY.get(f["code"], 9))["code"]
        entry = {
            "path": html.escape(path),
            "name": html.escape(name_of(c) or ("(cały katalog)" if not c else "(bez nazwy)")),
            "type": html.escape(str(c.get("type", "zbiorczo"))),
            "worst": worst,
            "findings": sorted(items, key=lambda f: (SEVERITY.get(f["code"], 9), f["field"])),
        }
        groups.setdefault(group_of(path), []).append(entry)

    out_groups = []
    for name in sorted(groups, key=lambda n: (n.startswith("("), n)):  # zbiorcze na koniec
        entries = sorted(groups[name], key=lambda e: (SEVERITY.get(e["worst"], 9), e["path"]))
        top = name.split("/")[0]
        label = GROUP_LABEL.get(top, top)
        if "/" in name:
            label += " — " + name.split("/", 1)[1]
        out_groups.append({
            "name": html.escape(name),
            "label": html.escape(label),
            "cards": entries,
            "findings": sum(len(e["findings"]) for e in entries),
        })

    return {
        "generated": datetime.date.today().isoformat(),
        "total_cards": len(cards),
        "total_findings": len(findings),
        "cards_with_findings": len(by_path),
        "counts": collections.Counter(f[0] for f in findings),
        "notes": [html.escape(n) for n in notes],
        "groups": out_groups,
    }


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "raport-kart.html")
    data = build()
    tpl = io.open(TEMPLATE, encoding="utf-8").read()
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    # </script> w danych rozbilby blok skryptu
    payload = payload.replace("</", "<\\/")
    page = tpl.replace("/*__DATA__*/ null", payload)
    assert "/*__DATA__*/" not in page, "nie podmieniono danych w szablonie"
    io.open(out, "w", encoding="utf-8", newline="\n").write(page)
    print("%s — %d kart, %d usterek, %d kart do poprawy"
          % (out, data["total_cards"], data["total_findings"], data["cards_with_findings"]))


def selftest():
    d = build(["Karty Badaczy"])
    assert d["total_cards"] == 17 and d["total_findings"] > 0
    assert d["groups"] and d["groups"][0]["cards"], "brak grup"
    first = d["groups"][0]["cards"][0]
    assert SEVERITY[first["worst"]] <= SEVERITY[d["groups"][0]["cards"][-1]["worst"]], "zla kolejnosc"
    assert "<" not in first["name"], "nazwa nieoescape'owana"
    print("selftest OK")


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        selftest()
    else:
        main()
