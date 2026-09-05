#!/usr/bin/env python3
"""Model scenariusza 2 "Nurt Szalenstwa": tempo, Monte Carlo, stol dla agenta.

Uzycie:
  python tools/scenario2_model.py tempo                         # analiza bez losowosci
  python tools/scenario2_model.py sim --games 2000 --variant A|B [--kara] [--seed N]
  python tools/scenario2_model.py table --seed N                # nowy stol (tasowanie)
  python tools/scenario2_model.py table draw encounter|tissue|chaos | state | set k=v
  python tools/scenario2_model.py --selftest

To NIE jest silnik zasad AH LCG. Karty gracza to profile liczbowe z tools/arkhamdb.py,
efekty kart spotkan sa skrocone do liczb, a polityka graczy to prosta lista
priorytetow. Kazde uproszczenie jest oznaczone komentarzem "# uproszczenie:".
Dane scenariusza przepisane recznie z kart w repo (stan: wrzesien 2026).
"""
import sys, os, io, json, random, argparse, statistics, collections

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(ROOT, ".cache")
PROFILES = os.path.join(CACHE, "arkhamdb", "profiles.json")

# ============================================================================
# DANE SCENARIUSZA (z kart)
# ============================================================================
# Worek chaosu: repo nie definiuje skladu -> Standard z instrukcji podstawki.
# uproszczenie: Starszy Znak = +1 dla kazdego badacza.
CHAOS_BAG = [1, 0, 0, -1, -1, -1, -2, -2, "skull", "skull", "cultist", "tablet", "fail", "elder"]

# Glowny nurt w kolejnosci; bariera[i] blokuje wplyniecie do RIVER[i].
RIVER = ["Stara Przystan", "Zakole Warty", "Legi Wierzbowe", "Skazony Nurt",
         "Rozlewiska Debiny", "Most Chwaliszewski"]
SHROUD = {"Stara Przystan": 2, "Zakole Warty": 3, "Legi Wierzbowe": 2, "Skazony Nurt": 4,
          "Rozlewiska Debiny": 4, "Most Chwaliszewski": 4,
          "Dworzec Puszczykowo": 3, "Pradawne Deby": 3, "Fabryka Drozdzy": 3, "Zrujnowany Fort": 5}
CLUES_PER_INV = {"Stara Przystan": 1, "Zakole Warty": 1, "Legi Wierzbowe": 1, "Skazony Nurt": 0,
                 "Rozlewiska Debiny": 0, "Most Chwaliszewski": 0, "Dworzec Puszczykowo": 1,
                 "Pradawne Deby": 1, "Fabryka Drozdzy": 1, "Zrujnowany Fort": 2}
# uproszczenie: karty nie mowia, ktore Pobrzeze lezy przy ktorym wezle rzeki
# ("zgodnie z mapa powiazan" - mapy nie ma w repo). Przypisanie tak, by przedmiot
# na bariere byl osiagalny PRZED ta bariera.
SHORE = {"Stara Przystan": "Dworzec Puszczykowo", "Zakole Warty": "Pradawne Deby",
         "Skazony Nurt": "Fabryka Drozdzy", "Rozlewiska Debiny": "Zrujnowany Fort"}
BARRIERS = {
    # blokuje wejscie do:      (nazwa, przedmiot omijajacy, droga alternatywna)
    "Legi Wierzbowe": ("Zyjacy Zator", "totem", "4 wskazowki w Zakolu (bariera zostaje w grze)"),
    "Rozlewiska Debiny": ("Toksyczny Kozuch", "ferment", "test grupowy com(10), kazdy 1 obrazenie"),
    "Most Chwaliszewski": ("Pruskie Miny", "dynamit", "test agi(4), porazka = 3 uszkodzenia barki"),
}
AGENDA = [6, 8, 10]          # progi zaglady; 2. przechodzi dalej tylko przy >=4 uszkodzeniach barki
BARGE_HP = 10
KOZUCH_DIFF = 5   # karta 4 IX: test jednego badacza com(5), kazdy inny w lokacji deklaruje 1 karte
MINY_DMG = 2
POMIOT_HORROR = 0   # 1 = stara wersja: kazdy badacz 1 przerazenia po pokonaniu
PLAYERS = 4

# Talia spotkan: plik -> skrot. Liczba kopii z pola `quantity` karty; karty scenariusza 2
# NIE MAJA tego pola (stan 5 IX 2026), wiec domyslnie DECK_COPIES kopii kazdej.
DECK_COPIES = 2
ENCOUNTER_FILES = {
    "Dar Czarnej Kozy": "dar", "Gwałtowny Rozkwit": "rozkwit", "Hierofanta Tysiąca Pędów": "hierofanta",
    "Kozi Pomiot": "pomiot", "Niekontrolowany Rozrost": "rozrost", "Nosiciel Zarodników": "nosiciel",
    "Rytuał Płodności": "rytual", "Rzeczne Młode": "mlode", "Twarze w Korze": "twarze",
    "Zapach Feromonów": "feromony", "Żywy Nurt": "nurt",
}


def qty_from_repo():
    out = {}
    d = os.path.join(ROOT, "Karty Spotkań", "scenariusz 2")
    for name, kind in ENCOUNTER_FILES.items():
        q = None
        p = os.path.join(d, name + ".card")
        if os.path.exists(p):
            try:
                q = int(json.loads(io.open(p, encoding="utf-8").read()).get("quantity") or 0) or None
            except (ValueError, TypeError):
                pass
        out[kind] = q
    return out


QTY = qty_from_repo()


def deck_from_repo():
    return [k for k, q in QTY.items() for _ in range(q or DECK_COPIES)]


ENCOUNTERS = deck_from_repo()

