#!/usr/bin/env python3
"""Model scenariuszy 1 ("Wioska wsrod drzew") i 3 ("Czarny Port"): tempo + Monte Carlo.

Uzycie:
  python tools/scenario13_model.py tempo 1|3
  python tools/scenario13_model.py sim 1|3 --games 2000 [--tweak K=V,...] [--pick 3,1]
  python tools/scenario13_model.py --selftest

Ta sama filozofia co tools/scenario2_model.py: to NIE jest silnik zasad AH LCG.
Talie graczy to profile liczbowe z tools/arkhamdb.py, efekty kart spotkan sa
skrocone do liczb, polityka graczy to lista priorytetow. Kazde uproszczenie ma
komentarz "# uproszczenie:". Dane przepisane recznie z kart w repo (stan 5 IX 2026,
commit 1dcd1ae "goniec debuffed"). Model NIE zmienia zadnych kart.

Pokretla (--tweak K=V), domyslnie = tak jak stoi na kartach:
  LOC_DOOM_COUNTS=1  zaglada na lokacjach liczy sie do progu tajemnicy (zasady AH LCG:
                     "zaglada w grze"); 0 = tylko zaglada na tajemnicy (czytanie "intencyjne")
  KOZA_STATS=0       0 = karta Czarna Koza tak jak w repo (kopia Agitatora: walka 2, 3 zdrowia);
                     1 = statystyki Awatara z folderu "Scenariusz 4" (walka 4, 10<badacz>, 2/2)
  KOZA_IN_DECK=1     karta Czarna Koza ma quantity 2 i grupe spotkan f, wiec siedzi w talii
"""
import sys, os, io, json, random, argparse, statistics, collections

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from scenario2_model import CHAOS_BAG, token_value, p_success, load_profiles, CACHE

PLAYERS = 4
LOC_DOOM_COUNTS = 1
KOZA_STATS = 0
KOZA_IN_DECK = 1
S3_CLUE_CUT = 0     # wrazliwosc: o ile obnizyc wskazowki/badacza w lokacjach z 3<badacz> (0 = jak na kartach)
S3_DECK_COPIES = 0  # wrazliwosc: 0 = quantity z kart; N = kazda karta talii w N kopiach

# ===========================================================================
# SCENARIUSZ 1 - "Wioska wsrod drzew"
# ===========================================================================
# Wioska: Srodek wioski (start) + losowe lokacje + Kosciol; Las: siatka 3x3 + Skraj Lasu;
# Posiadlosc stawiaja Nory / Oboz ocalalych (Pertraktacje int 4).
# uproszczenie: 11 z 14 lokacji wioski ma w repo zaslone i wskazowki "?" (pole puste) -
# przyjmujemy zaslone 2 i 1<badacz> wskazowek, bo bez tego nie da sie nic policzyc.
S1_VILLAGE = {  # nazwa: (zaslona, wskazowki na badacza)
    "Srodek wioski": (2, 1), "Kosciol": (2, 2), "Zachrystia": (1, 1),
    "Przybrzezna rampa": (2, 1), "Kapliczka": (2, 1), "Kostnica": (2, 1),
    "Pod Rogatym": (2, 1), "Sklad Drewna": (2, 1), "Stary magazyn": (2, 1),
    "Targ Rybny": (2, 1), "Warsztat Kowalski": (2, 1), "Warsztat Kolodzieja": (2, 1),
}
S1_FOREST = {  # las: (zaslona, wskazowki LACZNIE przy 4 graczach) - wartosci z kart
    "Skraj Lasu": (2, 4), "Ambona": (0, 1), "Dol": (2, 4), "Grzezawisko": (1, 8),
    "Gesty Las": (3, 4), "Nory": (4, 4), "Oboz na mokradlach": (3, 4), "Oboz ocalalych": (0, 2),
    "Polana": (2, 4), "Sciezka wsrod krzakow": (1, 4),
}
REVEAL_COST = 2   # "odrzuc 2 wskazowki: odkryj sasiadujaca lokacje" (Nory: 4, Grzezawisko/Gesty Las: test 5)
S1_ENEMY = {
    "ciekawski": dict(atk=2, hp=2, ev=2, dmg=1, hor=0, name="Ciekawski wiesniak", aloof=True, hunter=False),
    "wyznawca": dict(atk=3, hp=3, ev=3, dmg=1, hor=1, name="Przekonany wyznawca", aloof=False, hunter=True),
    "kultywator": dict(atk=1, hp=5, ev=1, dmg=1, hor=0, name="Zblakany Kultywator", aloof=True, hunter=False),
    "traktorzysta": dict(atk=4, hp=5, ev=3, dmg=2, hor=1, name="Kultysta Traktorzysta", aloof=False, hunter=True),
    "pomiot": dict(atk=3, hp=3, ev=2, dmg=1, hor=0, name="Kozi Pomiot", aloof=False, hunter=True),
    # karta: obrazenia puste (0), przerazenie 1
    "zerdz": dict(atk=3, hp=3 * PLAYERS, ev=3, dmg=0, hor=1, name="Zyrij Zerdz", aloof=False, hunter=False),
}
# Talia startowa: Ciekawski x5, Kultywator x2, Wolanie; reszta "odlozona na bok" (tajemnice).
S1_DECK_START = {"ciekawski": 5, "kultywator": 2, "wolanie": 1}
S1_SHUFFLE_IN = {  # po tajemnicy N -> co wtasowac (rewersy tajemnic)
    1: {"brama": 2, "kazanie": 1, "traktorzysta": 1, "komunia": 1, "chrzest": 1},
    2: {},                       # Brama/Traktorzysta juz w talii
    3: {"pomiot": 2},
}
S1_AGENDA = [7, 7, 7, 4]

