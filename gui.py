"""GUI around the webclient, allowing end-user to easily interact with the server.

"""

import os
import tkinter as tk
from tkinter import filedialog, simpledialog, font

from webclient import Send as Client
from commons import ServerError


TK_ROW_INFO = 1
TK_ROW_TEST = 2
TK_ROW_RESULT = 3
TK_ROW_FOOTER = 4

NO_COLOR = 'white'
COLOR_UNSET = 'pink'
COLOR_ERR = 'red'
COLOR_LOG = 'dark green'
COLOR_OK = 'light green'
COLOR_WAITING = 'yellow'

DEFAULT_SERVER_CONFIG = {'host': '127.0.0.1', 'port': '6700',
                         'name': '', 'password': '', 'root': False}
from webserver import PORT
DEFAULT_SERVER_CONFIG = {'host': '127.0.0.1', 'port': PORT,
                         'name': 'lucas', 'password': 'WOLOLO42', 'root': False}
SERVER_CONFIG_ORDER = ('name', 'password', 'host', 'port', 'root')


# """
try:
    from populate_server import populate
    conn = Client('SHUBISHI', name='populate3', root=True, port=PORT, host='127.0.0.1')
    print(conn)
    populate(conn)
    del conn
except ServerError as e:
    print('ServerError:', e.args[0])
"""#"""


# Put a special color on a field when different from the initial value
#  See https://stackoverflow.com/a/6549535/3077939
#  (NB: this method is deprecated in later versions)
def gen_callback(entry, initial_values, value_holder, type=str,
                 color_diff=COLOR_WAITING, color_nodiff=NO_COLOR, color_unvalid=COLOR_ERR):
    def callback(name, index, mode, sv=value_holder, initial_values=initial_values):
        try:
            entry.configure(bg=color_nodiff if type(sv.get()) in initial_values else color_diff)
        except ValueError:  # happen if sv.get() is not convertible to type
            entry.configure(bg=color_unvalid)
    return callback


class ServerDialog(tk.Toplevel):

    def __init__(self, parent, config_updater:callable,
                 config=DEFAULT_SERVER_CONFIG, can_cancel=True):
        self.server_config = config
        self.config_updater = config_updater
        self.parent = parent
        super().__init__(parent)
        self.__config_to_widgets(can_cancel=can_cancel)

    def __config_to_widgets(self, can_cancel:bool):
        parent = self

        def build_string_field(field, value, rowid:int):
            value_holder = tk.StringVar(parent, value=value)
            label = tk.Label(parent, text=field)
            entry = tk.Entry(parent, textvariable=value_holder)
            try:  # first try the new way
                value_holder.trace_add("write", gen_callback(entry, {value}, value_holder))
            except AttributeError:  # then the deprecated one
                value_holder.trace("w", gen_callback(entry, {value}, value_holder))
            label.grid(row=rowid, column=0)
            entry.grid(row=rowid, column=1)
            return value_holder

        def build_field(field, value, rowid, widget_type=tk.Entry, holder_type=tk.StringVar, var_param='textvariable', type=str, **widget_args):
            label = tk.Label(parent, text=field)
            value_holder = holder_type(value=value)
            box = widget_type(parent, **{var_param: value_holder}, **widget_args)
            try:  # first try the new way
                value_holder.trace_add("write", gen_callback(box, {value}, value_holder, type=type))
            except AttributeError:  # then the deprecated one
                value_holder.trace("w", gen_callback(box, {value}, value_holder))
            label.grid(row=rowid, column=0)
            box.grid(row=rowid, column=1)
            return value_holder

        def build_int_field(field, value, rowid:int):
            label = tk.Label(parent, text=field)
            value_holder = tk.StringVar(value=value)  # IntVar makes the cast itself, leading to errors
            box = tk.Spinbox(parent, from_=1025, to=64000, increment=1, textvariable=value_holder)
            try:  # first try the new way
                value_holder.trace_add("write", gen_callback(box, {value}, value_holder, type=int))
            except AttributeError:  # then the deprecated one
                value_holder.trace("w", gen_callback(box, {value}, value_holder))
            label.grid(row=rowid, column=0)
            box.grid(row=rowid, column=1)
            return value_holder

        def build_bool_field(field, value, rowid:int):
            label = tk.Label(parent, text=field)
            value_holder = tk.Variable(value=value)
            box = tk.Checkbutton(parent, var=value_holder)
            try:  # first try the new way
                value_holder.trace_add("write", gen_callback(box, {value}, value_holder))
            except AttributeError:  # then the deprecated one
                value_holder.trace("w", gen_callback(box, {value}, value_holder))
            label.grid(row=rowid, column=0)
            box.grid(row=rowid, column=1)
            return value_holder

        self.value_holders = {
            field: build_field(field, self.server_config[field], idx)
            for idx, field in enumerate(('name', 'password', 'host'))
        }
        self.value_holders['port'] =  build_field('port', self.server_config['port'], len(SERVER_CONFIG_ORDER)-2, tk.Spinbox, from_=1025, to='64000', increment=1, type=int)
        self.value_holders['root'] = build_field('root', self.server_config['root'], len(SERVER_CONFIG_ORDER)-1, tk.Checkbutton, tk.Variable, var_param='var')

        if can_cancel:
            # Place the ending buttons
            rowid = len(SERVER_CONFIG_ORDER)
            tk.Button(parent, text='Cancel', command=self.destroy).grid(row=rowid, column=0)
            tk.Button(parent, text='Apply', command=self.apply).grid(row=rowid, column=1)
        else:  # Place the only apply button
            rowid = len(SERVER_CONFIG_ORDER)
            tk.Button(parent, text='Apply', command=self.apply).grid(row=rowid, column=0, columnspan=2)


    def __widgets_to_config(self) -> dict:
        return {
            field: holder.get()
            for field, holder in self.value_holders.items()
        }


    def apply(self):
        self.config_updater(self.__widgets_to_config())
        self.destroy()



