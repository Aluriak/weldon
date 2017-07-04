"""Complex storyline with multiple students and teachers.

"""

import re
import random
from pprint import pprint
from functools import partial, wraps
import pytest
import server as weldon
from webclient import Send as Client
from commons import ServerError
import populate_server


class StoryError(Exception):
    pass


def get_story_sections(func:callable) -> iter:
    """Yield story sections in incoming order"""
    reg_section = re.compile('^\#([^\s]+)\s(.*)$')
    at_least_one_match = False
    for line in map(str.strip, func.__doc__.splitlines()):
        match = reg_section.match(line)
        if match:
            yield match.groups()
            at_least_one_match = True
    if not at_least_one_match:
        raise StoryError("No sections in {}".format(func.__name__))


def storyline(func):
    """Decorator making function a storyline described in its __doc__."""
    # @wraps  # breaks pytest introspection
    def storylined():
        context = type('ContextClass', (), {})  # data holder
        for idx, (section, comment) in enumerate(get_story_sections(func)):
            print('#' * 80)
            print('# {} {}'.format(idx, comment))
            context = globals()['section_' + section](context) or context
            print('#' * 80, end='\n\n')
    return storylined



@storyline
def test_story_multistudent():
    """Storyline:

    #init creation of the server
    #1 gérard (teacher) create a first problem (revcomp).
    #2 michel et jacqueline (students) register
    #3 jacqueline submit a first perfect solution
    #4 michel submit a first non-perfect solution
    #5 jacqueline submit a community test
    #6 michel submit a first perfect solution
    #7 michel submit a community test
    #8 jacqueline submit again its solution

    """


def section_init(context):
    context.PLAYER_PASSWORD = 'WOLOLO42'
    context.server = weldon.Server(player_password=context.PLAYER_PASSWORD)

def section_1(context):
    context.gerard = context.server.register_rooter('gérard')
    context.problem = context.server.register_problem(
        context.gerard, 'revcomp', *populate_server.PROBLEMS['revcomp']
    )
    context.problem_id = context.problem.title

def section_2(context):
    context.michel = context.server.register_player('michel', password=context.PLAYER_PASSWORD)
    context.jacqueline = context.server.register_player('jacqueline', password=context.PLAYER_PASSWORD)

def section_3(context):
     context.server.submit_solution(context.jacqueline, context.problem_id, GOOD_SOLUTION)

def section_4(context):
     context.server.submit_solution(context.michel, context.problem_id, BAD_SOLUTION)

def section_5(context):
     context.server.submit_test(context.jacqueline, context.problem_id, NEW_UNIT_TEST_1)

def section_6(context):
     context.server.submit_solution(context.michel, context.problem_id, GOOD_SOLUTION)

def section_7(context):
     context.server.submit_test(context.michel, context.problem_id, NEW_UNIT_TEST_2)

def section_8(context):
     context.server.submit_solution(context.jacqueline, context.problem_id, GOOD_SOLUTION)


GOOD_SOLUTION = """
def revcomp(sequence):
    complement = {'A': 'T', 'T': 'A', 'G': 'C', 'C': 'G',
                  'a': 't', 't': 'a', 'g': 'c', 'c': 'g'}
    try:
        return ''.join(reversed(tuple(complement[letter] for letter in sequence)))
    except KeyError:
        raise ValueError("Input sequence is not an ATGC one.")
"""
BAD_SOLUTION = """
def revcomp(sequence):
    complement = {'A': 'T', 'T': 'A', 'G': 'C', 'C': 'G',
                  'a': 't', 't': 'a', 'g': 'c', 'c': 'g'}
    return ''.join(reversed(tuple(complement[letter] for letter in sequence)))
"""
NEW_UNIT_TEST_1 = """
def test_multinuc_8():
    assert revcomp('CA') == 'TG'
"""
NEW_UNIT_TEST_2 = """
def test_multinuc_9():
    assert revcomp('CAT') == 'ATG'
"""
