# Playtest: Scenariusze 1 i 3

2026-09-04 · 4 badaczy · talie 0 XP z arkhamdb · worek Standard · **raport, bez zmian w kartach**

## Werdykt

**Scenariusz 1 „Wioska wśród drzew"** — model daje **84% wygranych** przy medianie **7 rund**. To nie jest scenariusz za łatwy w walce (16% partii kończy się wybiciem grupy), tylko scenariusz **bez zegara**: tajemnice mają razem 25 zagłady przy tempie 1/rundę, więc gra kończy się w 7. rundzie, a **tajemnica 3 i 4 nigdy nie wchodzą do gry** (na 400 partii: 45% kończy na tajemnicy 1, 55% na tajemnicy 2, 0% dalej). Cała eskalacja zaprojektowana na rewersach tajemnic — Kozi Pomiot, drugie wejście Kultysty Traktorzysty, Brama z Gałęzi — to **martwa treść, której gracze nie zobaczą**. Do tego Akt 1 nie ma jak postąpić: jedyna ścieżka prowadzi przez przedmiot **Klucz do zachrystii, którego nie ma w repo**.

**Scenariusz 3 „Czarny Port"** — model daje **0% wygranych**; 77% partii kończy się zakleszczeniem, 15% wybiciem grupy, 8% zagładą. Powód jest jeden i policzalny: **Goniec ma 2`<per>` zdrowia (8 przy 4 graczach) i zrzuca na lokację tyle zagłady, ile zostało mu punktów wytrzymałości**, a lokacja spacza się przy **4**. Jeden Goniec, który dojdzie do celu nietknięty, natychmiast spacza lokację z dwukrotnym zapasem — a wskazówki na spaczonej lokacji **zamieniają się w zagładę**. W śledzonej partii Cytadela i UAM były spaczone w **2. rundzie**, Mleczarnia w 6., Akt 1 zaliczono w 10., grupa padła w 17. Odzyskiwanie idzie testem `<wil>`(3) po ~1 żetonie, więc arytmetyka nie domyka się nigdy. Dodatkowo **Czarna Koza z Ostrowa — cel Aktu 6 — nie istnieje jako karta**.

Krótko: scenariusz 1 wymaga zegara i uzupełnienia jednej karty; scenariusz 3 wymaga przeliczenia zagłady na lokacjach i dopisania bossa, zanim w ogóle da się mówić o balansie.

## Metoda

Ten sam warsztat co przy scenariuszu 2: `tools/scenario13_model.py` (tempo + Monte Carlo), profile 4 talii 0 XP z arkhamdb (Marie Lambeau, Carolyn Fern, André Patel, Tommy Muldoon), worek Standard, po 1000 partii na scenariusz. Model **nie jest silnikiem zasad** — talie graczy to liczby, efekty spotkań są skrócone, polityka graczy to lista priorytetów. Liczby traktuj jako rząd wielkości, nie wynik do promila. Pełna lista uproszczeń na końcu.

Nic w kartach nie zostało zmienione.

---

# Scenariusz 1: „Wioska wśród drzew"

## Kompletność