class WeldonInterface(tk.Frame):
    def __init__(self, parent, *args, **kwargs):
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.parent = parent
        self.parent.title("Weldon")
        self.client = None
        self.__create_widgets()
        self._server_config = DEFAULT_SERVER_CONFIG
        self.configure_server(can_cancel=False)

        # Data holders
        self._source_file = None
        self._source_file_lasttime = 0  # last time of modification of the file

    def _connected_to_server(self) -> bool:
        return bool(self.client)


    @property
    def server_config(self): return dict(self._server_config)
    def update_server_config(self, newconfig:dict):
        self._server_config = dict(newconfig)


    def __create_widgets(self):
        parent = self.parent
        self.but_server_text = tk.StringVar(value='Server')
        self.but_server = tk.Button(parent, textvariable=self.but_server_text, command=self.configure_server, bg=COLOR_UNSET)
        self.but_server.grid(row=TK_ROW_INFO, column=0, sticky=tk.W + tk.E, columnspan=1)

        self.lab_problems = tk.Label(parent, text='Problem:')
        self.lab_problems.grid(row=TK_ROW_INFO, column=1, sticky=tk.W + tk.E)
        # self.lst_problems = tk.Listbox(parent, height=1)

        self.lst_problems_text = tk.StringVar(value='')
        self.lst_problems_trace = None  # will be used for later trace management
        self.lst_problems = tk.Spinbox(parent, textvariable=self.lst_problems_text, bg=COLOR_UNSET)
        self.lst_problems.grid(row=TK_ROW_INFO, column=2, sticky=tk.W + tk.E)
        self.__init_widget_problems()

        self.but_sourcefile = tk.Button(parent, text='Source code', command=self.find_source_code, bg=COLOR_UNSET)
        self.but_sourcefile.grid(row=TK_ROW_INFO, column=3, sticky=tk.W + tk.E)

        self.but_test = tk.Button(parent, text='Submit', command=self.submit)
        self.but_test.grid(row=TK_ROW_INFO, column=4, sticky=tk.W + tk.E)
        self.but_report = tk.Button(parent, text='Get report', command=self.ask_report)
        self.but_report.grid(row=TK_ROW_INFO, column=5, sticky=tk.W + tk.E)
        self.but_close = tk.Button(parent, text='Quit', command=self.confirm_close)
        self.but_close.grid(row=TK_ROW_INFO, column=6, sticky=tk.W + tk.E)

        error_font = font.Font(family='Helvetica', size=10, weight='bold')
        self.current_error = tk.StringVar(value=' ' * 40)
        self.lab_error = tk.Label(parent, textvariable=self.current_error, fg=COLOR_ERR, bg=NO_COLOR, height=1, font=error_font)
        self.lab_error.grid(row=TK_ROW_FOOTER, column=0, sticky=tk.W, columnspan=8)


    def __init_widget_problems(self):
        self.available_problems = tuple(self.client.list_problems()) if self.client else ()
        if self.lst_problems_trace:
            self.lst_problems_text.trace_remove(*self.lst_problems_trace)
        try:  # first try the new way
            trace = self.lst_problems_text.trace_add('write', gen_callback(self.lst_problems, self.available_problems, self.lst_problems_text, color_diff=COLOR_UNSET, color_nodiff=COLOR_OK))
            self.lst_problems_trace = 'write', trace
        except AttributeError:  # then the deprecated one
            trace = self.lst_problems_text.trace('w', gen_callback(self.lst_problems, self.available_problems, value_holder))
            self.lst_problems_trace = 'w', trace
        # give the proper initial color
        self.lst_problems['values'] = self.available_problems


    def __create_test_result_widget(self, test_name, test_type, test_success) -> tk.Label:
        pass

    def __handle_submission_result(self, results):
        nb_tests = sum(1 for test in results.tests)
        nb_succeed_tests = sum(1 for test in results.tests if test.succeed)
        self.log(f'Submission done. {nb_succeed_tests}/{nb_tests} tests succeed.')

        # print(results)


    def find_source_code(self):
        filedesc = filedialog.askopenfile(
            defaultextension='.py',
            initialdir=os.getcwd(),
        )
        if filedesc:
            self._source_file = filedesc.name
            self._source_file_lasttime = 0  # will be set correctly after submission
            basename = os.path.split(str(filedesc.name))[1]
            self.but_sourcefile.configure(text=basename, bg=COLOR_OK)


    def confirm_close(self):
        default_active_bg = self.but_close['activebackground']
        self.but_close.configure(text='Sure ?', bg=COLOR_WAITING, command=self.parent.quit, activebackground=COLOR_WAITING)
        def infirm_close(_):
            self.but_close.configure(text='Quit', bg=NO_COLOR, command=self.confirm_close, activebackground=default_active_bg)
        self.but_close.bind('<Button-3>', infirm_close)


    def configure_server(self, can_cancel:bool=True):
        dialog = ServerDialog(self, self.update_server_config,
                              config=self._server_config, can_cancel=can_cancel)
        self.wait_window(dialog)  # window could modify self.server_config
        server_config = {
            'name': self.server_config['name'],
            'registration_password': self.server_config['password'],
            'port': self.server_config['port'],
            'host': self.server_config['host'],
            'root': self.server_config['root'],
        }
        try:
            self.client = Client(**server_config)
            self.__init_widget_problems()
            self.but_server.configure(bg=COLOR_OK)
            self.but_server_text.set('Actualize')
            self.log('Connected to server')
        except ConnectionRefusedError as e:
            self.but_server.configure(bg=COLOR_ERR)
            self.err('Connection refused. Maybe a bad host or port ?')


    def ask_report(self):
        if self.__validate_current_state(validate_code=False):
            try:
                print(self.client.retrieve_report(problem_id=self.lst_problems_text.get()))
            except ServerError as e:
                self.err(e.args[0])

    def submit(self):
        self.info('Submission…')
        if self.__validate_current_state():
            self.client.problem_id = self.lst_problems_text.get()
            with open(self._source_file) as fd:
                source_code = fd.read()
            submission_result = self.client.submit_solution(source_code)
            # avoid two consecutive submissions on the same source code
            self._source_file_lasttime = os.path.getmtime(self._source_file)
            # finally handle the server answer
            self.__handle_submission_result(submission_result)


    def __validate_current_state(self, validate_code=True) -> bool:
        if not self._connected_to_server():
            self.err("Can't submit: not connected to server")
            self.but_server.configure(bg=COLOR_ERR)
        elif not self.lst_problems_text.get():
            self.err("Can't submit: no problem choosen")
            self.lst_problems.configure(bg=COLOR_ERR)
        elif self.lst_problems_text.get() not in self.available_problems:
            self.err("Can't submit: Given problem not known")
            self.lst_problems.configure(bg=COLOR_ERR)
        elif validate_code and not self._source_file:
            self.err("Can't submit: source code not given")
            self.but_sourcefile.configure(bg=COLOR_ERR)
        elif validate_code and os.path.getmtime(self._source_file) == self._source_file_lasttime:
            self.err("Can't submit: source code not changed since last submission.")
        else:  # no problem: we are ready to speak with the server
            return True
        return False  # their is at least one problem



    def err(self, msg:str):
        """Report given error message to user"""
        self.lab_error.configure(fg=COLOR_ERR)
        self.current_error.set(str(msg))
        self.update_idletasks()  # redraw (do not wait for the end of event handling)

    def log(self, msg:str):
        """Report given log message to user"""
        self.lab_error.configure(fg=COLOR_LOG)
        self.current_error.set(str(msg))
        self.update_idletasks()

    def info(self, msg:str):
        """Report given log message to user"""
        self.lab_error.configure(fg=COLOR_WAITING)
        self.current_error.set(str(msg))
        self.update_idletasks()


if __name__ == "__main__":
    root = tk.Tk()
    WeldonInterface(root)
    root.mainloop()
