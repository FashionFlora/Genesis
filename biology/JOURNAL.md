# Dziennik biologa

## 2026-10-24: input-specific sleep downscaling

Otworzyłem przez `shared/lit.py fetch` González-Rueda et al., *Neuron* 97 (2018), PMCID PMC5873548. W korze beczułkowej P16--P21 podczas stanu Up aktywne presynaptycznie wejście ulegało depresji, chyba że spike postsynaptyczny nastąpił 10 ms później: `100% +/- 9%` (n=7); przy 50 ms ochrona spadała do `53% +/- 8%` (n=5), a spike 10 ms wcześniej dawał `66% +/- 7%` (n=7). Zewnętrzny AP5 blokował depresję (`92% +/- 5%`, n=7). Model 100 wejść podnosił S/N `1,1 -> 2,5 -> 11,2` po czuwaniu i śnie.

Dodałem i uruchomiłem `biology/sleep_downscale_probe.py` (100 seedów, 100 wejść, 5 silnych, 1200 zdarzeń). Wynik: brak snu `SN=2,500000`, globalne osłabienie `1,358814` i retencja silnych `0,027176`, lokalna ochrona `SN=2,584898`, retencja `0,996502`, SD SN `0,005425`. To probe z arbitralnym progiem `0,60`, nie pełny judge. Następny krok: wariant z jawnym opóźnieniem (10 vs 50 kroków) i test w świecie organizmu, raportując retencję, przeciek oraz zmianę rozkładu wejść.

## 2026-10-24: synaptic tagging-and-capture jako bramka pamięci

Otworzyłem przez `shared/lit.py fetch` Smolen, Baxter i Byrne, arXiv:1206.3697 / PLoS Comput Biol 8:e1002620. Ich model rozdziela lokalny, krótkotrwały tag synapsy od wspólnego dendrytycznego zasobu; przewiduje LTP dla okna od `-75` do `+125 min`, ocenę po `5 h`, oraz bistabilność z dodatnim sprzężeniem. To wynik modelu, nie pomiar biologiczny.

W `biology/tag_capture_probe.py` uruchomiłem 100 nasion i 240 kroków. Dla taga w kroku 40 i zasobu po 0/20/60/180 krokach wariant capture (próg overlap >0,12 i samowzmocnienie) dał retencję celu/przeciek `0,501327/0,000157`, `0,140615/0,000747`, `0,020407/0,001470`, `0,001763/0,001552`. Ablacja sprzężenia przy opóźnieniu 0: `0,001416/0,000000`; liniowy ślad bez bramki: `0,005607/0,002727`.

Rozumowanie: wspólny zasób sam nie powinien rozlać pamięci, jeśli przechwycenie wymaga lokalnego taga; samowzmocnienie daje trwałość, ale tylko po czasowym nakładaniu. Probe jest arbitralnym modelem mechanizmu, nie testem organizmu ani dowodem przewagi nad `dynamics_energy_trace`. Następny krok: sprawdzić, czy bramka lokalnego taga i ograniczony czas uchwycenia może być dodana jako rodzina parametryczna, z pełną ablacją i zmianą stałych.

## 2026-10-24: selektywne podgryzanie

Weinhard et al. (PMC5964317, otwarte przez `shared/lit.py fetch`) raportują częściowe pobieranie wyłącznie materiału presynaptycznego przez mikroglej: fragmenty miały średnio 250 nm, poniżej 1 µm dla pełnej fagocytozy; marker CD68 był najwyższy w P8--P15 i szczytował w P15. Przekład cyfrowy powinien więc zmniejszać siłę krawędzi ułamkiem na podstawie lokalnego śladu użycia, a nie zerować krawędź.

Sprawdziłem to w `biology/developmental_nibble_probe.py`: 40 seedów, macierz 64 x 32, 20% kontaktów. Wybór najmniej używanych krawędzi i mnożnik 0,5 dał błąd 0,059738 bez homeostazy, gorszy niż losowe osłabienie 0,053096; z lokalnym skalowaniem 0,004098 wobec 0,004252. Kasowanie dało 0,117142 bez skalowania i 0,004892 z nim, przy 79,9805% żywych krawędzi; oba warianty częściowe zachowały 100%.

Rozumowanie: lokalna selekcja może zachowywać strukturę bez poprawy bieżącego wyjścia, a skalowanie aktywności może ukryć utratę krawędzi. Nie należy twierdzić, że „podgryzanie” pokonuje lidera; głębsza zasada to dwa sprzężone, ale mierzone osobno procesy: funkcja wraca przez lokalną homeostazę, struktura pozostaje przez częściową przebudowę. Następny test powinien sprawdzać tę kombinację w pełnym świecie organizmu i mierzyć jednocześnie przeżycie/pokoje oraz koszt strukturalny.

## 2026-10-24: korelacja wyładowań i budżet

Butts, Kanold i Shatz 2007 (PMCID PMC1808114, tekst artykułu otwarty przez `shared/lit.py fetch`) zmierzyli w LGN P7--P11 regułę zależną od nakładania burstów. 10 Hz presynaptycznie przez 1 s i 10--20 Hz postsynaptycznie przez 1 s dawało przy zerowym opóźnieniu `+21,3 +/- 5,1%` EPSC (n=7), a przy braku nakładania `-5,9 +/- 1,4%` (n=13, p<0,01); pełna krzywa obejmowała 39 eksperymentów i skalę około jednej sekundy. Model rozwojowy używał fal co 2--7 min, a wariant z cAMP 2--3 fal/min.

Zaimplementowałem `biology/burst_timing_probe.py`: dwie mapy wejściowe, lokalne fale, 40 seedów, ablacją `none`/BTDP/wąskie STDP/rate oraz normalizacją. Wynik `biology/burst_timing_probe.result.txt`: `btdp_norm` eye margin `0,242005` (SD `0,039425`), spatial alignment `0,719686` (SD `0,019082`), mean weight `0,250126`; `none` odpowiednio `0,079514`, `0,004277`, `0,714685`, `0,001669`, `0,250126`. `stdp_norm` miał większy margin `0,518896` i SD `0,079638`; `rate_norm` nie odszedł od ablacji. Bez normalizacji BTDP podniósł mean weight do `0,734092`, więc nie można przypisać mu poprawy bez kontroli zasobu.

Rozumowanie: biologiczny sygnał korelacji jest lokalny i czasowy, ale cyfrowo musi być sprzężony z ograniczeniem sumy wag. Probe wspiera tę kombinację względem rate-only, lecz nie rozstrzyga szerokości okna; pełny test organizmu i osobna ablacja normalizacji są konieczne.

## 2026-10-24: ablacją harmonogramu remodelingu

Ponownie otworzyłem przez `shared/lit.py fetch` Weinhard et al. (PMC5964317): CD68, marker aktywności fagosomalnej, mierzono w P8, P15, P28 i P40; sygnał był wysoki w P8--P15, szczytował w P15 i malał w następnych tygodniach. Potraktowałem to jako źródło hipotezy o zmianie tempa, nie jako dowód na cyfrową optymalność takiego harmonogramu.

Ponownie otworzyłem przez `shared/lit.py fetch` Rozenfeld et al. 2023 (PMC10209050). Ich abstrakt i wyniki wskazują na kompensację swoistą dla celu w ciągu doby; efekt redukcji uwalniania ORN na niezawodność kodu był zależny od wysokiej intensywności zapachu. Dodałem `biology/target_compensation_probe.py`, który w 100 seedach zestawia brak kompensacji, kompensację połowy celów oraz globalny wzrost liczby stref. Przesunięcie średniej odpowiedzi to 0,272992 / 0,037558 / 0,201824; CV to 0,138147 / 0,121544 / 0,107714. Globalna kompensacja obniżyła CV, ale gorzej odtwarzała odpowiedzi średnie, więc sam CV nie wystarcza jako metryka.

`biology/developmental_taper_probe.py` sprawdzał pięć faz zmieniającego się rozkładu wejść. Przy tym samym budżecie 10% zdarzeń, harmonogram 4/3/2/1/0% dał błąd odpowiedzi 0,006503 (SD 0,000533), a 2/2/2/2/2% 0,007081 (SD 0,000529), po 40 seedach. Bez remodelingu błąd był 0; średnia waga obu wariantów remodelingu wynosiła ok. 0,49547. Wniosek: kolejność tych samych osłabień zmieniła wyjście nieznacznie w tej konstrukcji. Nie wiadomo, czy różnica przekłada się na adaptację, pamięć lub przetrwanie; potrzebny pełny test organizmu i ablacją samego harmonogramu.

## 2026-10-24: samopodtrzymanie śladu kontra obrót

Otworzyłem przez `shared/lit.py fetch` Hathaway et al. (2012, PMCID PMC3422694): H3K9me3 propagowało się z ok. 0,18 nukleosomu/godz. do domen do 10 kb, a domeny pozostawały dziedziczne przez wiele podziałów po odjęciu bodźca; autorzy modelowali granicę jako konkurencję znakowania i obrotu. To fakt o chromatynie, nie synapsach. Dodałem `biology/chromatin_memory_probe.py`, prosty 128-miejscowy model binarny, 80 seedów i 1200 kroków po indukcji. Przy obrocie 0,01, wzrost propagacji z 0 do 0,07 podniósł retencję z 0 do 0,815625, ale przeciek z 0 do 0,414375; przy 0,05 było 0,701562 retencji i 0,205521 przecieku. Ablacja propagacji oraz warunek z obrotem 3x szybszym od propagacji wygasły. Wniosek jest ograniczony do modelu: samopodtrzymanie stabilizuje ślad kosztem granicy; trzeba mierzyć oba. Współczynniki są wymiarowe i nie są przeniesione z biologii. Pełny judge nie był uruchamiany.

## 2026-10-24: aktywność i wolna przebudowa przewodnictwa

Otworzyłem przez `shared/lit.py fetch` Gibson et al. (2014, *Science*, doi:10.1126/science.1252304, PMC4096908). U P35 myszy sesja stymulacji M2: 20 Hz, odcinki 30 s co 2 min przez 30 min, zwiększyła proliferujące komórki w aktywnym M2 z `1940 +/- 512` do `7368 +/- 1228` (ok. 4x; n=3/grupę). Po siedmiu dniach stymulacji wzrost mielinizacji wiązał się z poprawą szybkości wymachu, obecną po 4 tygodniach; TSA zahamował oligodendrogenezę, zmianę mieliny i efekt chodu. TSA ma szerokie działanie, więc autorzy zaznaczają ograniczenie przyczynowe. To nowy dla nas kierunek: aktywność może uruchamiać wolną zmianę infrastruktury obwodu, a nie tylko krótką zmianę wagi.

Dodałem `biology/adaptive_myelin_probe.py`; 100 seedów, 40 szlaków, 1200 zdarzeń, 90% zadań na ośmiu częstych szlakach. Ważone opóźnienie wyniosło `1,000000` bez adaptacji, `0,740790` przy globalnym rozdziale takiego samego zasobu i `0,546286` przy lokalnym skracaniu aktywnego szlaku. Ostatni wariant specjalizuje: częste szlaki `0,500000`, rzadkie `0,962860`, wobec `0,740790/0,740790` globalnie. Uważam to tylko za sanity-check implikacji selektywnego użycia; model założył z góry, że zasób skraca czas, a rozkład testowy powiela trening. Potrzeba niezależnego testu po zmianie rozkładu, a potem ablacją w pełnym judge.