# Pokretla (domyslnie = tak, jak stoi na kartach w repo):
PRESSURE_NEED = PLAYERS + 1   # Most B: "1<per>+1 znacznikow Cisnienia" (pakiet 5 IX 2026)
LEWIATAN_RETURNS = 1          # karta: wraca do lokacji barki na koniec nastepnej rundy
LEWIATAN_EVADE = 0            # karta: "Lewiatana nie mozna Unikac"; 1 = stara luka (Masywny, unik 1)
LEWIATAN_HP_MULT = 2          # zdrowie 2<badacz>
PUSH_PRESSURE = 2             # odepchniecie Lewiatana = 2 znaczniki Cisnienia
LEWIATAN_BARGE = 1            # obrazenia barki za atak Lewiatana (karta po dopiskach: 1)
PRESSURE_FAIL_DMG = 0         # nieudane "Cala naprzod!" = brak efektu (karta po dopiskach)
RETURN_EXHAUSTED = 0          # 1 = Lewiatan wraca wyczerpany (jeszcze jedna runda spokoju)
LEWIATAN_AOE = 0              # karta po dopiskach: atakuje sterujacego; 1 = kazdego badacza w lokacji
# Wrogowie: (walka=trudnosc testu com, zdrowie, unik, obrazenia, przerazenie, lowca)
ENEMY = {
    "pomiot": dict(atk=3, hp=3, ev=2, dmg=1, hor=0, hunter=True, name="Kozi Pomiot"),
    "hierofanta": dict(atk=4, hp=3, ev=2, dmg=1, hor=1, hunter=False, name="Hierofanta"),
    "nosiciel": dict(atk=3, hp=3, ev=2, dmg=1, hor=1, hunter=False, name="Nosiciel Zarodnikow"),
    "mlode": dict(atk=3, hp=4, ev=1, dmg=1, hor=1, hunter=False, name="Rzeczne Mlode"),
    "kierownik": dict(atk=4, hp=6, ev=2, dmg=2, hor=1, hunter=False, name="Zmutowany Kierownik"),
    "arcykaplan": dict(atk=3, hp=3 * PLAYERS, ev=3, dmg=2, hor=1, hunter=False, name="Arcykaplan"),
    "lewiatan": dict(atk=5, hp=3 * PLAYERS, ev=1, dmg=2, hor=2, hunter=False, name="Lewiatan"),
}
ENEMY["lewiatan"]["hp"] = 3 * PLAYERS   # nadpisywane w Game.__init__ przez LEWIATAN_HP_MULT
# Tkanki: (umiejetnosc do usuniecia, trudnosc, efekt-skrot)
TISSUES = {
    "gabczasta": ("int", 3, "+1 trudnosc testow w lokacji"),
    "kokon": ("com", 3, "przy postepie tajemnicy rozstawia wroga"),
    "korzenie": ("res", 2, "1 obrazenie przy opuszczaniu lokacji"),
    "pnacza": ("com", 3, "+1 akcja za ruch"),
    "splot": ("agi", 4, "1 przerazenie przy porazce o 2+"),
    "oczy": ("wil", 3, "+2 zaslona, odrzuc karte na koniec tury"),
    "blona": ("com", 3, "brak zagrywania kart"),
    "grzybnia": ("int", 4, "1 obrazenie kazdemu na koniec rundy"),
}


# ============================================================================
# WOREK I TESTY
# ============================================================================
def token_value(tok, ctx):
    """Modyfikator zetonu w kontekscie (tkanki w lokacji, boss w grze). None = autoporazka."""
    if isinstance(tok, int):
        return tok
    t = ctx.get("tissues", 0)
    if tok == "skull":
        return -max(0, t - 1)        # uproszczenie: X<0 traktowane jako 0
    if tok == "cultist":
        return -2
    if tok == "tablet":
        return -3
    if tok == "elder":
        return 1
    return None                      # 'fail'


def p_success(skill, difficulty, ctx=None):
    """Analityczne P(sukces): skill + zeton >= trudnosc."""
    ctx = ctx or {}
    ok = 0
    for tok in CHAOS_BAG:
        v = token_value(tok, ctx)
        if v is None:
            continue
        total = skill + v
        if total > difficulty or (total == difficulty and not (ctx.get("boss") and tok == "elder")):
            ok += 1
    return ok / len(CHAOS_BAG)


