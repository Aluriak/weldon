"""Implementation of the pytest run, allowing Server
to test a user submission.

"""

import os
import re
import shutil
import subprocess

import pytest

from commons import TEST_TYPES, SubmissionResult, TestResult


def run_tests_on_problem_by_fixture(problem, source_code, run_dir='./run/'):
    """Run problem specs on given source code, in given run_dir.

    This method is interesting, but needs to be ran by pytest itself.
    So it can't be used inside the server implementation…
    """
    TEMPLATE_TEST_UNIT = """
    import pytest
    pytest_plugins = "pytester"

    def test_something(testdir):
        "Test some thing."
        testdir.makepyfile('''{}''')
        result = testdir.runpytest('-vv')
        import re
        for line in result.stdout.lines:
            match = re.match(r'[a-zA-Z_0-9]+\.py::(test_[a-zA-Z_0-9]+) ([PASSEDFAIL]+)', line)
            if match:
                testname, result = match.groups()
                assert result == 'PASSED', "Test {} did not succeed".format(testname)
    """
    TEST_FILE = os.path.join(run_dir, 'test_all.py')
    with open(TEST_FILE, 'w') as fd:
        fd.write(TEMPLATE_TEST_UNIT.format(
            'import pytest\n'
            + 'from {} import *\n\n'.format(problem.source_name)
            + problem.public_tests
            + problem.hidden_tests
        ))

    # todo: intercept and return stdout
    pytest.main([TEST_FILE], ['pytester'])


def run_tests_on_problem_by_main(problem, source_code, run_dir='./run/'):
    """Run problem specs on given source code, in given run_dir

    This method is interesting, but pytest print results in stdout.
    This is a way to go, but needs interception of stdout.

    Another way, maybe the most simple, could be to call the pytest binary
    via subprocess. This way, later implementations with protection
    about executed code (apparmor for instance) could easily be plugged.
    """
    runnable_source_code_file = problem.source_code_filename(dir=run_dir)
    runnable_public_test_file = problem.public_test_filename(dir=run_dir)
    runnable_hidden_test_file = problem.hidden_test_filename(dir=run_dir)
    with open(runnable_source_code_file, 'w') as fd:
        fd.write(source_code)
    with open(runnable_public_test_file, 'w') as fd:
        fd.write('import pytest\n')
        fd.write('from {} import *\n\n'.format(problem.source_name))
        fd.write(problem.public_tests)
    with open(runnable_hidden_test_file, 'w') as fd:
        fd.write('import pytest\n')
        fd.write('from {} import *\n\n'.format(problem.source_name))
        fd.write(problem.hidden_tests)

    # todo: intercept and return stdout
    pytest.main([run_dir])


def run_tests_on_problem_by_subprocess(problem, source_code, run_dir='./run/',
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
        fd.write(problem.public_tests)
    with open(runnable_hidden_test_file, 'w') as fd:
        fd.write('import pytest\n')
        fd.write('from {} import *\n\n'.format(problem.source_name))
        fd.write(problem.hidden_tests)
    with open(runnable_community_test_file, 'w') as fd:
        fd.write('import pytest\n')
        fd.write('from {} import *\n\n'.format(problem.source_name))
        fd.write(problem.community_tests)
    # run the tests
    proc = subprocess.Popen(['pytest', run_dir, '-vv'], stdout=subprocess.PIPE)
    stdout, stderr = proc.communicate()
    return stdout.decode()


run_tests_on_problem = run_tests_on_problem_by_main
run_tests_on_problem = run_tests_on_problem_by_fixture
run_tests_on_problem = run_tests_on_problem_by_subprocess


def extract_results_from_pytest_output(output:str, problem_id:str) -> SubmissionResult:
    """Return a SubmissionResult instance describing given pytest output"""
    reg_test = re.compile(r'^[\/a-zA-Z_0-9]+test_([hiddenpubliccommunity]+)_cases\.py::test_([a-zA-Z_0-9]+) ([PASSEDFAIL]+)$')
    tests = {}  # test name: test status
    for line in output.splitlines(keepends=False):
        match = reg_test.match(line)
        if match:
            type, testname, result = match.groups()
            assert type in TEST_TYPES
            tests[testname] = TestResult(testname, type, result == 'PASSED')
    return SubmissionResult(tests=tests, full_trace=str(output), problem_id=problem_id)
