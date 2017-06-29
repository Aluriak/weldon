import re
import tempfile
from collections import namedtuple

from pylint import epylint


DEFAULT_EVALUATION = '10.0 - ((float(5 * error + warning + refactor + convention) / statement) * 10)'
EVALUATION_TEMPLATE = '10.0 - ((float({error} + {warning} + {refactor} + {convention}) / statement) * 10)'
PylintReport = namedtuple('PylintReport', 'messages tables rate stderr')


def evaluation_expression(error:int=5, warning:int=1,
                          refactor:int=1, convention:int=1) -> str:
    """Return the evaluation expression usable by pylint to compute the final
    rate of a program.
    By default, output the default expression.

    >>> evaluation_expression() == DEFAULT_EVALUATION
    True

    """
    weights = {'error': error, 'warning': warning,
               'refactor': refactor, 'convention': convention}
    return EVALUATION_TEMPLATE.format(
        **{field:'{} * {}'.format(val, field) if val != 1 else field
           for field, val in weights.items()}
    )


def run_pylint_on_source(source_code:str, report_messages:bool=True,
                         report_tables:bool=False,
                         module_name:str=None,
                         note_expr:str=DEFAULT_EVALUATION) -> PylintReport:
    """Return the full report of pylint when ran on given source code"""
    # push source code into tempfile
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as fd:
        filename = fd.name
        fd.write(source_code)

    # build command line for pylint
    cli = filename
    if report_messages: cli += ' --enable=all'
    if report_tables: cli += ' --reports=y'
    if True: cli += ' --reports=y'
    if note_expr: cli += ' --evaluation="{}"'.format(note_expr)

    # run pylint
    pylint_stdout, pylint_stderr = epylint.py_run(cli, return_std=True)

    # replace references to named temporary file to the module name.
    module_name = str(module_name or filename)
    pylint_stdout = '\n'.join(
        line.replace(filename, module_name)
        for line in pylint_stdout.getvalue().splitlines()
    )

    return _pylint_report_from_outputs((pylint_stdout, pylint_stderr.getvalue()))


def _pylint_report_from_outputs(outputs:(str, str)) -> PylintReport:
    """Return a PylintReport instance describing information found in stdin
    and stderr of pylint"""
    REG_RATE = re.compile(r' Your code has been rated at (-?[0-9\.]+)/10')
    REG_MESSAGES = re.compile(r'\*{13} Module [a-z_A-Z-0-9\.]+')
    stdout, stderr = outputs
    messages, tables = [], []
    current_acc = None

    for line in stdout.splitlines():
        if line.startswith(' Your'):
            rate = float(REG_RATE.match(line).groups()[0])
        elif line.startswith('****'):
            assert REG_MESSAGES.match(line)
            current_acc = messages
        elif line.rstrip() in {' Report', ' ======'}:
            current_acc = tables
        else:
            current_acc.append(line.rstrip())

    return PylintReport(
        messages=tuple(msg for msg in messages if msg),
        tables=tables,
        rate=rate,
        stderr=stderr,
    )


if __name__ == "__main__":
    report = run_pylint_on_source("""def f(a, b):\n    return a + b\n""", module_name='mysum')
    print('MESSAGES:', '\n\t' + '\n\t'.join(report.messages))
    print('TABLES:', '\n\t' + '\n\t'.join(report.tables))