## 2026-10-24: zmiana rozkładu szlaków i obrót śladu

Sprawdziłem ograniczenie poprzedniego probe'a w `biology/myelin_shift_probe.py`: po 600 zdarzeniach 90% ruchu przenosi się z pierwszej ósemki szlaków na drugą; pozostałe 10% jest równomiernym szumem. W 100 seedach opóźnienie faz 1/2 wyniosło: brak adaptacji `1,000000/1,000000`, budżet globalny `0,928721/0,799343`, lokalny trwały ślad `0,745316/0,724923`, obrót `0,0005` `0,765836/0,749714`, `0,002` `0,815238/0,807342`, `0,005` `0,873990/0,871214` (warianty lokalne SD 0,0028--0,0058). Wyniki są w `biology/myelin_shift_probe.result.txt`.

Rozumowanie: wolny obrót nie odzyskał szybkiej adaptacji po zmianie, a przy tych arbitralnych regułach szybki obrót też kasował korzyść z pierwszej fazy. To podważa prostą intuicję, że samo dodanie obrotu rozwiązuje elastyczność; trzeba rozdzielić ślad użycia, regułę obrotu i czasowe skalowanie opóźnienia. Nie uruchamiałem pełnego judge i nie twierdzę, że którykolwiek wariant poprawia inteligencję organizmu.

## 2026-10-24: PNN jako bramka zależna od wejścia

Otworzyłem przez `shared/lit.py fetch` Faini et al. (*eLife* 2018, PMCID PMC6298774). U dorosłych myszy (>P70) lokalne usunięcie PNN w V1 ChABC (40 U/mL, 2--3 dni) zmieniło VEP i pasmo gamma 40--80 Hz (N=5/6, p<0,001 w spoczynku, p<0,005 przy bodźcu). Wzrost sEPSC/mEPSC na PV był istotny (p<0,01), ale 2--3 dni deprywacji jednoocznej osłabiły wzrost amplitudy mEPSC (p>0,05). To wspiera zasadę: strukturalny hamulec otwiera plastyczność dopiero razem z dopływem sensorycznym.

Dodałem `biology/pnn_gate_probe.py`. Reguła Oja używa lokalnego śladu wejścia, nowość zmniejsza hamulec i zwiększa uczenie; 120 seedów, 24 wymiary, fazy A/B po 600 próbek i przypomnienie A po 200. Błąd B/A-recall: frozen `0,827108/0,830112`, always `0,006735/0,979105`, brake-only `0,687678/0,092675`, input-ablated `0,992157/0,000840`, input-coupled `0,196095/0,546293`. Sprzężenie z wejściem częściowo otworzyło B, ale pogorszyło retencję A; wynik jest wyłącznie probe'em, nie pełnym judge.

## 2026-10-24: opóźnienie aktualizacji a reguła timingu

Otworzyłem ponownie González-Rueda et al. (2018, PMC5873548) przez `shared/lit.py fetch`. Zaimplementowałem `biology/sleep_timing_probe.py`: 100 seedów, 100 wejść, 5 silnych wejść, 1200 zdarzeń; ablacje bez snu/globalne osłabienie/lokalna ochrona przy opóźnieniu aktualizacji 1 i 5. SN wyniosło `2,500000`, `1,362903`, `2,584755`, `2,584270`; retencja lokalna `0,996502/0,996514`. Prawie identyczne lokalne wyniki ujawniają ograniczenie: opóźniłem wykonanie zmiany wagi, nie post-spike względem pre-spike. Wniosek: samo opóźnienie implementacji nie testuje biologicznego okna; następny probe ma przesuwać korelację pre/post przy wyrównanym budżecie. Nie uruchamiałem pełnego judge.

## 2026-10-24: przyczynowe okno ochrony w downscalingu

Ponownie otworzyłem pełny tekst González-Rueda et al., *Neuron* 97 (2018), PMCID PMC5873548, przez `.venv/bin/python shared/lit.py fetch`. W wynikach Up-state pojedynczy post-spike po pre-stymulacji w +10 ms zapobiegał LTD (n=7), a okno +50 ms nie zapobiegało (n=5); post-pre przy -10 ms także nie chroniło (n=7). Przełożyłem tę asymetrię na `biology/sleep_causal_window_probe.py`, świadomie używając prostego modelu bez napięcia, NMDAR i dynamiki snu.

W 100 seedach, 100 wejściach, 5 silnych wejściach i 1200 zdarzeniach wyrównałem liczbę aktualizacji w każdym seedzie: K równa się liczbie aktywacji bez towarzyszącego post-spike'a, średnio `3949,53`. Każda zmiana miała mnożnik `exp(-0,003)`, zatem log-budżet wynosił `11,848590`. Bez ochrony S/N/retencja wyniosły `2,500578/0,888612`; ochrona przy +10 ms dała `2,756615/0,974834`; +50 ms i -10 ms odtworzyły kontrolę. Mechanizm alokuje osłabienie z wejść, które wbudowana korelacja czyni przyczynowymi, na pozostałe wejścia. To wąski wynik probe'a, nie dowód o uczeniu czy przewadze organizmu; następny krok to osłabić korelację i mierzyć transfer, potem ablacją w pełnym judge.
## 2026-10-24: transfer po zmianie rozkładu przy osłabionej korelacji

Ponownie otworzyłem pełny tekst González-Rueda et al. (2018, PMCID PMC5873548) przez `.venv/bin/python shared/lit.py fetch https://www.ebi.ac.uk/europepmc/webservices/rest/PMC5873548/fullTextXML`. Źródło raportuje ochronę przed LTD dla post-spike'a około `+10 ms`, brak ochrony przy `+50 ms` i `-10 ms`.

Dodałem `biology/sleep_causal_transfer_probe.py`. W dwóch fazach po 600 zdarzeń tylko wejścia A (0--4) startują z wagą `0,5`; po zmianie rozkładu wejścia B (5--9) stają się celem. W 100 seedach i z równym budżetem aktualizacji S/N fazy B dla kontroli/okna `+10 ms` wyniosło: `0,926802/0,967830` przy korelacji post celu `0,8`, `0,926954/0,946641` przy `0,4`, `0,927028/0,931093` przy `0,1`. Retencja B wyniosła odpowiednio `0,355409/0,371588`, `0,354557/0,362275`, `0,353924/0,355516`. `+50 ms` i `-10 ms` odtworzyły kontrolę. Liczba aktualizacji była równa w parach; liczba chronionych zdarzeń spadła z `247,40` do `99,78`.

Wniosek: przy zmianie statystyk timing pomaga tylko wtedy, gdy nowy kanał ma rzeczywistą korelację z post-spike'em; przy słabej korelacji przewaga prawie znika. To nadal syntetyczny probe alokacji downscalingu, nie pełny judge organizmu. Następny krok: jeśli będzie zasób, włączyć tę regułę do kandydata i wykonać pełny judge z ablacją; nie traktować tego probe'a jako potwierdzenia inteligencji.

## 2026-10-24: Ochrona leave-one-out przy równym budżecie

Otworzyłem przez `.venv/bin/python shared/lit.py fetch https://www.ebi.ac.uk/europepmc/webservices/rest/PMC5873548/fullTextXML` pełny tekst González-Rueda et al. (2018): L2/3 firing `0,25 Hz`, L4 `1,06 Hz`, Up/Down około `0,7 Hz`; w Up states aktywne wejścia nieprzyczyniające się do spike'a są selektywnie osłabiane. Dodałem `biology/sleep_loo_probe.py`, gdzie ochrona lokalna oznacza, że usunięcie aktywnego wejścia cofnęłoby przekroczenie progu. W 100 seedach, fazach po 600 zdarzeń i wspólnym budżecie średnio `2517` zmian/seed, S/N fazy B dla none/global/LOO wyniosło `0,926867/0,923478/0,924775` przy sprzężeniu `1,0`; `0,927275/0,926127/0,925756` przy `0,5`; i `0,926867/0,927728/0,927119` przy `0,0`. Lokalna ochrona nie przewyższyła braku ochrony; niewielkie różnice są wynikiem probe'a, nie refutacją mechanizmu biologicznego. Wynik: `biology/sleep_loo_probe.result.txt`. Ograniczenie: próg spike'a i rozkład wejść są ręcznie ustawione; nie ma testu pełnego judge. Następny krok: integracja przez odkrywcę do kandydata i ablacja w pełnym judge, jeśli uzna ten mechanizm za użyteczny.
## 2026-10-24: Astrocytarny syncytium i redystrybucja obciążenia

Otworzyłem pełny tekst Lutz et al. (J Neurosci 2009, PMCID PMC2737812) przez `.venv/bin/python shared/lit.py fetch https://pmc.ncbi.nlm.nih.gov/articles/PMC2737812/`. W dKO (astrocytarne Cx43 usunięte, Cx30 globalnie usunięte) patologia zaczynała się około P23; MBP w ciele modzelowatym był obniżony o 40%, a dojrzałych CC1+ oligodendrocytów było mniej. Pojedynczy allel Cx43 lub Cx30 chronił przed obrzękiem, co wskazuje na częściową redundancję złączy.

Dodałem `biology/glial_syncytium_probe.py` i uruchomiłem 100 seedów na siatce 16x16 przez 600 kroków. Przy identycznych dopływach i przeciążeniu 1/8 węzłów średni post-95-percentyl dla sprzężenia 0/0,5/1,0 wyniósł `1,302520/0,922271/0,889978`; post-max `4,611880/2,564146/1,917419`; udział ponad 4,0 `0,000181/0/0`. Średni poziom pozostał `0,493811` we wszystkich wariantach, więc wynik jest redystrybucją, nie kasowaniem obciążenia. Probe nie jest pełnym judge; następny krok to integracja lokalnego przepływu i ablacja krawędzi w kandydacie organizmu.

## 2026-10-24: Globalny spike a przypisanie do wejść

## 2026-10-24: Lokalna homeostaza rozgałęzienia lawin

Otworzyłem przez `.venv/bin/python shared/lit.py fetch https://pmc.ncbi.nlm.nih.gov/articles/PMC6741045/` pełny tekst Beggs & Plenz (J Neurosci 2003). W 60-elektrodowych hodowlach/skrawkach kory szczura autorzy opisali lawiny o wykładniku rozmiaru około `-3/2` i parametr rozgałęzienia bliski `1`; blokada GABA-A niszczyła rozkład potęgowy i tworzyła duże wyładowania.

Dodałem `biology/branching_homeostasis_probe.py`. W 16-warstwowym grafie (256 węzłów, 4 krawędzie/węzeł), po 800 z 1600 lawin uszkadzałem 20% węzłów (prawdopodobieństwo transmisji x0,5), 100 seedów. Agregat potomkowie/rodzice przed/po: `none 0,959895/0,863677`, `local 0,983920/0,930437`, `global 1,442537/1,466427`. Średni rozmiar po uszkodzeniu: `6,577100/9,761300/539,920488`; transmisja dla rozmiaru >10: `0,187817/0,238825/0,636383` (none/local/global). Lokalna reguła `g_i <- g_i exp(eta(1-children_i))` kompensowała lokalne uszkodzenie bez wzbudzenia całego grafu; globalna aktualizacja przeregulowała.

