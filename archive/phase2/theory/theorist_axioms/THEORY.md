# Warunkowa stabilność relacji

Każdy uczący się bez końca system musi utrzymać ślady przeszłości, ale ślad nie
może być nieodwołalny: nowe środowisko zmieni wartość dawnych zależności.
Z tego wynika zasada warunkowej stabilności: relacje trwają proporcjonalnie do
trafności przewidywań, a zaskoczenie lokalnie zwalnia ich zasoby na przebudowę.

Pierwszy test używał tablic warunkowych dla każdej pary kanałów i zaniku
modulowanego błędem. Wariant globalny uzyskał 6.9453 na poziomie 1, lokalny
wariant per cel 6.8635 przy baseline 20.9957. Oba przechodzą bramkę uczenia,
lecz wynik całościowy i pamięć powrotu są za słabe. Nie jest to potwierdzenie
zasady; dalszy test powinien sprawdzić, czy selektywna stabilizacja dawnych
relacji może zachować pamięć powrotu bez spowalniania adaptacji.
