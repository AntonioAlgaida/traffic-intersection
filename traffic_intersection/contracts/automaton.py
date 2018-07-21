# Try 2!

from random import sample
import inequality as iq
import numpy as np
import itertools
from graphviz import Digraph

# General state class. Has a 'set' property for the purposes of composition.
class State:
    def __init__(self, text, newset = None):
        self.text = text.upper()
        if newset == None:
            self.set = set()
            self.set.add(self)
        else:
            self.set = newset

def product(state1, state2):
    newset = state1.set.union(state2.set)
    newtext = '('
    for state in state1.set:
        newtext += state.text + ', '
    for state in state2.set:
        newtext += state.text + ', '
    newtext = newtext[:-2]
    newtext += ')'
    return State(newtext, newset)


# General transition class. Transition is a string from the alphabet.
class Transition:
    def __init__(self, start = None, end = None, transition = None):
        self.startState = start
        self.endState = end
        self.transition = transition

    def set_start_state(self, start):
        self.startState = start

    def set_end_state(self, end):
        self.endState = end

    def set_transition(self, transition):
        self.transition = transition

    def show(self):
        return self.transition

# General transition class for guard (where the guard is a set of inequalities.)
class guardTransition(Transition):
    def __init__(self, start = None, end = None, guard = True, inp = set(), out = set(), inter = set()):
        Transition.__init__(self, start, end)
        self.guard = guard # guard should be a dictionary of inequalities
        self.inputs = inp # set of inputs on the transition
        self.outputs = out
        self.internals = inter

        # transition reads guard/?inputs, !outputs, #internals
    def show(self):
        transtext = ''

        if self.guard == False:
            return transtext

        elif self.guard == True:
            transtext += 'True'
        else:
            for key in self.guard:
                ineq = self.guard[key]
                transtext += ineq.show() + ', '

            transtext = transtext[:-2] # deletes last comma and space

        transtext += ' / '

        if len(self.inputs) > 0:
            transtext += ' ?' + ', '.join(self.inputs)
        if len(self.outputs) > 0:
            transtext += ' !' + ', '.join(self.outputs) 
        if len(self.internals) > 0:
            transtext += ' #' + ', '.join(self.internals)

        return transtext

# takes two guard transitions and returns their composition
def compose_guard_trans(tr1, tr2):

    if tr1.guard == True:
        guard = tr2.guard
    elif tr2.guard == True:
        guard = tr1.guard
    else:
        guard = iq.conjunct(tr1.guard, tr2.guard)

    newstart = product(tr1.startState, tr2.startState)
    newend = product(tr1.endState, tr2.endState)
    inp = tr1.inputs.intersection(tr2.inputs)
    out = tr1.outputs.intersection(tr2.outputs)
    inter = (tr1.inputs.intersection(tr2.outputs)).union(
        tr1.outputs.intersection(tr2.inputs)).union(tr1.internals).union(tr2.internals)
    if len(inp.union(out).union(inter)) == 0:
        return False

    return guardTransition(newstart, newend, guard, inp, out, inter)

# General finite automaton. 
class Automaton:
    def __init__(self):
        self.alphabet = set()
        self.transitions_dict = {} # transitions_dict[state] is the set of transitions from that state's TEXT
        self.startState = None
        self.endStates = set()
        self.states = set()

    def add_state(self, state, end_state = 0, start_state = 0):
        if end_state:
            self.endStates.add(state)
        if start_state:
            self.startState = state

        self.states.add(state)
        self.transitions_dict[state] = set()

    def add_transition(self, transition):
        self.transitions_dict[transition.startState].add(transition)

    def set_start_state(self, state):
        self.startState = state

    def simulate(self, is_printing = False):
        state = self.startState
        while state not in self.endStates:
            if is_printing:
                print(state + "  taking transitions, output, input")
            else:
                print("taking transitions, output, input")
            state, = sample(self.transitions_dict[state], 1).endState # sample from set of all transistions uniformly at random
        print("simulation has terminated or deadlocked!")           

    def convert_to_digraph(self):
        automata = Digraph(comment = 'insert description parameter later?')

        for state in self.states:
            # adds nodes
            automata.attr('node', shape = 'circle', color='green', style='filled', fixedsize='false', width='1')
            if state in self.endStates:
                automata.attr('node', shape = 'doublecircle')
            if state == self.startState:
                automata.attr('node', color = 'yellow')
            automata.node(state.text, state.text)

        # adds transitions
        for state in self.states:
            transit = self.transitions_dict[state] # this is a set of transitions from the state
            for trans in transit:
                if trans != False:
                    state2 = trans.endState
                    transtext = trans.show()
                    automata.edge(state.text, state2.text, label = transtext)

        return automata

class ComponentAutomaton(Automaton):
    def __init__(self, inputAlphabet = set(), outputAlphabet = set()):
        Automaton.__init__(self)
        self.input_alphabet = inputAlphabet
        self.output_alphabet = outputAlphabet
        self.alphabet = self.input_alphabet.union(self.output_alphabet)

def compose_components(component_1, component_2):
    new_component = ComponentAutomaton()
    newalphabet = component_1.alphabet.union(component_2.alphabet)
    # figure out what to do with input/output alphabets? 
    dict1 = component_1.transitions_dict
    dict2 = component_2.transitions_dict
    for key1 in dict1:
        for key2 in dict2:
            newstate = product(key1, key2)

            new_component.add_state(newstate, key1 in component_1.endStates and key2 in component_2.endStates
                , key1 == component_1.startState and key2 == component_2.startState)

            for trans1 in dict1[key1]:
                for trans2 in dict2[key2]:
                    new_component.transitions_dict[newstate].add(compose_guard_trans(trans1, trans2))

    new_component.alphabet = newalphabet
    return new_component

# Add this later to make testing easier
def convert_digraph_to_automaton(Digraph x):
    return True



