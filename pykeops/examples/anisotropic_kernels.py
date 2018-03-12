import os.path
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + (os.path.sep + '..')*2)

# Standard imports
import numpy as np
from matplotlib import pyplot as plt
import matplotlib.cm as cm
import torch
from torch          import Tensor
from torch.autograd import Variable, grad
from pykeops.torch.kernels import Kernel, kernel_product

plt.ion()

# Choose the storage place for our data : CPU (host) or GPU (device) memory.
use_cuda = torch.cuda.is_available()
dtype    = torch.cuda.FloatTensor if use_cuda else torch.FloatTensor


# Define our dataset =====================================================================
# Three points in the plane R^2
y = Variable(torch.Tensor( [
    [ .2, .7],
    [ .5, .3],
    [ .7, .5]
    ])).type(dtype)
# Three scalar weights
b = Variable(torch.Tensor([
    1., 1., .5
])).type(dtype)
b = b.view(-1,1) # Remember : b is not a vector, but a "list of unidimensional vectors"!

# DISPLAY ================================================================================
# Create a uniform grid on the unit square:
res = 100
ticks  = np.linspace( 0, 1, res+1)[:-1] + .5 / res 
X,Y    = np.meshgrid( ticks, ticks )

x = Variable(torch.from_numpy(np.vstack( (X.ravel(), Y.ravel()) ).T).contiguous().type(dtype) )

def showcase_params( params , title, ind) :
    """Samples "x -> ∑_j b_j * k_j(x - y_j)" on the grid, and displays it as a heatmap."""
    heatmap   = kernel_product(x, y, b, params)
    heatmap   = heatmap.view(res,res).data.cpu().numpy() # reshape as a "background" image

    plt.subplot(2,3,ind)
    plt.imshow(  -heatmap, interpolation='bilinear', origin='lower', 
                vmin = -1, vmax = 1, cmap=cm.RdBu, 
                extent=(0,1,0,1)) 
    plt.title(title, fontsize=20)

plt.figure(figsize=(30,20))

# TEST ===================================================================================
# Let's use a "gaussian" kernel, i.e.
#        k(x_i,y_j) = exp( - WeightedSquareNorm(gamma, x_i-y_j ) )
params = {
    "id"      : Kernel("gaussian(x,y)"),
}

# The type of kernel is inferred from the shape of the parameter "gamma",
# used as a "metric multiplier".
# Denoting D == x.shape[1] == y.shape[1] the size of the feature space, rules are : 
#   - if "gamma" is a vector    (gamma.shape = [K]),   it is seen as a fixed parameter
#   - if "gamma" is a 2d-tensor (gamma.shape = [M,K]), it is seen as a "j"-variable "gamma_j"
#
#   - if K == 1 , gamma is a scalar factor in front of a simple euclidean squared norm :
#                 WeightedSquareNorm( g, x-y ) = g * |x-y|^2

#   - if K == D , gamma is a diagonal matrix:
#                 WeightedSquareNorm( g, x-y ) = < x-y, diag(g) * (x-y) >
#                                              = \sum_d  ( g[d] * ((x-y)[d])**2 )
#   - if K == D*D, gamma is a (symmetric) matrix:
#                 WeightedSquareNorm( g, x-y ) = < x-y, g * (x-y) >
#                                              = \sum_{k,l}  ( g[k,l] * (x-y)[k]*(x-y)[l] )
#
# N.B.: Beware of Shape([D]) != Shape([1,D]) confusions !

# Isotropic, uniform kernel -----------------------------------------------------------
sigma = Variable(torch.Tensor( [0.1] )).type(dtype)
params["gamma"] = 1./sigma**2
showcase_params(params, "Isotropic Uniform kernel", 1)

# Isotropic, Variable kernel ----------------------------------------------------------
sigma = Variable(torch.Tensor( [ 
    [0.15], 
    [0.07], 
    [0.3] 
] )).type(dtype)
params["gamma"] = 1./sigma**2
showcase_params(params, "Isotropic Variable kernel", 4)

# Anisotropic, Uniform kernel ---------------------------------------------------------
sigma = Variable(torch.Tensor( [0.2, 0.1] )).type(dtype)
params["gamma"] = 1./sigma**2
showcase_params(params, "Anisotropic Uniform kernel", 2)

# Anisotropic, Variable kernel --------------------------------------------------------
sigma = Variable(torch.Tensor( [ 
    [0.2, 0.1], 
    [.05, .15], 
    [.2,  .2] 
    ] )).type(dtype)
params["gamma"] = 1./sigma**2
showcase_params(params, "Anisotropic Variable kernel", 5)

# Fully-Anisotropic, Uniform kernel ---------------------------------------------------
Sigma = Variable(torch.Tensor( [1/0.2**2, 1/.25**2, 1/.25**2, 1/0.1**2 ] )).type(dtype)
params["gamma"]   = Sigma
params["backend"] = "pytorch"
showcase_params(params, "Fully-Anisotropic Uniform kernel", 3)

# Fully-Anisotropic, Variable kernel --------------------------------------------------
Sigma = Variable(torch.Tensor( [ 
    [1/0.2**2, 1/.25**2, 1/.25**2, 1/0.1**2  ] ,
    [1/0.1**2,     0,       0,     1/0.12**2 ] ,
    [1/0.3**2,-1/.25**2,-1/.25**2, 1/0.12**2 ] ,
    ] )).type(dtype)
params["gamma"] = Sigma
showcase_params(params, "Fully-Anisotropic Variable kernel", 6)


plt.show(block=True)