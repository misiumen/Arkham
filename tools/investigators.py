#!/usr/bin/env python3
"""Zdolnosci czworki badaczy i ich kart sygnaturowych - wg tekstu kart w Karty Badaczy/ (stan 5 IX 2026).

Kazda regula ma cytat z karty. Hooki wolane z modeli (scenario13_model.Base, scenario2_model.Game):
  setup(game, inv)            - stan poczatkowy (Taca, Halabarda, Gomez, Znikanie, Paprykarz w grze)
  start_turn(game, inv)       - Paprykarz (+akcja za 1 zasob), Taca (dobranie zasobow + klatwa)
  test_mod(game, inv, skill, base, diff)  -> modyfikator (Michal +X; Wieczne Dylematy)
  draw_token(game, inv)       -> zeton z worka gry (klatwy/blogoslawienstwa sa usuwane po wyciagnieciu)
  token_value_extra(game, inv, tok) -> wartosc dla 'elder'/'curse'/'bless' (Starszy Znak per badacz)
  after_test(game, inv, ok, margin)       - Wojciech (sukces o 1-2), Szyszka (po odrzuceniu karty)
  halabarda(game, inv, enemy)  -> (mod walki, +obrazenia, dodatkowe akcje) lub None
  avoid_attack(game, inv, enemy) -> True gdy Znikanie Bez Sladu uniknelo ataku (badacz przesuniety)
  end_of_turn(game, inv)      - Dawny Wspolnik (zasoby za karty na rece)
  upkeep(game, inv)           - Taca zamiast zasobu, Gomez (przerazenie bez Ruchu/Badania), Banh Mi
  weakness(game, inv)         - dobranie slabosci sygnaturowej w losowej rundzie 2-8
  shroud_mod(game, inv)       - Baruch: -1 zaslony, gdy w worku nie ma klatw
  free_action(game, inv)      -> True gdy badacz zuzyl akcje na Pertraktacje z Dawnym Wspolnikiem
Nie modelowane (brak kart w repo): "1 losowe podstawowe oslabienie" kazdego badacza.
"""
import random

CURSE, BLESS = "curse", "bless"     # zasady AH LCG: klatwa -2, blogoslawienstwo +2, zeton usuwany po wyciagnieciu

BARUCH, MICHAL, SZYSZKA, WOJCIECH = "Baruch Hałabała", "Michał z Bargłowa", "Szyszka Nowiczok", "Wojciech Robak"


def who(inv):
    return inv.get("investigator")


def setup(game, inv):
    n = who(inv)
    inv["weak_round"] = game.rng.randint(2, 8)
    inv["weak_done"] = False
    if n == BARUCH:
        inv["taca"] = 0            # "Rozpoczynasz gre z Taca Ofiarna w grze"
        inv["halabarda"] = False   # koszt 3 - zagrywana w 1. turze, gdy stac
    if n == MICHAL:
        inv["gomez"] = True        # "Rozpoczynasz gre z Toksycznym Gomezem w grze"; "-1 do agi"
        inv["agi"] -= 1
    if n == SZYSZKA:
        inv["znikanie"] = False    # Znikanie Bez Sladu, koszt 3 - zagrywane w 1. turze, gdy stac
        inv["znikanie_ready"] = True
        inv["wspolnik"] = False
    if n == WOJCIECH:
        inv["paprykarz"] = 0       # koszt 3, "Zuzywalny (3 zasoby)" - zagrywany w 1. turze
        inv["dylematy"] = 0


def start_turn(game, inv):
    n = who(inv)
    if n == BARUCH:
        if not inv["halabarda"] and inv["res"] >= 3:
            inv["res"] -= 3; inv["halabarda"] = True
            game.bag[:] = [BLESS if t == CURSE else t for t in game.bag]   # "Gdy Halabarda wchodzi do gry, zamien klatwy na blogoslawienstwa"
        # Taca: "Dobierz do 3 zasobow z Tacy Ofiarnej i dodaj 1 klatwe do worka" (szybka akcja)
        if inv["res"] <= 1 and inv["taca"] >= 2:
            take = min(3, inv["taca"]); inv["taca"] -= take; inv["res"] += take
            game.bag.append(CURSE); game.log["Taca: zasoby + klatwa"] += 1
    if n == SZYSZKA and not inv["znikanie"] and inv["res"] >= 3:
        inv["res"] -= 3; inv["znikanie"] = True
    if n == WOJCIECH:
        if not inv["paprykarz"] and inv["res"] >= 3 and not inv.get("paprykarz_played"):
            inv["res"] -= 3; inv["paprykarz"] = 3; inv["paprykarz_played"] = True
        if inv["paprykarz"] > 0 and inv["res"] >= 2:   # "Wydaj 1 zasob, wykonaj dodatkowa akcje"
            inv["res"] -= 1; inv["paprykarz"] -= 1; inv["actions"] += 1; game.log["Paprykarz: +1 akcja"] += 1