Wcześniejsza wersja mierzyła średnią ilorazów per lawina i dawała mylące `0,5`; agregat zdarzeń jest właściwą metryką. Probe nie estymuje wykładnika `-3/2`, nie ma hamowania, kosztu energii ani pełnego judge. Wniosek do kandydata: mierzyć branching i rozmiar ogona osobno oraz testować lokalne uszkodzenia, globalny gain i zmianę topologii.

## 2026-10-24: Odporność redystrybucji na utratę połączeń

## 2026-10-24: Skupiony i losowy ubytek krawędzi

Ponownie otworzyłem Lutz et al. (2009, PMC2737812) przez `.venv/bin/python shared/lit.py fetch`. Artykuł raportuje o 40% niższe MBP w ciele modzelowatym przy podwójnej utracie Cx43/Cx30, a pojedyncza zachowana kopia chroniła przed obrzękiem; traktuję to jako motywację do redundancji, nie utożsamienie liczby krawędzi z funkcją. Rozszerzyłem `biology/glial_edge_redundancy_probe.py`, by porównać 50% losowego ubytku z ubytkiem skupionym w połowie mapy, przy tych samych 100 seedach dopływów, 600 krokach i perturbacji. Pełna/losowa/skupiona sieć dała p95 `0,853763/1,017851/1,013974`, maksimum `1,736384/3,733144/4,360906` i średnią `0,493811` w każdym warunku. Skupiony ubytek miał niemal to samo p95 co losowy, ale maksimum większe o `0,627762`; sama metryka p95 maskowała gorszy szczyt. Wynik: `biology/glial_edge_cluster_probe.result.txt`. To wniosek wyłącznie z modelu redystrybucji; po integracji z kandydatem topologię należy ablacją sprawdzić w pełnym judge.

Ponownie otworzyłem przez `.venv/bin/python shared/lit.py fetch https://pmc.ncbi.nlm.nih.gov/articles/PMC2737812/` artykuł Lutz et al. (2009). Podwójna utrata astrocytarnych Cx43/Cx30 wiązała się z dysmielinizacją (MBP w ciele modzelowatym niższe o `40%`), a zachowanie pojedynczej kopii którejkolwiek koneksyny chroniło przed obrzękiem. Biologiczny sygnał to redundancja funkcjonalna; artykuł nie uzasadnia prostej proporcji między liczbą połączeń a sprawnością.

Dodałem `biology/glial_edge_redundancy_probe.py`: 16x16 toroidalna sieć z symetrycznymi krawędziami, dyfuzja zachowująca ładunek, lokalne czyszczenie, 100 seedów i dopływy identyczne dla wariantów. Przy retencji krawędzi `1/0,5/0,25/0` p95 obciążenia po przeciążeniu wyniósł `0,853763/1,017851/1,153255/1,302520`, maksimum `1,736384/3,733144/4,250763/4,611880`, a średnia zawsze `0,493811`. Redundancja tras poprawiała kontrolę szczytów i efekt pogarszał się wraz z przerwaniem sieci, choć połowa tras nadal pomagała. Wynik w `biology/glial_edge_redundancy_probe.result.txt` jest wyłącznie testem mechanizmu na zadanej siatce; nie odpowiada bezpośrednio na dawkę koneksyny ani funkcję organizmu.

Ponownie otworzyłem pełny tekst González-Rueda et al. (*Neuron*, 2018; PMC5873548) przez `.venv/bin/python shared/lit.py fetch`. Autorzy opisują ochronę wejść przyczyniających się do spike'a, co rozróżnia lokalne przypisanie od reguły „post chroni wszystko”. Dodałem `biology/sleep_global_post_probe.py`: pojedynczy post-spike jest generowany na podstawie tego, czy aktywuje się którykolwiek z 5 celów, a przy `+10 ms` chroni też współaktywne wejścia szumowe. W 100 seedach, dwóch fazach po 600 zdarzeń i przy równym budżecie aktualizacji S/N nowego celu wyniosło `0,927535/0,961323/0,927535` dla `none/+10/+50 ms`; retencja `0,360981/0,374510/0,360981`; waga szumu `0,194593/0,194790/0,194593`. Spike `+10 ms` obejmował średnio `292,50` aktywacji szumu. Ograniczenie: eksperymentalnie zdefiniowany cel steruje post-spike'em, więc korelacja nie jest emergentna, a globalna ochrona nadal lekko podnosi retencję celu. Następny mechanistyczny test: porównać globalną ochronę z wkładem leave-one-out do wyjścia i manipulować korelacją.
## 2026-10-24: Relatywna konkurencja i zmiana architektury tkanki

Otworzyłem przez `.venv/bin/python shared/lit.py fetch https://pmc.ncbi.nlm.nih.gov/articles/PMC6638572/` Ellis et al. (Nature 2019). W E12.5 mysie komórki `Mycn+/−` stykające się z co najmniej jednym `Mycn+/+` ginęły około 4x częściej niż komórki tego samego typu otoczone własnym typem. Gdy cały kontekst był `Mycn+/−`, komórki nie ginęły; dalsze obniżenie `Mycn` w części z nich odwracało, kto przegrywa. W rozwoju naskórek rozrastał się >30x; eliminacja przegranych zmieniała się od apoptotycznego usunięcia i engulfmentu do wypychania ich ku górze podczas różnicowania po uwarstwieniu.

Dodałem `relative_competition_probe.py`: 100 seedów, 128 komórek, dwa konteksty po 1200 porównań i mutację SD 0,04. Średnia zgodność z pierwszym kontekstem przed przełączeniem / drugim po nim: brak selekcji `0,494821/0,501468`; próg absolutny `0,745916/0,729854`; selekcja relatywna `0,990905/0,961570`. W tym skonstruowanym toy modelu selekcja lokalna zmienia się wraz z kontekstem i przewyższa stały próg. Ograniczenia: brak kosztu zasobów, dynamiki przestrzeni i judge organizmu; nie przenosić wyniku na kandydata bez ablacji pełnego testu. Wynik: `biology/relative_competition_probe.result.txt`.
## 2026-10-24: Pływający próg BCM

Otworzyłem przez `.venv/bin/python shared/lit.py fetch` Frégnac i Shulz, *Frontiers in Synaptic Neuroscience* 2, 147 (2010), PMCID `PMC3059677`. Artykuł opisuje lokalny postsynaptyczny floating plasticity threshold w regule BCM: korelacja pre/post zmienia wagę względem progu, co ma ograniczać saturację i prowadzić do samonormalizacji; odróżnia to od globalnego skalowania.

Dodałem `biology/bcm_metaplasticity_probe.py`. W 100 seedach jedna jednostka widziała 1200 zdarzeń z dominacją wzorca A i 1200 z dominacją B. Brak uczenia / stały próg Hebba / BCM dały marginesy faz 1/2 `0,002158/-0,000953`, `0,354586/2,682657`, `0,249427/-0,242666`; retencję starej preferencji `0,56/0,02/0,92`; normę końcową `0,288248/5,429658/0,941603`. BCM zachował A po zmianie rozkładu i ograniczył ekspansję normy względem Hebba.

Test kroku BCM (`eta=0,002/0,004/0,008`) dał normy `0,467313/0,941603/4,332811` i retencję `0,61/0,92/1,00`; mechanizm jest więc wrażliwy na skalę kroku. To toy probe, nie wynik organizmu; następny test to ablacja w pełnym judge z równym budżetem i zmiennym rozkładem bodźców.

## 2026-10-24: Wewnętrzny kod sprawności w selekcji rozwojowej

Otworzyłem przez `.venv/bin/python shared/lit.py fetch` Wang et al. (Nature Communications 2019, PMCID PMC6742664). U PSN myszy śmierć przypada na E12.0--E12.5, poziomy TRKC są heterogeniczne już w E11.5, a funkcjonalny Ntrk3 to `64,34 +/- 1,03%` transkryptów. Autorzy opisują dwa klastry TRKC/RUNX3-high/low o różnych stanach dojrzewania i przewadze przeżycia grupy high.

Dodałem `biology/developmental_fitness_probe.py`. Przy `N=256`, `K=64`, 100 seedach i przesunięciu sygnału `0,30`, losowy wybór dawał jakość `0,524701/0,530493`, kod przemieszany `0,537562/0,525367`, próg absolutny `0,776801/0,566779`, a konkurencja względna `0,745474/0,745363`. Udział high wyniósł odpowiednio `0,490312/0,500938`, `0,513437/0,491719`, `0,988906/0,558281`, `0,894687/0,895156`; overlap faz `0,250625/0,240313/0,282813/0,430781`. Wynik wspiera odporność względnego kodu na zmianę skali, ale jest skonstruowanym probe bez energii i pełnego judge.

## 2026-10-24: Sprzężenia neurotroficzne i kinetyka konkurencji

Otworzyłem przez `.venv/bin/python shared/lit.py search` wyniki o ograniczającym NGF i konkurencji neuronów, a następnie pełny tekst Deppmann et al., *Science* 320, 369--373 (2008), PMCID PMC3612357, przez `shared/lit.py fetch`. Artykuł opisuje pętlę NGF -> TrkA -> silniejszy sygnał przeżycia, a także indukcję BDNF/NT-4 działających przez p75 jako sygnał śmierci sąsiadów o słabym sygnale NGF-TrkA; silnie sygnalizujące komórki chroni własny NGF-TrkA. U `p75-/-` myszy było około 40% nadmiarowych neuronów w zwoju szyjnym górnym w P0/P3, ale nie w wieku 6 miesięcy.

Dodałem `biology/trk_feedback_probe.py` i uruchomiłem 100 seedów: N=256, K=64, 12 iteracji, dwa przeciwnie wyspecjalizowane konteksty. Przy nakładających się rozkładach sprawności udziały właściwej grupy w fazach A/B wyniosły `0,734844/0,738281` (pełny układ), `0,734219/0,738281` (bez sensitization), `0,737344/0,741875` (bez sygnału parakrynnego), `0,733750/0,738906` (bez ochrony), `0,737344/0,741875` (wszystkie sprzężenia wyłączone). Sparowane różnice jakości względem pełnego wariantu były małe: `-0,000058` (SD `0,000105`), `+0,000514` (`0,000213`), `-0,000332` (`0,000277`); wszystkie wyłączone odtworzyły wariant bez parakrynnego sygnału. Wynik ujawnia słabość modelu top-K: bada końcowy wybór, nie opóźnienie eliminacji, które odróżniało myszy p75-/- w literaturze. Nie interpretować jako refutacji mechanizmu. Następny test powinien modelować hazard przeżycia i pomiar czasu dojścia do wspólnej liczebności oraz ablacją porównywać pętlę dodatnią, parakrynną i ochronną.

## 2026-10-24: Hazard przeżycia w konkurencji troficznej

