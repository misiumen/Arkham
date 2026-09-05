# Playtest: Scenariusz 2 „Nurt Szaleństwa"

Data: 2026-09-01, aktualizacja 2026-09-04 · 4 badaczy · talie 0 XP z arkhamdb · worek Standard · warianty A i B

## Werdykt

Scenariusz w obecnej postaci jest **nie do wygrania w rozsądnym odsetku partii**: model daje 12% wygranych w wariancie A (Rytuał) i 6% w wariancie B (Ucieczka), a rozgrywka narracyjna skończyła się rozpadem grupy w 7. rundzie przy Skażonym Nurcie, w połowie drogi. Winna nie jest zagłada (1–2% porażek), tylko **gęstość wrogów w talii spotkań** — 14 z 26 kart to przeciwnicy, przy 4 graczach to 2 nowe wrogi co rundę po 3 zdrowia każdy — oraz **Kozi Pomiot ×4**, który za każde pokonanie daje przerażenie całej grupie. Do tego scenariusz jest **niekompletny**: Tajemnica 1 odsyła do wroga, którego nie ma (Topielec z Warty), dwie lokacje do atutu, którego nie ma (Zapas Paliwa), a przygotowanie nie mówi, kiedy Bariery wchodzą do gry ani jak leży mapa. Najpierw: dopisać brakujące karty i zasady, potem zdjąć 3–4 wrogów z talii i zmniejszyć karę Pomiota — dopiero wtedy warto stroić bariery i Most.

## Po poprawkach autora (2026-09-04)

