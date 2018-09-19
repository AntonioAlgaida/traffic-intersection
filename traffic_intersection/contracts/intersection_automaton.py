from contract_automaton import *

h_traffic_states = {'r_h', 'g_h', 'y_h', 'h_walk', 'both_r_h'}
h_trans_must = {}
h_trans_may = {}
starts_h = {'g_h'}
h_input_alph = {'r_v', 'g_v', 'y_v'}
h_output_alph = {'r_h', 'g_h', 'y_h', 'h_walk'}

h_trans_may[('g_h', 'r_h')] = {('True', 'r_h', '!')}
h_trans_must[('r_h', 'h_walk')] = {('h_timer == 2', 'r_h', '!')}
h_trans_must[('h_walk', 'h_walk')] = {('True', 'r_h', '!'), ('True', 'h_walk', '!')}
h_trans_must[('h_walk', 'both_r_h')] = {('True', 'r_v', '?')}
h_trans_must[('both_r_h', 'g_h')] = {('h_timer == 2', 'r_v', '?')}
h_trans_must[('g_h', 'y_h')] = {('True', 'r_v', '?')}
# h_trans_must[('g_h', 'g_h')] = {('True', 'g_h', '!')}
# h_trans_must[('y_h', 'y_h')] = {('True', 'y_h', '!')}
# h_trans_must[('y_h', 'fail')] = {('True', 'g_v', '?'), ('True', 'y_v', '?')}
# h_trans_must[('g_h', 'fail')] = {('True', 'g_v', '?'), ('True', 'y_v', '?')}
h_trans_must[('y_h', 'r_h')] = {('h_timer == 5', 'r_h', '!')}
h = construct_contract_automaton(state_set = h_traffic_states, starts = starts_h, musttrans = h_trans_must, maytrans = h_trans_may, input_alphabet = h_input_alph, output_alphabet = h_output_alph)
	
v_traffic_states = {'r_v', 'g_v', 'y_v', 'v_walk', 'both_r_v'}
v_trans_must = {}
v_trans_may = {}
v_input_alph = {'r_h', 'g_h', 'y_h'}
v_output_alph = {'r_v', 'g_v', 'y_v', 'v_walk'}
starts_v = {'v_walk'}

v_trans_may[('g_v', 'r_v')] = {('True', 'r_v', '!')}
v_trans_must[('r_v', 'v_walk')] = {('v_timer == 2', 'r_v', '!')}
v_trans_must[('v_walk', 'v_walk')] = {('True', 'r_v', '!'), ('True', 'v_walk', '!')}
v_trans_must[('v_walk', 'both_r_v')] = {('True', 'r_h', '?')}
v_trans_must[('both_r_v', 'g_v')] = {('v_timer == 2', 'r_h', '?')}
v_trans_must[('g_v', 'y_v')] = {('True', 'r_h', '?')}
v_trans_must[('y_v', 'r_v')] = {('v_timer == 5', 'r_v', '!')}
# v_trans_must[('y_v', 'fail')] = {('True', 'g_h', '?'), ('True', 'y_h', '?')}
# v_trans_must[('g_v', 'fail')] = {('True', 'g_h', '?'), ('True', 'y_h', '?')}
# h_trans_must[('g_v', 'g_v')] = {('True', 'g_v', '!')}
# h_trans_must[('y_v', 'y_v')] = {('True', 'y_v', '!')}

v = construct_contract_automaton(state_set = v_traffic_states, starts = starts_v, musttrans = v_trans_must, maytrans = v_trans_may, input_alphabet = v_input_alph, output_alphabet = v_output_alph)

pedestrian_states = {'p'}
p_must = {}
p_may = {}
p_input_alph = {'v_walk', 'h_walk'}
p_may[('p', 'p')] = {('can_walk', 'v_walk', '?'), ('can_walk', 'h_walk', '?')}
p = construct_contract_automaton(state_set = pedestrian_states, starts = pedestrian_states, musttrans = p_must, maytrans = p_may, input_alphabet = p_input_alph)

h.convert_to_digraph().render('h', view = True)
v.convert_to_digraph().render('v', view = True)



# road_states = ['full', 'not full', 'aux', 'start_road', 'aux2']
# road_trans_may = {}
# road_trans_must = {}
# starts_road = {'start_road'}
# road_trans_may[('full', 'not full')] = ('g_exit', 'can_exit', '!')
# road_trans_must[('full', 'aux2')] = ('num_cars < max_cap', '', '')
# road_trans_must[('aux2', 'not full')] = ('True', '', '')
# road_trans_may[('full', 'aux2')] = ('num_cars < max_cap', '', '')
# road_trans_may[('aux2', 'not full')] = ('True', '', '')

# road_trans_may[('start_road', 'full')] = ('num_cars == max_cap', '', '')
# road_trans_may[('start_road', 'not full')] = ('num_cars < max_cap', '', '')
# road_trans_must[('not full', 'aux')] = ('g_enter', 'can_enter', '!')
# road_trans_must[('aux', 'full')] = ('num_cars == max_cap', '', '')
# road_trans_may[('not full', 'aux')] = ('g_enter', 'can_enter', '!')
# road_trans_may[('aux', 'full')] = ('num_cars == max_cap', '', '')
# road_trans_must[('aux', 'not full')] = ('num_cars < max_cap', '', '')
# road_trans_may[('not full', 'not full')] = ('g_exit', 'can_exit', '!')

# road_auto = construct_contract_automaton(state_set = road_states, starts = starts_road, musttrans = road_trans_must, maytrans = road_trans_may)
# road_auto.convert_to_digraph().render('road', view = True)

car_states = {'0', '1', '2', '3'}
car_must = {}
car_may = {}
car_start = {'0'}
car_input_alph = {'rejected', 'accepted', 'primitives'}
car_output_alph = {'request'}
car_must[('0', '1')] = {('True', 'request', '!')}
car_must[('1', '2')] = {('True', 'accepted', '?')}
car_must[('1', '0')] = {('True', 'rejected', '!')}
car_must[('2', '3')] = {('True', 'primitives', '?')}
car_may[('3', '3')] = {('True', 'primitives', '?')}
car_may[('3', '0')] = {('not_done', 'request', '!')}
car_auto = construct_contract_automaton(state_set = car_states, starts = car_start, musttrans = car_must, maytrans = car_may, input_alphabet = car_input_alph, output_alphabet = car_output_alph)
car_auto.convert_to_digraph().render('car', view = True)

traff = compose_contract(h, v)
composed = compose_contract(traff, p)
composed.convert_to_digraph().render('total', view = True)

