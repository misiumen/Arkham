#!/usr/bin/env python3
"""Ekstraktor i linter kart JiMEditor (.card) dla agenta arkham-card-reviewer.

Pliki .card to JSON z wklejonym obrazem w base64 (do ~4 MB na karte), wiec nie
nadaja sie do czytania wprost. Ten skrypt wycina balast, tlumaczy chinskie
enumy JiMEditora na polski i robi mechaniczne kontrole, ktorych model nie musi
liczyc recznie.

Uzycie:  python tools/arkham_cards.py <index|text|dump|lint|story> [sciezka...]
"""
import sys, os, io, re, json, glob, zipfile, difflib, unicodedata, collections

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# --- slowniki enumow JiMEditora -------------------------------------------
TYPE = {
    "调查员": "badacz", "调查员背面": "badacz/rewers", "调查员小卡": "mini-karta badacza",
    "事件卡": "wydarzenie", "支援卡": "atut", "诡计卡": "podstep", "敌人卡": "przeciwnik",
    "地点卡": "lokacja", "场景卡": "akt", "密谋卡": "tajemnica", "故事卡": "karta fabularna",
    "冒险参考卡": "karta scenariusza", "规则小卡": "karta zasad",
    "遭遇卡背": "rewers spotkan", "玩家卡背": "rewers gracza", "定制卡背": "rewers custom",
}
CLASS = {
    "守护者": "Obronca", "探求者": "Poszukiwacz", "流浪者": "Wloczega", "潜修者": "Mistyk",
    "生存者": "Ocalaly", "中立": "Neutralna", "弱点": "Oslabienie",
}
MISC = {
    "已揭示": "odkryta", "未揭示": "nieodkryta", "默认": "domyslny",
    "盟友": "Sojusznik", "双手": "Obie rece", "手部": "Reka", "独特": "unikat",
    "调查员": "badacz",  # <调查员> = symbol badacza (skalowanie na gracza)
}
ICON = {
    "暗红漏斗": "ciemnoczerwony lejek", "橙心": "pomaranczowe serce", "浅褐水滴": "jasnobrazowa kropla",
    "深紫星": "ciemnofioletowa gwiazda", "深绿斜二": "ciemnozielone dwie kreski", "深蓝T": "granatowe T",
    "粉桃": "rozowa brzoskwinia", "紫月": "fioletowy ksiezyc", "红十": "czerwony krzyz",
    "红方": "czerwony kwadrat", "绿菱": "zielony romb", "褐扭": "brazowy zwoj",
    "青花": "turkusowy kwiat", "黄圆": "zolte kolo",
}
ENUMS = {**TYPE, **CLASS, **MISC, **ICON}

DROP = ("picture_base64", "tts_config", "content_hash", "picture_layout", "external_image")
# ikony umiejetnosci/zetonow wstawiane jako emoji zamiast tagow JiM
EMOJI_ICON = {
    "\U0001f9e0": "<int>", "\U0001f44a": "<com>", "\U0001f9b6": "<agi>", "⚡": "<wil>",
    "\U0001f4da": "<int>", "\U0001f311": "<eld>", "\U0001f480": "<sku>", "⭐": "<ble>",
    "\U0001f31f": "<ble>", "⭕": "<cur>", "\U0001f3c5": "?", "\U0001f575": "<badacz>",
    "\U0001f535": "punktor listy", "➡": "<act>",
}
KEYWORD_TAGS = {  # tagi JiM najczesciej uzywane w tym repo
    "for": "Wymuszony", "rev": "Odkrycie", "act": "Akcja", "rea": "Reakcja",
    "obj": "Cel", "upg": "punktor progu", "spa": "Spontaniczny", "pat": "Patrol",
    "hau": "Nawiedzony", "fre": "Wolna akcja", "eld": "Przedwieczny",
    "wil": "wola", "int": "intelekt", "com": "walka", "agi": "zrecznosc",
}
SEVERITY = {"BLOKER": 0, "BLAD": 1, "SPOJNOSC": 2, "BALANS": 3, "NIT": 4}
# oficjalne polskie nazwy akcji (Galakta) - wariant -> forma kanoniczna
CANON = {
    "pertraktacje": "Pertraktacje", "pertraktacja": "Pertraktacje",
    "rezygnacja": "Rezygnacja", "zrezygnuj": "Rezygnacja",
    "badanie": "Badanie", "ruch": "Ruch", "walka": "Walka", "unik": "Unik",
}
STOPWORDS = {"jesli", "jezeli", "kazdy", "gdy", "kiedy", "nastepnie", "wykonaj", "umiesc",
             "rozstaw", "odrzuc", "badacz", "badacze", "wybierz", "ten", "ta", "to",
             "przeszukaj", "poloz", "dobierz", "za", "nie", "po", "przed"}