class Game:
    """Jedna rozgrywka Monte Carlo."""

    def __init__(self, profiles, variant="A", kara=False, seed=None):
        self.rng = random.Random(seed)
        self.variant = variant
        self.kara = kara
        # uproszczenie: sojusznicy = dodatkowe pola zdrowia/poczytalnosci; mistyk z zaklaciami walczy wola
        self.inv = [dict(p, dmg=0, hor=0, hand=5, alive=True, loc=RIVER[0], exhausted_ally=False,
                         health=p["health"] + p.get("allies", 0), sanity=p["sanity"] + p.get("allies", 0))
                    for p in profiles]
        for i in self.inv:
            if i.get("weapons"):
                i["wil" if (i.get("faction") == "mystic" and i["wil"] >= i["com"]) else "com"] += 1
        self.barge_idx = 0
        self.barge_hp = BARGE_HP
        self.barge_moved = False
        self.doom = 0
        self.agenda = 0
        self.agenda2_mod = 0           # +1 trudnosc testow na barce po "resecie" Tajemnicy 2
        self.round = 0
        self.items = set()             # totem / ferment / dynamit
        self.barriers_left = set(BARRIERS)   # klucz = lokacja, ktora blokuje
        self.barrier_method = {}
        self.clues = collections.Counter()     # wskazowki lezace w lokacjach
        for loc, per in CLUES_PER_INV.items():
            self.clues[loc] = per * PLAYERS
        self.pool_clues = 0            # wskazowki zebrane przez grupe
        self.tissues = collections.defaultdict(list)   # lokacja -> [tkanka]
        self.enemies = []              # dict(kind, hp, loc, exhausted, engaged=idx|None)
        self.deck = deck_from_repo(); self.rng.shuffle(self.deck)
        self.discard = []
        self.tissue_deck = list(TISSUES); self.rng.shuffle(self.tissue_deck)
        self.pressure = 0
        self.boss = None
        self.victory = 0
        self.kierownik_done = False
        ENEMY["lewiatan"]["hp"] = LEWIATAN_HP_MULT * PLAYERS
        self.result = None
        self.log = collections.Counter()
        self.tests = collections.defaultdict(lambda: [0, 0])   # nazwa -> [proby, sukcesy]

    # --- pomocnicze ---------------------------------------------------------
    @property
    def barge_loc(self):
        return RIVER[self.barge_idx]

    def alive(self):
        return [i for i in self.inv if i["alive"]]

    def at(self, loc):
        return [i for i in self.alive() if i["loc"] == loc]

    def ctx(self, loc):
        return {"tissues": len(self.tissues.get(loc, [])), "boss": self.boss is not None}

    def draw_token(self):
        return self.rng.choice(CHAOS_BAG)

    def test(self, inv, skill, difficulty, loc=None, name=None, commit=True):
        """Test umiejetnosci: statystyka + (ewentualnie 1 karta z reki) + zeton."""
        loc = loc or inv["loc"]
        base = inv[skill]
        if commit and inv["hand"] > 0:   # uproszczenie: 1 karta z reki o srednich ikonach
            base += round(inv["icons"][{"wil": "willpower", "int": "intellect",
                                        "com": "combat", "agi": "agility"}[skill]])
            inv["hand"] -= 1
            inv["committed"] = True
        if inv.get("phase_bonus") and not inv.get("phase_used"):
            base += inv["phase_bonus"]; inv["phase_used"] = True
        difficulty += len([t for t in self.tissues[loc] if t == "gabczasta"])
        if loc == "Skazony Nurt" and self.tissues[loc]:
            difficulty += 1
        tok = self.draw_token()
        v = token_value(tok, self.ctx(loc))
        rec = self.tests[name or skill]
        rec[0] += 1
        if v is None:
            self.on_fail(inv, tok, loc, difficulty - base)
            return False, -99
        total = base + v
        ok = total > difficulty or (total == difficulty and not (self.boss and tok == "elder"))
        if ok:
            rec[1] += 1
        else:
            self.on_fail(inv, tok, loc, difficulty - total)
        return ok, total - difficulty

    def on_fail(self, inv, tok, loc, margin):
        if tok == "cultist" and len(self.tissues[loc]) < 2:
            self.attach_tissue(loc)
        if tok == "tablet":
            self.hurt(inv, 1, 0, "zeton tablicy")
        if any(t == "splot" for t in self.tissues[loc]) and margin >= 2:
            self.hurt(inv, 0, 1, "Nerwowy Splot")

    def hurt(self, inv, dmg, hor, src="inne"):
        inv["dmg"] += dmg
        inv["hor"] += hor
        self.log["obrazenia: " + src] += dmg
        self.log["przerazenie: " + src] += hor
        if inv["dmg"] >= inv["health"] or inv["hor"] >= inv["sanity"]:
            if inv["alive"]:
                inv["alive"] = False
                self.log["badacz pokonany"] += 1
                for e in self.enemies:
                    if e["engaged"] is inv:
                        e["engaged"] = None

    def attach_tissue(self, loc):
        if not self.tissue_deck:
            return
        self.tissues[loc].append(self.tissue_deck.pop())
        self.log["tkanki dolaczone"] += 1

    def spawn(self, kind, loc=None, engaged=None):
        e = dict(ENEMY[kind], kind=kind, loc=loc or self.barge_loc, exhausted=False, engaged=engaged)
        if engaged is None and self.at(e["loc"]):
            e["engaged"] = self.rng.choice(self.at(e["loc"]))
        self.enemies.append(e)
        self.log["wrog: " + e["name"]] += 1
        return e

    def add_doom(self, n=1):
        self.doom += n
        if self.doom >= AGENDA[self.agenda]:
            self.advance_agenda()

    def advance_agenda(self):
        self.doom = 0
        if self.agenda == 0:
            self.barge_hp -= 1
            # uproszczenie: "Topielec z Warty" nie istnieje w repo - pomijamy rozstawienie
            self.log["tajemnica 1 -> 2"] += 1
            self.agenda = 1
        elif self.agenda == 1:
            for i in self.alive():
                ok, _ = self.test(i, "agi", 3, name="Tajemnica 2: agi(3)")
                if not ok:
                    self.hurt(i, 1, 1, "Tajemnica 2")
            if BARGE_HP - self.barge_hp >= 4:
                self.agenda = 2
                self.log["tajemnica 2 -> 3"] += 1
            else:
                # uproszczenie: karta zostaje z progiem 8 i modyfikatorem +1; kolejne
                # osiagniecie progu znow sprawdza uszkodzenia barki
                self.agenda2_mod = 1
                self.log["tajemnica 2: reset zaglady"] += 1
        else:
            self.result = ("porazka", "zaglada (Tajemnica 3)")

    # --- faza Mitow ----------------------------------------------------------
    def draw_encounter(self, inv):
        if not self.deck:
            self.deck, self.discard = self.discard, []
            self.rng.shuffle(self.deck)
            self.log["talia spotkan przetasowana"] += 1
            if self.boss and self.boss["kind"] == "arcykaplan":
                self.boss["hp"] = min(ENEMY["arcykaplan"]["hp"], self.boss["hp"] + 3)
        card = self.deck.pop()
        loc = inv["loc"]
        self.log["spotkanie: " + card] += 1
        if card == "dar":
            ok, _ = self.test(inv, "wil", 4, name="Dar Czarnej Kozy wil(4)")
            if not ok:
                self.attach_tissue(self.barge_loc)
                self.add_doom(1)   # uproszczenie: zaglada na tkance liczy sie jak na tajemnicy
        elif card == "rozkwit":
            self.add_doom(1)
            if self.tissues[loc]:
                ok, _ = self.test(inv, "agi", 3, name="Gwaltowny Rozkwit agi(3)")
                if not ok:
                    self.hurt(inv, 1, 0, "Gwaltowny Rozkwit")
        elif card == "hierofanta":
            self.spawn("hierofanta", loc)
        elif card == "pomiot":
            self.spawn("pomiot", loc)
        elif card == "rozrost":
            self.attach_tissue(loc)
            ok, _ = self.test(inv, "agi", 3, name="Niekontrolowany Rozrost agi(3)")
            if not ok:
                self.hurt(inv, 1, 0, "Niekontrolowany Rozrost")
                inv["lost_action"] = True
        elif card == "nosiciel":
            tl = [l for l in self.tissues if self.tissues[l]]
            self.spawn("nosiciel", tl[0] if tl else loc)
        elif card == "rytual":
            self.spawn("nosiciel", loc, engaged=inv)   # uproszczenie: gracz wybiera wroga, nie 3 tkanki
        elif card == "mlode":
            tl = [l for l in self.tissues if self.tissues[l]]
            self.spawn("mlode", tl[0] if tl else self.barge_loc)
        elif card == "twarze":
            diff = 3 + len(self.tissues[loc])
            ok, margin = self.test(inv, "wil", diff, name="Twarze w Korze wil(3+)")
            if not ok:
                self.hurt(inv, 0, max(1, -margin if margin > -50 else 3), "Twarze w Korze")
        elif card == "feromony":
            ok, _ = self.test(inv, "wil", 3, name="Zapach Feromonow wil(3)")
            if not ok and self.enemies:
                self.hurt(inv, 1, 0, "Zapach Feromonow")   # uproszczenie: doskok wrogow = 1 obrazenie
        elif card == "nurt":
            if self.tissues[loc]:
                self.hurt(inv, 2, 0, "Zywy Nurt")
            else:
                self.attach_tissue(loc)
        self.discard.append(card)

    def mythos(self):
        self.add_doom(1)
        for e in self.enemies:
            if e["kind"] == "hierofanta":
                self.add_doom(1)
        for i in list(self.alive()):
            if self.result:
                return
            i["phase_used"] = False
            if i.get("weakness_horror") and i.get("weak_round", self.rng.randint(2, 8)) == self.round and not i.get("weak_done"):
                i["weak_done"] = True
                self.hurt(i, 0, i["weakness_horror"], "wlasna slabosc")
            i.setdefault("weak_round", self.rng.randint(2, 8))
            self.draw_encounter(i)

    # --- faza badaczy: polityka ---------------------------------------------
    def best(self, skill, where=None):
        cands = [i for i in self.alive() if not where or i["loc"] == where]
        return max(cands, key=lambda i: i[skill] + i["icons"][
            {"wil": "willpower", "int": "intellect", "com": "combat", "agi": "agility"}[skill]],
                   default=None)

    def fight_skill(self, inv):
        # mistyk z zaklaciami walczy wola, chyba ze walka jest lepsza (Michal: com 4, wil 2)
        if inv.get("faction") == "mystic" and inv.get("weapons") and inv["wil"] >= inv["com"]:
            return "wil"
        return "com"

    def fight_p(self, inv, enemy):
        sk = self.fight_skill(inv)
        return p_success(inv[sk] + round(inv["icons"]["willpower" if sk == "wil" else "combat"]),
                         enemy["atk"] + self.enemy_bonus(enemy), self.ctx(inv["loc"]))

    def evade_p(self, inv, enemy):
        return p_success(inv["agi"] + round(inv["icons"]["agility"]), enemy["ev"], self.ctx(inv["loc"]))

    def fight(self, inv, enemy):
        ok, _ = self.test(inv, self.fight_skill(inv), enemy["atk"] + self.enemy_bonus(enemy), name="walka")
        if ok:
            enemy["hp"] -= 1 + (inv["dmg_bonus"] if inv["weapons"] else 0)
            if enemy["hp"] <= 0:
                self.defeat(enemy)
        elif enemy["kind"] == "pomiot":
            self.hurt(inv, enemy["dmg"], enemy["hor"], "Kozi Pomiot (Msciwy)")   # Msciwy

    def enemy_bonus(self, enemy):
        b = 0
        if enemy["kind"] == "arcykaplan":
            b += len(self.barriers_left)
        if enemy["kind"] == "mlode" and self.tissues[enemy["loc"]]:
            b += 1
        return b

    def defeat(self, enemy):
        if enemy["kind"] == "lewiatan":
            enemy["hp"] = ENEMY["lewiatan"]["hp"]
            enemy["exhausted"] = True
            enemy["loc"] = RIVER[0]
            enemy["engaged"] = None
            enemy["away"] = 0
            self.pressure += PUSH_PRESSURE
            self.log["Lewiatan odepchniety"] += 1
            return
        self.enemies.remove(enemy)
        self.log["pokonany: " + enemy["name"]] += 1
        if enemy["kind"] == "pomiot" and POMIOT_HORROR:
            for i in self.at(enemy["loc"]):
                self.hurt(i, 0, 1, "Kozi Pomiot (pokonany)")
        if enemy["kind"] == "nosiciel" and not self.tissues[enemy["loc"]]:
            self.attach_tissue(enemy["loc"])
        if enemy["kind"] == "kierownik":
            self.kierownik_done = True
            self.items.add("ferment")
            self.log["przedmiot: ferment"] += 1
        if enemy["kind"] == "arcykaplan":
            self.result = ("wygrana", "Arcykaplan pokonany")

    def engaged_ready(self, inv):
        return [e for e in self.enemies if e["engaged"] is inv and not e["exhausted"]]

    def next_barrier(self):
        if self.barge_idx + 1 < len(RIVER):
            nxt = RIVER[self.barge_idx + 1]
            if nxt in self.barriers_left:
                return nxt
        return None

    def move_barge(self, inv):
        """Ruch barki o jeden wezel (test com/agi 3), jesli nic nie blokuje."""
        nxt = RIVER[self.barge_idx + 1]
        skill = "com" if inv["com"] + inv["icons"]["combat"] >= inv["agi"] + inv["icons"]["agility"] else "agi"
        diff = 3 + self.agenda2_mod
        if self.barge_loc == "Zakole Warty" and self.tissues["Zakole Warty"]:
            inv["actions"] -= 1
        ok, _ = self.test(inv, skill, diff, name="ruch barki %s(3)" % skill)
        if ok:
            crew = self.at(self.barge_loc)
            if any(t == "korzenie" for t in self.tissues[self.barge_loc]):
                for i in crew:
                    self.hurt(i, 1, 0, "Krwawe Korzenie")
            self.barge_idx += 1
            self.barge_moved = True
            for i in crew:
                i["loc"] = nxt; i["moved"] = True
            self.log["ruch barki"] += 1
            if nxt == "Most Chwaliszewski":
                if self.variant == "A":
                    self.boss = self.spawn("arcykaplan", nxt)
                else:
                    self.boss = self.spawn("lewiatan", nxt)
                    self.boss["exhausted"] = True
                    self.boss["engaged"] = None
            if nxt == "Rozlewiska Debiny":
                inv["actions"] -= 1   # +1 akcja za wplyniecie
        return ok

    def try_barrier(self, inv, nxt):
        """Omija bariere przedmiotem albo droga alternatywna. Zwraca True, gdy barka przeszla."""
        name, item, _ = BARRIERS[nxt]
        crew = self.at(self.barge_loc)
        if item in self.items:
            self.items.discard(item)
            if item == "ferment":
                pass   # wyczerpuje Fermenta i placi 1 zasob - uproszczenie: zawsze stac
            self.barriers_left.discard(nxt)
            self.barrier_method[nxt] = "przedmiot"
            self.victory += 1   # karta Bariery: Zwyciestwo 1, tylko gdy uzyto przedmiotu
            self.log["bariera %s: przedmiot" % name] += 1
            self._pass(nxt, crew)
            return True
        if nxt == "Legi Wierzbowe":
            if self.pool_clues >= 4:
                self.pool_clues -= 4
                self.barrier_method[nxt] = "4 wskazowki"
                self.log["bariera %s: 4 wskazowki" % name] += 1
                # uproszczenie: bariera zostaje w grze (liczy sie Arcykaplanowi) - barriers_left bez zmian
                self._pass(nxt, crew)
                return True
            return False
        if nxt == "Rozlewiska Debiny":
            # karta: najlepszy wojownik testuje com(5), kazdy inny w lokacji deklaruje 1 karte (srednie ikony)
            best = self.best("com", self.barge_loc) or inv
            group = best["com"] + sum(round(i["icons"]["combat"]) for i in crew if i is not best and i["hand"])
            if p_success(group, KOZUCH_DIFF) < 0.45 and not self.ferment_gone():
                return False   # czekaj na Fermenta
            for i in crew:
                if i is not best and i["hand"]:
                    i["hand"] -= 1
            inv = best
            ok, _ = self.test(inv, "com", KOZUCH_DIFF - (group - inv["com"]), name="Kozuch: com(%d)+karty" % KOZUCH_DIFF)
            for i in crew:
                self.hurt(i, 1, 0, "Kozuch (test grupowy)")
            if ok:
                self.barrier_method[nxt] = "test grupowy"
                self._pass(nxt, crew)
            return ok
        if nxt == "Most Chwaliszewski":
            ok, _ = self.test(inv, "agi", 4, name="Miny: agi(4)")
            if ok:
                self.barrier_method[nxt] = "test agi"
                self._pass(nxt, crew)
            else:
                self.barge_hp -= MINY_DMG
                self.log["obrazenia barki: Miny"] += MINY_DMG
            return ok
        return False

    def _pass(self, nxt, crew):
        self.barge_idx += 1
        self.barge_moved = True
        for i in crew:
            i["loc"] = nxt; i["moved"] = True
        if nxt == "Most Chwaliszewski":
            if self.variant == "A":
                self.boss = self.spawn("arcykaplan", nxt)
            else:
                self.boss = self.spawn("lewiatan", nxt)
                self.boss["exhausted"] = True
                self.boss["engaged"] = None

    def ferment_gone(self):
        """Fermenta juz nie da sie zdobyc (Kierownik pokonany, przedmiot zuzyty/nieobecny)."""
        return self.kierownik_done and "ferment" not in self.items

    def fetch_item_plan(self):
        """Ktory przedmiot warto zdobyc dla NASTEPNEJ bariery i gdzie."""
        nxt = self.next_barrier()
        if not nxt:
            return None
        item = BARRIERS[nxt][1]
        if item in self.items:
            return None
        if nxt == "Legi Wierzbowe":
            # Deby po zmianie: 4 wskazowki przy zaslonie 3 = ten sam koszt co Zakole, ale Totem zdejmuje
            # bariere (Arcykaplan bez +1, 1 PD). Polityka: idz po Totem, gdy barka stoi w Zakolu.
            return ("Pradawne Deby", "totem") if self.barge_loc == "Zakole Warty" else None
        if nxt == "Rozlewiska Debiny":
            if self.barge_loc == "Skazony Nurt" and not self.kierownik_done:
                return ("Fabryka Drozdzy", "kierownik")
            return None
        if nxt == "Most Chwaliszewski":
            if max(i["agi"] for i in self.alive()) >= 5:
                return None   # test agi(4) wystarczy
            return ("Zrujnowany Fort", "dynamit") if self.barge_loc == "Rozlewiska Debiny" else None

    def investigator_turn(self, inv):
        inv["phase_used"] = False
        inv["actions"] = 3 - (1 if inv.pop("lost_action", False) else 0)
        if self.kara and self.round == 1:
            inv["actions"] -= 1
        while inv["actions"] > 0 and inv["alive"] and not self.result:
            inv["actions"] -= 1
            if inv["actions"] == 0 and inv.get("move_or_horror") and not inv.get("moved"):
                inv["moved"] = True   # Gomez: ostatnia akcja tury na przejscie sie (1 akcja < 1 przerazenie)
                self.log["Gomez: akcja ruchu"] += 1
                continue
            self.act(inv)

    def act(self, inv):
        loc = inv["loc"]
        # 1. wrog w zwarciu
        eng = self.engaged_ready(inv)
        if eng:
            e = eng[0]
            if e["kind"] == "lewiatan" and self.variant == "B":
                pass
            elif (self.fight_p(inv, e) >= self.evade_p(inv, e) - 0.15 or e["hp"] <= 1 + inv["dmg_bonus"]
                  or (e.get("hunter") and self.fight_p(inv, e) >= 0.4)):
                return self.fight(inv, e)   # unik lowcy nic nie daje - wraca w fazie wrogow
            else:
                ok, _ = self.test(inv, "agi", e["ev"], name="unik")
                if ok:
                    e["exhausted"] = True; e["engaged"] = None
                return
        # 2. Most: cel wariantu
        if loc == "Most Chwaliszewski" and self.boss:
            if self.variant == "A":
                return self.fight(inv, self.boss)
            lev = self.boss
            if self.pressure >= PRESSURE_NEED and lev["exhausted"]:
                self.result = ("wygrana", "Rezygnacja z cisnieniem (Most zniszczony)")
                return
            if not lev["exhausted"] and lev["loc"] == self.barge_loc:
                # Masywny = w zwarciu z kazdym badaczem w lokacji, wiec Unik (1) go wyczerpuje
                if LEWIATAN_EVADE and inv is self.best("agi", loc):
                    ok, _ = self.test(inv, "agi", lev["ev"], name="unik Lewiatana agi(1)")
                    if ok:
                        lev["exhausted"] = True
                        self.log["Lewiatan uniknięty"] += 1
                    return
                if inv is self.best("com", loc):
                    return self.fight(inv, lev)
            skill = "wil" if inv["wil"] >= inv["com"] else "com"
            ok, margin = self.test(inv, skill, 4, name="Cala naprzod %s(4)" % skill)
            if ok:
                self.pressure += 2 if margin >= 3 else 1
            else:
                self.barge_hp -= PRESSURE_FAIL_DMG
                self.log["obrazenia barki: Cala naprzod"] += PRESSURE_FAIL_DMG
            return
        # 3. tkanka w lokacji barki
        if loc == self.barge_loc and self.tissues[loc]:
            t = self.tissues[loc][0]
            skill, diff, _ = TISSUES[t]
            if skill == "res":
                self.tissues[loc].pop(0); self.log["tkanka usunieta"] += 1
                return
            b = self.best(skill, loc)
            if b is inv:
                ok, _ = self.test(inv, skill, diff, name="usun tkanke %s(%d)" % (skill, diff))
                if ok:
                    self.tissues[loc].pop(0); self.log["tkanka usunieta"] += 1
                return
        # 4. przedmiot na nastepna bariere
        plan = self.fetch_item_plan()
        if plan:
            shore, task = plan
            if loc == self.barge_loc:
                if inv is self.best("int" if task == "totem" else "com"):
                    inv["loc"] = shore; inv["moved"] = True; self.log["wyprawa na pobrzeze"] += 1
                    if task == "kierownik" and not any(e["kind"] == "kierownik" for e in self.enemies):
                        self.spawn("kierownik", shore, engaged=inv)
                    return
            elif loc == shore:
                if task == "totem":
                    if self.clues["Pradawne Deby"] > 0:
                        ok, _ = self.test(inv, "int", SHROUD["Pradawne Deby"], name="Deby: badanie int(3)")
                        if ok:
                            self.clues["Pradawne Deby"] -= 1
                        return
                    self.items.add("totem"); self.log["przedmiot: totem"] += 1
                    inv["loc"] = self.barge_loc
                    return
                if task == "dynamit":
                    ok, _ = self.test(inv, "com", 3, name="Fort: com(3)")
                    if ok:
                        self.items.add("dynamit"); self.log["przedmiot: dynamit"] += 1
                        inv["loc"] = self.barge_loc
                    return
                if task == "kierownik":
                    k = [e for e in self.enemies if e["kind"] == "kierownik"]
                    if k:
                        return self.fight(inv, k[0])
                    inv["loc"] = self.barge_loc
                    return
        if loc != self.barge_loc:
            inv["loc"] = self.barge_loc; inv["moved"] = True   # wracaj na barke
            return
        # 5. ruch barki (raz na runde) - jesli droga wolna albo bariera do przejscia
        if not self.barge_moved and self.barge_idx + 1 < len(RIVER):
            nxt = RIVER[self.barge_idx + 1]
            if nxt in self.barriers_left:
                if nxt == "Legi Wierzbowe" and self.pool_clues < 4:
                    pass   # zbieraj wskazowki nizej
                elif inv is self.best("agi" if nxt == "Most Chwaliszewski" else "com", loc) \
                        or BARRIERS[nxt][1] in self.items:
                    if self.try_barrier(inv, nxt):
                        self.barge_moved = True
                        return
                    if nxt == "Rozlewiska Debiny" and not self.ferment_gone():
                        pass   # czekamy na Fermenta - badacz robi cos innego
                    else:
                        return
            else:
                if inv is self.best("com") or inv is self.best("agi"):
                    self.move_barge(inv)
                    return
        # 6. wskazowki
        if self.clues[loc] > 0:
            shroud = max(0, SHROUD[loc] + (2 if "oczy" in self.tissues[loc] else 0) + inv.get("shroud_mod", 0))
            ok, _ = self.test(inv, "int", shroud, name="badanie")
            if ok:
                self.clues[loc] -= 1; self.pool_clues += 1
            return
        # 7. odpoczynek
        inv["hand"] = min(8, inv["hand"] + 1)

    # --- faza wrogow i utrzymanie -------------------------------------------
    def enemy_phase(self):
        for e in self.enemies:
            if e["hunter"] and e["loc"] != self.barge_loc and not e["exhausted"]:
                e["loc"] = self.barge_loc; e["engaged"] = None
            if e["engaged"] is None and self.at(e["loc"]) and e["kind"] not in ("lewiatan",):
                e["engaged"] = self.rng.choice(self.at(e["loc"]))
        for e in list(self.enemies):
            if e["exhausted"]:
                continue
            if e["kind"] == "lewiatan":
                if e["loc"] != self.barge_loc:
                    continue   # odepchniety - nie ma czego atakowac
                crew = self.at(e["loc"])
                for i in (crew if LEWIATAN_AOE else crew[:0] + ([self.rng.choice(crew)] if crew else [])):
                    self.hurt(i, e["dmg"], e["hor"], "Lewiatan")
                self.barge_hp -= LEWIATAN_BARGE
                self.log["obrazenia barki: Lewiatan"] += LEWIATAN_BARGE
                continue
            if e["kind"] == "arcykaplan" and e["loc"] == self.barge_loc:
                self.barge_hp -= 2
                self.log["obrazenia barki: Arcykaplan"] += 2
                continue
            if e["engaged"] and e["engaged"]["alive"]:
                self.hurt(e["engaged"], e["dmg"], e["hor"], e["name"])
        if self.barge_loc == "Skazony Nurt":
            for i in self.alive():
                if i["loc"] != self.barge_loc:
                    self.hurt(i, 1, 0, "Skazony Nurt")

    def upkeep(self):
        for e in self.enemies:
            if e["kind"] == "lewiatan" and e["loc"] != self.barge_loc:
                e["away"] = e.get("away", 0) + 1
                if LEWIATAN_RETURNS and e["away"] >= LEWIATAN_RETURNS:
                    e["loc"] = self.barge_loc
                    self.log["Lewiatan wrocil"] += 1
                    if RETURN_EXHAUSTED:
                        continue
                else:
                    continue   # odepchniety Lewiatan zostaje wyczerpany (karta nic nie mowi o powrocie)
            e["exhausted"] = False
        self.barge_moved = False
        if not self.at(self.barge_loc):
            self.barge_hp -= 1
        if self.tissues["Legi Wierzbowe"] and self.barge_loc == "Legi Wierzbowe":
            self.barge_hp -= 1
        for loc, ts in self.tissues.items():
            if "grzybnia" in ts:
                for i in self.at(loc):
                    self.hurt(i, 1, 0, "Zraca Grzybnia")
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
            if i["loc"] == "Pradawne Deby":
                ok, _ = self.test(i, "wil", 3, name="Deby: wil(3)")
                if not ok:
                    self.hurt(i, 0, 1, "Pradawne Deby")
            # uproszczenie: leczenie = 1 pkt/runde z prawdopodobienstwem udzialu kart leczacych
            if i["heal_cards"] and self.rng.random() < i["heal_cards"] / i["cards"]:
                if i["dmg"] > 0:
                    i["dmg"] -= 1
                elif i["hor"] > 0:
                    i["hor"] -= 1

    def check_end(self):
        if self.result:
            return True
        if self.barge_hp <= 0:
            self.result = ("porazka", "barka zatopiona"); return True
        if not self.alive():
            self.result = ("porazka", "wszyscy badacze pokonani"); return True
        if self.round >= 60:
            self.result = ("porazka", "limit 60 rund"); return True
        return False

    def play(self):
        while not self.check_end():
            self.round += 1
            self.mythos()
            if self.check_end():
                break
            order = sorted(self.alive(), key=lambda i: -i["com"])
            for i in order:
                self.investigator_turn(i)
                if self.check_end():
                    break
            if self.check_end():
                break
            self.enemy_phase()
            self.upkeep()
        return self.result


