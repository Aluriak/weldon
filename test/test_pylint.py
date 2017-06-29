

from pylint_interface import run_pylint_on_source


def test_pylint_parser():
    report = run_pylint_on_source("""def f(a, b):\n    return a + b\n""", module_name='mysum')

    assert report.rate == -15.
    assert report.stderr == 'No config file found, using default configuration\n'
    assert set(report.messages) == {
        ' mysum:1: convention (C0111, missing-docstring, ) Missing module docstring',
        ' mysum:1: convention (C0103, invalid-name, f) Invalid function name "f"',
        ' mysum:1: convention (C0103, invalid-name, f) Invalid argument name "a"',
        ' mysum:1: convention (C0103, invalid-name, f) Invalid argument name "b"',
        ' mysum:1: convention (C0111, missing-docstring, f) Missing function docstring',
    }