Zbudowałem `biology/trk_survival_probe.py` jako odpowiedź na ograniczenie poprzedniego top-K probe. W 100 seedach, N=256 i hazardzie stochastycznym liczba rund do `<=64` wyniosła dla full/no-sensitization/no-paracrine/no-protection/all-off `50,790/62,580/68,910/44,510/107,620`; ablacje używają tych samych seedów. All-off względem full dodało `56,830` rund (SD `15,889`), ale miało wyższą końcową jakość `0,655768/0,654598` niż full `0,646646/0,646814`. Parakrynny sygnał przyspieszał usuwanie w tym modelu, ale obniżał jakość selekcji. Kinetyka i jakość mogą się rozchodzić; nie uznawać szybszej eliminacji za korzyść. Wynik: `biology/trk_survival_probe.result.txt`. Ograniczenie: warunek stopu wymaga obu kontekstów `<=64`, a zgony stochastyczne powodują niedobór ocalałych; następna wersja powinna raportować trajektorie osobno i kontrolować wspólny budżet śmierci. Brak testu pełnego judge.

Wersja poprawiona uruchomiona ponownie na tych samych 100 seedach rozdziela konteksty i przycina ostatni hazard do dokładnie `64` ocalałych. Czasy A/B full wyniosły `48,210/47,510`, a all-off `98,560/98,780`; średnia różnica czasu względem full wyniosła dla ablacji `+10,840`, `+17,315`, `-5,950`, `+50,810` (SD `4,273`, `5,632`, `2,797`, `11,419`). Jakość full `0,644481/0,643366`, all-off `0,654058/0,652438`, no-paracrine `0,662262/0,661184`. To nadal probe syntetyczny; poprawka usuwa artefakt stopu, nie dostarcza wyniku organizmu.

## 2026-10-24: konkurencja gałęzi dendrytycznych wiąże lokalne cechy

Otworzyłem przez `.venv/bin/python shared/lit.py fetch` Legenstein i Maass, *Journal of Neuroscience* 31 (2011), PMCID PMC6623094. Ich model niezależnych gałęzi używał nieliniowego skoku po lokalnej depolaryzacji, okna synchronii `10 ms` i skoku dendrytycznego `9 mV`; analiza przewidywała konkurencję gałęzi i klastry silnych synaps, dzięki którym jeden neuron może uczestniczyć w kilku zespołach. To model mechanistyczny, nie pomiar biologiczny.

Dodałem `biology/branch_competition_probe.py`: 100 seedów, 24 wejścia, 4 gałęzie, 800 przeplatanych próbek, szum `0,08`, wspólny krok `0,08`. Margines czysty wzorzec minus rekombinacja wyniósł `0,248253` dla lokalnego zwycięzcy, `-0,270473` dla globalnego update'u i `-0,269789` dla jednej gałęzi. Separacja zwycięskich gałęzi wyniosła `0,936235/0/0`, a użycie dwóch gałęzi `0,970000/1/0` (local/global/single). Globalny wariant miał czyste/rekombinowane odpowiedzi `0,727267/0,997740`, lokalny `0,987086/0,738833`: globalna reguła uśredniła oba wzorce.

Rozumowanie: lokalna konkurencja może zachować dwa prototypy bez etykiet, ale efekt jest tylko wynikiem toy probe'a na wektorach. Następny krok to rodzina parametryczna lub kandydat organizmu z lokalnymi gałęziami, obowiązkowo z ablacją liczby gałęzi, normalizacji i zmiany rozkładu.

Audyt `audit/life_strategy_probe.result.json` (wiadomość krytyka na tablicy) wykazał u lidera `life_metabolic_context` dokładność dekodera `room_context=0,9765625`; po zamianie sąsiednich pikseli odsetek zmian kontekstu wyniósł `0,51953125`, a sekwencja gryzienia była `1,0,0,0,0` powtarzana przez bramkę `age % 5`. To wskazuje na zależność od formatu świata i zegara, nie na samą zasadę metaboliczną. Odpowiedź na tablicy wymaga ablacją permutacji oka i impulsu wieku; moja zasada gałęzi również nie ma jeszcze wyniku pełnego judge.

## 2026-10-24: Fale siatkówkowe jako instrukcja topografii

Otworzyłem przez `.venv/bin/python shared/lit.py fetch https://pmc.ncbi.nlm.nih.gov/articles/PMC3119851/` Cang et al., *Neuron* 49 (2006). Autorzy rozdzielili poziom aktywności od jej wzoru: częstość RGC wynosiła `0,17±0,12 Hz` WT i `0,21±0,08 Hz` beta2(TG), `P=0,54`, ale rozmiar fali był `3–5x` mniejszy. Mapa retinotopowa SC pozostawała podobnie skupiona (`1,08±0,48%` vs `1,05±0,25%`), zaś segregacja oka była zaburzona. Fakt wspiera test wzoru czasoprzestrzennego, nie tezę, że większa aktywność sama uczy mapę.

Dodałem `biology/retinal_wave_probe.py`. W 100 seedach, `N=32`, 3000 zdarzeń i sumie aktywności `1` na zdarzenie lokalny zwycięzca oraz sąsiedzi uczyli z fal: `map_score/coverage/neighbor_step = 0,749254/0,816875/1,378750`. Losowe impulsy o tej samej sumie dały `0,391106/0,492813/3,288750`, globalny wzorzec `0,191217/0,204375/0,962500`, a fala bez sąsiedztwa `0,193280/0,218125/1,810625`. Niski krok globalny oznacza zapadnięcie do jednego kodu, więc pokrycie jest konieczne.

Rozumowanie: korelacja fal może dostarczać relacji topologicznej bez nagrody, ale potrzebuje lokalnej konkurencji wyjściowej, aby przełożyć się na uporządkowaną mapę. To toy probe bez świata organizmu, energii i zmiany topologii; następny krok to kandydat pełnego judge z ablacją sigma fali, promienia sąsiedztwa i zmianą rozkładu wejść.

## 2026-10-24: Zagęszczenie i lokalna odbudowa po ubytku

Otworzyłem przez `.venv/bin/python shared/lit.py fetch https://pmc.ncbi.nlm.nih.gov/articles/PMC4593481/` Eisenhoffer et al. (*Nature* 484, 2012). W jelicie ludzkim, naskórku danio i przepełnionym MDCK odpowiednio `80%` (`n=46`), `88%` (`n=160`) i `67%` (`n=300`) ekstrudowanych komórek było kaspazo-ujemnych. Obszary ekstrudowania były `1,7--1,8x` gęstsze; po zwiększeniu gęstości monowarstwy `112±5 -> 144±4` komórek/100 µm² liczebność wracała do `110±10` po 6 h. To sugeruje lokalny czujnik zagęszczenia równoważący podział i ekstrudowanie.

Napisałem `biology/crowding_turnover_probe.py`. W 100 sparowanych seedach, 96 miejscach, 64 komórkach początkowych i dwóch fazach po 1800 zdarzeń wprowadziłem ośmiomiejscową lesję w połowie fazy przesuniętej. Brak obrotu/globalna wymiana/lokalna gęstość dały odpowiednio pokrycie fazy przesuniętej `0,915674/0,957595/0,911575` oraz odbudowę lesji `0,000000/0,188750±0,121829/0,511250±0,083094`; liczebność końcowa lokalnej reguły `63,95±1,72`. Lokalność odbudowała ponad dwa razy więcej lesji niż globalna wymiana, lecz obniżyła pokrycie.

Wniosek: sprzężenie zagęszczenie--obrót jest kandydatem na odporność przestrzenną, nie uniwersalny sposób poprawy reprezentacji. Następny test powinien zmieniać promień i progi (`3/6`), rozmiar ubytku oraz koszt mutacji w pełnym judge; metryki odbudowy i pokrycia muszą pozostać rozdzielone.

## 2026-10-24: Heterosynaptyczna depresja jako lokalny set-point E/I

Otworzyłem przez `.venv/bin/python shared/lit.py fetch` Field et al., *Neuron* 106, 842--854 (2020), PMCID `PMC7274908`. W 25 komórkach młodej kory parowanie pre--post zwiększyło sparowane EPSC `40,3±10,5%` i IPSC `53,7±13,9%`, a na najsilniejszych niesparowanych wejściach wywołało LTD `−21,7±4,1%` i `−15,4±6,0%`; pozostałe wejścia zmieniły się o `1,4±8,0%` i `0,7±4,6%`. Heterosynaptyczne tau wynosiły `7,0±1,6` i `14,4±1,8` min wobec homosynaptycznych `2,3±0,9` i `4,1±1,1` min. To podpiera regułę szybkiego wzmacniania aktywnych krawędzi plus wolnego, selektywnego osłabiania najsilniejszych nieaktywnych.

Dodałem `biology/heterosynaptic_setpoint_probe.py`. Probe ma 100 sparowanych seedów, 12 jednostek, 24 kanały i dwie fazy po 1200 zdarzeń; porównuje brak depresji, lokalną depresję top-k, globalny budżet i losowy top-k. Selektywność czyste wzorce/mieszanka wyniosła `1,059206/1,106273/1,067410/1,064565`; SD lokalnej `0,034652`. Korelacja E/I wyniosła `0,996794/0,989482/0,996869/0,996824`, a odchylenie E/I `0,237371/0,232749/0,236267/0,236568`. Lokalność poprawiła selektywność, lecz obniżyła korelację; wynik nie jest uniwersalną poprawą i nie był testowany w judge.

## 2026-10-24: Odporność przyczynowego okna ochrony podczas snu

Otworzyłem przez `.venv/bin/python shared/lit.py fetch` González-Rueda et al., *Neuron* 97 (2018), PMCID `PMC5873548`. Autorzy opisują, że w stanie Up presynaptyczna aktywność prowadzi do depresji, a post-spike `+10 ms` chroni synapsę (`100% +/- 9%`, n=7), podczas gdy `+50 ms` (`53% +/- 8%`, n=5) i `-10 ms` (`66% +/- 7%`, n=7) nie chronią; ich model zwiększał S/N z `1,1` do `2,5` po czuwaniu i do `11,2` po selektywnym downscalingu.

Dodałem `biology/sleep_causal_window_robustness.py` i uruchomiłem 100 seedów dla okien `0/5/10/20/50 ms`, offsetów `5/10/20/50 ms`, prawdopodobieństwa post celu `0,8/0,4/0,1` i tempa `0,0015/0,003/0,006`. Przy `window=20`, `offset=10`, `target=0,8`, `decay=0,003` S/N/retencja wyniosły `2,756615/0,974834`, wobec `2,500578/0,888612` poza oknem. Przy target `0,1` S/N spadło do `2,526418`, a przy decay `0,006` retencja wyniosła `0,798457`. To wspiera zasadę alokacji stałego kosztu przez lokalną korelację, nie uniwersalny zysk pamięci; nie uruchamiano pełnego judge.

## 2026-10-24: Odporność heterosynaptycznej depresji na parametry i rozkład wejść

Rozszerzyłem `biology/heterosynaptic_setpoint_probe.py` o 100 sparowanych seedów na wariant, trzy rozkłady bodźców (klastrowany, niezależny rzadki `p=0,12`, niezależny gęsty `p=0,50`) oraz pięć ustawień tempa/k (`rate=0,002/0,010/0,030` przy `k=0,25`; `rate=0,010` przy `k=0,125/0,50`). Wszystkie warunki zachowują identyczny szybki update i normę; porównanie jest lokalna depresja vs homo-only.

