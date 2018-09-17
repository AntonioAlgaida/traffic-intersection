#!/usr/local/bin/python
# Visualization
# Tung M. Phan
# California Institute of Technology
# July 17, 2018
import sys
sys.path.append('..')
from prepare.helper import *
import time, platform, warnings, matplotlib, random
import components.scheduler as scheduler
import datetime
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

# set randomness
if not options.random_simulation:
    random.seed(options.random_seed)
    np.random.seed(options.np_random_seed )
# creates figure
fig = plt.figure()
ax = fig.add_axes([0,0,1,1]) # get rid of white border
if not options.show_axes:
    plt.axis('off')
# sampling time
dt = options.dt

#if true, pedestrians can cross street and cars cannot cross
def safe_to_walk(green_duration, light_color, light_time):
    walk_sign_delay = green_duration / 10
    return(light_color == 'green' and (light_time + walk_sign_delay) <= (green_duration / 3 + walk_sign_delay))

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

# create traffic intersection
the_traffic_intersection = Image.open(intersection.intersection_fig)
x_lim, y_lim = the_traffic_intersection.size
# create traffic lights
traffic_lights = traffic_signals.TrafficLights(yellow_max = 10, green_max = 50, random_start = True)
# create planner
planner = scheduler.Scheduler()
# create pedestrians
pedestrians = []