# --- wczytywanie -----------------------------------------------------------
def strip(node):
    if isinstance(node, dict):
        return {k: strip(v) for k, v in node.items() if k not in DROP}
    if isinstance(node, list):
        return [strip(v) for v in node]
    if isinstance(node, str):
        if node.strip() in ENUMS:
            return ENUMS[node.strip()]
        return node.replace("<调查员>", "<badacz>")  # symbol badacza w tekscie
    return node


def load(paths=None):
    """[(sciezka_wzgledna, dict_karty)] - bez base64, bez layoutu."""
    files = []
    for p in (paths or [ROOT]):
        p = p if os.path.isabs(p) else os.path.join(ROOT, p)
        if os.path.isdir(p):
            files += glob.glob(os.path.join(p, "**", "*.card"), recursive=True)
        elif p.endswith(".card"):
            files.append(p)
    out = []
    for f in sorted(set(files)):
        try:
            with open(f, encoding="utf-8") as fh:
                out.append((os.path.relpath(f, ROOT).replace("\\", "/"), strip(json.load(fh))))
        except Exception as e:  # uszkodzony JSON to tez znalezisko
            out.append((os.path.relpath(f, ROOT).replace("\\", "/"), {"_error": str(e)}))
    return out


def sides(card):
    """Awers + rewers osobno (lokacje/akty trzymaja tresc na rewersie)."""
    yield "front", card
    back = card.get("back")
    if isinstance(back, dict) and len(back) > 2:
        yield "back", back


def texts(card):
    for side, s in sides(card):
        for field in ("body", "flavor", "victory_text"):
            v = s.get(field)
            if isinstance(v, str) and v.strip():
                yield side, field, v
        for holder in ("card_back", "scenario_card"):
            sub = s.get(holder)
            if isinstance(sub, dict):
                for k, v in sub.items():
                    if isinstance(v, str) and v.strip():
                        yield side, holder + "." + k, v


def names_all(card):
    """Wszystkie nazwy karty (awers i rewers roznia sie np. przy lokacjach)."""
    out = []
    for _, s in sides(card):
        n = (s.get("name") or "").strip()
        if n and n not in out:
            out.append(n)
    return out


def name_of(card):
    """Nazwa do pokazania. Lokacja nieodkryta nosi nazwe grupy - licz sie z rewersem."""
    ns = names_all(card)
    if not ns:
        return ""
    if card.get("type") == "lokacja" and len(ns) > 1:
        return ns[-1]
    return ns[0]


# --- dopasowanie nazw mimo polskiej odmiany -------------------------------
def stem(text):
    t = unicodedata.normalize("NFKD", text.lower()).replace("ł", "l")
    t = "".join(c for c in t if not unicodedata.combining(c))
    return " ".join(w[:5] for w in re.findall(r"[a-z0-9]+", t) if w not in STOPWORDS)


def similar(a, b):
    return difflib.SequenceMatcher(None, stem(a), stem(b)).ratio()