# ============================================================================
# TRYBY
# ============================================================================
def load_profiles():
    """ARKHAM_PROFILES=custom -> profiles_custom.json (wlasni badacze z Karty Badaczy/)."""
    path = PROFILES
    if os.environ.get("ARKHAM_PROFILES") == "custom":
        path = os.path.join(CACHE, "arkhamdb", "profiles_custom.json")
    return json.loads(io.open(path, encoding="utf-8").read())


def cmd_tempo(profiles):
    print("# TEMPO - analiza bez losowosci (worek Standard, +1 karta z reki)")
    print("badacz            ruch com3/agi3  Zakole int3  Kozuch(grupa)  Miny agi4  Fort com4  Kierownik com4  Cisnienie wil4/com4")
    sk = {"wil": "willpower", "int": "intellect", "com": "combat", "agi": "agility"}
    def s(p, k):
        return p[k] + round(p["icons"][sk[k]])
    for p in profiles:
        move = max(p_success(s(p, "com"), 3), p_success(s(p, "agi"), 3))
        print("%-17s %5.0f%%          %4.0f%%        -           %4.0f%%      %4.0f%%      %4.0f%%          %4.0f%%"
              % (p["investigator"], 100 * move, 100 * p_success(s(p, "int"), 3),
                 100 * p_success(s(p, "agi"), 4), 100 * p_success(s(p, "com"), 4),
                 100 * p_success(s(p, "com"), 4),
                 100 * max(p_success(s(p, "wil"), 4), p_success(s(p, "com"), 4))))
    group = sum(s(p, "com") for p in profiles)
    print("\nKozuch: test grupowy com(10) przy sumie com grupy = %d -> %.0f%% (uproszczenie: suma statystyk)"
          % (group, 100 * p_success(group, 10)))
    best_move = max(max(p_success(s(p, "com"), 3), p_success(s(p, "agi"), 3)) for p in profiles)
    rounds_move = 5 / best_move
    extra = 3 * 2 / 26 * PLAYERS   # Gwaltowny Rozkwit + Dar: ~ile zaglady/runde z 4 kart
    print("Ruchow barki do Mostu: 5, barka wyczerpuje sie po ruchu -> min 5 rund; "
          "przy P=%.0f%% ~%.1f rund samego plyniecia." % (100 * best_move, rounds_move))
    print("Zegar: 6 + 8 (+reset) + 10 zaglady; Mitow rocznie 1 + ~%.2f z kart -> ~%d rund do Tajemnicy 3 "
          "bez Hierofanty." % (extra, int(24 / (1 + extra))))
    print("Wniosek wstepny: czas nie jest waskim gardlem, bariery i Most sa. Sprawdz sim.")


