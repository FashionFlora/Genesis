#!/usr/bin/env python3
"""Generuje prompty startowe agentów Codexa: agents/prompts/<nazwa>.txt."""
import os

G = "/opt/dlami/nvme/genesis"
OUT = f"{G}/agents/prompts"

HANDOVER = """Przejmujesz tę rolę po poprzednim agencie (inny model, sesja zakończona). Jego dorobek jest w plikach — najpierw go
przeczytaj, potraktuj krytycznie (mógł się mylić: sprawdzaj źródła, nie przepisuj na ślepo), popraw błędy i kontynuuj.
Na starcie: `python3 shared/board.py read {name}` (zobaczysz całą dotychczasową wymianę na tablicy)."""

AREAS = {
    "intrinsic_motivation": "uczenie/eksploracja bez nagrody zewnętrznej: ICM, RND, Plan2Explore, NGU, Agent57 (część eksploracyjna), empowerment, DIAYN, APT, Disagreement, LEXA, E3B, AMIGo, BYOL-Explore, Go-Explore, Episodic Curiosity oraz metody z wynikami na Crafterze bez nagrody (artykuł Crafter arXiv 2109.06780 i prace go cytujące).",
    "no_backprop": "uczenie bez backpropagation: reguły lokalne i hebbowskie (Oja, BCM, STDP), Forward-Forward, predictive coding, equilibrium propagation, feedback alignment / DFA, target propagation, strategie ewolucyjne (OpenAI-ES, CMA-ES, NEAT), neuromodulowane reguły plastyczności, HSIC bottleneck, PEPITA.",
    "continual": "uczenie ciągłe i rozwojowe: EWC, SI, MAS, LwF, GEM/A-GEM, replay i generative replay, PackNet, Progressive Nets, loss of plasticity (continual backprop, shrink-and-perturb), CLEAR, metody zdobywania i transferu umiejętności.",
    "memory_exploration": "pamięć i eksploracja: pamięć epizodyczna (MERLIN, episodic control), count-based i pseudo-counts, nowość stanów, pamięć zewnętrzna/NTM/DNC w RL, hippocampal-inspired replay (Go-Explore i Episodic Curiosity należą do intrinsic_motivation).",
    "algorithm_discovery": "automatyczne odkrywanie algorytmów: AutoML-Zero, Learned Policy Gradient (LPG), DiscoRL / odkryte reguły RL, meta-learned plasticity rules, learned optimizers (VeLO), OPEN, Evolving RL algorithms, LLM-driven discovery (FunSearch, AlphaEvolve, DiscoPOP).",
    "self_organization": "samoorganizacja i rozwój zdolności: neural cellular automata, open-endedness (POET, OMNI, OMNI-EPIC), automatic curriculum (PAIRED, PLR), self-organizing maps, growing networks, IMGEP / MAGELLAN, quality-diversity (MAP-Elites).",
    "world_models": "modele świata i przewidywanie konsekwencji: World Models (Ha&Schmidhuber), PlaNet, DreamerV1-V3, IRIS, DIAMOND, TWM, JEPA / V-JEPA, MuZero, Director, SPR, DreamerV3 na Crafterze.",
    "neuro_learning": "jak uczy się biologiczny mózg (mechanizmy z neuronauki + ich modele obliczeniowe): plastyczność synaptyczna (LTP/LTD, STDP z neuromodulacją, three-factor learning rules, eligibility traces), neuromodulacja jako sygnały uczenia, dendrytyczne obliczenia (Urbanczik-Senn, burst-dependent plasticity), complementary learning systems, konsolidacja i replay w śnie, active inference / free energy principle, predictive processing w korze, Thousand Brains / HTM, grid/place cells i mapy poznawcze (Tolman-Eichenbaum Machine), spiking networks z lokalnym uczeniem, e-prop, ciekawość u zwierząt. Oceniaj pod kątem implementacji w agencie na Crafterze.",
    "neuro_development": "jak mózg się sam BUDUJE i jak to przenieść do sztucznych sieci: neurogeneza, synaptogeneza i synaptic pruning, plastyczność strukturalna, critical periods, activity-dependent development, morfogeneza i reguły wzrostu, neural developmental programs (NDP, Najarro & Risi), HyperNEAT / indirect encodings, genomic bottleneck, sieci rosnące i przycinające się (Cascade-Correlation, DEN, Net2Net, firefly, neurogenesis deep learning), dynamic sparse training (SET, RigL) jako analog synaptogenezy/pruningu, emergencja modułowości. To jest rdzeń GENESIS — szczególnie metody, w których struktura sieci zmienia się ciągle w trakcie uczenia.",
}