def test_mod(game, inv, skill, base, difficulty):
    n = who(inv)
    mod = 0
    if n == MICHAL and not inv.get("phase_used"):   # "+X, X = karty w obszarze zagrozen (limit raz na faze)"
        x = (1 if inv.get("gomez") else 0)
        if x:
            mod += x; inv["phase_used"] = True
    if n == WOJCIECH and inv.get("dylematy", 0) > 0:   # Wieczne Dylematy: usun zeton; 1 przerazenie LUB wynik -1
        inv["dylematy"] -= 1
        if base + mod - difficulty >= 2:
            mod -= 1
        else:
            game.hurt(inv, 0, 1, "Wieczne Dylematy")
        if inv["dylematy"] == 0:
            game.log["Wieczne Dylematy odrzucone"] += 1
    return mod


def draw_token(game, inv):
    tok = game.rng.choice(game.bag)
    if tok in (CURSE, BLESS):
        game.bag.remove(tok)
    return tok


def token_value_extra(game, inv, tok):
    """Wartosc zetonow zaleznych od badacza. None = nie dotyczy."""
    if tok == CURSE:
        return -2
    if tok == BLESS:
        return 2
    if tok == "elder":
        n = who(inv)
        if n == BARUCH:      # "+1. Usun 1 klatwe z worka albo wydaj 2 zasoby z Tacy bez wrzucania klatwy"
            if CURSE in game.bag:
                game.bag.remove(CURSE)
            elif inv.get("taca", 0) >= 2:
                inv["taca"] -= 2; inv["res"] += 2
            return 1
        if n == MICHAL:      # "+1. Mozesz odrzucic dowolne oslabienie. Nastepnie dobierz 1 karte"
            inv["hand"] = min(8, inv["hand"] + 1)
            return 1
        if n == SZYSZKA:     # "+1. Mozesz wziac na reke 1 karte ze stosu odrzuconych"
            inv["hand"] = min(8, inv["hand"] + 1)
            return 1
        if n == WOJCIECH:    # "+1. Mozesz zyskac 1 zasob albo podejrzec 3 karty..."
            inv["res"] += 1
            return 1
    return None


def after_test(game, inv, ok, margin):
    n = who(inv)
    if n == WOJCIECH and ok and margin in (1, 2) and not inv.get("wojciech_used"):
        inv["wojciech_used"] = True   # "Raz na runde, po udanym tescie o 1 lub 2 wyzszym: dobierz 1 karte albo 1 zasob"
        if inv["hand"] < 5:
            inv["hand"] += 1
        else:
            inv["res"] += 1
    if n == SZYSZKA and inv.get("committed") and not inv.get("szyszka_used"):
        inv["szyszka_used"] = True    # "Raz na runde, po tym jak odrzucisz karte: 1 zasob albo wylecz 1 obrazenie/przerazenie"
        if inv["dmg"] > 0:
            inv["dmg"] -= 1
        elif inv["hor"] > 0:
            inv["hor"] -= 1
        else:
            inv["res"] += 1


def halabarda(game, inv, enemy):
    """Halabarda: <act> -1 com, +1 obr; <act><act> +1 com, +2 obr. Zwraca (mod, +obr, dodatkowe akcje) lub None."""
    if who(inv) != BARUCH or not inv.get("halabarda"):
        return None
    fv = inv["com"] + inv["icons"]["combat"]
    need = enemy["atk"] + game.enemy_bonus(enemy)
    if inv["actions"] >= 1 and enemy["hp"] >= 3 and fv + 1 >= need:
        return (1, 2, 1)
    if fv - 1 >= need:
        return (-1, 1, 0)
    return None


