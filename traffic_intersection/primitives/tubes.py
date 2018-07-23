#!/usr/local/bin/python
# -*- coding: utf-8 -*-
# Tube Computation for Primitives
# Author: Tùng M. Phan
# California Institute of Technology
# July 20, 2018

import os, sys
sys.path.append("..")
import numpy as np
import prepare.collision_check as collision
import assumes.params as params
import scipy.io
# set dir_path to current directory
dir_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
car_scale_factor = params.car_scale_factor
pedestrian_scale_factor = params.pedestrian_scale_factor

# load primitive data
primitive_data_path = dir_path + '/primitives/MA3.mat'
mat = scipy.io.loadmat(primitive_data_path)
num_of_prims = mat['MA3'][:,0].shape[0]

def get_prim_data(prim_id, data_field):
    '''
    This function simplifies the process of extracting data from the .mat file
    Input:
    prim_id: the index of the primitive the data of which we would like to return
    data_field: name of the data field (e.g., x0, x_f, controller_found etc.)

    Output: the requested data
    '''
    return mat['MA3'][prim_id,0][data_field][0,0][:,0]

def vertices_rect(center1, center2, theta, size_x, size_y):
    x, y = (center1 + center2) / 2.
    w = (float(np.linalg.norm(center1-center2)) + size_x) / 2.
    h = size_y / 2.
    unrotated_rects = [(x - w, y - h), (x - w, y + h), (x + w, y + h), (x + w, y - h)]
    vertices = [collision.rotate_vertex(x, y, theta, vertex) for vertex in unrotated_rects]
    return vertices

def make_tube(prim_id):
    x_ref = mat['MA3'][prim_id,0]['x_ref'][0,0]
    size_x = get_prim_data(prim_id, 'size_tube_x')
    size_y = get_prim_data(prim_id, 'size_tube_y')
    segments = [(x_ref[:,idx], x_ref[:,(idx+1)]) for idx in range(x_ref.shape[1]-1)]
    rects = [vertices_rect(center1 = segment[0][2:4], center2 = segment[1][2:4], theta = np.arctan2(segment[1][3]-segment[0][3], segment[1][2]-segment[0][2]), size_x = size_x, size_y = size_y) for segment in segments]
    return rects

def nonoverlapping_tubes(prim1_id, prim2_id):
    rects_1 = make_tube(prim1_id)
    rects_2 = make_tube(prim2_id)
    nonoverlapping = True
    for i in range(len(rects_1)):
        for j in range(i,len(rects_2)):
            nonoverlapping = nonoverlapping and collision.nonoverlapping_polygons(rects_1[i], rects_2[j])
            if nonoverlapping == False:
                return nonoverlapping
    return nonoverlapping

def compute_collision_dictionary(primitive_id_set):
    colsn_dict = {prim_id: set() for prim_id in primitive_id_set}
    for i in range(len(primitive_id_set)):
        for j in range(i, len(primitive_id_set)):
            if not nonoverlapping_tubes(primitive_id_set[i], primitive_id_set[j]): # if they don't collide
                colsn_dict[primitive_id_set[i]].add(primitive_id_set[j])
                colsn_dict[primitive_id_set[j]].add(primitive_id_set[i])
    return colsn_dict

# computes collision_dictionary
prim_id_set = [idx for idx in range(num_of_prims) if get_prim_data(idx, 'controller_found') ]
collision_dictionary = compute_collision_dictionary(prim_id_set)
#########################################################################################
#                                                                                       #
#                                   TESTING                                             #
#                                                                                       #
#########################################################################################
#### TEST2 ######
#prim_id = 0
#rects = make_rects(0)
#print(rects)
#x_ref = mat['MA3'][prim_id,0]['x_ref'][0,0]
#import matplotlib.pyplot as plt
#x = x_ref[2,:]
#y = x_ref[3,:]
#plt.plot(x,y)
#for idx in range(len(rects)):
#    xs = np.array(rects[idx])[:,0]
#    ys = np.array(rects[idx])[:,1]
#    xs = np.concatenate((xs, np.array([xs[0]]))) # to plot the remaining side
#    ys = np.concatenate((ys, np.array([ys[0]]))) # to plot the remaining side
#    plt.plot(xs,ys)
#plt.axis('equal')
#plt.savefig('tube_new.png')
#plt.show()
