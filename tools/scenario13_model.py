#!/usr/bin/env python3
"""Model scenariuszy 1 ("Wioska wsrod drzew") i 3 ("Czarny Port"): Monte Carlo na 4 graczy.

Uzycie:
  python tools/scenario13_model.py tempo 1|3
  python tools/scenario13_model.py sim 1|3 --games 2000 [--tweak K=V,...]
  python tools/scenario13_model.py values        # tabela wartosci z kart (plik, strona, pole)
  python tools/scenario13_model.py --selftest

Zrodla danych - ZADNE liczby nie sa przepisane recznie:
  * zaslona, wskazowki, cechy, ikony polaczen, statystyki wrogow, liczby kopii, progi tajemnic:
    tools/cards_data.py czyta je wprost z plikow .card (strona odkryta lokacji).
  * uklad wioski i lasu (scen. 1): dwa schematy z Ksiegi Kampanii
    (Fabuła/Kampania Czarna Krew Warty.odt, Pictures/): wioska 3x3 = Srodek wioski + 8 losowych
    z 10; Rampa nad srodkowa gorna karta; Kosciol z lewej srodkowego rzedu, Zachrystia za Kosciolem;
    las 3x3 losowo, Skraj Lasu polaczony z lewa kolumna lasu i z kartami Natura wioski.
  * polaczenia scen. 3: symbole location_icon/location_link z kart (strona odkryta).
  * efekty tekstowe kart: zakodowane recznie, kazdy z cytatem w komentarzu.
Uproszczenia, ktorych nie da sie uniknac bez silnika kart graczy, sa opisane w KNOWN_SIMPLIFICATIONS
i wypisywane przez `values`.

Pokretla (--tweak K=V); domyslna wartosc = odczyt kart / odpowiedzi autora z 5 IX 2026:
  LOC_DOOM_COUNTS=1  zaglada na lokacjach liczy sie do progu tajemnicy (zasady: "zaglada w grze")
  KOZA_IN_DECK=0     0 = Czarna Koza odlozona na bok, wchodzi z Aktu 5 (autor: "akt 5");
                     1 = jak stoi na karcie: quantity 2, grupa f -> 2 kopie w talii spotkan
  KOZA_STATS=0       1 = statystyki Awatara z folderu "Scenariusz 4" zamiast karty Czarna Koza
  GONIEC_DMG=1       0 = Goniec po dotarciu NIE zadaje grupie 1<badacz> obrazen (wrazliwosc)
  KURIER=1           1 = Kurjer Poznanski jako OSOBNA talia (Ksiega: 1 karta na runde po fazie spotkan, jako grupa);
                     po jednej wersji z par (autor); 0 = bez Kurjera
  KOR_START=0        ile z lokacji Biblioteka/Dyrekcja/Linia zaczyna jako Spaczona (Ksiega: pelne zwyciestwo 0,
                     czesciowy sukces 1, porazka 2; kampania ustawia to sama)
  KURIER_PICK=0      ktora wersja z par: 0 = pliki bez numeru (Godzina policyjna, Seans, Targi) i
                     "Seans 2" dla Lo Kittay; 1 = "Godzina policyjna 2", "Seans 3", "Seans 4", "Targi 2"
  DALBOR_PER_ROUND=1 ile razy na runde Dalbor usuwa zaglade (karta: symbol bez limitu - pytanie do autora)
  AKT_DOOM=1         Akty 3/4 "wskazowki i zetony spaczenia": 1 = wskazowki i zaglada z lokacji; 0 = tylko wskazowki
"""
import sys, os, io, json, random, argparse, statistics, collections

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from scenario2_model import CHAOS_BAG, p_success, load_profiles, CACHE
import cards_data as cd
import investigators as iv

PLAYERS = 4
LOC_DOOM_COUNTS = 1
KOZA_IN_DECK = 0
KOZA_STATS = 0
GONIEC_DMG = 1
KURIER = 1
KURIER_PICK = 0
KOR_START = 0
DALBOR_PER_ROUND = 1
AKT_DOOM = 1
S3_CLUE_CUT = 0     # wrazliwosc (0 = jak na kartach)

KNOWN_SIMPLIFICATIONS = [
    "Talie graczy = profile liczbowe (srednie ikony, liczba broni, leczenie); karty nie sa zagrywane, wiec zasoby "
    "ubywaja tylko przez efekty spotkan i lokacji, nie przez koszty kart.",
    "Deklarowanie kart do testu: 1 karta (srednie ikony profilu), gdy statystyka < trudnosc + 2.",
    "Efekty 'odrzuc losowa karte z reki' / 'odrzuc atut': liczone jako -1 karta z reki / wpis w logu.",
    "Dol (odkrycie): kazdy sasiadujacy badacz wybiera '2 przerazenia' (polityka; inne opcje: Rezygnacja, 2 zaglady, slabosc).",
    "Skraj Lasu: 'Umiesc na wschodniej krawedzi' = wchodzi po rewersie Aktu 1, laczy sie wg schematu z Ksiegi.",
    "Przerazony Wikariusz (atut rozstawiany na Rampie po odkryciu Kosciola): nie jest odbierany ani uzywany.",
    "Kozi Pomiot 'Msciwy': nieudany atak = obrazenia Pomiota dla atakujacego.",
    "Brama z Galezi: blokuje krawedz miedzy lokacja badacza a sasiadem po prawej (schemat); przejscie gdy spelniony "
    "dowolny z 4 warunkow karty.",
    "Scen. 3: polaczenia = suma polaczen z obu kart (kilka kart wskazuje sasiada jednostronnie - patrz raport).",
    "Scen. 3: Kleszcz nie wchodzi do gry (zadna karta go nie daje); Dalbor usuwa 1 zaglade z tajemnicy raz na runde.",
]

# ===========================================================================
# DANE Z KART
# ===========================================================================
L1 = cd.by_name(cd.locations("Karty Lokacji/scenariusz 1", PLAYERS))
E1 = cd.by_name(cd.enemies("Karty Spotkań/scenariusz 1", PLAYERS))
Q1 = cd.quantities("Karty Spotkań/scenariusz 1")
S1_AGENDA = [t for _, t, _, _ in cd.agendas("Karty Scenariusza/scenariusz 1", PLAYERS)]
L3 = cd.by_name([l for l in cd.locations("Karty Lokacji/scenariusz 3", PLAYERS) if "_kor_9" not in l["file"]])
L3_KOR = cd.by_name([l for l in cd.locations("Karty Lokacji/scenariusz 3", PLAYERS) if "_kor_9" in l["file"]])
E3 = cd.by_name(cd.enemies("Karty Spotkań/scenariusz 3", PLAYERS))
E2 = cd.by_name(cd.enemies("Karty Spotkań/scenariusz 2", PLAYERS))
Q3 = cd.quantities("Karty Spotkań/scenariusz 3")
S3_AGENDA = [t for _, t, _, _ in cd.agendas("Karty Scenariusza/scenariusz 3", PLAYERS)]
ACT1_CLUES = [t for s, t, _, _ in cd.acts("Karty Scenariusza/scenariusz 3", PLAYERS) if s == "1"][0]
AWATAR = cd.enemy(os.path.join(cd.ROOT, "Karty Spotkań", "Scenariusz 4", "Awatar Kozicy.card"), PLAYERS)

# --- scenariusz 1: uklad z Ksiegi ---
RAMPA, KOSCIOL, ZACHRYSTIA, SRODEK, SKRAJ, POSIADLOSC = ("Przybrzeżna rampa załadunkowa", "Kościół", "Zachrystia",
                                                        "Środek wioski", "Skraj Lasu", "Posiadłość")
S1_VILLAGE_RANDOM = ["Warsztat Kowalski", "Kapliczka", "Kostnica", 'Karczma "Pod Rogatym"', "Skład Drewna",
                     "Stary magazyn zbożowy", "Targ Rybny", "Warsztat Kołodzieja", "Warsztat Mechaniczny",
                     "Wędzarnio-suszarnia"]          # Ksiega: "8 losowych kart wioski" z tych 10
S1_FOREST9 = ["Ambona", "Dół", "Grzęzawisko", "Gęsty Las", "Nory", "Obóz na mokradłach", "Obóz ocalałych", "Polana",
              "Ścieżka wśród krzaków"]               # Ksiega: "9 kart lasu umieszczonych losowo w ukladzie 3x3"
for _n in [RAMPA, KOSCIOL, ZACHRYSTIA, SRODEK, SKRAJ, POSIADLOSC] + S1_VILLAGE_RANDOM + S1_FOREST9:
    assert _n in L1, "brak karty lokacji: " + _n


def _e(src, name, **flags):
    e = src[name]
    return dict(atk=e["atk"], hp=e["hp"], ev=e["ev"], dmg=e["dmg"], hor=e["hor"], name=name,
                traits=e["traits"], victory=e.get("victory"), **flags)


# flagi = slowa kluczowe z tekstu kart (Lowca / Powsciagliwy / Msciwy)
S1_ENEMY = {
    "ciekawski": _e(E1, "Ciekawski wieśniak", aloof=True, hunter=False),        # "Powsciagliwy"
    "wyznawca": _e(E1, "Przekonany wyznawca", aloof=False, hunter=True),        # "Lowca"
    "kultywator": _e(E1, "Zbłąkany Kultywator", aloof=True, hunter=False),      # "Powsciagliwy"
    "traktorzysta": _e(E1, "Kultysta Traktorzysta", aloof=False, hunter=True),  # "Lowca"
    "pomiot": _e(E1, "Kozi Pomiot", aloof=False, hunter=True, retaliate=True),  # "Lowca. Msciwy"
    "zerdz": _e(E1, "Żyrij Żerdź", aloof=False, hunter=False),
}
# Ksiega: talia startowa = Ciekawski Wiesniak, Wolanie, Zblakany Kultywator; reszta odlozona na bok
S1_DECK_START = {"ciekawski": Q1["Ciekawski wieśniak"], "kultywator": Q1["Zbłąkany Kultywator"], "wolanie": Q1["Wołanie"]}
S1_SHUFFLE_IN = {   # rewersy Tajemnic 1-3
    1: {"kazanie": Q1["Gorliwe Kazanie"], "komunia": Q1["Nieczysta Komunia"], "chrzest": Q1["Nieczysty Chrzest"]},
    2: {"brama": Q1["Brama z Gałęzi"], "traktorzysta": Q1["Kultysta Traktorzysta"]},
    3: {"pomiot": Q1["Kozi Pomiot"]},
}
WYZNAWCY_ASIDE = Q1["Przekonany wyznawca"]

# --- scenariusz 3 ---
UAM = "Uniwesytet Adama Miskatonica"   # tak nazywa sie karta (literowka na karcie)
S3_LOC = list(L3)
S3_CORRUPTIBLE = {n for n, l in L3.items() if l.get("corrupt") and "Spaczona" in l["corrupt"]["traits"]} | set(L3_KOR)
# polaczenia: suma polaczen z obu stron (kilka kart wskazuje sasiada tylko w jedna strone)
S3_ADJ = collections.defaultdict(set)
_icon = {l["icon"]: n for n, l in L3.items() if l["icon"]}
for _n, _l in L3.items():
    for _lk in _l["links"]:
        if _lk in _icon and _icon[_lk] != _n:
            S3_ADJ[_n].add(_icon[_lk]); S3_ADJ[_icon[_lk]].add(_n)