def avoid_attack(game, inv, enemy):
    """Znikanie Bez Sladu: "wyczerp i odrzuc 1 karte z reki: przemiesc sie do polaczonej lokalizacji i uniknij"."""
    if who(inv) != SZYSZKA or not inv.get("znikanie") or not inv.get("znikanie_ready") or inv["hand"] < 1:
        return False
    nb = [n for n in game.adj.get(inv["loc"], ()) if game.passable(inv, inv["loc"], n)] if hasattr(game, "adj") else []
    if not nb:
        return False
    inv["hand"] -= 1; inv["znikanie_ready"] = False
    enemy["engaged"] = None
    inv["loc"] = game.rng.choice(nb); inv["moved"] = True
    game.log["Znikanie Bez Sladu"] += 1
    return True


def end_of_turn(game, inv):
    if who(inv) == SZYSZKA and inv.get("wspolnik"):   # "odrzuc 1 zasob za kazda karte na rece (max 2); brak = 1 przerazenie"
        n = min(2, inv["hand"])
        pay = min(n, inv["res"]); inv["res"] -= pay
        if n - pay:
            game.hurt(inv, 0, n - pay, "Dawny Wspólnik")


def upkeep(game, inv):
    """Wolane PO standardowym +1 karta / +1 zasob w fazie utrzymania."""
    n = who(inv)
    inv["wojciech_used"] = False; inv["szyszka_used"] = False; inv["znikanie_ready"] = True; inv["phase_used"] = False
    if n == BARUCH:                    # Taca: "Zamiast dobrac zasob: poloz 2 zasoby na Tacy"
        inv["res"] -= 1; inv["taca"] += 2
    if n == MICHAL:
        if inv.get("gomez") and not (inv.get("moved") or inv.get("investigated")):
            game.hurt(inv, 0, 1, "Toksyczny Gomez")   # "chyba ze wykonasz akcje Ruch lub Badania"
        if game.rng.random() < 1.0 / max(1, inv.get("cards", 30)) and inv["res"] >= 1:   # Banh Mi: po dobraniu, 1 zasob -> lecz 1
            if inv["dmg"] > 0 or inv["hor"] > 0:
                inv["res"] -= 1
                if inv["dmg"] > 0: inv["dmg"] -= 1
                else: inv["hor"] -= 1
    inv["investigated"] = False


def weakness(game, inv):
    """Slabosc sygnaturowa dobrana w losowej rundzie (2-8)."""
    if inv.get("weak_done") or inv.get("weak_round") != game.round:
        return
    inv["weak_done"] = True
    n = who(inv)
    if n == BARUCH:        # Czas Spowiedzi: "Usun wszystkie zasoby z Tacy. Za kazda klatwe w worku 1 przerazenie"
        inv["taca"] = 0
        c = game.bag.count(CURSE)
        if c:
            game.hurt(inv, 0, c, "Czas Spowiedzi")
        game.log["Czas Spowiedzi"] += 1
    if n == SZYSZKA:       # Dawny Wspolnik: "zaplac 2 zasoby; za kazdy brakujacy 1 przerazenie"; zajmuje slot Sojusznika
        inv["wspolnik"] = True
        pay = min(2, inv["res"]); inv["res"] -= pay
        if 2 - pay:
            game.hurt(inv, 0, 2 - pay, "Dawny Wspólnik")
        game.log["Dawny Wspólnik w grze"] += 1
    if n == WOJCIECH:      # Wieczne Dylematy: "Umiesc 3 zetony watpliwosci"
        inv["dylematy"] = 3
        game.log["Wieczne Dylematy"] += 1
    if n == MICHAL:
        game.log["Michał: losowe oslabienie (nie modelowane)"] += 1


def shroud_mod(game, inv):
    if who(inv) == BARUCH and CURSE not in game.bag:   # "Jezeli w worku nie ma klatw: -1 do zaslony"
        return -1
    return 0


