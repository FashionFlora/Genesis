import importlib.util, json, sys, torch
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parents[1]))
from sandbox.organism_judge import run_life, _summary
from sandbox.worlds.organism import OrganismWorld

CANDS = ['metabolic_gate','metabolic_relaxation']

def load(name, sensors, batch, device, seed):
    path=f'candidates/{name}/principle_organism.py'
    spec=importlib.util.spec_from_file_location(name,path)
    mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    return mod.OrganismBrain(302,sensors,OrganismWorld.N_MOTORS,batch,device,seed)

def one(name, interoception, steps=1200, seed=43):
    device='cpu'
    batch=16; sensors=OrganismWorld.N_SENSORS if interoception else OrganismWorld.N_SENSORS-1
    brain=load(name,sensors,batch,device,seed)
    row=run_life(brain,batch,device,seed,interoception=interoception,steps=steps,n_units=302)
    s=_summary([row],302)
    return {'candidate':name,'interoception':interoception,'steps':steps,
            'rooms':s['rooms_reached']['mean'],'survival':s['survival']['mean'],
            'reversal_latency':s['reversal_latency']['mean'],'mean_energy':s['mean_energy']['mean'],
            'growth':row['growth']}

for name in CANDS:
    for intero in (True,False):
        print('START', name, intero, flush=True)
        out=one(name,intero)
        print(json.dumps(out,sort_keys=True), flush=True)
