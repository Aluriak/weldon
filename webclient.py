
import json
import socket
from pprint import pprint
# from ast import literal_eval

import wjson
from webserver import PORT as TCP_PORT, BUFFER_SIZE


def send(function:str, *args:str, **kwargs:str):
    TCP_IP = '127.0.0.1'

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((TCP_IP, TCP_PORT))
    payload = wjson.as_json((function, tuple(args), kwargs)).encode()
    s.send(payload)

    buffer = True
    received = ''
    while buffer:
        buffer = s.recv(BUFFER_SIZE).decode()
        received += buffer
    data = wjson.from_json(received)
    s.close()

    return data


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
print('# ROOTER PART')
print('#' * 80)


# Registering is performed by the rooter.
# It gives to the server the exact definition of the problem,
#  that any player can retrieve.
rooter_token = send('register_rooter', 'lucas', 'SHUBISHI')
print("Rooter register itself as a rooter, getting (secret) token '{}'."
      "".format(rooter_token))

print("Rooter, using (secret) token, create a new problem on the server.")
problem = send(
    'register_problem',
    rooter_token,
    'problem01',
    DESCRIPTION,
    public_tests=PUBLIC_TESTS,
    hidden_tests=HIDDEN_TESTS,
)
print('Problem registered as', problem.title)

PLAYER_PASSWORD = 'WOLOLO42'
print("Rooter gives to the player the password '{}', to use to register."
      "".format(PLAYER_PASSWORD))




print('\n\n')
print('#' * 80)
print('# PLAYER PART')
print('#' * 80)

print("First, i need to register on server, as a player."
      " Rooter gives me the password '{}'".format(PLAYER_PASSWORD))
my_token = send('register_player', 'elucator', password=PLAYER_PASSWORD)
print('My (secret) token is', my_token)

print('\nUsing my token, i can ask for specific problem at server.')
problem = send('retrieve_public_problem', my_token, 'problem01')
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
server_answer = send('submit_solution', my_token, problem.id, SOLUTION)
print("Server answers me with a full trace and a dictionnary giving test results:")
pprint(server_answer)
pprint(server_answer.tests)
# print(server_answer.full_trace)


print('\n\nI can also send new unit tests.')
send('submit_test', my_token, problem.id, """
def test_sent_by_lucas():
    assert revcomp('AAT') == 'ATT'
""")


print('\n\nI can send again my solution, to prove that i pass the new test.')

server_answer = send('submit_solution', my_token, problem.id, SOLUTION)
print("Server answers me with a full trace and a dictionnary giving test results:")
pprint(server_answer.tests)
