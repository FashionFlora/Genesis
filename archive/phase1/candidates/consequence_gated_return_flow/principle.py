"""Returned consequence gates the persistence of a relation."""
PARAMS = {"timescale": 16.0}
class System:
 def __init__(self): self.width=False; self.previous=None; self.cells=None; self.prediction=None; self.edges=False
 def step(self,obs):
  o=True; t=o+o; h=o/t
  if self.cells is None:
   self.width=len(obs); z=h-h; self.cells=[[[z,z,z] for _ in range(self.width)] for _ in range(self.width)]; self.prediction=[h]*self.width
  if self.previous is not None:
   s=PARAMS["timescale"]
   for i,b in enumerate(self.previous):
    x=t*b-o
    for j,a in enumerate(obs):
     c=self.cells[i][j]; q=t/(o+(h+h*c[o]*x-a)**t)-o; c[o]=(s*c[o]+x*(t*a-o))/(s+o); c[o+o]+=q
  p=[h]*self.width; self.edges=h-h
  for j in range(self.width):
   i=max(range(self.width),key=lambda k:self.cells[k][j][o+o]*abs(self.cells[k][j][o])); v=self.cells[i][j][o]; p[j]+=h*v*(t*obs[i]-o)
   self.edges+=(j>=self.width//t)*max(abs(self.cells[k][j][o]) for k in range(self.width//t))
  self.previous=list(obs); self.prediction=p; return [min(o,max(h-h,v)) for v in p]
 def structure(self): return {"units":self.width,"connections":self.edges,"memory_bytes":self.width*self.width*(True<<True<<True)}
