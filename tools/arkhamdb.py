#!/usr/bin/env python3
"""Talie z arkhamdb -> profile badaczy dla modelu scenariusza.

Uzycie:
  python tools/arkhamdb.py fetch decks [ID ...]   # 4 startery 0 XP z roznych klas (albo podane ID)
  python tools/arkhamdb.py show                    # wypisz profile z cache
  python tools/arkhamdb.py --selftest

Profil to HEURYSTYKA, nie symulacja kart. Talia zostaje sprowadzona do liczb:
  - statystyki badacza, zdrowie, poczytalnosc,
  - srednia liczba ikon danej umiejetnosci na karcie w talii (ile mozna
    srednio dolozyc do testu z jednej karty z reki),
  - ile kart daje +obrazenia w walce (bronie), ile znajduje wskazowki bez testu,
    ile leczy, ile to sojusznicy.
Cache: .cache/arkhamdb/ (decklisty, zrzut kart gracza 2,5 MB, profiles.json).
"""
import sys, os, re, io, json, collections, urllib.request

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(ROOT, ".cache", "arkhamdb")
API = "https://arkhamdb.com/api/public/"
FACTIONS = {"guardian": "Obronca", "seeker": "Poszukiwacz", "rogue": "Wloczega",
            "mystic": "Mistyk", "survivor": "Ocalaly", "neutral": "Neutralna"}


def get(url, name):
    """Pobiera url do cache/name, zwraca tekst. Bez sieci, gdy plik juz jest."""
    os.makedirs(CACHE, exist_ok=True)
    path = os.path.join(CACHE, name)
    if not os.path.exists(path):
        req = urllib.request.Request(url, headers={"User-Agent": "arkham-playtester/1.0"})
        with urllib.request.urlopen(req, timeout=40) as r:
            data = r.read()
        io.open(path, "wb").write(data)
    return io.open(path, encoding="utf-8", errors="replace").read()


def cards_by_code():
    data = json.loads(get(API + "cards/?encounter=0", "cards_player.json"))
    return {c["code"]: c for c in data}


def starter_deck_ids():
    """ID decklist z 'starter' w slugu na stronie popularnych - 0 XP z definicji serii."""
    html = get("https://arkhamdb.com/decklists/popular", "popular.html")
    ids = re.findall(r"/decklist/view/(\d+)/[a-z0-9-]*starter[a-z0-9-]*", html)
    return list(dict.fromkeys(ids))


def decklist(deck_id):
    return json.loads(get(API + "decklist/%s" % deck_id, "decklist_%s.json" % deck_id))


# --- profil -----------------------------------------------------------------
DMG_RE = re.compile(r"\+(\d) damage|deals? (\d) additional damage|\+(\d) obrażen", re.I)
CLUE_RE = re.compile(r"discover (?:\d|one|a) clue", re.I)
HEAL_RE = re.compile(r"heal (?:\d|one) (?:damage|horror)", re.I)


def profile(deck, cards):
    inv = cards[deck["investigator_code"]]
    n = 0
    icons = collections.Counter()
    weapons = clues = heal = allies = 0
    dmg_bonus = 0
    for code, qty in deck["slots"].items():
        c = cards.get(code)
        if not c or c["type_code"] in ("investigator",):
            continue
        n += qty
        for sk in ("willpower", "intellect", "combat", "agility"):
            icons[sk] += qty * (c.get("skill_%s" % sk) or 0)
        icons["wild"] += qty * (c.get("skill_wild") or 0)
        txt = c.get("real_text") or ""
        m = DMG_RE.search(txt)
        if m and c["type_code"] == "asset":
            weapons += qty
            dmg_bonus = max(dmg_bonus, int(next(g for g in m.groups() if g)))
        if CLUE_RE.search(txt):
            clues += qty
        if HEAL_RE.search(txt):
            heal += qty
        if c["type_code"] == "asset" and "Ally" in (c.get("real_traits") or ""):
            allies += qty
    n = n or 1
    return {
        "deck_id": deck["id"], "deck_name": deck["name"],
        "investigator": inv["name"], "code": inv["code"],
        "faction": inv["faction_code"], "klasa": FACTIONS.get(inv["faction_code"], "?"),
        "wil": inv["skill_willpower"], "int": inv["skill_intellect"],
        "com": inv["skill_combat"], "agi": inv["skill_agility"],
        "health": inv["health"], "sanity": inv["sanity"],
        "cards": n,
        # srednie ikony na karte = ile srednio doklada jedna zadeklarowana karta
        "icons": {k: round((icons[k] + icons["wild"]) / n, 2)
                  for k in ("willpower", "intellect", "combat", "agility")},
        "weapons": weapons, "dmg_bonus": dmg_bonus,
        "clue_cards": clues, "heal_cards": heal, "allies": allies,
    }


