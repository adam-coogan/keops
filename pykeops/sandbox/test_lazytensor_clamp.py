# Test for Clamp operation using LazyTensors

import time

import torch
from pykeops.torch import LazyTensor

M, N, D = 1000, 1000, 300

x = torch.randn(M, 1, D, requires_grad=True)
y = torch.randn(1, N, D)
a = -1 # -1.23
b = 1 # 1.42

def fun(x,y,a,b,backend):
    if backend=="keops":
        x = LazyTensor(x)
        y = LazyTensor(y)
        #a = LazyTensor(a)
        #b = LazyTensor(b)
    elif backend!="torch":
        raise ValueError("wrong backend")
    Dxy = ((x*y).clamp(a,b)).sum(dim=2) 
    Kxy = (- Dxy**2).exp() 
    return Kxy.sum(dim=1)
    
backends = ["torch","keops"]
    
out = []
for backend in backends:
    start = time.time()
    out.append(fun(x,y,a,b,backend).squeeze())
    end = time.time()
    print("time for "+backend+":", end-start )

if len(out)>1:
    print("relative error:", (torch.norm(out[0]-out[1])/torch.norm(out[0])).item() )

out_g = []
for k, backend in enumerate(backends):
    start = time.time()
    out_g.append(torch.autograd.grad((out[k] ** 2).sum(), [x])[0])
    end = time.time()
    print("time for "+backend+" (grad):", end-start )

if len(out_g)>1:
    print("relative error grad:", (torch.norm(out_g[0]-out_g[1])/torch.norm(out_g[0])).item() )