Klastry: bazowa selektywność `1,059206`; lokalna wyniosła `1,066009` przy `0,002/0,25`, `1,106273` przy `0,010/0,25`, `1,091221` przy `0,030/0,25`, `1,077673` przy `0,010/0,125` i `1,126382` przy `0,010/0,50`. Korelacja E/I przy najszybszym tempie spadła do `0,666642`, a największe `k` obniżyło ją do `0,987693`.

Rzadkie wejścia: baseline selektywność/korelacja `1,089390/0,073379`; warianty lokalne miały selektywność `1,067602--1,075857` i korelację `−0,337105--−0,991906`. Gęste wejścia: baseline `1,108620/0,764618`; warianty lokalne selektywność `1,071674--1,097797`, choć korelacja zależała od ustawienia (`0,615508--0,852870`). Wniosek: pierwotny zysk dotyczył konkretnej statystyki bodźca, nie ogólnej zasady. Plik z liczbami: `biology/heterosynaptic_setpoint_probe.robustness.txt`. Nie uruchamiano pełnego judge.
## 2026-10-24: Rozwojowe przełączenie znaku STDP

Otworzyłem przez `.venv/bin/python shared/lit.py fetch https://pmc.ncbi.nlm.nih.gov/articles/PMC4926245/` pełny tekst Itami et al. (*J Neurosci* 2016). W synapsach TCA->L2/3 t-LTP malało po P4--P5 i przechodziło po P7--P8 w t-LTD; losowa korelacja pre/post dawała `126,4+/-9,1%` kontroli u P5--P6 oraz `54,4+/-6,8%` u P8--P13. To kandydat na program rozwojowy, który najpierw buduje, a potem rafinuje przez zmianę znaku lokalnej korelacji.

Dodałem `biology/developmental_stdp_switch_probe.py`. 100 seedów, 32 wejścia/jednostki, 2400 zdarzeń, przełączenie po 1200. `switch` dał pokrycie/margines/skok/korelację faz `0,393750/0,059191/3,979677/0,085327`; zawsze-LTP `0,168750/0,319461/1,349355/0,027438`; zawsze-LTD `0,550000/0,003799/5,812903/-0,146012`; brak `0,362812/0,028287/3,137097/-0,258091`. Przy przełączeniu po 600/1200/1800 pokrycie wyniosło `0,498750/0,393750/0,213750`. Wniosek: znak steruje kompromisem różnorodność--selektywność, lecz wymaga strojenia czasu i nie jest dowodem przewagi w organizmie.

## 2026-10-24: Test przełącznika wieku z bilansem energii

Pełny v7 kandydata uruchomiłem z `--organism --organism-version v7 --organism-seeds 1 --author biolog`. Po 45 min przerwałem oczekiwanie w `_gpu_slot`; traceback wskazuje kolejkę do slotu GPU i nie ma wyniku ani wpisu score. Nie wolno traktować tego jako wyniku organizmu. Implementacja i wrapper przechodzą `py_compile`.

Zbudowałem `biology/developmental_metabolic_switch_probe.py` i uruchomiłem 200 seedów na wariant. Przełącznik po 2400/6000 kroków miał zgodność okien `0,017892/0,104867/0,144392/0,000000` i held-out `0,000000`; zawsze-LTP `0,017892/0,104867/1,000000/0,071992`, held-out `0,002500`; zawsze-LTD `0,950042/0/0/0,777492`, held-out `0,995000`; none `0,5/0/0,5/0,5`, held-out `0,5`. Wniosek: znak LTD może pasować do tego konkretnego odwrócenia, ale przełącznik nie zachowuje znaczenia bilansu i nie jest odporny. Dodałem kandydat `candidates/biolog_developmental_switch` z lokalnym wiekiem, miękkim przejściem i testem v7 w toku.
## 2026-10-25: Rozwojowa polaryzacja GABA jako kompromis rekrutacja--separacja

Otworzyłem przez `.venv/bin/python shared/lit.py fetch https://pmc.ncbi.nlm.nih.gov/articles/PMC4501047/` Chabwine et al. (BMC Neurosci 2015). W małych DRGN `[Cl−]i` spadło z `44 mM` (E14) do `30/29 mM` (E16/E19), a udział NKCC1 z `57%` do `33%/38%`; stała powrotu po opróżnieniu chlorku wzrosła z `0,9` do `1,64 min`.

Dodałem `biology/gaba_polarity_probe.py` i uruchomiłem 100 seedów, 16 jednostek, 32 kanały, 1200 kroków, cztery znaki GABA. Separacja `none/depolarizing/hyperpolarizing/developmental` wyniosła `0,010449/0,002727/1,175535/0,768122`; pokrycie wczesne/późne dla przełącznika `0,909563/0,806056`, dla stałej hiperpolaryzacji `0,715262/0,604203`. Zmiana `eta=0,001/0,002/0,004` dała separację `0,378908/0,768122/0,925094`.

Wniosek: przełączenie daje więcej aktywnych jednostek niż stały hamulec, lecz słabszą separację i wyraźną zależność od skali aktualizacji. To probe mechanizmu, bez pełnego judge; następny test powinien modelować stan chlorku i moment przełączenia.

## 2026-10-25: Kinetyka chlorku rozciąga kompromis rekrutacja--separacja

Ponownie otworzyłem przez `.venv/bin/python shared/lit.py fetch https://pmc.ncbi.nlm.nih.gov/articles/PMC4501047/` Chabwine et al. (2015). Ich dane o `[Cl−]i` (E14 `44±2 mM`, E16 `30±2`, E19 `29±1`; n=`71/11/13`) oraz asymetrycznych powrotach po obciążeniu i opróżnieniu (E19 tau `2,97` i `1,64 min`, E14 opróżnianie `0,9 min`) motywują model stanu z ograniczoną szybkością, ale nie dostarczają mapowania minut na kroki cyfrowe.

Dodałem `biology/gaba_chloride_kinetics_probe.py` i wynik `biology/gaba_chloride_kinetics_probe.result.txt`. W 100 seedach, 16 jednostkach, 32 wejściach i 1200 krokach stałe znaki dały separację `none/depolarizing/hyperpolarizing = 0,010452/0,002727/1,175275`. Przy kinetyce `tau=120`, przesunięcie dojrzewania `25/50/75%` dało separację `0,841676/0,504794/0,221299`, pokrycie późne `0,777353/0,845391/0,936934`. Dla dojrzewania 50%, `tau=30/120/480` dało separację `0,534583/0,504794/0,040284`; sztuczny ładunek ±`0,0002` zmienił wynik tylko do `0,503989/0,487126`.

Interpretacja: późniejsze dojrzewanie utrzymuje rekrutację, wcześniejsze lepiej separuje klasy; zbyt wolna zmiana nie zdąży ujawnić hamowania w krótkim życiu. Ten probe jest toy modelem z ręcznie zadanym celem chlorku, nie implementacją transportu ani testem judge. Nie mapować `tau` na organizm bez skalowania czasu; następny krok to sprawdzić, czy lokalny stan chlorku zależny od aktywności wnosi coś ponad zwykły harmonogram, z ablacją bocznego sprzężenia.

## 2026-10-25: Lokalny ładunek chlorku nie pobił harmonogramu GABA

Ponownie otworzyłem przez `.venv/bin/python shared/lit.py fetch` Chabwine et al., *BMC Neuroscience* 16, 41 (2015), PMCID `PMC4501047`. Oprócz spadku [Cl−]i `44±2 -> 30±2 -> 29±1 mM` (E14/E16/E19) i udziału NKCC1 `57% -> 33%/38%`, autorzy stosowali 5-sekundowe impulsy GABA do ładowania i opróżniania chlorku; powrót po opróżnieniu trwał `1,64 min` w E19 i `0,9 min` w E14.

Dodałem `biology/gaba_local_state_probe.py` i uruchomiłem 100 seedów (16 jednostek, 32 wejścia, 1200 kroków). Przy `tau=120` harmonogram bez lokalnego ładunku miał separację/pokrycie wczesne/późne/średni chlorek `0,504794/0,952334/0,845391/0,006598`; stan lokalny z `q=0,0015*y_i` `0,343280/0,982422/0,929741/0,174769`, a ablacją `q=0,0015*mean(y)` `0,327397/0,984279/0,937134/0,175410`. Sparowana różnica lokalny minus ablacją to `+0,015883` (SD `0,009252`) separacji i `−0,007394` (SD `0,004315`) pokrycia późnego. `tau=30` dawało separację `0,503210`, `tau=480` `0,002670`; stałe hiperpolarizing `1,175275`.

Wniosek: lokalne ładowanie zwiększa rekrutację i opóźnia rafinację, ale w tej konstrukcji nie daje stabilnej przewagi nad harmonogramem ani wyraźnej przewagi nad globalną ablacją. To probe mechanizmu, bez pełnego judge; nie promować H013 na podstawie tych liczb.

## 2026-10-25: Tryb usuwania przegranych zależy od architektury

Otworzyłem `.venv/bin/python shared/lit.py fetch https://pmc.ncbi.nlm.nih.gov/articles/PMC6638572/` (Ellis et al., *Nature* 2019). W mysiej epidermie rozwijającej się do pola >30x, mozaikowe `Mycn+/−` komórki w kontakcie z co najmniej jednym `Mycn+/+` ginęły około 4x częściej niż WT-WT lub `Mycn+/−` w jednorodnym otoczeniu. Artykuł opisuje wczesne zabijanie/engulfment w monowarstwie i późniejszy wypływ przegranych przez różnicowanie po uwarstwieniu; zakłócenie konkurencji zaburzało barierę. Wniosek mechanistyczny: wynik lokalnej konkurencji jest względny, a droga eliminacji zmienia się z architekturą.

Dodałem `biology/competition_reserve_probe.py`: 100 seedów, 128 jednostek, trzy fazy A→B→A po 1200 interakcji, wspólny sąsiedzki test sprawności. Usuwanie i rezerwa bez odczytu dały A/B/A `0,990905/0,961570/0,990853`; rezerwa z odczytem `0,992250/0,991818/0,992069`. W tym toy modelu odzyskanie zapisanych wektorów sprawiło, że po zmianie kontekstu sprawność B wzrosła o `0,030248`, a SD spadło z `0,026264` do `0,002256`; samo składowanie bez przywołania nie zmieniało wyniku. To architektoniczna analogia, nie model naskórka ani wynik judge. Pełny zapis w `biology/competition_reserve_probe.result.txt`.
## 2026-10-25: Ablacja konkurencji troficznej przy równym budżecie eliminacji

Otwarty wcześniej przez `shared/lit.py fetch` Deppmann et al. (*Science*, 2008; PMCID PMC3612357) stanowi źródło faktu biologicznego użytego w zasadzie 20: p75 może wzmacniać eliminację neuronów z niskim sygnałem TrkA, zaś różnica liczby neuronów u `p75-/-` była przejściowa (około 40% nadmiaru w P0/P3, brak różnicy w 6 miesiącu). Poprzedni probe zmieniał jednocześnie liczbę rund i liczbę ocalałych, więc dodałem `biology/trk_survival_budget_probe.py`, gdzie każdy wariant ma 4 zgony/rundę i dokładnie 64 ocalałych po 48 rundach.

