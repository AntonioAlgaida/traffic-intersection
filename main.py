# Simulation Plaform for Street Intersection Controller
# Tung M. Phan
# California Institute of Technology
# May 2, 2018

import os
import car, traffic_signals
import prepare.waypoint_graph as waypoint_graph
import matplotlib.animation as animation
import matplotlib.pyplot as plt
from time import time
from numpy import cos, sin, tan
import numpy as np
from PIL import Image
import random

dir_path = os.path.dirname(os.path.realpath(__file__))
intersection_fig = dir_path + "/imglib/intersection_states/intersection_"
blue_car_fig = dir_path + "/imglib/blue_car.png"
gray_car_fig = dir_path + "/imglib/gray_car.png"
car_scale_factor = 0.12

def find_corner_coordinates(x_rel_i, y_rel_i, x_des, y_des, theta, square_fig):
    """
    This function takes an image and an angle then computes
    the coordinates of the corner (observe that vertical axis here is flipped)
    """
    w, h = square_fig.size
    theta = -theta
    if w != h:
        raise Exception("Figure has to be square!")
    x_corner_rel, y_corner_rel = -w/2, -h/2
    R = np.array([[cos(theta), sin(theta)], [-sin(theta), cos(theta)]])
    x_rel_f, y_rel_f = R.dot(np.array([[x_rel_i], [y_rel_i]]))
    # xy_unknown - xy_corner + xy_rel_f = xy_des
    return int(x_des - x_rel_f + x_corner_rel), int(y_des - y_rel_f + y_corner_rel)

def draw_car(vehicle):
    vee, theta, x, y = vehicle.state
    # convert angle to degrees and positive counter-clockwise
    theta_d = -theta/np.pi * 180
    if vehicle.color  == 'blue':
        vehicle_fig = Image.open(blue_car_fig)
    elif vehicle.color  == 'gray':
        vehicle_fig = Image.open(gray_car_fig)
    # set expand=True so as to disable cropping of output image
    vehicle_fig = vehicle_fig.rotate(theta_d, expand = False)
    scaled_vehicle_fig_size  =  tuple([int(car_scale_factor * i) for i in vehicle_fig.size])
    # rescale car 
    vehicle_fig = vehicle_fig.resize(scaled_vehicle_fig_size, Image.ANTIALIAS)
    # at this scale (-28, 0) is the relative coordinates of the center of the rear axle w.r.t. the
    # center of the figure
    x_corner, y_corner = find_corner_coordinates(-28, 0, x, y, theta, vehicle_fig)
    background.paste(vehicle_fig, (x_corner, y_corner), vehicle_fig)

# creates figure
fig = plt.figure()
# turn on/off axes
plt.axis('on')
# sampling time
dt = 0.1
# Artist Animation option is used to generate offline movies - implemented here as a backup
use_artist_animation = False
if use_artist_animation:
    frames = []
    for i in range(0,100):
        # create new background
        background = Image.open(intersection_fig)
        # test values - should be changed according to needs
        car_1 = car.KinematicCar(init_state=(2,np.pi,300,300), L=50)
        draw_car(car_1)
        car_1.next((10, 0.001),dt)
        frames.append([plt.imshow(background, animated = True)])
    ani = animation.ArtistAnimation(fig, frames, interval = 10, repeat_delay=1)
    plt.show()
else:
    # creates cars
    car_1 = car.KinematicCar(init_state=(100,np.pi,1000,500), L = 60)
    car_2 = car.KinematicCar(init_state=(100,np.pi/2,600,300), color='gray', L=60)
    # create traffic lights
    traffic_lights = traffic_signals.TrafficLights(0.5, 2)
    cars = [car_1, car_2]
    horizontal_light = traffic_lights._state['horizontal'][0]
    vertical_light = traffic_lights._state['vertical'][0]
    background = Image.open(intersection_fig + horizontal_light + '_' + vertical_light + '.png')
    def init():
        stage = plt.imshow(background, origin="lower",zorder=0) # this origin option flips the y-axis
        return stage, # notice the comma is required to make returned object iterable (a requirement of FuncAnimation)

    def animate(i): # update animation by dt
        """ online frame update """
        global background
        # update traffic lights
        traffic_lights.update(dt)
        horizontal_light = traffic_lights._state['horizontal'][0]
        vertical_light = traffic_lights._state['vertical'][0]
        # update background
        # TODO: implement option to lay waypoint graph over background
        background = Image.open(intersection_fig + horizontal_light + '_' + vertical_light + '.png')
        x_lim, y_lim = background.size
        if waypoint_graph == True:
            graph = waypoint_graph.plot_edges(plt, waypoint_graph.G, plt_src_snk=True)
            background.paste(graph, (0, 0), graph)
        # update planner

        # update cars
        ## USES PRIMITIVES
        ## TO BE INPLEMENTED
        for vehicle in cars:
            nu = 0
            acc = 0
            if random.random() > 0.1:
                nu = random.uniform(-0.05,0.05)
            if random.random() > 0.3:
                acc = random.uniform(-5,10)
            vehicle.next((acc, nu),dt)
            if (vehicle.state[2] <= x_lim and vehicle.state[3] <= y_lim):
                draw_car(vehicle)
        stage = plt.imshow(background, origin="lower") # this origin option flips the y-axis
#        dots = plt.axes().plot(300,300,'.')
#        dots = plt.axes().plot(240,300,'.')
#        return stage, dots  # notice the comma is required to make returned object iterable (a requirement of FuncAnimation)
        return stage,   # notice the comma is required to make returned object iterable (a requirement of FuncAnimation)

    ##
    ## OBSERVER GOES HERE 
    ## TAKES IN CONTRACTS, CARS AND TRAFFIC LIGHT,  AS OS
    ##
    t0 = time()
    animate(0)
    t1 = time()
    interval = (t1 - t0)
    show_waypoint_graph = True
    ani = animation.FuncAnimation(fig, animate, frames=300, interval=interval, blit=True, init_func = init)
plt.show()
