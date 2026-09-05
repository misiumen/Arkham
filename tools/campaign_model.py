#!/usr/bin/env python3
"""Kampania "Czarna Krew Warty": scenariusze 1 -> 2 -> 3 pod rzad, z XP, traumami i dziennikiem.

Uzycie:
  python tools/campaign_model.py run [--campaigns 400] [--variant A|B] [--seed N] [--tweak K=V,...]
  python tools/campaign_model.py narrate [--seed N] [--variant A|B] [--tweak ...]   # jedna kampania, log
  python tools/campaign_model.py xp        # sama arytmetyka doswiadczenia z kart i fabuly
  python tools/campaign_model.py --selftest

Laczy modele: Game1 i Game3 z scenario13_model, Game2 z scenario2_model. Miedzy
scenariuszami przenosi doswiadczenie, traumy i wpisy w dzienniku kampanii wedlug
tekstow rozwiazan z Fabuly (stan 5 IX 2026). To NIE jest silnik zasad.

PRZELICZNIK XP NA MOC (uproszczenie, jawnie arbitralne):
  co 5 XP  -> +1 do kolejnej najlepszej statystyki badacza (maks +3)
  8 XP     -> +1 do obrazen z broni (lepsza bron)
  12 XP    -> +0,2 ikony na karte w talii (lepsze karty umiejetnosci)
Trauma fizyczna obniza zdrowie o 1, psychiczna poczytalnosc o 1 - na stale.
Badacz, ktorego trauma zrownuje sie z bazowym zdrowiem lub poczytalnoscia, ginie
i wchodzi nowy z 0 XP.
"""
import sys, os, io, json, random, argparse, statistics, collections

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import scenario13_model as s13
import investigators as iv
import scenario2_model as s2
from scenario2_model import load_profiles

PLAYERS = 4

# Punkty zwyciestwa dostepne na kartach (pola victory / victory_text), stan 5 IX 2026:
#  scen 1: Nory (1), Oboz na mokradlach (1), Zyrij Zerdz (1)
#  scen 2: 3 karty Barier po 1 (tylko przedmiotem), Arcykaplan 2, Zmutowany Kierownik 1
#  scen 3: ZADNA karta nie ma pola victory
VICTORY_AVAILABLE = {1: 3, 2: 6, 3: 0}
# Premie z Fabuly: scen 1 Z1 +4, Z2 (pokonani) +2, Z3/Z4 0; scen 2 +2 za ukonczenie (1a, 1b) i +2 za
# stracenie Lewiatana (1b); scen 3 tylko Victory X
SURVIVAL_XP = {1: {"wygrana": 4, "porazka": 2, "zaglada": 0}, 2: {"wygrana": 2, "porazka": 0},
               3: {"wygrana": 0, "porazka": 0}}
TASK_XP = 2   # "Wiesniacy zostali uratowani" / "pochowek": +2 PD za zadanie


