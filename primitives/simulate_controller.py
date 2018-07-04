# Primitive Controller
# Authors: Bastian Schürmann, Tùng M. Phan
# California Institute of Technology
# July 4, 2018

import scipy.io
import numpy as np
mat = scipy.io.loadmat('MA3.mat')

prim_num = 0 # primitive number
prim = mat['MA3'][prim_num,0] # the primitive corresponding to the primitive number

if not prim['controller_found'][0,0][0,0]:
    print('Maneuver does not exist yet. Please choose different maneuver_number.')

N = 5 # number of segments for the reference trajectory
G_u = np.array([[175], [1.29]]) # size of input set
nu = 2 # number of inputs
nx = 4 # number of states

x = np.zeros([4*nx, N+1])
x_temp0 = np.array(prim['x0'][0,0]) + np.matmul(np.diag([4, 0.02, 4, 4]), 2*np.random.rand(nx,1)-np.ones((nx,1))) # random state in initial set

x1 = x_temp0
x2 = prim['x0'][0,0]
x3 = x_temp0 - prim['x0'][0,0]
x4 = np.matmul(np.linalg.inv(np.diag([4, 0.02, 4, 4])), (x_temp0-prim['x0'][0,0]))
x[:,0] = (np.vstack((x1,x2,x3,x4)))[:,0]
for k in range(0,N):
    dist= np.array([[8*(2*np.random.rand())], [0.065*(2*np.random.rand()-1)]]) # % random constant disturbance for this time step, disturbance can vary freely. Constant implementation only for easier simulation.
    print(dist)
    print('\n')


# q=[reshape(MA{maneuver_number}.K{k},[],1);0.5*(MA{maneuver_number}.x_ref(:,k+1)+MA{maneuver_number}.x_ref(:,k));MA{maneuver_number}.u_ref(:,k);MA{maneuver_number}.u_ref(:,k);reshape(G_u*MA{maneuver_number}.alpha((k-1)*nu+1:k*nu,:),[],1)]; % parameters for the controller

