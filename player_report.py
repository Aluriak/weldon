"""Implementation of player report creation.

Once a problem is finished, a report is created
for each participating player.

"""


from io import StringIO
from itertools import chain
from contextlib import redirect_stdout
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
                  pch='█', colour='green', showSummary=True, height=hist_height)
    return output.getvalue()


def make_report_on_player(name:str, submissions:[SubmissionResult], problem=None) -> iter:
    """Yield lines of report"""
    # setup
    yield '#' * 20 + ' ' + str(name) + ' ' + '#' * 20
    yield 'Sent {} submissions.'.format(len(submissions))
    final_submission = submissions[-1]
    passed_tests = []  # number of passed test per submission
    for submission in submissions:
        validated_tests = frozenset(test for test, passed in submission.tests.items() if passed)
        passed_tests.append(len(validated_tests))

    yield from plot_passed_tests(passed_tests).splitlines()
    yield '{}/{} tests passed'.format(len(validated_tests), len(submission.tests))

    # coding style (pylint)
    pylint_report = run_pylint_on_source(final_submission.source_code,
                                         module_name='module')
    yield from ('Pylint messages:\n\t' + '\n\t'.join(pylint_report.messages)).splitlines()
    yield '{}/10 pylint score'.format(pylint_report.rate)

    # teardown
    yield '#' * 80 + '\n\n\n\n\n'


if __name__ == "__main__":
    print(plot_passed_tests([0, 10, 40, 11, 7, 3, 8, 34]))