# ===========================================================================
# SCENARIUSZ 3 - "Czarny Port"
# ===========================================================================
# (zaslona, wskazowki na badacza, moze sie spaczyc)
S3_LOC = {
    "Nadbrzeze Warty": (1, 1, False), "Stary Rynek": (2, 2, True),
    "Ostrow Tumski": (3, 1, True), "Rynek Jezycki": (3, 2, True),
    "Solacz": (3, 1, True), "Ogrod Botaniczny": (4, 1, True),
    "Zaklady Cegielskiego": (4, 1, True), "Mleczarnia Spoldzielcza": (2, 3, True),
    "Linia Rozlewnicza": (4, 3, True), "Dyrekcja Zakladu": (4, 3, True),
    "Biblioteka Uniwersytecka": (4, 3, True), "UAM": (4, 3, True),
    "Cytadela": (2, 2, True), "Tunele Forteczne": (4, 3, False),
}
# Odzyskiwanie spaczonej lokacji: (umiejetnosc, trudnosc, ile zaglady za sukces: "margin" | 1)
# Stary Rynek: rewers nie ma zadnej akcji odzyskania -> None (permanentny).
S3_RECOVER = {
    "Cytadela": ("com", 2, "margin"), "Mleczarnia Spoldzielcza": ("wil", 3, "margin"),
    "Ogrod Botaniczny": ("com", 3, 1), "Ostrow Tumski": ("wil", 2, 1), "Rynek Jezycki": ("wil", 3, 1),
    "Solacz": ("wil", 3, 1), "UAM": ("int", 3, 1), "Zaklady Cegielskiego": ("wil", 3, 1),
    "Linia Rozlewnicza": ("int", 4, 1), "Dyrekcja Zakladu": ("int", 4, 1),
    "Biblioteka Uniwersytecka": ("int", 4, 1), "Stary Rynek": None,
}
# Sasiedztwo z symboli polaczen (location_link/location_icon) - do patrolu Goncow
S3_ADJ = {
    "Nadbrzeze Warty": ["Stary Rynek", "Ostrow Tumski"],
    "Stary Rynek": ["Cytadela", "UAM", "Nadbrzeze Warty", "Ostrow Tumski", "Mleczarnia Spoldzielcza"],
    "Ostrow Tumski": ["Cytadela", "Nadbrzeze Warty", "Stary Rynek", "Mleczarnia Spoldzielcza"],
    "Cytadela": ["UAM", "Stary Rynek", "Tunele Forteczne", "Zaklady Cegielskiego", "Ostrow Tumski", "Solacz"],
    "UAM": ["Stary Rynek", "Cytadela", "Zaklady Cegielskiego", "Biblioteka Uniwersytecka", "Ogrod Botaniczny",
            "Rynek Jezycki", "Solacz"],
    "Zaklady Cegielskiego": ["Dyrekcja Zakladu", "Mleczarnia Spoldzielcza", "UAM", "Cytadela"],
    "Mleczarnia Spoldzielcza": ["Linia Rozlewnicza", "Stary Rynek", "Ostrow Tumski", "Zaklady Cegielskiego"],
    "Linia Rozlewnicza": ["Mleczarnia Spoldzielcza"], "Dyrekcja Zakladu": ["Zaklady Cegielskiego"],
    "Biblioteka Uniwersytecka": ["UAM"], "Ogrod Botaniczny": ["UAM"], "Rynek Jezycki": ["UAM"],
    "Solacz": ["UAM", "Cytadela"], "Tunele Forteczne": ["Cytadela"],
}
S3_ENEMY = {
    "agitator": dict(atk=2, hp=3, ev=3, dmg=1, hor=0, name="Agitator z Wildy", hunter=False),
    "cien": dict(atk=0, hp=1 * PLAYERS, ev=0, dmg=0, hor=2, name="Cien z Jezyc", hunter=True),   # atk/ev = X
    "goniec1": dict(atk=3, hp=2 * PLAYERS, ev=3, dmg=1, hor=1, name="Goniec (Mleczarnia)", hunter=False,
                    aloof=True, spawn="Cytadela", target="Mleczarnia Spoldzielcza"),
    "goniec2": dict(atk=3, hp=1 * PLAYERS, ev=3, dmg=1, hor=1, name="Goniec (UAM)", hunter=False,
                    aloof=True, spawn="Nadbrzeze Warty", target="UAM"),
    "goniec3": dict(atk=3, hp=3 * PLAYERS, ev=3, dmg=1, hor=1, name="Goniec (Cytadela)", hunter=False,
                    aloof=True, spawn="Cytadela", target="Cytadela", flat=2),
    "student": dict(atk=2, hp=3, ev=3, dmg=0, hor=1, name="Oblakany Student", hunter=False, aloof=True),
    "bamber": dict(atk=4, hp=3, ev=2, dmg=1, hor=0, name="Wkurwiony Bamber", hunter=False),
    "koza_karta": dict(atk=2, hp=3, ev=3, dmg=1, hor=0, name="Czarna Koza (karta z repo)", hunter=False),
    "koza": dict(atk=2, hp=3, ev=3, dmg=1, hor=0, name="Czarna Koza (boss)", hunter=False),
    # z Interludium II czesc 2 (po porazce w scen. 2)
    "nosiciel": dict(atk=3, hp=3, ev=2, dmg=1, hor=1, name="Nosiciel Zarodnikow", hunter=False),
    "hierofanta": dict(atk=4, hp=3, ev=2, dmg=1, hor=1, name="Hierofanta", hunter=False),
    "pomiot": dict(atk=3, hp=3, ev=2, dmg=1, hor=0, name="Kozi Pomiot", hunter=True),
}
# quantity z kart; karty bez pola (Kryzys, Cenzura, Tej, Dostawa) = 1
S3_DECK = {"agitator": 2, "cien": 2, "koza_karta": 2, "student": 2, "bamber": 2,
           "sadza": 2, "kryzys": 1, "cenzura": 1, "smrod": 2, "strajk": 3,
           "tej": 1, "trauma": 2, "dostawa": 1,
           # 14 kart "Artykuly Kuriera" ma grupe spotkan f = ta sama co scenariusz 3
           "kurier": 14}
KURIER = 14   # 0 = bez Kuriera w talii
S3_GONIEC_ASIDE = ["goniec1", "goniec2", "goniec3"]
S3_AGENDA = [4, 8, 12, 14]
DOOM_FLIP = 4          # tyle zaglady na lokacji odwraca ja na Spaczona
ACT1_CLUES = 3         # 3<badacz> na Akcie 1
ACT_TARGET = [None, "Zaklady Cegielskiego", "UAM", "Mleczarnia Spoldzielcza", "Tunele Forteczne", None]


