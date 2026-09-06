#!/usr/bin/env python3
"""Liczby do modeli WPROST z plikow .card (bez recznego przepisywania).

Zasady odczytu (JiMEditor):
  - lokacja: jesli awers ma location_type 未揭示 (nieodkryta) a rewers 已揭示 (odkryta), wartosci
    (shroud, clues, traits, location_icon/link, name) sa na rewersie; inaczej na awersie.
    W scenariuszu 3 rewers to strona Spaczona - zwracany osobno jako "corrupt".
  - "3<调查员>" = 3 na badacza; "X", "?", "-", "" = brak liczby (None) - model musi to obsluzyc jawnie.
  - wrog: attack / enemy_health / evade / enemy_damage / enemy_damage_horror / quantity / victory / traits.
  - tajemnica: threshold wg serial_number; akt: threshold.

Uzycie:  python tools/cards_data.py [table]   - tabela wszystkich wartosci z zrodlem (plik, strona, pole)
         python tools/cards_data.py --selftest
"""
import sys, os, io, json, glob, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UNREVEALED, REVEALED = "未揭示", "已揭示"
PER_INV = "<调查员>"


def load(path):
    return json.loads(io.open(path, encoding="utf-8").read())


def num(v, players):
    """'3<调查员>' -> 3*players; '2' -> 2; 'X'/'?'/'-'/'' / None -> None."""
    if v is None:
        return None
    s = str(v).strip()
    if s in ("", "X", "?", "-"):
        return None
    per = s.endswith(PER_INV) or s.endswith("<badacz>")
    s = s.replace(PER_INV, "").replace("<badacz>", "").strip()
    if not re.fullmatch(r"-?\d+", s):
        return None
    return int(s) * (players if per else 1)


def _victory(side, d):
    v = side.get("victory") or d.get("victory")
    if v:
        return int(v)
    for t in (side.get("victory_text"), d.get("victory_text"), (d.get("back") or {}).get("victory_text")):
        m = re.search(r"Zwyci\w+\s+(\d+)", str(t or ""))
        if m:
            return int(m.group(1))
    return None


def location(path, players=4):
    d = load(path)
    b = d.get("back") or {}
    rev_is_back = d.get("location_type") == UNREVEALED and b.get("location_type") == REVEALED
    side = b if rev_is_back else d
    side_name = "back" if rev_is_back else "front"
    out = dict(
        file=os.path.relpath(path, ROOT), side=side_name,
        name=side.get("name") or d.get("name"),
        shroud_raw=side.get("shroud"), clues_raw=side.get("clues"),
        shroud=num(side.get("shroud"), players), clues=num(side.get("clues"), players),
        traits=list(side.get("traits") or []), icon=side.get("location_icon"),
        links=list(side.get("location_link") or []), victory=_victory(side, d),
        quantity=d.get("quantity"),
    )
    if not rev_is_back and b.get("location_type") == REVEALED:
        # obie strony "odkryte": rewers = strona Spaczona (scenariusz 3)
        out["corrupt"] = dict(shroud_raw=b.get("shroud"), clues_raw=b.get("clues"),
                              shroud=num(b.get("shroud"), players), clues=num(b.get("clues"), players),
                              traits=list(b.get("traits") or []), icon=b.get("location_icon"),
                              links=list(b.get("location_link") or []))
    return out


def locations(folder, players=4):
    return [location(p, players) for p in sorted(glob.glob(os.path.join(ROOT, folder, "**", "*.card"), recursive=True))
            if load(p).get("type") == "地点卡"]


def enemy(path, players=4):
    d = load(path)
    return dict(
        file=os.path.relpath(path, ROOT), name=d.get("name"),
        atk=num(d.get("attack"), players), hp=num(d.get("enemy_health"), players), ev=num(d.get("evade"), players),
        atk_raw=d.get("attack"), hp_raw=d.get("enemy_health"), ev_raw=d.get("evade"),
        dmg=int(d.get("enemy_damage") or 0), hor=int(d.get("enemy_damage_horror") or 0),
        quantity=d.get("quantity"), victory=d.get("victory"), traits=list(d.get("traits") or []),
    )


def enemies(folder, players=4):
    return [enemy(p, players) for p in sorted(glob.glob(os.path.join(ROOT, folder, "*.card")))
            if load(p).get("type") == "敌人卡"]


def agendas(folder, players=4):
    """[(serial, threshold, name, file)] w kolejnosci serial_number."""
    out = []
    for p in sorted(glob.glob(os.path.join(ROOT, folder, "*.card"))):
        d = load(p)
        if d.get("type") == "密谋卡":
            out.append((str(d.get("serial_number")), num(d.get("threshold"), players), d.get("name"),
                        os.path.relpath(p, ROOT)))
    return sorted(out, key=lambda t: t[0])


def acts(folder, players=4):
    out = []
    for p in sorted(glob.glob(os.path.join(ROOT, folder, "*.card"))):
        d = load(p)
        if d.get("type") == "场景卡":
            out.append((str(d.get("serial_number")), num(d.get("threshold"), players), d.get("name"),
                        os.path.relpath(p, ROOT)))
    return sorted(out, key=lambda t: t[0])


