"""Exemple of problem case for weldon.

This contains:
- description of the problem
- public unit tests
- hidden unit tests

"""

import random
from pprint import pprint
import pytest
import server as weldon
from commons import ServerError, SourceError


def test_story_problem01():
    print('#' * 80)
    print('# ROOTER PART')
    print('#' * 80)

    # Registering is performed by the rooter.
    # It gives to the server the exact definition of the problem,
    #  that any player can retrieve.
    PLAYER_PASSWORD = 'WOLOLO42'
    server = weldon.Server(player_password=PLAYER_PASSWORD)
    rooter_token = server.register_rooter('gérard')
    print("Rooter register itself as a rooter, getting (secret) token {}."
          "".format(rooter_token))
    problem = server.register_problem(
        rooter_token,
        'problem01',
        DESCRIPTION,
        public_tests=PUBLIC_TESTS,
        hidden_tests=HIDDEN_TESTS,
        # TODO: implement rules (or additionnal options on problem)
        # rules=['allow upload test if all tests succeed',
               # 'allow upload solution if player or rooter']  # should be a default
    )
    assert problem.title == 'problem01'
    assert problem.description == DESCRIPTION

    print("Rooter, using (secret) token, create a new problem on the server.")
    print("Rooter gives to the player the password '{}', to use to register."
          "".format(PLAYER_PASSWORD))




    print('\n\n')
    print('#' * 80)
    print('# PLAYER PART')
    print('#' * 80)

    print("First, i need to register on server, as a player."
          " Rooter gives me the password '{}'".format(PLAYER_PASSWORD))
    my_token = server.register_player('lucas', password=PLAYER_PASSWORD)
    print('My (secret) token is', my_token)

    print('\nUsing my token, i can ask for specific problem at server.')
    problem = server.retrieve_public_problem(my_token, 'problem01')
    print('The problem given by the rooter is {}.'.format(problem.title))
    print('Full object given by server:\n', problem, '\n\n', sep='')

    print("\nNote that, as a player, i can't submit new problems.")
    with pytest.raises(ServerError):
        print(server.register_problem(my_token, '', '', '', ''))

    print('I code my solution, and send it to the server using my token.')
    server_answer = server.submit_solution(my_token, problem.id, BAD_SOLUTION)
    print("Server answers me with a full trace and a dictionnary giving test results:")
    pprint(server_answer.tests)
    print("I can see that my solution do not pass all the tests. I propose another one.")
    server_answer = server.submit_solution(my_token, problem.id, GOOD_SOLUTION)
    print("This time it's ok:")
    pprint(server_answer.tests)
    # print(server_answer.full_trace)
    assert all(test.succeed for test in server_answer.tests)

    print('\n\nI can also send new unit tests.')
    try:
        server.submit_test(my_token, problem.id, NEW_UNIT_TEST_BAD)
        assert False, "server didn't spot the error in NEW_UNIT_TEST_BAD"
    except SourceError as e:
        print('Server refuse my test because', e.args[0])
    print('So i update my code and resend it:')
    server.submit_test(my_token, problem.id, NEW_UNIT_TEST_GOOD)
    print('Now it is added to the community tests for this exercise !')


    print('\n\nI can send again my solution, to prove that i pass the new test.')
    server_answer = server.submit_solution(my_token, problem.id, GOOD_SOLUTION)
    print("Server answers me with a full trace and a dictionnary giving test results:")
    pprint(server_answer.tests)
    assert all(test.succeed for test in server_answer.tests)


    print('\n\n\n\n')
    print('#' * 80)
    print('# ROOTER PART II')
    print('#' * 80)
    print('Rooter will close the session, because deadline is met.')
    server.close_problem_session(rooter_token, problem.id)


    print('\n\n\n\n')
    print('#' * 80)
    print('# PLAYER PART II')
    print('#' * 80)
    print("As a player, i can't push new solutions since the sesson is over:")
    server_answer = server.submit_solution(my_token, problem.id, GOOD_SOLUTION)
    pprint(server_answer.tests)



    print('\n\n\n\n')
    print('#' * 80)
    print('# ROOTER PART III')
    print('#' * 80)
    print('Rooter will now ask for report about students work.')
    print('Rooter can retrieve students implied in the problem:')
    players = server.retrieve_players_of(rooter_token, problem.id)
    print('\t' + '\n\t'.join(players))
    assert len(players) == 1, "There is only one student in this story, but not 1 are found"
    choosen_player = random.choice(players)
    print('Rooter looks at the progress of student {} by asking a report to the server:'
          ''.format(choosen_player))

    print('\n\n')
    report = server.retrieve_report(choosen_player, problem.id)
    print(report)


DESCRIPTION = """Writing in a module *revcomp.py* a function *revcomp*
that convert ATGC to TACG and reverse the sequence.
Insert here more biological background and formal explanations,
and also expected behavior on error.
"""

PUBLIC_TESTS = ("""
def test_onenuc():
    assert revcomp('A') == 'T'
    assert revcomp('T') == 'A'
    assert revcomp('C') == 'G'
    assert revcomp('G') == 'C'
""","""
def test_multinuc_1():
    assert revcomp('ATCG') == 'CGAT'
""","""
def test_multinuc_2():
    assert revcomp('AAAACAAAA') == 'TTTTGTTTT'
""","""
def test_error1():
    with pytest.raises(ValueError):
        revcomp('ABCD')
""")
HIDDEN_TESTS = ("""
def test_multinuc_3():
    assert revcomp('AATACATAA') == 'TTATGTATT'
""","""
def test_multinuc_4():
    assert revcomp('ACGACATAA') == 'TTATGTCGT'
""","""
def test_multinuc_5():
    assert revcomp('acgacataa') == 'ttatgtcgt'
""")

BAD_SOLUTION = """
def revcomp(sequence):
    complement = {'A': 'T', 'T': 'A', 'G': 'C', 'C': 'G',
                  'a': 't', 't': 'a', 'g': 'c', 'c': 'g'}
    return ''.join(reversed(tuple(complement[letter] for letter in sequence)))
"""
GOOD_SOLUTION = """
def revcomp(sequence):
    complement = {'A': 'T', 'T': 'A', 'G': 'C', 'C': 'G',
                  'a': 't', 't': 'a', 'g': 'c', 'c': 'g'}
    try:
        return ''.join(reversed(tuple(complement[letter] for letter in sequence)))
    except KeyError:
        raise ValueError("Input sequence is not an ATGC one.")
"""
NEW_UNIT_TEST_BAD = """
def test_sent_by_student():
    revcomp('AAT') == 'ATT'
"""
NEW_UNIT_TEST_GOOD = """
def test_sent_by_student():
    assert revcomp('AAT') == 'ATT'
"""


if __name__ == "__main__":
    test_story_problem01()