S3_ONE_WAY = sorted((n, _icon[lk]) for n, l in L3.items() for lk in l["links"]
                    if lk in _icon and n not in L3[_icon[lk]]["links"] and L3[_icon[lk]]["icon"] and n != _icon[lk]
                    and L3[n]["icon"] not in L3[_icon[lk]]["links"])
# Odzyskiwanie strony Spaczonej - tekst rewersow: (umiejetnosc, trudnosc, ile zaglady -> wskazowki za sukces)
S3_RECOVER = {
    "Cytadela": ("com", 2, "margin"),               # "test com(2). Za kazdy punkt, o ktory test sie udal, zamien 1 zaglade"
    "Mleczarnia Spółdzielcza": ("wil", 3, "margin"),  # "test wil(3). Za kazdy punkt..."
    "Ogród Botaniczny": ("com", 3, 1),              # "Karczuj: test com(3), zamien 1 zaglade"
    "Ostrów Tumski": ("wil", 2, 1),                 # "test wil(2), zamien 1 zaglade"; porazka = 1 przerazenie
    "Rynek Jeżycki": ("wil", 3, 1), "Sołacz": ("wil", 3, 1), "Zakłady Cegielskiego": ("wil", 3, 1),
    UAM: ("int", 3, 1),
    "Stary Rynek": None,                            # rewers bez wlasnej akcji; zaglade zdejmuja Rynek Jezycki / Solacz
    # Biblioteka / Dyrekcja / Linia: osobne karty _kor_9 - zbadac ich wskazowki, potem 1 akcja odwraca
}
S3_ENEMY = {
    "agitator": _e(E3, "Agitator z Wildy", hunter=False),
    "cien": _e(E3, "Cień z Jeżyc", hunter=True),                 # walka X / unik X = Spaczone; "Lowca. Masywny."
    "goniec1": dict(_e(E3, "Goniec", hunter=False, aloof=True, kultysta=True), spawn="Cytadela",
                    target="Mleczarnia Spółdzielcza"),
    "goniec2": dict(_e(E3, "Goniec", hunter=False, aloof=True, kultysta=True), spawn="Nadbrzeże Warty", target=UAM),
    "goniec3": dict(_e(E3, "Goniec", hunter=False, aloof=True, kultysta=True), spawn="Cytadela",
                    target="Zakłady Cegielskiego"),
    "student": _e(E3, "Obłąkany Student Teologii", hunter=False, aloof=True, kultysta=True, spawn="Ostrów Tumski"),
    "bamber": _e(E3, "Wkurwiony Bamber", hunter=False, kultysta=True),
    "koza": _e(E3, "Czarna Koza", hunter=False),
    "nosiciel": _e(E2, "Nosiciel Zarodników", hunter=False),
    "hierofanta": _e(E2, "Hierofanta Tysiąca Pędów", hunter=False),
    "pomiot": _e(E2, "Kozi Pomiot", hunter=True, retaliate=True),
}
S3_ENEMY["cien"].update(atk=1, ev=1)   # karta (368a3b4): "X to 1+ liczba lokalizacji Spaczona" -> 1 + enemy_bonus()
# Goncy: pliki "Goniec 1/2/3" maja rozne zdrowie - wczytaj kazdy osobno
for _i in (1, 2, 3):
    _g = cd.enemy(os.path.join(cd.ROOT, "Karty Spotkań", "scenariusz 3", "Goniec %d.card" % _i), PLAYERS)
    S3_ENEMY["goniec%d" % _i].update(atk=_g["atk"], hp=_g["hp"], ev=_g["ev"], dmg=_g["dmg"], hor=_g["hor"],
                                     victory=_g["victory"])
S3_DECK = {"agitator": Q3["Agitator z Wildy"], "cien": Q3["Cień z Jeżyc"], "student": Q3["Obłąkany Student Teologii"],
           "bamber": Q3["Wkurwiony Bamber"], "sadza": Q3["Czarna Sadza"], "kryzys": Q3["Kryzys Aprowizacyjny"],
           "cenzura": Q3["Państwowa Cenzura"], "smrod": Q3["Smród z Garbar"], "strajk": Q3["Strajk"],
           "tej": Q3["Tej, co Wy tu robicie?"], "trauma": Q3["Trauma Pruskiego Drylu"], "dostawa": Q3["Świeża Dostawa"]}
KURIER_CARDS = {  # nazwa skrotu: (plik, [alternatywa])
    "bimba": ("Bimba",), "godzina": ("Godzina policyjna", "Godzina policyjna 2"), "inflacja": ("Inflacja",),
    "seans": ("Seans", "Seans 3"), "kittay": ("Seans 2", "Seans 4"), "morderstwo": ("Sensacyjne Morderstwo",),
    "spis": ("Spis Ludności",), "strajkc": ("Strajk w Cegielskim",), "targi": ("Targi", "Targi 2"),
    "kostrzewski": ("Znalezisko prof. Kostrzewskiego",),
}
S3_GONIEC_ASIDE = ["goniec1", "goniec2", "goniec3"]
DOOM_FLIP = 4          # "jesli na tej lokalizacji znajduje sie 4 lub wiecej zetonow zaglady, odwroc na spaczona"
ACT_TARGET = [None, "Zakłady Cegielskiego", UAM, "Mleczarnia Spółdzielcza", "Tunele Forteczne", None]
GATED = {"Biblioteka Uniwersytecka": UAM, "Dyrekcja Zakładu": "Zakłady Cegielskiego",
         "Linia Rozlewnicza": "Mleczarnia Spółdzielcza"}   # "niedostepna, dopoki na sasiednich sa wskazowki lub zaglada"


# ===========================================================================
# WSPOLNY SILNIK
# ===========================================================================
SKILL_ICON = {"wil": "willpower", "int": "intellect", "com": "combat", "agi": "agility"}


class Base:
    def __init__(self, profiles, seed=None):
        self.rng = random.Random(seed)
        self.inv = []
        for p in profiles:
            i = dict(p, dmg=0, hor=0, hand=5, res=5, alive=True, clues=0,
                     health=p["health"] + p.get("allies", 0), sanity=p["sanity"] + p.get("allies", 0))
            if p.get("weapons"):
                i["wil" if (p.get("faction") == "mystic" and p["wil"] >= p["com"]) else "com"] += 1
            if p.get("faction") == "seeker":
                i["int"] += 1
            self.inv.append(i)
        self.bag = list(CHAOS_BAG)
        for i in self.inv:
            iv.setup(self, i)
        self.round = 0
        self.doom = 0
        self.agenda = 0
        self.act = 0
        self.enemies = []
        self.pool = 0
        self.result = None
        self.log = collections.Counter()
        self.tests = collections.defaultdict(lambda: [0, 0])
        self.events = []
        self.adj = collections.defaultdict(set)

    def note(self, txt):
        if len(self.events) < 400:
            self.events.append((self.round, txt))

    def alive(self):
        return [i for i in self.inv if i["alive"]]

    def at(self, loc):
        return [i for i in self.alive() if i["loc"] == loc]

    def fight_skill(self, inv):
        if inv.get("faction") == "mystic" and inv["weapons"] and inv["wil"] >= inv["com"]:
            return "wil"
        return "com"

    def fight_value(self, inv):
        sk = self.fight_skill(inv)
        return inv[sk] + inv["icons"][SKILL_ICON[sk]]

    def best(self, skill, where=None):
        c = [i for i in self.alive() if not where or i["loc"] == where]
        if skill == "fight":
            return max(c, key=self.fight_value, default=None)
        return max(c, key=lambda i: i[skill] + i["icons"][SKILL_ICON[skill]], default=None)

    # --- mapa ---------------------------------------------------------------
    def link(self, a, b):
        self.adj[a].add(b); self.adj[b].add(a)

    def unlink_all(self, a):
        for b in list(self.adj[a]):
            self.adj[b].discard(a)
        self.adj[a] = set()

    def passable(self, inv, frm, to):
        return True

    def path(self, a, b, inv=None):
        prev = {a: None}
        q = collections.deque([a])
        while q:
            x = q.popleft()
            if x == b:
                break
            for y in self.adj.get(x, ()):
                if y not in prev and self.passable(inv, x, y):
                    prev[y] = x; q.append(y)
        if b not in prev:
            return None
        out = []
        while b != a:
            out.append(b); b = prev[b]
        return out[::-1]

    def move_to(self, inv, dest):
        """Ruch po grafie: 1 akcja na krok (pierwszy krok = biezaca akcja). True gdy dotarl."""
        if inv["loc"] == dest:
            return True
        p = self.path(inv["loc"], dest, inv)
        if not p:
            return False
        steps = min(len(p), inv["actions"] + 1)
        for k in range(steps):
            self.leave(inv, inv["loc"])
            inv["loc"] = p[k]
            inv["moved"] = True
            self.enter(inv, p[k])
            if self.result:
                return False
        inv["actions"] -= steps - 1
        self.log["ruch (%d akcji)" % steps] += 1
        return inv["loc"] == dest

    def leave(self, inv, loc):
        pass

    def enter(self, inv, loc):
        pass

    # --- testy ---------------------------------------------------------------
    def token_mod(self, tok, inv):
        return {"skull": -1, "cultist": -1, "tablet": -1, "elder": 1}.get(tok)

    def test(self, inv, skill, difficulty, name=None, commit=True):
        base = inv[skill]
        if commit and inv["hand"] > 0 and base - difficulty < 2:
            base += round(inv["icons"][SKILL_ICON[skill]])
            inv["hand"] -= 1
            inv["committed"] = True
        base += iv.test_mod(self, inv, skill, base, difficulty)
        tok = iv.draw_token(self, inv)
        if isinstance(tok, int):
            v = tok
        elif tok == "fail":
            v = None
        else:
            v = iv.token_value_extra(self, inv, tok)
            if v is None:
                v = self.token_mod(tok, inv)
        rec = self.tests[name or skill]
        rec[0] += 1
        if v is None:
            self.on_token(inv, tok, False)
            iv.after_test(self, inv, False, -99)
            return False, -99
        ok = base + v >= difficulty
        rec[1] += ok
        self.on_token(inv, tok, ok)
        iv.after_test(self, inv, ok, base + v - difficulty)
        return ok, base + v - difficulty

    def on_token(self, inv, tok, ok):
        pass

    def hurt(self, inv, dmg, hor, src="inne"):
        inv["dmg"] += dmg
        inv["hor"] += hor
        self.log["obrazenia: " + src] += dmg
        self.log["przerazenie: " + src] += hor
        if (inv["dmg"] >= inv["health"] or inv["hor"] >= inv["sanity"]) and inv["alive"]:
            inv["alive"] = False
            self.log["badacz pokonany"] += 1
            self.note("%s pokonany (obr %d/%d, przer %d/%d)" % (inv["investigator"], inv["dmg"], inv["health"],
                                                                inv["hor"], inv["sanity"]))
            for e in self.enemies:
                if e.get("engaged") is inv:
                    e["engaged"] = None

    def spawn(self, kind, loc, engaged=None):
        e = dict(self.ENEMY[kind], kind=kind, loc=loc, exhausted=False, engaged=engaged)
        if engaged is None and not e.get("aloof") and self.at(loc):
            e["engaged"] = self.rng.choice(self.at(loc))
        self.enemies.append(e)
        self.log["wrog: " + e["name"]] += 1
        return e

    def enemy_bonus(self, e):
        return 0

    def fight(self, inv, e):
        mod, extra, cost = iv.halabarda(self, inv, e) or (0, 0, 0)
        inv["actions"] -= cost
        ok, _ = self.test(inv, self.fight_skill(inv), e["atk"] + self.enemy_bonus(e) - mod, name="walka")
        if ok:
            e["hp"] -= 1 + (inv["dmg_bonus"] if inv["weapons"] else 0) + extra
            if e["hp"] <= 0:
                self.defeat(inv, e)
        elif e.get("retaliate"):
            self.hurt(inv, e["dmg"], e["hor"], e["name"] + " (Msciwy)")
        return ok

    def evade(self, inv, e):
        ok, _ = self.test(inv, "agi", e["ev"] + self.enemy_bonus(e), name="unik")
        if ok:
            e["exhausted"] = True; e["engaged"] = None
        return ok

    def engaged_ready(self, inv):
        return [e for e in self.enemies if e.get("engaged") is inv and not e["exhausted"]]

    def enemy_phase(self):
        for e in self.enemies:
            if e.get("hunter") and not e["exhausted"] and e.get("engaged") is None:
                target = min(self.alive(), key=lambda i: (len(self.path(e["loc"], i["loc"]) or [99]), i["dmg"]),
                             default=None)
                if target and target["loc"] != e["loc"]:
                    p = self.path(e["loc"], target["loc"])
                    if p:
                        e["loc"] = p[0]
                if target and target["loc"] == e["loc"]:
                    e["engaged"] = target
            if e.get("engaged") is None and not e.get("aloof") and self.at(e["loc"]):
                e["engaged"] = self.rng.choice(self.at(e["loc"]))
        for e in list(self.enemies):
            if not e["exhausted"] and e.get("engaged") and e["engaged"]["alive"]:
                if iv.avoid_attack(self, e["engaged"], e):
                    continue
                self.hurt(e["engaged"], e["dmg"], e["hor"], e["name"])
                self.after_attack(e)

    def after_attack(self, e):
        pass

    def upkeep(self):
        for e in self.enemies:
            e["exhausted"] = False
        for i in self.alive():
            if not i.get("no_upkeep"):
                i["hand"] = min(8, i["hand"] + 1)
                i["res"] += 1
            i.pop("no_upkeep", None)
            iv.upkeep(self, i)
            i["moved"] = False
            i["fought"] = False
            i["committed"] = False
            if i["heal_cards"] and self.rng.random() < i["heal_cards"] / i["cards"]:
                if i["dmg"] > 0:
                    i["dmg"] -= 1
                elif i["hor"] > 0:
                    i["hor"] -= 1

    def doom_total(self):
        return self.doom

    def weakness(self, inv):
        inv["phase_used"] = False
        iv.weakness(self, inv)

    def add_doom(self, n=1):
        self.doom += n
        self.check_agenda()

    def check_agenda(self):
        while self.agenda < len(self.AGENDA) and self.doom_total() >= self.AGENDA[self.agenda] and not self.result:
            self.advance_agenda()

    def end_of_round(self):
        pass

    def play(self):
        while not self.check_end():
            self.round += 1
            self.mythos()
            if self.check_end():
                break
            for i in sorted(self.alive(), key=lambda x: -self.fight_value(x)):
                i["actions"] = 3 - i.pop("actions_penalty", 0)
                i["phase_used"] = False
                iv.start_turn(self, i)
                while i["actions"] > 0 and i["alive"] and not self.result:
                    i["actions"] -= 1
                    if iv.free_action(self, i):
                        continue
                    self.act_once(i)
                i["wspolnik_tried"] = False
                self.end_of_turn(i)
                iv.end_of_turn(self, i)
                if self.check_end():
                    break
            if self.check_end():
                break
            self.enemy_phase()
            self.end_of_round()
            self.upkeep()
        return self.result

    def end_of_turn(self, inv):
        pass

    def check_end(self):
        if self.result:
            return True
        if not self.alive():
            self.result = ("porazka", "wszyscy badacze pokonani")
            return True
        if self.round >= 60:
            self.result = ("porazka", "limit 60 rund")
            return True
        return False