W 100 sparowanych seedach jakość A/B i udział właściwego typu A/B wyniosły: full `0,649148/0,646711`, `0,622031/0,628125`; bez uwrażliwiania `0,631207/0,631272`, `0,600156/0,618281`; bez parakrynnego sygnału `0,666632/0,666233`, `0,643750/0,664531`; bez ochrony `0,634863/0,633682`, `0,606719/0,612812`; all-off `0,654835/0,652508`, `0,639062/0,633437`. Wynik sugeruje w tym ręcznie skonstruowanym hazardzie, że parakrynny składnik szkodzi selekcji przy stałym budżecie, zaś uwrażliwianie poprawia ją względem własnej ablacji. Nie wynika z tego, że mechanizm p75 jest biologicznie zbędny: model nie zawiera mechaniki molekularnej ani rzeczywistego organizmu. `py_compile` i uruchomienie przeszły; szczegóły: `biology/trk_survival_budget_probe.result.txt`.
## 2026-10-25: lokalna homeostaza chlorku

Dodałem `biology/gaba_homeostasis_probe.py`, aby rozdzielić aktywnościowe ładowanie chlorku od dojrzałościowego wypływu KCC2-podobnego. Źródła otwarte przez `shared/lit.py fetch`: Ludwig et al. 2017 (PMCID PMC5286847), gdzie KCC2 jest neuronalnym transporterem wypływu Cl− i mierzono furosemidozależną dynamikę, oraz Chabwine et al. 2015 (PMCID PMC4501047): [Cl−]i 44 mM E14, 30/29 mM E16/E19; udział NKCC1 57%, 33%/38%.

Uruchomienie: 100 seedów, 16 jednostek, 32 wejścia, 1200 kroków. `tau=120`: local load+extrusion separacja/pokrycie późne `0,419185/0,887912`, global `0,416854/0,890631`, extrusion-only `0,519694/0,842225`, load-only `0,343280/0,929741`, none `0,010452/1,000000`. Sparowana local-global: separacja `+0,002330` (SD `0,007228`), późne pokrycie `−0,002719` (SD `0,002695`); local wygrywał separację w 60%, pokrycie w 13%. Dla tau `30/120/480` separacja `0,517524/0,419185/0,023259`. Zaktualizowano zasadę 30 i RULES: lokalność sama nie daje stabilnego zysku, a ładowanie i wypływ muszą być ablowowane osobno. Wynik nie jest testem judge.
## 2026-10-25: Lokalny mnożnik kontra skalowanie afiniczne

Otworzyłem przez `.venv/bin/python shared/lit.py fetch` Kim, Tsien i Alger, *PLoS ONE* 7, e37364 (2012), PMCID `PMC3355135`. Autorzy ostrzegają, że dopasowanie `y=ax+b` nie jest czystym skalowaniem: dla mIPSC średnie wynosiły `58±6` i `91±9 pA`, a czysty mnożnik odtwarzał rozkład gorzej (`p=1,3×10^-14`); dla mEPSC podano `p=9,7×10^-9`.

Dodałem `biology/affine_scaling_probe.py`. W 100 seedach, 64 jednostkach i perturbacji połowy jednostek przez `0,4`, lokalny mnożnik przywrócił aktywność i relacje wag (`0,000000/0,000000`) oraz margines (`1,000000`). Globalny mnożnik miał błąd aktywności `0,423245`. Lokalna afiniczna (`a=0,75`) i addytywna zmieniły relacje (`ratio_rmse=0,211703/0,181456`) i margines (`0,650574/0,700492`) mimo zerowego błędu aktywności. To wspiera ablowanie składnika addytywnego, ale probe ma łatwą separację klas i nie jest wynikiem judge.
## 2026-10-25: geometria kontaktu w lateralnej inhibicji

Otworzyłem przez `.venv/bin/python shared/lit.py fetch` Richa et al., *Current Biology* 36 (2026), PMCID `PMC7619482`. W wyborze neuroblastu długość interfejsu neuroblast--sąsiad miała AUC `0,76`, czas kontaktu `0,55`; model z małym zróżnicowaniem pola komórek przewidywał bias przed aktywacją transkrypcyjną. Transkrypcja trwała `22,6±5` min w kontroli i `38,3±5` min po zahamowaniu Rho-kinazy.

Napisałem `biology/notch_contact_probe.py`: 100 seedów, klaster 3x3, 80 iteracji, równy krok aktualizacji. Unikalność/margines/ranga pola zwycięzcy: lokalne ważenie `0,660000/0,417407/0,823750`, jednorodne sąsiedztwo `0,670000/0,429874/0,830000`, globalne `0,840000/2,391637/0,950000`, brak biasu `0,000000/0,055992/0,413750`. Geometria nie pobiła prostszego hamowania; globalny margines wynikał z wyboru największej komórki. Wniosek: w cyfrowym mechanizmie trzeba ablowować początkowy bias i raportować zapadanie różnorodności razem z separacją. Wynik jest toy probe, nie pełny judge.

## 2026-10-25: odporność geometrii kontaktu i miara zapadania

Zgodnie z handoffem dodałem `biology/notch_contact_robustness_probe.py`. Każdą z 20 geometrii powtarzałem 20 razy z nowym szumem molekularnym; zmieniałem rozmiar klastra `2x2/3x3/4x4`, SD pola `0,04/0,08/0,16` i szum interfejsu `0/0,15/0,30`. Dla `3x3`, SD `0,08`, szumu `0,15`, lokalne/jednorodne/globalne/brak biasu dały unikalność `0,677500/0,712500/0,857500/0,012500`, margines `0,417303/0,442117/2,610845/0,059647`, rangę pola `0,800312/0,809375/0,970000/0,487187` i efektywną frakcję zwycięzców `0,563950/0,577291/0,893341/0,990604`. Efektywna frakcja to `exp(entropia zwycięzców)/N`; brak biasu jest różnorodny, lecz nie rozdziela zwycięzcy, natomiast globalne hamowanie ma duży margines i wybiera największą komórkę. Przy `4x4` mały szum obniżył lokalną unikalność do `0,550000` i frakcję do `0,286542`, więc wynik zależy od skali klastra. Probe nie wspiera mocnej wersji przewagi geometrii; pozostaje jedynie ograniczona hipoteza o lokalnym kontakcie z równym budżetem, wymagająca pełnego judge.
## 2026-10-25: Młode interneurony jako bramkowane rozdzielanie wzorców

Otworzyłem przez `.venv/bin/python shared/lit.py fetch https://pmc.ncbi.nlm.nih.gov/articles/PMC5912906/` Li et al. (eLife 2018). W opuszce węchowej myszy wyciszenie młodych ABN nie zmieniało łatwego rozróżniania (4,18±0,21 vs 4,39±0,25 sesji do >80%, p=0,4523), ale pogarszało trudne rozróżnianie podobnych mieszanin (kontrola w sesji 10: 0,760±0,017; różnica grup p<0,0001). Spadek dotyczył odpowiedzi supresyjnych komórek mitralnych (p<0,0001), nie pobudzających, i znikał przy biernej ekspozycji; losowa ablacja większej liczby dojrzałych komórek nie dawała tego samego deficytu.

Dodałem `biology/adultborn_pattern_probe.py`. Uczenie nie zna etykiet: młoda pula wolno estymuje wspólny kierunek i przy lokalnym zaangażowaniu odejmuje jego projekcję. W 200 seedach przy szumie 0,32 dokładność podobnych klas wyniosła none/random/young_off/young = 0,259703/0,260477/0,259703/0,277738 (SD młodej 0,024897); osobne łatwe klasy 0,3816 (random 0,3825). Przy szumie 0,24 młoda/brak = 0,375734/0,334055 (100 seedów), przy 0,40 = 0,226172/0,217977; przewaga zależy od SNR. Pierwszy wariant zbyt szybkiego śladu szkodził (0,175), więc wolna kinetyka i zamrożenie śladu w teście są konieczne.

Wniosek: zasada jest obiecująca wyłącznie jako bramkowane, anty-korelacyjne hamowanie podobnych wejść; nie przenosić jej do kandydata bez wyprowadzenia zaangażowania z interocepcji/niepewności i pełnego judge. Losowy kierunek oraz zamknięta bramka są obowiązkowymi ablacji.

## 2026-10-25: Próg AIS jako wolna, odwracalna regulacja pobudliwości

Otworzyłem przez `.venv/bin/python shared/lit.py fetch https://pmc.ncbi.nlm.nih.gov/articles/PMC3196626/` Grubb i Burrone (*Nature* 2010). W hodowli hipokampa 15 mM K+ przez 48 h przesuwało AIS do `17 µm` (885 komórek, 36 hodowli), nie zmieniając jego długości (`P=0,11`) ani poziomu PanNaV; powrót do 5 mM cofał położenie (194 komórki, 8 hodowli). Bursty działały przy tej samej średniej częstości, a regularne impulsy nie.

Dodałem `biology/ais_homeostasis_probe.py`. W 200 seedach, 48 jednostkach, trzech fazach gain `1,0/1,8/1,0`, lokalny próg AIS dał średnią aktywność `0,221674`, separację `1,148466`, przesunięcie progu `0,014851` i błąd powrotu `0,000654`; brak adaptacji miał aktywność `0,499808` i separację `1,190853`. Globalny próg był podobny (`0,221769/1,151081`), a skalowanie wag zmieniło kod (`code_change=0,182817`, norm ratio `0,101946`), podczas gdy AIS zachował wagi (`code_change=0`). Wariant burstowy nie wracał (`recovery error=0,092706`). To nie jest dowód przewagi w judge; zasada wymaga testu burst-vs-rate, lokalności i pełnego świata.

## 2026-10-25: sparowana odporność lokalnego ładowania chlorku

Odpowiedziałem na uwagi krytyka o H013, dodając `biology/gaba_local_state_robustness.py` i `biology/gaba_local_state_pairs.py`. Źródło Chabwine et al. (BMC Neurosci 2015, PMCID PMC4501047) otwarte ponownie przez `shared/lit.py fetch`: [Cl-]i `44±2` mM (E14, n=71), `30±2` (E16, n=11), `29±1` (E19, n=13), NKCC1 `57%` do `33/38%`, recovery po depletion `0,9` do `1,64` min.

W pełnym probe 100 seedów, 1200 kroków, 16 jednostek: dla wejścia blokowego separacja harmonogramu tau `30/120/480` = `0,536243/0,496269/0,040234`; lokalne `q=0,0015` = `0,329772`, globalne = `0,312889`, no-GABA = `0,010270`, fixed-hyper = `1,174218` przy late coverage `0,606613`. Dla rozproszonego wejścia harmonogram tau 120 = `0,024882`, lokalne/globalne = `0,011841/0,007045`.

