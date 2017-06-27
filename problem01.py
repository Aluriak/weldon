"""Exemple of problem case for weldon.

This contains:
- description of the problem
- public unit tests
- hidden unit tests

"""

from pprint import pprint
import pytest
import server as weldon


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

print('#' * 80)
print('# TEARCHER PART')
print('#' * 80)


# Registering is performed by the rooter.
# It gives to the server the exact definition of the problem,
#  that any player can retrieve.
PLAYER_PASSWORD = 'WOLOLO42'
server = weldon.Server(player_password=PLAYER_PASSWORD)
rooter_token = server.register_rooter()
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


SOLUTION = """
def revcomp(sequence):
    complement = {'A': 'T', 'T': 'A', 'G': 'C', 'C': 'G',
                  'a': 't', 't': 'a', 'g': 'c', 'c': 'g'}
    try:
        return ''.join(reversed(tuple(complement[letter] for letter in sequence)))
    except KeyError:
        raise ValueError("Input sequence is not an ATGC one.")
"""

print('I code my solution, and send it to the server using my token.')
server_answer = server.submit_solution(my_token, problem.id, SOLUTION)
print("Server answers me with a full trace and a dictionnary giving test results:")
pprint(server_answer.tests)


print('\n\nI can also send new unit tests.')
server.submit_test(my_token, problem.id, """
def test_sent_by_lucas():
    assert revcomp('AAT') == 'ATT'
""")


print('\n\nI can send again my solution, to prove that i pass the new test.')
server_answer = server.submit_solution(my_token, problem.id, SOLUTION)
print("Server answers me with a full trace and a dictionnary giving test results:")
pprint(server_answer.tests)