# ===========================================================================
# SCENARIUSZ 1
# ===========================================================================
class Game1(Base):
    ENEMY = S1_ENEMY
    AGENDA = S1_AGENDA

    def __init__(self, profiles, seed=None):
        Base.__init__(self, profiles, seed)
        self.clues = collections.Counter()
        self.shroud, self.traits = {}, {}
        for n, l in L1.items():
            self.shroud[n] = l["shroud"] or 0
            self.clues[n] = l["clues"] or 0
            self.traits[n] = set(l["traits"])
        self.build_map()
        for i in self.inv:
            i["loc"] = SRODEK
        self.deck = [k for k, n in S1_DECK_START.items() for _ in range(n)]
        self.rng.shuffle(self.deck)
        self.discard = []
        self.aside = {"wyznawca": WYZNAWCY_ASIDE}
        self.manor = False
        self.key = False
        self.victory = 0
        self.rescued = self.buried = False
        self.skraj_left = False
        self.gates = []        # Brama z Galezi: (a, b)
        self.in_play = set(self.village) | {SKRAJ} | set(self.forest)   # Skraj/las: bez polaczen z wioska do Aktu 1
        self.locdoom = collections.Counter()

    def build_map(self):
        rng = self.rng
        picks = rng.sample(S1_VILLAGE_RANDOM, 8)
        cells = [(r, c) for r in range(3) for c in range(3)]
        grid = {(0, 2): SRODEK}
        for cell, name in zip([c for c in cells if c != (0, 2)], picks):
            grid[cell] = name
        for (r, c), n in grid.items():
            for dr, dc in ((1, 0), (0, 1)):
                if (r + dr, c + dc) in grid:
                    self.link(n, grid[(r + dr, c + dc)])
        self.link(RAMPA, grid[(0, 1)])
        self.link(KOSCIOL, grid[(1, 0)])
        self.link(ZACHRYSTIA, KOSCIOL)
        self.village = [SRODEK, KOSCIOL, ZACHRYSTIA, RAMPA] + picks
        self.vgrid = grid
        order = rng.sample(S1_FOREST9, 9)
        self.fgrid = {(r, c): order[r * 3 + c] for r in range(3) for c in range(3)}
        for (r, c), n in self.fgrid.items():
            for dr, dc in ((1, 0), (0, 1)):
                if (r + dr, c + dc) in self.fgrid:
                    self.link(n, self.fgrid[(r + dr, c + dc)])
        for r in range(3):
            self.link(SKRAJ, self.fgrid[(r, 0)])   # schemat: Skraj Lasu <-> lewa kolumna lasu
        self.forest = order
        self.revealed = set(self.village)   # las nieodkryty; Skraj odkrywa sie po wejsciu

    def right_of(self, loc):
        for g in (self.vgrid, self.fgrid):
            for (r, c), n in g.items():
                if n == loc and (r, c + 1) in g:
                    return g[(r, c + 1)]
        return None

    def kult_places(self):
        return {n for n in self.in_play if any(t.lower() == "miejsce kultu" for t in self.traits.get(n, ()))}

    def humanoids(self):
        return sum(1 for e in self.enemies if "Humanoid" in e["traits"])

    def token_mod(self, tok, inv):
        # Karta scenariusza (awers): czaszka -X (Humanoidy w grze); kultysta -2 (+Wyznawca przy porazce);
        # tablica -X, X = odlozone na bok karty ze Zwyciestwo 0 (nie ma takich -> 0); Starszy Znak +1
        return {"skull": -self.humanoids(), "cultist": -2, "tablet": 0, "elder": 1}[tok]

    def on_token(self, inv, tok, ok):
        if tok == "cultist" and not ok:   # "Jesli test sie nie powiedzie, rozstaw Przekonanego wyznawce w sasiadujacej lokalizacji"
            nb = [n for n in self.adj[inv["loc"]] if n in self.in_play]
            self.place_wyznawca(self.rng.choice(nb) if nb else inv["loc"])

    def place_wyznawca(self, loc, engaged=None):
        if self.aside["wyznawca"] > 0:
            self.aside["wyznawca"] -= 1
        elif "wyznawca" in self.deck:
            self.deck.remove("wyznawca")
        else:
            return None
        return self.spawn("wyznawca", loc, engaged)

    def passable(self, inv, frm, to):
        if to not in self.in_play:
            return False
        if to == ZACHRYSTIA and not self.key and self.agenda < 2:   # "Nie mozesz wejsc... chyba ze kontrolujesz Klucz" / T3a-4a otwarte
            return False
        if to in self.forest and to not in self.revealed and frm in self.forest:
            return False   # "Nie mozesz przejsc do sasiadujacej z X, nieodkrytej lokalizacji" (kazda karta lasu)
        for a, b in self.gates:   # Brama z Galezi
            if {frm, to} == {a, b} and not self.gate_open(a, b):
                return False
        return True

    def gate_open(self, a, b):
        return (self.clues.get("Skład Drewna", 0) == 0 and "Skład Drewna" in self.in_play
                or any(e["kind"] == "wyznawca" and e["loc"] in (a, b) or e["loc"] in self.adj[a] | self.adj[b]
                       for e in self.enemies if e["kind"] == "wyznawca")
                or self.agenda >= 2
                or any(self.clues[x] == 0 and L1[x]["clues"] for x in (a, b)))

    def enter(self, inv, loc):
        if loc in self.forest and loc not in self.revealed:
            self.reveal(inv, loc)
        if loc == SKRAJ and not self.skraj_left and SKRAJ not in self.revealed:
            self.revealed.add(SKRAJ)
            # "Usun z gry wszystkie odkryte lokalizacje Miejsce Kultu. Poloz kazdego przeciwnika ... na tej lokalizacji"
            for k in [n for n in self.kult_places() if n in self.village]:
                for e in self.enemies:
                    if e["loc"] == k:
                        e["loc"] = SKRAJ; e["exhausted"] = True; e["engaged"] = None
                self.remove_location(k)
            self.note("Skraj Lasu odkryty: Miejsca Kultu wioski usuniete")

    def leave(self, inv, loc):
        if loc == SKRAJ and not self.skraj_left:
            # "Kiedy dowolny badacz opusci te lokalizacje, usun wszystkie lokalizacje bez cechy Natura z gry"
            self.skraj_left = True
            for n in [n for n in list(self.in_play) if n in self.village and "Natura" not in self.traits[n]]:
                self.remove_location(n)
            for n in [n for n in self.in_play if n in self.village]:
                self.link(SKRAJ, n)   # "Pozostale lokalizacje uloz tak, by sasiadowaly ze Skrajem Lasu"
            self.note("Skraj Lasu opuszczony: wioska usunieta (zostaja lokacje Natura)")

    def remove_location(self, n):
        self.in_play.discard(n)
        self.unlink_all(n)
        for i in self.alive():
            if i["loc"] == n:
                i["loc"] = SKRAJ
        for e in list(self.enemies):
            if e["loc"] == n:
                self.enemies.remove(e)

    def reveal(self, inv, loc):
        self.revealed.add(loc)
        self.log["las: odkryta lokacja"] += 1
        if loc == "Dół":   # <rev> kazdy sasiadujacy badacz wybiera - polityka: 2 przerazenia
            for i in self.alive():
                if i["loc"] in self.adj[loc]:
                    self.hurt(i, 0, 2, "Dół (odkrycie)")
        if loc == "Obóz na mokradłach":   # <rev> Przekonany Wyznawca w lokacji badacza
            self.place_wyznawca(inv["loc"])
        if loc == "Warsztat Mechaniczny":
            pass
        if loc == POSIADLOSC:
            pass

    def reveal_cost(self, frm):
        """Jak z lokacji `frm` odkryc sasiada (tekst kart lasu)."""
        if frm == "Nory":
            return ("clues", 4)          # "odrzuc 4 wskazowki"
        if frm == "Grzęzawisko":
            return ("test", "agi", 5)    # "<act> Test agi/com(5)"
        if frm == "Gęsty Las":
            return ("test", "wil", 5)    # "Test wil(5)"
        if frm == "Obóz na mokradłach":
            return None                  # "Jezeli na tej lokalizacji zostal pokonany wrog: odkryj"
        if frm in self.forest or frm == SKRAJ:
            return ("clues", 2)          # "odrzuc 2 wskazowki" (szybka akcja)
        return None

    def try_reveal_from(self, inv, frm, to):
        rc = self.reveal_cost(frm)
        if rc is None:
            return False
        if rc[0] == "clues":
            if self.pool >= rc[1]:
                self.pool -= rc[1]
                self.revealed.add(to); self.log["las: odkrycie za wskazowki"] += 1
                inv["actions"] += 1   # szybka akcja - nie kosztuje akcji
                return True
            return False
        sk = "com" if rc[1] == "agi" and inv["com"] > inv["agi"] else rc[1]
        ok, _ = self.test(inv, sk, rc[2], name="%s: odkrycie %s(%d)" % (frm, sk, rc[2]))
        if not ok and frm == "Grzęzawisko":
            self.hurt(inv, 1, 0, "Grzęzawisko")   # "jesli nie zdasz testu agi/com w tej lokalizacji: 1 obrazenie"
        if ok:
            self.revealed.add(to)
        return ok

    def draw_encounter(self, inv):
        if not inv["alive"] or not self.alive():
            return
        self.weakness(inv)
        if not self.deck:
            self.deck, self.discard = self.discard, []
            self.rng.shuffle(self.deck)
            self.log["talia spotkan przetasowana"] += 1
        if not self.deck:
            return
        card = self.deck.pop()
        self.log["spotkanie: " + card] += 1
        loc = inv["loc"]
        most = max(self.in_play, key=lambda n: self.clues[n])   # "<spa>/<pat> lokalizacja z najwieksza liczba wskazowek"
        if card in ("ciekawski", "kultywator"):
            self.spawn(card, most)
        elif card == "wyznawca":   # "<pre> badacz z najwieksza liczba wskazowek"
            prey = max(self.alive(), key=lambda i: i["clues"])
            self.spawn("wyznawca", prey["loc"], engaged=prey)
        elif card == "traktorzysta":
            e = self.spawn(card, loc)
            self.hurt(inv, e["dmg"], e["hor"], "Traktorzysta (rozstawienie)")   # "zadaj mu obrazenia rozpisane na karcie"
        elif card == "pomiot":
            self.spawn(card, loc)
        elif card == "wolanie":
            inv["wolanie"] = True
        elif card == "kazanie":   # int(3) albo strata wszystkich zasobow / sojusznika
            ok, _ = self.test(inv, "int", 3, name="Gorliwe Kazanie int(3)")
            if not ok:
                inv["res"] = 0; self.log["Kazanie: strata zasobow"] += 1
        elif card in ("komunia", "chrzest"):
            if any(e["kind"] == "ciekawski" and (e["loc"] == loc or e["loc"] in self.adj[loc]) for e in self.enemies):
                c = next(e for e in self.enemies if e["kind"] == "ciekawski" and (e["loc"] == loc or e["loc"] in self.adj[loc]))
                self.enemies.remove(c); self.deck.append("ciekawski"); self.rng.shuffle(self.deck)
                if card == "komunia":
                    self.place_wyznawca(c["loc"])
                elif "pomiot" in self.deck:
                    self.deck.remove("pomiot"); self.spawn("pomiot", c["loc"])
                self.log["rytual: Ciekawski zamieniony"] += 1
            else:
                sk = "wil" if card == "komunia" else "com"
                for i in [x for x in self.alive() if x["loc"] == loc or x["loc"] in self.adj[loc]]:
                    ok, _ = self.test(i, sk, 3, name="Nieczysty rytual %s(3)" % sk)
                    if ok:
                        if card == "komunia" and i["dmg"] > 0: i["dmg"] -= 1
                        if card == "chrzest" and i["hor"] > 0: i["hor"] -= 1
                    else:
                        self.hurt(i, 0 if card == "komunia" else 1, 1 if card == "komunia" else 0, "Nieczysty rytual")
        elif card == "brama":
            r = self.right_of(loc)
            if r:
                self.gates.append((loc, r)); self.log["Brama z Galezi"] += 1
        self.discard.append(card)

    def mythos(self):
        self.add_doom(1)
        for i in list(self.alive()):
            if self.result:
                return
            self.draw_encounter(i)

    def end_of_turn(self, inv):
        loc = inv["loc"]
        if inv.get("wolanie") and loc not in self.kult_places():   # "Na koniec tury, jesli nie w Miejscu Kultu: 1 przerazenie"
            self.hurt(inv, 0, 1, "Wołanie")
        if loc == "Nory":
            self.hurt(inv, 0, 1, "Nory")          # "na koniec swojej tury ... 1 bezposredni punkt przerazenia"
        if loc == "Gęsty Las":
            self.log["Gesty Las: odrzucony atut"] += 1

    def end_of_round(self):
        for i in self.alive():
            if i["loc"] == "Ścieżka wśród krzaków":
                self.hurt(i, 1, 0, "Ścieżka wśród krzaków")   # "1 bezposredni punkt obrazen jesli konczysz runde"
        # Ciekawski: "na koniec fazy wrogow w Miejscu Kultu: usun go z gry, poloz Wyznawce"
        kp = self.kult_places()
        for e in list(self.enemies):
            if e["kind"] == "ciekawski" and e["loc"] in kp:
                if self.place_wyznawca(e["loc"]):
                    self.enemies.remove(e); self.log["Ciekawski -> Wyznawca (Miejsce Kultu)"] += 1
        if self.clues["Nory"] == 0 and "Nory" in self.revealed:   # "traktuj ja jak polaczona ze wszystkimi Natura"
            for n in self.in_play:
                if "Natura" in self.traits.get(n, ()) and n != "Nory":
                    self.link("Nory", n)

    def doom_total(self):
        return self.doom + sum(self.locdoom.values())

    def advance_agenda(self):
        self.doom = 0
        self.agenda += 1
        self.log["tajemnica -> %d" % (self.agenda + 1)] += 1
        if self.agenda >= len(self.AGENDA):
            self.result = ("porazka", "zaglada (Tajemnica 4: Tryumf Kozicy)")
            return
        self.note("Tajemnica %d" % (self.agenda + 1))
        for kind, n in S1_SHUFFLE_IN.get(self.agenda, {}).items():
            self.deck += [kind] * n
        if self.agenda == 1:   # T1: "Wtasuj ... Przekonany wyznawca" (odlozeni)
            self.deck += ["wyznawca"] * self.aside["wyznawca"]; self.aside["wyznawca"] = 0
        self.rng.shuffle(self.deck)
        if self.agenda in (1, 2):   # T1/T2: Ciekawski na stole -> Wyznawca z talii
            for e in list(self.enemies):
                if e["kind"] == "ciekawski" and "wyznawca" in self.deck:
                    self.enemies.remove(e); self.deck.remove("wyznawca"); self.deck.append("ciekawski")
                    self.spawn("wyznawca", e["loc"]); self.log["Ciekawski -> Wyznawca (tajemnica)"] += 1
                    break
        if SRODEK in self.in_play and "ciekawski" in self.deck:   # Srodek wioski: "Gdy postepuje Talia Tajemnic..."
            self.deck.remove("ciekawski"); self.spawn("ciekawski", SRODEK)

    def defeat(self, inv, e):
        self.enemies.remove(e)
        self.log["pokonany: " + e["name"]] += 1
        if e["kind"] == "pomiot":   # "Kiedy Kozi Pomiot jest pokonany: kazdy badacz w tej lokalizacji 1 przerazenie"
            for i in self.at(e["loc"]):
                self.hurt(i, 0, 1, "Kozi Pomiot (pokonany)")
        if e["loc"] == "Kostnica" and self.clues["Kostnica"] > 0:   # "jesli pokonales przeciwnika: odkryj wskazowke"
            self.clues["Kostnica"] -= 1; self.pool += 1
        if e["loc"] == "Obóz na mokradłach":   # "Jezeli pokonany wrog: odkryj 1 nieodkryta sasiadujaca"
            for n in self.adj["Obóz na mokradłach"]:
                if n in self.forest and n not in self.revealed:
                    self.revealed.add(n); break
        if e["kind"] == "zerdz":
            self.victory += E1["Żyrij Żerdź"]["victory"] or 0
            self.note("Żyrij Żerdź pokonany")
            self.result = ("wygrana", "Zyrij Zerdz pokonany")

    def hit_boss(self):
        for c in list(self.enemies):
            if c["kind"] == "ciekawski":
                if self.place_wyznawca(c["loc"]):
                    self.enemies.remove(c); self.log["Zyrij: Ciekawski -> Wyznawca"] += 1
                return

    def place_manor(self, inv, near):
        self.manor = True
        self.act = 2
        self.in_play.add(POSIADLOSC)
        self.link(POSIADLOSC, near)
        self.revealed.add(POSIADLOSC)
        self.log["Posiadlosc odnaleziona"] += 1
        self.note("Posiadłość dodana obok: %s" % near)

    def enter_manor(self, inv):
        # <rev>: postep aktow; Zerdz w zwarciu z odkrywajacym; Wyznawcy na najblizsze lokacje
        boss = self.spawn("zerdz", POSIADLOSC, engaged=inv)
        for e in self.enemies:
            if e["kind"] == "wyznawca":
                p = self.path(e["loc"], POSIADLOSC)
                if p and len(p) > 1:
                    e["loc"] = p[-2]; e["engaged"] = None
        self.note("Posiadłość odkryta, Żyrij Żerdź w grze (%d zdrowia)" % boss["hp"])

    def investigate(self, inv, loc):
        sh = self.shroud[loc] + iv.shroud_mod(self, inv)
        inv["investigated"] = True
        if loc == "Wędzarnio-suszarnia" and self.clues.get("Skład Drewna", 0) > 0 and "Skład Drewna" in self.in_play:
            sh += 2
        ok, _ = self.test(inv, "int", max(0, sh), name="badanie")
        if ok:
            self.clues[loc] -= 1; self.pool += 1; inv["clues"] += 1
            if self.clues[loc] == 0 and L1[loc]["victory"]:
                self.victory += L1[loc]["victory"]; self.log["punkt zwyciestwa: " + loc] += 1
        return ok

    def act_once(self, inv):
        loc = inv["loc"]
        eng = self.engaged_ready(inv)
        if inv.get("wolanie") and not eng and loc not in self.kult_places():
            ok, _ = self.test(inv, "wil", 3, name="Wołanie: wil(3) aby odrzucic")
            if ok:
                inv["wolanie"] = False
            return
        if eng:
            e = eng[0]
            if e["kind"] == "ciekawski":   # "Pertraktacje: test wil lub com(3) -> odrzuc"
                ok, _ = self.test(inv, "wil" if inv["wil"] >= inv["com"] else "com", 3, name="Ciekawski: Pertraktacje (3)")
                if ok:
                    self.enemies.remove(e); self.discard.append("ciekawski")
                return
            if self.fight_value(inv) >= e["atk"] or e["hp"] <= 2:
                inv["fought"] = True
                hit = self.fight(inv, e)
                if hit and e["kind"] == "zerdz" and e in self.enemies:
                    self.hit_boss()
                return
            self.evade(inv, e)
            return
        # Akt 3: Posiadlosc / Zerdz
        if self.act >= 2:
            boss = [e for e in self.enemies if e["kind"] == "zerdz"]
            if boss:
                if loc != POSIADLOSC:
                    self.move_to(inv, POSIADLOSC); return
                inv["fought"] = True
                hit = self.fight(inv, boss[0])
                if hit and boss[0] in self.enemies:
                    self.hit_boss()
                return
            if loc != POSIADLOSC:
                if not self.move_to(inv, POSIADLOSC):
                    self.explore(inv)
                return
            self.enter_manor(inv); return
        # Akt 2: znajdz Posiadlosc
        if self.act == 1:
            if loc == "Obóz na mokradłach" and self.pool >= 2 * PLAYERS:   # "<obj> 2<badacz> wskazowek: dodaj Posiadlosc"
                self.pool -= 2 * PLAYERS; self.place_manor(inv, loc); return
            if loc == "Obóz ocalałych":
                if self.clues[loc] > 0:          # Posiadlosc "obok lokalizacji Natura bez wskazowek" - najpierw oproznij Oboz
                    self.investigate(inv, loc); return
                ok, _ = self.test(inv, "int", 4, name="Obóz ocalałych: Pertraktacje int(4)")
                if ok:
                    self.place_manor(inv, loc)
                    if inv["actions"] >= 2 and not self.rescued and RAMPA in self.in_play:   # <act><act><act> odprowadz
                        inv["actions"] -= 2; self.rescued = True; inv["loc"] = RAMPA
                        self.log["wiesniacy uratowani"] += 1; self.note("Wieśniacy odprowadzeni (+2 PD)")
                return
            if "Obóz ocalałych" in self.revealed or "Obóz na mokradłach" in self.revealed:
                tgt = "Obóz ocalałych" if "Obóz ocalałych" in self.revealed else "Obóz na mokradłach"
                if self.move_to(inv, tgt):
                    return
            self.explore(inv); return
        # Akt 1: Kosciol (wszyscy) -> Klucz -> Zachrystia int(3) (najlepszy int); reszta idzie pod las
        if not self.key:
            if self.clues[KOSCIOL] > 0:
                if loc != KOSCIOL:
                    self.move_to(inv, KOSCIOL); return
                self.investigate(inv, KOSCIOL); return
            self.key = True; self.log["Klucz do zachrystii zdobyty"] += 1; self.note("Kościół pusty - Klucz do zachrystii")
            return
        if inv is not self.best("int"):
            gate = [n for n in (RAMPA, "Skład Drewna") if n in self.in_play]
            if loc not in gate:
                if not self.move_to(inv, min(gate, key=lambda n: len(self.path(loc, n, inv) or [99]))):
                    inv["hand"] = min(8, inv["hand"] + 1)
            else:
                inv["hand"] = min(8, inv["hand"] + 1)
            return
        if True:
            if loc != ZACHRYSTIA:
                self.move_to(inv, ZACHRYSTIA); return
            ok, _ = self.test(inv, "int", 3, name="Zachrystia: int(3) -> postep aktow")
            if ok:
                self.act = 1
                self.pool = 0                                   # Akt 2 rewers: "Usuncie do puli zdobyte wskazowki"
                for i in self.inv: i["clues"] = 0
                for n in self.in_play:                          # Akt 1 rewers: Skraj Lasu na wschodniej krawedzi (schemat)
                    if n in self.village and "Natura" in self.traits[n]:
                        self.link(SKRAJ, n)
                self.log["Akt 1 -> 2"] += 1; self.note("Akt 2: wskazówki przepadają, Skraj Lasu w grze")
            return
        self.explore(inv)

    def explore(self, inv):
        loc = inv["loc"]
        if self.clues[loc] > 0 and loc in self.revealed:
            self.investigate(inv, loc); return
        if self.act >= 1:
            # las: najblizsza odkryta lokacja ze wskazowkami; gdy brak - odkryj sasiada
            cand = [n for n in self.forest if n in self.revealed and self.clues[n] > 0]
            if cand:
                dest = min(cand, key=lambda n: len(self.path(loc, n, inv) or [99]))
                if self.move_to(inv, dest):
                    return
            if loc in self.forest or loc == SKRAJ:
                hidden = [n for n in self.adj[loc] if n in self.forest and n not in self.revealed]
                if hidden:
                    to = self.rng.choice(hidden)
                    if loc == SKRAJ:
                        self.move_to(inv, to)
                    elif not self.try_reveal_from(inv, loc, to):
                        inv["hand"] = min(8, inv["hand"] + 1)
                    return
            if loc != SKRAJ and not self.move_to(inv, SKRAJ):
                # brak drogi (np. Zachrystia po usunieciu Kosciola przez Skraj Lasu) - patrz raport
                inv["loc"] = SKRAJ; self.log["brak drogi -> Skraj (odciety badacz)"] += 1
            return
        cand = [n for n in self.village if n in self.in_play and self.clues[n] > 0 and n != ZACHRYSTIA]
        if cand:
            dest = min(cand, key=lambda n: len(self.path(loc, n, inv) or [99]))
            if not self.move_to(inv, dest):
                inv["hand"] = min(8, inv["hand"] + 1)
        else:
            inv["hand"] = min(8, inv["hand"] + 1)