AREA_TASK = """Zadanie 01 (tryb A, katalog literatury). Jesteś agentem GENESIS `{name}`, jednym z kilkunastu równoległych; nazwa na tablicy: {name}.
Przeczytaj AGENTS.md i registry/SCHEMA.md i trzymaj się ich ściśle (granice, tablica, narzędzie shared/lit.py, uczciwość danych).

{handover}
Twój dotychczasowy dorobek: registry/areas/{name}.jsonl i reports/task01_{name}.md (mogą nie istnieć).

Twój obszar: `{name}` — {desc}

Cel: co najmniej 15-20 dobrze zweryfikowanych rekordów (uzupełnij starsze o pola self_building i brain_relevance). Metody
należące głównie do innego obszaru przekaż właściwemu agentowi przez tablicę. Każdą metodę najpierw zajmij (claim).
Dla każdej metody: znajdź artykuł (lit.py arxiv/search), przeczytaj (lit.py fetch: abstrakt, a dla reguły uczenia i wyników
pełny tekst HTML/PDF), znajdź kod (lit.py github). Brak pełnego tekstu NIE jest powodem do pominięcia — wtedy rekord z
abstraktu (verified_from: abstract, brakujące pola = null). Nie kończ przed osiągnięciem celu.

Piszesz WYŁĄCZNIE do: registry/areas/{name}.jsonl oraz reports/task01_{name}.md (lista metod, wyniki na Crafterze lub
podobnych środowiskach z tabelami, czego nie zweryfikowano, 3-5 obserwacji dla celu GENESIS, co dostałeś/przekazałeś przez
tablicę). Nie edytuj STATUS.md ani plików innych obszarów."""


def write(name, text):
    os.makedirs(OUT, exist_ok=True)
    open(f"{OUT}/{name}.txt", "w").write(text)


for name, desc in AREAS.items():
    write(name, AREA_TASK.format(name=name, desc=desc, handover=HANDOVER.format(name=name)))

# Engine, krytyk, teoretycy: dotychczasowe zadania + przekazanie + zamiana narzędzi Claude -> lit.py
SPECIAL = {"experiment_engine": "task_engine_prompt.txt", "novelty_auditor": "task_audit_prompt.txt",
           "theorist_axioms": "task_theorist_axioms_prompt.txt", "theorist_life": "task_theorist_life_prompt.txt"}
OWN = {"experiment_engine": "engine/, experiments/, reports/task_E1.md",
       "novelty_auditor": "audit/, reports/task_N1.md",
       "theorist_axioms": "theory/theorist_axioms/", "theorist_life": "theory/theorist_life/"}
for name, f in SPECIAL.items():
    t = open(f"{G}/logs/{f}").read()
    t = (t.replace("CLAUDE.md", "AGENTS.md")
          .replace("(WebSearch, arXiv, Semantic Scholar, OpenReview, GitHub)", "(.venv/bin/python shared/lit.py search|arxiv|fetch|github)")
          .replace("supervisor będzie Cię wznawiał", "nadzorca będzie Cię wznawiał"))
    extra = HANDOVER.format(name=name) + f"\nTwój dotychczasowy dorobek: {OWN[name]}."
    if name == "novelty_auditor":
        extra += " Pracujesz w pętli ok. 2 h: między odczytami tablicy `sleep 120`."
    if name == "experiment_engine":
        extra += (" Harness ma pozwalać agentowi zmieniać własną architekturę w trakcie przebiegu (rosnące/przycinane sieci)"
                  " — to główny kierunek GENESIS. Masz GPU (sprawdź nvidia-smi przed użyciem).")
    write(name, t.rstrip() + "\n\n" + extra + "\n")
print("\n".join(sorted(os.listdir(OUT))))