def apply_xp(prof, xp):
    """XP -> ulepszenia z investigators.UPGRADES (badacze z repo); inni: +1 statystyka co 5 PD."""
    if prof.get("investigator") in iv.UPGRADES:
        return iv.apply_upgrades(prof, xp)[0]
    p = dict(prof)
    p["icons"] = dict(prof["icons"])
    lvl = min(3, xp // 5)
    order = sorted(("wil", "int", "com", "agi"), key=lambda k: -prof[k])
    for i in range(lvl):
        p[order[i % 4]] += 1
    if xp >= 8:
        p["dmg_bonus"] = min(3, p.get("dmg_bonus", 0) + 1)
    if xp >= 12:
        p["icons"] = {k: round(v + 0.2, 2) for k, v in p["icons"].items()}
    return p


def apply_trauma(prof, phys, ment):
    p = dict(prof)
    p["health"] = prof["health"] - phys
    p["sanity"] = prof["sanity"] - ment
    return p


class Investigator:
    """Stan badacza miedzy scenariuszami."""

    def __init__(self, base):
        self.base = base
        self.xp = 0
        self.phys = 0
        self.ment = 0
        self.dead = False

    def profile(self):
        p = apply_xp(self.base, self.xp)
        return apply_trauma(p, self.phys, self.ment)

    def wound(self, phys=0, ment=0):
        self.phys += phys
        self.ment += ment
        if self.base["health"] - self.phys <= 0 or self.base["sanity"] - self.ment <= 0:
            self.dead = True

    def heal_trauma(self):
        if self.phys >= self.ment and self.phys > 0:
            self.phys -= 1
        elif self.ment > 0:
            self.ment -= 1


def run_campaign(bases, variant="A", seed=None, log=None, narrate=False):
    """Jedna kampania: scenariusze 1, 2, 3 pod rzad. Zwraca podsumowanie."""
    rng = random.Random(seed)
    invs = [Investigator(b) for b in bases]
    out = {"scenarios": [], "xp_after": [], "trauma_after": [], "deaths": 0, "journal": []}
    kara2 = False        # -1 zasob i -1 akcja w scen. 2 (dziennik: Kult zyskal na czasie)
    slime = False        # Interludium II cz. 2: Nosiciel + Hierofanta + Kozi Pomiot w talii scen. 3

    for scen in (1, 2, 3):
        alive_invs = [i for i in invs if not i.dead]
        while len(alive_invs) < PLAYERS:      # zastepstwo za poleglych: nowy badacz z 0 XP
            fresh = Investigator(rng.choice(bases))
            invs.append(fresh)
            alive_invs.append(fresh)
        crew = alive_invs[:PLAYERS]
        profs = [i.profile() for i in crew]

        if scen == 1:
            g = s13.Game1(profs, seed=rng.random())
        elif scen == 2:
            g = s2.Game(profs, variant=variant, kara=kara2, seed=rng.random())
        else:
            extra = ["nosiciel", "hierofanta", "pomiot"] if slime else []
            g = s13.Game3(profs, seed=rng.random(), extra_deck=extra)
        res = g.play()
        won = res[0] == "wygrana"

        victory = getattr(g, "victory", 0)
        key = "wygrana" if won else ("zaglada" if "zaglada" in res[1] else "porazka")
        earned = victory + SURVIVAL_XP[scen].get(key, 0)
        if scen == 1 and getattr(g, "rescued", False):
            earned += TASK_XP
        if scen == 2 and won and variant == "B":
            earned += 2   # Fabula 1b: +2 PD za stracenie Lewiatana w otchlan

        # traumy: pokonany badacz = 1 trauma; do tego kary z rozwiazan
        for inv_state, sim in zip(crew, g.inv):
            if not sim["alive"]:
                inv_state.wound(phys=1) if rng.random() < 0.5 else inv_state.wound(ment=1)
            inv_state.xp += earned

        journal = []
        if scen == 1:
            if won:
                journal.append("Ojciec Zerdz uciekl do Poznania bez swojego kostura")
            else:
                journal.append("Rytual Zerdzia zostal dopelniony" if key == "porazka"
                               else "Zostawiliscie wioske wlasnemu losowi")
                for i in crew:
                    i.wound(ment=1) if rng.random() < 0.5 else i.wound(phys=1)
                journal.append("Kult zyskal na czasie")
                kara2 = True
        if scen == 2:
            if won:
                journal.append("Odlam kultu na poludniu zostal wypleniony" if variant == "A"
                               else "Most Chwaliszewski legl w gruzach; Lewiatan stracony w otchlan")
                journal.append("Kult przemyca czarne mleko")
                for i in crew:
                    i.heal_trauma()          # Interludium II cz. 1: -1 trauma
            else:
                journal.append("Szlam wylal sie na ulice portu")
                slime = True
                if res[1] == "barka zatopiona":
                    journal.append("Barka Jadwiga spoczela na dnie (2 traumy, slabosc, -2 akcje)")
                    for i in crew:
                        i.wound(phys=1, ment=1)
                else:
                    journal.append("Nurt Warty okazal sie zbyt silny (1 trauma)")
                    for i in crew:
                        i.wound(phys=1) if rng.random() < 0.5 else i.wound(ment=1)
        if scen == 3:
            journal.append("Czarna Koza z Ostrowa zostala zgladzona" if won
                           else "Poznan zostal pochloniety przez zgnilizne - KONIEC KAMPANII")

        out["scenarios"].append({
            "scen": scen, "won": won, "reason": res[1], "rounds": g.round,
            "victory": victory, "xp": earned, "events": list(getattr(g, "events", [])),
            "log": dict(g.log), "tests": {k: list(v) for k, v in g.tests.items()},
            "inv": [(i["investigator"], i["dmg"], i["health"], i["hor"], i["sanity"], i["alive"]) for i in g.inv],
        })
        out["journal"].append(journal)
        out["xp_after"].append(statistics.mean(i.xp for i in crew))
        out["trauma_after"].append(statistics.mean(i.phys + i.ment for i in crew))
        out["deaths"] = sum(1 for i in invs if i.dead)
        if log is not None:
            log.append("scen %d: %s (%s), rundy %d, XP +%d (zwyc %d), sredni XP %.1f, traumy %.1f"
                       % (scen, "WYGRANA" if won else "porazka", res[1], g.round, earned, victory,
                          out["xp_after"][-1], out["trauma_after"][-1]))
    out["all_won"] = all(s["won"] for s in out["scenarios"])
    return out


def cmd_run(bases, n, variant, seed):
    rng = random.Random(seed)
    per = {1: collections.Counter(), 2: collections.Counter(), 3: collections.Counter()}
    xp = {1: [], 2: [], 3: []}
    tr = {1: [], 2: [], 3: []}
    rounds = {1: [], 2: [], 3: []}
    wins = {1: 0, 2: 0, 3: 0}
    reasons = {1: collections.Counter(), 2: collections.Counter(), 3: collections.Counter()}
    all_won = deaths = 0
    for _ in range(n):
        c = run_campaign(bases, variant, seed=rng.random())
        for k, s in enumerate(c["scenarios"]):
            i = s["scen"]
            wins[i] += s["won"]
            reasons[i][("WYGRANA " if s["won"] else "porazka ") + s["reason"]] += 1
            xp[i].append(c["xp_after"][k])
            tr[i].append(c["trauma_after"][k])
            rounds[i].append(s["rounds"])
            per[i][s["xp"]] += 1
        all_won += c["all_won"]
        deaths += c["deaths"]

    print("# KAMPANIA: scenariusze 1 -> 2 -> 3, %d przebiegow, %d graczy, scen. 2 wariant %s"
          % (n, PLAYERS, variant))
    print("# LOC_DOOM_COUNTS=%d KOZA_STATS=%d KOZA_IN_DECK=%d LEWIATAN_EVADE=%d LEWIATAN_RETURNS=%d PRESSURE_NEED=%d DECK_COPIES=%d"
          % (s13.LOC_DOOM_COUNTS, s13.KOZA_STATS, s13.KOZA_IN_DECK, s2.LEWIATAN_EVADE, s2.LEWIATAN_RETURNS,
             s2.PRESSURE_NEED, s2.DECK_COPIES))
    print("kampanie wygrane w calosci (3 z 3): %.1f%%   sredni bilans zgonow: %.2f na kampanie"
          % (100 * all_won / n, deaths / n))
    print()
    print("%-4s %-9s %-8s %-11s %-11s %s" % ("scen", "wygrane", "rundy", "XP/badacz", "traumy", "najczestsze zakonczenie"))
    for i in (1, 2, 3):
        top = reasons[i].most_common(1)[0]
        print("%-4d %6.1f%%   %6.1f   %8.1f    %8.2f     %s (%.0f%%)"
              % (i, 100 * wins[i] / n, statistics.median(rounds[i]),
                 statistics.mean(xp[i]), statistics.mean(tr[i]), top[0], 100 * top[1] / n))
    print()
    print("Rozklad zdobytego XP w pojedynczym scenariuszu:")
    for i in (1, 2, 3):
        d = ", ".join("%d XP: %.0f%%" % (k, 100 * v / n) for k, v in sorted(per[i].items()))
        print("  scen %d -> %s" % (i, d))
    print()
    print("Przyczyny konca:")
    for i in (1, 2, 3):
        print("  scen %d:" % i)
        for r, v in reasons[i].most_common(5):
            print("    %-64s %5.1f%%" % (r, 100 * v / n))
    return {"wins": {i: wins[i] / n for i in wins}, "all_won": all_won / n,
            "xp": {i: statistics.mean(xp[i]) for i in xp}, "rounds": {i: statistics.median(rounds[i]) for i in rounds},
            "reasons": {i: dict(reasons[i].most_common(5)) for i in reasons}, "deaths": deaths / n}


def cmd_narrate(bases, variant, seed):
    c = run_campaign(bases, variant, seed=seed)
    print("# NARRACJA: jedna kampania, seed %s, wariant %s" % (seed, variant))
    for k, s in enumerate(c["scenarios"]):
        print()
        print("== SCENARIUSZ %d: %s (%s) po %d rundach, +%d PD (zwyc. %d)"
              % (s["scen"], "WYGRANA" if s["won"] else "PORAZKA", s["reason"], s["rounds"], s["xp"], s["victory"]))
        for r, txt in s["events"][:40]:
            print("  r%-3d %s" % (r, txt))
        print("  badacze: " + "; ".join("%s obr %d/%d przer %d/%d%s" % (n, d, h, ho, sa, "" if al else " POKONANY")
                                         for n, d, h, ho, sa, al in s["inv"]))
        print("  dziennik: " + " | ".join(c["journal"][k]))
        print("  sredni XP po scenariuszu: %.1f, traumy: %.1f" % (c["xp_after"][k], c["trauma_after"][k]))
        top = sorted(s["log"].items(), key=lambda kv: -kv[1])[:10]
        print("  zdarzenia: " + ", ".join("%s x%d" % kv for kv in top))
        hard = sorted(((k2, n, ok) for k2, (n, ok) in s["tests"].items() if n >= 3), key=lambda t: t[2] / t[1])[:4]
        print("  najtrudniejsze testy: " + ", ".join("%s %d%% (n=%d)" % (k2, 100 * ok / n, n) for k2, n, ok in hard))


def cmd_xp():
    print("# ARYTMETYKA DOSWIADCZENIA (z pol victory na kartach i rozwiazan w Fabule)")
    print()
    print("%-6s %-24s %-22s %s" % ("scen", "punkty zwyciestwa", "premia za przetrwanie", "maks XP"))
    tot = 0
    src = {1: "Nory, Oboz na mokradlach, Zyrij; +2 wiesniacy, +2 pochowek",
           2: "3 Bariery (przedmiotem), Arcykaplan 2, Kierownik 1; +2 ukonczenie, +2 Lewiatan (B)",
           3: "brak pol victory w scenariuszu 3"}
    for i in (1, 2, 3):
        v = VICTORY_AVAILABLE[i]
        b = SURVIVAL_XP[i]["wygrana"] + (2 * TASK_XP if i == 1 else 0) + (2 if i == 2 else 0)
        tot += v + b
        print("%-6d %-24s %-22s %d      (%s)" % (i, v, "+%d" % b, v + b, src[i]))
    print()
    print("Maksimum po trzech scenariuszach: %d XP na badacza (przy komplecie zwyciestw i zadan)." % tot)
    print("Dla porownania: oficjalne kampanie FFG daja zwykle 5-10 XP za scenariusz,")
    print("czyli po trzech scenariuszach badacz ma 15-25 XP i talie na poziomie 3-5.")


def apply_tweaks(spec):
    for kv in filter(None, spec.split(",")):
        k, v = kv.split("=")
        v = int(v)
        hit = False
        for mod in (s13, s2):
            if hasattr(mod, k):
                setattr(mod, k, v)
                hit = True
        if not hit:
            sys.exit("nieznane pokretlo: " + k)
        print("# tweak:", k, "=", v)


def selftest():
    base = dict(investigator="X", faction="guardian", wil=3, int=3, com=4, agi=2,
                health=9, sanity=5, weapons=2, dmg_bonus=1, heal_cards=2, cards=30, allies=1,
                icons={"willpower": 0.5, "intellect": 0.5, "combat": 0.8, "agility": 0.4})
    p0 = apply_xp(base, 0)
    assert p0["com"] == 4 and p0["dmg_bonus"] == 1
    p10 = apply_xp(base, 10)
    assert p10["com"] == 5 and p10["wil"] == 4 and p10["dmg_bonus"] == 2, p10
    p15 = apply_xp(base, 15)
    assert p15["icons"]["combat"] == 1.0, p15["icons"]
    i = Investigator(base)
    i.wound(phys=9)
    assert i.dead
    prof = Investigator(base).profile()
    assert prof["health"] == 9 and prof["sanity"] == 5
    c = run_campaign([base] * 4, seed=1)
    assert len(c["scenarios"]) == 3 and c["xp_after"][2] >= c["xp_after"][0]
    print("selftest OK")


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a or a[0] in ("-h", "--help"):
        print(__doc__)
    elif a[0] == "--selftest":
        selftest()
    elif a[0] == "xp":
        cmd_xp()
    elif a[0] in ("run", "narrate"):
        ap = argparse.ArgumentParser()
        ap.add_argument("--campaigns", type=int, default=400)
        ap.add_argument("--variant", default="A")
        ap.add_argument("--seed", type=int, default=1)
        ap.add_argument("--tweak", default="")
        ap.add_argument("--json", default="")
        o = ap.parse_args(a[1:])
        apply_tweaks(o.tweak)
        if a[0] == "run":
            r = cmd_run(load_profiles()[:PLAYERS], o.campaigns, o.variant, o.seed)
            if o.json:
                io.open(o.json, "w", encoding="utf-8").write(json.dumps(r, ensure_ascii=False, indent=1))
        else:
            cmd_narrate(load_profiles()[:PLAYERS], o.variant, o.seed)
    else:
        sys.exit("nieznany tryb: %s" % a[0])