def cmd_sim(profiles, games, variant, kara, seed):
    rng = random.Random(seed)
    results = collections.Counter()
    rounds = []
    logs = collections.Counter()
    tests = collections.defaultdict(lambda: [0, 0])
    methods = collections.Counter()
    dmg = hor = 0
    for _ in range(games):
        g = Game(profiles, variant, kara, seed=rng.random())
        res = g.play()
        results[res] += 1
        rounds.append(g.round)
        logs.update(g.log)
        for k, (n, s) in g.tests.items():
            tests[k][0] += n; tests[k][1] += s
        for k, v in g.barrier_method.items():
            methods[(BARRIERS[k][0], v)] += 1
        dmg += sum(i["dmg"] for i in g.inv) / PLAYERS
        hor += sum(i["hor"] for i in g.inv) / PLAYERS
    wins = sum(v for (r, _), v in results.items() if r == "wygrana")
    out = {
        "variant": variant, "games": games, "kara": kara,
        "win_rate": wins / games,
        "rounds_median": statistics.median(rounds),
        "results": {"%s: %s" % k: v for k, v in results.most_common()},
        "tests": {k: {"n": n, "success": round(s / n, 2) if n else None} for k, (n, s) in sorted(tests.items())},
        "barriers": {"%s -> %s" % k: v for k, v in methods.most_common()},
        "avg_damage_per_inv": round(dmg / games, 2), "avg_horror_per_inv": round(hor / games, 2),
        "events_per_game": {k: round(v / games, 2) for k, v in logs.most_common(30)},
    }
    os.makedirs(CACHE, exist_ok=True)
    path = os.path.join(CACHE, "sim_scenariusz2_%s.json" % variant)
    io.open(path, "w", encoding="utf-8").write(json.dumps(out, ensure_ascii=False, indent=1))
    print("# SIM wariant %s, %d gier%s" % (variant, games, ", kara z dziennika" if kara else ""))
    print("wygrane: %.1f%%   mediana rund: %s   obrazenia/badacz: %.1f   przerazenie/badacz: %.1f"
          % (100 * out["win_rate"], out["rounds_median"], out["avg_damage_per_inv"], out["avg_horror_per_inv"]))
    for k, v in out["results"].items():
        print("  %-52s %5.1f%%" % (k, 100 * v / games))
    print("bariery:")
    for k, v in out["barriers"].items():
        print("  %-52s %5.1f%%" % (k, 100 * v / games))
    print("testy (n, sukces):")
    for k, v in out["tests"].items():
        print("  %-40s n=%-6d %s" % (k, v["n"], "%.0f%%" % (100 * v["success"]) if v["success"] is not None else "-"))
    print("zdarzenia/gre:")
    for k, v in out["events_per_game"].items():
        print("  %-40s %.2f" % (k, v))
    print("zapisano:", path)
    return out


