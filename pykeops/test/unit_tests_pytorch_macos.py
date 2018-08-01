import os.path
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + (os.path.sep + '..')*2)

import unittest
import itertools
import numpy as np

from pykeops.numpy.utils import np_kernel, log_np_kernel, grad_np_kernel, differences

from pykeops import torch_found, gpu_available

@unittest.skipIf(not torch_found,"Pytorch was not found on your system. Skip tests.")
class PytorchUnitTestCase(unittest.TestCase):

    N    = int(6)
    M    = int(10)
    D = int(3)
    E  = int(3)

    a = np.random.rand(N,E).astype('float32')
    x = np.random.rand(N,D).astype('float32')
    y = np.random.rand(M,D).astype('float32')
    f = np.random.rand(M,1).astype('float32')
    b = np.random.rand(M,E).astype('float32')
    p = np.random.rand(2).astype('float32')
    sigma = np.array([0.4]).astype('float32')

    try:
        import torch
        from torch.autograd import Variable

        use_cuda = 0*torch.cuda.is_available()
        dtype    = torch.cuda.FloatTensor if use_cuda else torch.FloatTensor

        ac = Variable(torch.from_numpy(a.copy()).type(dtype), requires_grad=True).type(dtype)
        xc = Variable(torch.from_numpy(x.copy()).type(dtype), requires_grad=True).type(dtype)
        yc = Variable(torch.from_numpy(y.copy()).type(dtype), requires_grad=True).type(dtype)
        fc = Variable(torch.from_numpy(f.copy()).type(dtype), requires_grad=True).type(dtype)
        bc = Variable(torch.from_numpy(b.copy()).type(dtype), requires_grad=True).type(dtype)
        pc = Variable(torch.from_numpy(p.copy()).type(dtype), requires_grad=True).type(dtype)
        sigmac = torch.autograd.Variable(torch.from_numpy(sigma.copy()).type(dtype), requires_grad=False).type(dtype)
        print("Running Pytorch tests.")
    except:
        print("Pytorch could not be loaded.")
        pass


#--------------------------------------------------------------------------------------
    def test_generic_syntax(self):
#--------------------------------------------------------------------------------------
        from pykeops.torch.generic_red import generic_sum, generic_logsumexp
        aliases = ["p=Pm(0,1)","a=Vy(1,1)","x=Vx(2,3)","y=Vy(3,3)"]
        formula = "Square(p-a)*Exp(x+y)"
        signature   =   [ (3, 0), (1, 2), (1, 1), (3, 0), (3, 1) ]
        axis = 1       

        if gpu_available:
            backend_to_test = ['auto','GPU_1D','GPU_2D','GPU']
        else:
            backend_to_test = ['auto']

        for b in backend_to_test:
            with self.subTest(b=b):
                
                # Call cuda kernel
                my_routine = generic_sum(formula=formula,aliases=aliases,axis=axis,backend=b)
                gamma_keops = my_routine(self.sigmac,self.fc,self.xc,self.yc)
                # Numpy version
                gamma_py = np.sum((self.sigma - self.f)**2 *np.exp( (self.y.T[:,:,np.newaxis] + self.x.T[:,np.newaxis,:])),axis=1).T

                # compare output
                self.assertTrue( np.allclose(gamma_keops.cpu().data.numpy(), gamma_py , atol=1e-6))


#--------------------------------------------------------------------------------------
    def test_generic_syntax_simple(self):
#--------------------------------------------------------------------------------------
        from pykeops.torch.generic_red import generic_sum

#        aliases = [ "A = Vx(" + str(self.xc.shape[1]) + ") ",  # output,       indexed by i, dim D.
#                    "P = Pm(2)",                               # 1st argument,  a parameter, dim 2. 
#                    "X = Vx(" + str(self.xc.shape[1]) + ") ",  # 2nd argument, indexed by i, dim D.
#                    "Y = Vy(" + str(self.yc.shape[1]) + ") "]  # 3rd argument, indexed by j, dim D.
        aliases = [ "P = Pm(0,2)",                               # 1st argument,  a parameter, dim 2. 
                    "X = Vx(1," + str(self.xc.shape[1]) + ") ",  # 2nd argument, indexed by i, dim D.
                    "Y = Vy(2," + str(self.yc.shape[1]) + ") "]  # 3rd argument, indexed by j, dim D.
        # The actual formula:
        # a_i   =   (<x_i,y_j>**2) * (       p[0]*x_i  +       p[1]*y_j )
        formula = "Pow( (X|Y) , 2) * ( (Elem(P,0) * X) + (Elem(P,1) * Y) )"

        if gpu_available:
            backend_to_test = ['auto','GPU_1D','GPU_2D','GPU']
        else:
            backend_to_test = ['auto']

        for b in backend_to_test:
            with self.subTest(b=b):

                my_routine = generic_sum(formula, aliases, backend=b)
                gamma_keops = my_routine(self.pc, self.xc, self.yc)
        
                # Numpy version
                scals = (self.x @ self.y.T)**2 # Memory-intensive computation!
                gamma_py = self.p[0] * scals.sum(1).reshape(-1,1) * self.x \
                         + self.p[1] * (scals @ self.y)

                # compare output
                self.assertTrue( np.allclose(gamma_keops.cpu().data.numpy(), gamma_py , atol=1e-6))


if __name__ == '__main__':
    """
    run tests
    """
    unittest.main()