Sparowane delty z tymi samymi seedami (kolejność metryk: separacja/early/late/chloride): blokowe local-q0 `-0,166496/+0,030175/+0,086500/+0,168532`, CI95 `0,016758/0,001270/0,004411/0,000626`; local-global `+0,016883/-0,001861/-0,007391/-0,000647`, CI95 `0,001625/0,000203/0,000817/0,000093`. Rozproszone local-q0 `-0,013041/+0,045903/+0,162744/+0,176249`, CI95 separacji `0,006391`; local-global separacja `+0,004796`, CI95 `0,000817`. Wniosek: ładowanie zwiększa rekrutację i obniża separację; lokalność daje mały, geometrii-zależny efekt nad średnią populacji. H013 pozostaje niepotwierdzona i nie pobija lidera.
## 2026-10-25: lokalne klastry gałęzi i odporność pamięci

Otworzyłem przez `.venv/bin/python shared/lit.py fetch https://pmc.ncbi.nlm.nih.gov/articles/PMC3292711/` Yadav et al. (*Nature* 2012). W korze ruchowej myszy 32,5+/-2,2% nowych kolców w fazie nabywania było w klastrach, wobec 6,8+/-4,6% u kontroli i 7,4+/-4,3% w późnej konsolidacji; klastry miały wyższe przeżycie po 16 dniach (p<0,01) i 4 miesiącach (p<0,05). To sugeruje, że powtarzana współaktywacja może być lokalnym mechanizmem zarówno nieliniowego sumowania, jak i retencji.

Dodałem `biology/dendritic_cluster_probe.py`. Model ma 24 wejścia w 6 blokach, 6 gałęzi, lokalny próg ReLU i aktualizację tylko aktywnej gałęzi; porównania zachowują liczbę synaps i aktualizacji. Przy 200 seedach i szumie 0,42 dokładność starych klas przed/po nowej fazie: cluster 0,262611/0,267542, random 0,171556/0,171743, global 0,166667/0,166667, fixed 0,222167/0,222167. Odporność 100 seedów: po fazie cluster/random = 0,208986/0,168139 przy szumie 0,30 oraz 0,439236/0,189069 przy 0,60. Zmiana odpowiedzi klastra po dystraktorze była 0,000175 (random 0,000002), więc stabilność nie oznacza poprawy funkcji sama w sobie.

Rozumowanie: lokalność daje separację tylko wtedy, gdy powtarzane współaktywne cechy trafiają do jednej gałęzi; globalna suma traci ten kod, a random mask nie ma geometrii. Wynik jest wąski i częściowo skonstruowany przez blokową maskę, dlatego zasada trafia do PRINCIPLES jako hipoteza mechanistyczna, nie rekomendacja dla judge. Następny test powinien uczyć przypisanie gałęzi z korelacji bez etykiet i sprawdzić pełny organism z permutacją oka.

## 2026-10-25: rzadkie silne krawędzie jako nośnik selektywności

Otworzyłem przez `.venv/bin/python shared/lit.py fetch https://pmc.ncbi.nlm.nih.gov/articles/PMC4843963/` Cossell et al. (*Nature* 2015). W L2/3 V1 korelacja odpowiedzi par miała medianę `0,012` (średnia `0,021+/-0,051`, zakres `-0,12...0,67`), połączonych było `75/520=0,14` par, a mediana EPSP wynosiła `0,19 mV`. Najsilniejsze `25%` wejść niosło `78%` sumy wagi; usunięcie tej grupy obniżało F1 o `95%`, pozostawienie tylko jej o `5%`.

Dodałem `biology/rare_strong_probe.py`. Reguła bez etykiet wzmacnia lokalnie współaktywne wejścia, zachowuje stały budżet wiersza i obcina do top-k; porównania to dense/global i losowy top-k. Przy 200 seedach i szumie `0,35` top-k miał selektywność `2,9270 -> 2,4807`, pokrycie `0,944 -> 0,950`, dokładność zamrożonego dekodera `0,976` i zmianę odpowiedzi `0,1590`; dense/global `1,3122 -> 1,1753`, pokrycie `0,134 -> 0,131`, dokładność `0,226`, zmiana `0,0945`; random top-k `2,8300 -> 1,5423`, pokrycie `0,950 -> 0,853`, zmiana `0,4059`. Przy szumie `0,60` top-k utrzymał retencję selektywności `0,9365`, losowy top-k `0,4492`.

Wniosek: w tej kontrolowanej rodzinie lokalna konkurencja odtwarza rzadkie, silne połączenia i daje selektywność, ale próg `k=25%` jest ręcznie zadany, a probe nie ma energii ani świata. Następny test: bezetykietowe uczenie liczby silnych krawędzi, zmiana korelacji wejść i pełna ablacją w judge.

## 2026-10-25: konkurencja ciągła nie odtwarza pruning

Otworzyłem przez `.venv/bin/python shared/lit.py fetch https://pmc.ncbi.nlm.nih.gov/articles/PMC11873734/` przegląd Fujimoto o konkurencji dendrytów komórek mitralnych. Liczby orientacyjne z tekstu: około `1000` receptorów/kłębuszków i `20--50` komórek mitralnych na kłębuszek; komórka przechodzi od wielu dendrytów do jednego w pierwszym tygodniu poporodowym. To motywuje rozdzielenie stabilizacji od aktywnej eliminacji.

Dodałem `biology/continuous_competition_probe.py`. Oja-local (lokalna reguła Oja i renormalizacja wiersza) oraz dense/global były nierozróżnialne w 200 seedach: selektywność przed `1,3143/1,3122/1,3122`, accuracy `0,2263/0,2256/0,2256`, retencja `0,9059/0,9066/0,9066`. Top-k 25% miał `2,9270` selektywności, accuracy `0,9758`, pokrycie `0,9438`, retencję `0,8482`. Przy szumie `0,60` Oja retencja `0,9580`, top-k `0,9365`, ale top-k nadal miał selektywność `1,9171` po dystraktorze wobec `1,1362` Oja.

Wniosek: sama konkurencja o ciągłą masę nie jest równoważna aktywnemu pruningowi. To toy refutacja, nie wynik pełnego judge. Następny mechanizm powinien obracać krawędzie przez lokalny ślad kosztu/zużycia bez stałego `k`, a potem przejść pełne ablacjami przez świat organizmu.

## 2026-10-25: lokalny ślad obrotu krawędzi nie daje przewagi

Otworzyłem przez `.venv/bin/python shared/lit.py fetch https://pmc.ncbi.nlm.nih.gov/articles/PMC8541743/` przegląd Neniskyte i Gross. W obwodzie siatkówka--LGN autorzy podają przerzedzanie przed P10 i dalszą przebudowę kolców po świetle w P20--P30; słabsze synapsy są usuwane, a inne utrzymywane i wzmacniane. Zasada cyfrowa miała wykładniczy lokalny ślad użycia oraz hazard wymiany `w*(1-u/max(u))`, z losowym obrotem przy tym samym koszcie jako kontrolą.

Dodałem `biology/trace_edge_turnover_probe.py`. W 20 seedach, 48 jednostkach, 24 wejściach i fazach 800+800 zdarzeń, przy szumie `0,35`, retencja bez obrotu / ślad / losowo = `0,893340/0,893206/0,893130`, accuracy = `0,227875/0,229688/0,233000`, a liczba obrotów = `0/153,7/154,85`. Przy szumie `0,60` retencja = `0,957846/0,957750/0,957653`, accuracy = `0,179125/0,179688/0,179688`, obroty = `0/153,7/154,85`. Lokalny ślad nie poprawił starego kodu względem losowej wymiany. To refutacja tej implementacji, nie pełny judge.

## 2026-10-25: KCC2 jako przyczyna, nie zegar GABA

Otworzyłem przez `.venv/bin/python shared/lit.py fetch https://pmc.ncbi.nlm.nih.gov/articles/PMC2945502/` Lee et al. (2005). Przedwczesny hKCC2 w niedojrzałych neuronach przesunął `E_GABA` o `13 mV` (`-54 -> -67 mV`), a szacowane `[Cl-]i` spadło `18 -> 11 mM`; odpowiedzi wapniowe na GABA znikały lub słabły.

Dodałem `biology/kcc2_sufficiency_probe.py` i uruchomiłem `120` sparowanych seedów. `no_kcc2` miał proxy Ca `1,662751/2,103573` (wczesne/późne) i separację `0,003257`; `premature` `0/0` i `0,600641`; `endogenous` `0,102103/0` i `0,350826`; bezpośredni `fixed_schedule` `0,235137/0` i `0,826072`. Gain endogenny `0,40/0,80/1,20` zmieniał separację `0,006557/0,350826/0,644676`, a tempo transportu `0,010/0,020/0,040` przy gain `0,80` dawało `0,006557/0,350826/0,698070`.

Wniosek: stan transportera jest przyczynowo potrzebny do wygaszenia depolaryzacji w tym modelu, ale nie pobił ręcznego harmonogramu i jest wrażliwy na skalę. To nie jest wynik organism judge; wymagane są jawne perturbacje `k_i`, ablacją transportu i test skali czasu.

## 2026-10-25: faza lokalna jako sygnał remodelingu przewodzenia

Otworzyłem przez `.venv/bin/python shared/lit.py fetch https://pmc.ncbi.nlm.nih.gov/articles/PMC7306810/` Noori et al. (2020), model synchronizacji z aktywnością-zależną mieliną. W artykule `tau≈l/c`, lokalna faza wpływa na prędkość przewodzenia, a koszt metaboliczny przyciąga ją do poziomu bazowego; modelowe prędkości mieściły się w granicach `3–100 m/s`. Autorzy raportują synchronizację i odporność na spadek łączności, ale zaznaczają, że lokalna faza jest fenomenologicznym mechanizmem, a biologiczny mechanizm pozostaje słabo poznany.

Dodałem `biology/phase_myelin_probe.py`. W 100 seedach i dwóch fazach obciążenia błąd fazy na aktywnych trasach spadł z `1,567818/1,559473 rad` bez adaptacji do `0,581169/0,579965` z korektą fazy; samo skracanie często używanych tras dało `1,551786/1,542135`. Składnik kosztu zmienił błąd tylko do `0,589180/0,587414`, bez poprawy wobec `phase_only`. Próba ma zadany offset fazowy i projektowaną regułę korekty; to test algebraiczny, nie dynamika oscylatorów ani judge. Wniosek: warto rozdzielać sygnał fazy od częstości użycia, lecz brak tu dowodu funkcjonalnego lub na korzyść kosztu.

## 2026-10-25: astrocytarny filtr metaboliczny

Otworzyłem przez `.venv/bin/python shared/lit.py fetch https://pmc.ncbi.nlm.nih.gov/articles/PMC5792514/` Barros i Weber (2018). Przegląd podaje wzrost laktatu po zadaniu pamięci około `10 µM/s` przy spoczynkowym `1 mM`, zużycie po odstawieniu znieczulenia około `5 µM/s` i uwalnianie bramkowane K+; podkreśla też, że pełny ANLS pozostaje dyskutowany.

Dodałem `biology/astro_lactate_shuttle_probe.py`. Przy 200 seedach i 4500 krokach bezpośredni sygnał energetyczny miał zgodność po odwróceniu/powrocie `0,109875/0,124737` i opóźnienie odzysku `823,625`. Lokalny filtr czasowy dał `0,308600/0,306950`, `533,750`, a globalny filtr `0,321687/0,320200`, `499,625`. Ablacja szybkości lokalnego filtra (`alpha=0,02/0,08/0,20`) dała po zmianie/powrocie `0,305725/0,303325`, `0,306300/0,322375`, `0,209025/0,209925`.

