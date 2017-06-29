"""Implementation of the pytest run, allowing Server
to test a user submission.

"""

import os
import re
import shutil
import subprocess

import pytest

from commons import TEST_TYPES, SubmissionResult, TestResult


def result_from_pytest(problem, source_code, run_dir='./run/',
                       test_output:str='./run/test_output') -> SubmissionResult:
    """Main API: return submission result knowing the problem,
    the source code and the pytest related parameters

    """
    results = run_tests_on_problem(problem, source_code, run_dir, test_output)
    return extract_results_from_pytest_output(results, problem.id, source_code)


def run_tests_on_problem(problem, source_code, run_dir='./run/',
                         test_output:str='./run/test_output'):
    """Run problem specs on given source code, in given run_dir.

    WARNING: Will erase everything found in run_dir.

    Return the tests results (raw lines returned by pytest).

    This method is interesting, but go out of python.
    Could be an advantage when passing by apparmor or other sandboxing modes.
    """
    # first backup and empty the run dir
    backup_dir = run_dir.rstrip('/') + '.backup'
    if os.path.exists(backup_dir):
        shutil.rmtree(backup_dir)
    if os.path.exists(run_dir):
        shutil.move(run_dir, backup_dir)
    os.mkdir(run_dir)

    # populate the run dir
    runnable_source_code_file = problem.source_code_filename(dir=run_dir)
    runnable_public_test_file = problem.public_test_filename(dir=run_dir)
    runnable_hidden_test_file = problem.hidden_test_filename(dir=run_dir)
    runnable_community_test_file = problem.community_test_filename(dir=run_dir)
    with open(runnable_source_code_file, 'w') as fd:
        fd.write(source_code)
    with open(runnable_public_test_file, 'w') as fd:
        fd.write('import pytest\n')
        fd.write('from {} import *\n\n'.format(problem.source_name))
        fd.write('\n'.join(map(str, problem.public_tests)))
    with open(runnable_hidden_test_file, 'w') as fd:
        fd.write('import pytest\n')
        fd.write('from {} import *\n\n'.format(problem.source_name))
        fd.write('\n'.join(map(str, problem.hidden_tests)))
    with open(runnable_community_test_file, 'w') as fd:
        fd.write('import pytest\n')
        fd.write('from {} import *\n\n'.format(problem.source_name))
        fd.write('\n'.join(map(str, problem.community_tests)))
    # run the tests
    proc = subprocess.Popen(['pytest', run_dir, '-vv'], stdout=subprocess.PIPE)
    stdout, stderr = proc.communicate()
    return stdout.decode()


def extract_results_from_pytest_output(output:str, problem_id:int,
                                       source_code:str) -> SubmissionResult:
    """Return a SubmissionResult instance describing given pytest output"""
    reg_test = re.compile(r'^[\/a-zA-Z_0-9]+test_([hiddenpubliccommunity]+)_cases\.py::test_([a-zA-Z_0-9]+) ([PASSEDFAIL]+)$')
    tests = {}  # test name: test status
    for line in output.splitlines(keepends=False):
        match = reg_test.match(line)
        if match:
            type, testname, result = match.groups()
            assert type in TEST_TYPES
            tests[testname] = TestResult(testname, type, result == 'PASSED')
    return SubmissionResult(tests=tests, full_trace=str(output),
                            problem_id=problem_id, source_code=str(source_code))