# --- tryby -----------------------------------------------------------------
def m_index(paths):
    print("plik\ttyp\tnazwa\tklasa\tkoszt/poz\tstatystyki\tgrupa\tcechy")
    for path, c in load(paths):
        b = c.get("back") or {}
        stats = []
        for k, lab in (("attack", "atk"), ("enemy_health", "hp"), ("evade", "ucz"),
                       ("enemy_damage", "obr"), ("enemy_damage_horror", "prz"),
                       ("health", "zdr"), ("horror", "psy")):
            if c.get(k) not in (None, ""):
                stats.append("%s%s" % (lab, c[k]))
        for k, lab in (("shroud", "zaslona"), ("clues", "wskaz"), ("threshold", "prog"),
                       ("victory", "zwyc")):
            v = c.get(k, b.get(k))
            if v not in (None, ""):
                stats.append("%s%s" % (lab, v))
        traits = c.get("traits") or b.get("traits") or []
        print("\t".join([
            path, str(c.get("type", "?")), name_of(c) or "-", str(c.get("class") or "-"),
            "%s/%s" % (c.get("cost", "-"), c.get("level", "-")), ",".join(stats) or "-",
            str(c.get("encounter_group_number") or b.get("encounter_group_number")
                or c.get("encounter_group") or "-"),
            ",".join(traits) or "-",
        ]))


def m_text(paths):
    for path, c in load(paths):
        print("\n### %s - %s [%s]" % (path, name_of(c) or "(bez nazwy)", c.get("type", "?")))
        for side, field, v in texts(c):
            print("[%s.%s] %s" % (side, field, v))


def m_dump(paths):
    for path, c in load(paths):
        print("### %s" % path)
        print(json.dumps(c, ensure_ascii=False, indent=1))


def m_story(paths):
    files = []
    for p in (paths or [os.path.join(ROOT, "Fabuła")]):
        p = p if os.path.isabs(p) else os.path.join(ROOT, p)
        if os.path.isdir(p):
            for ext in ("*.docx", "*.odt"):
                files += glob.glob(os.path.join(p, "**", ext), recursive=True)
        else:
            files.append(p)
    for f in sorted(set(files)):
        inner = "content.xml" if f.endswith(".odt") else "word/document.xml"
        try:
            with zipfile.ZipFile(f) as z:
                xml = z.read(inner).decode("utf-8", "replace")
        except Exception as e:
            print("### %s: BLAD odczytu (%s)" % (f, e))
            continue
        xml = re.sub(r"</(w:p|text:p|text:h)>", "\n", xml)
        txt = re.sub(r"<[^>]+>", "", xml)
        txt = (txt.replace("&amp;", "&").replace("&lt;", "<")
                  .replace("&gt;", ">").replace("&#8217;", "'").replace("&quot;", '"'))
        print("\n### %s" % os.path.relpath(f, ROOT))
        print(re.sub(r"\n{3,}", "\n\n", txt).strip())


