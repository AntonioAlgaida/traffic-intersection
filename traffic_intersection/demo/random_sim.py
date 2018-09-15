#!/usr/local/bin/python
# Visualization
# Tung M. Phan
# California Institute of Technology
# July 17, 2018

import sys
sys.path.append('..')
import os, time, platform, warnings, matplotlib, random
import components.planner as planner
import components.car as car
import components.auxiliary.honk_wavefront as wavefront
import components.pedestrian as pedestrian
import components.traffic_signals as traffic_signals
import components.intersection as intersection
import prepare.car_waypoint_graph as car_graph
import prepare.pedestrian_waypoint_graph as pedestrian_graph
import prepare.queue as queue
from PIL import Image, ImageDraw
from components.auxiliary.pedestrian_names import names
import prepare.options as options
from  prepare.collision_check import collision_free, get_bounding_box
from  prepare.helper import *
import numpy as np
import variables.global_vars as global_vars
import assumes.params as params

if platform.system() == 'Darwin': # if the operating system is MacOS
    matplotlib.use('macosx')
else: # if the operating system is Linux or Windows
    try:
        import PySide2 # if pyside2 is installed
        matplotlib.use('Qt5Agg')
    except ImportError:
        warnings.warn('Using the TkAgg backend, this may affect performance. Consider installing pyside2 for Qt5Agg backend')
        matplotlib.use('TkAgg') # this may be slower
import matplotlib.animation as animation
import matplotlib.pyplot as plt

# set dir_path to current directory
dir_path = os.path.dirname(os.path.dirname(os.path.realpath('__file__')))
intersection_fig = dir_path + "/components/imglib/intersection_states/intersection_lights.png"

# set random seed (for debugging)
# random.seed(2)
# np.random.seed(400)

# disable antialiasing for better performance
medic_signs = []
medic_sign = dir_path + '/components/imglib/medic.png'
medic_fig = Image.open(medic_sign).convert("RGBA")
medic_fig = medic_fig.resize((25,25))
def draw_medic_signs(medic_signs_coordinates):
    for coordinate in medic_signs_coordinates:
        x, y = find_corner_coordinates(0, 0, coordinate[0], coordinate[1], 0, medic_fig)
        background.paste(medic_fig, (int(x), int(y)), medic_fig)

walk_sign_go = dir_path + '/components/imglib/go.png'
go_fig = Image.open(walk_sign_go).convert("RGBA")
go_fig = go_fig.resize((18,18))

walk_sign_stop = dir_path + '/components/imglib/stop.png'
stop_fig = Image.open(walk_sign_stop).convert("RGBA")
stop_fig = stop_fig.resize((18,18))

vertical_go_fig = go_fig.rotate(-180, expand = False)
vertical_stop_fig = stop_fig.rotate(-180, expand = False)
horizontal_go_fig = go_fig.rotate(-90, expand = True)
horizontal_stop_fig = stop_fig.rotate(-90, expand = True)

vertical_walk_fig = {True: vertical_go_fig, False: vertical_stop_fig}
horizontal_walk_fig = {True: horizontal_go_fig, False: horizontal_stop_fig}
walk_sign_figs = {'vertical': vertical_walk_fig, 'horizontal': horizontal_walk_fig}
walk_sign_coordinates = {'vertical': [(378, 621), (683, 90)], 'horizontal': [(272, 193), (736, 565)]}

def draw_walk_signs(vertical_fig, horizontal_fig):
    for coordinate in walk_sign_coordinates['vertical']:
        x, y = find_corner_coordinates(0, 0, coordinate[0], coordinate[1], 0, vertical_fig)
        background.paste(vertical_fig, (int(x), int(y)), vertical_fig)
    for coordinate in walk_sign_coordinates['horizontal']:
        x, y = find_corner_coordinates(0, 0, coordinate[0], coordinate[1], 0, horizontal_fig)
        background.paste(horizontal_fig, (int(x), int(y)), horizontal_fig)

vertical_light_coordinates = {'green':[(377, 642), (682,110)], 'yellow': [(377, 659), (682,126)], 'red': [(378, 675), (682.5, 144.5)]}
horizontal_light_coordinates = {'green':[(291, 193), (756, 566.25)], 'yellow': [(309, 193), (773, 566.25)], 'red': [(327, 193), (790, 566.25)]}

# creates figure
fig = plt.figure()
ax = fig.add_axes([0,0,1,1]) # get rid of white border

# turn on/off axes
show_axes = False
if not show_axes:
    plt.axis('off')