def cmd_table(args):
    """Stol dla agenta: seedowane tasowania i kolejka zetonow, stan w JSON."""
    path = os.path.join(CACHE, "table_scenariusz2.json")
    if args and args[0] == "--seed":
        rng = random.Random(int(args[1]))
        deck = list(ENCOUNTERS); rng.shuffle(deck)
        tissue = list(TISSUES); rng.shuffle(tissue)
        chaos = [rng.choice(CHAOS_BAG) for _ in range(400)]
        state = {"seed": int(args[1]), "encounter_deck": deck, "encounter_discard": [],
                 "tissue_deck": tissue, "chaos_queue": chaos, "round": 0, "doom": 0, "agenda": 1,
                 "act": 1, "barge_loc": RIVER[0], "barge_damage": 0, "notes": {}}
        os.makedirs(CACHE, exist_ok=True)
        io.open(path, "w", encoding="utf-8").write(json.dumps(state, ensure_ascii=False, indent=1))
        print("nowy stol, seed %s. Talia spotkan: %d kart, tkanek: %d. Nastepnie: table draw ..."
              % (args[1], len(deck), len(tissue)))
        return
    state = json.loads(io.open(path, encoding="utf-8").read())
    if not args or args[0] == "state":
        show = dict(state); show["encounter_deck"] = "%d kart" % len(state["encounter_deck"])
        show["chaos_queue"] = "%d zetonow w kolejce" % len(state["chaos_queue"])
        show["tissue_deck"] = "%d kart" % len(state["tissue_deck"])
        print(json.dumps(show, ensure_ascii=False, indent=1))
    elif args[0] == "draw":
        what = args[1]
        if what == "encounter":
            if not state["encounter_deck"]:
                state["encounter_deck"] = state["encounter_discard"]; state["encounter_discard"] = []
                random.Random(state["seed"] + state["round"]).shuffle(state["encounter_deck"])
                print("(talia spotkan przetasowana ze stosu odrzuconych)")
            c = state["encounter_deck"].pop(); state["encounter_discard"].append(c)
            print("spotkanie:", c)
        elif what == "tissue":
            print("tkanka:", state["tissue_deck"].pop() if state["tissue_deck"] else "BRAK - talia pusta")
        elif what == "chaos":
            tok = state["chaos_queue"].pop(0)
            print("zeton:", tok)
        io.open(path, "w", encoding="utf-8").write(json.dumps(state, ensure_ascii=False, indent=1))
    elif args[0] == "set":
        for kv in args[1:]:
            k, v = kv.split("=", 1)
            try:
                v = json.loads(v)
            except ValueError:
                pass
            if k in state:
                state[k] = v
            else:
                state["notes"][k] = v
        io.open(path, "w", encoding="utf-8").write(json.dumps(state, ensure_ascii=False, indent=1))
        print("ok")
    else:
        sys.exit("table: state | draw encounter|tissue|chaos | set k=v | --seed N")