# --- lint ------------------------------------------------------------------
def lint_findings(paths):
    """(karty, [(kod, sciezka, pole, opis)], [uwagi_globalne])"""
    cards = load(paths)
    findings, notes = [], []

    def add(path, field, code, msg):
        findings.append((code, path, field, msg))

    names, display = {}, {}
    for path, c in cards:
        for n in names_all(c):
            names.setdefault(n, []).append(path)
        # nazwa awersu lokacji to nazwa grupy (np. "Las") i powtarza sie legalnie
        if name_of(c):
            display.setdefault(name_of(c), []).append(path)

    for n, where in display.items():
        where = sorted(set(where))
        if len(where) > 1:
            add(where[0], "name", "SPOJNOSC",
                "nazwa '%s' powtarza sie w: %s" % (n, ", ".join(where[1:])))
        if not re.search(r"[aeiouyąęó]", n.lower()) or re.fullmatch(r"[a-z]{4,}", n):
            add(where[0], "name", "BLAD", "nazwa wyglada na placeholder: '%s'" % n)

    alt_labels = collections.Counter()
    unmatched = {}
    no_art = []
    for path, c in cards:
        if "_error" in c:
            add(path, "-", "BLOKER", "nie da sie sparsowac JSON: %s" % c["_error"])
            continue
        typ = c.get("type", "")
        emoji_here = collections.Counter()

        for side, field, v in texts(c):
            loc = "%s.%s" % (side, field)
            # alternatywne notacje slow kluczowych
            for m in re.finditer(r"【([^】]{1,30})】|\{\{([^}]{1,30})\}\}", v):
                lab = m.group(1) or m.group(2)
                alt_labels[lab.strip()] += 1
                if lab != lab.strip() or lab.strip().endswith((".", ",")):
                    add(path, loc, "SPOJNOSC",
                        "znacznik '%s' ma zbedna spacje/kropke" % m.group(0))
                key = next((t for t, pl in KEYWORD_TAGS.items() if similar(pl, lab) > 0.85), None)
                if key:
                    add(path, loc, "SPOJNOSC",
                        "'%s' zapisane recznie - w repo dominuje tag <%s>" % (m.group(0), key))
            # ikony jako emoji (zbiorczo dla calej karty)
            for ch in EMOJI_ICON:
                if ch in v:
                    emoji_here[ch] += v.count(ch)
            # test umiejetnosci bez podanej trudnosci
            for m in re.finditer(r"test\w*\s+(?:<\w+>|[\U0001F300-\U0001FAFF⚡⭐])", v, re.I):
                seg = v[m.start():m.start() + 70].splitlines()[0].strip()
                if not re.search(r"\(\s*[\dX]", seg):
                    add(path, loc, "BLAD", "test bez podanej trudnosci: '%s'" % seg)
                    break
            # odwolania do innych kart
            pat = (r"【([^】]{3,40})】|"
                   r"(?:kart[ęyai]?|wrog[aiu]|przeciwnik\w*|lokalizacj\w+|lokacj\w+|"
                   r"atut\w*|o nazwie)\s+((?:[A-ZĄĆĘŁŃÓŚŹŻ]"
                   r"[\wąćęłńóśźż-]+\s*){1,4})")
            for m in re.finditer(pat, v):
                cand = (m.group(1) or m.group(2) or "").strip(" .,:;\"")
                if len(cand) < 4 or cand.lower() in STOPWORDS:
                    continue
                best, score = max(((n, similar(cand, n)) for n in names),
                                  key=lambda x: x[1], default=("", 0))
                if score >= 0.92:
                    continue
                if score >= 0.7:
                    add(path, loc, "SPOJNOSC",
                        "odwolanie '%s' ~ karta '%s' - ujednolic nazwe" % (cand, best))
                elif m.group(1):
                    unmatched.setdefault(cand, []).append(path)

        if emoji_here:
            add(path, "tekst", "SPOJNOSC", "ikony wpisane jako emoji zamiast tagow JiM: %s"
                % ", ".join("%s->%s (%dx)" % (ch, EMOJI_ICON[ch], n)
                            for ch, n in emoji_here.most_common()))

        # sanity pol
        if c.get("cost") == -1:
            add(path, "cost", "BLAD", "koszt = -1 (pole niewypelnione)")
        if c.get("level") == -1 and typ in ("atut", "wydarzenie"):
            add(path, "level", "SPOJNOSC", "poziom = -1")
        if typ in ("przeciwnik", "podstep", "lokacja", "akt", "tajemnica", "karta fabularna"):
            if not any(f == "body" for _, f, _ in texts(c)):
                add(path, "body", "BLAD", "karta bez tekstu zasad")
            if not (c.get("encounter_group") or (c.get("back") or {}).get("encounter_group")):
                add(path, "encounter_group", "SPOJNOSC", "brak grupy spotkan")
        if typ in ("przeciwnik", "lokacja", "atut", "badacz") and not (
                c.get("illustrator") or (c.get("back") or {}).get("illustrator")):
            no_art.append(path)
        for key in ("shroud", "clues", "threshold", "enemy_health", "attack", "evade"):
            for side, s in sides(c):
                v = s.get(key)
                if isinstance(v, str) and v.strip() and not re.fullmatch(
                        r"[\dX?]+\s*(\+\s*\d+)?\s*(<badacz>)?", v.strip()):
                    add(path, "%s.%s" % (side, key), "BLAD", "nietypowa wartosc '%s'" % v)

    # rozjazd notacji w skali repo
    if alt_labels:
        notes.append("etykiety w 【】/{{}}: %s" %
              ", ".join("%s(%d)" % (k, v) for k, v in alt_labels.most_common(15)))
        seen = list(alt_labels)
        for i, a in enumerate(seen):
            for b in seen[i + 1:]:
                if a == b or similar(a, b) <= 0.85:
                    continue
                bare = lambda s: s.strip(" .,:;")
                if bare(a) == bare(b):
                    notes.append("blizniacze etykiety: '%s' vs '%s' - roznia sie tylko "
                                 "interpunkcja lub spacja, do poprawy" % (a, b))
                elif any(CANON.get(bare(x).lower(), bare(x)) != bare(x) for x in (a, b)):
                    # wariant nazwy akcji, nie odmiana: Pertraktacja/Zrezygnuj
                    notes.append("blizniacze etykiety: '%s' vs '%s' - dwie nazwy na jedno "
                                 "slowo kluczowe, oficjalna to '%s'"
                                 % (a, b, CANON.get(bare(a).lower()) or CANON.get(bare(b).lower())))
                else:
                    notes.append("blizniacze etykiety: '%s' vs '%s' - odmiana tego samego "
                                 "slowa; po polsku bywa poprawna, sprawdz kontekst" % (a, b))

    # graf polaczen lokacji per scenariusz
    scen = collections.defaultdict(lambda: {"own": {}, "links": collections.defaultdict(set), "cards": 0})
    for path, c in cards:
        if c.get("type") != "lokacja":
            continue
        key = "/".join(path.split("/")[:2])
        scen[key]["cards"] = scen[key].get("cards", 0) + 1
        for side, s in sides(c):
            if s.get("location_icon"):
                scen[key]["own"].setdefault(s["location_icon"], set()).add(name_of(c))
            for lk in (s.get("location_link") or []):
                scen[key]["links"][lk].add(name_of(c))
    for key, g in sorted(scen.items()):
        if not g["own"] and g["links"]:
            add(key, "location_icon", "BLAD",
                "zadna z %d lokacji nie ma ustawionego wlasnego symbolu (location_icon), "
                "a %d symboli wystepuje w polaczeniach - mapy nie da sie zlozyc"
                % (g["cards"], len(g["links"])))
            continue
        for icon, users in sorted(g["links"].items()):
            if icon not in g["own"]:
                add(key, "location_link", "BLAD",
                    "symbol '%s' w polaczeniach (%s), ale zadna lokacja go nie nosi"
                    % (icon, ", ".join(sorted(users))))
        for icon, owners in sorted(g["own"].items()):
            if icon not in g["links"]:
                add(key, "location_icon", "SPOJNOSC",
                    "symbol '%s' (%s) - zadna lokacja tam nie prowadzi (slepy zaulek)"
                    % (icon, ", ".join(sorted(owners))))

    if unmatched:
        for lab, where in sorted(unmatched.items()):
            add(where[0], "tekst", "SPOJNOSC",
                "etykieta '%s' (%dx) nie jest nazwa zadnej karty - jesli to cecha, akcja lub "
                "slowo kluczowe, notacja 【】 miesza je z nazwami kart" % (lab, len(where)))
    if no_art:
        add("(zbiorczo)", "illustrator", "NIT",
            "%d kart bez ilustratora, m.in.: %s" % (len(no_art), ", ".join(no_art[:5])))

    findings = sorted(set(findings))
    findings.sort(key=lambda f: (SEVERITY.get(f[0], 9), f[1]))
    return cards, findings, notes