# ===========================================================================
# WSPOLNY SILNIK
# ===========================================================================
class Base:
    def __init__(self, profiles, seed=None):
        self.rng = random.Random(seed)
        self.inv = []
        for p in profiles:
            i = dict(p, dmg=0, hor=0, hand=5, alive=True, clues=0,
                     health=p["health"] + p.get("allies", 0),
                     sanity=p["sanity"] + p.get("allies", 0))
            if p.get("weapons"):
                i["wil" if (p.get("faction") == "mystic" and p["wil"] >= p["com"]) else "com"] += 1
            if p.get("faction") == "seeker":
                i["int"] += 1
            self.inv.append(i)
        self.round = 0
        self.doom = 0
        self.agenda = 0
        self.act = 0
        self.enemies = []
        self.pool = 0
        self.result = None
        self.log = collections.Counter()
        self.tests = collections.defaultdict(lambda: [0, 0])
        self.events = []   # narracja: (runda, tekst)

    def note(self, txt):
        if len(self.events) < 400:
            self.events.append((self.round, txt))

    # --- podstawy ---------------------------------------------------------
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
        return inv[sk] + inv["icons"]["willpower" if sk == "wil" else "combat"]

    def best(self, skill, where=None):
        c = [i for i in self.alive() if not where or i["loc"] == where]
        if skill == "fight":
            return max(c, key=self.fight_value, default=None)
        key = {"wil": "willpower", "int": "intellect", "com": "combat", "agi": "agility"}[skill]
        return max(c, key=lambda i: i[skill] + i["icons"][key], default=None)

    def ctx(self, loc):
        return {}

    def move_to(self, inv, dest):
        """Ruch kosztuje akcje wg odleglosci. uproszczenie: dystans losowy 1-3 kroki
        (wioska i las to siatki ~3x3, wiec srednia odleglosc to ~2 akcje)."""
        if inv["loc"] == dest:
            return True
        steps = self.rng.choice([1, 2, 2, 3])
        inv["actions"] -= steps - 1
        inv["loc"] = dest
        inv["moved"] = True
        self.log["ruch (%d akcji)" % steps] += 1
        return True

    def test(self, inv, skill, difficulty, name=None, commit=True):
        base = inv[skill]
        if commit and inv["hand"] > 0 and base - difficulty < 2:
            base += round(inv["icons"][{"wil": "willpower", "int": "intellect",
                                        "com": "combat", "agi": "agility"}[skill]])
            inv["hand"] -= 1
            inv["committed"] = True
        if inv.get("phase_bonus") and not inv.get("phase_used"):
            base += inv["phase_bonus"]; inv["phase_used"] = True
        tok = self.rng.choice(CHAOS_BAG)
        v = token_value(tok, self.ctx(inv["loc"]))
        rec = self.tests[name or skill]
        rec[0] += 1
        if v is None:
            self.on_token(inv, tok)
            return False, -99
        ok = base + v >= difficulty
        rec[1] += ok
        if not ok:
            self.on_token(inv, tok)
        return ok, base + v - difficulty

    def on_token(self, inv, tok):
        pass

    def hurt(self, inv, dmg, hor, src="inne"):
        inv["dmg"] += dmg
        inv["hor"] += hor
        self.log["obrazenia: " + src] += dmg
        self.log["przerazenie: " + src] += hor
        if (inv["dmg"] >= inv["health"] or inv["hor"] >= inv["sanity"]) and inv["alive"]:
            inv["alive"] = False
            self.log["badacz pokonany"] += 1
            self.note("%s pokonany (obr %d/%d, przer %d/%d)" % (inv["investigator"], inv["dmg"],
                                                                inv["health"], inv["hor"], inv["sanity"]))
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

    def fight(self, inv, e):
        ok, _ = self.test(inv, self.fight_skill(inv), e["atk"] + self.enemy_bonus(e), name="walka")
        if ok:
            e["hp"] -= 1 + (inv["dmg_bonus"] if inv["weapons"] else 0)
            if e["hp"] <= 0:
                self.defeat(inv, e)
        return ok

    def enemy_bonus(self, e):
        return 0

    def engaged_ready(self, inv):
        return [e for e in self.enemies if e.get("engaged") is inv and not e["exhausted"]]

    def enemy_phase(self):
        for e in self.enemies:
            if e.get("hunter") and not e["exhausted"] and e.get("engaged") is None:
                target = min(self.alive(), key=lambda i: (i["loc"] != e["loc"], i["dmg"]), default=None)
                if target:
                    e["loc"] = target["loc"]
                    e["engaged"] = target
            if e.get("engaged") is None and not e.get("aloof") and self.at(e["loc"]):
                e["engaged"] = self.rng.choice(self.at(e["loc"]))
        for e in self.enemies:
            if not e["exhausted"] and e.get("engaged") and e["engaged"]["alive"]:
                self.hurt(e["engaged"], e["dmg"], e["hor"], e["name"])
                self.after_attack(e)

    def after_attack(self, e):
        pass

    def upkeep(self):
        for e in self.enemies:
            e["exhausted"] = False
        for i in self.alive():
            i["hand"] = min(8, i["hand"] + 1)
            if i.get("move_or_horror") and not i.get("moved"):
                self.hurt(i, 0, 1, "Toksyczny Gomez (bez ruchu)")
            i["moved"] = False
            if i.get("heal_on_commit") and i.get("committed"):
                if i["dmg"] > 0:
                    i["dmg"] -= 1
                elif i["hor"] > 0:
                    i["hor"] -= 1
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
        inv.setdefault("weak_round", self.rng.randint(2, 8))
        if inv.get("weakness_horror") and inv["weak_round"] == self.round and not inv.get("weak_done"):
            inv["weak_done"] = True
            self.hurt(inv, 0, inv["weakness_horror"], "wlasna slabosc")

    def add_doom(self, n=1):
        self.doom += n
        self.check_agenda()

    def check_agenda(self):
        while self.agenda < len(self.AGENDA) and self.doom_total() >= self.AGENDA[self.agenda] and not self.result:
            self.advance_agenda()

    def play(self):
        while not self.check_end():
            self.round += 1
            self.mythos()
            if self.check_end():
                break
            for i in sorted(self.alive(), key=lambda x: -self.fight_value(x)):
                i["actions"] = 3
                i["phase_used"] = False
                while i["actions"] > 0 and i["alive"] and not self.result:
                    i["actions"] -= 1
                    if i["actions"] == 0 and i.get("move_or_horror") and not i.get("moved"):
                        i["moved"] = True   # Gomez: ostatnia akcja tury na przejscie sie
                        self.log["Gomez: akcja ruchu"] += 1
                        continue
                    self.act_once(i)
                if self.check_end():
                    break
            if self.check_end():
                break
            self.enemy_phase()
            self.upkeep()
        return self.result

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


