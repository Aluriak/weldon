"""Populate a server with various problems.

"""

from webclient import Send as Client



def populate(conn:Client):
    for problem in copopulate(conn):
        pass

def populate_with(title:str, conn:Client):
    (desc, public, hidden) = PROBLEMS[title]
    return conn.register_problem(
        title,
        desc,
        public_tests=public,
        hidden_tests=hidden,
    )

def copopulate(conn:Client):
    """Coroutine version, allowing client to perform one at a time
    modification of remote server

    """
    for title, (desc, public, hidden) in PROBLEMS.items():
        yield conn.register_problem(
            title,
            desc,
            public_tests=public,
            hidden_tests=hidden,
        )


PROBLEMS = {
    'revcomp': (
        """Writing in a module *revcomp.py* a function *revcomp*
that convert ATGC to TACG and reverse the sequence.
Insert here more biological background and formal explanations,
and also expected behavior on error.
""",
        ("""
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
"""),
        ("""
def test_multinuc_3():
    assert revcomp('AATACATAA') == 'TTATGTATT'
""","""
def test_multinuc_4():
    assert revcomp('ACGACATAA') == 'TTATGTCGT'
""","""
def test_multinuc_5():
    assert revcomp('acgacataa') == 'ttatgtcgt'
"""
),
    ),
    'password': (
        """Writing in a module *password.py* a function *check_password*
that returns a truthy value if input value is a valid password.

A valid password is at least 8 character long,
and contains at least 1 char of each of the following types:
upper case, lower case, number, non-alphanumeric

""",
        ("""
def test_good_password():
    assert check_password('Aa1~Aa1~')
""","""
def test_no_upper():
    assert not check_password('a1~a1~a1~')
""","""
def test_no_lower():
    assert not check_password('A1~A1~A1~')
""","""
def test_no_number():
    assert not check_password('A_~A_~A_~')
""","""
def test_no_nonalphanum():
    assert not check_password('A1aA1aA1a')
"""),
        ("""
def test_good_password():
    assert check_password('Ta0>Ta0>')
""","""
def test_no_upper():
    assert not check_password('a0>a0>a0>')
""","""
def test_no_lower():
    assert not check_password('T0>T0>T0>')
""","""
def test_no_number():
    assert not check_password('T_>T_>T_>')
""","""
def test_no_nonalphanum():
    assert not check_password('T0aT0aT0a')
"""),
    ),
}