| waga | plik / miejsce | problem |
|---|---|---|
| BLOKER | Zachrystia.card + Kościół.card | Jedyna ścieżka postępu Aktu 1 → 2 prowadzi przez przedmiot **Klucz do zachrystii** („dobierz odłożony na bok przedmiot Klucz do zachrystii"). **Karty nie ma w repo.** Bez niej Akt 1 nie ma jak postąpić — jego treść to samo „Zdobądź poszlaki na temat sytuacji w tej wiosce", bez progu wskazówek. |
| BLOKER | Skraj Lasu.card | `<act>Jako grupa wydaj 3B wskazówek żeby spowodować postęp talii aktów` — **`3B` to literówka**, zapewne `3<badacz>`. To druga (i po Akcie 1 jedyna) droga postępu aktów, więc próg jest nieczytelny. |
| BLOKER | Obóz na Mokradłach.card | „Rozstaw w tej lokalizacji odłożonego na bok **Czempiona Koziegłowych**" — karty nie ma w repo. |
| BŁĄD | Ojciec Żerdź.card | Boss ma `enemy_damage` **puste** — zadaje 0 obrażeń, tylko 1 przerażenie. Przy 3`<per>` = 12 zdrowia to przeciwnik, który nie może nikogo pokonać inaczej niż przez poczytalność. |
| BŁĄD | Tajemnica 1 / Tajemnica 2 | Obie każą wtasować **Bramę z gałęzi i Kultystę Traktorzystę**; Tajemnica 3 wtasowuje Traktorzystę po raz trzeci. Kopii jest odpowiednio 2 i **1**. Nie wiadomo, co robić przy drugim i trzecim poleceniu. |
| BŁĄD | Tajemnica 1 vs Nieczysta Komunia | Tajemnica mówi o **„odłożonym na bok"** Przekonanym wyznawcy, a Nieczysta Komunia każe go **„przeszukać w talii spotkań"**. Karta jest albo w talii, albo obok — dwie karty mówią co innego, a od tego zależy skład talii startowej (13 vs 8 kart). |
| BŁĄD | Przygotowanie (fabuła) | Nie mówi, które karty spotkań są odkładane na bok. Wynika to dopiero z rewersów tajemnic. Trzeba dopisać listę. |
| BŁĄD | Grzęzawisko.card | `<for> jeśli nie zdasz dowolnego testu <agi>/<com> w tej lokalizacji` — brak trudności to tu akurat poprawne (warunek, nie test), ale pole `clues` ma wartość **`2 <badacz>`** ze spacją, inaczej niż na wszystkich pozostałych kartach. |
| SPÓJNOŚĆ | 9 lokacji wioski | Zasłona i wskazówki **niewypełnione** (`?` po obu stronach): Kapliczka, Kostnica, Pod Rogatym, Skład Drewna, Stary magazyn, Targ Rybny, oba Warsztaty Kowalskie, Warsztat Kołodzieja, Wędzarnio-suszarnia. Bez nich nie da się grać ani policzyć tempa (model przyjął zasłonę 2 i 1`<per>`). |
| SPÓJNOŚĆ | grupy spotkań | Trzy różne nazwy w jednym scenariuszu: „Ciemne chaty, puste pola", „Mroczne sprawki", „g" — a Kozi Pomiot nie ma żadnej. Podobnie lokacje: „Wioska wśród drzew" vs „Wioska pośród drzew" vs „Miejsca zwyczajne" vs „Zwyczajne miejsca". |
| SPÓJNOŚĆ | Warsztat Kowalski | Dwa pliki, ta sama nazwa i numer 9, **różne zdolności** (`9 Warsztat Kowalski.card` vs `Warsztat Kowalski 9.card`). Jedna wersja jest nieaktualna. |
| SPÓJNOŚĆ | mapa | Żadna z 26 lokacji nie ma `location_icon`, a w połączeniach występują 4 symbole. Przygotowanie odsyła do „schematu z instrukcji", którego w repo nie ma. |

## Balans (1000 partii, 4 graczy)

| miara | wynik |
|---|---|
| wygrane (Żyrij pokonany) | **84%** |
| porażka: wybicie grupy | 16% |
| porażka: zagłada | **0%** |
| mediana rund | 7 (maks. 12) |
| obrażenia / przerażenie na badacza | 3,5 / 5,2 |
| osiągnięta tajemnica | 1: 45% · 2: 55% · **3 i 4: 0%** |

### Za łatwe

- **Zegar nie istnieje.** 7 + 7 + 7 + 4 = 25 zagłady przy 1/rundę i braku innych źródeł zagłady w talii = 25 rund. Gra trwa 7. Tajemnica 4 („Tryumf Kozicy", przegrana) jest nieosiągalna.
- **Skutek:** wszystko, co tajemnice wnoszą do gry — Brama z Gałęzi, Kultysta Traktorzysta, Kozi Pomiot ×2, konwersje Ciekawskich na Wyznawców — pojawia się rzadko albo wcale. Talia spotkań przez większość partii to te same 13 kart.
- **Żyrij Żerdź** przy zerowych obrażeniach i 12 zdrowia jest workiem treningowym: grupa z jednym wojownikiem zdejmuje go w 4–6 udanych ataków, ryzykując tylko przerażenie.

### Za trudne

- **Talia startowa to 12 wrogów na 13 kart (92%).** Przy 4 graczach wyczerpuje się po ~3 rundach, więc ci sami wrogowie wracają dwa–trzy razy w jednej partii. Stąd 16% wybić mimo braku zegara.
- **Przekonany wyznawca ×5**: Łowca, Polowanie na badacza z największą liczbą wskazówek, 3/3/3, 1 obrażenie i 1 przerażenie. Pięć kopii poluje na tę samą osobę — badacza od wskazówek. Carolyn (poczytalność 9, walka 1) nie ma na to odpowiedzi.
- **Trudność 3 dla wszystkich testów spotkań** przy statystykach 2–5 daje 0–86% zależnie od badacza; Nieczysty Chrzest (`<com>`(3)) przechodzi u Carolyn w **0%** przypadków.

### Martwe

- **Tajemnice 3 i 4** — nigdy nie widziane.
- **Kozi Pomiot ×2** — wchodzi dopiero z tajemnicą 3.
- **Brama z Gałęzi ×2** — cztery alternatywne warunki przejścia, z których pierwszy („Skład Drewna nie ma wskazówek") zwykle jest spełniony od ręki; karta blokuje przejście średnio przez pół rundy.
- **Zbłąkany Kultywator ×2** — Powściągliwy, 1/5/1, buffuje sąsiadów o +1`<com>`/+1`<agi>`. Nikt go nie atakuje (5 zdrowia za brak nagrody), więc bufuje bezkarnie — ale że wrogowie i tak nie są problemem, efekt jest niezauważalny.

### Co bym zmienił (propozycje, nie wprowadzone)

1. **Skrócić zegar do ~12–14 zagłady** (np. 4 / 4 / 3 / 3) albo dodać źródła zagłady do talii spotkań. Bez tego trzy czwarte projektu tajemnic jest niewidoczne. To jedna zmiana, która robi najwięcej.
2. **Żyrij: wpisać obrażenia** (proponuję 2) i rozważyć „Łowca" — teraz można go bezkarnie ignorować.
3. **Rozrzedzić talię startową**: Ciekawski ×5 i Przekonany ×5 to za dużo jak na 13 kart. Ciekawski ×4, Przekonany ×3, plus 2–3 podstępy z tajemnicy 1 przeniesione do talii startowej.
4. **Wypełnić zasłonę i wskazówki na 9 lokacjach wioski**, ujednolicić nazwy grup spotkań i usunąć duplikat Warsztatu Kowalskiego.
5. **Dodać Klucz do zachrystii i Czempiona Koziegłowych**, poprawić `3B` → `3<badacz>`.

---

# Scenariusz 3: „Czarny Port"

## Kompletność

| waga | plik / miejsce | problem |
|---|---|---|
| BLOKER | Akt 6.card | Cel: „Pokonaj **Czarną Kozę z Ostrowa**". **Karty nie ma w repo** — scenariusza nie da się wygrać. |
| BLOKER | Przygotowanie (fabuła) | Odkłada na bok lokację **Stary Fort Pruski** („zostanie wprowadzona w kulminacyjnym momencie") — karty nie ma; **nic jej też nie wprowadza**. Akt 5 każe „dostać się do fortu na Cytadeli", a Tunele Forteczne są „niedostępne, chyba że wynika to z karty scenariusza" — i żadna karta tego nie odblokowuje. |
| BLOKER | Akt 3.card i Akt 4.card | **Identyczny cel**: „Usuń wszystkie wskazówki z lokalizacji Mleczarnia". Po zaliczeniu Aktu 3 Akt 4 jest natychmiast spełniony (albo nie da się go spełnić drugi raz). |
| BŁĄD | Przygotowanie (fabuła) | Wymienia **Szpital Kliniczny** wśród lokacji do rozłożenia — karty nie ma. Odsyła też do „mapy powiązań kampanii", której nie ma. |
| BŁĄD | Goniec 1/2/3 | Trzy karty o **tej samej nazwie** „Goniec" i różnych celach patrolu (Mleczarnia, UAM, Cytadela) — w grze nie da się ich odróżnić. Do tego Goniec 3 ma 3`<per>` zdrowia, a pozostałe 2`<per>`. |
| BŁĄD | Czarna Sadza, Smród z Garbar, Trauma Pruskiego Drylu | To **podstępy z wypełnionymi statystykami wroga** (atak 3, zdrowie 2`<per>`, unik 3, obrażenia 1). Wyrenderują się z paskami walki jak przeciwnicy. |
| BŁĄD | 10 lokacji | Zasłona i wskazówki na rewersie **`-`** (niewypełnione): Mleczarnia, Nadbrzeże, Ogród Botaniczny, Ostrów Tumski, Rynek Jeżycki, Sołacz, Stary Rynek, Tunele Forteczne, UAM, Zakłady Cegielskiego. |
| BŁĄD | Cień z Jeżyc | Atak i unik = **`X`**, a karta definiuje X tylko raz („X to liczba lokalizacji z cechą Spaczona"). Przy zerze Spaczonych ma atak 0 i unik 0. |
| BŁĄD | Smród z Garbar | Odsyła do „akcji Badania" pisanej wielką literą jako nazwa akcji, a jednocześnie ma statystyki wroga (patrz wyżej) — nie wiadomo, czym ta karta ma być. |
| SPÓJNOŚĆ | Biblioteka / Dyrekcja / Linia Rozlewnicza | Warunek „niedostępna, dopóki na **sąsiednich** lokalizacjach są wskazówki" na trzech kartach naraz, przy braku mapy, może zamknąć pół planszy. |
| SPÓJNOŚĆ | wersje `_kor_9` | Cztery lokacje mają warianty w nazwie pliku (`Biblioteka Uniwersytecka_kor_9`, `Dyrekcja Zakładu_kor_9`, `Linia Rozlewnicza_kor_9`) o tej samej nazwie karty — to strony Spaczone, ale nic tego nie mówi; wyglądają jak duplikaty. |
| SPÓJNOŚĆ | Linia Rozlewnicza | Dwie wersje mają różne cechy: „Mdła" i „Smrodliwa" — cechy nieużywane nigdzie indziej. |
| SPÓJNOŚĆ | emoji zamiast tagów | Biblioteka, Cytadela, Rynek Jeżycki, Sołacz i Ogród Botaniczny używają ➡️/📚/👊/🧠 zamiast tagów, mimo że reszta repo została ujednolicona. |

## Balans (1000 partii, 4 graczy)

| miara | wynik |
|---|---|
| wygrane | **0%** |
| porażka: zakleszczenie (spaczonej lokacji nie da się odzyskać) | 77% |
| porażka: wybicie grupy | 15% |
| porażka: zagłada (Tajemnica 4) | 8% |
| mediana rund | 11 |
| osiągnięty akt | 1: 0,5% · 2: 18% · **3: 79%** · 4: 0,3% · 5: 3% |

### Arytmetyka, która to psuje

| element | wartość | skutek |
|---|---|---|
| Goniec — zdrowie | 2`<per>` = **8** przy 4 graczach | tyle zagłady zrzuca na lokację, jeśli dojdzie nietknięty |
| próg spaczenia lokacji | **4** żetony | jeden Goniec spacza lokację z **dwukrotnym zapasem** |
| Gońców w talii | **6** kart (3 nazwy × 2) | ~1 na 4 dobierane karty |
| spaczenie | wskazówki na lokacji → zagłada | **traci się cały dorobek badania tej lokacji** |
| odzyskanie | test `<wil>`(3), 1 żeton za sukces (+1 za każdy punkt nadwyżki) | ~0,5 żetonu na akcję przy 43% skuteczności |

Goniec jest przy tym **Powściągliwy** — nie wchodzi w zwarcie, więc nie prowokuje reakcji; trzeba go świadomie ścigać i zabić 8 punktów zdrowia, zanim dojdzie. Przy 4 graczach i jednym wojowniku to nie jest wykonalne dla sześciu kopii.

W śledzonej partii (seed 4): **Cytadela i UAM spaczone w rundzie 2**, Mleczarnia w 6., Akt 1 zaliczony dopiero w 10. rundzie, grupa padła w 17. przy trzech trwale spaczonych lokacjach.

### Za trudne

- **Karta scenariusza**: kultysta i tablica dają **−X, gdzie X to liczba Spaczonych lokacji**, bez limitu. Przy trzech spaczonych to −3, przy pięciu −5, a spaczenie jest w praktyce nieodwracalne. To pętla dodatniego sprzężenia: więcej spaczenia → gorsze testy → mniej odzyskiwania → więcej spaczenia.
- **Zagłada rośnie z wielu źródeł naraz**: Goniec (masowo), Świeża Dostawa, Obłąkany Student (1/rundę w zwarciu), Wkurwiony Bamber (1 po każdym ataku), Mity (1/rundę). 38 zagłady wygląda dużo, ale to nie zagłada zabija — tylko 8% porażek.
- **Mleczarnia Spółdzielcza**: „+2 zasłony za **każdego badacza w tej lokacji**" przy bazowej 2 i 3`<per>` wskazówek — czterech badaczy robi z niej zasłonę 10. A jest celem dwóch aktów.
- **Smród z Garbar** w Mleczarni lub na Linii: `<wil>`(5) — w modelu przechodzi w **18%**.

### Za łatwe / martwe

- **Zagłada jako zegar** — 8% porażek. Prawdziwy zegar to spaczenie lokacji, a ono nie jest opisane jako zagrożenie.
- **Wkurwiony Bamber**: „Wydaj 4 zasoby: Pertraktacje, odrzuć" — 4 zasoby to dwie tury zbierania; taniej go zabić (3 zdrowia).
- **Nadbrzeże Warty** — jedyna lokacja, która nie może się spaczyć, zasłona 1, i daje darmowy ruch po zbadaniu. Bezpieczna baza, w której nic się nie dzieje.
- **Ogród Botaniczny, Sołacz, Rynek Jeżycki** — po 1–2 wskazówki i zdolności „odrzuć zasoby/kartę, by usunąć zagładę". Przy skali zagłady z Gońca (8) usuwanie po 1 żetonie za 2 zasoby jest bez znaczenia.

### Co bym zmienił (propozycje, nie wprowadzone)

1. **Goniec: zrzucaj 1–2 żetony zagłady zamiast „tyle, ile zdrowia"**, albo podnieś próg spaczenia do 6–8. To jedna liczba, która odblokowuje cały scenariusz.
2. **Spaczenie: zamiast „wskazówki → zagłada" niech zostaje połowa wskazówek** (zaokrąglona w górę). Teraz jedno zdarzenie kasuje pracę całej rundy.
3. **Karta scenariusza: ograniczyć `−X` do −3** (albo „X = liczba Spaczonych, maksymalnie 3"). Bez limitu spirala nie ma dna.
4. **Mleczarnia: „+2 zasłony za każdego badacza" → „+1"**, albo liczyć tylko badaczy poza tym, który bada.
5. **Dodać Czarną Kozę z Ostrowa i Stary Fort Pruski**, rozróżnić trzy Gońce nazwami (np. Goniec z Mleczarni / z UAM / z Cytadeli), rozdzielić cele Aktów 3 i 4.
6. **Usunąć statystyki wroga z trzech podstępów** i uzupełnić zasłonę/wskazówki na 10 lokacjach.

---

## Założenia modelu (uproszczenia)

Wspólne z modelem scenariusza 2: worek **Standard** (+1, 0, 0, −1, −1, −1, −2, −2, 💀💀, 👤, 📜, 🐙, ⭐); talie graczy jako profile liczbowe (średnie ikony na kartę deklarowane, gdy przewaga < 2; broń/zaklęcie w grze = +1 do walki, mistyk walczy wolą; narzędzia poszukiwacza = +1 intelekt; sojusznik = +1 zdrowia i poczytalności; leczenie 1 pkt/rundę z prawdopodobieństwem udziału kart leczących); 3 akcje na turę; ruch kosztuje **1–3 akcje** (siatki ~3×3, losowany dystans).

**Scenariusz 1**: 9 lokacji wioski ma puste pola, więc przyjęto zasłonę 2 i 1`<per>` wskazówek. Akt 1 → 2 zamodelowany jako „wydaj 3`<per>` wskazówek" (realna ścieżka przez Klucz do zachrystii nie istnieje). Akt 2 → 3 to udany test `<int>`(4) w Norach lub Obozie ocalałych. Talia startowa: Ciekawski ×5, Przekonany ×5, Zbłąkany ×2, Wołanie — pozostałe karty dokładają tajemnice. Ciekawski traktowany jako Powściągliwy (Pertraktacje `<wil>`/`<com>` 3 usuwają go). Żyrij: 12 zdrowia, każde trafienie zamienia Ciekawskiego w Wyznawcę.

**Scenariusz 3**: 13 lokacji, wskazówki 1–3`<per>`, zasłona z awersów. Goniec patroluje do celu (1 krok/rundę) i zrzuca zagładę równą zdrowiu. Spaczenie przy 4 zagłady zamienia wskazówki na zagładę. Odzyskiwanie: `<wil>`(3), 1 żeton + nadwyżka. Akty: 1 = 3`<per>` wskazówek, 2 = Zakłady, 3 i 4 = Mleczarnia, 5 = Cytadela, 6 = boss (zamodelowany jako 4`<per>` zdrowia, mimo że karty nie ma). „Zakleszczenie" to 40 akcji z rzędu bez postępu — model uznaje to za porażkę, przy stole byłoby to po prostu przegrane tempo.

**Nie modelowane**: konkretne karty gracza, ataki okazyjne, zasoby, mapa połączeń (dystans losowany), Brama z Gałęzi jako blokada, warunki „niedostępna, dopóki sąsiedzi mają wskazówki", odwracanie lokacji z powrotem na stronę czystą poza celem aktu.

Narzędzia: `tools/scenario13_model.py` (`tempo 1|3`, `sim 1|3`), profile z `tools/arkhamdb.py`.