Wniosek: bufor czasowy stabilizował zapis z własnego bilansu, lecz lokalność przegrała z filtrem globalnym w tej konstrukcji. Nie twierdzić, że to dowód astrocytarnej topologii ani przewagi nad liderem; następny krok to perturbacja lokalnego rezerwuaru w pełnym judge.

## 2026-10-25: przeciek między lokalnymi buforami

Ponownie otworzyłem `.venv/bin/python shared/lit.py fetch https://pmc.ncbi.nlm.nih.gov/articles/PMC5792514/`; Barros i Weber przedstawiają ANLS jako propozycję, nie konsensus, co nie uzasadnia przyjęcia lokalności w modelu.

Dodałem parametr przecieku do `biology/astro_lactate_shuttle_probe.py` oraz osobną sondę `biology/astro_lactate_crosstalk_probe.py`. Przeciek miesza stan czterech rezerwuarów zgodnie z `r += lambda*(mean(r)-r)`. Na 100 wspólnych seedach, 4500 krokach i zadaniu z dwoma odwróceniami, trafność po pierwszym odwróceniu dla `lambda=0/0,1/0,3/0,6/1` to `0,306300/0,311050/0,318375/0,334875/0,365875`; zgodność po powrocie `0,322375/0,287775/0,308700/0,342350/0,330425`; opóźnienie `516,75/579,25/590,75/578,75/453,75`. Pełne mieszanie dało sparowaną zmianę po pierwszym odwróceniu `+0,059575` (95% CI `0,030525–0,088625`), ale różnica dla okna powrotu i opóźnienia nie była rozstrzygająca. Globalny filtr miał po zmianie `0,314650` i opóźnienie `480,5`, bez istotnej różnicy względem lokalnego bufora w sparowanych CI.

Wniosek: rozchodzenie się endogennego sygnału może pomóc jednemu typowi zmiany w tym toy zadaniu; nie pokazuje przewagi lokalności ani poprawy organizmu. Koszt przecieku i pełny judge z lokalnym/globalnym wariantem pozostają nieprzetestowane. Dane: `biology/astro_lactate_crosstalk_probe.result.txt`.

## 2026-10-25: przeciek buforów przy zmiennym szumie

Dodałem `biology/astro_crosstalk_noise_probe.py`; uruchomiłem 100 wspólnych seedów na każdy szum `0,02/0,08/0,20`, porównując bufor lokalny, przeciek `0,3`, przeciek `1,0` oraz wariant globalny. Przy szumie `0,02` pełny przeciek poprawił trafność po odwróceniu o `0,044450` (95% sparowany CI `0,001844–0,087056`) i po powrocie o `0,087425` (`0,046780–0,128070`); przy `0,08` poprawił tylko pierwsze okno (`+0,059575`, `0,030525–0,088625`); przy `0,20` różnice obu okien obejmowały zero (`+0,024400`, `-0,010965–0,059765`; powrót `+0,022425`, `-0,010152–0,055002`). Opóźnienia były zmienne i bez rozstrzygającej różnicy. Wynik zaostrza §42: przeciek może poprawić adaptację przy częściowo niskim szumie, ale nie jest odporną regułą. To probe syntetyczne, bez kosztu przepływu i świata organizmu. Raport: `biology/astro_crosstalk_noise_probe.result.txt`.

## 2026-10-25: arbitralny koszt transferu rezerwuarów

Dodałem do `astro_lactate_shuttle_probe.py` `transfer_cost`, odejmujący od energii koszt razy średnia wartość bezwzględnego przepływu między buforami. `astro_transfer_cost_probe.py` uruchomił 100 wspólnych seedów dla przecieku `0/0,3/1` i podatku `0/0,01/0,05` (szum `0,08`). Pełny przeciek vs izolowane bufory dał delty trafności po zmianie `+0,059575/+0,073925/+0,043000`, wszystkie 95% CI powyżej zera; po powrocie `+0,008050/+0,042775/+0,031125`, istotna tylko środkowa. Średnie opóźnienie: `-63/-51,25/+19,5` kroków; CI obejmowały zero. Nie ma monotonicznego zmniejszania efektu z podatkiem. Koszt jest arbitralny i sprzężony z energią obcinaną do `[0,1]`; nie jest biologiczną kalibracją. Raport: `astro_transfer_cost_probe.result.txt`.
## 2026-10-25: PNN jako hamulec otwierany nowością

Otworzyłem przez `.venv/bin/python shared/lit.py fetch https://www.nature.com/articles/s41598-017-04007-x` Sorg et al., *Scientific Reports* 2017. W dorosłej V1 CS wynosił `2134,4±123,2` pmol/mg WT vs `1169,5±52,9` T1-KO (`4` myszy, p=`0,002`), a diazepam dawał ostrość oka deprywowanego `0,29±0,01` po pierwszym podaniu i `0,50±0,03` po drugim, wobec `0,54±0,02` pojazdu. To wspiera dwufazowe strojenie PV/PNN, nie prosty zegar zamykający plastyczność.

Uruchomiłem `nice -n 15 .venv/bin/python biology/pnn_gate_probe.py` (120 seedów, fazy 600/600 i recall 200). Błąd B/A-recall: frozen `0,827108/0,830112`, always `0,006735/0,979105`, brake-only `0,687678/0,092675`, input-ablated `0,992157/0,000840`, input-coupled `0,196095/0,546293`. Sprzężenie nowości poprawiło uczenie B względem stałego hamulca, lecz kosztowało retencję A; brak sygnału wejściowego zablokował B. Uzupełniłem §8 w `PRINCIPLES.md` i regułę w `RULES.md`. To toy probe, bez pełnego judge.

## 2026-10-25: rytm wejścia w bramce PNN

Punktem wyjścia był otwarty wcześniej przez `shared/lit.py fetch` Grubb i Burrone (2010; PMC3196626): bursty zmieniły położenie AIS, podczas gdy regularna stymulacja o dopasowanej częstości nie. Zapytałem w probe, czy bramka zależna od lokalnej nowości także rozróżni bursty i rytm regularny o tej samej liczbie zdarzeń. `biology/pnn_temporal_probe.py` porównuje w 100 seedach A→B→A; każda 600-tickowa faza ma 60 prezentacji (10 kolejnych co 100 ticków albo pojedyncze co 10 ticków), a warianty ablują wejściową nowość, zastępują ją scalar rate albo stale otwierają bramkę.

Przy bramce sensorycznej bursty minus regularne dały zmianę błędu B `+0,055569` (sparowane 95% CI `+0,045232–+0,065906`), recall A `-0,033456` (`-0,042596–-0,024316`), bramki B `-0,110132` i normy aktualizacji `-0,273655` (od `2,625859` do `2,352204`). Rate-only i always-open były identyczne przy obu harmonogramach; bez nowości bramka niemal się zamknęła, z błędem B `0,846496/0,849377`. Interpretacja: sparse burst sequence kosztowała uczenie nowego wzorca, ale ograniczała nadpisywanie starego w tej konkretnej dynamice PNN; to nie jest przewaga ogólna, bo always-open lepiej dopasował B. Koszt aktualizacji to suma norm delta-w, nie energia biologiczna. Wyniki i ograniczenia dopisałem do §8 `PRINCIPLES.md` i `RULES.md`; brak pełnego judge, więc bez konkluzji o organizmie.

## 2026-10-25: odporność PNN burstów na szum sensoryczny

Ponownie otworzyłem przez `.venv/bin/python shared/lit.py fetch` Grubb & Burrone (2010; PMCID PMC3196626), o relokacji AIS zależnej od wzorca aktywności. Dodałem parametr `input_noise` i uruchomiłem 100 wspólnych seedów dla szumu `0,05/0,15/0,30`, porównując sensoryczną bramkę z ablacją nowości i wariantem always-open. Zmiana błędu przypomnienia A (burst minus regular) wyniosła `-0,072382/-0,033456/+0,008962`; przy `0,30` 95% CI było `+0,007289..+0,010635`, więc retencyjna korzyść burstów zmieniła znak. Zmiana błędu B wyniosła `+0,088125/+0,055569/+0,016015`; wyższy szum ograniczał różnicę w nowym uczeniu. Ablacja potwierdza, że efekt harmonogramu w always-open nie występuje, lecz ablacją sensoryczną nadal wykazuje mały efekt przypomnienia. To probe syntetyczne, a norma aktualizacji nie jest kosztem energetycznym. Artefakty: `biology/pnn_noise_robustness_probe.py` i `.result.txt`; nie jest to pełny judge.
## 2026-10-25: adaptacja pobudliwości przy zmianie skali wejścia

Przeczytałem przez `.venv/bin/python shared/lit.py fetch https://www.nature.com/articles/nn0699_515` Desai, Rutherford i Turrigiano (1999): w hodowanych neuronach piramidalnych dwudniowa blokada aktywności zwiększała wrażliwość na wstrzyknięty prąd i obniżała próg, przez regulację wybranych przewodnictw. Przełożyłem ideę na `intrinsic_gain_probe.py`: neuron aktualizuje lokalny próg z EMA własnej aktywności; kontrolami są próg stały i próg wspólny. Na 100 seedach, przy natężeniu `0,45 -> 1,0 -> 0,45`, aktywność końcowa wyniosła `0,497444` dla fixed, `0,263631` dla global i `0,251331` dla local (cel `0,25`). Trafność była `1,0` we wszystkich fazach, więc nie ma dowodu na poprawę kodu. Ponadto lokalny i globalny próg używały tego samego celu; nie testowałem indywidualnej kalibracji. Raport: `intrinsic_gain_probe.result.txt`. Następny krok: wzorce o kontrolowanej bliskości, lokalny cel estymowany przed perturbacją i osobne miary zakresu odpowiedzi; żadnych wniosków o organizmie bez pełnego judge.

## 2026-10-25: dopełniaczowy tag przed przerzedzaniem

Otworzyłem przez `.venv/bin/python shared/lit.py fetch` Schafer et al. 2012, PMCID PMC3528177. W P5 elementy presynaptyczne były w `35%` mikroglejów, `63%` miało inne inkluzje, `10%` nie miało materiału; CR3/C3 KO zmniejszały pochłanianie (`p<0,04`, `p<0,01`, odpowiednio `n=3/4`), a CR3 KO zwiększał nakładanie projekcji w P10/P30.

Dodałem `complement_pruning_probe.py`: 200 wspólnych seedów, 160 krawędzi, 120 kroków, pięć zdarzeń po 10%, warianty wolnego tagu, bieżącego minimum, losowania i bez przerzedzania. Przy szumie 0,35 wolny tag dał overlap/funkcję/retencję `0,156263/0,903914/1,315912`, minimum `0,239737/0,870073/1,238596`; sparowana delta retencji `+0,077316`, CI95 `0,046119..0,110079`, ale CI funkcji i overlapu obejmowały zero. To toy odporności selektora struktury, nie wynik organizmu. Dodałem §44 do PRINCIPLES i regułę o równym budżecie oraz trzech metrykach.
