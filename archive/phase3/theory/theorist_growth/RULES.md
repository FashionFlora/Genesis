# Reguły z wyników

- Próg nowości 0.18 zatrzymał wzrost przy 1 prototypie i score 0.0156.
- Próg 0.02 uruchomił wzrost zależny od czasu (do 814 jednostek przy puli 1000), ale score spadł do 0.0. Struktura nie wystarcza bez użytecznego sterowania.
- RSS procesu PyTorch maskuje koszt modelu; dalszy pomiar powinien raportować także bajty tensorów modelu.
- Rozszerzenie lokalnego creditu energii na wszystkie trzy kanały akcji dało score 0.003906 (1/256 światów w pokoju 2); ablacja interocepcji dała ten sam score. To nie jest stabilna poprawa przeżycia.
- Przy 1200 krokach wzrost w assayu osiąga 301/814 aktywnych jednostek przy limitach 302/1000+; pamięć tensorów to 4.12/13.96 MB. Limity 10k i 100k nie tworzą większej struktury bez dodatkowej nowości.
## Nowe obserwacje

- Test pruning musi zawierać dostatecznie długi odcinek bez kontekstu. Przy `decay=0.994`
  1400 kroków po wycofaniu jednego z czterech powtarzalnych kontekstów nie zmniejszyło
  liczby aktywnych jednostek (4/4); obecna utility/threshold nie realizuje deklarowanego zaniku.
- Sędziowski score pojedynczego seedu nie dowodzi mechanizmu: `growth_energy_vector`
  uzyskał 0.0156 na każdej skali, ale survival=0 i tylko 2/128 dotarły do drugiego pokoju.
- Relatywna selekcja popytem (`growth_demand_competition`) zmniejszyła pulę aktywną z 4
  do 3 po wycofaniu kontekstu i odtworzyła 4 przy jego powrocie; score organism=0.1641
  wobec 0.0039 bez interocepcji. Nadal survival=0, wynik jest płaski dla 302–100k,
  a tensor state ma 54,528 B, bo zaledwie 4 sloty zostały zaalokowane.
- Assay z 24 kontekstami wymaga wycofania ich wszystkich poza jednym; samo przełączanie
  między pozostałymi 23 nie mierzy zaniku. Po 1,400 krokach na kontekście 0 struktura
  spadła z 16 jednostek/48 połączeń do 1/3, a po powrocie wzorca 23 wzrosła do 2/6.
  Błąd sensoryczny=0.001009; tensor state=218,112 B i 16 zaalokowanych slotów na
  limitach 302–100k. Mierzony zakres efektu jest więc poniżej minimalnego świata,
  a pamięć nie skaluje się z limitem.
- Replika organism na 2 światy/rozmiar potwierdziła score=0.1641 (CI95 0.0796–0.2485),
  rooms_reached; survival=0 dla wszystkich rozmiarów. Poprawa assayu nie przeniosła się
  na przeżycie ani nie zmieniła płaskiej skali.
- Mutacja startująca z 1 slotu (growth_demand_expansion) nie poprawiła wyniku rodzica:
  organism=0.1641 z energią, 0.0039 bez; survival=0 i wyniki identyczne dla 302–100k.
  Assay na 24 syntetycznych kontekstach wykazał 1->16 jednostek/3->48 połączeń,
  pruning 16->1 i reaktywację do 2/6; błąd=0.001009, tensory=218,112 B na każdej skali.
  Limit testu jest różnorodnością bodźców: 24 wzorce nigdy nie żądają >16 jednostek.