def selftest():
    assert abs(p_success(3, 3) - 6 / 14) < 1e-9, p_success(3, 3)   # +1,0,0,czaszka x2,Starszy = 6 z 14
    assert p_success(0, 10) == 0.0 and p_success(20, 1) == 13 / 14
    assert p_success(3, 3, {"tissues": 3}) < p_success(3, 3)
    strong = [dict(investigator="X%d" % i, wil=20, int=20, com=20, agi=20, health=99, sanity=99,
                   icons={"willpower": 0, "intellect": 0, "combat": 0, "agility": 0},
                   weapons=1, dmg_bonus=5, heal_cards=0, cards=30) for i in range(4)]
    wins = sum(Game(strong, "A", seed=s).play()[0] == "wygrana" for s in range(40))
    assert wins >= 36, "silni badacze powinni wygrywac: %d/40" % wins
    weak = [dict(p, wil=0, int=0, com=0, agi=0, health=3, sanity=3, dmg_bonus=0) for p in strong]
    losses = sum(Game(weak, "B", seed=s).play()[0] == "porazka" for s in range(40))
    assert losses >= 38, "slabi badacze powinni przegrywac: %d/40" % losses
    g1, g2 = Game(strong, "A", seed=5), Game(strong, "A", seed=5)
    assert g1.deck == g2.deck, "seed deterministyczny"
    print("selftest OK")


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a or a[0] in ("-h", "--help"):
        print(__doc__)
    elif a[0] == "--selftest":
        selftest()
    elif a[0] == "tempo":
        cmd_tempo(load_profiles())
    elif a[0] == "sim":
        ap = argparse.ArgumentParser()
        ap.add_argument("--games", type=int, default=1000)
        ap.add_argument("--variant", default="A")
        ap.add_argument("--kara", action="store_true")
        ap.add_argument("--seed", type=int, default=1)
        ap.add_argument("--tweak", default="", help="np. LEWIATAN_EVADE=0,PRESSURE_NEED=4")
        o = ap.parse_args(a[1:])
        for kv in filter(None, o.tweak.split(",")):
            k, v = kv.split("=")
            globals()[k] = int(v)
            print("# tweak:", k, "=", v)
        cmd_sim(load_profiles(), o.games, o.variant, o.kara, o.seed)
    elif a[0] == "table":
        cmd_table(a[1:])
    else:
        sys.exit("nieznany tryb: %s" % a[0])