def m_lint(paths):
    cards, findings, notes = lint_findings(paths)
    for n in notes:
        print("# " + n)
    for code, path, field, msg in findings:
        print("%s [%s]: %s - %s" % (path, field, code, msg))
    print("\n# kart: %d, znalezisk: %d" % (len(cards), len(findings)))


def selftest():
    assert strip({"picture_base64": "x", "type": "地点卡"}) == {"type": "lokacja"}
    assert strip({"class": "守护者"})["class"] == "Obronca"
    assert similar("Przekonanego Wyznawce", "Przekonany Wyznawca") > 0.9, "odmiana PL"
    assert similar("Przybrzezna rampa zaladunkowa", "Przybrzeżna rampa załadunkowa") > 0.95
    assert similar("Kozi Pomiot", "Czempion Kozieglowych") < 0.7
    assert stem("Wymuszony") == stem("wymuszony")
    assert normalize_labels("【Pertraktacje.】Test") == "【Pertraktacje】. Test"
    assert normalize_labels("【Tkanki 】i") == "【Tkanki】i", "odmiana zostaje"
    assert normalize_labels("【Pertraktacja 】(4)") == "【Pertraktacje】(4)"
    assert normalize_labels("【Zrezygnuj.】 X") == "【Rezygnacja】. X"
    assert normalize_labels("【Ruchu】") == "【Ruchu】", "odmiany nie ruszamy"
    c = {"type": "lokacja", "name": "Las", "back": {"type": "lokacja", "body": "a",
                                                    "name": "Grzezawisko", "flavor": "f"}}
    assert name_of(c) == "Grzezawisko", "lokacja: nazwa po odkryciu"
    assert names_all(c) == ["Las", "Grzezawisko"] and len(list(texts(c))) == 2
    print("selftest OK")