# ---------------------------------------------------------------------------
class Game1(Base):
    """Scenariusz 1: wioska -> las -> posiadlosc -> Zyrij."""
    ENEMY = S1_ENEMY
    AGENDA = S1_AGENDA

    def __init__(self, profiles, seed=None):
        Base.__init__(self, profiles, seed)
        self.clues = collections.Counter()
        self.shroud = {}
        for name, (sh, cl) in S1_VILLAGE.items():
            self.shroud[name] = sh
            self.clues[name] = cl * PLAYERS
        for name, (sh, cl) in S1_FOREST.items():
            self.shroud[name] = sh
            self.clues[name] = cl
        self.village = list(S1_VILLAGE)
        self.forest = [f for f in S1_FOREST if f != "Skraj Lasu"]
        self.revealed = {"Skraj Lasu"}
        for i in self.inv:
            i["loc"] = "Srodek wioski"
        self.deck = [k for k, n in S1_DECK_START.items() for _ in range(n)]
        self.rng.shuffle(self.deck)
        self.discard = []
        self.manor = False        # Posiadlosc w grze
        self.key = False          # Klucz do zachrystii (z oproznionego Kosciola)
        self.victory = 0          # punkty zwyciestwa: Nory, Oboz na mokradlach, Zyrij
        self.rescued = False      # "Wiesniacy zostali uratowani" (+2 PD z Fabuly)
        self.aside = {"wyznawca": 5}

    def ctx(self, loc):
        # czaszka: -X, X = liczba wrogow z cecha Humanoid w grze. token_value liczy
        # -(tissues-1), wiec podajemy tissues = humanoidy + 1 (uproszczenie: wszyscy wrogowie)
        return {"tissues": 1 + min(5, len(self.enemies))}

    def on_token(self, inv, tok):
        if tok == "cultist":   # rozstaw Przekonanego wyznawce w sasiedniej lokacji
            if self.aside["wyznawca"] > 0:
                self.aside["wyznawca"] -= 1
                self.spawn("wyznawca", inv["loc"])

    def move_to(self, inv, dest):
        """Las: do nieodkrytej lokacji nie da sie wejsc z lasu - trzeba ja odkryc za 2 wskazowki."""
        if dest in self.forest and dest not in self.revealed:
            if inv["loc"] == "Skraj Lasu" or inv["loc"] in self.village:
                self.revealed.add(dest)   # ze Skraju Lasu wchodzi sie bez ograniczen (odkrywa po wejsciu)
            elif self.pool >= REVEAL_COST:
                self.pool -= REVEAL_COST
                self.revealed.add(dest)
                self.log["las: odkrycie za wskazowki"] += 1
            else:
                return False
        return Base.move_to(self, inv, dest)

    def draw_encounter(self, inv):
        self.weakness(inv)
        if not self.deck:
            self.deck, self.discard = self.discard, []
            self.rng.shuffle(self.deck)
            self.log["talia spotkan przetasowana"] += 1
        if not self.deck:
            return
        card = self.deck.pop()
        self.log["spotkanie: " + card] += 1
        if card in ("ciekawski", "wyznawca", "kultywator", "traktorzysta", "pomiot"):
            e = self.spawn(card, inv["loc"])
            if card == "traktorzysta":
                self.hurt(inv, e["dmg"], e["hor"], "Traktorzysta (rozstawienie)")
        elif card == "wolanie":
            inv["wolanie"] = True
        elif card == "kazanie":
            ok, _ = self.test(inv, "int", 3, name="Gorliwe Kazanie int(3)")
            if not ok:
                self.log["Kazanie: strata zasobow/sojusznika"] += 1
        elif card in ("komunia", "chrzest"):
            sk = "wil" if card == "komunia" else "com"
            ok, _ = self.test(inv, sk, 3, name="Nieczysty rytual %s(3)" % sk)
            if not ok:
                self.hurt(inv, 0 if card == "komunia" else 1, 1 if card == "komunia" else 0, "Nieczysty rytual")
        elif card == "brama":
            self.log["Brama z Galezi (blokada przejscia)"] += 1
            inv["actions_penalty"] = 1
        self.discard.append(card)

    def mythos(self):
        self.add_doom(1)
        for i in list(self.alive()):
            if self.result:
                return
            self.draw_encounter(i)
            if i.get("wolanie"):
                self.hurt(i, 0, 1, "Wolanie")   # poza Miejscem Kultu; badacz zdejmuje je akcja wil(3)

    def advance_agenda(self):
        self.doom = 0
        self.agenda += 1
        self.log["tajemnica -> %d" % (self.agenda + 1)] += 1
        self.note("Tajemnica %d" % (self.agenda + 1))
        if self.agenda >= len(self.AGENDA):
            self.result = ("porazka", "zaglada (Tajemnica 4: Tryumf Kozicy)")
            return
        for kind, n in S1_SHUFFLE_IN.get(self.agenda, {}).items():
            self.deck += [kind] * n
        self.rng.shuffle(self.deck)
        # Srodek wioski: rozstaw Ciekawskiego; zamiana Ciekawskiego na Przekonanego wyznawce
        for e in list(self.enemies):
            if e["kind"] == "ciekawski" and self.aside["wyznawca"] > 0:
                self.enemies.remove(e)
                self.aside["wyznawca"] -= 1
                self.spawn("wyznawca", e["loc"])
                self.log["Ciekawski -> Wyznawca (tajemnica)"] += 1
                break

    def defeat(self, inv, e):
        self.enemies.remove(e)
        self.log["pokonany: " + e["name"]] += 1
        if e["kind"] == "pomiot":
            for i in self.at(e["loc"]):
                self.hurt(i, 0, 1, "Kozi Pomiot (pokonany)")
        if e["kind"] == "zerdz":
            self.victory += 1
            self.note("Zyrij Zerdz pokonany")
            self.result = ("wygrana", "Zyrij Zerdz pokonany")

    def hit_boss(self):
        """Kazde obrazenie zadane Zyrijowi zamienia najblizszego Ciekawskiego w Wyznawce."""
        for c in list(self.enemies):
            if c["kind"] == "ciekawski" and self.aside["wyznawca"] > 0:
                self.enemies.remove(c)
                self.aside["wyznawca"] -= 1
                self.spawn("wyznawca", c["loc"])
                self.log["Zyrij: Ciekawski -> Wyznawca"] += 1
                return

    def act_once(self, inv):
        loc = inv["loc"]
        if inv.pop("actions_penalty", 0):
            return
        eng = self.engaged_ready(inv)
        if inv.get("wolanie") and not eng:
            ok, _ = self.test(inv, "wil", 3, name="Wolanie: wil(3) aby odrzucic")
            if ok:
                inv["wolanie"] = False
            return
        if eng:
            e = eng[0]
            if e["kind"] == "ciekawski":   # Pertraktacje wil/com (3) - taniej niz walka
                ok, _ = self.test(inv, "wil" if inv["wil"] >= inv["com"] else "com", 3,
                                  name="Ciekawski: Pertraktacje (3)")
                if ok:
                    self.enemies.remove(e)
                    self.log["Ciekawski: pertraktacje"] += 1
                return
            if self.fight_value(inv) >= e["atk"] or e["hp"] <= 2:
                return self.fight(inv, e)
            ok, _ = self.test(inv, "agi", e["ev"], name="unik")
            if ok:
                e["exhausted"] = True
                e["engaged"] = None
            return
        # Akt 3: Posiadlosc i Zyrij
        if self.act >= 2:
            boss = [e for e in self.enemies if e["kind"] == "zerdz"]
            if boss:
                if loc != "Posiadlosc":
                    self.move_to(inv, "Posiadlosc")
                    return
                hit = self.fight(inv, boss[0])
                if hit and boss[0] in self.enemies:
                    self.hit_boss()
                return hit
            if loc != "Posiadlosc":
                self.move_to(inv, "Posiadlosc")
                return
            self.spawn("zerdz", "Posiadlosc")
            self.note("Posiadlosc odkryta, Zyrij Zerdz w grze (%d zdrowia)" % (3 * PLAYERS))
            self.log["Zyrij rozstawiony"] += 1
            return
        # Akt 2: znajdz Posiadlosc (Nory / Oboz ocalalych: Pertraktacje int(4))
        if self.act == 1 and not self.manor:
            if loc not in ("Nory", "Oboz ocalalych"):
                dest = "Nory" if self.rng.random() < 0.5 else "Oboz ocalalych"
                if not self.move_to(inv, dest):
                    self.explore_or_investigate(inv)
                return
            ok, _ = self.test(inv, "int", 4, name="Nory/Oboz: Pertraktacje int(4)")
            if ok:
                self.manor = True
                self.act = 2
                self.log["Posiadlosc odnaleziona"] += 1
                self.note("Posiadlosc odnaleziona (%s)" % loc)
                if loc == "Oboz ocalalych" and inv["actions"] >= 2 and not self.rescued:
                    # <act><act><act>: odprowadz ocalalych -> "Wiesniacy zostali uratowani" (+2 PD)
                    inv["actions"] -= 2
                    self.rescued = True
                    inv["loc"] = "Przybrzezna rampa"
                    self.log["wiesniacy uratowani"] += 1
                    self.note("Wiesniacy odprowadzeni do wioski (+2 PD)")
            return
        # Akt 1 -> 2: oproznij Kosciol (Klucz do zachrystii), potem Zachrystia int(3).
        # uproszczenie: karty Klucz do zachrystii nie ma w repo - model zaklada,
        # ze oprozniony Kosciol po prostu go daje.
        if self.act == 0 and inv is self.best("int"):
            if not self.key:
                if self.clues["Kosciol"] > 0:
                    if loc != "Kosciol":
                        self.move_to(inv, "Kosciol")
                        return
                    ok, _ = self.test(inv, "int", max(0, self.shroud["Kosciol"] + inv.get("shroud_mod", 0)), name="badanie Kosciola")
                    if ok:
                        self.clues["Kosciol"] -= 1
                        self.pool += 1
                    return
                self.key = True
                self.log["Klucz do zachrystii zdobyty"] += 1
                self.note("Kosciol oprozniony - Klucz do zachrystii")
                return
            if loc != "Zachrystia":
                self.move_to(inv, "Zachrystia")
                return
            ok, _ = self.test(inv, "int", 3, name="Zachrystia: int(3) -> postep aktow")
            if ok:
                self.act = 1
                self.pool = 0   # Akt 2 rewers: "Usuncie do puli zdobyte zetony wskazowek"
                self.log["Akt 1 -> 2"] += 1
                self.note("Akt 2: wskazowki wioski przepadaja, Skraj Lasu w grze")
                for i in self.alive():
                    i["loc"] = "Skraj Lasu"
                    i["actions"] -= 1
            return
        self.explore_or_investigate(inv)

    def explore_or_investigate(self, inv):
        loc = inv["loc"]
        if self.clues[loc] > 0:
            ok, _ = self.test(inv, "int", max(0, self.shroud[loc] + inv.get("shroud_mod", 0)), name="badanie")
            if ok:
                self.clues[loc] -= 1
                self.pool += 1
                if self.clues[loc] == 0 and loc in ("Nory", "Oboz na mokradlach"):
                    self.victory += 1
                    self.log["punkt zwyciestwa: " + loc] += 1
            return
        pool = self.forest if self.act >= 1 else self.village
        cand = [l for l in pool if self.clues[l] > 0 and (l in self.revealed or self.pool >= REVEAL_COST
                                                          or loc == "Skraj Lasu")]
        dest = self.rng.choice(cand) if cand else self.rng.choice(pool)
        if not self.move_to(inv, dest):
            inv["hand"] = min(8, inv["hand"] + 1)   # nie ma jak sie ruszyc: odpoczynek