# sampling time
dt = options.dt
# create car
def spawn_car():
    plate_number = generate_license_plate()
    rand_num = np.random.choice(10)
    start_node = random.sample(car_graph.G._sources, 1)[0]
    end_node = random.sample(car_graph.G._sinks, 1)[0]
    color = np.random.choice(tuple(car.car_colors))
    the_car = car.KinematicCar(init_state=start_node, color=color, plate_number=plate_number)
    return start_node, end_node, the_car

def spawn_pedestrian():
    name = random.choice(names)
    age = random.randint(18,70)
    start_node = random.sample(pedestrian_graph.G._sources, 1)[0]
    end_node = random.sample(pedestrian_graph.G._sinks, 1)[0]
    init_state = start_node + (0,0)
    if age > 50:
        pedestrian_type = '2'
    else:
        pedestrian_type = random.choice(['1','2','3','4','5','6'])
    the_pedestrian = pedestrian.Pedestrian(init_state=init_state, pedestrian_type=pedestrian_type, name=name, age=age)
    return name, start_node, end_node, the_pedestrian


#if true, pedestrians can cross street and cars cannot cross
def safe_to_walk(green_duration, light_color, light_time):
    walk_sign_delay = green_duration / 10
    return(light_color == 'green' and (light_time + walk_sign_delay) <= (green_duration / 3 + walk_sign_delay))

# create traffic lights
traffic_lights = traffic_signals.TrafficLights(yellow_max = 10, green_max = 50, random_start = True)
horizontal_light = traffic_lights.get_states('horizontal', 'color')
vertical_light = traffic_lights.get_states('vertical', 'color')
background = Image.open(intersection_fig)

pedestrians = []

honk_x = []
honk_y = []
honk_t = []
all_wavefronts = set()

# checks if pedestrian is crossing street
def is_between(lane, person_xy):
    return distance(lane[0], person_xy) + distance(lane[1], person_xy) == distance(lane[0], lane[1])

# cross the street if light is green, or if the pedestrian just crossed the street, continue walking and ignore traffic light color
def continue_walking(person, walk_sign, lane1, lane2, direction, remaining_time):
    person_xy = (person.state[0], person.state[1])
    theta = person.state[2]
    if person_xy in (lane1 + lane2) and walk_sign:
        prim_data, prim_progress = person.prim_queue.get_element_at_index(-2)
        start, finish, vee = prim_data
        dx = finish[0] - start[0]
        dy = finish[1] - start[1]
        remaining_distance = np.linalg.norm(np.array([dx, dy]))
        vee_max = 50
        if (remaining_distance / vee) > remaining_time:
            vee = remaining_distance / remaining_time
        return (vee <= vee_max)
    elif (person_xy == lane1[0] or person_xy == lane2[0]) and theta == direction[0]:
        return True
    elif (person_xy == lane1[1] or person_xy == lane2[1]) and theta == direction[1]:
        return True
    else:
        return False

# if the pedestrian isn't going fast enough, increase speed to cross street before light turns red
def walk_faster(person, remaining_time):
    person_xy = (person.state[0], person.state[1])
    prim_data, prim_progress = person.prim_queue.top()
    start, finish, vee = prim_data
    dx = finish[0] - person.state[0]
    dy = finish[1] - person.state[1]
    remaining_distance = np.linalg.norm(np.array([dx, dy]))
    vee_max = 50
    if (remaining_distance / vee) > remaining_time:
        vee = remaining_distance / remaining_time
        if (vee <= vee_max):
            person.prim_queue.replace_top(((start, finish, vee), prim_progress))

