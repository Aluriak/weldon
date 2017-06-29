"""Implementation of player report creation.

Once a problem is finished, a report is created
for each participating player.

"""


from io import StringIO
from itertools import chain
from contextlib import redirect_stdout
from collections import defaultdict

from commons import SubmissionResult
from pylint_interface import run_pylint_on_source
from bashplotlib.histogram import plot_hist


MAX_PLOT_HEIGHT = 20


def plot_passed_tests(number_of_passed_test:iter) -> str:
    # get timeline data in term of unique observation.
    #  in: [1, 2, 4, 3]
    # out: [1, 1, 2, 2, 3, 3, 3, 3, 4, 4, 4]
    data = tuple(chain.from_iterable((
        ([time] * nb_test)  # the value at x-axis must appears nb_test time in data
        for time, nb_test in enumerate(number_of_passed_test)
    )))

    # limit plot size
    hist_height = max(number_of_passed_test)
    while hist_height > MAX_PLOT_HEIGHT:
        hist_height //= 2

    # print the plot
    output = StringIO()
    with redirect_stdout(output):
        plot_hist(data, title='Number of passed tests according to time',
                  pch='█', colour='green', height=hist_height)
    return output.getvalue()


def make_report_on_player(name:str, token:str,
                          submissions:[SubmissionResult], problem) -> iter:
    """Yield lines of report"""
    # setup
    yield ('{emph} {} {emph}').format(name, emph='#'*20)
    yield "Send {} submissions for problem '{}' (id:{}).".format(
        len(submissions), problem.title, problem.id
    )
    yield ''
    final_submission = submissions[-1]
    passed_tests = []  # number of passed test per submission
    for submission in submissions:
        validated_tests = frozenset(test for test in submission.tests if test.succeed)
        passed_tests.append(len(validated_tests))

    # add a few padding on the left of the plot.
    yield from ('\t' + line for line in plot_passed_tests(passed_tests).splitlines())

    yield ''
    yield '#' * 10 + ' Final submission ' + '#' * 10
    yield from stats_on_tests(name, token, problem, submissions)

    # coding style (pylint)
    pylint_report = run_pylint_on_source(final_submission.source_code,
                                         module_name='module')
    yield ''
    yield from ('Pylint messages:\n\t' + '\n\t'.join(pylint_report.messages)).splitlines()
    yield '{}/10 pylint score'.format(pylint_report.rate)

    # teardown
    yield '#' * 80 + '\n\n\n\n\n'


def stats_on_tests(name, token, problem, submissions) -> iter:
    last_submission = submissions[-1]
    types = defaultdict(set)
    for test in last_submission.tests:
        types[test.type].add(test)
    testtypes = {type: ({test for test in tests if test.succeed}, tests)
                 for type, tests in types.items()}
    yield 'TESTS:'
    for type in ('public', 'hidden', 'community'):
        succeeds, tests = testtypes.get(type, ((), ()))
        msg = '\t{}: {}/{}'.format(type.upper(), len(succeeds), len(tests))
        if type == 'community':
            msg += '\t ({} sent)'.format(_nb_tests_sent_by(token, problem.tests))
        yield msg
    nb_regression = _nb_regression(submissions)
    if nb_regression:
        yield '\t{} regressions'.format(_nb_regression(submissions))
    else:
        yield '\tNo regressions'



def _nb_tests_sent_by(token:str, tests) -> int:
    return len(tuple(test for test in tests if test.author == token))


def _nb_regression(submissions) -> int:
    count = 0
    prev_success = 0
    for submission in submissions:
        curr_success = sum(1 for test in submission.tests if test.succeed)
        if curr_success < prev_success:
            count += prev_success - curr_success
            prev_success = curr_success
    return count



if __name__ == "__main__":
    print(plot_passed_tests([0, 10, 40, 11, 7, 3, 8, 34]))
