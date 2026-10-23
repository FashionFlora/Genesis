"""Minimal population ecology of predictive processes; deterministic given seed."""
from dataclasses import dataclass
import json
from pathlib import Path
import random
from statistics import mean, median, stdev

@dataclass
class Process:
    niche: int
    prediction: float
    energy: float = 1.0
    age: int = 0
    error: float = 0.0

def run(seed=7, steps=5000, niches=8, capacity=96, plastic=True, mutate=True,
        initial_niches=None, mutation_rate=0.08):
    rng = random.Random(seed)
    # Environment signals are periodic niche-local binary events. No task reward exists.
    if initial_niches is None:
        initial_niches = list(range(niches))
    pop = [Process(initial_niches[i % len(initial_niches)], rng.random()) for i in range(capacity // 2)]
    counts=[]; errors=[]
    for t in range(steps):
        active = [int(((t // (3 + n)) + n) % 2 == 0) for n in range(niches)]
        for p in pop:
            y=active[p.niche]
            e=(p.prediction-y)**2
            p.error=0.97*p.error+0.03*e
            # Local predictive plasticity; no global loss gradient or external reward.
            if plastic:
                p.prediction += 0.08*(y-p.prediction)
            p.energy = max(0.0, 0.92*p.energy + 0.08*(1.0-e))
            p.age += 1
        # Turnover: death by low viability, division by sustained viability.
        pop=[p for p in pop if not (p.energy < 0.28 and rng.random() < 0.35)]
        survivors=[]
        for p in pop:
            survivors.append(p)
            if len(survivors)<capacity and p.energy>0.78 and p.age%17==0:
                # Daughter inherits niche, with rare niche mutation.
                n=(p.niche + (rng.choice((-1,1)) if mutate and rng.random()<mutation_rate else 0))%niches
                survivors.append(Process(n, min(1,max(0,p.prediction+rng.gauss(0,.04)))))
        pop=survivors[:capacity]
        # Resource-limited common energy dilution prevents unbounded immortality.
        if pop:
            load=max(0,len(pop)/capacity-.65)
            for p in pop: p.energy=max(0,p.energy-.025*load)
        if t%100==0:
            counts.append(len(pop)); errors.append(sum(p.error for p in pop)/max(1,len(pop)))
    occupancy=len({p.niche for p in pop})
    return counts, errors, len(pop), occupancy

if __name__=='__main__':
    results={
        "model":"ecological_predictor_v1",
        "seed7_controls":[],
        "incomplete_two_niche":[],
        "single_niche_frontier":{"parameters":{"steps":5000,"niches":8,"capacity":96,"initial_niches":[0],"seeds":list(range(20))},"runs":[],"summary":[]},
    }
    for label, plastic, mutate in (("baseline",True,True),("frozen",False,True),("no_mutation",True,False)):
        c,e,n,o=run(plastic=plastic,mutate=mutate)
        print(f'{label} seed=7 steps=5000 final_population={n} occupied_niches={o}/{8}')
        print(f'population_min={min(c)} max={max(c)} mean_error_last10={sum(e[-10:])/10:.6f}')
        results["seed7_controls"].append({"condition":label,"seed":7,"steps":5000,"final_population":n,"occupied_niches":o,"population_min":min(c),"population_max":max(c),"mean_error_last10":sum(e[-10:])/10})
    for mutate in (True, False):
        vals=[]
        for seed in range(10):
            c,e,n,o=run(seed=seed, mutate=mutate, initial_niches=[0,1])
            vals.append((o,n,sum(e[-10:])/10))
        print(f'incomplete_init mutate={mutate} seeds=0..9 mean_occupied={sum(x[0] for x in vals)/10:.3f} mean_final_population={sum(x[1] for x in vals)/10:.3f} mean_error={sum(x[2] for x in vals)/10:.6f} occupancy_values={[x[0] for x in vals]}')
        results["incomplete_two_niche"].append({"mutate":mutate,"seeds":list(range(10)),"runs":[{"seed":seed,"occupied_niches":o,"final_population":n,"mean_error_last10":err} for seed,(o,n,err) in enumerate(vals)],"mean_occupied_niches":mean(x[0] for x in vals),"mean_final_population":mean(x[1] for x in vals),"mean_error_last10":mean(x[2] for x in vals)})

    # Frontier test: only niche 0 is initially populated. This checks whether
    # local niche mutation spreads viable predictors around the ring.
    for rate in (0.0, 0.08, 0.25):
        vals=[]
        for seed in range(20):
            c,e,n,o=run(seed=seed, mutate=True, mutation_rate=rate, initial_niches=[0])
            row={"seed":seed,"mutation_rate":rate,"final_population":n,"occupied_niches":o,"population_min":min(c),"population_max":max(c),"mean_error_last10":mean(e[-10:])}
            vals.append(row)
            results["single_niche_frontier"]["runs"].append(row)
        occ=[x["occupied_niches"] for x in vals]
        pop=[x["final_population"] for x in vals]
        err=[x["mean_error_last10"] for x in vals]
        summary={"mutation_rate":rate,"n":len(vals),"mean_occupied_niches":mean(occ),"sd_occupied_niches":stdev(occ),"median_occupied_niches":median(occ),"all_niches_fraction":sum(x==8 for x in occ)/len(occ),"mean_final_population":mean(pop),"mean_error_last10":mean(err)}
        results["single_niche_frontier"]["summary"].append(summary)
        print(f'frontier initial=[0] mutation_rate={rate:.2f} seeds=0..19 mean_occupied={summary["mean_occupied_niches"]:.3f} sd_occupied={summary["sd_occupied_niches"]:.3f} all_8_fraction={summary["all_niches_fraction"]:.3f} mean_population={summary["mean_final_population"]:.3f} mean_error={summary["mean_error_last10"]:.6f}')

    output=Path(__file__).with_name("ecology_results.json")
    output.write_text(json.dumps(results,indent=2,sort_keys=True)+"\n")
    print(f"saved_results={output}")