# ---------------------------------------------------------------------------
class Game3(Base):
    """Scenariusz 3: 6 aktow, zaglada na lokacjach, spaczenie, Goncy."""
    ENEMY = S3_ENEMY
    AGENDA = S3_AGENDA

    def __init__(self, profiles, seed=None, extra_deck=()):
        Base.__init__(self, profiles, seed)
        self.clues = collections.Counter()
        self.locdoom = collections.Counter()
        self.corrupt = set()
        self.shroud = {}
        for name, (sh, cl, _) in S3_LOC.items():
            self.shroud[name] = sh
            self.clues[name] = (max(1, cl - S3_CLUE_CUT) if cl >= 3 else cl) * PLAYERS
        for i in self.inv:
            i["loc"] = "Nadbrzeze Warty"
        self.deck = [k for k, n in S3_DECK.items() for _ in range(KURIER if k == "kurier" else (S3_DECK_COPIES or n))
                     if k != "koza_karta" or KOZA_IN_DECK]
        self.deck += list(extra_deck)
        self.rng.shuffle(self.deck)
        self.discard = []
        self.aside = list(S3_GONIEC_ASIDE)
        self.victory = 0
        self.stall = 0
        if KOZA_STATS:
            self.ENEMY = dict(S3_ENEMY)
            self.ENEMY["koza"] = dict(atk=4, hp=10 * PLAYERS, ev=2, dmg=2, hor=2, name="Awatar Shub-Niggurath",
                                      hunter=False)

    def ctx(self, loc):
        return {"tissues": 0, "corrupt": len(self.corrupt)}

    def doom_total(self):
        return self.doom + (sum(self.locdoom.values()) if LOC_DOOM_COUNTS else 0)

    def token_mod(self, tok, loc):
        """Karta scenariusza 3 (awers): czaszka -1, kultysta/tablica -X (X = Spaczone), Starszy -1/-3."""
        if tok in ("cultist", "tablet"):
            return -len(self.corrupt)
        if tok == "skull":
            return -1
        if tok == "elder":
            return -3 if loc in self.corrupt else -1
        return None

    def test(self, inv, skill, difficulty, name=None, commit=True):
        base = inv[skill]
        if commit and inv["hand"] > 0 and base - difficulty < 2:
            base += round(inv["icons"][{"wil": "willpower", "int": "intellect",
                                        "com": "combat", "agi": "agility"}[skill]])
            inv["hand"] -= 1
            inv["committed"] = True
        if inv.get("phase_bonus") and not inv.get("phase_used"):
            base += inv["phase_bonus"]; inv["phase_used"] = True
        tok = self.rng.choice(CHAOS_BAG)
        v = tok if isinstance(tok, int) else self.token_mod(tok, inv["loc"])
        rec = self.tests[name or skill]
        rec[0] += 1
        if tok == "fail":
            return False, -99
        ok = base + v >= difficulty
        rec[1] += ok
        return ok, base + v - difficulty

    def add_locdoom(self, loc, n=1):
        self.locdoom[loc] += n
        if self.locdoom[loc] >= DOOM_FLIP and loc not in self.corrupt and S3_LOC[loc][2]:
            self.corrupt.add(loc)
            if loc not in ("Biblioteka Uniwersytecka", "Dyrekcja Zakladu", "Linia Rozlewnicza"):
                self.locdoom[loc] += self.clues[loc]   # rewers: wskazowki zamieniaja sie w zaglade
                self.clues[loc] = 0
            self.log["lokacja spaczona"] += 1
            self.note("%s spaczona (%d zaglady)" % (loc, self.locdoom[loc]))
            if len(self.corrupt) >= 3 and "Stary Rynek" not in self.corrupt:
                self.corrupt.add("Stary Rynek")
                self.locdoom["Stary Rynek"] += self.clues["Stary Rynek"]
                self.clues["Stary Rynek"] = 0
                self.log["lokacja spaczona"] += 1
                self.note("Stary Rynek spaczony (3+ Spaczonych) - bez akcji odzyskania")
        self.check_agenda()

    def spawn_goniec(self, kind):
        e = self.spawn(kind, self.ENEMY[kind]["spawn"])
        e["hp"] = self.ENEMY[kind]["hp"]
        return e

    def draw_encounter(self, inv):
        self.weakness(inv)
        if not self.deck:
            self.deck, self.discard = self.discard, []
            self.rng.shuffle(self.deck)
            self.log["talia spotkan przetasowana"] += 1
        card = self.deck.pop()
        loc = inv["loc"]
        self.log["spotkanie: " + card] += 1
        if card.startswith("goniec"):
            self.spawn_goniec(card)
        elif card == "cien":
            tgt = max(S3_LOC, key=lambda l: self.locdoom[l])
            self.spawn("cien", tgt)
        elif card in self.ENEMY:
            self.spawn(card, loc)
        elif card == "sadza":
            ok, _ = self.test(inv, "agi", 2, name="Czarna Sadza agi(2)")
            if not ok:
                self.hurt(inv, 1, 0, "Czarna Sadza")
                inv["actions_penalty"] = 1
        elif card == "kryzys":
            self.test(inv, "wil", 4, name="Kryzys Aprowizacyjny wil(4)")
        elif card == "smrod":
            diff = 5 if loc in ("Mleczarnia Spoldzielcza", "Linia Rozlewnicza") else 3
            ok, _ = self.test(inv, "wil", diff, name="Smrod z Garbar wil(%d)" % diff)
            if not ok:
                self.hurt(inv, 0, 1, "Smrod z Garbar")
                inv["no_investigate"] = True
        elif card == "trauma":
            self.hurt(inv, 0, 1, "Trauma Pruskiego Drylu")   # uproszczenie: badacz zwykle bada, nie rusza sie / nie walczy
        elif card in ("strajk", "tej"):
            inv["blocked"] = True
        elif card == "dostawa":
            # uproszczenie: 2 zasoby albo zaglada na lokacji - pol na pol
            if self.rng.random() < 0.5:
                self.add_locdoom(loc)
            else:
                self.log["Dostawa: oplacona zasobami"] += 1
        elif card == "cenzura":
            self.log["Cenzura: strata przedmiotu"] += 1
        elif card == "kurier":
            # uproszczenie: artykuly Kuriera to glownie lagodne, jednorundowe efekty z opcja testu:
            # 60% nic, 20% 1 przerazenie (nieudany test 3), 20% -1 zaglada z tajemnicy (udany test)
            r = self.rng.random()
            if r < 0.2:
                self.hurt(inv, 0, 1, "Kurier (nieudany test)")
            elif r < 0.4 and self.doom > 0:
                self.doom -= 1
                self.log["Kurier: -1 zaglada"] += 1
        self.discard.append(card)

    def mythos(self):
        self.add_doom(1)
        for i in list(self.alive()):
            if self.result:
                return
            self.draw_encounter(i)
        # Goniec: patroluje 1 lokacje/runde i zrzuca zaglade rowna pozostalemu zdrowiu (Goniec 3: 2)
        for e in list(self.enemies):
            if e["kind"].startswith("goniec") and not e["exhausted"]:
                if e["loc"] != e["target"]:
                    path = self.path(e["loc"], e["target"])
                    e["loc"] = path[0] if path else e["target"]
                    e["engaged"] = None
                else:
                    n = e.get("flat") or e["hp"]
                    self.add_locdoom(e["target"], n)
                    self.enemies.remove(e)
                    self.discard.append(e["kind"])
                    self.log["Goniec zrzucil zaglade"] += 1
                    self.note("%s dotarl do celu: +%d zaglady na %s" % (e["name"], n, e["target"]))
        for e in self.enemies:
            if e["kind"] == "student" and e.get("engaged"):
                self.add_doom(1)

    def path(self, a, b):
        """BFS po S3_ADJ. Zwraca liste krokow (bez a)."""
        prev = {a: None}
        q = collections.deque([a])
        while q:
            x = q.popleft()
            if x == b:
                break
            for y in S3_ADJ.get(x, []):
                if y not in prev:
                    prev[y] = x
                    q.append(y)
        if b not in prev:
            return []
        out = []
        while b != a:
            out.append(b)
            b = prev[b]
        return out[::-1]

    def after_attack(self, e):
        if e["kind"] == "bamber":
            self.add_doom(1)

    def enemy_bonus(self, e):
        b = 1 if e["loc"] in self.corrupt and e["kind"] == "agitator" else 0
        if e["kind"] == "cien":
            b += len(self.corrupt)   # X
        return b

    def advance_agenda(self):
        self.doom = 0   # zaglada z lokacji ZOSTAJE (tekst tajemnic 1-3)
        self.agenda += 1
        self.log["tajemnica -> %d" % (self.agenda + 1)] += 1
        if self.agenda >= len(self.AGENDA):
            self.note("Tajemnica 4 dobiegla konca (zaglada na lokacjach: %d)" % sum(self.locdoom.values()))
            self.result = ("porazka", "zaglada (Tajemnica 4: Miasto pod presja)")
            return
        self.note("Tajemnica %d (zaglada na lokacjach: %d)" % (self.agenda + 1, sum(self.locdoom.values())))
        n = 1 if self.agenda == 1 else 2
        if self.agenda >= 2:   # 1<badacz> przerazenia za kazda Spaczona, dla grupy
            per = len(self.corrupt) * PLAYERS
            for k in range(per):
                alive = self.alive()
                if not alive:
                    break
                self.hurt(alive[k % len(alive)], 0, 1, "tajemnica (Spaczone)")
        for _ in range(n):
            if self.aside:
                self.spawn_goniec(self.aside.pop(self.rng.randrange(len(self.aside))))

    def defeat(self, inv, e):
        self.enemies.remove(e)
        self.log["pokonany: " + e["name"]] += 1
        if e["kind"] == "koza":
            self.note("Czarna Koza pokonana")
            self.result = ("wygrana", "Czarna Koza pokonana")

    def recover(self, inv, loc):
        """Odzyskanie spaczonej lokacji wg jej rewersu."""
        r = S3_RECOVER.get(loc)
        if r is None:
            return False
        skill, diff, how = r
        if how == 1 and loc in ("Biblioteka Uniwersytecka", "Dyrekcja Zakladu", "Linia Rozlewnicza"):
            # rewers: zbadaj wszystkie wskazowki, potem 1 akcja odwraca (zaglada zostaje)
            if self.clues[loc] > 0:
                ok, _ = self.test(inv, "int", self.shroud[loc], name="badanie")
                if ok:
                    self.clues[loc] -= 1; self.pool += 1
                return True
            self.corrupt.discard(loc)
            self.log["lokacja odzyskana"] += 1
            return True
        ok, m = self.test(inv, skill, diff, name="odzyskaj %s %s(%d)" % (loc, skill, diff))
        if ok:
            got = max(1, m) if how == "margin" else 1
            self.locdoom[loc] = max(0, self.locdoom[loc] - got)
            self.clues[loc] += got
            if self.locdoom[loc] == 0:
                self.corrupt.discard(loc)
                self.log["lokacja odzyskana"] += 1
                self.note("%s odzyskana" % loc)
        return True

    def act_once(self, inv):
        loc = inv["loc"]
        if inv.pop("actions_penalty", 0):
            return
        eng = self.engaged_ready(inv)
        if eng:
            e = eng[0]
            if self.fight_value(inv) >= e["atk"] + self.enemy_bonus(e) or e["hp"] <= 2:
                return self.fight(inv, e)
            ok, _ = self.test(inv, "agi", e["ev"] + self.enemy_bonus(e), name="unik")
            if ok:
                e["exhausted"] = True
                e["engaged"] = None
            return
        # Goniec w drodze: najlepszy wojownik go przechwytuje (Powsciagliwy: zwarcie kosztuje akcje)
        gon = [e for e in self.enemies if e["kind"].startswith("goniec") and e["loc"] != e["target"]]
        if gon and inv is self.best("fight") and self.act < 5:
            g = gon[0]
            if loc != g["loc"]:
                self.move_to(inv, g["loc"])
                return
            if g.get("engaged") is not inv:
                g["engaged"] = inv
                return
            return self.fight(inv, g)
        if self.act >= 5:   # Akt 6: Czarna Koza
            boss = [e for e in self.enemies if e["kind"] == "koza"]
            if not boss:
                self.spawn("koza", "Ostrow Tumski")["exhausted"] = True
                self.note("Akt 6: Czarna Koza na Ostrowie Tumskim")
                return
            if loc != "Ostrow Tumski":
                self.move_to(inv, "Ostrow Tumski")
                return
            return self.fight(inv, boss[0])
        if self.act == 0:   # Akt 1: 3<badacz> wskazowek
            if self.pool >= ACT1_CLUES * PLAYERS:
                self.pool -= ACT1_CLUES * PLAYERS
                self.act = 1
                worst = max(S3_LOC, key=lambda l: self.locdoom[l])
                if self.locdoom[worst]:
                    self.locdoom[worst] -= 1; self.clues[worst] += 1
                self.log["Akt 1 -> 2"] += 1
                self.note("Akt 2 (wskazowki: %d)" % self.pool)
                return
        else:
            tgt = ACT_TARGET[self.act]
            need_doom = self.act in (2, 3)   # Akt 3 i 4: "wskazowki i zetony spaczenia"; Akt 2 i 5: same wskazowki
            if tgt and self.clues[tgt] == 0 and (self.locdoom[tgt] == 0 or not need_doom):
                self.act += 1
                self.stall = 0
                self.log["Akt %d -> %d" % (self.act, self.act + 1)] += 1
                self.note("Akt %d" % (self.act + 1))
                if self.act == 2:
                    for i in self.alive():
                        if self.clues[i["loc"]] > 0:
                            self.clues[i["loc"]] -= 1; self.pool += 1
                if self.act == 5:
                    worst = max(S3_LOC, key=lambda l: self.locdoom[l])
                    self.locdoom[worst] = max(0, self.locdoom[worst] - 2)
                    self.log["Dalbor dolacza"] += 1
                return
        tgt = ACT_TARGET[self.act]
        if tgt is None:
            tgt = loc if self.clues[loc] > 0 else None
        if tgt in self.corrupt:
            if loc != tgt:
                self.move_to(inv, tgt)
                return
            self.stall += 1
            if S3_RECOVER.get(tgt) is None or self.stall > 60:
                self.result = ("porazka", "zakleszczenie: cel aktu (%s) spaczony bez wyjscia" % tgt)
                return
            self.recover(inv, tgt)
            return
        if inv.pop("no_investigate", False) or inv.pop("blocked", False):
            return
        need_doom = self.act in (2, 3)
        if tgt and tgt != loc and (self.clues[tgt] > 0 or (need_doom and self.locdoom[tgt] > 0)):
            self.move_to(inv, tgt)
            return
        if tgt and loc == tgt and need_doom and self.locdoom[loc] > 0 and self.clues[loc] == 0:
            # niespaczona zaglada na celu aktu: Rynek Jezycki (odrzuc karte) / Solacz (2 zasoby) zdejmuja
            # po 1 zetonie z wybranej lokacji. uproszczenie: 1 akcja + 1 karta z reki = -1 zaglada
            if inv["hand"] > 0:
                inv["hand"] -= 1
            self.locdoom[loc] -= 1
            self.log["zaglada zdjeta (Rynek/Solacz)"] += 1
            return
        if self.clues[loc] > 0 and not (loc == "Ostrow Tumski" and self.corrupt - {"Ostrow Tumski"}):
            sh = self.shroud[loc]
            if loc == "Mleczarnia Spoldzielcza":
                sh += 2 * len(self.at(loc))   # "+2 zaslony za kazdego badacza w tej lokacji"
            ok, _ = self.test(inv, "int", max(0, sh + inv.get("shroud_mod", 0)), name="badanie")
            if ok:
                self.clues[loc] -= 1
                self.pool += 1
                self.stall = 0
            return
        cand = [l for l in S3_LOC if self.clues[l] > 0 and l not in self.corrupt and l != "Tunele Forteczne"]
        if cand:
            self.move_to(inv, self.rng.choice(cand))
        elif self.corrupt - {"Stary Rynek"}:
            c = self.rng.choice(sorted(self.corrupt - {"Stary Rynek"}))
            if loc != c:
                self.move_to(inv, c)
            else:
                self.recover(inv, c)
        else:
            inv["hand"] = min(8, inv["hand"] + 1)