def animate(frame_idx): # update animation by dt
    ax.cla() # clear Axes before plotting
    deadlocked = False
    global_vars.current_time = frame_idx * dt # compute current time from frame index and dt
    print('{:.2f}'.format(global_vars.current_time)+'/'+str(options.duration)) # print out current time to 2 decimal places

    horizontal_light = traffic_lights.get_states('horizontal', 'color')
    vertical_light = traffic_lights.get_states('vertical', 'color')

    horizontal_light_time = traffic_lights.get_states('horizontal', 'time')
    vertical_light_time = traffic_lights.get_states('vertical', 'time')
    green_duration = traffic_lights._max_time['green']

    # if sign is true then walk, stop if false
    vertical_walk_safe = safe_to_walk(green_duration, vertical_light, vertical_light_time)
    horizontal_walk_safe = safe_to_walk(green_duration, horizontal_light, horizontal_light_time)
    #draw_walk_signs(walk_sign_figs['vertical'][vertical_walk_safe], walk_sign_figs['horizontal'][horizontal_walk_safe])

    """ online frame update """
    global background

    # car request
    if with_probability(options.new_car_probability):
        new_start_node, new_end_node, new_car = spawn_car()
        global_vars.request_queue.enqueue((new_start_node, new_end_node, new_car))
    service_count = 0
    original_request_len = global_vars.request_queue.len()
    while global_vars.request_queue.len() > 0 and not deadlocked: # if there is at least one live request in the queue
        request = global_vars.request_queue.pop() # take the first request
        planner.serve_request(request=request,graph=car_graph.G,traffic_lights=traffic_lights)
        service_count += 1
        if service_count == original_request_len:
            service_count = 0 # reset service count
            if global_vars.request_queue.len() == original_request_len:
                deadlocked = True
            else:
                original_request_len = global_vars.request_queue.len()

    # pedestrian
    if with_probability(options.new_pedestrian_probability):
        while True:
            name, begin_node, final_node, the_pedestrian = spawn_pedestrian()
            if not begin_node == final_node:
                break
        _, shortest_path = planner.dijkstra((begin_node[0], begin_node[1]), final_node, pedestrian_graph.G)
        vee = np.random.uniform(20, 40)
        while len(shortest_path) > 0:
            if len(shortest_path) == 1:
                the_pedestrian.prim_queue.enqueue(((shortest_path[0], shortest_path[0], vee), 0))
                del shortest_path[0]
            else:
                the_pedestrian.prim_queue.enqueue(((shortest_path[0], shortest_path[1], vee), 0))
                del shortest_path[0]
        pedestrians.append(the_pedestrian)

    # update traffic lights
    traffic_lights.update(dt)
    horizontal_light = traffic_lights.get_states('horizontal', 'color')
    vertical_light = traffic_lights.get_states('vertical', 'color')

    # update background
    background.close()
    background = Image.open(intersection_fig)
    x_lim, y_lim = background.size

    if options.highlight_crossings:
        alpha = int(alt_sin(70,150,global_vars.current_time,1)) # transparency 
        green = (34,139,34,alpha)
        red = (200,0,0,alpha)
        vertical_lane_color = green if vertical_walk_safe else red
        horizontal_lane_color = green if horizontal_walk_safe else red

        img1 = Image.open(intersection_fig) # highlighted crossings will be drawn on this image
        draw = ImageDraw.Draw(img1)
        draw.rectangle([(344,209),(366,553)], fill = vertical_lane_color)
        draw.rectangle([(695,209),(718,553)], fill = vertical_lane_color)
        draw.rectangle([(392,580),(670,602)], fill = horizontal_lane_color)
        draw.rectangle([(392,158),(670,180)], fill = horizontal_lane_color)
        img = Image.alpha_composite(background, img1) # image with highlighted walk lanes
        background.paste(img)

    draw_walk_signs(walk_sign_figs['vertical'][vertical_walk_safe], walk_sign_figs['horizontal'][horizontal_walk_safe])

    x = []
    y = []
    for coordinate in vertical_light_coordinates[vertical_light]:
        x.append(coordinate[0])
        y.append(coordinate[1])
    circle1 = plt.Circle((x[0],y[0]), radius=6, alpha=alt_sin(0.3,1,100,global_vars.current_time), color=vertical_light[0])
    circle2 = plt.Circle((x[1],y[1]), radius=6, alpha=alt_sin(0.3,1,100,global_vars.current_time), color=vertical_light[0])
    vertical_lights =[ax.add_artist(circle1), ax.add_artist(circle2)]

    x = []
    y = []
    for coordinate in horizontal_light_coordinates[horizontal_light]:
        x.append(coordinate[0])
        y.append(coordinate[1])

    circle1 = plt.Circle((x[0],y[0]), radius=6, alpha=alt_sin(0.3,1,100,global_vars.current_time), color=horizontal_light[0])
    circle2 = plt.Circle((x[1],y[1]), radius=6, alpha=alt_sin(0.3,1,100,global_vars.current_time), color=horizontal_light[0])
    horizontal_lights = [ax.add_artist(circle1), ax.add_artist(circle2)]

    # update pedestrians
    pedestrians_to_keep = []
    pedestrians_waiting = []

    lane1 = [(355, 195), (355, 565)] # left vertical path, (bottom node, top node)
    lane2 = [(705, 195), (705, 565)] # right vertical path, (bottom node, top node)
    lane3 = [(380, 590), (680, 590)] # top horizontal path (left node, right node)
    lane4 = [(380, 170), (680, 170)] # bottom horizontal path (left node, right node)

    if len(pedestrians) > 0:
        for person in pedestrians:
            if (person.state[0] <= x_lim and person.state[0] >= 0 and person.state[1] >= 0 and person.state[1] <= y_lim):
                person_xy = (person.state[0], person.state[1])
                walk_sign_duration = green_duration / 3.
                remaining_vertical_time = abs(walk_sign_duration - vertical_light_time)
                remaining_horizontal_time = abs(walk_sign_duration  - horizontal_light_time)

                if person_xy not in (lane1 + lane2 + lane3 + lane4): # if pedestrian is not at any of the nodes then continue  
                    person.prim_next(dt)
                    pedestrians_to_keep.append(person)
                elif continue_walking(person, vertical_walk_safe, lane1, lane2, (-pi/2, pi/2), remaining_vertical_time): # if light is green cross the street, or if at a node and facing away from the street i.e. just crossed the street then continue
                    person.prim_next(dt)
                    pedestrians_to_keep.append(person)
                elif continue_walking(person, horizontal_walk_safe, lane3, lane4, (pi, 0), remaining_horizontal_time):
                    person.prim_next(dt)
                    pedestrians_to_keep.append(person)
                else:
                    person.state[3] = 0
                    pedestrians_waiting.append(person)

                # pedestrians walk faster if not going fast enough to finish crossing the street before walk sign is off or 'false'
                if is_between(lane1, person_xy) or is_between(lane2, person_xy):
                    walk_faster(person, remaining_vertical_time)
                elif is_between(lane3, person_xy) or is_between(lane4, person_xy):
                    walk_faster(person, remaining_horizontal_time)

    cars_to_keep = []
    cars_to_remove = set()

    # determine which cars to keep
    for plate_number in global_vars.all_cars.keys():
        car = global_vars.all_cars[plate_number]
        if car.prim_queue.len() > 0:
            # update cars with primitives
            global_vars.all_cars[plate_number].prim_next(dt)
            # add cars to keep list
            cars_to_keep.append(global_vars.all_cars[plate_number])
        else:
            cars_to_remove.add(plate_number)
    # determine which cars to remove
    for plate_number in cars_to_remove:
        del global_vars.all_cars[plate_number]

    clear_stamps()
    if not show_axes:
        plt.axis('off')

    honk_waves = ax.scatter(None,None)
    if options.show_honks:
        honk_xs = []
        honk_ys = []
        radii = []
        intensities = []
        for wave in all_wavefronts:
            wave.next(dt)
            honk_x, honk_y, radius, intensity = wave.get_data()
            if intensity > 0:
                honk_xs.append(honk_x)
                honk_ys.append(honk_y)
                radii.append(radius)
                intensities.append(intensity)
            else:
                all_wavefronts.remove(wave)

        rgba_colors = np.zeros((len(intensities),4))
        # red color
        rgba_colors[:,0] = 1.0
        # intensities
        rgba_colors[:, 3] = intensities
        honk_waves = ax.scatter(honk_xs, honk_ys, s = radii, lw=1, facecolors='none', color=rgba_colors)

    for car in cars_to_keep:
        if with_probability(0.005) and not car.is_honking:
            car.toggle_honk()
            # offset is 600 before scaling
            wave = wavefront.HonkWavefront([car.state[2] + 600*params.car_scale_factor*np.cos(car.state[1]), car.state[3] + 600*params.car_scale_factor*np.sin(car.state[1]), 0, 0], init_energy=100000)
            all_wavefronts.add(wave)
        elif with_probability(0.4) and car.is_honking:
            car.toggle_honk()

    # initialize boxes
    boxes = [ax.plot([], [], 'c')[0] for _ in range(len(cars_to_keep))]

    if options.show_boxes:
        for i in range(len(cars_to_keep)):
            curr_car = cars_to_keep[i]
            vertex_set,_,_,_ = get_bounding_box(curr_car)
            xs = [vertex[0] for vertex in vertex_set]
            ys = [vertex[1] for vertex in vertex_set]
            xs.append(vertex_set[0][0])
            ys.append(vertex_set[0][1])
            if with_probability(1):
               boxes[i].set_data(xs,ys)
            for j in range(i + 1, len(cars_to_keep)):
               if not collision_free(curr_car, cars_to_keep[j]):
                    boxes[j].set_color('r')
                    boxes[i].set_color('r')
    # initialize ids
    ids = [ax.text([], [], '') for _ in range(len(cars_to_keep))]
    if options.show_plates:
        for i in range(len(cars_to_keep)):
            _,_,x,y = cars_to_keep[i].state
            plate_number = cars_to_keep[i].plate_number
            ids[i] = ax.text(x,y,str(plate_number), color='w', horizontalalignment='center', verticalalignment='center', bbox=dict(facecolor='red', alpha=0.5), fontsize=10)

    # initialize prims
    plot_prims = [ax.text([], [], '') for _ in range(len(cars_to_keep))]
    if options.show_prims:
        for i in range(len(cars_to_keep)):
            _,_,x,y = cars_to_keep[i].state
            prim_str = 'None'
            if cars_to_keep[i].prim_queue.len() > 0:
                prim_str = str((cars_to_keep[i].prim_queue.top()[0], int(params.num_subprims*cars_to_keep[i].prim_queue.top()[1])))
            plot_prims[i] = ax.text(x,y, prim_str, color='w', horizontalalignment='center', verticalalignment='center', bbox=dict(facecolor='red', alpha=0.5), fontsize=10)

    # plot primitive tubes
    curr_tubes = []
    # initialize tubes
    if options.show_tubes:
        curr_tubes = [ax.plot([], [],'b')[0] for _ in range(len(cars_to_keep))]

        for i in range(len(cars_to_keep)):
            curr_car = cars_to_keep[i]
            if curr_car.prim_queue.len() > 0:
                if curr_car.prim_queue.top()[1] < 1:
                    curr_prim_id = curr_car.prim_queue.top()[0]
                    if curr_prim_id == -1:
                        pass
                    else:
                        curr_prim_progress = curr_car.prim_queue.top()[1]
                        vertex_set = tubes.make_tube(curr_prim_id)
                        xs = [vertex[0][0] for vertex in vertex_set[int(curr_prim_progress * params.num_subprims )]]
                        ys = [vertex[1][0] for vertex in vertex_set[int(curr_prim_progress * params.num_subprims )]]
                        xs.append(xs[0])
                        ys.append(ys[0])
                        curr_tubes[i].set_data(xs,ys)

    # if cars are hitting pedestrians replace pedestrian with medic sign
    for person in pedestrians_to_keep:
        for car in cars_to_keep:
            collision_free1,_ = collision_free(person, car)
            if not collision_free1 and car.state[0] > 1:
                medic_signs.append((person.state[0], person.state[1]))
                del pedestrians[pedestrians.index(person)]

    # plot honking 
    np.random.shuffle(pedestrians_waiting)
    np.random.shuffle(pedestrians_to_keep)
    draw_pedestrians(pedestrians_waiting, background)
    draw_medic_signs(medic_signs)
    draw_pedestrians(pedestrians_to_keep, background) # draw pedestrians to background
    draw_cars(cars_to_keep, background)


    # plot traffic light walls
    walls = [ax.plot([], [],'r')[0] for _ in range(4)]
    if options.show_traffic_light_walls:
        if traffic_lights.get_states('horizontal', 'color') == 'red':
            xs = intersection.traffic_light_walls['west']['x']
            ys = intersection.traffic_light_walls['west']['y']
            xs.append(xs[0])
            ys.append(ys[0])
            walls[0].set_data(xs,ys)
            xs = intersection.traffic_light_walls['east']['x']
            ys = intersection.traffic_light_walls['east']['y']
            xs.append(xs[0])
            ys.append(ys[0])
            walls[1].set_data(xs,ys)
        elif traffic_lights.get_states('vertical', 'color') == 'red':
            xs = intersection.traffic_light_walls['north']['x']
            ys = intersection.traffic_light_walls['north']['y']
            xs.append(xs[0])
            ys.append(ys[0])
            walls[2].set_data(xs,ys)
            xs = intersection.traffic_light_walls['south']['x']
            ys = intersection.traffic_light_walls['south']['y']
            xs.append(xs[0])
            ys.append(ys[0])
            walls[3].set_data(xs,ys)

    stage = ax.imshow(background, origin="lower") # update the stage
    all_artists = [stage] + [honk_waves] + boxes + curr_tubes + ids + plot_prims + walls + vertical_lights + horizontal_lights
    return all_artists
t0 = time.time()
animate(0)
t1 = time.time()
interval = (t1 - t0)
interval = 1

ani = animation.FuncAnimation(fig, animate, frames=int(options.duration/options.dt), interval=interval, blit=True, repeat=False) # by default the animation function loops so set repeat to False in order to limit the number of frames generated to num_frames

if options.save_video:
    Writer = animation.writers['ffmpeg']
    writer = Writer(fps = options.speed_up_factor*int(1/options.dt), metadata=dict(artist='Me'), bitrate=-1)
    ani.save('../movies/cython.avi', writer=writer, dpi=200)
plt.show()
t2 = time.time()
print('Total elapsed time: ' + str(t2-t0))