def quantities(folder):
    out = {}
    for p in sorted(glob.glob(os.path.join(ROOT, folder, "*.card"))):
        d = load(p)
        out[d.get("name")] = out.get(d.get("name"), 0) + (int(d.get("quantity")) if d.get("quantity") else 1)
    return out


def by_name(items):
    return {i["name"]: i for i in items}


def table(players=4):
    print("# WARTOSCI UZYWANE PRZEZ MODELE - kazda z plikiem, strona i polem (4 graczy)")
    for scen, folder in ((1, "Karty Lokacji/scenariusz 1"), (2, "Karty Lokacji/scenariusz 2"),
                         (3, "Karty Lokacji/scenariusz 3")):
        print("\n## Lokacje scenariusz %d  (strona | zaslona | wskazowki lacznie | cechy | ikona -> polaczenia)" % scen)
        for l in locations(folder, players):
            print("%-32s %-5s zasl=%-4s wsk=%-4s  [%s | %s]  %s  %s -> %s" % (
                l["name"], l["side"], l["shroud_raw"], l["clues_raw"], l["shroud"], l["clues"],
                ",".join(l["traits"]) or "-", l["icon"] or "-", ",".join(l["links"]) or "-"))
            if l.get("corrupt"):
                c = l["corrupt"]
                print("%-32s %-5s zasl=%-4s wsk=%-4s  [%s | %s]  %s  %s -> %s" % (
                    "   (Spaczona)", "back", c["shroud_raw"], c["clues_raw"], c["shroud"], c["clues"],
                    ",".join(c["traits"]) or "-", c["icon"] or "-", ",".join(c["links"]) or "-"))
    for scen, folder in ((1, "Karty Spotkań/scenariusz 1"), (2, "Karty Spotkań/scenariusz 2"),
                         (3, "Karty Spotkań/scenariusz 3")):
        print("\n## Wrogowie scenariusz %d  (walka | zdrowie | unik | obr/przer | kopie | zwyc | cechy)" % scen)
        for e in enemies(folder, players):
            print("%-30s atk=%-3s hp=%-10s ev=%-3s -> [%s|%s|%s] %d/%d  q=%s v=%s  %s" % (
                e["name"], e["atk_raw"], e["hp_raw"], e["ev_raw"], e["atk"], e["hp"], e["ev"], e["dmg"], e["hor"],
                e["quantity"], e["victory"], ",".join(e["traits"])))
    for scen in (1, 2, 3):
        print("\n## Tajemnice i akty scenariusz %d" % scen)
        for s, t, n, f in agendas("Karty Scenariusza/scenariusz %d" % scen, players):
            print("  Tajemnica %-3s prog=%-4s %s" % (s, t, n))
        for s, t, n, f in acts("Karty Scenariusza/scenariusz %d" % scen, players):
            print("  Akt       %-3s prog=%-4s %s" % (s, t, n))
    for scen in (1, 2, 3):
        print("\n## Kopie kart spotkan scenariusz %d (quantity; brak pola = 1)" % scen)
        print("  " + ", ".join("%s x%d" % kv for kv in sorted(quantities("Karty Spotkań/scenariusz %d" % scen).items())))
    print("\n## Artykuly Kuriera: " + ", ".join("%s x%d" % kv for kv in sorted(quantities("Karty Spotkań/Artykuły Kuriera").items())))


def selftest():
    assert num("3<调查员>", 4) == 12 and num("2", 4) == 2 and num("X", 4) is None and num("?", 4) is None
    assert num("-", 4) is None and num("", 4) is None and num(None, 4) is None
    l = by_name(locations("Karty Lokacji/scenariusz 1"))
    assert l["Środek wioski"]["shroud"] == 2 and l["Środek wioski"]["clues"] == 4 and l["Środek wioski"]["side"] == "back"
    assert "Miejsce kultu" in l["Dół"]["traits"] and l["Dół"]["name"] == "Dół"
    assert l["Zachrystia"]["clues"] == 1
    l3 = by_name(locations("Karty Lokacji/scenariusz 3"))
    assert l3["Sołacz"]["shroud"] == 2 and l3["Sołacz"]["corrupt"]["shroud"] is None   # karta 4f9ffbe: zaslona 2
    assert l3["Tunele Forteczne"]["shroud"] is None and l3["Tunele Forteczne"]["clues"] == 12
    e = by_name(enemies("Karty Spotkań/scenariusz 1"))
    assert e["Żyrij Żerdź"]["hp"] == 12 and e["Żyrij Żerdź"]["victory"] == 1
    assert [t for _, t, _, _ in agendas("Karty Scenariusza/scenariusz 3")] == [4, 8, 14, 18]   # 4f9ffbe: T4 = 18
    assert quantities("Karty Spotkań/scenariusz 2")["Strażnik Śluzy"] == 1
    print("selftest OK")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if "--selftest" in sys.argv:
        selftest()
    else:
        table()