# ===========================================================================
# TRYBY
# ===========================================================================
def cmd_tempo(which, profiles):
    sk = {"wil": "willpower", "int": "intellect", "com": "combat", "agi": "agility"}
    val = lambda p, k: p[k] + round(p["icons"][sk[k]])
    if which == "1":
        clue_total = sum(c * PLAYERS for _, c in S1_VILLAGE.values())
        print("# TEMPO scenariusz 1 (4 graczy, worek Standard)")
        print("Wioska: %d lokacji, %d wskazowek (zaslona '?' -> 2); Las: %d lokacji, %d wskazowek"
              % (len(S1_VILLAGE), clue_total, len(S1_FOREST), sum(c for _, c in S1_FOREST.values())))
        print("Zegar: %s = %d zaglady; 1/runde z Mitow -> %d rund do konca"
              % (" + ".join(map(str, S1_AGENDA)), sum(S1_AGENDA), sum(S1_AGENDA)))
        n = sum(S1_DECK_START.values())
        print("Talia startowa: %d kart (Ciekawski x5, Kultywator x2, Wolanie) -> przy 4 graczach "
              "wyczerpuje sie po %.0f rundach; reszta dochodzi z tajemnic." % (n, n / PLAYERS))
        print("Zyrij Zerdz: %d zdrowia, walka 3, 0 obrazen / 1 przerazenie za atak." % (3 * PLAYERS))
        for p in profiles:
            print("  %-17s badanie zaslona2: %3.0f%%  Pertraktacje int(4): %3.0f%%  walka(3): %3.0f%%"
                  % (p["investigator"], 100 * p_success(val(p, "int"), 2),
                     100 * p_success(val(p, "int"), 4), 100 * p_success(val(p, "com"), 3)))
    else:
        clue_total = sum(c * PLAYERS for _, c, _ in S3_LOC.values())
        print("# TEMPO scenariusz 3 (4 graczy, worek Standard)")
        print("Lokacje: %d, wskazowek na stole: %d; Akt 1 wymaga %d, Tunele Forteczne %d (zaslona 4)"
              % (len(S3_LOC), clue_total, ACT1_CLUES * PLAYERS, 3 * PLAYERS))
        print("Zegar: %s = %d zaglady; 6 aktow do przejscia" % (" + ".join(map(str, S3_AGENDA)), sum(S3_AGENDA)))
        print("Goncy (odlozeni na bok, wchodza z tajemnic): Mleczarnia +%d, UAM +%d, Cytadela +2 za kazde dojscie"
              % (2 * PLAYERS, PLAYERS))
        print("Prog spaczenia: %d zaglady. Zaglada z lokacji liczy sie do tajemnicy: %s"
              % (DOOM_FLIP, "TAK (zasady)" if LOC_DOOM_COUNTS else "nie (czytanie intencyjne)"))
        for p in profiles:
            print("  %-17s badanie zaslona4: %3.0f%%  Mleczarnia we 4 (zaslona 10): %3.0f%%  odzyskanie wil(3): %3.0f%%"
                  % (p["investigator"], 100 * p_success(val(p, "int"), 4),
                     100 * p_success(val(p, "int"), 10), 100 * p_success(val(p, "wil"), 3)))


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
            tests[k][0] += n
            tests[k][1] += s
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
    for k, v in logs.most_common(22):
        print("  %-40s %.2f" % (k, v / games))