def animate(frame_idx): # update animation by dt
    t0 = time.time()
    ax.cla() # clear Axes before plotting
    deadlocked = False
    global_vars.current_time = frame_idx * dt # update current time from frame index and dt

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
    # car request
    if with_probability(options.new_car_probability):
        new_start_node, new_end_node, new_car = spawn_car()
        planner._request_queue.enqueue((new_start_node, new_end_node, new_car)) # planner takes request
    service_count = 0
    original_request_len = planner._request_queue.len()
    while planner._request_queue.len() > 0 and not deadlocked: # if there is at least one live request in the queue
        planner.serve(graph=car_graph.G,traffic_lights=traffic_lights)
        service_count += 1
        if service_count == original_request_len:
            service_count = 0 # reset service count
            if planner._request_queue.len() == original_request_len:
                deadlocked = True
            else:
                original_request_len = planner._request_queue.len()
    planner.clear_stamps()

    # pedestrian entering
    if with_probability(options.new_pedestrian_probability):
        while True:
            name, begin_node, final_node, the_pedestrian = spawn_pedestrian()
            if not begin_node == final_node:
                break
        _, shortest_path = dijkstra((begin_node[0], begin_node[1]), final_node, pedestrian_graph.G)
        vee = np.random.uniform(20, 40)
        while len(shortest_path) > 1:
                the_pedestrian.prim_queue.enqueue(((shortest_path[0], shortest_path[1], vee), 0))
                del shortest_path[0]
        pedestrians.append(the_pedestrian)

    # update traffic lights
    traffic_lights.update(dt)
    update_traffic_lights(ax, plt, traffic_lights) # for plotting
    draw_walk_signs(traffic_signals.walk_sign_figs['vertical'][vertical_walk_safe], traffic_signals.walk_sign_figs['horizontal'][horizontal_walk_safe], the_traffic_intersection)

    # update cars
    cars_to_keep = []
    update_cars(cars_to_keep, dt)
    draw_cars_fast(ax, cars_to_keep)

    # update pedestrians
    if len(pedestrians) > 0:
        for person in pedestrians:
            if (person.state[0] <= x_lim and person.state[0] >= 0 and person.state[1] >= 0 and person.state[1] <= y_lim):
                person_xy = (person.state[0], person.state[1])
                walk_sign_duration = green_duration / 3.
                remaining_vertical_time = abs(walk_sign_duration - vertical_light_time)
                remaining_horizontal_time = abs(walk_sign_duration  - horizontal_light_time)

                if person_xy not in (pedestrian_graph.lane1 + pedestrian_graph.lane2 + pedestrian_graph.lane3 + pedestrian_graph.lane4): # if pedestrian is not at any of the nodes then continue  
                    person.prim_next(dt)
                    global_vars.pedestrians_to_keep.add(person)
                elif continue_walking(person, vertical_walk_safe, pedestrian_graph.lane1, pedestrian_graph.lane2, (-pi/2, pi/2), remaining_vertical_time): # if light is green cross the street, or if at a node and facing away from the street i.e. just crossed the street then continue
                    person.prim_next(dt)
                    global_vars.pedestrians_to_keep.add(person)
                elif continue_walking(person, horizontal_walk_safe, pedestrian_graph.lane3, pedestrian_graph.lane4, (pi, 0), remaining_horizontal_time):
                    person.prim_next(dt)
                    global_vars.pedestrians_to_keep.add(person)
                else:
                    person.state[3] = 0

                # pedestrians walk faster if not going fast enough to finish crossing the street before walk sign is off or 'false'
                if is_between(pedestrian_graph.lane1, person_xy) or is_between(pedestrian_graph.lane2, person_xy):
                    walk_faster(person, remaining_vertical_time)
                elif is_between(pedestrian_graph.lane3, person_xy) or is_between(pedestrian_graph.lane4, person_xy):
                    walk_faster(person, remaining_horizontal_time)
            else:
                del person

    ################################ Update and Generate Visuals ################################ 
    # highlight crossings
    vertical_lane_color = 'g' if vertical_walk_safe else 'r'
    horizontal_lane_color = 'g' if horizontal_walk_safe else 'r'
    if options.highlight_crossings:
        draw_crossings(ax, plt, vertical_lane_color, horizontal_lane_color)
    # show honk wavefronts
    if options.show_honks:
        show_wavefronts(ax, dt)
        honk_randomly(cars_to_keep)
    # show bounding boxes
    if options.show_boxes:
        plot_boxes(ax, cars_to_keep)
    # show license plates
    if options.show_plates:
        show_license_plates(ax, cars_to_keep)
    # show primitive ids
    if options.show_prims:
        show_prim_ids(ax, cars_to_keep)
    # show primitive tubes
    if options.show_tubes:
        plot_tubes(ax, cars_to_keep)
    # show traffic light walls
    if options.show_traffic_light_walls:
        plot_traffic_light_walls(ax, traffic_lights)
    # check for collisions and update pedestrian state
    check_for_collisions(cars_to_keep)
    draw_pedestrians(ax) # draw pedestrians to background

    the_intersection = [ax.imshow(the_traffic_intersection, origin="lower")] # update the stage
    all_artists = the_intersection + global_vars.crossing_highlights + global_vars.honk_waves + global_vars.boxes + global_vars.curr_tubes + global_vars.ids + global_vars.prim_ids_to_show + global_vars.walls + global_vars.show_traffic_lights + global_vars.cars_to_show + global_vars.pedestrians_to_show
    t1 = time.time()
    elapsed_time = (t1 - t0)
    print('{:.2f}'.format(global_vars.current_time)+'/'+str(options.duration) + ' at ' + str(int(1/elapsed_time)) + ' fps') # print out current time to 2 decimal places
    return all_artists
t0 = time.time()
animate(0)
t1 = time.time()
interval = (t1 - t0)
ani = animation.FuncAnimation(fig, animate, frames=int(options.duration/options.dt), interval=interval, blit=True, repeat=False) # by default the animation function loops so set repeat to False in order to limit the number of frames generated to num_frames
if options.save_video:
    Writer = animation.writers['ffmpeg']
    writer = Writer(fps = options.speed_up_factor*int(1/options.dt), metadata=dict(artist='Me'), bitrate=-1)
    now = str(datetime.datetime.now())
    ani.save('../movies/' + now + '.avi', writer=writer, dpi=200)
plt.show()
t2 = time.time()
print('Total elapsed time: ' + str(t2-t0))