def normalize_labels(text):
    """Porzadkuje etykiety 【...】: spacje, interpunkcja, kanoniczne nazwy akcji.

    Odmiana zostaje nietknieta - 'akcja 【Ruchu】' to poprawna polszczyzna.
    Podmieniane sa tylko warianty tej samej nazwy akcji (Pertraktacja -> Pertraktacje,
    Zrezygnuj -> Rezygnacja), bo to dwie nazwy na jedno slowo kluczowe.
    """
    def one(m):
        lab = m.group(1)
        tail = ""
        core = lab.strip()
        while core and core[-1] in ".,;:":  # kropka wychodzi poza nawias
            tail = core[-1] + tail
            core = core[:-1].strip()
        canon = CANON.get(core.lower())
        if canon and canon != core:
            core = canon
        return "【%s】%s" % (core, tail)

    out = re.sub(r"【([^】]*)】", one, text)
    # po wyjeciu kropki sklej odstep: '】.Test' -> '】. Test'
    return re.sub(r"(】[.,;:])(?=[^\s\\])", r"\1 ", out)


def m_fix(paths):
    """Podglad zmian; z --apply zapisuje pliki. Tekst .card ruszany jest surowo,
    zeby nie przepisywac obrazu base64 ani formatowania JSON."""
    apply = "--apply" in paths
    paths = [p for p in paths if p != "--apply"]
    files = [os.path.join(ROOT, p) for p, _ in load(paths or None)]
    changed = 0
    for f in files:
        with io.open(f, encoding="utf-8", newline="") as fh:
            raw = fh.read()
        new = normalize_labels(raw)
        if new == raw:
            continue
        changed += 1
        rel = os.path.relpath(f, ROOT).replace("\\", "/")
        olds = re.findall(r"【[^】]*】[.,;:]?", raw)
        news = re.findall(r"【[^】]*】[.,;:]?", new)
        for a, b in zip(olds, news):
            if a != b:
                print("%s: %s  ->  %s" % (rel, a, b))
        if apply:
            with io.open(f, "w", encoding="utf-8", newline="") as fh:
                fh.write(new)
    print("\n# plikow do zmiany: %d%s" % (changed, " (ZAPISANE)" if apply else
                                          " (podglad; dodaj --apply zeby zapisac)"))


MODES = {"index": m_index, "text": m_text, "dump": m_dump, "lint": m_lint,
         "story": m_story, "fix": m_fix}

if __name__ == "__main__":
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        print(__doc__)
    elif args[0] == "--selftest":
        selftest()
    elif args[0] in MODES:
        try:
            MODES[args[0]](args[1:])
            sys.stdout.flush()
        except (BrokenPipeError, OSError):  # np. przy `| head`
            os._exit(0)
    else:
        sys.exit("nieznany tryb: %s (dostepne: %s, --selftest)" % (args[0], ", ".join(MODES)))