def cmd_fetch(args):
    ids = [a for a in args if a.isdigit()] or starter_deck_ids()
    cards = cards_by_code()
    chosen, seen = [], set()
    for did in ids:
        d = decklist(did)
        if d.get("xp"):
            continue  # tylko 0 XP
        p = profile(d, cards)
        if p["faction"] in seen and not any(a.isdigit() for a in args):
            continue  # rozne klasy, chyba ze uzytkownik podal ID recznie
        seen.add(p["faction"])
        chosen.append(p)
        if len(chosen) == 4:
            break
    if len(chosen) < 4:
        print("UWAGA: znaleziono tylko %d talii o roznych klasach" % len(chosen))
    io.open(os.path.join(CACHE, "profiles.json"), "w", encoding="utf-8").write(
        json.dumps(chosen, ensure_ascii=False, indent=1))
    cmd_show([])


def load_profiles():
    return json.loads(io.open(os.path.join(CACHE, "profiles.json"), encoding="utf-8").read())


def cmd_show(args):
    for p in load_profiles():
        print("%-18s %-11s wil%d int%d com%d agi%d  hp%d/san%d  ikony/karta w%.1f i%.1f c%.1f a%.1f  "
              "bronie%d(+%d) wskaz%d lecz%d sojusz%d  [%s #%s]"
              % (p["investigator"], p["klasa"], p["wil"], p["int"], p["com"], p["agi"],
                 p["health"], p["sanity"], p["icons"]["willpower"], p["icons"]["intellect"],
                 p["icons"]["combat"], p["icons"]["agility"], p["weapons"], p["dmg_bonus"],
                 p["clue_cards"], p["heal_cards"], p["allies"], p["deck_name"][:28], p["deck_id"]))


def selftest():
    cards = {
        "01001": {"code": "01001", "name": "Roland", "faction_code": "guardian", "type_code": "investigator",
                  "skill_willpower": 3, "skill_intellect": 3, "skill_combat": 4, "skill_agility": 2,
                  "health": 9, "sanity": 5},
        "01016": {"code": "01016", "type_code": "asset", "real_text": "Fight. +1 damage.",
                  "real_traits": "Item. Weapon.", "skill_combat": 1},
        "01089": {"code": "01089", "type_code": "skill", "skill_wild": 1, "real_text": ""},
    }
    p = profile({"id": 1, "name": "t", "investigator_code": "01001",
                 "slots": {"01016": 2, "01089": 2}}, cards)
    assert p["weapons"] == 2 and p["dmg_bonus"] == 1, p
    assert p["icons"]["combat"] == 1.0 and p["icons"]["agility"] == 0.5, p["icons"]
    assert p["com"] == 4 and p["klasa"] == "Obronca"
    print("selftest OK")


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a or a[0] in ("-h", "--help"):
        print(__doc__)
    elif a[0] == "--selftest":
        selftest()
    elif a[0] == "fetch":
        cmd_fetch(a[1:])
    elif a[0] == "show":
        cmd_show(a[1:])
    else:
        sys.exit("nieznany tryb: %s" % a[0])