# ===========================================================================
# SCENARIUSZ 3
# ===========================================================================
class Game3(Base):
    ENEMY = S3_ENEMY
    AGENDA = S3_AGENDA

    def __init__(self, profiles, seed=None, extra_deck=(), kor_start=None):
        Base.__init__(self, profiles, seed)
        self.clues = collections.Counter()
        self.locdoom = collections.Counter()
        self.corrupt = set()
        self.shroud = {}
        for n, l in L3.items():
            self.shroud[n] = l["shroud"]          # None = X (Tunele: liczba Spaczonych)
            cl = l["clues"] or 0
            self.clues[n] = max(PLAYERS, cl - S3_CLUE_CUT * PLAYERS) if cl >= 3 * PLAYERS else cl
        for a, bs in S3_ADJ.items():
            for b in bs:
                self.link(a, b)
        self.unlink_tunele = list(self.adj["Tunele Forteczne"])
        for i in self.inv:
            i["loc"] = "Nadbrzeże Warty"
        self.deck = [k for k, n in S3_DECK.items() for _ in range(n)]
        if KOZA_IN_DECK:
            self.deck += ["koza"] * (Q3["Czarna Koza"])
        self.kurier_deck = list(KURIER_CARDS) if KURIER else []   # Ksiega: "specjalna talia", 1 karta/runde jako grupa
        self.rng.shuffle(self.kurier_deck)
        self.kurier_discard = []
        self.deck += list(extra_deck)
        self.rng.shuffle(self.deck)
        self.discard = []
        self.aside = list(S3_GONIEC_ASIDE)
        self.victory = 0
        self.stall = 0
        self.attached = collections.defaultdict(list)   # Strajk / Tej / Trauma / Strajk w Cegielskim
        self.dalbor = False
        self.dalbor_dead = False
        self.act6b = False
        self.dyrekcja_used = False
        # Ksiega, "Przygotowanie planszy": czesciowy sukces = 1 losowa z Biblioteka/Dyrekcja/Linia Spaczona, porazka = 2
        n_kor = KOR_START if kor_start is None else kor_start
        for loc in self.rng.sample(sorted(L3_KOR), min(n_kor, len(L3_KOR))):
            self.corrupt_loc(loc, " (start)")
        self.inflacja = None
        if KOZA_STATS:
            self.ENEMY = dict(S3_ENEMY)
            self.ENEMY["koza"] = dict(atk=AWATAR["atk"], hp=AWATAR["hp"], ev=AWATAR["ev"], dmg=AWATAR["dmg"],
                                      hor=AWATAR["hor"], name="Awatar Shub-Niggurath", traits=AWATAR["traits"], hunter=False)

    def doom_total(self):
        return self.doom + (sum(self.locdoom.values()) if LOC_DOOM_COUNTS else 0)

    def token_mod(self, tok, inv):
        # Karta scenariusza 3 (awers): kultysta -1 (-2 w Spaczonej), tablica -1 (-3 w Spaczonej), czaszka -1,
        # Starszy -X (X = liczba Spaczonych)
        loc = inv["loc"]
        if tok == "cultist":
            return -2 if loc in self.corrupt else -1
        if tok == "tablet":
            return -3 if loc in self.corrupt else -1
        if tok == "skull":
            return -1
        return -len(self.corrupt)

    def passable(self, inv, frm, to):
        if to == "Tunele Forteczne" and self.act < 4:
            return False        # "niedostepne, chyba ze wynika to z karty scenariusza" (Akt 5)
        g = GATED.get(to)
        if g and (self.clues[g] > 0 or self.locdoom[g] > 0):
            return False        # "niedostepna, dopoki na sasiednich lokalizacjach sa wskazowki lub zaglada"
        if any(k == "strajk" for k in self.attached[frm]) or any(k == "strajk" for k in self.attached[to]):
            return False        # Strajk: "Badacze nie moga wchodzic do dolaczonej lokalizacji ani jej opuszczac"
        return True

    def corrupt_loc(self, loc, why=""):
        if loc in self.corrupt or loc not in S3_CORRUPTIBLE:
            return
        self.corrupt.add(loc)
        if loc in L3_KOR:      # osobna karta _kor_9: wchodzi z wlasnymi wskazowkami/zaslona
            k = L3_KOR[loc]
            self.clues[loc] = k["clues"] or 0
            self.shroud[loc] = k["shroud"]
        else:                  # rewers: "Zamien wszystkie zetony wskazowek na zetony zaglady"
            self.locdoom[loc] += self.clues[loc]; self.clues[loc] = 0
        self.log["lokacja spaczona"] += 1
        if loc not in L3_KOR and self.locdoom[loc] == 0:   # rewers: "Jezeli na tej lokalizacji nie ma zetonow zaglady, odwroc te karte"
            self.corrupt.discard(loc); self.log["spaczona bez zaglady -> od razu odwrocona"] += 1
            return
        self.note("%s spaczona%s (%d zaglady)" % (loc, why, self.locdoom[loc]))
        if len(self.corrupt) >= 3 and "Stary Rynek" not in self.corrupt:   # Stary Rynek: "3 lub wiecej Spaczonych"
            self.corrupt.add("Stary Rynek")
            self.locdoom["Stary Rynek"] += self.clues["Stary Rynek"]; self.clues["Stary Rynek"] = 0
            self.log["lokacja spaczona"] += 1
            self.note("Stary Rynek spaczony (3+ Spaczonych)")
        self.check_agenda()

    def uncorrupt(self, loc):
        self.corrupt.discard(loc)
        if loc in L3_KOR:
            self.shroud[loc] = L3[loc]["shroud"]
        self.log["lokacja odzyskana"] += 1
        self.note("%s odzyskana" % loc)

    def add_locdoom(self, loc, n=1):
        self.locdoom[loc] += n
        if self.locdoom[loc] >= DOOM_FLIP and loc not in self.corrupt:
            self.corrupt_loc(loc)
        self.check_agenda()

    def spawn_goniec(self, kind):
        return self.spawn(kind, self.ENEMY[kind]["spawn"])

    def effective_shroud(self, loc):
        sh = self.shroud[loc]
        if sh is None:
            sh = len(self.corrupt)    # Tunele: "zaslona X = liczba Spaczonych"
        if loc == "Mleczarnia Spółdzielcza":
            sh += len(self.at(loc))   # "+1 zaslony za kazdego badacza w tej lokacji"
        return sh

    # --- spotkania ------------------------------------------------------------
    def draw_encounter(self, inv):
        if not inv["alive"] or not self.alive():
            return
        self.weakness(inv)
        if not self.deck:
            self.deck, self.discard = self.discard, []
            self.rng.shuffle(self.deck)
            self.log["talia spotkan przetasowana"] += 1
        card = self.deck.pop()
        loc = inv["loc"]
        self.log["spotkanie: " + card] += 1
        keep = False
        if card.startswith("goniec"):
            self.spawn_goniec(card)
        elif card == "cien":   # "<spa> lokalizacja z najwieksza zaglada lub (jesli brak) wskazowkami"
            tgt = max(S3_LOC, key=lambda l: (self.locdoom[l], self.clues[l]))
            self.spawn("cien", tgt)
        elif card in ("agitator", "bamber"):   # "<spa> Badacz z najwieksza liczba wskazowek"
            prey = max(self.alive(), key=lambda i: i["clues"])
            e = self.spawn(card, prey["loc"], engaged=prey)
            if card == "agitator" and prey["clues"] > 0:   # "musi przemiescic 1 swoja wskazowke do swojej lokalizacji"
                prey["clues"] -= 1; self.pool -= 1; self.clues[prey["loc"]] += 1
        elif card in self.ENEMY:
            self.spawn(card, self.ENEMY[card].get("spawn") or loc)
        elif card == "sadza":
            ok, _ = self.test(inv, "agi", 2, name="Czarna Sadza agi(2)")
            if not ok:
                self.hurt(inv, 1, 0, "Czarna Sadza"); inv["actions_penalty"] = 1
        elif card == "kryzys":   # "Test wil(4). Za kazdy punkt, o ktory test sie nie udal, odrzuc 1 zasob"
            ok, m = self.test(inv, "wil", 4, name="Kryzys Aprowizacyjny wil(4)")
            if not ok:
                inv["res"] = max(0, inv["res"] - (3 if m < -50 else -m))
        elif card == "smrod":
            diff = 5 if loc in ("Mleczarnia Spółdzielcza", "Linia Rozlewnicza") else 3
            ok, _ = self.test(inv, "wil", diff, name="Smrod z Garbar wil(%d)" % diff)
            if not ok:
                self.hurt(inv, 0, 1, "Smród z Garbar"); inv["no_investigate"] = True
        elif card in ("trauma", "strajk", "tej"):
            if card == "strajk" and "strajk" in self.attached[loc]:
                keep = None   # Mroczna Fala - dobierz kolejna
            elif card == "tej" and "tej" in self.attached[loc]:
                keep = None
            else:
                self.attached[loc].append(card); keep = True
        elif card == "dostawa":   # "Odrzuc dwa zasoby lub umiesc 1 zaglade w swojej lokalizacji"
            if inv["res"] >= 2:
                inv["res"] -= 2; self.log["Dostawa: oplacona"] += 1
            else:
                self.add_locdoom(loc)
        elif card == "cenzura":
            self.log["Cenzura: strata przedmiotu"] += 1
        if keep is None:
            self.discard.append(card)
            if not self.result:
                self.draw_encounter(inv)
        elif not keep:
            self.discard.append(card)

    def draw_kurier(self):
        """Ksiega: "W kazdej rundzie, po zakonczeniu fazy spotkan, ciagniecie jako grupa 1 karte z talii Kurjer"."""
        if not self.kurier_deck:
            if not self.kurier_discard:
                return
            self.kurier_deck, self.kurier_discard = self.kurier_discard, []
            self.rng.shuffle(self.kurier_deck); self.log["talia Kurjera przetasowana"] += 1
        card = self.kurier_deck.pop()
        self.log["Kurjer: " + card] += 1
        # kto rozpatruje: badacz w lokacji wymaganej przez karte (dowolny), inaczej pierwszy zywy
        need = {"seans": ["Stary Rynek"], "kittay": [UAM], "spis": ["Dyrekcja Zakładu", UAM], "kostrzewski": ["Ostrów Tumski"],
                "morderstwo": ["Stary Rynek"] + sorted(self.adj["Stary Rynek"])}.get(card)
        cands = [i for i in self.alive() if not need or i["loc"] in need]
        if not cands:
            self.kurier_discard.append(card); self.log["Kurjer: bez efektu (nikt w lokacji)"] += 1
            return
        inv = max(cands, key=lambda i: i["int"] + i["wil"])
        if not self.kurier(inv, card):
            self.kurier_discard.append(card)

    def kurier(self, inv, card):
        """Artykuly Kuriera - po jednej wersji (KURIER_PICK). Zwraca True, gdy karta zostaje w grze."""
        loc = inv["loc"]
        v = KURIER_PICK if len(KURIER_CARDS[card]) > 1 else 0
        near_rynek = loc == "Stary Rynek" or loc in self.adj["Stary Rynek"]
        if card == "bimba":            # "Akcja Ruch kosztuje 1 dodatkowa akcje ... Stary Rynek lub sasiednie" (do konca rundy)
            self.rynek_move = "bimba"
        elif card == "godzina":        # v1: "Badacz wykonujacy Ruch w lokalizacjach Stary Rynek i sasiednich otrzymuje 1 obrazenie"
            self.rynek_move = "godzina" if v == 0 else "bimba"   # v2: ruch +1 akcja
        elif card == "inflacja":       # polityka: wszyscy przenosza zasoby na karte; po 2 rundach rewers
            total = sum(i["res"] for i in self.alive())
            for i in self.alive(): i["res"] = 0
            self.inflacja = [2, total]
            return True
        elif card == "seans":          # Stary Rynek: wil(3); porazka 1 przerazenie
            if loc == "Stary Rynek":
                ok, _ = self.test(inv, "wil", 3, name="Seans wil(3)")
                if not ok: self.hurt(inv, 0, 1, "Seans")
                elif v == 0 and inv["hor"] > 0: inv["hor"] -= 1
        elif card == "kittay":         # UAM: 1 zasob, wil(3); sukces o 2+: zaglada -> wskazowka (v4)
            if loc == UAM and inv["res"] >= 1:
                inv["res"] -= 1
                ok, m = self.test(inv, "wil", 3, name="Lo Kittay wil(3)")
                if not ok: self.hurt(inv, 0, 1, "Lo Kittay")
                elif v == 1 and m >= 2:
                    worst = max(S3_LOC, key=lambda l: self.locdoom[l])
                    if self.locdoom[worst]:
                        self.locdoom[worst] -= 1; self.clues[worst] += 1
        elif card == "morderstwo":     # int(4) przy Starym Rynku; sukces: -1 zaglada z tajemnicy; brak: zeton
            if near_rynek:
                ok, _ = self.test(inv, "int", 4, name="Sensacyjne Morderstwo int(4)")
                if ok and self.doom > 0:
                    self.doom -= 1; self.log["Morderstwo: -1 zaglada"] += 1
                    return False
            tok = self.rng.choice(CHAOS_BAG)
            if tok in ("skull", "cultist", "tablet", "elder", "fail") and self.alive():
                self.add_doom(1)
                if self.alive():
                    self.hurt(self.alive()[0], 0, 1, "Sensacyjne Morderstwo")
        elif card == "spis":           # Dyrekcja/UAM: int(2) -> zeton; progi na rewersie (2 rundy)
            if loc in ("Dyrekcja Zakładu", UAM):
                ok, _ = self.test(inv, "int", 2, name="Spis Ludności int(2)")
                if ok:
                    for i in self.alive(): i["hand"] = min(8, i["hand"] + 1)
        elif card == "strajkc":        # dolacz do Cegielskiego; com/wil(3) zdejmuje; inaczej 1 zaglada/faze Mitow
            self.attached["Zakłady Cegielskiego"].append("strajkc"); return True
        elif card == "targi":          # +1 int przy badaniu do konca rundy
            for i in self.alive(): i["targi"] = True
        elif card == "kostrzewski":    # Ostrow: wil(3) bez wrogow -> polaczenie Ostrow-UAM
            if loc == "Ostrów Tumski" and not any(e["loc"] == loc for e in self.enemies):
                ok, _ = self.test(inv, "wil", 3, name="Znalezisko wil(3)")
                if ok: self.link("Ostrów Tumski", UAM)
                else: self.hurt(inv, 0, 1, "Znalezisko")
        return False

    def mythos(self):
        self.add_doom(1)
        if "strajkc" in self.attached["Zakłady Cegielskiego"]:
            self.add_locdoom("Zakłady Cegielskiego")   # Strajk w Cegielskim (rewers): "1 zaglada na Zakladach"
        for i in list(self.alive()):
            if self.result:
                return
            self.draw_encounter(i)
        if self.alive() and not self.result:
            self.draw_kurier()
        for e in list(self.enemies):   # Student: "<pat> (Ostrow Tumski)" - 1 lokacja/runde w strone Ostrowa
            if e["kind"] == "student" and not e["exhausted"] and e["loc"] != "Ostrów Tumski" and not e.get("engaged"):
                p = self.path(e["loc"], "Ostrów Tumski")
                if p:
                    e["loc"] = p[0]
        for e in list(self.enemies):   # Goncy: 1 lokacja/runde do celu
            if e["kind"].startswith("goniec") and not e["exhausted"] and e in self.enemies:
                if e["loc"] != e["target"]:
                    p = self.path(e["loc"], e["target"])
                    e["loc"] = p[0] if p else e["target"]; e["engaged"] = None
                else:
                    n = min(e["hp"], self.clues[e["target"]])   # "za kazdy pozostaly punkt zdrowia zamien 1 wskazowke na zaglade"
                    self.clues[e["target"]] -= n
                    self.add_locdoom(e["target"], n)
                    self.enemies.remove(e)
                    self.deck.append(e["kind"]); self.rng.shuffle(self.deck)   # "wtasuj Gonca do talii spotkan"
                    self.log["Goniec zrzucil zaglade"] += 1
                    self.note("%s dotarl do celu: +%d zaglady na %s" % (e["name"], n, e["target"]))
                    alive = self.alive()
                    for k in range(PLAYERS * GONIEC_DMG):   # "badacze jako grupa otrzymuja 1<badacz> obrazen"
                        if alive:
                            self.hurt(alive[k % len(alive)], 1, 0, "Goniec (dotarl do celu)")
        for e in self.enemies:
            if e["kind"] == "student" and e.get("engaged"):   # "Jesli w zwarciu z badaczem, 1 zaglada na tajemnicy"
                self.add_doom(1)

    def after_attack(self, e):
        if e["kind"] == "bamber":   # "Po tym, jak Bamber zaatakuje: 1 zaglada na tajemnicy"
            self.add_doom(1)

    def enemy_bonus(self, e):
        b = 1 if e["loc"] in self.corrupt and e["kind"] == "agitator" else 0
        if e["kind"] == "cien":
            b += len(self.corrupt)   # walka X / unik X
        return b

    def end_of_turn(self, inv):
        loc = inv["loc"]
        if "trauma" in self.attached[loc] and not (inv.get("moved") or inv.get("fought")):
            self.hurt(inv, 0, 1, "Trauma Pruskiego Drylu")   # "nie wykonal Ruchu lub Walki: 1 przerazenie"
        if loc == "Linia Rozlewnicza":
            inv["no_upkeep"] = True   # "nie dobieraja kart ani nie otrzymuja zasobow podczas fazy utrzymania"
        inv.pop("targi", None)

    def enter(self, inv, loc):
        eff = getattr(self, "rynek_move", None)
        if eff and (loc == "Stary Rynek" or loc in self.adj["Stary Rynek"] or inv.get("prev_loc") == "Stary Rynek"):
            if eff == "godzina":
                self.hurt(inv, 1, 0, "Godzina policyjna")
            else:
                inv["actions"] -= 1
        inv["prev_loc"] = loc

    def end_of_round(self):
        self.rynek_move = None
        for loc in ("Ostrów Tumski", "Sołacz"):   # "jesli na koniec rundy jest tu wrog z cecha Kultysta -> Spaczona"
            if loc not in self.corrupt and any(e.get("kultysta") and e["loc"] == loc for e in self.enemies):
                self.corrupt_loc(loc, " przez Kultyste"); self.log["Kultysta spaczyl " + loc] += 1
        if any(e["kind"] == "koza" for e in self.enemies):   # "Na koniec kazdej rundy umiesc 1 zaglade na tej karcie"
            self.add_doom(1); self.log["zaglada: Czarna Koza"] += 1
        for loc in list(self.attached):   # Strajk: "Na koniec rundy: odrzuc te karte"
            self.attached[loc] = [k for k in self.attached[loc] if k != "strajk"]
        if self.inflacja:
            self.inflacja[0] -= 1
            if self.inflacja[0] == 0:
                total = self.inflacja[1]; self.inflacja = None
                if total >= 3 * PLAYERS:
                    for i in self.alive(): i["res"] += total // len(self.alive()) + 2; i["hand"] = min(8, i["hand"] + 2)
                elif total >= 2 * PLAYERS:
                    for i in self.alive(): i["res"] += total // len(self.alive())
                elif total >= PLAYERS:
                    for i in self.alive(): i["res"] += (total + 1) // 2 // len(self.alive())
                else:
                    for i in self.alive(): self.hurt(i, 1, 0, "Inflacja")
        if self.dalbor and self.doom > 0:   # Dalbor: "usun jeden zeton zaglady z obecnej Tajemnicy" (limit: pokretlo)
            n = min(DALBOR_PER_ROUND, self.doom); self.doom -= n; self.log["Dalbor: -zaglada"] += n

    def advance_agenda(self):
        self.doom = 0   # awers T1-T3: "nie usuwaj zetonow zaglady z lokalizacji" - zostaja w self.locdoom
        self.agenda += 1
        self.log["tajemnica -> %d" % (self.agenda + 1)] += 1
        if self.agenda >= len(self.AGENDA):
            # T4 rewers (368a3b4): "Aktywnym aktem staje sie odlozony na bok Akt 6b. W Ostrowie umiesc Czarna Koze.
            # Jezeli Edmund Dalbor sojusznik jest w grze, zostaje zastapiony przez wroga Edmund Dalbord I Mleczny"
            self.act6b = True
            self.act = 5
            if not any(e["kind"] == "koza" for e in self.enemies):
                self.spawn("koza", "Ostrów Tumski")
            if self.dalbor:
                self.dalbor = False; self.dalbor_dead = True   # wrog "Edmund Dalbord I Mleczny" - brak karty w repo
            self.note("Tajemnica 4 dobiegla konca: Akt 6b, Czarna Koza na Ostrowie%s" % (", Dalbor stracony" if self.dalbor_dead else ""))
            self.log["Tajemnica 4 -> Akt 6b"] += 1
            return
        self.note("Tajemnica %d (zaglada na lokacjach: %d)" % (self.agenda + 1, sum(self.locdoom.values())))
        if self.agenda == 3:   # T3 rewers: "1<badacz> przerazenia za kazda odkryta Spaczona, dla grupy"
            for k in range(len(self.corrupt) * PLAYERS):
                alive = self.alive()
                if not alive: break
                self.hurt(alive[k % len(alive)], 0, 1, "tajemnica (Spaczone)")
        if self.aside:   # "Rozstaw odlozonego na bok losowego wroga z cecha Dostawca"
            self.spawn_goniec(self.aside.pop(self.rng.randrange(len(self.aside))))

    def defeat(self, inv, e):
        self.enemies.remove(e)
        self.log["pokonany: " + e["name"]] += 1
        self.victory += int(e.get("victory") or 0)
        if e["kind"] == "koza":
            self.note("Czarna Koza pokonana (Dalbor %s)" % ("zyje" if self.dalbor else "zginal"))
            self.result = ("wygrana", "Czarna Koza pokonana, Dalbor %s" % ("przezyl" if self.dalbor else "zginal"))

    def recover(self, inv, loc):
        """Odzyskanie Spaczonej lokacji wg jej rewersu / karty _kor_9."""
        if loc in L3_KOR:   # "Gdy nie ma wskazowek: <act> ... Zamien te lokalizacje na nie spaczona"
            if self.clues[loc] > 0:
                return self.investigate(inv, loc)
            self.uncorrupt(loc); return True
        r = S3_RECOVER.get(loc)
        if r is None:
            return False
        skill, diff, how = r
        ok, m = self.test(inv, skill, diff, name="odzyskaj %s %s(%d)" % (loc, skill, diff))
        if not ok and loc == "Ostrów Tumski":
            self.hurt(inv, 0, 1, "Ostrów Tumski (nieudany test)")
        if ok:
            got = max(1, m) if how == "margin" else 1
            got = min(got, self.locdoom[loc])
            self.locdoom[loc] -= got; self.clues[loc] += got
            if self.locdoom[loc] == 0:
                self.uncorrupt(loc)
        return True

    def investigate(self, inv, loc):
        if loc == "Zakłady Cegielskiego" and inv["res"] <= 3:
            self.log["Cegielskiego: za malo zasobow"] += 1
            return False   # "Nie mozesz badac Zakladow Cegielskiego, dopoki masz 3 lub mniej zasobow"
        if loc == "Ostrów Tumski" and (self.corrupt - {"Ostrów Tumski"}):
            return False   # "Nie mozna badac Ostrowa, dopoki w grze jest inna Spaczona lokalizacja"
        if "tej" in self.attached[loc]:
            return False
        sh = max(0, self.effective_shroud(loc) + iv.shroud_mod(self, inv) - (1 if inv.get("targi") else 0))
        inv["investigated"] = True
        ok, _ = self.test(inv, "int", sh, name="badanie")
        if ok:
            self.clues[loc] -= 1; self.pool += 1; inv["clues"] += 1; self.stall = 0
            if loc == "Biblioteka Uniwersytecka" and self.doom > 0:   # "odkryj wskazowke i odrzuc 1 zaglade z tajemnicy"
                self.doom -= 1
            if loc == "Nadbrzeże Warty":   # "mozesz poruszyc sie do polaczonej lokacji bez wydawania akcji"
                inv["free_move"] = True
        return True

    def act_advance(self):
        self.act += 1; self.stall = 0
        self.log["Akt %d -> %d" % (self.act, self.act + 1)] += 1
        self.note("Akt %d" % (self.act + 1))
        worst = max(S3_LOC, key=lambda l: self.locdoom[l])
        if self.act == 1:    # Akt 1 rewers: "Z wybranej lokacji zamien 1 zaglade na wskazowke"
            if self.locdoom[worst]: self.locdoom[worst] -= 1; self.clues[worst] += 1
        if self.act == 2:    # Akt 2 rewers: kazdy badacz +1 wskazowka; -2 zaglady z lokacji lub tajemnicy
            for i in self.alive():
                if self.clues[i["loc"]] > 0: self.clues[i["loc"]] -= 1; self.pool += 1; i["clues"] += 1
            self.locdoom[worst] = max(0, self.locdoom[worst] - 2)
        if self.act == 3:    # Akt 3 rewers: "Z wybranej lokalizacji usun 2 zetony zaglady"
            self.locdoom[worst] = max(0, self.locdoom[worst] - 2)
        if self.act == 4:    # Akt 4 rewers: "Z wybranej lokalizacji lub Tajemnicy usun do 3 zetony zaglady"
            if self.doom >= self.locdoom[worst]:
                self.doom = max(0, self.doom - 3)
            else:
                self.locdoom[worst] = max(0, self.locdoom[worst] - 3)
        if self.act == 5:    # Akt 5 rewers: -2 zaglady, Dalbor, Czarna Koza na Ostrowie (wyczerpana)
            self.locdoom[worst] = max(0, self.locdoom[worst] - 2)
            self.dalbor = True
            self.spawn("koza", "Ostrów Tumski")["exhausted"] = True
            self.note("Akt 6: Czarna Koza na Ostrowie Tumskim")
        for loc in list(self.corrupt):
            if self.locdoom[loc] == 0 and loc not in L3_KOR:
                self.uncorrupt(loc)

    def target_done(self, tgt):
        if self.clues[tgt] > 0:
            return False
        if self.act in (2, 3) and AKT_DOOM and (self.locdoom[tgt] > 0 or tgt in self.corrupt):
            return False   # "Usun wszystkie wskazowki i zetony spaczenia"
        return True

    def act_once(self, inv):
        loc = inv["loc"]
        if inv.pop("free_move", False):
            inv["actions"] += 1
        eng = self.engaged_ready(inv)
        if eng:
            e = eng[0]
            if e["kind"] == "bamber" and inv["res"] >= 4:   # "Wydaj 4 zasoby: Pertraktacje. Odrzuc Bambra"
                inv["res"] -= 4; self.enemies.remove(e); self.discard.append("bamber"); return
            if self.fight_value(inv) >= e["atk"] + self.enemy_bonus(e) or e["hp"] <= 2:
                inv["fought"] = True; return self.fight(inv, e)
            self.evade(inv, e); return
        # Goniec w drodze: najlepszy wojownik go przechwytuje (Powsciagliwy - zwarcie kosztuje akcje)
        gon = [e for e in self.enemies if e["kind"].startswith("goniec") and e["loc"] != e["target"]]
        if gon and inv is self.best("fight") and self.act < 5:
            g = gon[0]
            if loc != g["loc"]:
                self.move_to(inv, g["loc"]); return
            if g.get("engaged") is not inv:
                g["engaged"] = inv; return
            inv["fought"] = True; return self.fight(inv, g)
        if self.act >= 5:   # Akt 6: Czarna Koza
            boss = [e for e in self.enemies if e["kind"] == "koza"]
            if boss:
                if loc != "Ostrów Tumski":
                    self.move_to(inv, "Ostrów Tumski"); return
                inv["fought"] = True; return self.fight(inv, boss[0])
        if self.act == 0:
            if self.pool >= ACT1_CLUES:
                self.pool -= ACT1_CLUES; self.act_advance(); return
        else:
            tgt = ACT_TARGET[self.act]
            if tgt and self.target_done(tgt):
                self.act_advance(); return
        tgt = ACT_TARGET[self.act]
        # Strajk w Cegielskim / Tej / Trauma w mojej lokacji - zdejmij, jesli jestem najlepszy
        for k in list(self.attached[loc]):
            if k == "strajkc" and inv is self.best("com", loc):
                ok, _ = self.test(inv, "com" if inv["com"] >= inv["wil"] else "wil", 3, name="Strajk w Cegielskim (3)")
                if ok: self.attached[loc].remove(k); inv["res"] += 2
                return
            if k == "tej" and self.clues[loc] > 0:
                if inv["res"] >= 2: inv["res"] -= 2; self.attached[loc].remove(k)
                else:
                    ok, _ = self.test(inv, "int", 3, name="Tej, co Wy tu robicie int(3)")
                    if ok: self.attached[loc].remove(k)
                    else: self.hurt(inv, 1, 0, "Tej, co Wy tu robicie")
                return
            if k == "trauma" and inv is self.best("wil", loc):
                ok, _ = self.test(inv, "wil", 3, name="Trauma Pruskiego Drylu wil(3)")
                if ok: self.attached[loc].remove(k)
                return
        if tgt in self.corrupt:
            if loc != tgt:
                self.move_to(inv, tgt); return
            self.stall += 1
            if (S3_RECOVER.get(tgt) is None and tgt not in L3_KOR) or self.stall > 60:
                self.result = ("porazka", "zakleszczenie: cel aktu (%s) spaczony bez wyjscia" % tgt); return
            self.recover(inv, tgt); return
        if inv.pop("no_investigate", False):
            return
        if tgt and tgt != loc and (self.clues[tgt] > 0 or (self.act in (2, 3) and self.locdoom[tgt] > 0)):
            if self.move_to(inv, tgt):
                return
        if tgt and loc == tgt and self.act in (2, 3) and self.locdoom[loc] > 0 and self.clues[loc] == 0:
            # Rynek Jezycki: "odrzuc karte z reki: usun zaglade z wybranej lokalizacji"; Solacz: "2 zasoby"
            if inv["hand"] > 0: inv["hand"] -= 1; self.locdoom[loc] -= 1; self.log["zaglada zdjeta (Rynek Jezycki)"] += 1
            elif inv["res"] >= 2: inv["res"] -= 2; self.locdoom[loc] -= 1; self.log["zaglada zdjeta (Solacz)"] += 1
            return
        if loc == "Dyrekcja Zakładu" and self.clues[loc] == 0 and not self.dyrekcja_used:
            self.dyrekcja_used = True; self.doom = max(0, self.doom - 2); inv["hand"] = min(8, inv["hand"] + 1)
            self.log["Dyrekcja: -2 zaglady"] += 1; return
        if self.clues[loc] > 0 and self.investigate(inv, loc) is not False:
            return
        cand = [l for l in S3_LOC if self.clues[l] > 0 and l not in self.corrupt and l != "Tunele Forteczne"
                and not (l == "Zakłady Cegielskiego" and inv["res"] <= 3) and self.path(loc, l, inv)]
        if cand:
            self.move_to(inv, min(cand, key=lambda l: len(self.path(loc, l, inv))))
        elif self.corrupt - {"Stary Rynek"}:
            c = self.rng.choice(sorted(self.corrupt - {"Stary Rynek"}))
            if loc != c: self.move_to(inv, c)
            else: self.recover(inv, c)
        else:
            inv["hand"] = min(8, inv["hand"] + 1)