def free_action(game, inv):
    """Szyszka: Pertraktacje z Dawnym Wspolnikiem - wil(2) +1 trudnosci za kazdy kontrolowany atut."""
    if who(inv) == SZYSZKA and inv.get("wspolnik") and not inv.get("wspolnik_tried"):
        inv["wspolnik_tried"] = True
        assets = (1 if inv.get("znikanie") else 0) + (1 if inv.get("heal_cards", 0) >= 3 else 0)   # atuty w grze: Znikanie, Peter Sylvestre
        if inv["wil"] + inv["icons"]["willpower"] < 2 + assets - 1:
            return False   # polityka: nie marnuj akcji, gdy test prawie niemozliwy - placi zasobami
        ok, _ = game.test(inv, "wil", 2 + assets, name="Dawny Wspólnik: Pertraktacje wil(%d)" % (2 + assets))
        if ok:
            inv["wspolnik"] = False; game.log["Dawny Wspólnik odrzucony"] += 1
        return True
    return False


# --- ulepszenia za PD (wybor analityka, do odrzucenia przez autora; karty z arkhamdb, poziom w nawiasie) ---
UPGRADES = {
    BARUCH: [(2, "Beat Cop (2)", dict(com=1)), (2, "Vicious Blow (2)", dict(dmg_bonus=1)),
             (2, "Physical Training (2)", dict(icons_wil=0.5, icons_com=0.5))],
    MICHAL: [(3, "Shrivelling (3)", dict(dmg_bonus=1)), (2, "Guts (2)", dict(icons_wil=0.5)),
             (2, "Ward of Protection (2)", dict(ward=1))],
    SZYSZKA: [(2, "Peter Sylvestre (2)", dict(sanity=1, heal_cards=3)), (2, "Lucky! (2)", dict(icons_all=0.3)),
              (2, "Track Shoes (2)", dict(agi=1))],
    WOJCIECH: [(1, "Lockpicks (1)", dict(int=1)), (2, "Switchblade (2)", dict(dmg_bonus=1)),
               (3, "Streetwise (3)", dict(agi=1))],
}


def apply_upgrades(prof, xp):
    """Kupuje ulepszenia po kolei, poki starcza PD. Zwraca (nowy profil, lista kupionych)."""
    p = dict(prof); p["icons"] = dict(prof["icons"])
    bought = []
    for cost, name, eff in UPGRADES.get(prof.get("investigator"), []):
        if xp < cost:
            break
        xp -= cost; bought.append(name)
        for k, v in eff.items():
            if k.startswith("icons_"):
                keys = ["willpower", "intellect", "combat", "agility"] if k == "icons_all" else \
                    [{"wil": "willpower", "com": "combat", "int": "intellect", "agi": "agility"}[k[6:]]]
                for kk in keys:
                    p["icons"][kk] = round(p["icons"][kk] + v, 2)
            else:
                p[k] = p.get(k, 0) + v
    return p, bought


def selftest():
    class G:
        pass
    g = G(); g.rng = random.Random(1); g.bag = [0, "elder"]; g.log = __import__("collections").Counter()
    g.hurt = lambda inv, d, h, s="": inv.__setitem__("hor", inv["hor"] + h)
    inv = dict(investigator=BARUCH, res=5, hand=3, dmg=0, hor=0, agi=2, com=4, icons={"combat": 0.8}, actions=2)
    setup(g, inv); start_turn(g, inv)
    assert inv["halabarda"] and inv["res"] == 2
    assert token_value_extra(g, inv, "elder") == 1
    assert token_value_extra(g, inv, CURSE) == -2 and shroud_mod(g, inv) == -1
    g.bag.append(CURSE); assert shroud_mod(g, inv) == 0
    w = dict(investigator=WOJCIECH, res=5, hand=3, dmg=0, hor=0, dylematy=3, wil=2, actions=2)
    setup(g, w); w["dylematy"] = 3
    assert test_mod(g, w, "wil", 6, 3) == -1 and w["dylematy"] == 2
    assert test_mod(g, w, "wil", 2, 3) == 0 and w["hor"] == 1
    p, b = apply_upgrades(dict(investigator=WOJCIECH, int=4, agi=4, icons={"willpower": 0, "intellect": 0, "combat": 0, "agility": 0}), 6)
    assert p["int"] == 5 and p["dmg_bonus"] == 1 and p["agi"] == 5 and len(b) == 3
    print("selftest OK")


if __name__ == "__main__":
    selftest()
