#!/usr/bin/env python3
"""Profile modelowe dla wlasnych badaczy z Karty Badaczy/ -> .cache/arkhamdb/profiles_custom.json

Uzycie:
  python tools/custom_investigators.py build      # czyta karty z repo, pisze profiles_custom.json
  python tools/custom_investigators.py show
  ARKHAM_PROFILES=custom python tools/campaign_model.py run ...   # modele biora ten plik

Statystyki, zdrowie, poczytalnosc i klasa sa z kart. Talia = profil startera arkhamdb tej
samej klasy (srednie ikony, bronie, leczenie, sojusznicy), bo wlasni badacze nie maja
gotowych talii. Zdolnosci i slabosci liczone dokladnie w tools/investigators.py,
kazdy z komentarzem, co pomija.
"""
import sys, os, io, json, glob

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import arkham_cards as ac
import arkhamdb

ROOT = ac.ROOT
OUT = os.path.join(ROOT, ".cache", "arkhamdb", "profiles_custom.json")
FACTION = {"Obronca": "guardian", "Poszukiwacz": "seeker", "Wloczega": "rogue", "Mistyk": "mystic", "Ocalaly": "survivor"}
BASE_DECK = {"guardian": "62530", "mystic": "64502", "rogue": "64503", "survivor": "64750", "seeker": "64388"}
PICK = ["Szyszek Nowacki", "Michał z Bargłowa", "Baruch Hałabała", "Wojciech Robak"]

# Zdolnosci, karty sygnaturowe i slabosci sa liczone dokladnie w tools/investigators.py
# (wg tekstu kart); profil niesie tylko statystyki z karty badacza i talie startera.


def build():
    cards = arkhamdb.cards_by_code()
    out = []
    for stem in PICK:
        path = os.path.join(ROOT, "Karty Badaczy", stem + ".card")
        raw = json.load(io.open(path, encoding="utf-8"))
        c = ac.strip(raw)
        name = c["name"]
        faction = FACTION[c["class"]]
        wil, intel, com, agi = [int(x) for x in raw["attribute"]]
        base = arkhamdb.profile(arkhamdb.decklist(BASE_DECK[faction]), cards)
        p = dict(base)
        p.update({"investigator": name, "code": os.path.basename(path), "faction": faction, "klasa": c["class"],
                  "wil": wil, "int": intel, "com": com, "agi": agi,
                  "health": int(raw["health"]), "sanity": int(raw["horror"]),
                  "deck_name": "talia klasowa: " + base["deck_name"], "deck_id": base["deck_id"]})
        out.append(p)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    io.open(OUT, "w", encoding="utf-8").write(json.dumps(out, ensure_ascii=False, indent=1))
    show()


def show():
    for p in json.loads(io.open(OUT, encoding="utf-8").read()):
        extra = "zdolnosci: investigators.py"
        print("%-18s %-11s wil%d int%d com%d agi%d  hp%d/san%d  ikony w%.1f i%.1f c%.1f a%.1f  bronie%d(+%d) lecz%d sojusz%d  %s"
              % (p["investigator"], p["klasa"], p["wil"], p["int"], p["com"], p["agi"], p["health"], p["sanity"],
                 p["icons"]["willpower"], p["icons"]["intellect"], p["icons"]["combat"], p["icons"]["agility"],
                 p["weapons"], p["dmg_bonus"], p["heal_cards"], p["allies"], extra))


if __name__ == "__main__":
    a = sys.argv[1:]
    if a and a[0] == "build":
        build()
    elif a and a[0] == "show":
        show()
    else:
        print(__doc__)