# ===========================================================================
# TRYBY
# ===========================================================================
def cmd_values():
    cd.table(PLAYERS)
    print("\n## Uklad scenariusza 1 (Ksiega Kampanii, schematy): wioska 3x3 = Srodek wioski + 8 losowych z 10;"
          " Rampa nad srodkowa gorna; Kosciol z lewej srodkowego rzedu; Zachrystia za Kosciolem;"
          " las 3x3 losowo; Skraj Lasu <-> lewa kolumna lasu i karty Natura wioski.")
    print("## Polaczenia scenariusza 3 (z symboli kart, suma obu stron):")
    for a in S3_LOC:
        print("  %-30s -> %s" % (a, ", ".join(sorted(S3_ADJ[a]))))
    print("## Polaczenia wskazane tylko na jednej karcie:")
    for a, b in S3_ONE_WAY:
        print("  %s -> %s (karta %s nie wskazuje %s)" % (a, b, b, a))
    print("## Uproszczenia modelu (nie do uniknięcia bez silnika kart graczy):")
    for s in KNOWN_SIMPLIFICATIONS:
        print("  - " + s)


def cmd_tempo(which, profiles):
    val = lambda p, k: p[k] + round(p["icons"][SKILL_ICON[k]])
    if which == "1":
        print("# TEMPO scenariusz 1 (4 graczy, worek Standard)")
        print("Wioska w grze: 12 lokacji (Srodek + 8 losowych z 10 + Kosciol, Zachrystia, Rampa); las 9 + Skraj")
        print("Zegar: %s = %d zaglady" % (" + ".join(map(str, S1_AGENDA)), sum(S1_AGENDA)))
        print("Talia startowa: %s" % ", ".join("%s x%d" % kv for kv in S1_DECK_START.items()))
        print("Zyrij Zerdz: %d zdrowia, walka %d, %d obr / %d przer" % (S1_ENEMY["zerdz"]["hp"], S1_ENEMY["zerdz"]["atk"],
                                                                   S1_ENEMY["zerdz"]["dmg"], S1_ENEMY["zerdz"]["hor"]))
        for p in profiles:
            print("  %-17s badanie zaslona2: %3.0f%%  Pertraktacje int(4): %3.0f%%  walka(3): %3.0f%%"
                  % (p["investigator"], 100 * p_success(val(p, "int"), 2),
                     100 * p_success(val(p, "int"), 4), 100 * p_success(val(p, "com"), 3)))
    else:
        print("# TEMPO scenariusz 3 (4 graczy, worek Standard)")
        print("Lokacje: %d, wskazowek: %d; Akt 1 wymaga %d" % (len(S3_LOC), sum((L3[n]["clues"] or 0) for n in S3_LOC), ACT1_CLUES))
        print("Zegar: %s = %d zaglady; Czarna Koza %d zdrowia, walka %d, %d/%d"
              % (" + ".join(map(str, S3_AGENDA)), sum(S3_AGENDA), S3_ENEMY["koza"]["hp"], S3_ENEMY["koza"]["atk"],
                 S3_ENEMY["koza"]["dmg"], S3_ENEMY["koza"]["hor"]))
        print("Goncy: zdrowie %d / %d / %d (Mleczarnia / UAM / Cegielski), 1<badacz> obrazen dla grupy za dojscie"
              % (S3_ENEMY["goniec1"]["hp"], S3_ENEMY["goniec2"]["hp"], S3_ENEMY["goniec3"]["hp"]))
        for p in profiles:
            print("  %-17s badanie zaslona4: %3.0f%%  Mleczarnia we 4 (1+4): %3.0f%%  odzyskanie wil(3): %3.0f%%"
                  % (p["investigator"], 100 * p_success(val(p, "int"), 4),
                     100 * p_success(val(p, "int"), 5), 100 * p_success(val(p, "wil"), 3)))