def selftest():
    global LOC_DOOM_COUNTS
    prof = [dict(investigator="X%d" % i, faction="guardian", wil=20, int=20, com=20, agi=20,
                 health=99, sanity=99, weapons=1, dmg_bonus=9, heal_cards=0, cards=30, allies=0,
                 icons={"willpower": 0, "intellect": 0, "combat": 0, "agility": 0})
            for i in range(4)]
    w1 = sum(Game1(prof, seed=s).play()[0] == "wygrana" for s in range(30))
    assert w1 >= 25, "silni badacze powinni wygrywac scen 1: %d/30" % w1
    old = LOC_DOOM_COUNTS
    LOC_DOOM_COUNTS = 0
    w3 = sum(Game3(prof, seed=s).play()[0] == "wygrana" for s in range(30))
    LOC_DOOM_COUNTS = old
    assert w3 >= 20, "silni badacze powinni wygrywac scen 3 (intencyjnie): %d/30" % w3
    weak = [dict(p, wil=0, int=0, com=0, agi=0, health=3, sanity=3, dmg_bonus=0) for p in prof]
    l1 = sum(Game1(weak, seed=s).play()[0] == "porazka" for s in range(30))
    assert l1 >= 28, "slabi badacze powinni przegrywac: %d/30" % l1
    assert Game1(prof, seed=5).deck == Game1(prof, seed=5).deck, "seed deterministyczny"
    g = Game3(prof, seed=1)
    assert g.path("Cytadela", "Mleczarnia Spoldzielcza") == ["Stary Rynek", "Mleczarnia Spoldzielcza"]
    assert g.path("Nadbrzeze Warty", "UAM") == ["Stary Rynek", "UAM"]
    print("selftest OK")


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a or a[0] in ("-h", "--help"):
        print(__doc__)
    elif a[0] == "--selftest":
        selftest()
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
