"""GUI around the webclient, allowing end-user to easily interact with the server.

"""

import os
import tkinter as tk
from tkinter import filedialog, simpledialog

from webclient import Send as Client

TK_ROW_INFO = 1
TK_ROW_TEST = 2
TK_ROW_RESULT = 3
TK_ROW_FOOTER = 4

NO_COLOR = 'white'
COLOR_UNSET = 'pink'
COLOR_ERR = 'red'
COLOR_OK = 'light green'
COLOR_WAITING = 'light yellow'
DEFAULT_SERVER_CONFIG = {'host': '127.0.0.1', 'port': '6700',
                         'name': '', 'password': '', 'root': False}
SERVER_CONFIG_ORDER = ('name', 'password', 'host', 'port', 'root')


class ServerDialog(tk.Toplevel):

    def __init__(self, parent, config_updater:callable, config=DEFAULT_SERVER_CONFIG):
        self.server_config = config
        self.config_updater = config_updater
        self.parent = parent
        super().__init__(parent)
        self.__config_to_widgets()

    def __config_to_widgets(self):
        parent = self

        # Put a special color on a field when different from the initial value
        #  See https://stackoverflow.com/a/6549535/3077939
        #  (NB: this method is deprecated in later versions)
        def gen_callback(field, entry, value, value_holder):
            def callback(name, index, mode, sv=value_holder, initial_value=value):
                entry.configure(bg=COLOR_WAITING if initial_value != sv.get() else NO_COLOR)
            return callback

        def build_string_field(field, value, rowid:int):
            value_holder = tk.StringVar(parent, value=value)
            label = tk.Label(parent, text=field)
            entry = tk.Entry(parent, textvariable=value_holder)
            try:  # first try the new way
                value_holder.trace_add("write", gen_callback(field, entry, value, value_holder))
            except AttributeError:  # then the deprecated one
                value_holder.trace("w", gen_callback(field, entry, value, value_holder))

            label.grid(row=rowid, column=0)
            entry.grid(row=rowid, column=1)
            return label, value_holder, entry

        def build_bool_field(field, value, rowid:int):
            label = tk.Label(parent, text=field)
            value_holder = tk.Variable(value=value)
            check = tk.Checkbutton(parent, var=value_holder)

            try:  # first try the new way
                value_holder.trace_add("write", gen_callback(field, check, value, value_holder))
            except AttributeError:  # then the deprecated one
                value_holder.trace("w", gen_callback(field, check, value, value_holder))

            label.grid(row=rowid, column=0)
            check.grid(row=rowid, column=1)
            return label, value_holder, check

        self.value_holders = {
            field: build_string_field(field, self.server_config[field], idx)[1]
            for idx, field in enumerate(('name', 'password', 'host', 'port'))
        }
        self.value_holders['root'] = build_bool_field('root', self.server_config['root'], len(SERVER_CONFIG_ORDER)-1)[1]

        # Place the ending buttons
        rowid = len(SERVER_CONFIG_ORDER)
        tk.Button(parent, text='Cancel', command=self.destroy).grid(row=rowid, column=0)
        tk.Button(parent, text='Apply', command=self.apply).grid(row=rowid, column=1)


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
        self.__create_widgets()
        self._server_config = DEFAULT_SERVER_CONFIG
        self.client = None


    def _connected_to_server(self) -> bool:
        return bool(self.client)


    @property
    def server_config(self): return dict(self._server_config)
    def update_server_config(self, newconfig:dict):
        self._server_config = dict(newconfig)


    def __create_widgets(self):
        parent = self.parent
        self.current_error = tk.StringVar(value='')
        self.lab_error = tk.Label(parent, textvariable=self.current_error, fg=COLOR_ERR, height=1, width=8)

        self.lab_problems = tk.Label(parent, text='Problem:')
        self.lst_problems = tk.Listbox(parent, height=1)
        self.lst_problems = tk.Entry(parent, text='problem name', bg=COLOR_UNSET)

        self.but_sourcefile = tk.Button(parent, text="Source code", command=self.find_source_code, bg=COLOR_UNSET, width=2)
        self.but_server = tk.Button(parent, text="Server", command=self.config_server, bg=COLOR_UNSET)
        self.but_test = tk.Button(parent, text="Submit", command=self.submit, width=2)
        self.but_report = tk.Button(parent, text="Get report", command=self.ask_report, width=2)
        self.but_close = tk.Button(parent, text="Quit", command=self.confirm_close, width=2)

        # Place items in the grid
        rows = {
            TK_ROW_INFO: (self.but_server, self.lab_problems, self.lst_problems, self.but_sourcefile),
            # TK_ROW_TEST: (self.lab_sourcefile,),
            TK_ROW_RESULT: (self.but_test, self.but_report, self.but_close),
            TK_ROW_FOOTER: (self.lab_error,),
        }
        for rowid, widgets in rows.items():
            colid = 0
            for widget in widgets:
                columnspan = int(widget['width']) or 1
                print(widget, columnspan)
                widget.grid(row=rowid, column=colid, sticky=tk.W + tk.E, columnspan=columnspan)
                colid += columnspan

        # self.label.grid(columnspan=2, sticky=tk.W)

    def __create_test_result_widget(self, test_name, test_type, test_success) -> tk.Label:
        pass



    def find_source_code(self):
        filedesc = filedialog.askopenfile(
            defaultextension='.py',
            initialdir=os.getcwd(),
        )
        self._source_file = os.path.split(str(filedesc.name))[1]
        self._source_code = ''.join(filedesc)
        self.but_sourcefile.configure(text=self._source_file, bg=COLOR_OK)


    def confirm_close(self):
        default_active_bg = self.but_close['activebackground']
        self.but_close.configure(text='Sure ?', bg=COLOR_WAITING, command=self.parent.quit, activebackground=COLOR_WAITING)
        def infirm_close(_):
            self.but_close.configure(text='Quit', bg=NO_COLOR, command=self.confirm_close, activebackground=default_active_bg)
        self.but_close.bind('<Button-3>', infirm_close)


    def config_server(self):
        dialog = ServerDialog(self, self.update_server_config, config=self._server_config)
        self.wait_window(dialog)  # window could modify self.server_config
        self.but_server.configure(bg=COLOR_OK)
        server_config = {
            'name': self.server_config['name'],
            'registration_password': self.server_config['password'],
            'port': self.server_config['port'],
            'host': self.server_config['host'],
            'root': self.server_config['root'],
        }
        try:
            self.client = Client(**server_config)
            self.log('Connected to server')
        except ConnectionRefusedError as e:
            self.err('Connection refused. Maybe a bad host or port ?')



    def ask_report(self):
        print('REPORT')

    def submit(self):
        if not self._connected_to_server():
            self.err("Can't submit: not connected to server")
            self.but_server.configure(bg=COLOR_ERR)
        elif not self.lab_problems.get():
            self.err("Can't submit: no problem choosen")
            self.lab_problems.configure(bg=COLOR_ERR)
        elif not self._source_file:
            self.err("Can't submit: source code not given")
            self.but_sourcefile.configure(bg=COLOR_ERR)
        else:  # no problem: we can send
            pass

    def err(self, msg:str):
        """Report given error message to user"""
        self.lab_error.configure(fg=COLOR_ERR)
        self.current_error.set(str(msg))

    def log(self, msg:str):
        """Report given log message to user"""
        self.lab_error.configure(fg=COLOR_OK)
        self.current_error.set(str(msg))


if __name__ == "__main__":
    root = tk.Tk()
    WeldonInterface(root)
    root.mainloop()