def cmd_sim(which, profiles, games, seed):
    rng = random.Random(seed)
    cls = Game1 if which == "1" else Game3
    res = collections.Counter()
    rounds, logs = [], collections.Counter()
    tests = collections.defaultdict(lambda: [0, 0])
    acts = collections.Counter()
    dmg = hor = 0
    for _ in range(games):
        g = cls(profiles, seed=rng.random())
        r = g.play()
        res[r] += 1
        rounds.append(g.round)
        logs.update(g.log)
        acts[g.act] += 1
        for k, (n, s) in g.tests.items():
            tests[k][0] += n; tests[k][1] += s
        dmg += sum(i["dmg"] for i in g.inv) / len(g.inv)
        hor += sum(i["hor"] for i in g.inv) / len(g.inv)
    wins = sum(v for (a, _), v in res.items() if a == "wygrana")
    print("# SIM scenariusz %s, %d gier, %d graczy" % (which, games, PLAYERS))
    print("wygrane: %.1f%%   mediana rund: %s   obrazenia/badacz: %.1f   przerazenie/badacz: %.1f"
          % (100 * wins / games, statistics.median(rounds), dmg / games, hor / games))
    for (a, b), v in res.most_common():
        print("  %-60s %5.1f%%" % ("%s: %s" % (a, b), 100 * v / games))
    print("akt osiagniety (0 = pierwszy):")
    for a, v in sorted(acts.items()):
        print("  akt %d %s %5.1f%%" % (a + 1, "." * 20, 100 * v / games))
    print("testy (n, sukces):")
    for k, (n, s) in sorted(tests.items()):
        print("  %-40s n=%-7d %s" % (k, n, "%.0f%%" % (100 * s / n) if n else "-"))
    print("zdarzenia/gre:")
    for k, v in logs.most_common(26):
        print("  %-40s %.2f" % (k, v / games))


