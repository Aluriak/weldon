

import random
from pprint import pprint

from webserver import PORT as TCP_PORT, BUFFER_SIZE
from webclient import Send
from commons import ServerError


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


print('#' * 80)
print('# ROOTER PART')
print('#' * 80)


# Registering is performed by the rooter.
# It gives to the server the exact definition of the problem,
#  that any player can retrieve.
root_conn = Send(name='lucas', registration_password='SHUBISHI', root=True)
assert root_conn.get_api() == root_conn.server_api  # the first request the server

print("Rooter register itself as a rooter, getting (secret) token '{}'."
      "".format(root_conn.token))

print("Rooter, using (secret) token, create a new problem on the server.")
try:
    problem = root_conn.register_problem(
        'problem01',
        DESCRIPTION,
        public_tests=PUBLIC_TESTS,
        hidden_tests=HIDDEN_TESTS,
    )
    print('Problem registered as', problem.title)
except ServerError as e:
    # NOTE: you can override internals params during call, or…
    problem = root_conn.retrieve_problem(problem_id='problem01')
root_conn.problem_id = 'problem01'  # … set them for later calls
root_conn.open_problem_session()
print('Problem already registered registered as', problem.title)


PLAYER_PASSWORD = 'WOLOLO42'
print("Rooter gives to the player the password '{}', to use to register."
      "".format(PLAYER_PASSWORD))



print('\n\n')
print('#' * 80)
print('# PLAYER PART')
print('#' * 80)

print("First, i need to register on server, as a player."
      " Rooter gives me the password '{}'".format(PLAYER_PASSWORD))
conn = Send(name='elucator', registration_password=PLAYER_PASSWORD)
print('My (secret) token is', conn.token)

print('\nUsing my token, i can ask for specific problem at server.')
conn.problem_id = 'problem01'  # could have been given to Send object constructor
problem = conn.retrieve_public_problem()
print('The problem given by the rooter is {}.'.format(problem.title))
print('Full object given by server:\n', problem, '\n\n', sep='')

print("\nNote that, as a player, i can't submit new problems.")
# Also, the Send object do not provide non-accessible API
#  (for instance, register_problem when player is not root).
#  So, we have to bypass it to perform the problem registering.
#  Note that server will detect the fault and return an error.
try:
    conn._send(
        'register_problem', token=conn.token, title='title',
        description='description', public_tests='tests',
        hidden_tests='tests'
    )
    assert False, "Call to 'register_problem' as a student did not raise any error."
except ServerError:
    print("I tested, and server detected the fault")

print('I code my solution, and send it to the server using my token.')
server_answer = conn.submit_solution(BAD_SOLUTION)
print("Server answers me with a full trace and a dictionnary giving test results:")
pprint(server_answer.tests)
print("I can see that my solution do not pass all the tests. I propose another one.")
server_answer = conn.submit_solution(GOOD_SOLUTION)
print("This time it's ok:")
pprint(server_answer.tests)
# print(server_answer.full_trace)
assert all(test.succeed for test in server_answer.tests)


print('\n\nI can also send new unit tests.')
try:
    conn.submit_test(NEW_UNIT_TEST_BAD)
    assert False, "server didn't spot the error in NEW_UNIT_TEST_BAD"
except ServerError as e:
    print('Server refused my test because', e.args[0])
print('So i update my code and resend it:')
try:
    conn.submit_test(NEW_UNIT_TEST_GOOD)
    print('Now it is added to the community tests for this exercise !')
except ServerError as e:
    assert e.args[0].startswith('A test is already named '), "Wrong error spotted by Server on NEW_UNIT_TEST_BAD"
    print('Well, it already exists. So i already succeed to pass it \o/')


print('\n\nI can send again my solution, to prove that i pass the new test.')
server_answer = conn.submit_solution(GOOD_SOLUTION)
print("Server answers me with a full trace and a dictionnary giving test results:")
pprint(server_answer.tests)
assert all(test.succeed for test in server_answer.tests)


print('\n\n\n\n')
print('#' * 80)
print('# ROOTER PART II')
print('#' * 80)
print('Rooter will close the session, because deadline is met.')
root_conn.close_problem_session()


print('\n\n\n\n')
print('#' * 80)
print('# PLAYER PART II')
print('#' * 80)
print("As a player, i can't push new solutions since the sesson is over:")
server_answer = conn.submit_solution(GOOD_SOLUTION)
pprint(server_answer.tests)



print('\n\n\n\n')
print('#' * 80)
print('# ROOTER PART III')
print('#' * 80)
print('Rooter will now ask for report about students work.')
print('Rooter can retrieve students implied in the problem:')
players = root_conn.retrieve_players_of()
print('\t' + '\n\t'.join(players))
choosen_player = random.choice(players)
print('Rooter looks at the progress of student {} by asking a report to the server:'
      ''.format(choosen_player))

print('\n\n')
report = root_conn.retrieve_report(token=choosen_player)
print(report)