Autor: Bariery leżą na stole od początku razem z lokacjami (przygotowanie do doprecyzowania — teraz mówi „odłóżcie na bok"); Tajemnica 1 rozstawia teraz Rzeczne Młode zamiast nieistniejącego Topielca. Model czyta `quantity` prosto z kart, więc zmiany w talii od razu liczą się w symulacji.

**Talia spotkań po zmianie: Kozi Pomiot 4→2, Nosiciel 3→2, Rzeczne Młode 3→2, Hierofanta 2→1** (26 → 21 kart, wrogów 14 → 7).

| skład talii | A | B |
|---|---|---|
| pierwotny (14 wrogów / 26) | 12% | 4% |
| Pomiot 2 | 33% | 8% |
| Pomiot 2, Nosiciel 2, Młode 2, Hierofanta 1 — **wpisane do kart** | **35%** | 5% |
| jw. + Pomiot 1 | 47% | 8% |

Wariant A wraca do grywalności samymi liczbami. Wariant B nie — 55–70% partii nadal tonie na Moście, bo Lewiatan (2 barce co rundę) i porażki „Cała naprzód" (1 barce) wyprzedzają zbieranie 6 znaczników Ciśnienia. Sprawdzone w modelu (400 gier każde, talia po zmianie):

| zmiana w wariancie B | wygrane B |
|---|---|
| bez zmian | 8% |
| Lewiatan nie atakuje wszystkich (tylko zwarcie) | 10% |
| „Cała naprzód" wil(3)/com(3) zamiast 4 | 21% |
| **Ciśnienie: 4 znaczniki zamiast `<per>`+2** | **26%** |
| Ciśnienie 4 + porażka nie uszkadza barki | 28% |
| Ciśnienie 4 + Lewiatan 1 barce | 28% |
| Ciśnienie 4 + Lewiatan 1 barce, tylko zwarcie + porażka bez uszkodzenia | **36%** |

## Wprowadzone zmiany (2026-09-04, druga tura)

Model przeliczony po edycjach kart (1000 gier na wariant, talia 21 kart): **A 52%, B 46%** (start: 12% / 6%). Obie ścieżki w tym samym przedziale, żadna nie jest trywialna.

| karta | zmiana | dlaczego |
|---|---|---|
| Most Chwaliszewski B | Ciśnienie: **4 znaczniki** zamiast `<per>`+2; Rezygnacja także gdy Lewiatana „nie ma w tej lokacji"; porażka „Cała naprzód" uszkadza barkę tylko przy **różnicy 2+** | największa dźwignia B (8% → 26% samym progiem); okno po odepchnięciu Lewiatana trwało jedną rundę |
| Lewiatan | Wymuszony dostał wyzwalacz: „Gdy Lewiatan atakuje: zamiast badacza atakuje Barkę (dokładnie 2), każdy badacz w lokacji 1 przerażenie" | tekst nie mówił, kiedy atakuje; 2 obrażenia + 2 przerażenia każdemu co rundę wybijało grupę |
| Skażony Nurt | Tkanka: **+1** do testów zamiast +2 | tu grupa stawała (rundy 4–7 w rozgrywce); testy 5–6 przy statystykach 3–5 |
| Toksyczny Kożuch | „test grupowy com(10)" → **jeden badacz com(5), każdy inny deklaruje 1 kartę** | testów grupowych nie ma w zasadach; w modelu 0% |
| Zrujnowany Fort | com(4) → **com(3)** | Dynamit był martwą ścieżką (1%); teraz Miny przez Dynamit 41% w A |
| Karta Scenariusza | „Mutacji" → „Tkanki/Tkanek"; czaszka „minus 1 **(minimum 0)**"; dopisane: **pusta Talia Tkanek → przetasuj odrzucone** | dwa różne teksty na jednej karcie; X = −1 przy zerze Tkanek; talia kończyła się w 5. rundzie |
| Most A / Most B | nagłówek `【Wariant A: Rytuał】` / `【Wariant B: Ucieczka】`; Akt 3: „kartę Mostu wykładacie podczas przygotowania"; domknięty nawias `(->【Z2】)` | dwie karty o tej samej nazwie, nic nie mówiło, którą wyłożyć |
| Kozi Pomiot | **bez zmian tekstu** (2 kopie) | to klon oficjalnego *Goat Spawn* z podstawki — brzmienie zostaje oficjalne, gęstość zmniejszona przez quantity |

**Mroczna fala** — słusznie: to oficjalne polskie tłumaczenie *Surge* z Kompletnej Księgi Zasad („dobierz i rozpatrz dodatkową kartę spotkania"). Zdejmuję z listy braków; Żywy Nurt i Zapach Feromonów są poprawne. Jedyna uwaga: oficjalna pisownia to „Mroczna fala" (mała litera).

### Brakujące karty — propozycje (utworzone jako pliki .card bez ilustracji)

| karta | plik | typ / cechy | koszt · slot · statystyki | tekst |
|---|---|---|---|---|
| **Zapas Paliwa** | Karty Spotkań/scenariusz 2/Zapas Paliwa.card | atut neutralny · Przedmiot, Zapas · grupa spotkań c | – (z poza gry) | `<rea>` Gdy badacz w twojej lokacji wykonuje test ruchu Barką, wyczerp: +1 do testu. Odrzuć: wpłynięcie do Rozlewisk nie kosztuje dodatkowej akcji. Gdy opuści grę: usuń z rozgrywki. |
| **Wdzięczne Żyjątko** | Karty Badaczy/Wdzięczne Żyjątko.card | atut fabularny · Sojusznik, Istota, Fabularny | koszt 2 · Sojusznik · zdrowie 2 / poczytalność 2 · poziom 0 | `<rea>` Gdy wróg z cechą Narośl lub Potwór wchodzi do gry w twojej lokacji, wyczerp: wchodzi wyczerpany. `<rea>` Gdy ujawnisz `<cur>`, wyczerp: traktuj jak 0. Gdy opuści grę: usuń z rozgrywki. |
| **Żebro Lewiatana** | Karty Badaczy/Żebro Lewiatana.card | atut fabularny · Przedmiot, Broń, Relikt, Fabularny | koszt 3 · Ręka · poziom 0 | `<act>` **Walka.** +2 `<com>`; sukces: +1 obrażenie; wróg z cechą Narośl, Potwór lub Rzeka: dodatkowo +1. Gdy opuści grę: usuń z rozgrywki. |

Uzasadnienie: Zapas Paliwa robi dokładnie to, do czego odsyłają Przystań i Rozlewiska, plus mały bonus, żeby nie był martwą kartą. Żyjątko to nagroda za wariant A — soak 2/2 jak Sojusznik za 2 zasoby, zdolność wiąże się z klątwą (motyw kampanii) i Naroślami (scenariusz 3). Żebro to nagroda za B — poziom Machete +1, bo kosztuje most i barkę.

### Otwarte (wymaga twojej decyzji)

- **Mapa Pobrzeży** — nadal brak `location_icon`; model zakłada Dęby↔Zakole, Fabryka↔Skażony Nurt, Fort↔Rozlewiska, Dworzec↔Przystań.
- **Przygotowanie w fabule**: „Odłóżcie na bok Bariery" → „Wyłóżcie Bariery przy lokacjach, które blokują (Łęgi, Rozlewiska, Most)"; dopisać wybór Mostu wraz z wariantem. Nie edytowałem `.docx`.
- **Tajemnica 2 po resecie** — próg 8 ponownie? zagłada z Hierofanty też znika? Model: tak / tak.
- **Rozstawienie „w lokalizacji z Tkanką"** przy kilku takich lokacjach — sugeruję „najbliższej badaczowi, który dobrał kartę".
- **Oślizgła Macka** — tylko w `archiwum/`, brak karty; jeśli archiwum jest martwe, usuń folder.

## Trzecia tura (2026-09-04): skalowanie i porządki — wprowadzone

| karta / plik | zmiana |
|---|---|
| Żyjący Zator | „4 wskazówki" → **1`<per>` wskazówek** |
| Most Chwaliszewski B | Ciśnienie **`<per>`** znaczników; przy wpłynięciu **+1 Ciśnienia za każdą Barierę w Puli Zwycięstwa** (nagroda za przedmioty w B) |
| Nosiciel Zarodników | dołącza Tkankę tylko, gdy w lokacji nie ma żadnej |
| Zapas Paliwa | nowa akcja: odrzuć → spal 1 Tkankę w lokacji (wybór: paliwo na Rozlewiska czy na Tkankę) |
| Skrzynia Dynamitu | 3 obrażenia wrogom, **1** badaczom (było 3) |
| Lewiatan | „Lewiatan nie wraca do lokacji Most Chwaliszewski" |
| Tajemnica 2 | zamiast „+1 trudność na Barce": **Barka otrzymuje 1 uszkodzenie**, zagłada z gry, próg 8 ponownie |
| Karta Scenariusza | zdanie o wyczerpaniu talii spotkań (przetasuj; Kokon i Akt 4A reagują) |
| Fabuła (odt = docx) | Dworzec Puszczykowo przy **Łęgach Wierzbowych** (jedyny węzeł bez Pobrzeża, zamiast martwej Przystani); przy wyborze wariantu: „A to walka z bossem na Moście, B to wyścig z czasem i ucieczka przed Lewiatanem" |
| Rytuał Płodności | **bez zmian** — próba „Nosiciel gotowy i atakuje natychmiast" kosztowała 11 pp w A; martwy wybór zostaje jako niski priorytet |

Przetestowane i odrzucone: Tajemnica 2 z karą 2 uszkodzeń (−4 pp w A), Rytuał z natychmiastowym atakiem (−11 pp).

| graczy | A | B |
|---|---|---|
| 4 | **48%** | **64%** |
| 3 (Tommy, Carolyn, Patel) | 10% | 10% |
| 2 (Tommy, Carolyn) | 17% | 27% |

B przy 4 graczach jest teraz łatwiejsze od A o ~16 pp — głównie przez bonus Ciśnienia za Bariery. Jeśli przy stole B wyjdzie za lekko, pierwszy kandydat do zdjęcia to właśnie ten bonus. 2–3 graczy nadal wyraźnie trudniejsze niż 4 (patrz ocena niżej) — to do testu przy stole.

## Czwarta tura (2026-09-04): ścieżka bojowa i doświadczenie — wprowadzone

Model przeliczony: **wariant A 54,8%, wariant B 61,0%** w kampanii (było 54,8% / 70,8%), przy 0 XP oba po ~44%. Doświadczenie z scenariusza wzrosło z 1–2 do **6–8 PD**.

### Sprostowanie do wcześniejszej oceny Lewiatana

W modelu był błąd: Lewiatan uszkadzał Barkę **także po odepchnięciu w dół rzeki**. Przez to odpychanie wyglądało na bezwartościowe i napisałem, że „nikt by z tego nie skorzystał". Po poprawce ścieżka bojowa okazała się realna — trzeba jej było tylko dać cenę i nagrodę.

### Zmiany na kartach

| karta | zmiana | efekt |
|---|---|---|
| Lewiatan | zdrowie **2`<badacz>`** zamiast 3`<badacz>`; słowo kluczowe **Łowca**; odepchnięcie kładzie **2 znaczniki Ciśnienia**; usunięte „nie wraca do lokacji Most Chwaliszewski" | odepchnięcie używane w **64% zwycięstw** wariantu B, ale nieobowiązkowe |
| Most Chwaliszewski B | próg Rezygnacji **`<badacz>`+1**; usunięty bonus Ciśnienia za Bariery w Puli Zwycięstwa | bonus dawał wariantowi B 10 pp przewagi nad A |
| Zmutowany Kierownik | **Zwycięstwo 1** | zdejmowany w 81–98% partii, dotąd bez nagrody |
| Arcykapłan Odrodzonej Warty | **Zwycięstwo 2** | pokonanie bossa dotąd nie dawało XP |
| Fabuła, Rozwiązanie 1a | +2 PD za ukończenie scenariusza | scenariusz nie miał żadnej premii za przetrwanie |
| Fabuła, Rozwiązanie 1b | +2 PD za ukończenie + 2 PD za strącenie Lewiatana | wyrównuje wypłatę obu ścieżek |
| Żyjący Zator, Toksyczny Kożuch, Pruskie Miny | dopisek „Podczas przygotowania wyłóżcie tę kartę w grze przy lokacji… Ta karta nie trafia do talii spotkań" | Bariery to podstępy, które nigdy nie wchodzą do talii |
| Tajemnica 2 | doprecyzowany reset: zagłada z Hierofanty też znika, próg 8 obowiązuje od nowa, test powtarza się przy każdym osiągnięciu | |
| Zakole Warty | dopisana brakująca grupa spotkań (`c`) | |
| 9 kart | ujednolicona nazwa **Barka Jadwiga** (bez cudzysłowów) | zgodnie z polem `name` karty |

### Dlaczego akurat te liczby

Ścieżka Ciśnienia to 4–5 udanych testów, czyli ~6 akcji rozłożonych na grupę. Odepchnięcie przy 3`<badacz>` = 12 obrażeń to ~8–9 akcji jednego wojownika i było ściśle gorsze. Przy 2`<badacz>` = 8 obrażeń i nagrodzie 2 Ciśnienia obie drogi kosztują podobnie.

| konfiguracja (4 graczy, 5 XP) | wygrane B | odepchnięć/partię | zwycięstw z odepchnięciem |
|---|---|---|---|
| dzisiejszy tekst (przed zmianą) | 78,3% | 0,20 | 27% |
| samo usunięcie bonusu za Bariery | 68,5% | 0,28 | 40% |
| **wprowadzone: HP 2`<per>`, push 2, próg `<per>`+1, Łowca** | **69,9%** | **0,46** | **64%** |
| jw. bez Łowcy (odepchnięty znika na stałe) | 77,7% | 0,37 | 47% |
| jw. z progiem 6 | 62,7% | 0,51 | 79% |

Wariant A dla odniesienia: 69,3%. Przy 2 graczach zmiana poprawia też skalowanie wariantu B: 19,8% → 25,4%.

### Co to daje kampanii

| | przed czwartą turą | po |
|---|---|---|
| XP po scenariuszu 2 (wariant A) | 6,3 | **9,2** |
| XP po scenariuszu 2 (wariant B) | 5,3 | **8,7** |
| XP wchodząc do scenariusza 3 | 5,7–6,3 | **9,2–9,6** |
| Pełna kampania 3/3 | 0,0–0,2% | **0,5–1,5%** |

Kampania nadal rozbija się o scenariusz 3 — tam nic nie zmienialiśmy.

## Ocena balansu i grywalności — stan po zmianach

**4 graczy (1000 gier/wariant): A 52%, B 53%.** Obie ścieżki w tym samym przedziale, mediana 12 / 8 rund, żadna nie kończy się przez zegar. To jest przedział, w którym siedzą oficjalne scenariusze na Standardzie. W A przegrywa się przez wybicie grupy (39%), w B przez zatopienie barki na Moście (38%) — czyli każdy wariant ma swój własny, czytelny sposób przegrania. Dobrze.

**2–3 graczy: A 14–17%, B 1–7%.** Tu scenariusz się nie skaluje. Trzy rzeczy są stałe, a powinny iść z `<per>`:

| element | teraz | propozycja | efekt w modelu (2 graczy) |
|---|---|---|---|
| Żyjący Zator: „wydajcie 4 wskazówki" | 4 (stałe) | **1`<per>`** wskazówek — przy 4 graczach bez zmian, przy 2 to 2 | +1 pp; przy 2 graczach 4 wskazówki to dwie całe lokacje |
| Most B: Ciśnienie | 4 (stałe) | **`<per>`** znaczników (2p: 2, 3p: 3, 4p: 4) | B 1% → 7% |
| Talia Tkanek + źródła Tkanek | 8 kart, 5 źródeł niezależnych od liczby graczy | `<per>` przy „dołącz Tkankę" nie ma sensu — zamiast tego: **Nosiciel Zarodników dołącza Tkankę tylko, gdy w lokacji nie ma żadnej** | model: 6,8 Tkanki/grę przy 2 graczach, którzy mają 6 akcji na rundę na wszystko |

Nawet po tych zmianach 2 graczy zostaje przy ~17% / ~7%. Reszta różnicy to coś, czego model nie łapie dobrze: przy 2 badaczach jedyny wojownik zabija ~1 wroga na rundę przy ~1 nowym na rundę i nie robi nic innego; prawdziwe talie mają na to odpowiedzi (Dynamite Blast, sojusznicy-tarcze, Unik + ucieczka barką), których profil liczbowy nie ma. **Wniosek: 4 graczy jest zbalansowane w modelu; 2 graczy trzeba przetestować przy stole, a trzy zmiany `<per>` powyżej są tanie i idiomatyczne, więc warto je wpisać niezależnie od wyniku.**

### Co dodać

- **Sposób na Tkanki poza testami.** Każda Tkanka to test 3–4 albo (Korzenie) 2 zasoby. Brakuje karty gracza/atutu fabularnego, który usuwa Tkankę bez testu — np. Zapas Paliwa mógłby dostać „odrzuć: spal Tkankę w twojej lokacji". Daje decyzję: paliwo na Rozlewiska czy na Tkankę.
- **Nagrodę za Bariery usunięte przedmiotem** w wariancie B. W A każda Bariera w grze to +1/+1 Arcykapłana, więc przedmioty mają sens; w B jedyną motywacją jest „taniej". Propozycja: w B Most B „za każdą Barierę w Puli Zwycięstwa Cisnienie zaczyna od +1".
- **Jeden przeciwnik nie-Narośl / nie-Potwór.** Faustyn, Totem, Żyjątko, Żebro — wszystkie nagrody premiują walkę z Naroślą/Potworem, a talia ma 7 wrogów, z których 6 ma te cechy. Bez kontrastu premie nie są wyborem. Hierofanta (Kultysta) mógłby zostać drugą osią: „Pertraktacje" zamiast walki — już to ma, ale 1 kopia ginie w talii.
- **Tekst „co gdy talia spotkań się wyczerpie" na Karcie Scenariusza** — Kokon i Akt 4A reagują na to zdarzenie, a przy 4 graczach zdarza się co 5 rund; gracze powinni to widzieć.

### Co usunąć albo uprościć

- **Rytuał Płodności (×2)**: opcja „odrzuć 5 kart → Tkanka za każdy atut/wydarzenie" jest zawsze gorsza niż „Nosiciel w zwarciu" — w modelu nikt jej nie wybiera; przy stole też nikt nie wybierze 2–3 Tkanek zamiast jednego wroga 3 hp. Albo wzmocnić opcję B (Nosiciel wchodzi **gotowy, w zwarciu, i atakuje**), albo zamienić na zwykłą kartę „dołącz Tkankę".
- **Skrzynia Dynamitu zadaje 3 każdemu badaczowi w lokacji** — po zmianie Fortu na com(3) Dynamit jest brany w 36% partii A, ale użycie go w walce prawie nigdy się nie opłaca (własna grupa obrywa). Zostawić tylko jako klucz do Min, albo „3 obrażenia każdemu wrogowi, 1 każdemu badaczowi".
- **Tajemnica 2 z resetem** — jedyna karta, której zasady trzeba tłumaczyć; w modelu wypada 1,4×/grę i prawie nigdy nie prowadzi do Tajemnicy 3 (0,6%). Prostsze: „Jeśli Barka ma 4+ uszkodzeń → Tajemnica 3; w przeciwnym razie Barka otrzymuje 2 uszkodzenia i usuńcie zagładę" — kara, którą widać, zamiast +1 trudności, o którym wszyscy zapomną.
- **Dworzec Puszczykowo** — przy Przystani, gdzie nikt nie wraca; w modelu odwiedzany 0×. Albo przenieść na Łęgi (jedyny węzeł bez Pobrzeża), albo usunąć.

### Grywalność przy stole (poza liczbami)

- Z rozgrywki narracyjnej: **rundy 1–3 są dobre** — barka płynie, Zator za wskazówki daje poczucie postępu, Tkanki wchodzą stopniowo. **Rundy 4–7 były jedną lokacją** (Skażony Nurt) — po zmianie +2→+1 i Kożuchu com(5) powinno być krócej, ale to miejsce nadal warto obserwować przy stole.
- Lewiatan po odepchnięciu **wraca?** Nie ma Łowcy, więc nie — ale gracze będą pytać. Jedno zdanie na karcie: „Lewiatan nie wraca na Most".
- Wariant wybierany przed grą to dobra decyzja fabularna, ale gracze nie wiedzą, czym się różnią mechanicznie. Jedno zdanie w fabule: „A: walka z bossem, B: wyścig na czas".

## Kompletność

| waga | plik | problem |
|---|---|---|
| OK | Karty Scenariusza/scenariusz 2/Tajemnica 1.card | **Poprawione przez autora** — rozstawia Rzeczne Młode. |
| BŁĄD | Fabuła/Kampania Czarna Krew Warty (Przygotowanie) | „Odłóżcie na bok wszystkie karty z cechą Bariera" — a wg autora Bariery leżą od początku przy lokacjach. Przygotowanie mówi coś innego, niż gra ma robić: dopisać „wprowadźcie Bariery do gry przy lokacjach, które blokują". |
| BLOKER | Fabuła / Karty Lokacji/scenariusz 2 | „Rozłóżcie lokacje Pobrzeży po lewej i prawej stronie odpowiednich lokacji rzecznych zgodnie z mapą powiązań" — **mapy nie ma w repo**, a żadna lokacja nie ma `location_icon`. Nie wiadomo, gdzie leży Fabryka, Fort, Dęby i Dworzec. |
| OK | Karty Lokacji/scenariusz 2/Most Chwaliszewski A/B | Akt 3 mówi „Wariant A → Akt 4a (A)", ale **nic nie mówi, którą kartę Mostu wystawić** w którym wariancie. Obie nazywają się tak samo. | **→ załatwione w drugiej turze.**
| OK | Przystań.card, Rozlewiska Dębiny.card (+ archiwum) | atut **Zapas Paliwa** „(z poza gry)" — brak karty. Rozlewiska bez niego kosztują +1 akcję zawsze. | **→ załatwione w drugiej turze.**
| OK | Fabuła (Rozwiązania 1a, 1b) | atuty fabularne **Wdzięczne Żyjątko** i **Żebro Lewiatana** — brak kart. | **→ załatwione w drugiej turze.**
| OK | Karta Scenariusza.card | `body` mówi „kart **Mutacji**", „Talii **Mutacji**", a pola `scenario_card.*` mówią „Tkanki" — dwa różne teksty na jednej karcie. | **→ załatwione w drugiej turze.**
| OK | Karty Barier/Toksyczny Kożuch.card | „Jako grupa wykonajcie test com(10)" — **w AH LCG nie ma testów grupowych**. Kto testuje, kto deklaruje karty, czy statystyki się sumują? | **→ załatwione w drugiej turze.**
| OK | Żywy Nurt.card, Zapach Feromonów.card | słowo kluczowe **Mroczna Fala** nie jest zdefiniowane na żadnej karcie ani w fabule. | **→ załatwione w drugiej turze.**
| OK | Lewiatan.card | „`<for>` Lewiatan atakuje każdego badacza w swojej lokalizacji ORAZ zadaje 2 obrażenia Barce" — **Wymuszony bez wyzwalacza** (kiedy? co fazę wrogów? zamiast zwykłego ataku?). | **→ załatwione w drugiej turze.**
| OK | Most Chwaliszewski B.card / Lewiatan.card | Rezygnacja wymaga „Lewiatan jest wyczerpany", a odepchnięty Lewiatan gotowieje w najbliższym utrzymaniu i nie ma Łowcy — okno na ucieczkę to jedna runda, o czym karty nie mówią. | **→ załatwione w drugiej turze.**
| BŁĄD | Tajemnica 2.card | Po „resecie" karta zostaje z progiem 8: czy zagłada z Hierofanty też znika? czy przy kolejnym 8 znów sprawdza uszkodzenia barki? Nieopisane. |
| OK | Most Chwaliszewski A.card | `(->【Z2)` — niedomknięty nawias. | **→ załatwione w drugiej turze.**
| OK | Karty Tkanek (8) | Talia Tkanek ma 8 kart; przy 4 graczach kończy się w 5. rundzie (rozgrywka: dokładnie tak). Co wtedy? Karty milczą. | **→ załatwione w drugiej turze.**
| SPÓJNOŚĆ | Nosiciel Zarodników, Rzeczne Młode | „Rozstawienie: w lokalizacji z kartą Tkanki" — gdy takich lokacji jest kilka, kto wybiera? |

## Balans A vs B (Monte Carlo, 2000 gier na wariant)

| miara | A — Przerwać Rytuał | B — Ostatni Zryw |
|---|---|---|
| wygrane | **12,2%** | **5,6%** |
| mediana rund | 11 | 7 |
| porażka: wszyscy badacze pokonani | 76% | 31% |
| porażka: barka zatopiona | 10% | **63%** |
| porażka: zagłada (Tajemnica 3) | 1,5% | 0,3% |
| obrażenia / przerażenie na badacza | 7,8 / 7,1 | 6,5 / 5,4 |
| Żyjący Zator | Totem 52% · wskazówki ~0% | wskazówki 93% |
| Toksyczny Kożuch | Ferment 27% · test grupowy 0% | Ferment 69% · test grupowy 0% |
| Pruskie Miny | agi(4) 21% · Dynamit 1% | agi(4) 64% · Dynamit 0,5% |

Odsetki barier liczą się od wszystkich gier — reszta partii kończy się, zanim barka tam dopłynie.

### Za trudne

- **Gęstość wrogów.** 14/26 kart talii to przeciwnicy (Pomiot ×4, Nosiciel ×3, Młode ×3, Hierofanta ×2 + Rytuał ×2 rozstawia Nosiciela). Przy 4 kartach na rundę to ~2,2 wroga/rundę po 3 zdrowia. Jeden pełny wojownik z bronią zabija ~1,5/rundę i nie robi nic innego. Stąd 76% porażek w A to wybicie grupy, nie zegar.
- **Kozi Pomiot ×4 + Mściwy + Łowca.** Każde pokonanie = 1 przerażenie dla **każdego** badacza w lokacji. Cztery kopie = do 4 przerażenia całej grupie tylko za sprzątanie. W rozgrywce Carolyn (poczytalność 9) miała 6 przerażenia w 6. rundzie.
- **Hierofanta ×2** kładzie zagładę co fazę Mitów. Z progiem 6 Tajemnicy 1 to awans w 2–3 rundy (w rozgrywce: runda 2). Tajemnica 1 przy awansie uszkadza barkę i… odsyła do nieistniejącego Topielca.
- **Skażony Nurt z Tkanką: +2 do wszystkich testów.** Przy 4 graczach Tkanka tam ląduje niemal zawsze (Nosiciel przy pokonaniu, Żywy Nurt, kultysta z worka). Testy 5–6 przy statystykach 3–5 = 20–40%. To tu grupa staje. W rozgrywce: rundy 4–7 bez postępu.
- **Wariant B — Lewiatan.** Atak 5, 12 zdrowia, 2 obrażenia + 2 przerażenia każdemu co rundę + 2 barce, a barka ma 8 i przypływa już uszkodzona. Ciśnienie 6 przy wil(4)/com(4) to 22–57% na test → ~12 akcji, czyli 3+ rundy pod ostrzałem. 63% partii tonie.
- **Wariant A — Arcykapłan +1/+1 za każdą Barierę w grze.** Bariery ominięte drogą alternatywną zostają w grze → atak 5–6. Trafialny tylko po zdobyciu przedmiotów. Dlatego A wygrywa tylko wtedy, gdy Totem, Ferment i Dynamit są zdobyte (52% / 27% / 1%).

### Martwe

- **Test grupowy com(10)** na Kożuchu — 0% w symulacji, brak zasad w grze. Ferment to jedyna realna droga.
- **Skrzynia Dynamitu** — Fort wymaga com(4) w lokacji z cechą Ruiny obok Rozlewisk; Patel z agi 5 przechodzi Miny taniej (agi 4). 1% użycia.
- **Zwęglony Totem** poza wariantem A — 8 wskazówek przy zasłonie 4 vs 4 wskazówki w Zakolu przy zasłonie 3.
- **Zagłada jako zegar** — 1,5% porażek. 24 punkty przy 5 ruchach barki to luz; Tajemnica 2 dodatkowo resetuje. Presja zegara jest wyłącznie przez Tajemnicę 1 → uszkodzenie barki.

### Za łatwe

- **Żyjący Zator.** 4 wskazówki w Zakolu (1 na badacza, zasłona 3) to 1–2 rundy. Bariera „zostaje w grze", ale w B nic z tego nie wynika.

## Rozgrywka narracyjna (seed 7, wariant B)

Talia spotkań od góry: Rozrost, Hierofanta, Nosiciel, Twarze | Dar, Rozkwit, Młode, Rozkwit | Rozrost, Twarze, Pomiot, Dar | Rytuał, Rytuał, Feromony, Nosiciel | Młode, Nurt, Młode, Nosiciel | Nurt, Pomiot, Pomiot, Feromony | Hierofanta, Pomiot. Tkanki: Błona, Gąbczasta, Kokon, Grzybnia, Oczy, Pnącza, Korzenie, Splot. Żetony w kolejności z `table --seed 7`.

| runda | co się stało |
|---|---|
| 1 | Rozrost dołącza **Śluzowatą Błonę do lokacji startowej** — nikt nie może wystawić atutów startowych. Hierofanta i Nosiciel na Przystani. Tommy bez broni obija Hierofantę, Patel omija Nosiciela i **przepływa barką do Zakola** (agi 5 vs 3). Grupa zbiera 5 wskazówek. |
| 2 | Dar Czarnej Kozy (porażka) + kultysta z worka: **dwie Tkanki w Zakolu** (Gąbczasta, Kokon) + zagłada. Rozkwit ×2. **Tajemnica 1 awansuje w rundzie 2** (Hierofanta) — barka −1, Topielec z Warty **nie istnieje**. Młode rozstawione przy Tkance. Grupa wydaje 4 wskazówki na **Żyjący Zator** → Łęgi. |
| 3 | Rozrost + kultysta + Dar: **trzy Tkanki w Łęgach** (Grzybnia, Oczy, Pnącza), Pomiot w zwarciu. Tommy dobija Pomiota → **cała grupa +1 przerażenia**. Patel przepływa do Skażonego Nurtu → **Akt 1 zaliczony**. |
| 4 | Rytuał ×2 → dwóch Nosicieli w zwarciu z Tommym i Carolyn. Feromony ściągają Pomiota #1 i przesuwają resztę wrogów w stronę barki. Tommy zabija Nosiciela → **Korzenie na Skażonym Nurcie: +2 do wszystkich testów**. Carolyn nie omija Nosiciela dwa razy (test 4). Kożuch przed nami: test grupowy nie ma zasad, Ferment wymaga zabicia Kierownika (6 zdrowia, atak 4) na Fabryce. |
| 5 | **Tajemnica 2 osiąga 8** — testy zręczności, dwie porażki; barka ma 1 uszkodzenie → reset zagłady, +1 trudność na barce. Żywy Nurt dołącza Splot → **talia Tkanek pusta**. Trzy nowe wrogi (Młode ×2, Nosiciel) rozstawiają się przy Tkankach na Przystani. Tommy 3 razy chybia (test 5), Marie zabija Nosiciela zaklęciem. |
| 6 | Żywy Nurt: 2 obrażenia Tommy'emu (7/9). Pomiot ×2 w zwarciu. Feromony ściągają całą menażerię z Przystani i Zakola w naszą stronę. Marie dobija Pomiota #1 → **znów +1 przerażenia wszystkim**. |
| 7 | Hierofanta #2 w zwarciu z Tommym (1 zdrowia). Pomiot #4 na Carolyn (już 4/6 obrażeń, 6/9 przerażenia). **Talia spotkań wyczerpana → Kokon w Zakolu rozstawia kolejnego wroga.** Grupa nie ma jak przejść Kożucha ani przeżyć fazy wrogów. Koniec: barka przy Skażonym Nurcie, Akt 2 z 4, wszyscy badacze ranni, Tommy i Carolyn spadają w rundzie 8. |

Zgodne z symulacją: mediana 7 rund, porażka przez wybicie grupy, barka nigdy nie dopłynęła do Mostu.

### Pytania do autora (z rozgrywki)

1. **Kiedy Bariery wchodzą do gry?** Przygotowanie każe je odłożyć na bok i nic więcej.
2. **Skąd bierze się Lewiatan?** „Przyzwij Lewiatana" — jest odłożony? w talii? Przygotowanie odkłada tylko Arcykapłana i Bariery.
3. **Test grupowy com(10)** na Kożuchu — jaka mechanika?
4. **Czaszka −X, X = Tkanki − 1**: przy zerze Tkanek X = −1. Czaszka daje +1?
5. **Żyjący Zator**: przeniesienie barki za 4 wskazówki — czy barka się wyczerpuje? czy to „ruch barką" (liczy się do +1 akcji w Rozlewiskach / przy Tkance w Zakolu)?
6. **Mięsne Pnącza** „akcja Ruch" — dotyczy ruchu barką (to aktywacja atutu, nie akcja Ruchu)?
7. **Rozstawienie „w lokalizacji z Tkanką"** przy kilku takich lokacjach — kto wybiera?
8. **Talia Tkanek pusta** (runda 5 przy 4 graczach) — co wtedy z „dobierz z Talii Tkanek"?
9. **Śluzowata Błona w lokacji startowej w rundzie 1** blokuje wystawienie atutów startowych — zamierzone?
10. **Tajemnica 2 po resecie** — próg znowu 8? zagłada z Hierofanty też znika?
11. **Lewiatan**: kiedy wykonuje atak na wszystkich? Czy odepchnięty (gotowy w utrzymaniu) liczy się jako „wyczerpany" dla Rezygnacji?
12. **Mroczna Fala** — co robi?
13. **Który Most** w którym wariancie?

## Założenia modelu (uproszczenia)

Model to nie silnik zasad — liczby to kierunek i rząd wielkości.

- Worek chaosu: **Standard** (+1, 0, 0, −1, −1, −1, −2, −2, 💀💀, 👤, 📜, 🐙, ⭐); Starszy Znak = +1; czaszka przy zerze Tkanek = 0.
- Pobrzeża przypisane tak, by przedmiot był osiągalny **przed** barierą: Dworzec ↔ Przystań, Dęby ↔ Zakole, Fabryka ↔ Skażony Nurt, Fort ↔ Rozlewiska. Bariery w grze od początku.
- Badacze z arkhamdb: Marie Lambeau (Mistyk, #64502), Carolyn Fern (Poszukiwacz, #64388), André Patel (Włóczęga, #64503), Tommy Muldoon (Obrońca, #62530). Talia = profil liczbowy: średnie ikony na kartę deklarowane tylko gdy przewaga < 2, 1 karta na test, +1 karta na rundę; broń/zaklęcie w grze = +1 do umiejętności walki (mistyk walczy wolą); narzędzia poszukiwacza = +1 intelekt; każdy sojusznik = +1 zdrowia i +1 poczytalności; leczenie 1 pkt/rundę z prawdopodobieństwem udziału kart leczących.
- Efekty spotkań skrócone: Rytuał Płodności = zawsze Nosiciel; Zapach Feromonów (porażka) = 1 obrażenie; zagłada z Daru liczy się do tajemnicy; Topielec z Warty pominięty (brak karty); Tajemnica 2 po resecie: próg 8, +1 trudność na barce.
- Kożuch: „test grupowy" = suma walki grupy + po 1 karcie; raz na rundę. Ferment: zawsze stać na 1 zasób. Zator za wskazówki: bariera zostaje w grze (liczy się Arcykapłanowi).
- Lewiatan: atak na wszystkich co fazę wrogów; po odepchnięciu liczy się jako „wyczerpany" dla Rezygnacji.
- Polityka graczy: walka/unik wg statystyk → cel wariantu na Moście → zdjąć Tkankę z lokacji barki → przedmiot na najbliższą barierę (A: wszystkie, B: tańsza droga) → ruch barką raz na rundę → wskazówki → odpoczynek. Pierwszy badacz w kolejności = najlepszy wojownik.
- Nie modelowane: konkretne karty gracza, ataki okazyjne, zasoby, przetasowanie stosu odrzuconych Tkanek, Kokon, wpływ Barier na ruch po Pobrzeżach.

Pliki: `tools/scenario2_model.py` (`tempo`, `sim`, `table`), `tools/arkhamdb.py` (talie), `.cache/sim_scenariusz2_A.json`, `.cache/sim_scenariusz2_B.json`, `.cache/table_scenariusz2.json` (seed 7).