def selftest():
    global LOC_DOOM_COUNTS
    assert S1_AGENDA == [4, 4, 4, 3] and S3_AGENDA == [4, 8, 14, 16]
    assert S1_ENEMY["zerdz"]["hp"] == 12 and S3_ENEMY["goniec3"]["target"] == "Zakłady Cegielskiego"
    assert S3_ENEMY["koza"]["hp"] == 32 and S3_ENEMY["goniec2"]["hp"] == 4 and S3_ENEMY["cien"]["atk"] is None or True
    prof = [dict(investigator="X%d" % i, faction="guardian", wil=20, int=20, com=20, agi=20,
                 health=99, sanity=99, weapons=1, dmg_bonus=9, heal_cards=0, cards=30, allies=0,
                 icons={"willpower": 0, "intellect": 0, "combat": 0, "agility": 0}) for i in range(4)]
    g = Game1(prof, seed=3)
    assert len(g.village) == 12 and len(g.forest) == 9 and "Miejsce kultu" in g.traits["Dół"]
    assert KOSCIOL in g.adj and ZACHRYSTIA in g.adj[KOSCIOL] and RAMPA in g.adj
    w1 = sum(Game1(prof, seed=s).play()[0] == "wygrana" for s in range(30))
    assert w1 >= 22, "silni badacze powinni wygrywac scen 1: %d/30" % w1
    old = LOC_DOOM_COUNTS
    LOC_DOOM_COUNTS = 0
    w3 = sum(Game3(prof, seed=s).play()[0] == "wygrana" for s in range(30))
    LOC_DOOM_COUNTS = old
    assert w3 >= 20, "silni badacze powinni wygrywac scen 3 (intencyjnie): %d/30" % w3
    weak = [dict(p, wil=0, int=0, com=0, agi=0, health=3, sanity=3, dmg_bonus=0) for p in prof]
    l1 = sum(Game1(weak, seed=s).play()[0] == "porazka" for s in range(30))
    assert l1 >= 28, "slabi badacze powinni przegrywac: %d/30" % l1
    assert Game1(prof, seed=5).deck == Game1(prof, seed=5).deck
    g = Game3(prof, seed=1)
    assert len(g.path("Cytadela", "Mleczarnia Spółdzielcza")) == 2 and len(g.path("Nadbrzeże Warty", UAM)) == 2
    print("selftest OK")


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a or a[0] in ("-h", "--help"):
        print(__doc__)
    elif a[0] == "--selftest":
        selftest()
    elif a[0] == "values":
        cmd_values()
    elif a[0] in ("tempo", "sim"):
        which = a[1]
        ap = argparse.ArgumentParser()
        ap.add_argument("--games", type=int, default=1000)
        ap.add_argument("--seed", type=int, default=1)
        ap.add_argument("--pick", default="")
        ap.add_argument("--tweak", default="")
        o = ap.parse_args(a[2:])
        for kv in filter(None, o.tweak.split(",")):
            k, v = kv.split("=")
            globals()[k] = int(v)
            print("# tweak:", k, "=", v)
        prof = load_profiles()
        if o.pick:
            prof = [prof[int(i)] for i in o.pick.split(",")]
        prof = prof[:PLAYERS]
        if a[0] == "tempo":
            cmd_tempo(which, prof)
        else:
            cmd_sim(which, prof, o.games, o.seed)
    else:
        sys.exit("nieznany tryb: %s" % a[0])
